"""Offline integration: a real code path, controlled adapter responses, no live-source claim."""
from datetime import datetime,timezone,timedelta
from bta.domain import Selection
from bta.research import engine


def test_nfl_weekly_context_is_used_without_auto_grading(monkeypatch):
    tip=(datetime.now(timezone.utc)+timedelta(days=2)).isoformat()
    s=Selection.new(sport='NFL',game_id='12345',game_label='Dallas Cowboys @ Houston Texans',
                    game_start=tip,subject='Test Receiver',market='receiving_yards',direction='YES',
                    threshold=20,inclusive=True)
    context={'fixture_verified':True,'athlete_id':'999','athlete_team_id':'1',
             'team_ids':{'away':'1','home':'2'},'team_abbreviations':{'away':'DAL','home':'HOU'},
             'team_names':{'away':'Dallas Cowboys','home':'Houston Texans'},
             'team_locations':{'away':'Dallas','home':'Houston'},'week':10,
             'matchup_code':'DAL@HOU','sources':[],'status':'THIRD_PARTY_CONTEXT_AVAILABLE'}
    monkeypatch.setattr(engine,'discover_market_context',lambda _:context)
    monkeypatch.setattr(engine,'gamelog',lambda *a,**k:({},'https://site.web.api.espn.com/gamelog'))
    monkeypatch.setattr(engine,'rows_from_gamelog',lambda *a,**k:[])
    teamgames=[]
    for week in range(1,10):
        teamgames.append({'event_id':str(2000+week),'week':week,'opponent_abbr':'NYG',
                          'date':f'2026-09-{week:02d}T18:00:00+00:00',
                          'points_for':22,'points_against':20,'margin':2,'result':'W'})
    monkeypatch.setattr(engine,'team_schedule',lambda *a,**k:(teamgames,'https://site.api.espn.com/schedule'))
    def mocked_weekly(*a,**k):
        return {'state':'HISTORICAL_WEEKLY_RESEARCH','sample':9,
                'source_url':'https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_2026.csv',
                'rows':[{'week':w,'opponent':'NYG','date':'2026-W01','value':35,
                         'targets':6} for w in range(1,10)],
                'reason':'Controlled fixture'}
    import bta.sources.nfl_weekly as weekly
    monkeypatch.setattr(weekly,'nfl_weekly_observations',mocked_weekly)
    import bta.research.football as football
    monkeypatch.setattr(football,'football_market_evidence',lambda *a,**k:
                        {'sport':'NFL','injury':{'state':'NOT_LISTED'},'official_injury':{'state':'UNAVAILABLE'}})
    out=engine.analyze(s)
    assert out['history']['sample']==9 and out['history']['hits']==9
    assert out['role_evidence']['state']=='SUPPORTED'
    assert 'nflverse' in out['source_type']
    assert out['scripts'][0]['verdict']=='NOT_ASSESSED'
    assert out['grade']=='PENDING VERIFICATION'
    assert out['nfl_weekly_evidence']['state']=='HISTORICAL_WEEKLY_RESEARCH'
