from bta.domain import Selection
from bta.research.market_specific import advanced_statistical_result
from bta.research.freshness import freshness_state
from bta.research.live import observed_from_summary


def sel(market='anytime_td',direction='YES',threshold=1,inclusive=True):
    return Selection.new(sport='NFL',game_id='12345678',game_label='A @ B',
        game_start='2026-11-09T00:00:00Z',subject='Player',market=market,
        direction=direction,threshold=threshold,inclusive=inclusive)


def test_td_exactly_rush_receive_not_pass_td():
    result=advanced_statistical_result(sel(),{
        'td_contract':'RUSH_OR_RECEIVE','rushing_touchdowns':0,
        'receiving_touchdowns':0,'passing_touchdowns':5},verified_final=True)
    assert result['statistical_result']=='MISS' and result['value']==0
    assert result['settlement']=='UNVERIFIED'


def test_td_missing_receiving_count_never_turns_to_zero():
    assert advanced_statistical_result(sel(),{'td_contract':'RUSH_OR_RECEIVE',
        'rushing_touchdowns':0},verified_final=True)['state']=='UNRESOLVED'


def test_td_contract_type_required():
    assert advanced_statistical_result(sel(),{'rushing_touchdowns':1,'receiving_touchdowns':0},
        verified_final=True)['state']=='UNRESOLVED'


def test_any_quarter_requires_all_four_quarters():
    s=sel('quarter_rushing_yards',threshold=5)
    v={'quarter_contract':'ANY_SINGLE_QUARTER_REGULATION',
       'regulation_quarters':{'1':0,'2':1,'3':5,'4':0}}
    result=advanced_statistical_result(s,v,verified_final=True)
    assert result['statistical_result']=='HIT' and result['value']==5
    del v['regulation_quarters']['4']
    assert advanced_statistical_result(s,v,verified_final=True)['state']=='UNRESOLVED'


def test_final_verification_and_corrections_block_statistical_result():
    s=sel()
    obs={'td_contract':'RUSH_OR_RECEIVE','rushing_touchdowns':1,'receiving_touchdowns':0}
    assert advanced_statistical_result(s,obs,verified_final=False)['state']=='UNRESOLVED'
    assert advanced_statistical_result(s,obs,verified_final=True,official_stat_correction_pending=True)['state']=='UNRESOLVED'


def test_live_freshness_requires_provider_time_not_just_fetch():
    kw={'retrieved_at':'2026-11-07T20:00:00Z','max_age_seconds':180,'now':'2026-11-07T20:00:05Z'}
    assert freshness_state(provider_updated_at=None,**kw)['state']=='TIMESTAMP_UNVERIFIED'
    assert freshness_state(provider_updated_at='2026-11-07T19:59:20Z',**kw)['state']=='CURRENT'
    assert freshness_state(provider_updated_at='2026-11-07T19:40:00Z',**kw)['state']=='DELAYED'
    assert freshness_state(provider_updated_at='2026-11-08T06:00:00Z',**kw)['state']=='UNAVAILABLE'


def test_espm_live_box_without_provider_timestamp_is_not_fresh():
    out=observed_from_summary(sel(),{'header':{'competitions':[{'competitors':[]}]}})
    assert out['freshness']['state']=='TIMESTAMP_UNVERIFIED'
    assert out['probability'] is None and out['settlement']=='UNVERIFIED'


def test_td_game_log_combines_only_matching_event_rush_receive_not_passing():
    from bta.sources.espn import rows_from_gamelog
    payload={'events':{'101':{'gameDate':'2026-10-19T20:00:00Z','opponent':{'abbreviation':'NYG'}}},
       'seasonTypes':[{'categories':[
          {'name':'rushing','labels':['YDS','TD'],'events':[{'eventId':'101','stats':['0','1']}]},
          {'name':'receiving','labels':['REC','TD'],'events':[{'eventId':'101','stats':['3','0']}]},
          {'name':'passing','labels':['YDS','TD'],'events':[{'eventId':'101','stats':['200','4']}]},
       ]}]}
    result=rows_from_gamelog(payload,'anytime_td',cutoff='2026-11-05T20:00:00Z')
    assert len(result)==1 and result[0]['value']==1
    payload['seasonTypes'][0]['categories'][1]['events']=[]
    assert rows_from_gamelog(payload,'anytime_td',cutoff='2026-11-05T20:00:00Z')==[]
