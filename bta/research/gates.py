"""Evidence provenance, source gates and an independent deterministic second pass.

No AI text, client-side flags, or unsourced test rows can satisfy certification.
All inputs here are computed from trusted *server-fetched* adapters.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from statistics import median
from urllib.parse import urlsplit
from bta.domain import Selection, selection_hit

GATE_KEYS=('participation','market','settlement','opponent','script_evidence','role','provenance')


def timestamp(value: str) -> datetime | None:
    try:
        d=datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError,TypeError):
        return None


def valid_https(value: str, permitted_hosts: tuple[str,...]) -> bool:
    u=urlsplit(value or '')
    return u.scheme=='https' and u.username is None and u.password is None and u.hostname in permitted_hosts


def role_observation(selection: Selection, rows: list[dict]) -> dict:
    """Minimum reproducible opportunity from numeric game logs. Not a health guarantee."""
    sample=rows[:10]
    field= 'minutes' if selection.sport=='NBA' else (
        'attempts' if selection.market in ('passing_yards','passing_attempts','completions','passing_touchdowns',
            'rushing_yards','rushing_attempts') else 'targets' if selection.market in ('receptions','receiving_yards') else '')
    values=[float(r[field]) for r in sample if field and isinstance(r.get(field),(int,float)) and r[field]>=0]
    if len(values)<8:
        return {'state':'UNKNOWN','field':field,'sample':len(values),
                'reason':'Comparable minutes/attempts/targets not available for eight recent games'}
    typical=median(values)
    minimum=20 if field=='minutes' else 10 if selection.market.startswith('passing') or selection.market=='completions' else 5 if field=='attempts' else 3
    retained=sum(v>=0.65*typical for v in values)
    stable=typical>=minimum and retained>=8
    return {'state':'SUPPORTED' if stable else 'UNSTABLE','field':field,'sample':len(values),
            'median':round(typical,1),'games_at_65pct_median':retained,
            'reason':f'Observed {retained}/{len(values)} with >=65% of sample median opportunity; qualification requires 8/10 and median >= {minimum}. Not a projected floor.'}


def quote_observation(selection: Selection, quote: dict | None, *, checked_at: str) -> dict:
    """Called only after retrieving provider response server-side; never trusts client booleans.

    A quote confirms an observed offer, not bookmaker acceptance or full settlement.
    """
    result={'state':'UNAVAILABLE','reason':'No fresh server-retrieved exact bookmaker quote','source_url':'','checked_at':checked_at}
    if not quote:return result
    now=timestamp(checked_at); asof=timestamp(str(quote.get('market_observed_at','')))
    if not now or not asof or not timedelta(0)<=now-asof<=timedelta(minutes=15):return result
    same=(quote.get('market')==selection.market and quote.get('direction')==selection.direction
        and quote.get('subject','').casefold().strip()==selection.subject.casefold().strip()
        and quote.get('threshold')==selection.threshold
        and quote.get('platform')==selection.platform
        and quote.get('athlete_id','')==selection.athlete_id
        and quote.get('provider_market_id'))
    if not same:return result
    # The old stored offer may have been repriced or replaced. This validates
    # the *exact* original quoted side/price/identity, not a superficially
    # similar live market. Manually supplied thresholds without native ids
    # can still be matched on exact terms and price.
    if (selection.provider_market_id and
        str(selection.provider_market_id)!=str(quote.get('provider_market_id'))):
        return {**result,'reason':'Saved provider selection identity no longer matches refreshed offer'}
    if (selection.american_odds is not None and
        selection.american_odds!=quote.get('american_odds')):
        return {**result,'reason':'Bookmaker price changed; fresh user confirmation required'}
    price=quote.get('american_odds')
    if isinstance(price,bool) or not isinstance(price,int) or abs(price)<100:
        return result
    source=quote.get('market_source_url','')
    if not valid_https(source,('sportsgameodds.com','api.sportsgameodds.com','api.prop-line.com','parlay-api.com')):return result
    return {'state':'OBSERVED','reason':'Fresh server-refetched exact offer; wager acceptance and settlement not implied',
            'source_url':source,'checked_at':checked_at, 'observed_at':asof.isoformat(),
            'provider_market_id':quote['provider_market_id']}


def independent_second_pass(selection: Selection, history: dict, scripts: list[dict],
                            gates: dict, records: list[dict]) -> dict:
    """Deterministic re-audit independent of the primary grading function."""
    failures=[]
    for key in GATE_KEYS:
        if gates.get(key) is not True:failures.append(f'Unresolved gate: {key}')
    if len(scripts)!=5 or any(s.get('evidence_status')!='VERIFIED' for s in scripts):
        failures.append('Five script observations not source-linked')
    if history.get('available') and records:
        recent=records[:10]
        valid=[selection_hit(float(r['value']),float(selection.threshold),selection.direction,selection.inclusive)
               for r in recent if r.get('value') is not None] if selection.threshold is not None else []
        if len(valid)!=len(recent) or sum(v=='HIT' for v in valid)!=history.get('hits'):
            failures.append('Historical recomputation disagreed with report')
    if history.get('sample',0)<8:failures.append('Fewer than eight comparable game logs')
    if history.get('median_clearance') is None:failures.append('Missing exact-line clearance cushion')
    if not (selection.game_id and selection.game_id.isdigit()):failures.append('Unverified game identity')
    return {'status':'PASS' if not failures else 'PENDING','failures':failures,
            'method':'Independent deterministic recomputation; no AI-reported fact can satisfy a gate'}


def candidate_screen(history:dict, role:dict, scripts:list[dict]) ->dict:
    """Useful preliminary screen; is deliberately NOT a BTA certification."""
    if not history.get('available') or history.get('sample',0)<8:
        return {'status':'INSUFFICIENT_HISTORY','message':'Need eight comparable games for the preliminary screen'}
    n=history['sample']; hits=history['hits']; cushion=history['median_clearance']
    worse=sum(s.get('verdict')=='WORSE' and s.get('evidence_status')=='VERIFIED' for s in scripts)
    if worse>=2:
        return {'status':'PRELIMINARY_CUT','message':'Two source-backed adverse game conditions observed'}
    if hits>=n-1 and cushion>0 and role.get('state')=='SUPPORTED':
        return {'status':'STRONG_RESEARCH_CANDIDATE','message':'High observed exact-line consistency and stable measured opportunity; certification gates remain independent'}
    if hits>=n-2 and cushion>0:
        return {'status':'WORTH_INVESTIGATING','message':'Promising observed history; opponent, injury and game-script checks are still decisive'}
    return {'status':'WEAK_HISTORICAL_CASE','message':'Normal observed misses/cushion do not support a strict candidate'}
