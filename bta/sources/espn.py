"""ESPN public web endpoints: unofficial, best-effort, NOT an official/status/odds verification source.
No access guarantee, third-party usage restrictions must be reviewed before launch.
"""
from __future__ import annotations
import requests
from datetime import date, datetime, timezone
from functools import lru_cache
from urllib.parse import urlencode
from bta.domain import Game, utcnow

BASE = "https://site.api.espn.com/apis/site/v2/sports"
WEB = "https://site.web.api.espn.com/apis/common/v3/sports"
ROUTES = {"NBA": ("basketball", "nba"), "NFL": ("football", "nfl"), "CFB": ("football", "college-football")}
TIMEOUT = 12

class SourceError(RuntimeError):
    pass

@lru_cache(maxsize=400)
def _request_cached(url: str, bucket: int) -> dict:
    del bucket
    response = requests.get(url, timeout=TIMEOUT, headers={"User-Agent": "BTA2.0 research-prototype/0.1", "Accept": "application/json"}, allow_redirects=False)
    if response.status_code != 200:
        raise SourceError(f"Sports feed returned HTTP {response.status_code}")
    if len(response.content) > 7_000_000:
        raise SourceError("Feed response exceeded safety limit")
    try:
        payload = response.json()
    except ValueError as exc:
        raise SourceError("Sports feed did not return JSON") from exc
    if not isinstance(payload, dict):
        raise SourceError("Unexpected provider response")
    return payload


def fetch(url: str, ttl_seconds: int = 300, refresh: bool = False) -> dict:
    import time
    # Entire URL assembled from controlled route constants and numeric identifiers.
    if not url.startswith((BASE + "/", WEB + "/")):
        raise SourceError("Unapproved feed URL")
    bucket = int(time.time() / max(30, ttl_seconds))
    if refresh:
        _request_cached.cache_clear()
    try:
        return _request_cached(url, bucket)
    except (requests.RequestException, ValueError) as exc:
        raise SourceError(f"Feed unavailable: {type(exc).__name__}") from exc


def scoreboard(sport: str, on_date: date | None = None, refresh: bool = False) -> tuple[list[Game], str]:
    if sport not in ROUTES:
        raise ValueError("Unknown league")
    category, league = ROUTES[sport]
    url = f"{BASE}/{category}/{league}/scoreboard"
    params = {}
    if on_date is not None:
        params["dates"] = on_date.strftime("%Y%m%d")
    if sport == "CFB":
        params["limit"] = 300
        params["groups"] = 80  # ESPN college-football group 80 = FBS (I-A); 81 = FCS
    if params:
        url += "?" + urlencode(params)
    data = fetch(url, ttl_seconds=240, refresh=refresh)
    checked = utcnow()
    events = data.get("events") or []
    games = []
    for event in events:
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        competitors = competitions[0].get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away or not event.get("id"):
            continue
        status = (event.get("status") or {}).get("type") or {}
        state = status.get("state", "unknown")
        details = status.get("shortDetail") or status.get("detail") or status.get("description") or ""
        home_team, away_team = home.get("team") or {}, away.get("team") or {}
        score = ""
        if home.get("score") is not None and away.get("score") is not None:
            score = f"{away.get('score')} – {home.get('score')}"
        games.append(Game(
            id=str(event["id"]), sport=sport, start_time=event.get("date", ""),
            home=home_team.get("displayName") or home_team.get("name", "Home"),
            away=away_team.get("displayName") or away_team.get("name", "Away"),
            home_id=str(home_team.get("id") or ""), away_id=str(away_team.get("id") or ""),
            state=str(state), score=score, detail=details, source_url=url, checked_at=checked,
            source_status="OBSERVED_THIRD_PARTY", league=league,
        ))
    games.sort(key=lambda g: g.start_time)
    return games, url


def summary(sport: str, event_id: str, refresh: bool = False) -> tuple[dict, str]:
    if sport not in ROUTES or not event_id.isdigit():
        raise SourceError("Invalid game identifier")
    cat, league = ROUTES[sport]
    url = f"{BASE}/{cat}/{league}/summary?event={event_id}"
    return fetch(url, ttl_seconds=180, refresh=refresh), url


def roster(sport: str, team_id: str) -> tuple[list[dict], str]:
    if sport not in ROUTES or not team_id.isdigit():
        raise SourceError("Invalid team identifier")
    cat, league = ROUTES[sport]
    url = f"{BASE}/{cat}/{league}/teams/{team_id}/roster"
    data = fetch(url, ttl_seconds=86400)
    athletes = data.get("athletes") or []
    entries = []
    for group in athletes:
        if not isinstance(group, dict):
            continue
        items=group.get("items")
        if isinstance(items,list):
            entries.extend(items)
        elif group.get('id'):
            entries.append(group)
    players=[]
    for athlete in entries:
        if not athlete.get('id'):
            continue
        pos=athlete.get('position') or {}
        if isinstance(pos, dict):
            pos=pos.get('abbreviation') or pos.get('shortName') or pos.get('name') or ''
        if not pos and isinstance(athlete.get('athlete'),dict):
            sub=athlete['athlete']
            pos=(sub.get('position') or {}).get('abbreviation','') if isinstance(sub.get('position'),dict) else sub.get('position','')
        players.append({"id":str(athlete['id']),"name":athlete.get('displayName') or athlete.get('fullName') or '',
                        "position":str(pos or ''), "status":"ROSTER_ONLY"})
    return players,url


def gamelog(sport: str, athlete_id: str, season: int | None = None) -> tuple[dict, str]:
    if sport not in ROUTES or not athlete_id.isdigit() or len(athlete_id) > 15:
        raise SourceError("Invalid athlete identifier")
    cat, league = ROUTES[sport]
    url = f"{WEB}/{cat}/{league}/athletes/{athlete_id}/gamelog"
    if season is not None:
        if not 2000 <= season <= 2100:
            raise SourceError("Invalid season")
        url += f"?season={season}"
    return fetch(url, ttl_seconds=14400), url


def rows_from_gamelog(payload: dict, market: str, cutoff: str = "") -> list[dict]:
    """Read parallel stats/labels; returns only explicit numeric fields and dated finished games.
    ESPN may change schema. Missing/unclear columns are NOT replaced by zero.
    """
    mapping = {
        "points": ("PTS", "points"), "rebounds": ("REB", "rebounds"),
        "assists": ("AST", "assists"), "three_pointers_made": ("3PM", "3PTM", "3PT", "threePointersMade"),
        "steals": ("STL", "steals"), "blocks": ("BLK", "blocks"),
        "rushing_yards": ("YDS", "rushYds", "rushingYards"),
        "receiving_yards": ("YDS", "REC YDS", "REC_YDS", "receivingYards"),
        "passing_yards": ("YDS", "PASS YDS", "passingYards"),
        "receptions": ("REC", "receptions"),
        "rushing_attempts": ("CAR", "rushingAttempts"),
        "passing_attempts": ("ATT", "passingAttempts"),
        "completions": ("CMP", "completions"),
        "passing_touchdowns": ("TD", "PASS TD", "passingTouchdowns"),
        "rushing_touchdowns": ("TD", "RUSH TD", "rushingTouchdowns"),
        "receiving_touchdowns": ("TD", "REC TD", "receivingTouchdowns"),
    }
    combo_components = {
        # Do not count QB passing TDs as an anytime rushing/receiving TD.
        # Both component stats must be independently present for an event.
        "anytime_td": ("rushing_touchdowns", "receiving_touchdowns"),
        "points_rebounds_assists": ("points", "rebounds", "assists"),
        "points_rebounds": ("points", "rebounds"),
        "points_assists": ("points", "assists"),
        "rebounds_assists": ("rebounds", "assists"),
        "steals_blocks": ("steals", "blocks"),
        "rushing_receiving_yards": ("rushing_yards", "receiving_yards"),
    }
    if market in combo_components:
        parts = [rows_from_gamelog(payload, component, cutoff=cutoff) for component in combo_components[market]]
        if not parts or not all(parts):return []
        others=[{r['event_id']:r for r in part} for part in parts[1:]]
        assembled=[]
        for first in parts[0]:
            peers=[by_event.get(first['event_id']) for by_event in others]
            if any(x is None or x['date']!=first['date'] for x in peers):continue
            combined={'event_id':first['event_id'],'date':first['date'],
                'opponent':first['opponent'],'value':round(sum(p['value'] for p in [first,*peers]),3)}
            # NBA combined markets inherit independently observed minutes from the
            # same athlete and same event, never from a different game.
            if market!='rushing_receiving_yards' and first.get('minutes') is not None:
                combined['minutes']=first['minutes']
            assembled.append(combined)
        return sorted(assembled,key=lambda r:r['date'],reverse=True)
    if market not in mapping:
        return []
    meta = payload.get("events") or {}
    if isinstance(meta, list):
        meta = {str(g.get("id")): g for g in meta if isinstance(g, dict)}
    results = []
    seen = set()
    for season_type in payload.get("seasonTypes") or []:
        for cat in season_type.get("categories") or []:
            category_name = str(cat.get("name") or cat.get("displayName") or "").lower()
            # Different NFL/YDS columns share a name. Only parse YDS in the relevant stat family.
            expected_family = {
                "passing_yards": "passing", "passing_touchdowns": "passing",
                "passing_attempts": "passing", "completions": "passing",
                "rushing_yards": "rushing", "rushing_attempts": "rushing",
                "receiving_yards": "receiving", "receptions": "receiving",
                "rushing_touchdowns": "rushing", "receiving_touchdowns": "receiving",
            }.get(market)
            if expected_family and expected_family not in category_name:
                # The entire category may be unlabelled by the upstream provider; do not guess.
                continue
            labels = cat.get("labels") or payload.get("labels") or []
            if not isinstance(labels, list):
                continue
            lookup = {str(key).upper().replace(" ", "").replace("_", ""): i for i, key in enumerate(labels)}
            def get_value(stats, keys):
                for key in keys:
                    idx = lookup.get(key.upper().replace(" ", "").replace("_", ""))
                    if idx is not None and idx < len(stats):
                        try:
                            raw=str(stats[idx]).replace(",", "").strip()
                            if key in ("3PM", "3PTM", "3PT", "threePointersMade") and "-" in raw:
                                raw=raw.split("-",1)[0] # 3PT column is made-attempted
                            if key in ("MIN", "minutes") and ":" in raw:
                                m,sec=raw.split(":",1)
                                raw=str(int(m)+int(sec)/60)
                            val = float(raw)
                        except (TypeError, ValueError):
                            continue
                        if val >= 0:
                            return val
                return None
            for entry in cat.get("events") or []:
                event_id = str(entry.get("eventId") or entry.get("id") or "")
                details = meta.get(event_id) or {}
                event_date = details.get("gameDate") or details.get("date") or ""
                if not event_id or not event_date or event_id in seen:
                    continue
                if cutoff:
                    try:
                        event_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
                        cutoff_dt = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
                        if event_dt.tzinfo is None: event_dt = event_dt.replace(tzinfo=timezone.utc)
                        if cutoff_dt.tzinfo is None: cutoff_dt = cutoff_dt.replace(tzinfo=timezone.utc)
                        if event_dt >= cutoff_dt:
                            continue
                    except (TypeError, ValueError):
                        continue  # Unknown date cannot enter a no-lookahead sample.
                stats = entry.get("stats") or []
                if market == "points_rebounds_assists":
                    values = [get_value(stats, mapping[m]) for m in ("points", "rebounds", "assists")]
                    value = sum(values) if all(v is not None for v in values) else None
                else:
                    value = get_value(stats, mapping[market])
                if value is None:
                    continue
                seen.add(event_id)
                opponent = details.get("opponent") or {}
                row={"event_id": event_id, "date": event_date,
                     "opponent": opponent.get("abbreviation") or opponent.get("displayName") or "Unknown", "value": value}
                # Independently observed opportunity data; never turn an absent field into 0.
                if market in {"points","rebounds","assists","three_pointers_made","steals","blocks"}:
                    minutes=get_value(stats,("MIN","minutes"))
                    if minutes is not None:row['minutes']=minutes
                if expected_family == 'passing':
                    attempts=get_value(stats,("ATT","passingAttempts"))
                    if attempts is not None:row['attempts']=attempts
                if expected_family == 'rushing':
                    attempts=get_value(stats,("CAR","rushingAttempts"))
                    if attempts is not None:row['attempts']=attempts
                if expected_family == 'receiving':
                    targets=get_value(stats,("TGT","TAR","targets"))
                    if targets is not None:row['targets']=targets
                results.append(row)
    return sorted(results, key=lambda r: r["date"], reverse=True)


def team_schedule(sport: str, team_id: str, season: int) -> tuple[list[dict], str]:
    """Observed historical finals from public scoreboard/schedule, no opponent-quality rating implied."""
    if sport not in ROUTES or not team_id.isdigit() or not (2000 <= season <= 2100):
        raise SourceError("Invalid team schedule lookup")
    cat, league = ROUTES[sport]
    url = f"{BASE}/{cat}/{league}/teams/{team_id}/schedule?season={season}"
    data = fetch(url, ttl_seconds=14400)
    rows = []
    for event in data.get("events") or []:
        competitions = event.get("competitions") or []
        if not competitions:
            continue
        comp = competitions[0]
        competitors = comp.get("competitors") or []
        mine = next((x for x in competitors if str((x.get("team") or {}).get("id") or x.get("id")) == str(team_id)), None)
        other = next((x for x in competitors if x is not mine), None)
        if not mine or not other:
            continue
        status = (comp.get("status") or event.get("status") or {}).get("type") or {}
        if status.get("state") != "post":
            continue
        try:
            mine_score = float((mine.get("score") or {}).get("value") if isinstance(mine.get("score"),dict) else mine.get("score"))
            other_score = float((other.get("score") or {}).get("value") if isinstance(other.get("score"),dict) else other.get("score"))
        except (TypeError, ValueError):
            continue
        week_obj=event.get('week') or comp.get('week') or {}
        if isinstance(week_obj,dict):week_value=week_obj.get('number') or week_obj.get('week')
        else:week_value=week_obj
        try:
            week_num=int(week_value)
            if not 1<=week_num<=23:week_num=None
        except (TypeError,ValueError):week_num=None
        rows.append({"date": event.get("date", ""),
            "week":week_num,
            "opponent_abbr":(other.get("team") or {}).get("abbreviation") or '',
            "opponent":(other.get("team") or {}).get("displayName") or "Unknown",
            "points_for":mine_score,"points_against":other_score,"margin":mine_score-other_score,
            "result":"W" if mine_score>other_score else "L" if mine_score<other_score else "T",
            "event_id":str(event.get("id", "")),"source_url":url})
    return sorted(rows,key=lambda r:r["date"],reverse=True),url
