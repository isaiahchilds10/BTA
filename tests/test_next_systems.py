"""New offline integration and adversarial tests. No real API keys are used."""
from datetime import datetime, timedelta, timezone
import copy
import requests
import pytest
from bta.domain import Game, Selection
from bta.sources import free_odds as odds
from bta.research.gates import quote_observation
from bta.models.frozen_evidence import create_pregame_freeze
from bta.models.validation import probability_display_gate
from bta.ai import providers as ai

NOW=datetime.now(timezone.utc)
UPCOMING=(NOW+timedelta(days=1)).isoformat()
RECENT=(NOW-timedelta(minutes=1)).isoformat()
GAME=Game(id='1',sport='NBA',start_time=UPCOMING,away='Houston Rockets',home='Phoenix Suns',state='pre')
PLAYERS=[{'name':'Test Athlete','id':'77','team_id':'2','position':'SG'}]

def event(market='player_points',period='FULL',asof=RECENT):
    return {'id':'up-1','home_team':GAME.home,'away_team':GAME.away,'commence_time':UPCOMING,
        'bookmakers':[{'key':'fanduel','markets':[{'key':market,'period':period,
        'last_update':asof,'outcomes':[{'name':'Over','description':'Test Athlete',
                                      'point':22.5,'price':-115},
                                     {'name':'Under','description':'Test Athlete',
                                      'point':22.5,'price':-105}]}]}]}


def test_propline_normalizes_only_full_game_known_player():
    q=odds.parse_nested(event(),GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/basketball_nba/odds')
    assert len(q)==2
    assert [r['direction'] for r in q]==['OVER','UNDER']
    assert all(r['market']=='points' and r['athlete_id']=='77' and r['source_name']=='PropLine' for r in q)
    assert all(not r['inclusive'] for r in q)


def test_propline_blocks_inverted_fixture_and_wrong_start():
    inverted=event();inverted['home_team'],inverted['away_team']=inverted['away_team'],inverted['home_team']
    assert odds.parse_nested(inverted,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')==[]
    changed=event();changed['commence_time']=(NOW+timedelta(days=3)).isoformat()
    assert odds.parse_nested(changed,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')==[]


def test_stale_and_unsupported_period_and_ambiguous_role_fail_closed():
    old=event(asof=(NOW-timedelta(hours=3)).isoformat())
    assert not odds.parse_nested(old,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')
    q1=event(period='Q1')
    assert not odds.parse_nested(q1,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')
    assert not odds.parse_nested(event(),GAME,PLAYERS*2,'PropLine','https://api.prop-line.com/v1/sports/x/odds')


def test_no_unsupported_player_market_or_suspended_offer():
    bad=event(market='player_imaginary_market')
    assert not odds.parse_nested(bad,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')
    pulled=event();pulled['bookmakers'][0]['markets'][0]['suspended_at']=RECENT
    assert not odds.parse_nested(pulled,GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/x/odds')


def test_parlay_flat_props_exact_response_fields():
    row={'event_id':'p123','home_team':GAME.home,'away_team':GAME.away,
        'commence_time':UPCOMING,'bookmaker':'draftkings','player':'Test Athlete',
        'market_key':'player_points','line':22.5,'over_price':-112,'under_price':-108,
        'last_update':RECENT,'period':'FULL'}
    got=odds.parse_flat_props([row],GAME,PLAYERS,'https://parlay-api.com/v1/sports/basketball_nba/props')
    assert len(got)==2 and got[0]['platform']=='DraftKings'
    assert got[0]['threshold']==22.5 and got[1]['direction']=='UNDER'
    assert odds.parse_flat_props([row],GAME,PLAYERS,'https://parlay-api.com/v1/sports/basketball_nba/props',truncated=True)==[]
    row['period']='UNKNOWN'
    assert not odds.parse_flat_props([row],GAME,PLAYERS,'https://parlay-api.com/v1/sports/basketball_nba/props')


def test_refetched_offer_can_pass_exact_quote_gate():
    q=odds.parse_nested(event(),GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/basketball_nba/odds')[0]
    selection=Selection.new(sport='NBA',game_id='1',game_label=f'{GAME.away} @ {GAME.home}',
        game_start=UPCOMING,subject='Test Athlete',market='points',direction='OVER',threshold=22.5,
        platform='FanDuel',athlete_id='77')
    result=quote_observation(selection,q,checked_at=NOW.isoformat())
    assert result['state']=='OBSERVED'
    selection.threshold=20.5
    assert quote_observation(selection,q,checked_at=NOW.isoformat())['state']=='UNAVAILABLE'


def test_parlay_fallback_after_primary_429(monkeypatch):
    monkeypatch.setattr(odds,'configured',lambda:('PropLine','ParlayAPI'))
    monkeypatch.setattr(odds,'setting',lambda key,default='':{'PROPLINE_API_KEY':'a','PARLAY_API_KEY':'b'}.get(key,default))
    calls=[]
    row={'event_id':'p123','home_team':GAME.home,'away_team':GAME.away,
        'commence_time':UPCOMING,'bookmaker':'fanduel','player':'Test Athlete',
        'market_key':'player_points','line':22.5,'over_price':-110,'under_price':-110,
        'last_update':RECENT,'period':'FULL'}
    def request(url,key,params,**kwargs):
        calls.append(url)
        if 'prop-line.com' in url:raise odds.FreeOddsUnavailable('429')
        assert '/props' in url
        return [row],{'x-result-truncated':'false'}
    monkeypatch.setattr(odds,'_get',request)
    result=odds.fetch_quotes(GAME,PLAYERS,'points')
    assert result['state']=='OBSERVED' and result['provider']=='ParlayAPI'
    assert len(result['quotes'])==2 and len(calls)==2


def test_no_credentials_do_not_invent_offers(monkeypatch):
    monkeypatch.setattr(odds,'configured',lambda:())
    result=odds.fetch_quotes(GAME,PLAYERS,'points')
    assert result['state']=='UNAVAILABLE' and result['quotes']==[]


def selection():
    return Selection.new(sport='NBA',game_id='1',game_label=f'{GAME.away} @ {GAME.home}',
        game_start=UPCOMING,subject='Test Athlete',market='points',direction='OVER',threshold=22.5)


def test_freeze_pregame_and_immutability_fingerprint():
    s=selection();r={'checked_at':RECENT,'grade':'PENDING VERIFICATION','history':{'sample':3},
                     'source_url':'https://www.nba.com/', 'ai':{'text':'Not part of frozen evidence'},
                     'private_email':'secret@example.com'}
    a=create_pregame_freeze(s,r,at=NOW.isoformat())
    b=create_pregame_freeze(s,r,at=NOW.isoformat())
    assert a and a['evidence_hash']==b['evidence_hash']
    assert a['probability_state']=='NOT_SUPPORTED' and a['frozen_at']<a['game_start']
    assert 'ai' not in a['research_snapshot'] and 'private_email' not in a['research_snapshot']
    assert len(a['evidence_hash'])==64


def test_freeze_refuses_after_start_or_unknown_report_time():
    s=selection();r={'checked_at':RECENT,'grade':'BTA'}
    assert create_pregame_freeze(s,r,at=(NOW+timedelta(days=2)).isoformat()) is None
    assert create_pregame_freeze(s,{'grade':'BTA'},at=NOW.isoformat()) is None


def test_numerical_probability_cannot_be_enabled_with_unverified_forecast_pack():
    a={'status':'RESEARCH_GATE_PASSED','external_snapshot_provenance_verified':False,
       'validated_probability':False}
    result=probability_display_gate(audit=a,externally_approved=True,fresh=True,
                                    exact_model_match=True,provider_lineage_verified=True)
    assert result['show_numeric_probability'] is False


def test_ai_rejects_new_urls(monkeypatch):
    monkeypatch.setattr(ai,'providers',lambda:[('groq','model','key')])
    ai.COOLDOWN.clear();ai.HEALTH.clear()
    monkeypatch.setattr(ai,'_request',lambda *args,**kwargs:'Confirmed by https://fake-data.invalid/article this is definitely safe.')
    r=ai.complete('SPECIALIST',{'source_url':'https://www.nba.com/official.pdf'},'Critique')
    assert r.status=='UNAVAILABLE'
    assert ai.provider_health()['groq']['failures']==1


def test_ai_supports_separate_role_rankings(monkeypatch):
    ai.COOLDOWN.clear();ai.HEALTH.clear()
    monkeypatch.setattr(ai,'providers',lambda:[('groq','g','k'),('gemini','m','k')])
    monkeypatch.setattr(ai,'setting',lambda k,default='': 'gemini,groq' if k=='BTA_AI_ORDER_ADVERSARIAL_CRITIC' else default)
    calls=[]
    def fake(name,*args,**kwargs):
        calls.append(name);return 'Sourced information is incomplete and must remain pending.'
    monkeypatch.setattr(ai,'_request',fake)
    r=ai.complete('ADVERSARIAL_CRITIC',{'source_url':'https://www.nba.com/official.pdf'},'Find errors')
    assert r.status=='COMPLETE' and calls==['gemini']

def test_repriced_book_quote_requires_reconfirmation():
    q=odds.parse_nested(event(),GAME,PLAYERS,'PropLine','https://api.prop-line.com/v1/sports/basketball_nba/odds')[0]
    s=Selection.new(sport='NBA',game_id='1',game_label=f'{GAME.away} @ {GAME.home}',
        game_start=UPCOMING,subject='Test Athlete',market='points',direction='OVER',threshold=22.5,
        platform='FanDuel',athlete_id='77',american_odds=-115,provider_market_id=q['provider_market_id'])
    assert quote_observation(s,q,checked_at=NOW.isoformat())['state']=='OBSERVED'
    changed=dict(q,american_odds=-130)
    assert quote_observation(s,changed,checked_at=NOW.isoformat())['state']=='UNAVAILABLE'
    changed=dict(q,provider_market_id='another-select-id')
    assert quote_observation(s,changed,checked_at=NOW.isoformat())['state']=='UNAVAILABLE'

def test_adaptive_ai_task_is_selected_from_missing_gates():
    r={'verification_gates':{'participation':False,'role':True,'opponent':True}}
    assert ai.select_specialist_task(r)[0]=='AVAILABILITY_SPECIALIST'
    r['verification_gates']={'participation':True,'role':False,'opponent':False}
    assert ai.select_specialist_task(r)[0]=='ROLE_OPPORTUNITY_SPECIALIST'
    r['verification_gates']={'participation':True,'role':True,'opponent':False}
    assert ai.select_specialist_task(r)[0]=='MATCHUP_SPECIALIST'
    r['verification_gates']={'participation':True,'role':True,'opponent':True,'market':False}
    assert ai.select_specialist_task(r)[0]=='EXACT_MARKET_SPECIALIST'
    r['verification_gates']={'participation':True,'role':True,'opponent':True,'market':True,'settlement':True}
    assert ai.select_specialist_task(r)[0]=='GAME_SCRIPT_SPECIALIST'
