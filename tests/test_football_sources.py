"""Contract-based offline tests, not claims that upstream APIs were queried live."""
from datetime import datetime,timedelta,timezone
import pytest
from bta.sources.nfl_injuries import nfl_injury_observation
from bta.sources.cfbd import match_fixture, cfb_matchup_evidence, historic_team_profile
from bta.research.football import cfb_stress_audit

NOW=datetime(2026,11,7,18,0,tzinfo=timezone.utc)
KICK='2026-11-08T20:00:00+00:00'


def injury(status='Questionable',modified='2026-11-07T11:00:00Z'):
    return dict(season='2026',week='10',team='JAC',full_name='Test Receiver',report_status=status,
                date_modified=modified,practice_status='Limited',report_primary_injury='Ankle')


def test_nfl_report_is_corroboration_not_primary_certification():
    o=nfl_injury_observation('Test Receiver','JAX',2026,10,
                             as_of='2026-11-07T18:00:00Z',snapshot_rows=[injury()])
    assert o['state']=='REPORTED_SECONDARY' and o['status']=='QUESTIONABLE'
    assert o['official_verification'] is False and o['practice_status']=='Limited'


def test_nfl_not_listed_is_not_active():
    o=nfl_injury_observation('Another Player','JAX',2026,10,
                             as_of='2026-11-07T18:00:00Z',snapshot_rows=[injury()])
    assert o['state']=='NOT_LISTED' and o['official_verification'] is False


def test_nfl_future_entry_cannot_leak_into_past():
    o=nfl_injury_observation('Test Receiver','JAC',2026,10,
                             as_of='2026-11-06T18:00:00Z',snapshot_rows=[injury()])
    assert o['state']=='NOT_LISTED'


def test_nfl_conflicting_same_timestamp_is_visible():
    o=nfl_injury_observation('Test Receiver','JAC',2026,10,
                             as_of='2026-11-07T18:00:00Z',snapshot_rows=[injury(),injury('Out')])
    assert o['state']=='CONFLICTING'


def test_nfl_old_injury_reports_not_current():
    o=nfl_injury_observation('Test Receiver','JAC',2026,10,
                             as_of='2026-11-07T18:00:00Z',snapshot_rows=[injury(modified='2026-10-29T18:00:00Z')])
    assert o['state']=='OUTDATED'


def fixture(id,home,away,date,home_pts=None,away_pts=None,**extra):
    return {'id':id,'homeTeam':home,'awayTeam':away,'startDate':date,'homePoints':home_pts,'awayPoints':away_pts,**extra}


def sample_cfb():
    future=fixture(100,'Ohio State','Michigan',KICK,homeClassification='fbs',awayClassification='fbs')
    games=[future]
    boxes={'Ohio State':[],'Michigan':[]}
    for idx in range(7):
        date=(datetime(2026,10,1,tzinfo=timezone.utc)+timedelta(days=idx)).isoformat()
        games.append(fixture(200+idx,'Ohio State','Michigan',date,30+idx,14+idx))
        boxes['Ohio State'].append({'id':200+idx,'teams':[{'team':'Ohio State','stats':[
            {'category':'totalYards','stat':'490'}, {'category':'totalPlays','stat':'70'},
            {'category':'rushingYards','stat':'200'},{'category':'turnovers','stat':'1'}]}]})
        boxes['Michigan'].append({'id':200+idx,'teams':[{'team':'Michigan','stats':[
            {'category':'totalYards','stat':'300'}, {'category':'totalPlays','stat':'60'},
            {'category':'rushingYards','stat':'85'},{'category':'turnovers','stat':'2'}]}]})
    return games,boxes


def test_cfb_fixture_requires_unique_two_sided_date_identity():
    games,boxes=sample_cfb()
    assert match_fixture(games,'Ohio State','Michigan',KICK)['id']==100
    assert match_fixture(games,'Michigan','Ohio State',KICK) is None
    assert match_fixture(games+[games[0]],'Ohio State','Michigan',KICK) is None


def test_cfb_profile_uses_only_prior_real_games():
    games,boxes=sample_cfb()
    games.append(fixture(999,'Ohio State','Michigan','2026-11-20T12:00:00Z',200,1))
    p=historic_team_profile('Ohio State',games,boxes['Ohio State'],KICK)
    assert p['sample']==7 and p['points_for']==33
    assert p['yards_per_play']==7
    assert all(r['game_id']!='999' for r in p['games'])


def test_cfb_matchup_context_never_claims_certification():
    games,boxes=sample_cfb()
    result=cfb_matchup_evidence('Ohio State','Michigan',KICK,'',fixture_games=games,boxscores=boxes)
    assert result['fixture_verified'] and result['fbs_verified']
    assert result['state']=='RESEARCH_AVAILABLE'
    scenarios=cfb_stress_audit(result)
    assert len(scenarios)==5
    assert all(row['verdict']=='NOT_ASSESSED' and row['evidence_status']=='PARTIAL' for row in scenarios)


def test_cfb_fcs_blocks_even_with_good_scores():
    games,boxes=sample_cfb();games[0]['awayClassification']='fcs'
    result=cfb_matchup_evidence('Ohio State','Michigan',KICK,'',fixture_games=games,boxscores=boxes)
    assert result['state']=='FCS_BLOCKED' and not result['fbs_verified']


def test_official_nfl_parser_accepts_only_exact_team_week_player():
    from bta.sources.nfl_official import parse_official_nfl_html
    markup='''<h1>Injuries - WEEK 10</h1><h3>Houston Texans</h3>
        <table><tr><th>Player</th><th>Position</th><th>Game Status</th></tr>
        <tr><td>Test Receiver</td><td>WR</td><td>Questionable</td></tr></table>'''
    good=parse_official_nfl_html(markup,player='Test Receiver',team_name='Houston Texans',season=2026,week=10)
    assert good['state']=='OFFICIALLY_DESIGNATED' and good['status']=='QUESTIONABLE'
    assert not parse_official_nfl_html(markup,player='Test Receiver',team_name='Dallas Cowboys',season=2026,week=10)['official_verification']
    assert not parse_official_nfl_html(markup,player='Test Receiver',team_name='Houston Texans',season=2026,week=11)['official_verification']


def test_official_nfl_blank_game_status_is_not_active():
    from bta.sources.nfl_official import parse_official_nfl_html
    markup='<div>Injuries - WEEK 10</div><h3>Houston Texans</h3><table><tr><th>Player</th><th>Game Status</th></tr><tr><td>Test Receiver</td><td></td></tr></table>'
    result=parse_official_nfl_html(markup,player='Test Receiver',team_name='Houston Texans',season=2026,week=10)
    assert result['state']=='OFFICIALLY_LISTED' and not result['official_verification']


def test_nfl_blown_out_scoring_analogy_not_historical_favorite_claim():
    from bta.domain import Selection
    from bta.research.stress import sourced_scripts
    s=Selection.new(sport='NFL',game_id='123456',game_label='A @ B',
           game_start=KICK,subject='Test Player',market='receiving_yards',
           direction='YES',threshold=20,inclusive=True)
    history=[];games=[]
    for i in range(16):
        history.append({'event_id':str(500+i),'date':'2026-10-01','value':30 if i<13 else 10})
        margin=21 if i<4 else -21 if i<8 else 0
        games.append({'event_id':str(500+i),'points_for':20+margin,'points_against':20,
                      'margin':margin,'result':'W' if margin>0 else 'L' if margin<0 else 'T'})
    unknown=sourced_scripts(s,history,games,'https://site.api.espn.com/source')
    assert unknown[0]['verdict']=='NOT_ASSESSED' and unknown[1]['verdict']=='NOT_ASSESSED'
    specified=sourced_scripts(s,history,games,'https://site.api.espn.com/source',
          player_team_is_favorite=True,favorite_source='https://sportsgameodds.com/docs/endpoints/getEvents')
    assert specified[0]['evidence_status']=='VERIFIED' and specified[0]['sample']==4
    assert specified[1]['sample']==4 and 'historical actual game margins' in specified[0]['mechanism']


def test_spread_is_not_a_future_probability():
    from bta.sources.sportsgameodds import favorite_from_moneyline_quotes
    quotes=[{'market':'moneyline','direction':'YES','subject':'Houston Texans',
             'american_odds':-155,'market_observed_at':'2026-11-07T18:00:01Z',
             'market_source_url':'https://sportsgameodds.com/docs/endpoints/getEvents'},
            {'market':'moneyline','direction':'YES','subject':'Dallas Cowboys',
             'american_odds':+145,'market_observed_at':'2026-11-07T18:00:03Z',
             'market_source_url':'https://sportsgameodds.com/docs/endpoints/getEvents'}]
    f=favorite_from_moneyline_quotes(quotes,player_team='Houston Texans',current_time='2026-11-07T18:00:05Z')
    assert f['state']=='OBSERVED_MARKET_FAVORITE' and f['player_team_is_favorite'] is True
    assert 'probability' not in f
    quotes[1]['market_observed_at']='2026-11-07T15:00:03Z'
    assert favorite_from_moneyline_quotes(quotes,player_team='Houston Texans',current_time='2026-11-07T18:00:05Z')['state']=='UNVERIFIED'


def test_nfl_weekly_history_matches_player_team_season_and_pregame_week():
    from bta.sources.nfl_weekly import nfl_weekly_observations
    rows=[{'season':'2026','week':str(w),'player_display_name':'Test Receiver',
           'player_id':'00-1111','recent_team':'JAC','opponent_team':'HOU',
           'position':'WR','receiving_yards':str(30+w),'targets':'5','receptions':'3'}
          for w in range(1,12)]
    result=nfl_weekly_observations('Test Receiver','JAX','receiving_yards',2026,10,snapshot_rows=rows)
    assert result['sample']==9 and result['rows'][0]['week']==9
    assert result['rows'][0]['value']==39 and all(r['week']<10 for r in result['rows'])
    assert result['rows'][0]['targets']==5


def test_nfl_weekly_history_missing_or_ambiguous_identity_fails_closed():
    from bta.sources.nfl_weekly import nfl_weekly_observations
    rows=[{'season':'2026','week':str(w),'player_display_name':'Test Receiver',
           'player_id':f'00-{w}','recent_team':'JAC','position':'WR',
           'receiving_yards':'34'} for w in range(1,4)]
    result=nfl_weekly_observations('Test Receiver','JAX','receiving_yards',2026,10,snapshot_rows=rows)
    assert result['state']=='UNAVAILABLE'


def test_week_to_event_mapping_requires_same_opponent_and_single_schedule_week():
    from bta.research.football import join_nfl_weekly_events
    w=[{'week':1,'opponent':'HOU','date':'2026-W01','value':40},
       {'week':2,'opponent':'NYG','date':'2026-W02','value':30}]
    g=[{'week':1,'opponent_abbr':'HOU','date':'2026-09-10T18:00Z','event_id':'12345'},
       {'week':2,'opponent_abbr':'PHI','date':'2026-09-17T18:00Z','event_id':'12346'}]
    linked=join_nfl_weekly_events(w,g)
    assert linked[0]['event_id']=='12345' and linked[0]['date']=='2026-09-10T18:00Z'
    assert 'event_id' not in linked[1] and linked[1]['script_join_status']=='NOT_JOINED'
