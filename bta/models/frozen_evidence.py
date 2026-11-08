"""Frozen pregame evidence records: actual-source audits, never inferred probabilities.

Immutable insert-only snapshots let us accumulate genuine pre-event research and
later join official settlements. No synthetic probability is generated here.
"""
from __future__ import annotations
from datetime import datetime,timezone
from hashlib import sha256
import json
from bta.domain import Selection, utcnow
from bta.research.gates import timestamp

PUBLIC_FIELDS=(
    'status','grade','grade_reason','history','scripts','verification_gates',
    'independent_audit','role_evidence','official_availability','opponent_evidence',
    'market_verification','settlement_evidence','source_url','source_context',
    'blockers','failure_paths','source_type','data_issue','evidence_quality',
)


def create_pregame_freeze(selection:Selection,report:dict,*,at:str|None=None)->dict|None:
    """Freeze real observed report only before actual kickoff.

    A hash proves bytes were not modified *after* creation; it does not
    independently prove that an upstream publisher was authoritative.
    """
    at=at or utcnow()
    started=timestamp(selection.game_start)
    frozen=timestamp(at)
    report_checked=timestamp(report.get('checked_at'))
    if not (started and frozen and report_checked and report_checked<=frozen<started):
        return None
    snapshot={key:report.get(key) for key in PUBLIC_FIELDS if key in report}
    snapshot['game_id']=selection.game_id
    snapshot['sport']=selection.sport
    snapshot['market']=selection.market
    snapshot['subject']=selection.subject
    snapshot['direction']=selection.direction
    snapshot['threshold']=selection.threshold
    snapshot['inclusive']=selection.inclusive
    snapshot['game_start']=started.isoformat()
    snapshot['forecast_cutoff']=frozen.isoformat()
    # Exclude AI narrative, passwords and account metadata, and bound DB rows.
    payload=json.dumps(snapshot,sort_keys=True,separators=(',',':'),default=str)
    if len(payload.encode())>180_000:return None
    return {'selection_id':selection.id,'game_start':started.isoformat(),
            'frozen_at':frozen.isoformat(),'evidence_hash':sha256(payload.encode()).hexdigest(),
            'research_snapshot':snapshot,'probability_state':'NOT_SUPPORTED'}


def persist_owner_freeze(admin,job:dict,selection:Selection,report:dict)->bool:
    freeze=create_pregame_freeze(selection,report)
    if freeze is None:return False
    # Caller is trusted scheduled worker; owner/ticket membership is already
    # checked from the DB before research. No client can write this table.
    admin.table('pregame_freezes').insert({'ticket_id':job['ticket_id'],
        'owner_id':job['owner_id'],**freeze}).execute()
    return True
