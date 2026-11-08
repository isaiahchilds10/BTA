"""Server-only Supabase gateway for Google OIDC edition.

The project secret never leaves trusted Python. No direct member JWT client or
Supabase magic-link auth is used. Use GoogleCloudStore for all member IO.
"""
from __future__ import annotations
from bta.config import setting


def make_client(service: bool = False):
    from supabase import create_client
    url=setting('SUPABASE_URL')
    key=(setting('SUPABASE_SECRET_KEY') or setting('SUPABASE_SERVICE_ROLE_KEY')) if service else (setting('SUPABASE_PUBLISHABLE_KEY') or setting('SUPABASE_ANON_KEY'))
    if not url.startswith('https://') or not key:
        raise RuntimeError('Supabase project URL/key not configured')
    return create_client(url,key)


def lookup_member_for_sharing(requester_id:str,recipient_email:str) -> list[dict]:
    """Exact lookup permitted only when requester's membership remains active."""
    email=recipient_email.strip().lower()
    if '@' not in email or len(email)>180:
        return []
    admin=make_client(service=True)
    requester=(admin.table('members').select('id,enabled,google_sub')
               .eq('id',requester_id).eq('enabled',True).limit(1).execute().data or [])
    if not requester or not requester[0].get('google_sub'):
        raise PermissionError('Member access denied')
    return (admin.table('members').select('id,enabled').eq('email',email)
            .eq('enabled',True).limit(1).execute().data or [])
