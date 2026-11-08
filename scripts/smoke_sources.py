"""Optional real-network smoke probe to run from actual hosting environment.
It prints objective outcomes rather than claiming fixture counts when feeds are empty.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from bta.sources.espn import scoreboard, SourceError


def run() -> tuple[dict,int]:
    outcome = {"checked_at":datetime.now(timezone.utc).isoformat(),"sources":{}}
    healthy = 0
    for sport in ("NBA","NFL","CFB"):
        try:
            games,url = scoreboard(sport, refresh=True)
            invalid = [g.id for g in games if not g.id.isdigit() or not g.home or not g.away or not g.start_time]
            outcome["sources"][sport] = {"status":"INVALID" if invalid else "FETCHED", "events":len(games), "invalid":invalid[:10], "source_url":url}
            if not invalid: healthy += 1
        except (SourceError,ValueError) as exc:
            outcome["sources"][sport]={"status":"UNAVAILABLE","reason":str(exc)[:200]}
    return outcome, 0 if healthy == 3 else 1

if __name__ == "__main__":
    result,code=run()
    print(json.dumps(result,indent=2))
    sys.exit(code)
