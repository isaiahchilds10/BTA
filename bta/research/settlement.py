"""Exact-market statistical and settlement eligibility with fail-closed states.

A statistical win is not a sportsbook settlement. Valid provider rules, game
participation, official results, correction window, and contract wording are
required to settle. This function supports common full-game and special NFL
contracts without claiming bookmaker equivalence.
"""
from __future__ import annotations
from dataclasses import dataclass
from bta.domain import Selection, selection_hit
from bta.research.market_specific import advanced_statistical_result


@dataclass(frozen=True)
class Resolution:
    state: str
    result: str | None
    reason: str
    observed: float | None = None


def resolve_exact_market(selection: Selection, facts:dict, *,
                         verified_official_final:bool, terms_verified:bool,
                         participation_verified:bool, corrections_closed:bool) -> Resolution:
    if not verified_official_final:
        return Resolution('PENDING',None,'Official final event/statistics not yet verified')
    if not corrections_closed:
        return Resolution('PENDING',None,'Official correction window has not been reconciled')
    if not terms_verified:
        return Resolution('PENDING',None,'Exact operator/contract settlement rules not established')
    if not participation_verified:
        return Resolution('PENDING',None,'Player participation/void conditions not established')
    if selection.market in ('anytime_td','quarter_rushing_yards'):
        result=advanced_statistical_result(selection,facts,verified_final=True)
        if result['state']!='STATISTICAL_RESULT_ONLY':
            return Resolution('PENDING',None,result['reason'])
        return Resolution('STATISTICAL_RESULT',result['statistical_result'],
                          'Market-specific statistics satisfy the supplied settlement definitions; external official settlement remains separate',result['value'])
    value=facts.get('value')
    if value is None or isinstance(value,bool) or selection.threshold is None:
        return Resolution('PENDING',None,'Missing exact recognized market statistic')
    try:
        f=float(value)
        if not __import__('math').isfinite(f):raise ValueError
        hit=selection_hit(f,float(selection.threshold),selection.direction,selection.inclusive)
    except (TypeError,ValueError):
        return Resolution('PENDING',None,'Invalid exact market statistic or direction')
    return Resolution('STATISTICAL_RESULT',hit,'Official completed statistics; book/contract settlement may still have special exceptions',f)
