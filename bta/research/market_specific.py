"""Strict statistical evaluation for advanced NFL markets.

This module does not decide sportsbook/Polymarket settlements or convert an
observed game stat into a validated future probability. Contract semantics must
be explicit; incomplete breakdowns yield UNRESOLVED, never a guessed zero.
"""
from __future__ import annotations
from math import isfinite
from bta.domain import Selection, selection_hit


def _number(value):
    if isinstance(value,bool) or value is None:return None
    try:
        n=float(value)
        if isfinite(n):return n
    except (TypeError,ValueError):pass
    return None


def advanced_statistical_result(selection:Selection,observed:dict,*,
                                verified_final:bool=False,
                                official_stat_correction_pending:bool=False)->dict:
    """Statistics-only result, never wager settlement. Supports exact NFL markets."""
    base={'state':'UNRESOLVED','statistical_result':None,'value':None,
          'settlement':'UNVERIFIED','reason':'Exact market-specific stats or contract terms not established'}
    if selection.sport!='NFL' or selection.market not in ('anytime_td','quarter_rushing_yards'):
        return {**base,'reason':'Not an advanced NFL market handled by this evaluator'}
    if not verified_final:return {**base,'reason':'Final official/statistical event verification not supplied'}
    if official_stat_correction_pending:
        return {**base,'reason':'Official statistical correction pending'}
    if selection.threshold is None:
        return base
    if selection.market=='anytime_td':
        if selection.direction not in ('YES','NO') or selection.threshold!=1 or not selection.inclusive:
            return {**base,'reason':'Touchdown contract must explicitly require one or more qualifying TDs'}
        if observed.get('td_contract')!='RUSH_OR_RECEIVE':
            return {**base,'reason':'Verified contract must specify qualifying rushing/receiving touchdown types'}
        rush=_number(observed.get('rushing_touchdowns'))
        receive=_number(observed.get('receiving_touchdowns'))
        if rush is None or receive is None or min(rush,receive)<0:
            return {**base,'reason':'Both exact rushing and receiving TD counts are required; missing is not zero'}
        value=rush+receive
    else:
        if observed.get('quarter_contract')!='ANY_SINGLE_QUARTER_REGULATION':
            return {**base,'reason':'Any-single-quarter versus specific-quarter settlement is unverified'}
        if not selection.inclusive or selection.direction not in ('YES','NO'):
            return {**base,'reason':'Exact inclusive YES/NO quarter market semantics required'}
        quarter=observed.get('regulation_quarters') or {}
        if not isinstance(quarter,dict):return base
        numeric=[_number(quarter.get(str(i),quarter.get(i))) for i in range(1,5)]
        if any(v is None for v in numeric):
            return {**base,'reason':'Four regulation quarter values required; no imputation from full-game totals'}
        value=max(numeric)
    result=selection_hit(value,selection.threshold,selection.direction,selection.inclusive)
    return {**base,'state':'STATISTICAL_RESULT_ONLY','statistical_result':result,
            'value':value,'reason':'Verified final statistical values; operator/prediction-market settlement, player participation, overtime and void rules remain independent'}
