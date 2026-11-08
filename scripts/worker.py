"""Scheduled, durable per-leg research worker. Runtime source retrieval is never simulated.

GitHub Actions is a delayed best-effort scheduler, not guaranteed realtime monitoring.
"""
from __future__ import annotations
import os
from datetime import datetime,timezone,timedelta
from bta.storage.cloud import make_client
from bta.domain import Selection
from bta.research.workflow import research_leg


def scan_active_tickets(admin,*,max_tickets=120) -> int:
    """Enqueue targeted refreshes with deduplication and conservative free-quota limits."""
    now=datetime.now(timezone.utc)
    tickets=admin.table('tickets').select('id,owner_id,legs').eq('state','ACTIVE').order('updated_at',desc=True).limit(max_tickets).execute().data or []
    queued=0
    for ticket in tickets:
        for raw in ticket.get('legs',[]):
            try:
                start=datetime.fromisoformat(raw['game_start'].replace('Z','+00:00'))
            except (ValueError,KeyError,TypeError):continue
            if start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
            if start < now-timedelta(hours=5) or start>now+timedelta(days=4):continue
            recent=admin.table('jobs').select('created_at').eq('ticket_id',ticket['id']).eq('selection_id',raw['id']).gte('created_at',(now-timedelta(minutes=30 if start-now<timedelta(hours=6) else 120)).isoformat()).limit(1).execute().data or []
            if recent:continue
            admin.table('jobs').insert({'ticket_id':ticket['id'],'owner_id':ticket['owner_id'],'selection_id':raw['id'],'state':'queued'}).execute()
            queued+=1
            if queued>=30:return queued
    return queued


def run(batch_size:int=12) -> int:
    if os.getenv('BTA_MODE')!='private':raise RuntimeError('Worker requires private mode')
    admin=make_client(service=True)
    # A full provider outage should not stop tickets from remaining in the durable job store.
    try:scan_active_tickets(admin)
    except Exception:pass
    completed=0
    for _ in range(batch_size):
        claimed=admin.rpc('claim_next_job').execute().data or []
        if not claimed:break
        job=claimed[0] if isinstance(claimed,list) else claimed
        try:
            tickets=admin.table('tickets').select('id,owner_id,legs').eq('id',job['ticket_id']).eq('owner_id',job['owner_id']).execute().data or []
            if not tickets:raise PermissionError('Original ticket unavailable')
            leg=next((x for x in tickets[0]['legs'] if x.get('id')==job['selection_id']),None)
            if not leg:raise ValueError('Selection deleted or updated')
            report=research_leg(Selection(**leg),with_ai=True)
            # Save pregame freeze BEFORE the report so an absent migration
            # cannot generate multiple duplicate report rows on job retries.
            from bta.models.frozen_evidence import persist_owner_freeze
            persist_owner_freeze(admin,job,Selection(**leg),report)
            admin.table('reports').insert({'ticket_id':job['ticket_id'],'owner_id':job['owner_id'],
                'selection_id':job['selection_id'],'report':report}).execute()
            state='pending_evidence' if report['grade']=='PENDING VERIFICATION' else 'complete'
            admin.table('jobs').update({'state':state,'updated_at':datetime.now(timezone.utc).isoformat()}).eq('id',job['id']).execute()
            completed+=1
        except Exception as exc:
            attempts=int(job.get('retries',0))+1
            admin.table('jobs').update({'state':'failed' if attempts>=5 else 'retry',
                'retries':attempts,'last_error':type(exc).__name__,
                'next_attempt':(datetime.now(timezone.utc)+timedelta(minutes=5*2**min(attempts,4))).isoformat(),
                'updated_at':datetime.now(timezone.utc).isoformat()}).eq('id',job['id']).execute()
    return completed

if __name__=='__main__':print('Completed:',run())
