"""NFL weekly source-backed volume/history fallback using nflverse CSV.

Matches a real fixture roster and canonical selected team, and excludes weeks
at/after the selected game. nflverse stats are THIRD-PARTY, postgame revised,
not certified as point-in-time historical pregame snapshots.
"""
from __future__ import annotations
from csv import DictReader
from datetime import datetime,timezone
from functools import lru_cache
from io import StringIO
from urllib.parse import urlparse
import requests
from bta.sources.nfl_injuries import normalized,nfl_team_code

URL_TEMPLATE='https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv'
MAX_BYTES=45_000_000
SUPPORTED={'passing_yards':'passing_yards','passing_touchdowns':'passing_tds',
           'passing_attempts':'attempts','completions':'completions',
           'rushing_yards':'rushing_yards','rushing_attempts':'carries',
           'receptions':'receptions','receiving_yards':'receiving_yards',
           'rushing_receiving_yards':None}

class NFLWeeklyError(RuntimeError):pass


@lru_cache(maxsize=5)
def _weekly_csv(season:int,bucket:int)->tuple[list[dict],str]:
    del bucket
    if not 2000<=season<=2100:raise NFLWeeklyError('Unsupported season')
    url=URL_TEMPLATE.format(season=season)
    try:
        response=requests.get(url,headers={'User-Agent':'BTA sports research/2.0','Accept':'text/csv'},
                              timeout=20,stream=True,allow_redirects=True)
        response.raise_for_status()
        if urlparse(response.url).scheme!='https' or urlparse(response.url).hostname not in {
                'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}:
            raise NFLWeeklyError('Unapproved CSV redirect')
        content=bytearray()
        for block in response.iter_content(65_536):
            content.extend(block)
            if len(content)>MAX_BYTES:raise NFLWeeklyError('Weekly stats release too large')
        records=list(DictReader(StringIO(content.decode('utf-8-sig'))))
        required={'week','season','player_display_name','recent_team','position'}
        if not records or not required.issubset(records[0]):
            raise NFLWeeklyError('Weekly stats release schema mismatch')
        return records,url
    except (requests.RequestException,UnicodeError) as exc:
        raise NFLWeeklyError(f'NFL weekly stats unavailable ({type(exc).__name__})') from exc


def _safe_number(value):
    try:
        if value is None or str(value).strip()=='':return None
        n=float(value)
        if not -10000<n<100000:return None
        return n
    except (TypeError,ValueError):return None


def nfl_weekly_observations(subject:str,team_abbr:str,market:str,season:int,
                            upcoming_week:int|None, *,snapshot_rows:list[dict]|None=None)->dict:
    base={'state':'UNAVAILABLE','rows':[],'source_url':'','sample':0,
          'reason':'No exact, dated NFL weekly player observations'}
    if market not in SUPPORTED or not team_abbr or not isinstance(upcoming_week,int) or isinstance(upcoming_week,bool):
        return {**base,'reason':'Exact NFL market, team and game week required'}
    if snapshot_rows is None:
        try:
            from time import time
            records,url=_weekly_csv(season,int(time()//3600))
        except NFLWeeklyError as exc:return {**base,'reason':str(exc)}
    else:records,url=snapshot_rows,URL_TEMPLATE.format(season=season)
    filtered=[]
    for row in records:
        try:
            if int(row.get('season') or -1)!=season:continue
            week=int(row.get('week') or -1)
            if not 1<=week<upcoming_week:continue
        except (ValueError,TypeError):continue
        if normalized(row.get('player_display_name'))!=normalized(subject):continue
        if nfl_team_code(row.get('recent_team',''))!=nfl_team_code(team_abbr):continue
        filtered.append((week,row))
    if not filtered:return {**base,'source_url':url,'reason':'No exact historical player/team/week rows'}
    identities={r.get('player_id') for _,r in filtered if r.get('player_id')}
    if len(identities)!=1:
        return {**base,'source_url':url,'reason':'Player ID missing or ambiguous in matched weekly release rows'}
    result=[];seen=set()
    for week,row in sorted(filtered,key=lambda x:x[0],reverse=True):
        if week in seen:continue
        seen.add(week)
        if market=='rushing_receiving_yards':
            rush=_safe_number(row.get('rushing_yards'))
            recv=_safe_number(row.get('receiving_yards'))
            value=rush+recv if rush is not None and recv is not None else None
        else:
            value=_safe_number(row.get(SUPPORTED[market]))
        if value is None:continue
        item={'week':week,'date':f'{season}-W{week:02d}',
              'opponent':row.get('opponent_team') or 'Unknown',
              'value':value,'player_id':next(iter(identities)),
              'source_kind':'nflverse_weekly'}
        volume_field={'passing_yards':'attempts','passing_touchdowns':'attempts',
                      'completions':'attempts','passing_attempts':'attempts',
                      'rushing_yards':'carries','rushing_attempts':'carries',
                      'receiving_yards':'targets','receptions':'targets'}.get(market)
        if volume_field:
            volume=_safe_number(row.get(volume_field))
            if volume is not None:
                item['attempts' if volume_field in ('attempts','carries') else 'targets']=volume
        result.append(item)
    return {'state':'HISTORICAL_WEEKLY_RESEARCH' if result else 'INCOMPLETE',
            'source_url':url,'rows':result,'sample':len(result),
            'reason':'Third-party updated weekly game aggregates, NOT a frozen pregame snapshot or official injury report'}
