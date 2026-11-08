"""Offline security regression tests for Gmail-free invite-only Google OIDC."""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import pytest

from bta.security.google_identity import validate_google_claims, GoogleIdentity
from bta.security import google_membership
from bta.storage import google_oidc
from bta.ai.providers import select_specialist_task


def claims(**kwargs):
    return {"email":"Approved@Example.com", "email_verified":True,
            "sub":"10010000000000000001", "iss":"https://accounts.google.com",**kwargs}


def test_google_verified_identity_required():
    x=validate_google_claims(claims())
    assert x.email=="approved@example.com" and x.subject.startswith("100")
    for payload in (claims(email_verified=False), claims(sub=""),
                    claims(iss="https://fake.example"), claims(email="other")):
        with pytest.raises(PermissionError):validate_google_claims(payload)


class Response:
    def __init__(self,data):self.data=data


class Query:
    def __init__(self,db,name):
        self.db,self.name,self.filters,self.operation,self.payload=db,name,[],"select",None
    def select(self,*args,**kwargs):return self
    def eq(self,key,value):self.filters.append((key,value));return self
    def is_(self,key,value):self.filters.append((key,None if value=="null" else value));return self
    def limit(self,*args,**kwargs):return self
    def order(self,*args,**kwargs):return self
    def insert(self,payload):self.operation='insert';self.payload=payload;return self
    def update(self,payload):self.operation='update';self.payload=payload;return self
    def execute(self):
        self.db.calls.append((self.name,self.operation,dict(self.filters),self.payload))
        data=[dict(item) for item in self.db.rows.get(self.name,[]) if
              all(item.get(key)==value for key,value in self.filters)]
        if self.operation=='update':
            for original in self.db.rows.get(self.name,[]):
                if all(original.get(key)==value for key,value in self.filters):
                    original.update(self.payload)
            data=[dict(item) for item in self.db.rows.get(self.name,[]) if
                  all(item.get(key)==value for key,value in self.filters if key not in self.payload)]
        if self.operation=='insert':data=[self.payload]
        return Response(data)


class DB:
    def __init__(self,rows):self.rows=rows;self.calls=[]
    def table(self,name):return Query(self,name)


def test_unknown_google_member_denied(monkeypatch):
    db=DB({'members':[]})
    monkeypatch.setattr(google_membership,'make_client',lambda service:db)
    with pytest.raises(PermissionError,match='not on the BTA member list'):
        google_membership.require_member(GoogleIdentity('testsubject','unknown@example.com'))


def test_google_member_binds_once_and_prevents_other_subject(monkeypatch):
    db=DB({'members':[{'id':'id1','email':'approved@example.com','role':'member','enabled':True,
                      'google_sub':None,'activated_at':None,
                      'invite_expires_at':(datetime.now(timezone.utc)+timedelta(days=3)).isoformat()}]})
    monkeypatch.setattr(google_membership,'make_client',lambda service:db)
    monkeypatch.setattr(google_membership,'audit',lambda *args,**kwargs:None)
    member=google_membership.require_member(GoogleIdentity('google123','approved@example.com'))
    assert member['google_sub']=='google123' and member['activated_at']
    assert google_membership.require_member(GoogleIdentity('google123','approved@example.com'))['id']=='id1'
    with pytest.raises(PermissionError,match='not the one linked'):
        google_membership.require_member(GoogleIdentity('other-google','approved@example.com'))


def test_expired_and_disabled_invites_denied(monkeypatch):
    for enabled, days in [(True,-1),(False,3)]:
        db=DB({'members':[{'id':'id1','email':'approved@example.com','role':'member',
             'enabled':enabled,'google_sub':None,'activated_at':None,
             'invite_expires_at':(datetime.now(timezone.utc)+timedelta(days=days)).isoformat()}]})
        monkeypatch.setattr(google_membership,'make_client',lambda service:db)
        with pytest.raises(PermissionError):
            google_membership.require_member(GoogleIdentity('google123','approved@example.com'))


def test_trusted_storage_denies_cross_account_ticket_read(monkeypatch):
    db=DB({'tickets':[{'id':'own','owner_id':'alice','legs':[], 'version':1},
                      {'id':'foreign','owner_id':'bob','legs':[], 'version':1}],
           'reports':[{'selection_id':'sample','owner_id':'bob','ticket_id':'foreign','report':{}}]})
    monkeypatch.setattr(google_oidc,'make_client',lambda service:db)
    store=google_oidc.GoogleCloudStore({'id':'alice','enabled':True,'role':'member'})
    assert [t['id'] for t in store.list_tickets()]==['own']
    with pytest.raises(PermissionError):store.list_reports('foreign')
    with pytest.raises(PermissionError):store.list_versions('foreign')
    with pytest.raises(PermissionError):store.add_job('foreign','sample')
    with pytest.raises(PermissionError):store.save_ticket({'id':'foreign','version':1,'owner_id':'bob','legs':[]})
    assert db.calls and all(op=='select' for _,op,_,_ in db.calls)


def test_specialist_routes_nested_verification_results():
    assert select_specialist_task({'verification_gates':{'participation':{'passed':False}}})[0]=='AVAILABILITY_SPECIALIST'
    assert select_specialist_task({'verification_gates':{'role':{'passed':False}}})[0]=='ROLE_OPPORTUNITY_SPECIALIST'
    assert select_specialist_task({'verification_gates':{'opponent':{'passed':False}}})[0]=='MATCHUP_SPECIALIST'
    assert select_specialist_task({'verification_gates':{'market':{'passed':False}}})[0]=='EXACT_MARKET_SPECIALIST'


def test_migration_is_service_only_and_ui_has_no_email_login():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    sql=(root/'sql/003_google_oidc_membership.sql').read_text()
    ui=(root/'streamlit_app.py').read_text()
    assert "auth.role() is distinct from 'service_role'" in sql
    assert 'owner_id=p_actor' in sql
    assert 'revoke all on function public.save_ticket_version_service' in sql
    assert 'st.login()' in ui and 'st.logout()' in ui
    assert 'sign_in_with_otp' not in ui
    assert 'Email me a sign-in link' not in ui
    assert (root/'assets/bta_belt_branding_logo.png').is_file()
