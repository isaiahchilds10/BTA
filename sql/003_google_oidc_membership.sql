-- BTA 2.0 | Add after 001_schema.sql and 002_pregame_freezes.sql
-- Streamlit validates Google OIDC sessions. The trusted server checks this
-- identity binding before using the service-role API with owner-scoped filters.
-- Google OIDC NEVER grants direct PostgREST service-role credentials.
alter table public.members add column if not exists google_sub text;
create unique index if not exists members_google_sub_unique on public.members(google_sub)
  where google_sub is not null;

-- Service-role-only atomic, versioned ticket update. The caller is the trusted
-- Streamlit server; member browser identities are never permitted to call it.
-- Preserve original immutable ticket_versions via trigger/version transaction.
create or replace function public.save_ticket_version_service(
 p_actor uuid, p_ticket_id uuid, p_expected_version integer,
 p_name text, p_state text, p_legs jsonb
) returns public.tickets language plpgsql security definer set search_path='' as $$
declare t public.tickets;
begin
 if auth.role() is distinct from 'service_role' then raise exception 'not authorized'; end if;
 if not exists(select 1 from public.members m where m.id=p_actor and m.enabled and
    (m.activated_at is not null or m.invite_expires_at>now()) and m.google_sub is not null)
 then raise exception 'not an active bound member'; end if;
 if p_legs is null or jsonb_typeof(p_legs)<>'array' or jsonb_array_length(p_legs)>30
   or length(coalesce(p_name,'')) not between 1 and 100
   or p_state not in ('DRAFT','ACTIVE','ARCHIVED') then raise exception 'invalid ticket'; end if;
 update public.tickets set name=p_name,state=p_state,legs=p_legs,
      version=version+1,updated_at=now()
 where id=p_ticket_id and owner_id=p_actor and version=p_expected_version
 returning * into t;
 if not found then raise exception 'ticket not found or version conflict'; end if;
 insert into public.ticket_versions(ticket_id,owner_id,version,snapshot)
 values(t.id,t.owner_id,t.version,to_jsonb(t));
 return t;
end $$;
revoke all on function public.save_ticket_version_service(uuid,uuid,integer,text,text,jsonb)
 from public,anon,authenticated;
grant execute on function public.save_ticket_version_service(uuid,uuid,integer,text,text,jsonb)
 to service_role;

-- Google OIDC is the ONLY supported interactive member auth in this edition.
-- Direct Supabase Auth JWTs must not access member data: the trusted app server
-- authorizes the Google subject separately. No client has a database key.
drop policy if exists member_self_select on public.members;
drop policy if exists tickets_select on public.tickets;
drop policy if exists tickets_create on public.tickets;
drop policy if exists version_select on public.ticket_versions;
drop policy if exists reports_select on public.reports;
drop policy if exists jobs_select on public.jobs;
drop policy if exists jobs_enqueue on public.jobs;
drop policy if exists shares_read on public.shares;
drop policy if exists shares_insert on public.shares;
drop policy if exists shares_owner_revoke on public.shares;
revoke all on public.members,public.tickets,public.ticket_versions,public.reports,
 public.jobs,public.shares,public.audit_events from anon, authenticated;
revoke execute on function public.save_ticket_version(uuid,integer,text,text,jsonb) from authenticated;
revoke execute on function public.activate_my_invitation() from authenticated;
revoke execute on function public.revoke_my_share(uuid) from authenticated;
-- Tables still have RLS enabled, with no general authenticated grants/policies.
-- Only the trusted backend uses its project secret, which must stay server-side.
revoke execute on function public.member_enabled(uuid) from authenticated;
