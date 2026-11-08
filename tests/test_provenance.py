from datetime import datetime,timezone,timedelta
from bta.sources.trust import Claim, freshness,reconcile

def make_claim(value,origin,official=False):
    now=datetime.now(timezone.utc).isoformat()
    return Claim('Player','status',value,'https://example.org/a','official' if official else 'report',origin,now,now,origin,official)

def test_repeated_secondary_source_not_independent():
    result=reconcile([make_claim('questionable','reporter1'),make_claim('questionable','reporter1')])
    assert result['state']=='UNCONFIRMED'

def test_official_beats_secondary_and_conflicts():
    result=reconcile([make_claim('available','league',True),make_claim('out','press')])
    assert result['state']=='OFFICIALLY_CONFIRMED' and result['value']=='available'
    result=reconcile([make_claim('available','league',True),make_claim('out','team',True)])
    assert result['state']=='CONFLICTING'

def test_freshness_status():
    now=datetime.now(timezone.utc)
    assert freshness(now.isoformat(),20,now)=='CURRENT'
    assert freshness((now-timedelta(hours=2)).isoformat(),20,now)=='DELAYED'
    assert freshness('',20,now)=='UNAVAILABLE'
