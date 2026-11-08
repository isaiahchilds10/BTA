"""League-controlled NBA live scoreboard adapter.

Reads published JSON with an exact two-team identity match, and exposes
upstream publication time separately from fetch time. Does not map player IDs
or imply up-to-the-second stat availability. Licensing/deployment verification
required before wider member redistribution.
"""
from __future__ import annotations
from datetime import datetime, timezone
from functools import lru_cache
import requests
from bta.domain import utcnow
from bta.research.gates import timestamp
from bta.research.freshness import freshness_state

URL='https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json'


def _team_name(team:dict)->str:
    return ' '.join(str(team.get(k) or '').strip() for k in ('teamCity','teamName')).strip()


def match_nba_scoreboard(payload:dict,*,home:str,away:str,now:str|None=None)->dict:
    """No fuzzy team joins, no fabricated clock, no guessed publication zone."""
    base={'state':'UNAVAILABLE','source_url':URL,'checked_at':now or utcnow(),
          'reason':'No unique NBA league scoreboard entry for selected matchup',
          'player_stats_current':False}
    board=payload.get('scoreboard') or {}
    games=board.get('games') or []
    if not isinstance(games,list):return base
    names=lambda x:' '.join(str(x).casefold().split())
    matched=[g for g in games if names(_team_name(g.get('homeTeam') or {}))==names(home)
             and names(_team_name(g.get('awayTeam') or {}))==names(away)]
    if len(matched)!=1:return base
    g=matched[0]; meta=payload.get('meta') or {}
    updated=str(meta.get('time') or '')
    # Some NBA payload versions expose meta.time without a timezone offset.
    # Such values cannot safely prove UTC freshness.
    if updated and not (updated.endswith('Z') or '+' in updated[10:] or '-' in updated[10:]):
        updated=''
    freshness=freshness_state(provider_updated_at=updated,retrieved_at=base['checked_at'],
                              max_age_seconds=180,now=base['checked_at'])
    return {**base,'state':'OBSERVED_SCOREBOARD','source_updated_at':updated or None,
            'freshness':freshness,'game_id':str(g.get('gameId') or ''),
            'period':g.get('period'),'clock':g.get('gameClock'),
            'status':g.get('gameStatusText'),'home_score':(g.get('homeTeam') or {}).get('score'),
            'away_score':(g.get('awayTeam') or {}).get('score'),
            'reason':'League-controlled score/status only; no proof of individual prop-stat freshness'}


@lru_cache(maxsize=6)
def _fetch(bucket:int)->dict:
    del bucket
    resp=requests.get(URL,timeout=10,allow_redirects=False,
                      headers={'Accept':'application/json','User-Agent':'BTA 2.0 Sports Research'})
    resp.raise_for_status()
    if len(resp.content)>4_000_000:raise ValueError('NBA scoreboard payload too large')
    data=resp.json()
    if not isinstance(data,dict) or not isinstance((data.get('scoreboard') or {}).get('games'),list):
        raise ValueError('Unexpected league scoreboard structure')
    return data


def observed_nba_scoreboard(*,home:str,away:str)->dict:
    from time import time
    try:
        return match_nba_scoreboard(_fetch(int(time()//120)),home=home,away=away)
    except (requests.RequestException,ValueError) as exc:
        return {'state':'UNAVAILABLE','source_url':URL,'checked_at':utcnow(),
                'reason':f'League scoreboard unavailable ({type(exc).__name__})',
                'player_stats_current':False}
