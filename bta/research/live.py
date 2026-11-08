"""Observed game/athlete progress. Never returns settlement or calibrated probability."""
from __future__ import annotations
from bta.domain import Selection, utcnow
from bta.sources.espn import summary
from bta.research.freshness import freshness_state

LABELS = {
    "points": "PTS", "rebounds": "REB", "assists": "AST", "three_pointers_made": "3PM",
    "steals": "STL", "blocks": "BLK", "receptions": "REC",
    "receiving_yards": "YDS", "rushing_yards": "YDS", "passing_yards": "YDS",
}
CATEGORIES = {
    "receiving_yards":"receiving", "rushing_yards":"rushing", "passing_yards":"passing",
    "receptions":"receiving",
}


def observed_from_summary(selection: Selection, payload: dict) -> dict:
    header = payload.get("header") or {}
    comps = header.get("competitions") or []
    comp = comps[0] if comps else {}
    status = (comp.get("status") or header.get("status") or {})
    status_type = status.get("type") or {}
    competitors = comp.get("competitors") or []
    scores = []
    for team in competitors:
        title = (team.get("team") or {}).get("displayName") or "Team"
        score = team.get("score")
        if isinstance(score,dict): score = score.get("displayValue") or score.get("value")
        scores.append(f"{title} {score if score is not None else '—'}")
    result = {
        "checked_at":utcnow(), "provider":"ESPN public web summary (third party)",
        "score":" · ".join(scores),"state":status_type.get("state", "unknown"),
        "period":status.get("period"), "detail":status_type.get("shortDetail") or status_type.get("detail") or "",
        "value":None,"progress":"Player progress not available from source for this exact market",
        "player_stat_freshness":{"state":"UNAVAILABLE","can_refresh_probability":False,
            "reason":"No independent per-player upstream statistic timestamp verified"},
        "settlement":"UNVERIFIED", "probability":None,
    }
    # Only explicit provider update fields can establish freshness. Most public
    # ESPN summary responses do not expose an authenticated publication time.
    # Never confuse a new HTTP response with new player statistics.
    raw_updated=payload.get('lastUpdated') or payload.get('updatedAt')
    result['freshness']=freshness_state(provider_updated_at=raw_updated,
                          retrieved_at=result['checked_at'],max_age_seconds=180)
    result['provider_updated_at']=raw_updated
    result['score_freshness']=result['freshness']
    result['probability']=None
    if not selection.athlete_id or selection.market not in LABELS:
        return result
    for roster in (payload.get("boxscore") or {}).get("players") or []:
        for block in roster.get("statistics") or []:
            category = str(block.get("name") or block.get("displayName") or "").lower()
            expected = CATEGORIES.get(selection.market)
            if expected and expected not in category:
                continue
            labels = block.get("labels") or []
            key = LABELS[selection.market]
            if key not in labels:
                continue
            index = labels.index(key)
            for entry in block.get("athletes") or []:
                athlete = entry.get("athlete") or {}
                if str(athlete.get("id", "")) != selection.athlete_id:
                    continue
                stats = entry.get("stats") or []
                if index >= len(stats):
                    continue
                try: value = float(stats[index])
                except (ValueError,TypeError): continue
                result["value"] = value
                # Team scoreboard publication and a player's last stat update
                # are independent facts. Use the player field only if upstream
                # explicitly supplies an unambiguous per-stat timestamp.
                field_updated=(entry.get('statisticsUpdatedAt') or block.get('statisticsUpdatedAt'))
                result['player_stat_freshness']=freshness_state(
                    provider_updated_at=field_updated,retrieved_at=result['checked_at'],
                    max_age_seconds=180)
                if selection.threshold is not None:
                    result["progress"] = f"Observed {value:g} toward the exact {selection.threshold:g} threshold; this is not a hit probability or official settlement."
                else:
                    result["progress"] = f"Observed {value:g} (not a moneyline result)"
                return result
    return result


def fetch_live(selection: Selection) -> tuple[dict,str]:
    if not selection.game_id.isdigit():
        raise ValueError("A verified ESPN numeric game ID is necessary for observed live data")
    payload, source_url = summary(selection.sport, selection.game_id, refresh=True)
    report=observed_from_summary(selection,payload)
    if selection.sport=='NBA' and selection.game_label.count(' @ ')==1:
        try:
            from bta.sources.nba_scoreboard import observed_nba_scoreboard
            away,home=selection.game_label.split(' @ ',1)
            league=observed_nba_scoreboard(home=home,away=away)
            report['official_scoreboard']=league
            report['score_crosscheck_state']='OFFICIAL_OBSERVED' if league.get('state')=='OBSERVED_SCOREBOARD' else 'OFFICIAL_UNAVAILABLE'
            # Don't overwrite the third-party player box-score observation:
            # a scoreboard observation is not evidence of athlete statistics.
        except Exception as exc:
            report['score_crosscheck_state']='OFFICIAL_UNAVAILABLE'
    return report, source_url
