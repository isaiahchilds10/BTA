"""Market-specific source freshness, separate from retrieval-time wall clock."""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
from bta.research.gates import timestamp


def freshness_state(*,provider_updated_at:str|None,retrieved_at:str|None,
                    max_age_seconds:int,now:str|None=None)->dict:
    at=timestamp(now) if now else datetime.now(timezone.utc)
    provider=timestamp(provider_updated_at) if provider_updated_at else None
    fetched=timestamp(retrieved_at) if retrieved_at else None
    base={'state':'UNAVAILABLE','provider_updated_at':provider_updated_at,
          'retrieved_at':retrieved_at,'can_refresh_probability':False,'age_seconds':None}
    if not at or not fetched or fetched>at+timedelta(minutes=2):
        return {**base,'reason':'Missing or invalid retrieval timestamp'}
    if not provider:
        return {**base,'state':'TIMESTAMP_UNVERIFIED',
                'reason':'No upstream provider-update time; successful HTTP retrieval is not proof of fresh data'}
    if provider>at+timedelta(minutes=2):
        return {**base,'reason':'Provider publication timestamp is unexpectedly in the future'}
    age=max(0,int((at-provider).total_seconds()))
    if age>max_age_seconds:
        return {**base,'state':'DELAYED','age_seconds':age,
                'reason':'Upstream source is older than the configured market freshness policy'}
    return {**base,'state':'CURRENT','age_seconds':age,
            'can_refresh_probability':True,'reason':'Upstream publication is within the configured age bound; model validation still required'}
