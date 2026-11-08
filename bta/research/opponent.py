"""NBA opponent-vs-position audit built only from real finished boxscores.

This uses observed minutes and position groups in the opponent's recent games,
not a team's raw defensive ranking as a substitute for player matchup data.
It remains descriptive: historical opponents differ in strength and injuries.
"""
from __future__ import annotations
from statistics import median
from bta.domain import Selection
from bta.sources.espn import summary,team_schedule,SourceError
from bta.research.matchup import season_for

ROLE_GROUP={'PG':'G','SG':'G','G':'G','SF':'F','PF':'F','F':'F','C':'C'}
STAT_LABEL={
    'points':('PTS',), 'rebounds':('REB',), 'assists':('AST',),
    'three_pointers_made':('3PT',), 'steals':('STL',),'blocks':('BLK',),
    'points_rebounds_assists':('PTS','REB','AST'),
    'points_rebounds':('PTS','REB'),'points_assists':('PTS','AST'),
    'rebounds_assists':('REB','AST'),'steals_blocks':('STL','BLK'),
}


def read_nba_boxscore(payload:dict, opponent_id:str,position:str,market:str)->list[dict]:
    if not isinstance(payload,dict) or market not in STAT_LABEL:return []
    wanted=ROLE_GROUP.get(position.upper().strip())
    if not wanted:return []
    box=(payload.get('boxscore') or {}).get('players') or []
    if not any(str((team.get('team') or {}).get('id',''))==str(opponent_id) for team in box):
        return [] # Do not treat an unrelated game as data against this defense.
    found=[]
    for team in box:
        if str((team.get('team') or {}).get('id',''))==str(opponent_id):
            continue # We need players who FACED this opponent defense.
        for section in team.get('statistics') or []:
            labels=[str(x).upper().replace(' ','') for x in (section.get('labels') or section.get('names') or [])]
            for a in section.get('athletes') or []:
                ath=a.get('athlete') or {}
                position_data=ath.get('position') or {}
                p=position_data.get('abbreviation','') if isinstance(position_data,dict) else str(position_data)
                if ROLE_GROUP.get(p.upper().strip())!=wanted:continue
                stats=a.get('stats') or []
                if len(labels)!=len(stats):continue
                lookup=dict(zip(labels,stats))
                try:
                    raw_min=str(lookup['MIN'])
                    if ':' in raw_min:
                        minute,seconds=raw_min.split(':',1)
                        minutes=int(minute)+int(seconds)/60
                    else:minutes=float(raw_min)
                    if not 15<=minutes<=60:continue
                    values=[]
                    for label in STAT_LABEL[market]:
                        raw=str(lookup[label]); raw=raw.split('-',1)[0] if label=='3PT' else raw
                        values.append(float(raw.replace(',','')))
                    if any(v<0 for v in values):continue
                except (KeyError,ValueError,TypeError):continue
                found.append({'value':sum(values),'minutes':minutes,'position':p,
                              'player':ath.get('displayName','')})
    return found


def audit_nba_defense(selection:Selection,opponent_id:str,player_rows:list[dict]) -> dict:
    base={'state':'NOT_ASSESSED','source_urls':[],'sample':0,'games':0,
          'reason':'Opponent-vs-position boxscores unavailable or not comparable'}
    if selection.sport!='NBA' or selection.market not in STAT_LABEL or not ROLE_GROUP.get(selection.team_role.upper()):
        return base
    source_rows=[r for r in player_rows[:10] if isinstance(r.get('minutes'),(float,int)) and r['minutes']>=15]
    if len(source_rows)<8:
        return {**base,'reason':'Player game log lacks eight source-backed minutes+stat observations'}
    typical_minutes=median(r['minutes'] for r in source_rows)
    try:
        finished,team_url=team_schedule('NBA',opponent_id,season_for('NBA',selection.game_start))
        finished=[r for r in finished if not selection.game_start or r.get('date','')<selection.game_start][:12]
    except (SourceError,ValueError,TypeError):return base
    sample=[];good_games=0;urls=[team_url]
    for entry in finished:
        try:
            raw,url=summary('NBA',entry['event_id'])
            values=read_nba_boxscore(raw,opponent_id,selection.team_role,selection.market)
            if values:
                good_games+=1;urls.append(url)
                # Normalize opportunity to the player's median minutes; this is an
                # explicit descriptive approximation and NOT a forecast distribution.
                sample.extend(round(v['value']*typical_minutes/v['minutes'],2) for v in values)
        except (SourceError,ValueError,TypeError,KeyError,IndexError):continue
        if good_games>=8:break
    if good_games<6 or len(sample)<10:
        return {**base,'games':good_games,'sample':len(sample),'source_urls':urls,
                'reason':'Insufficient opponent position-matched boxscore sample (6 games/10 player observations minimum)'}
    opp_median=median(sample)
    player_median=median(float(r['value']) for r in source_rows)
    ratio=opp_median/player_median if player_median>0 else None
    if ratio is None:return base
    status='FAVORABLE' if ratio>=.95 else 'ADVERSE' if ratio<.8 else 'MIXED'
    return {'state':'ASSESSED','matchup_label':status,'median_opponent_adjusted':round(opp_median,2),
            'player_median':round(player_median,2),'comparison_ratio':round(ratio,3),
            'typical_minutes':typical_minutes,'sample':len(sample),'games':good_games,
            'source_urls':urls,
            'reason':('Actual recent opponent-allowed position-group boxscores, normalized to player typical minutes. '
                      'Not adjusted for historical opponent talent, scheme changes, or current missing personnel.')}
