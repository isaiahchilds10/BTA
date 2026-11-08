"""Server-side owner operations. Never expose service-role secret to frontend JS."""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
from bta.config import setting
from bta.storage.cloud import make_client


def owner_bootstrap() -> None:
    """Bootstrap only the exact configured owner email, if not yet installed."""
    email=setting('BTA_OWNER_EMAIL').strip().lower()
    if not email or '@' not in email: raise RuntimeError('BTA_OWNER_EMAIL required')
    admin=make_client(service=True)
    existing=admin.table('members').select('id').eq('email',email).limit(1).execute().data or []
    if existing: return
    created=admin.auth.admin.create_user({'email':email,'email_confirm':True})
    uid=created.user.id
    admin.table('members').insert({'id':uid,'email':email,'role':'owner', 'enabled':True,
        'invite_expires_at':(datetime.now(timezone.utc)+timedelta(days=3650)).isoformat()}).execute()
    audit(admin,uid,'owner_bootstrap',uid)


def audit(admin,actor_id:str|None,action:str,target_id:str|None=None,details:dict|None=None):
    admin.table('audit_events').insert({'actor_id':actor_id,'action':action,'target_id':target_id,'details':details or {}}).execute()


def invite_member(owner_id:str,email:str)->str:
    admin=make_client(service=True)
    owner=admin.table('members').select('role,enabled').eq('id',owner_id).limit(1).execute().data or []
    if not owner or owner[0]['role']!='owner' or not owner[0]['enabled']:
        raise PermissionError('Only owner may invite members')
    email=email.strip().lower()
    if not email or '@' not in email or len(email)>180: raise ValueError('Invalid email')
    exist=admin.table('members').select('id,enabled').eq('email',email).execute().data or []
    if exist: raise ValueError('Member already exists; re-enable explicitly in admin settings')
    created=admin.auth.admin.create_user({'email':email,'email_confirm':True})
    uid=created.user.id
    try:
        admin.table('members').insert({'id':uid,'email':email,'role':'member','enabled':True,
            'invite_expires_at':(datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}).execute()
        # Login magic link is dispatched via public auth endpoint on user's request; no fake email sent claim.
        audit(admin,owner_id,'invite_created',uid)
    except Exception:
        admin.auth.admin.delete_user(uid)
        raise
    return uid


def set_member_enabled(owner_id:str,member_id:str,enabled:bool)->None:
    admin=make_client(service=True)
    actor=admin.table('members').select('role,enabled').eq('id',owner_id).execute().data or []
    target=admin.table('members').select('role,enabled').eq('id',member_id).execute().data or []
    if not actor or actor[0]['role']!='owner' or not actor[0]['enabled'] or not target or target[0]['role']=='owner':
        raise PermissionError('Admin action forbidden')
    admin.table('members').update({'enabled':enabled}).eq('id',member_id).execute()
    audit(admin,owner_id,'member_enabled' if enabled else 'member_disabled',member_id)


def renew_member_invitation(owner_id:str,member_id:str)->None:
    """Explicit owner renewal when a 7-day Google OIDC approval expires."""
    admin=make_client(service=True)
    actor=admin.table('members').select('role,enabled').eq('id',owner_id).limit(1).execute().data or []
    target=admin.table('members').select('role,activated_at').eq('id',member_id).limit(1).execute().data or []
    if not actor or actor[0]['role']!='owner' or not actor[0]['enabled'] or not target or target[0]['role']=='owner':
        raise PermissionError('Only owner may renew a member approval')
    admin.table('members').update({'enabled':True,'invite_expires_at':
       (datetime.now(timezone.utc)+timedelta(days=7)).isoformat()}).eq('id',member_id).execute()
    audit(admin,owner_id,'invite_renewed',member_id)
