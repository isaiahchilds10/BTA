"""Invite-only Google OIDC authorization against the trusted Supabase backend.

The service-role client is server-only. No user-supplied ID or email is trusted:
identity comes exclusively from Streamlit's verified OIDC cookie, and membership
is checked on each app rerun. OIDC is identity, not permission to access data.
"""
from __future__ import annotations
from datetime import datetime, timezone
from bta.security.google_identity import GoogleIdentity
from bta.security.membership import audit
from bta.storage.cloud import make_client


def require_member(identity: GoogleIdentity) -> dict:
    admin = make_client(service=True)
    rows = (admin.table('members').select('id,email,role,enabled,activated_at,invite_expires_at,google_sub')
            .eq('email', identity.email).limit(1).execute().data or [])
    if len(rows) != 1:
        raise PermissionError('This Google account is not on the BTA member list')
    member=rows[0]
    if not member.get('enabled'):
        raise PermissionError('Your BTA membership is disabled')
    expires=member.get('invite_expires_at')
    if member.get('activated_at') is None:
        if not expires:
            raise PermissionError('Invitation expiry could not be verified')
        try:
            deadline=datetime.fromisoformat(expires.replace('Z','+00:00'))
        except (TypeError,ValueError):
            raise PermissionError('Invitation expiry is invalid') from None
        if deadline <= datetime.now(timezone.utc):
            raise PermissionError('Your invitation expired; ask the owner to renew it')
    saved_sub=member.get('google_sub')
    if saved_sub and saved_sub != identity.subject:
        raise PermissionError('This Google identity is not the one linked to your account')
    if saved_sub and member.get('activated_at') is None:
        # Reconcile an explicitly pre-bound account without weakening expiry.
        changed=(admin.table('members').update({'activated_at':datetime.now(timezone.utc).isoformat()})
                 .eq('id',member['id']).eq('google_sub',identity.subject)
                 .eq('enabled',True).execute().data or [])
        if not changed:raise PermissionError('Unable to activate your Google membership')
        member=changed[0]
    if not saved_sub:
        # Atomic bind prevents concurrent first-logins with different subjects.
        changed=(admin.table('members').update({'google_sub':identity.subject,
              'activated_at':datetime.now(timezone.utc).isoformat()})
              .eq('id',member['id']).is_('google_sub','null')
              .eq('enabled',True).execute().data or [])
        if not changed:
            raise PermissionError('Unable to bind Google identity; sign out and retry')
        audit(admin, member['id'], 'google_oidc_first_login', member['id'])
        member=changed[0]
    return member
