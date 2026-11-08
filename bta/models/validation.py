"""Strict, reproducible probability backtesting on pre-event frozen predictions.

Not a forecasting model. It refuses to certify invented demonstrations, fitted
success rates, hindsight thresholds, or unsupported dependencies. Approval must
be a separate human-governed gate using externally timestamped snapshots.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import log
from statistics import mean
from bta.research.gates import timestamp

MIN_TRAIN_EVENTS=300
MIN_TEST_EVENTS=100
MIN_TEST_DAYS=21
MAX_EXPECTED_CALIBRATION_ERROR=0.08
MIN_BRIER_IMPROVEMENT=0.01


def _brier(values):
    return mean((p-y)**2 for p,y in values)

def _logloss(values):
    return mean(-y*log(max(1e-9,min(1-1e-9,p)))-(1-y)*log(max(1e-9,min(1-1e-9,1-p))) for p,y in values)

def _ece(values):
    n=len(values); total=0.0
    for b in range(10):
        bucket=[(p,y) for p,y in values if min(9,int(p*10))==b]
        if bucket:total+=len(bucket)/n*abs(mean(x[0] for x in bucket)-mean(x[1] for x in bucket))
    return total


def audit_chronological_forecasts(records:list[dict], *, sport:str, market:str,
                                  model_version:str, min_train:int=MIN_TRAIN_EVENTS,
                                  min_test:int=MIN_TEST_EVENTS) -> dict:
    """Run an out-of-time holdout audit for one precisely specified market.

    A row requires immutable forecast/source cutoff < event start and recorded
    final result timestamp > start. The function checks timestamp *claims*;
    independent source snapshots are required before real model approval.
    """
    base={'status':'MODEL_UNDER_TEST','sport':sport,'market':market,
          'model_version':model_version,'validated_probability':False,
          'reason':'No verified chronological holdout performance'}
    if not records or not sport or not market or not model_version:return base
    accepted=[]; violations=[]; seen=set()
    for i,r in enumerate(records):
        if (r.get('sport'),r.get('market'),r.get('model_version'))!=(sport,market,model_version):
            violations.append((i,'Wrong model/sport/market'));continue
        freeze=timestamp(r.get('forecast_at'))
        source=timestamp(r.get('last_input_at'))
        start=timestamp(r.get('game_start'))
        final=timestamp(r.get('result_published_at'))
        game_id=r.get('game_id')
        threshold_id=r.get('exact_market_id')
        snapshot_id=r.get('frozen_snapshot_id')
        p=r.get('probability'); y=r.get('outcome')
        if isinstance(p,bool) or not isinstance(p,(float,int)) or not 0 < p < 1 or y not in (0,1):
            violations.append((i,'Invalid probability or binary outcome'));continue
        if not (freeze and source and start and final and source<=freeze<start<final):
            violations.append((i,'Lookahead or absent timestamps'));continue
        if not (game_id and threshold_id and snapshot_id):
            violations.append((i,'Missing frozen evidence, event or exact market identity'));continue
        key=(game_id,threshold_id)
        if key in seen:
            violations.append((i,'Duplicate market/event predicted more than once'));continue
        seen.add(key)
        accepted.append((start,float(p),int(y),str(game_id)))
    if violations:
        return {**base,'reason':'Invalid records must be excluded and investigated before model approval',
                'invalid_records':len(violations),'examples':violations[:8]}
    accepted.sort(key=lambda row:row[0])
    n=len(accepted)
    if n<min_train+min_test:
        return {**base,'reason':f'Need {min_train} prior events and {min_test} strictly later held-out events',
                'observations':n}
    # Complete game clusters must stay together to avoid cross-leg test leakage.
    boundary=max(min_train,int(n*0.75))
    while boundary<n and accepted[boundary][0]==accepted[boundary-1][0]:boundary+=1
    train=accepted[:boundary]; test=accepted[boundary:]
    if len(train)<min_train or len(test)<min_test:
        return {**base,'reason':'Chronological test set too small after separating event-time groups',
                'train_n':len(train),'test_n':len(test)}
    if (test[-1][0]-test[0][0]).days<MIN_TEST_DAYS:
        return {**base,'reason':'Held-out evaluation must span at least 21 calendar days',
                'train_n':len(train),'test_n':len(test)}
    if len(set(x[3] for x in test)) < min_test:
        return {**base,'reason':'Insufficient distinct out-of-time events in holdout'}
    base_rate=mean(row[2] for row in train)
    vals=[(row[1],row[2]) for row in test]
    baseline=[(base_rate,y) for _,y in vals]
    model_brier=_brier(vals); baseline_brier=_brier(baseline)
    ece=_ece(vals)
    improvement=baseline_brier-model_brier
    meets=(ece<=MAX_EXPECTED_CALIBRATION_ERROR and improvement>=MIN_BRIER_IMPROVEMENT)
    return {**base,'status':'RESEARCH_GATE_PASSED' if meets else 'RESEARCH_GATE_FAILED',
            'validated_probability':False,
            'reason':('Quantitative preapproval checks passed; independent provenance, systematic calibration, and human model governance still required'
                      if meets else 'Held-out calibration or predictive advantage failed'),
            'train_n':len(train),'test_n':len(test),
            'train_period':[train[0][0].isoformat(),train[-1][0].isoformat()],
            'test_period':[test[0][0].isoformat(),test[-1][0].isoformat()],
            'brier_model':round(model_brier,5),'brier_constant_baseline':round(baseline_brier,5),
            'brier_improvement':round(improvement,5),'logloss_model':round(_logloss(vals),5),
            'ece_ten_bins':round(ece,5),
            'external_snapshot_provenance_verified':False,
            'joint_parlay_model_validated':False}


def probability_display_gate(*, audit:dict, externally_approved:bool, fresh:bool,
                             exact_model_match:bool, provider_lineage_verified:bool) -> dict:
    """Never present a numerical prediction from a mere historical hit frequency."""
    ok=all((audit.get('status')=='RESEARCH_GATE_PASSED',
            audit.get('external_snapshot_provenance_verified') is True,
            audit.get('validated_probability') is True, externally_approved,
            fresh,exact_model_match,provider_lineage_verified))
    return {'state':'VALIDATED_FOR_MARKET' if ok else 'NOT_SUPPORTED',
            'show_numeric_probability':ok,
            'reason':('Approved market-specific model with current input sources' if ok else
                      'Real held-out evaluation, provider provenance, current inputs and independent authorization are required')}
