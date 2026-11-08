"""Opponent-side factual snapshot. Not a qualified moneyline forecast."""
from __future__ import annotations
from datetime import datetime, timezone
from statistics import mean
from bta.sources.espn import team_schedule, SourceError


def season_for(sport: str, iso: str) -> int:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        dt = datetime.now(timezone.utc)
    if sport == "NBA": return dt.year + (1 if dt.month >= 8 else 0)
    if sport in {"NFL","CFB"} and dt.month <= 2: return dt.year-1
    return dt.year


def side_by_side(sport: str, away_id: str, home_id: str, game_start: str) -> dict:
    season = season_for(sport,game_start)
    result = {"season": season, "teams": [], "warnings": []}
    for name,team_id in (("Away",away_id),("Home",home_id)):
        if not team_id or not team_id.isdigit():
            result["warnings"].append(f"{name}: verified team ID unavailable")
            continue
        try:
            rows, url = team_schedule(sport,team_id,season)
            # Chronological pregame cutoff: exclude the selected game's start and later.
            rows = [r for r in rows if not game_start or r["date"] < game_start]
            sample = rows[:8]
            result["teams"].append({"side":name,"games":len(sample),
                "wins":sum(x["result"]=="W" for x in sample),
                "avg_margin":round(mean(x["margin"] for x in sample),1) if sample else None,
                "rows":sample,"source_url":url})
        except SourceError as exc:
            result["warnings"].append(f"{name} team feed unavailable: {exc}")
    result["limits"] = "Descriptive recent scores only. Does not adjust for opponent quality, QB injuries, line play, turnovers, venue or current line. No moneyline grade can be based on this alone."
    return result
