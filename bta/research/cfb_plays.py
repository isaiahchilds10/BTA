"""Historical CFB adverse-game situations from real timestamped CFBD plays.

Summary evidence supplements, never replaces, QB/availability and bookmaker
verification. No claim that a selected favorite was favored in past games.
"""
from __future__ import annotations
from collections import defaultdict
from bta.research.gates import timestamp
from bta.sources.cfbd import name_key, get, CFBDError


def _score_for(row:dict, team:str):
    """CFBD play scores are offense/defense-relative, not home/away."""
    if name_key(row.get('offense'))==name_key(team):
        own=row.get('offenseScore'); opponent=row.get('defenseScore')
    elif name_key(row.get('defense'))==name_key(team):
        own=row.get('defenseScore'); opponent=row.get('offenseScore')
    else:return None
    if isinstance(own,bool) or isinstance(opponent,bool) or not isinstance(own,(int,float)) or not isinstance(opponent,(int,float)):
        return None
    return float(own),float(opponent)


def cfb_historical_adversity(plays:list[dict], *,team:str, allowed_completed_game_ids:set[str],
                             as_of:str,minimum_games:int=3)->dict:
    """Describe actual first-half deficits and one-possession fourth quarters."""
    cutoff=timestamp(as_of)
    base={'state':'INSUFFICIENT','games':0,'early_deficit_10':{'games':0,'comeback_wins':0},
          'fourth_quarter_one_score':{'games':0,'wins':0},
          'reason':'Need source-linked completed historic plays and final results'}
    if not cutoff or not allowed_completed_game_ids or not team:return base
    grouped=defaultdict(list)
    for p in plays:
        gid=str(p.get('gameId') or '')
        if gid not in allowed_completed_game_ids:continue
        at=timestamp(p.get('wallclock') or '')
        if at is None or at>=cutoff:continue
        score=_score_for(p,team)
        if score is None:continue
        period=p.get('period')
        if isinstance(period,bool) or not isinstance(period,int) or period<1 or period>5:continue
        grouped[gid].append((at,period,score[0],score[1]))
    if len(grouped)<minimum_games:
        return {**base,'games':len(grouped),'reason':'Fewer than required distinct fully linked games with time-ordered plays'}
    early_n=early_w=close_n=close_w=0
    details=[]
    for gid,events in grouped.items():
        events.sort(key=lambda x:x[0])
        # CFBD play data may omit end-of-game plays; require a fourth-quarter
        # observation but still do not assert a game was officially final.
        q4=[e for e in events if e[1]>=4]
        if not q4:continue
        # Record final score only as observed at last included play. Caller must
        # link to a verified completed game to validate it independently.
        final=q4[-1]; won=final[2]>final[3]
        early=any(e[3]-e[2]>=10 and e[1]<=2 for e in events)
        close=any(abs(e[2]-e[3])<=8 for e in q4)
        early_n+=int(early);early_w+=int(early and won)
        close_n+=int(close);close_w+=int(close and won)
        details.append({'game_id':gid,'early_down_10':early,'close_in_fourth':close,
                        'last_observed_winner':bool(won),
                        'interpretation':'Descriptive observed historical condition, not a calibrated future probability'})
    return {'state':'OBSERVED' if len(details)>=minimum_games else 'INSUFFICIENT',
            'games':len(details),
            'early_deficit_10':{'games':early_n,'comeback_wins':early_w},
            'fourth_quarter_one_score':{'games':close_n,'wins':close_w},
            'evidence':details,
            'reason':'Actual source play chronology; requires verified finished-game cross-check. No pregame favorite inference.'}


def historical_cfb_plays_for_team(team:str,season:int,weeks:list[int],api_key:str,*,max_weeks:int=4)->dict:
    """Budgeted request helper. Call only for a high-priority active ticket."""
    if not api_key:return {'state':'UNAVAILABLE','reason':'CFBD key not configured','plays':[]}
    usable=sorted({w for w in weeks if isinstance(w,int) and 1<=w<=16},reverse=True)[:max_weeks]
    result=[]; sources=[]
    for week in usable:
        try:
            plays,url=get('/plays',{'year':season,'week':week,'team':team,'classification':'fbs'},api_key)
            if len(plays)>20000:raise CFBDError('Unexpectedly large play response')
            result.extend(plays);sources.append(url)
        except CFBDError as exc:
            return {'state':'PARTIAL' if result else 'UNAVAILABLE',
                    'reason':str(exc),'plays':result,'sources':sources}
    return {'state':'HISTORICAL_PLAYS','plays':result,'sources':sources,
            'reason':'Play-by-play supplied as historical context; provider availability and licensing subject to testing'}
