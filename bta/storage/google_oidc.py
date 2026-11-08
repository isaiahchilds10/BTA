"""Trusted-server Supabase storage for Streamlit's Google OIDC identity.

The service key is never given to the browser. All member reads/writes are
explicitly owner-scoped and validated server-side. RLS remains enabled in SQL
for all *direct* external database requests; service-role bypasses RLS, so
these explicit scoped checks are mandatory and security-tested.
"""
from __future__ import annotations
from bta.storage.cloud import make_client
from bta.domain import utcnow


class GoogleCloudStore:
    def __init__(self, member: dict):
        if not member.get('id') or not member.get('enabled'):
            raise PermissionError('Active membership required')
        self.c=make_client(service=True)
        self.uid=str(member['id'])
        self.role=member['role']

    def _owned_ticket(self, ticket_id: str) -> dict:
        rows=(self.c.table('tickets').select('id,owner_id,legs,version')
              .eq('id',str(ticket_id)).eq('owner_id',self.uid).limit(1).execute().data or [])
        if not rows:raise PermissionError('Ticket not found in your private account')
        return rows[0]

    def list_tickets(self) -> list[dict]:
        return (self.c.table('tickets').select('*').eq('owner_id',self.uid)
                .order('updated_at',desc=True).execute().data or [])

    def create_ticket(self, name:str) -> dict:
        label=(name or '').strip()[:100]
        if not label:raise ValueError('A ticket name is required')
        rows=(self.c.table('tickets').insert({'owner_id':self.uid,'name':label,
               'state':'DRAFT','legs':[]}).execute().data or [])
        if len(rows)!=1 or rows[0].get('owner_id')!=self.uid:
            raise PermissionError('Unable to create scoped ticket')
        return rows[0]

    def save_ticket(self, ticket:dict) -> dict:
        t=self._owned_ticket(str(ticket.get('id','')))
        if len(ticket.get('legs',[]))>30:raise ValueError('Maximum 30 legs per ticket')
        if str(ticket.get('owner_id',self.uid)) != self.uid:
            raise PermissionError('Cannot change ticket owner')
        if int(ticket.get('version',0))!=int(t['version']):
            raise ValueError('Version conflict: reload your ticket before editing')
        result=self.c.rpc('save_ticket_version_service',{'p_actor':self.uid,
            'p_ticket_id':t['id'],'p_expected_version':t['version'],
            'p_name':ticket['name'],'p_state':ticket['state'],
            'p_legs':ticket['legs']}).execute().data
        if isinstance(result,list):result=result[0] if result else None
        if not result or result.get('owner_id')!=self.uid:
            raise PermissionError('Ticket update was not committed to your account')
        return result

    def list_versions(self, ticket_id:str) -> list[dict]:
        self._owned_ticket(ticket_id)
        return (self.c.table('ticket_versions').select('version,snapshot,created_at')
                .eq('ticket_id',ticket_id).eq('owner_id',self.uid)
                .order('version',desc=True).execute().data or [])

    def list_reports(self, ticket_id:str) -> dict[str,dict]:
        self._owned_ticket(ticket_id)
        rows=(self.c.table('reports').select('selection_id,report,created_at')
              .eq('ticket_id',ticket_id).eq('owner_id',self.uid)
              .order('created_at').execute().data or [])
        return {r['selection_id']:r['report'] for r in rows}

    def add_report(self, ticket_id:str, selection_id:str, report:dict) -> None:
        raise PermissionError('Only the scheduled trusted worker may add research reports')

    def add_job(self, ticket_id:str, selection_id:str) -> None:
        ticket=self._owned_ticket(ticket_id)
        if not any(str(leg.get('id'))==str(selection_id) for leg in ticket['legs']):
            raise PermissionError('This selection does not belong to this ticket')
        self.c.table('jobs').insert({'owner_id':self.uid,'ticket_id':ticket_id,
             'selection_id':selection_id,'state':'queued'}).execute()

    def list_jobs(self,ticket_id:str|None=None)->list[dict]:
        q=self.c.table('jobs').select('id,ticket_id,selection_id,state,retries,updated_at').eq('owner_id',self.uid)
        if ticket_id:
            self._owned_ticket(ticket_id)
            q=q.eq('ticket_id',ticket_id)
        return q.order('updated_at',desc=True).execute().data or []

    def share_ticket(self,ticket:dict,recipient_id:str)->None:
        current=self._owned_ticket(ticket['id'])
        if current['owner_id']!=self.uid or recipient_id==self.uid:
            raise PermissionError('Invalid recipient or ticket')
        target=(self.c.table('members').select('id,enabled').eq('id',recipient_id)
                .eq('enabled',True).limit(1).execute().data or [])
        if not target:raise PermissionError('Recipient is not an active member')
        safe_legs=[{k:v for k,v in item.items() if k not in {'notes'}} for item in current['legs']]
        snap={'name':ticket['name'],'state':ticket['state'],'legs':safe_legs,'shared_at':utcnow()}
        self.c.table('shares').insert({'owner_id':self.uid,'recipient_id':recipient_id,
             'ticket_id':ticket['id'],'frozen_snapshot':snap}).execute()

    def list_shares(self)->list[dict]:
        outgoing=(self.c.table('shares').select('*').eq('owner_id',self.uid).execute().data or [])
        incoming=(self.c.table('shares').select('*').eq('recipient_id',self.uid)
                 .eq('revoked',False).execute().data or [])
        by_id={item['id']:item for item in outgoing+incoming}
        return sorted(by_id.values(),key=lambda x:x.get('created_at',''),reverse=True)

    def revoke_share(self,share_id:str)->None:
        rows=(self.c.table('shares').update({'revoked':True}).eq('id',share_id)
              .eq('owner_id',self.uid).execute().data or [])
        if not rows:raise PermissionError('Share not found or already revoked')
