"""Acceptance/fault-injection tests for the formerly hard-locked certification path."""
from datetime import datetime,timezone,timedelta
from bta.domain import Selection
from bta.research import engine
from bta.research.gates import role_observation, quote_observation, independent_second_pass
from bta.research.stress import sourced_scripts
from bta.research.opponent import read_nba_boxscore
from bta.sources.nba_official import pdf_row_status,player_key,_latest_link
from bta.sources.house_rules import validate_market_settlement
from bta.sources import house_rules


def nba_selection(**extras):
    s=Selection.new(sport='NBA',game_id='40199',game_label='Houston Rockets @ Phoenix Suns',
        game_start='2026-11-09T02:00:00Z',subject='Sample Player',market='points',
        direction='OVER',threshold=20.5,inclusive=False,athlete_id='99',
        team_role='PG',team_id='7',platform='FanDuel',jurisdiction='OH')
    for k,v in extras.items():setattr(s,k,v)
    return s


def history_rows():
    return [{'event_id':str(n),'date':f'2026-10-{n+1:02d}T02:00:00Z',
         'opponent':'XYZ','value':28+n%5,'minutes':34} for n in range(10)]


def games():
    margins=[16,18,-16,-17,2,-3,4,17,-18,1]
    totals=[210,218,208,205,198,196,212,214,226,225]
    return [{'event_id':str(i),'date':f'2026-10-{i+1:02d}T02:00:00Z',
        'margin':m, 'points_for':(t+m)/2,'points_against':(t-m)/2,
        'result':'W' if m>0 else 'L'} for i,(m,t) in enumerate(zip(margins,totals))]


def test_official_nba_injury_requires_exact_player_game_and_date():
    rows=[['11/08/2026','09:00 (ET)','HOU@PHX','Houston Rockets','Player, Sample','Available','Arm'],
          ['','','','Phoenix Suns','Other, Person','Out','Knee']]
    assert player_key('Player, Sample')==player_key('Sample Player')
    assert pdf_row_status(rows,matchup='HOU@PHX',game_date='11/08/2026',player='Sample Player')['status']=='Available'
    assert pdf_row_status(rows,matchup='ATL@LAL',game_date='11/08/2026',player='Sample Player')['state']=='MATCHUP_NOT_FOUND'
    assert pdf_row_status(rows,matchup='HOU@PHX',game_date='11/09/2026',player='Sample Player')['state']=='MATCHUP_NOT_FOUND'
    assert pdf_row_status(rows,matchup='HOU@PHX',game_date='11/08/2026',player='Missing Player')['state']=='NOT_LISTED'


def test_official_pdf_index_blocks_untrusted_hosts_and_selects_latest():
    h='''<a href="https://evil.example/Injury-Report_2026-11-08_09_45PM.pdf">Evil</a>
          <a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-08_09_30PM.pdf">Good</a>
          <a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-11-08_08_45PM.pdf">Older</a>'''
    url,stamp=_latest_link(h)
    assert url.endswith('09_30PM.pdf') and '2026-11-09' in stamp  # UTC offset


def test_quote_requires_exact_fresh_server_observation():
    s=nba_selection()
    now=datetime.now(timezone.utc)
    quote={'market':'points','direction':'OVER','subject':s.subject,'threshold':20.5,
           'platform':'FanDuel','athlete_id':'99','provider_market_id':'abc','american_odds':-110,
           'market_source_url':'https://sportsgameodds.com/docs/endpoints/getEvents',
           'market_observed_at':now.isoformat()}
    assert quote_observation(s,quote,checked_at=now.isoformat())['state']=='OBSERVED'
    assert quote_observation(s,{**quote,'threshold':30.5},checked_at=now.isoformat())['state']=='UNAVAILABLE'
    assert quote_observation(s,{**quote,'market_observed_at':(now-timedelta(hours=1)).isoformat()},checked_at=now.isoformat())['state']=='UNAVAILABLE'
    assert quote_observation(s,{**quote,'market_source_url':'https://evil.example/x'},checked_at=now.isoformat())['state']=='UNAVAILABLE'


def test_role_is_measured_not_inferred_from_yards():
    s=nba_selection()
    assert role_observation(s,history_rows())['state']=='SUPPORTED'
    assert role_observation(s,[{**r,'minutes':None} for r in history_rows()])['state']=='UNKNOWN'


def test_sourced_nba_scripts_are_real_event_id_joins():
    s=nba_selection()
    labels=sourced_scripts(s,history_rows(),games(),'https://site.api.espn.com/test')
    assert len(labels)==5
    assert all(v['evidence_status']=='VERIFIED' for v in labels)
    assert all(v['sample']>=3 for v in labels)
    disconnected=sourced_scripts(s,history_rows(),[{**r,'event_id':f'wrong-{i}'} for i,r in enumerate(games())],'https://site.api.espn.com/test')
    assert all(v['verdict']=='NOT_ASSESSED' for v in disconnected)


def test_nfl_favorite_script_not_inferred_from_final_score():
    s=nba_selection(sport='NFL',market='receiving_yards',direction='OVER',team_role='WR')
    out=sourced_scripts(s,history_rows(),games(),'https://site.api.espn.com/test')
    assert out[0]['verdict']==out[1]['verdict']=='NOT_ASSESSED'


def test_opponent_boxscore_requires_matching_position_and_opposing_team():
    summary={'boxscore':{'players':[
      {'team':{'id':'5'},'statistics':[{'labels':['MIN','PTS','REB','AST'],
        'athletes':[{'athlete':{'displayName':'Sample Guy','position':{'abbreviation':'PG'}},'stats':['35','27','4','7']},
                    {'athlete':{'displayName':'Center','position':{'abbreviation':'C'}},'stats':['29','21','12','1']}]}]},
      {'team':{'id':'6'},'statistics':[{'labels':['MIN','PTS','REB','AST'],
        'athletes':[{'athlete':{'displayName':'Opponent PG','position':{'abbreviation':'PG'}},'stats':['36','37','8','4']}]}]}
    ]}}
    r=read_nba_boxscore(summary,'6','PG','points')
    assert len(r)==1 and r[0]['value']==27


def test_operator_region_and_terms_are_checked(monkeypatch):
    monkeypatch.setattr(house_rules,'_get_operator_terms',lambda url:'nba player performance markets overtime official')
    s=nba_selection()
    assert validate_market_settlement(s)['state']=='DOCUMENTED_FOR_REGION'
    s.jurisdiction='';assert validate_market_settlement(s)['state']=='NOT_VERIFIED'
    s.jurisdiction='OH';s.platform='DraftKings';assert validate_market_settlement(s)['state']=='NOT_VERIFIED'


def test_no_fabricated_upgrade_from_client_flags(monkeypatch):
    s=nba_selection()
    s.market_verified=True;s.settlement_verified=True
    report=engine.analyze(s,rows_override=history_rows(),source_override='https://site.api.espn.com/fake')
    assert report['grade']=='PENDING VERIFICATION'
    assert not any(item['passed'] for item in report['verification_gates'].values())
    assert report['preliminary_screen']['status']!='STRONG_RESEARCH_CANDIDATE' or report['grade']=='PENDING VERIFICATION'


def test_end_to_end_verified_provider_path_can_now_reach_bta_plus(monkeypatch):
    """A verified-source fixture simulates adapters, not a user-uploaded evidence pack.

    Covers the previous hardlock: gates={} and NOT_ASSESSED scripts no longer forced.
    This is an OFFLINE contract test, not a claim that real providers have passed.
    """
    s=nba_selection()
    context={'status':'THIRD_PARTY_CONTEXT_AVAILABLE','fixture_verified':True,'athlete_id':'99',
      'athlete_team_id':'7','team_ids':{'away':'7','home':'8'},'matchup_code':'HOU@PHX',
      'sources':[],'team_comparison':None,'warnings':[]}
    monkeypatch.setattr(engine,'discover_market_context',lambda selection:context)
    monkeypatch.setattr(engine,'gamelog',lambda *a,**k:({},'https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/99/gamelog'))
    monkeypatch.setattr(engine,'rows_from_gamelog',lambda *a,**k:history_rows())
    monkeypatch.setattr(engine,'team_schedule',lambda *a,**k:(games(),'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/7/schedule'))
    monkeypatch.setattr(engine,'setting',lambda key,default='':'secret' if key=='SPORTSGAMEODDS_API_KEY' else default)
    monkeypatch.setattr(engine,'summary',lambda *a,**k:({'header':{'competitions':[{'competitors':[
       {'homeAway':'home','team':{'displayName':'Phoenix Suns'}},{'homeAway':'away','team':{'displayName':'Houston Rockets'}}]}]}},'https://site.api.espn.com/test'))
    monkeypatch.setattr(engine,'roster',lambda *a,**k:([{'id':'99','name':'Sample Player','position':'PG'}],'https://site.api.espn.com/test'))
    from bta.sources import nba_official, sportsgameodds
    monkeypatch.setattr(nba_official,'current_player_status',lambda *a,**k:{'state':'OFFICIALLY_REPORTED','status':'Available','source_url':'https://ak-static.cms.nba.com/test.pdf'})
    monkeypatch.setattr(sportsgameodds,'observed_game_odds',lambda *a,**k:{'dummy':True})
    monkeypatch.setattr(sportsgameodds,'extract_quotes',lambda *a,**k:[{
         'market':s.market,'direction':s.direction,'subject':s.subject,'threshold':s.threshold,
         'platform':'FanDuel','athlete_id':s.athlete_id,'provider_market_id':'line-key','american_odds':-110,
         'market_source_url':'https://sportsgameodds.com/docs/endpoints/getEvents',
         'market_observed_at':(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()}])
    monkeypatch.setattr(engine,'audit_nba_defense',lambda *a,**k:{'state':'ASSESSED','matchup_label':'FAVORABLE'})
    monkeypatch.setattr(engine,'validate_market_settlement',lambda *a,**k:{'state':'DOCUMENTED_FOR_REGION'})
    report=engine.analyze(s)
    assert report['grade']=='BTA+'
    assert report['status']=='SOURCE-GATED RESEARCH CERTIFIED'
    assert report['independent_audit']['status']=='PASS'
    assert all(x['passed'] for x in report['verification_gates'].values())
    assert len(report['scripts'])==5
    assert report['model_true_probability'] is None


def test_player_3pt_makes_and_nba_combos_are_parsed_from_actual_columns():
    from bta.sources.espn import rows_from_gamelog
    data={'events':{'22':{'gameDate':'2026-10-20T00:00:00Z','opponent':{'abbreviation':'PHX'}}},
      'seasonTypes':[{'categories':[{'name':'general','labels':['MIN','PTS','REB','AST','3PT'],
        'events':[{'eventId':'22','stats':['34:30','22','7','6','4-11']}]}]}]}
    three=rows_from_gamelog(data,'three_pointers_made')
    combo=rows_from_gamelog(data,'points_rebounds_assists')
    assert three[0]['value']==4 and abs(three[0]['minutes']-34.5)<.01
    assert combo[0]['value']==35 and combo[0]['minutes']==34.5


def test_noncertification_of_past_game_even_when_all_mocked_sources_look_good(monkeypatch):
    s=nba_selection(game_start='2026-01-01T02:00:00Z')
    # No current injury or market information can certify a historical pregame
    # forecast constructed at analysis time after this game's tipoff.
    monkeypatch.setattr(engine,'discover_market_context',lambda sel:{'fixture_verified':True,
        'athlete_id':'99','athlete_team_id':'7','team_ids':{'away':'7','home':'8'},'matchup_code':'HOU@PHX'})
    monkeypatch.setattr(engine,'gamelog',lambda *a,**k:({},'https://site.web.api.espn.com/test'))
    monkeypatch.setattr(engine,'rows_from_gamelog',lambda *a,**k:history_rows())
    monkeypatch.setattr(engine,'team_schedule',lambda *a,**k:(games(),'https://site.api.espn.com/test'))
    monkeypatch.setattr(engine,'audit_nba_defense',lambda *a,**k:{'state':'ASSESSED','matchup_label':'FAVORABLE'})
    from bta.sources import nba_official
    monkeypatch.setattr(nba_official,'current_player_status',lambda *a,**k:{'state':'OFFICIALLY_REPORTED','status':'Available'})
    report=engine.analyze(s)
    assert report['grade']=='PENDING VERIFICATION'
    assert report['verification_gates']['provenance']['passed'] is False
