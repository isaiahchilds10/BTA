"""Football-specific injury and matchup audit, distinct from NBA scripts.

A descriptive sports-data observation is never a substitute for confirmed QB
availability, verified historical prices, official inactive lists, or a full
trench matchup. CFB adverse scripts are evaluated as hypotheses with explicit
source-backed observations and unresolved mechanisms.
"""
from __future__ import annotations
from bta.domain import CFB_SCRIPTS
from bta.research.participation import reconcile_participation
from bta.sources.cfb_availability import CONFERENCES, availability_source_plan


def cfb_stress_audit(matchup:dict|None)->list[dict]:
    m=matchup or {}
    home,away=tuple((m.get('teams') or {}).values())[:2] if len(m.get('teams') or {})>=2 else ({},{})
    ready=bool(m.get('fixture_verified') and home.get('state')=='OBSERVED' and away.get('state')=='OBSERVED'
               and home.get('sample',0)>=5 and away.get('sample',0)>=5)
    home_ppg=home.get('points_for')
    away_ppg=away.get('points_for')
    home_yp=home.get('yards_per_play')
    away_yp=away.get('yards_per_play')
    home_to=home.get('turnovers')
    away_to=away.get('turnovers')
    home_opp=home.get('opponent_other_games_win_rate')
    away_opp=away.get('opponent_other_games_win_rate')
    stat_ref=', '.join(x for x in m.get('sources',[]) if isinstance(x,str))
    notes=[
        (f"Pre-cutoff team scoring: home {home_ppg}, away {away_ppg}; historical yards/play: home {home_yp}, away {away_yp}. Opponents' other-game win fractions: home {home_opp}, away {away_opp}; this is descriptive, NOT a validated SOS or QB/trench adjustment."),
        ('Underdog 10–0/14–0 start: documented historical offense/defense can inform comeback plausibility, but quarterback passing under pressure and down/distance response remain unverified.'),
        (f"Favorite -2 turnovers: observed unadjusted turnovers per game home {home_to}, away {away_to}. A two-possession reversal must not be converted into a calibrated win chance."),
        ('Primary strength neutralized: player-specific quarterback, running game, line efficiency and opponent run/pass response are not fully verified; do not assume balanced fallback.'),
        ('One-score fourth quarter: aggregated results cannot establish actual one-possession closing drives, kicker reliability, coaching decisions or 4Q quarterback performance.'),
    ]
    return [{'scenario':script,
             'verdict':'NOT_ASSESSED',
             'evidence_status':'PARTIAL' if ready else 'INSUFFICIENT',
             'mechanism':(notes[i] if ready else 'Insufficient verified pre-cutoff FBS team data for this script. '+notes[i]),
             'source':stat_ref,'required_to_verify':{
                 0:'QB identity, opponent adjustment and line matchup',
                 1:'QB comeback/pressure and opponent defensive response',
                 2:'Scoring resiliency under lost possessions and special teams',
                 3:'Specific weapon-versus-defense unit matchups',
                 4:'Verified fourth-quarter play-level closing performance',
             }[i]} for i,script in enumerate(CFB_SCRIPTS)]


def football_market_evidence(selection,fixture_context:dict,*,cfbd_key:str='')->dict:
    """Report NFL/CFB contextual research, without overriding qualification gates."""
    if selection.sport=='NFL':
        from bta.sources.nfl_injuries import nfl_injury_observation
        from bta.sources.nfl_official import official_nfl_observation
        team_id=fixture_context.get('athlete_team_id')
        abbr=''
        for side,tid in (fixture_context.get('team_ids') or {}).items():
            if tid==team_id:
                abbr=(fixture_context.get('team_abbreviations') or {}).get(side,'')
        week=fixture_context.get('week')
        from bta.research.matchup import season_for
        full_team_name=''
        for side,tid in (fixture_context.get('team_ids') or {}).items():
            if tid==team_id:
                full_team_name=(fixture_context.get('team_names') or {}).get(side,'')
        season=season_for('NFL',selection.game_start)
        official=(official_nfl_observation(selection.subject,full_team_name,season,week)
                  if full_team_name else {'state':'UNAVAILABLE','reason':'Fixture team name missing'})
        from bta.sources.nfl_editorial import nfl_editorial_observation
        editorial=(nfl_editorial_observation(player=selection.subject,
              team_nickname=full_team_name.split()[-1],week=week,season=season)
              if full_team_name and week else {'state':'UNAVAILABLE','reason':'No verified NFL team/week'})
        secondary=nfl_injury_observation(selection.subject,abbr,season,week)
        # The NFL webpage usually lacks a machine-readable original published_at
        # for each row; retrieving it now does NOT establish when it was first
        # available. Nor does week+team identify the exact fixture on its own.
        official_obs=[]
        if official.get('official_verification') and official.get('published_at') and official.get('game_id_verified'):
            official_obs.append({'status':official.get('status'),'source_class':'OFFICIAL_LEAGUE',
                'source_url':official.get('source_url'),'published_at':official.get('published_at'),
                'game_id_verified':True})
        status=reconcile_participation(official_obs,game_start=selection.game_start)
        return {'sport':'NFL','official_injury':official,
                'injury':secondary,'editorial_injury':editorial,
                'participation_reconciliation':status,
                'notes':['NFL injury transcription is not independent official verification',
                         'Official game-status/inactive check and stable opportunity are required for certification']}
    if selection.sport=='CFB':
        from bta.sources.cfbd import cfb_matchup_evidence
        locations=fixture_context.get('team_locations') or {}
        if selection.market=='moneyline' and locations.get('home') and locations.get('away'):
            report=cfb_matchup_evidence(locations['home'],locations['away'],selection.game_start,cfbd_key)
            # Publish official conference report hubs as *source leads* only, not
            # verified individual availability; they require exact fixture and
            # published-status joins before the participation gate can pass.
            same_conference=(str(report.get('home_conference') or '').casefold()==
                             str(report.get('away_conference') or '').casefold() and
                             bool(report.get('home_conference')))
            conf_aliases={'B1G':'BIG TEN','BIG TEN':'BIG TEN','SEC':'SEC','ACC':'ACC'}
            active_conf=conf_aliases.get(str(report.get('home_conference') or '').upper()) if same_conference else None
            hubs={name:availability_source_plan(name,is_conference_game=(name==active_conf))
                  for name in CONFERENCES}
            play_context={'state':'NOT_REQUESTED','reason':'Play-by-play fetch budgeted to priority moneyline investigations'}
            try:
                from bta.config import setting
                from bta.research.cfb_plays import historical_cfb_plays_for_team,cfb_historical_adversity
                weeks=int(setting('CFBD_PLAY_WEEKS') or '0')
                wk=fixture_context.get('week')
                if cfbd_key and 0<weeks<=4 and isinstance(wk,int) and 2<=wk<=16 and report.get('fixture_verified'):
                    samples={}
                    for side,team in (('home',locations['home']),('away',locations['away'])):
                        prior=(report.get('teams') or {}).get(team,{}).get('games',[])
                        allowed={str(x.get('game_id')) for x in prior if x.get('game_id')}
                        fetched=historical_cfb_plays_for_team(team,int(selection.game_start[:4]),
                            list(range(max(1,wk-weeks),wk)),cfbd_key,max_weeks=weeks)
                        samples[side]={'status':fetched['state'],'sources':fetched.get('sources',[]),
                            'adversity':cfb_historical_adversity(fetched.get('plays',[]),team=team,
                                    allowed_completed_game_ids=allowed,as_of=selection.game_start)}
                    play_context={'state':'OBSERVED_SAMPLES','teams':samples}
            except (ValueError,TypeError,KeyError) as exc:
                play_context={'state':'UNAVAILABLE','reason':f'Play-by-play context unavailable ({type(exc).__name__})'}
            selected_side=next((side for side in ('home','away')
                 if locations.get(side,'').casefold()==selection.subject.strip().casefold()),'')
            scenarios=enrich_cfb_script_notes(cfb_stress_audit(report),play_context,selected_side)
            return {'sport':'CFB','matchup':report,'scripts':scenarios,
                    'official_availability_hubs':hubs,'historical_adversity':play_context,
                    'notes':['CFBD free tier does not provide live feeds or all opponent-adjusted metrics',
                             'Quarterback/line/injury confirmation still required before strict moneyline certification']}
        return {'sport':'CFB','notes':['Team locations/fixture missing or player market requires distinct player-level evidence']}
    return {'sport':selection.sport,'notes':[]}



def enrich_cfb_script_notes(scripts:list[dict],play_context:dict,selected_team_side:str)->list[dict]:
    """Explain observed historical adversity without inventing a script verdict."""
    out=[dict(row) for row in scripts]
    sample=(play_context.get('teams') or {}).get(selected_team_side,{})
    seen=sample.get('adversity') or {}
    if seen.get('state')!='OBSERVED' or len(out)!=5:
        return out
    early=seen.get('early_deficit_10') or {}
    close=seen.get('fourth_quarter_one_score') or {}
    out[1]['mechanism'] += (f" Historical same-team play records: {early.get('comeback_wins',0)}/"
                            f"{early.get('games',0)} games with an observed first-half 10+ deficit"
                            ' ended with the team ahead at the last observed play. This does not establish'
                            ' that the opponent was an underdog or that the team would repeat it.')
    out[4]['mechanism'] += (f" Historical same-team play records: {close.get('wins',0)}/"
                            f"{close.get('games',0)} games that were within eight points in the"
                            ' fourth period ended with the team ahead at the last observed play.'
                            ' These are not calibrated scenario probabilities.')
    for i in (1,4):
        out[i]['source'] += ' ' + ', '.join(sample.get('sources') or [])
        out[i]['evidence_status']='PARTIAL'
    return out


def join_nfl_weekly_events(weekly_rows:list[dict],completed_team_games:list[dict])->list[dict]:
    """Cross-source join requires unique observed week AND opposing team code.

    If no exact join exists, weekly stats remain useful for player history but
    cannot be assigned to historical game-script samples.
    """
    from bta.sources.nfl_injuries import nfl_team_code
    games_by_week={}
    for g in completed_team_games:
        week=g.get('week')
        opp=g.get('opponent_abbr')
        if isinstance(week,int) and opp and g.get('event_id') and g.get('date'):
            games_by_week.setdefault(week,[]).append(g)
    result=[]
    for row in weekly_rows:
        peers=[g for g in games_by_week.get(row.get('week'),[])
               if nfl_team_code(g.get('opponent_abbr',''))==nfl_team_code(row.get('opponent',''))]
        if len(peers)==1:
            result.append({**row,'event_id':peers[0]['event_id'],'date':peers[0]['date']})
        else:result.append({**row,'script_join_status':'NOT_JOINED'})
    return result
