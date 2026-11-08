"""CollegeFootballData free-tier, date-cutoff-aware FBS matchup evidence.

Only basic documented free endpoints are used. This adapter does NOT access
paid advanced adjustment, live-score, or QB status endpoints. Published
current-season statistics cannot be used to backfill a historical pregame pick.
"""
from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from statistics import mean
from urllib.parse import urlencode
import requests

from bta.research.gates import timestamp
from bta.domain import utcnow

BASE='https://api.collegefootballdata.com'
PERMITTED={'/games','/games/teams','/plays'}

class CFBDError(RuntimeError):
    pass


def name_key(value: object) -> str:
    return ' '.join(str(value or '').casefold().replace('&',' and ').replace('.', '').replace("'",'').split())


def _as_number(value):
    if value is None or isinstance(value,bool):return None
    try:return float(value)
    except (TypeError,ValueError):return None


@lru_cache(maxsize=256)
def _cached(path: str, parameters: tuple[tuple[str,str],...], key: str, bucket: int) -> list[dict]:
    del bucket
    if path not in PERMITTED:raise CFBDError('Unsupported endpoint')
    url=BASE+path+'?'+urlencode(parameters)
    try:
        r=requests.get(url,headers={'Authorization':'Bearer '+key,
             'Accept':'application/json','User-Agent':'BTA2.0 research/1'},
             timeout=16,allow_redirects=False)
        if r.status_code in (401,403,429):
            raise CFBDError(f'CFBD authentication/entitlement/quota rejection HTTP {r.status_code}')
        r.raise_for_status()
        if len(r.content)>8_000_000:raise CFBDError('CFBD oversized response')
        result=r.json()
        if not isinstance(result,list):raise CFBDError('Unexpected CFBD schema')
        return result
    except (requests.RequestException,ValueError) as exc:
        raise CFBDError(f'CFBD data unavailable ({type(exc).__name__})') from exc


def get(path:str, params:dict[str,str|int], api_key:str)->tuple[list[dict],str]:
    if not api_key:return [],''
    from time import time
    parameters=tuple(sorted((k,str(v)) for k,v in params.items()))
    url=BASE+path+'?'+urlencode(parameters)
    return _cached(path,parameters,api_key,int(time()//3600)),url


def _date(value:object):
    return timestamp(str(value or ''))


def match_fixture(games:list[dict],home:str,away:str,kickoff:str)->dict|None:
    """Strict double-sided fixture matching; no fuzzy mascots/abbreviation joins."""
    target=_date(kickoff)
    if target is None:return None
    matched=[]
    for row in games:
        if not isinstance(row,dict):continue
        if name_key(row.get('homeTeam'))!=name_key(home) or name_key(row.get('awayTeam'))!=name_key(away):continue
        start=_date(row.get('startDate'))
        if start and abs((start-target).total_seconds())<=12*3600:
            matched.append(row)
    return matched[0] if len(matched)==1 else None


def game_stat_values(row:dict)->dict[str,float]:
    raw={str(s.get('category') or '').casefold():s.get('stat') for s in row.get('stats',[]) if isinstance(s,dict)}
    field_names={'totalYards':'totalyards','totalPlays':'totalplays','rushingYards':'rushingyards',
                 'passingYards':'passingyards','turnovers':'turnovers',
                 'sacks':'sacks','interceptions':'interceptions','fumblesLost':'fumbleslost'}
    result={}
    for dest,src in field_names.items():
        number=_as_number(raw.get(src))
        if number is not None and number>=0:result[dest]=number
    if result.get('totalPlays',0)>0 and 'totalYards' in result:
        result['yardsPerPlay']=round(result['totalYards']/result['totalPlays'],3)
    return result


def historic_team_profile(name:str, games:list[dict], boxes:list[dict], cutoff:str, limit:int=8)->dict:
    end=_date(cutoff)
    if end is None:return {'state':'INCOMPLETE','reason':'Missing dated kickoff'}
    relevant=[]
    for g in games:
        if name_key(name) not in (name_key(g.get('homeTeam')),name_key(g.get('awayTeam'))):continue
        kickoff=_date(g.get('startDate'))
        if kickoff is None or kickoff>=end:continue
        home_side=name_key(name)==name_key(g.get('homeTeam'))
        own=_as_number(g.get('homePoints') if home_side else g.get('awayPoints'))
        other=_as_number(g.get('awayPoints') if home_side else g.get('homePoints'))
        if own is None or other is None:continue
        relevant.append((kickoff,g,own,other))
    relevant.sort(key=lambda x:x[0],reverse=True)
    by_id={str(b.get('id')):b for b in boxes if isinstance(b,dict) and b.get('id') is not None}
    records=[]
    for start,g,own,other in relevant[:limit]:
        game_id=str(g.get('id') or '')
        peers=[p for p in (by_id.get(game_id,{}).get('teams') or []) if name_key(p.get('team'))==name_key(name)]
        metrics=game_stat_values(peers[0]) if len(peers)==1 else {}
        opponent=g.get('awayTeam') if name_key(name)==name_key(g.get('homeTeam')) else g.get('homeTeam')
        # Straightforward schedule-quality context, not an advanced opponent-
        # adjusted rating. Exclude the player's own H2H game from the opponent's
        # record to avoid baking this performance into its own quality measure.
        other_results=[]
        for prior in games:
            if str(prior.get('id'))==game_id:continue
            prior_time=_date(prior.get('startDate'))
            if prior_time is None or prior_time>=end:continue
            opp_home=name_key(prior.get('homeTeam'))==name_key(opponent)
            opp_away=name_key(prior.get('awayTeam'))==name_key(opponent)
            if not opp_home and not opp_away:continue
            ps=_as_number(prior.get('homePoints') if opp_home else prior.get('awayPoints'))
            po=_as_number(prior.get('awayPoints') if opp_home else prior.get('homePoints'))
            if ps is not None and po is not None and ps!=po:
                other_results.append(1 if ps>po else 0)
        opponents_pct=round(mean(other_results),3) if len(other_results)>=3 else None
        records.append({'game_id':game_id,'date':start.isoformat(),
                        'opponent':opponent,'opponent_other_games_win_rate':opponents_pct,
                        'points_for':own,'points_against':other,'margin':own-other,'metrics':metrics})
    if not records:return {'state':'INCOMPLETE','reason':'No verified pre-cutoff completed games','games':[]}
    def average(field:str):
        numbers=[r['metrics'][field] for r in records if field in r['metrics']]
        return round(mean(numbers),3) if len(numbers)>=min(5,len(records)) else None
    quality=[r['opponent_other_games_win_rate'] for r in records
             if r.get('opponent_other_games_win_rate') is not None]
    return {'state':'OBSERVED','sample':len(records),'games':records,
            'opponents_observed':len(quality),
            'opponent_other_games_win_rate':round(mean(quality),3) if len(quality)>=4 else None,
            'points_for':round(mean(r['points_for'] for r in records),2),
            'points_against':round(mean(r['points_against'] for r in records),2),
            'margin':round(mean(r['margin'] for r in records),2),
            'yards_per_play':average('yardsPerPlay'),
            'rushing_yards':average('rushingYards'),
            'passing_yards':average('passingYards'),
            'turnovers':average('turnovers')}


def cfb_matchup_evidence(home:str,away:str,game_start:str,api_key:str,
                         *,fixture_games:list[dict]|None=None,
                         boxscores:dict[str,list[dict]]|None=None)->dict:
    """CFBD comparison, with independent fixture and chronological identity checks.

    Args marked optional are deterministic test fixtures and do not certify a live
    match (production never sets a grade gate from test-only source injection).
    """
    result={'state':'UNAVAILABLE','checked_at':utcnow(),'provider':'CollegeFootballData (third-party API)',
            'sources':[],'teams':{},'fixture_verified':False,'fbs_verified':False,
            'missing':['Verified FBS fixture, QB availability, line-of-scrimmage and current injury evidence']}
    if not api_key and fixture_games is None:return {**result,'reason':'CFBD_API_KEY not configured (free key available)'}
    kickoff=_date(game_start)
    if kickoff is None:return {**result,'reason':'Game start time missing/invalid'}
    if kickoff<=datetime.now(timezone.utc) and fixture_games is None:
        return {**result,'reason':'Historical/live lookback requires saved pregame snapshots; refuses hindsight reconstruction'}
    season=kickoff.year if kickoff.month>=3 else kickoff.year-1
    try:
        if fixture_games is None:
            schedule,src=get('/games',{'year':season,'classification':'fbs'},api_key)
            result['sources'].append(src)
        else:schedule=fixture_games
        fixture=match_fixture(schedule,home,away,game_start)
        if fixture is None:return {**result,'state':'IDENTITY_PENDING','reason':'No unique dated two-team CFBD fixture match'}
        result['fixture_verified']=True
        result['cfbd_game_id']=fixture.get('id')
        result['home_conference']=str(fixture.get('homeConference') or '')
        result['away_conference']=str(fixture.get('awayConference') or '')
        # Match on classifications only when independently supplied by CFBD;
        # do not assume FBS because the schedule endpoint was filtered.
        home_class=str(fixture.get('homeClassification') or '').lower()
        away_class=str(fixture.get('awayClassification') or '').lower()
        if home_class=='fbs' and away_class=='fbs':result['fbs_verified']=True
        elif home_class=='fcs' or away_class=='fcs':
            return {**result,'state':'FCS_BLOCKED','reason':'FCS matchup excluded under BTA default policy'}
        history=[g for g in schedule if g is not fixture]
        for team in (home,away):
            if boxscores is not None:
                boxes=boxscores.get(team,[])
            else:
                boxes,src=get('/games/teams',{'year':season,'team':team},api_key)
                result['sources'].append(src)
            result['teams'][team]=historic_team_profile(team,history,boxes,game_start)
        result['state']='RESEARCH_AVAILABLE' if all(x['state']=='OBSERVED' for x in result['teams'].values()) else 'PARTIAL'
        result['reason']='Historical pregame performance profiles; no certified QB, trench, or official injury audit'
        return result
    except CFBDError as exc:
        return {**result,'reason':str(exc)}
