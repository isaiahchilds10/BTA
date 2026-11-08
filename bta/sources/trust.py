"""Conservative canonical provenance and source-conflict policy.

No AI response may create an OFFICIALLY_CONFIRMED fact. Unknown official data remains
UNKNOWN, even if two articles share the same journalist or one model repeats a claim.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import datetime,timezone,timedelta
from typing import Literal

State=Literal['OFFICIALLY_CONFIRMED','CREDIBLY_REPORTED','CONFLICTING','UNCONFIRMED','OUTDATED','UNKNOWN']

@dataclass(frozen=True)
class Claim:
    subject:str
    field:str
    value:str
    source_url:str
    source_kind:str
    publisher:str
    published_at:str
    retrieved_at:str
    upstream_origin:str = ''
    # Verified upstream official classification is determined only by trusted adapter, not external AI text.
    is_verified_official:bool=False


def iso(when:str)->datetime|None:
    try:
        value=datetime.fromisoformat(when.replace('Z','+00:00'))
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except (ValueError,TypeError,AttributeError):return None


def freshness(retrieved_at:str,max_age_minutes:int=20,now:datetime|None=None)->str:
    moment=iso(retrieved_at)
    if moment is None:return 'UNAVAILABLE'
    current=now or datetime.now(timezone.utc)
    age=(current-moment).total_seconds()
    if age<0 or age>max_age_minutes*60:return 'DELAYED'
    return 'CURRENT'


def reconcile(claims:list[Claim],*,now:datetime|None=None,max_age_hours:int=48)->dict:
    """Source lineage prevents syndications from being counted as independent corroboration."""
    current=now or datetime.now(timezone.utc)
    visible=[c for c in claims if c.source_url.startswith('https://') and iso(c.retrieved_at)]
    valid=[c for c in visible if iso(c.published_at) and timedelta(0)<=(current-iso(c.published_at))<=timedelta(hours=max_age_hours)]
    official=[c for c in valid if c.is_verified_official]
    def pack(state,reason,chosen=None):
        return {'state':state,'reason':reason,'value':chosen,'claims':[asdict(x) for x in visible],
            'checked_at':current.isoformat()}
    if official:
        values=set(c.value.casefold().strip() for c in official)
        if len(values)>1:return pack('CONFLICTING','Conflicting verified official claims')
        return pack('OFFICIALLY_CONFIRMED','Verified authoritative source',official[0].value)
    if not valid:return pack('OUTDATED' if visible else 'UNKNOWN','No current evidence')
    # Count independent upstream origins, not repeated articles quoting the same reporter.
    origins={c.upstream_origin.strip().casefold() or c.publisher.strip().casefold() for c in valid}
    values={c.value.casefold().strip() for c in valid}
    if len(values)>1:return pack('CONFLICTING','Material reporting disagreement')
    if len(origins)>=2:return pack('CREDIBLY_REPORTED','At least two independent upstream reporting origins',valid[0].value)
    return pack('UNCONFIRMED','Only one distinct reporting origin',valid[0].value)
