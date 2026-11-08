"""End-to-end ticket research. Real observations always outrank model commentary."""
from __future__ import annotations
from dataclasses import dataclass
from bta.domain import Selection
from bta.research.engine import analyze, assess_ticket
from bta.ai.providers import investigate


def research_leg(selection:Selection, *, with_ai:bool=True) -> dict:
    report=analyze(selection)
    # Preserve the original immutable deterministic report, append optional context.
    if with_ai:
        report['ai']=investigate(report)
    else:
        report['ai']={'researcher':{'status':'NOT_REQUESTED'},'critic':{'status':'NOT_REQUESTED'}}
    return report


def persist_report_as_owner(ticket:dict, selection:Selection, report:dict) -> None:
    """Trusted server writes to the exact owner ticket ONLY, not arbitrary client-selected ID."""
    from bta.storage.cloud import make_client
    admin=make_client(service=True)
    own=admin.table('tickets').select('id,owner_id,legs').eq('id',ticket['id']).eq('owner_id',ticket['owner_id']).limit(1).execute().data or []
    if not own or not any(l.get('id')==selection.id for l in own[0]['legs']):
        raise PermissionError('No authorized leg found on this ticket')
    admin.table('reports').insert({'ticket_id':ticket['id'],'owner_id':ticket['owner_id'],
        'selection_id':selection.id,'report':report}).execute()


def recheck_leg_as_user(store,ticket:dict,selection:Selection,*,with_ai=True)->dict:
    """Immediate authenticated request; never pass `verified` booleans from browser to verifier."""
    if store.uid != ticket.get('owner_id') or not any(l.get('id')==selection.id for l in ticket.get('legs',[])):
        raise PermissionError('Ticket access denied')
    report=research_leg(selection,with_ai=with_ai)
    persist_report_as_owner(ticket,selection,report)
    return report


def submit_full_ticket(store,ticket:dict, progress=None, *, with_ai=True) ->dict:
    """Researches legs in original order, versions reports, and returns parlay audit.

    This is synchronous and best suited to short tickets. A 30-leg ticket can be slow;
    failure per leg is reported and workers can process queued jobs later.
    """
    legs=[Selection(**item) for item in ticket.get('legs',[])]
    reports=store.list_reports(ticket['id'])
    for i,leg in enumerate(legs,1):
        if progress: progress(i,len(legs),leg)
        try:
            if store.__class__.__name__=='LocalStore':
                report=research_leg(leg,with_ai=with_ai)
                store.add_report(ticket['id'],leg.id,report)
            else:
                report=recheck_leg_as_user(store,ticket,leg,with_ai=with_ai)
            reports[leg.id]=report
        except Exception as exc:
            # Preserve prior complete report; no false successful claims.
            reports.setdefault(leg.id,{'grade':'PENDING VERIFICATION','status':'RETRY NEEDED',
                'grade_reason':f'Analysis temporarily unavailable ({type(exc).__name__})',
                'blockers':['Data provider or analysis job did not complete'], 'scripts':[]})
            try:store.add_job(ticket['id'],leg.id)
            except Exception:pass
    return {'reports':reports,'parlay':assess_ticket(legs,reports)}


def enqueue_full_ticket(store,ticket:dict)->dict:
    """Request durable asynchronous research of all exact legs, with basic deduplication.

    This fast path avoids holding the Streamlit request open for 30 x several AI calls.
    GitHub's scheduled worker must actually be configured for progress to continue
    when the user navigates away. No fake completion percentages are shown.
    """
    legs=[Selection(**item) for item in ticket.get('legs',[])]
    if len(legs)>30:raise ValueError('Only 30 exact selections per ticket')
    existing=store.list_jobs(ticket['id'])
    queued_ids={str(j['selection_id']) for j in existing if j.get('state') in
                {'queued','retrieving','checking_injuries','testing_scripts','retry'}}
    queued=0;already=0;failed=0
    for leg in legs:
        if leg.id in queued_ids:
            already+=1
            continue
        try:
            store.add_job(ticket['id'],leg.id)
            queued+=1
        except Exception:
            failed+=1
    reports=store.list_reports(ticket['id'])
    return {'new_queued':queued,'already_queued':already,'failed_to_queue':failed,
            'total':len(legs),'parlay':assess_ticket(legs,reports)}
