from datetime import datetime,timedelta,timezone
from bta.research.participation import reconcile_participation
from bta.sources.cfb_availability import availability_source_plan, extract_conference_report
from bta.research.settlement import resolve_exact_market
from bta.research.cfb_plays import cfb_historical_adversity
from bta.models.validation import audit_chronological_forecasts, probability_display_gate
from bta.domain import Selection

TIP='2026-11-15T20:00:00+00:00'


def _report(status='Available',authority='OFFICIAL_CONFERENCE',published='2026-11-15T17:30:00Z'):
    return {'source_class':authority,'source_url':'https://bigten.org/game/report',
            'status':status,'published_at':published,'game_id_verified':True}


def test_same_game_official_status_and_uncertainty():
    status=reconcile_participation([_report()],game_start=TIP,checked_at='2026-11-15T18:00:00Z')
    assert status['state']=='OFFICIALLY_AVAILABLE' and not status['workload_confirmed']
    conflicting=reconcile_participation([_report('Available'),_report('Out')],game_start=TIP,
                                        checked_at='2026-11-15T18:00:00Z')
    assert conflicting['state']=='CONFLICTING'


def test_primary_overrides_secondary_but_not_future_and_unknown():
    secondary=_report('Out','SECONDARY_TRANSCRIPTION')
    assert reconcile_participation([_report('Questionable'),secondary],game_start=TIP,
           checked_at='2026-11-15T18:00:00Z')['state']=='OFFICIALLY_UNCERTAIN'
    too_late=_report('Available',published='2026-11-16T17:30:00Z')
    assert not reconcile_participation([too_late],game_start=TIP,
           checked_at='2026-11-16T20:00:00Z')['eligible']
    other_game={**_report(),'game_id_verified':False}
    assert not reconcile_participation([other_game],game_start=TIP,
           checked_at='2026-11-15T18:00:00Z')['eligible']


def test_official_hub_is_not_player_clearance():
    plan=availability_source_plan('SEC',is_conference_game=True)
    assert plan['state']=='OFFICIAL_HUB_IDENTIFIED'
    assert availability_source_plan('SEC',is_conference_game=False)['state']=='NO_CONFERENCE_REPORT_ASSUMED'


def test_conference_rows_require_exact_player_fixture_source():
    source='https://bigten.org/game/report'
    html='<h3>Ohio State @ Michigan — 11/15/2026</h3><table><tr><th>Player</th><th>Status</th></tr><tr><td>Test QB</td><td>Out</td></tr></table>'
    args=dict(conference='BIG TEN',fixture_label='Ohio State @ Michigan',player_name='Test QB',
              game_date=TIP,report_published_at='2026-11-15T17:00:00Z',source_url=source)
    ok=extract_conference_report(html,**args)
    assert ok['status']=='OUT' and ok['game_id_verified']
    assert extract_conference_report(html,**{**args,'player_name':'Other QB'})['state']=='UNVERIFIED'
    assert extract_conference_report(html,**{**args,'source_url':'https://example.com/game'})['state']=='UNVERIFIED'


def _selection(market,direction,threshold,inclusive):
    return Selection.new(sport='NFL',game_id='123',game_label='Test @ Other',game_start=TIP,
      subject='Test Player',market=market,direction=direction,threshold=threshold,inclusive=inclusive)


def test_anytime_touchdown_counts_rushing_and_receiving_only():
    sel=_selection('anytime_td','YES',1,True)
    observed={'rushing_touchdowns':0,'receiving_touchdowns':1,
              'passing_touchdowns':4,'td_contract':'RUSH_OR_RECEIVE'}
    args=dict(verified_official_final=True,terms_verified=True,participation_verified=True,
              corrections_closed=True)
    assert resolve_exact_market(sel,observed,**args).result=='HIT'
    assert resolve_exact_market(sel,observed,**{**args,'terms_verified':False}).state=='PENDING'
    assert resolve_exact_market(_selection('anytime_td','NO',1,True),observed,**args).result=='MISS'


def test_any_quarter_rejects_full_game_and_requires_all_four_quarters():
    sel=_selection('quarter_rushing_yards','YES',5,True)
    args=dict(verified_official_final=True,terms_verified=True,participation_verified=True,
              corrections_closed=True)
    assert resolve_exact_market(sel,{'value':150},**args).state=='PENDING'
    quarter={'quarter_contract':'ANY_SINGLE_QUARTER_REGULATION','regulation_quarters':{'1':-1,'2':0,'3':6,'4':-1}}
    assert resolve_exact_market(sel,quarter,**args).result=='HIT'


def test_historical_adversity_never_guesses_game_without_last_quarter():
    plays=[]
    for i in range(3):
        kickoff=datetime(2026,10,2+i,tzinfo=timezone.utc)
        for j,period,own,opp in [(0,1,0,14),(1,2,17,14),(2,4,23,20)]:
            plays.append({'gameId':100+i,'offense':'A','defense':'B','offenseScore':own,
              'defenseScore':opp,'period':period,'wallclock':(kickoff+timedelta(hours=j)).isoformat()})
    result=cfb_historical_adversity(plays,team='A',allowed_completed_game_ids={'100','101','102'},as_of=TIP)
    assert result['state']=='OBSERVED' and result['early_deficit_10']=={'games':3,'comeback_wins':3}
    assert result['fourth_quarter_one_score']['games']==3


def test_validation_rejects_hindsight_and_small_samples():
    r={'sport':'NFL','market':'receiving_yards','model_version':'v1','game_id':'1',
       'exact_market_id':'p1','frozen_snapshot_id':'s1','forecast_at':'2026-11-08T19:00:00Z',
       'last_input_at':'2026-11-08T18:00:00Z','game_start':'2026-11-08T20:00:00Z',
       'result_published_at':'2026-11-09T05:00:00Z','outcome':1,'probability':0.8}
    result=audit_chronological_forecasts([r],sport='NFL',market='receiving_yards',model_version='v1')
    assert result['status']=='MODEL_UNDER_TEST' and not result['validated_probability']
    bad={**r,'last_input_at':'2026-11-09T01:00:00Z'}
    assert audit_chronological_forecasts([bad],sport='NFL',market='receiving_yards',model_version='v1')['invalid_records']==1
    assert not probability_display_gate(audit=result,externally_approved=True,fresh=True,
                                        exact_model_match=True,provider_lineage_verified=True)['show_numeric_probability']


def test_nfl_official_parser_nickname_headings():
    from bta.sources.nfl_official import parse_official_nfl_html
    html='<h1>Injuries - WEEK 10</h1><h3>Bears</h3><table><tr><th>Player</th><th>Game Status</th></tr><tr><td>Test Receiver</td><td>Questionable</td></tr></table>'
    data=parse_official_nfl_html(html,player='Test Receiver',team_name='Chicago Bears',season=2026,week=10)
    assert data['state']=='OFFICIALLY_DESIGNATED'


def test_official_nba_scoreboard_does_not_certify_player_stat_freshness():
    from bta.sources.nba_scoreboard import match_nba_scoreboard
    payload={'meta':{'time':'2026-11-15T18:00:00Z'},'scoreboard':{'games':[
       {'gameId':'0022600001','gameStatusText':'Q2',
        'homeTeam':{'teamCity':'Phoenix','teamName':'Suns','score':41},
        'awayTeam':{'teamCity':'Houston','teamName':'Rockets','score':43}}]}}
    found=match_nba_scoreboard(payload,home='Phoenix Suns',away='Houston Rockets',
        now='2026-11-15T18:01:00Z')
    assert found['state']=='OBSERVED_SCOREBOARD' and found['freshness']['state']=='CURRENT'
    assert not found['player_stats_current']
    assert match_nba_scoreboard(payload,home='Houston Rockets',away='Phoenix Suns')['state']=='UNAVAILABLE'


def test_claimed_official_status_from_fake_host_cannot_clear_participation():
    fake={**_report(),'source_url':'https://fake-example.net/official'}
    assert not reconcile_participation([fake],game_start=TIP,
              checked_at='2026-11-15T18:00:00Z')['eligible']


def test_conference_header_requires_exact_date():
    html='<h3>Ohio State @ Michigan</h3><table><tr><th>Player</th><th>Status</th></tr><tr><td>Test QB</td><td>Out</td></tr></table>'
    got=extract_conference_report(html,conference='BIG TEN',fixture_label='Ohio State @ Michigan',
       player_name='Test QB',game_date=TIP,report_published_at='2026-11-15T17:00:00Z',
       source_url='https://bigten.org/game/report')
    assert got['state']=='UNVERIFIED'


def test_cfb_play_context_explains_adversity_without_fabricated_grade():
    from bta.research.football import enrich_cfb_script_notes
    rows=[{'scenario':str(i),'verdict':'NOT_ASSESSED','evidence_status':'PARTIAL',
           'mechanism':'Baseline:','source':''} for i in range(5)]
    sample={'teams':{'away':{'adversity':{'state':'OBSERVED',
       'early_deficit_10':{'games':3,'comeback_wins':2},
       'fourth_quarter_one_score':{'games':5,'wins':4}},
       'sources':['https://api.collegefootballdata.com/plays?year=2026']}}}
    out=enrich_cfb_script_notes(rows,sample,'away')
    assert '2/3 games' in out[1]['mechanism'] and '4/5 games' in out[4]['mechanism']
    assert all(r['verdict']=='NOT_ASSESSED' for r in out)


def test_nfl_editorial_fallback_never_claims_game_day_active():
    from bta.sources.nfl_editorial import parse_nfl_editorial
    html='''<html><head><meta property="article:published_time" content="2026-11-06T18:00:00Z"/></head>
    <body><h1>NFL Week 10 injury report 2026 season</h1><h3>Bears</h3>
    <p>OUT: WR Test Receiver (ankle), QB Some Person (foot)</p>
    <p>QUESTIONABLE: TE Another Player (ankle)</p>
    <h3>Packers</h3><p>OUT: WR Test Receiver (toe)</p></body></html>'''
    outcome=parse_nfl_editorial(html,team_nickname='Bears',player='Test Receiver',week=10,season=2026)
    assert outcome['state']=='LEAGUE_EDITORIAL_STATUS' and outcome['status']=='OUT'
    assert not outcome['game_id_verified']
    assert parse_nfl_editorial(html,team_nickname='Bears',player='Unknown',week=10,season=2026)['state']=='UNVERIFIED'
    assert parse_nfl_editorial(html,team_nickname='Bears',player='Test Receiver',week=11,season=2026)['state']=='UNVERIFIED'
