-- BTA 2.0 ONE-TIME INSTALL. Dedicated new Supabase project only.

-- BTA 2.0 · INITIAL SCHEMA · RUN ONCE IN A NEW SUPABASE PROJECT
-- Private by default. Do not run against the user's older project.
create extension if not exists pgcrypto;

create table if not exists public.members (
 id uuid primary key references auth.users(id) on delete cascade,
 email text not null unique,
 role text not null default 'member' check (role in ('owner','member')),
 enabled boolean not null default true,
 invite_expires_at timestamptz not null default (now()+interval '7 days'),
 activated_at timestamptz,
 created_at timestamptz not null default now()
);
create table if not exists public.tickets (
 id uuid primary key default gen_random_uuid(),
 owner_id uuid not null references public.members(id) on delete cascade,
 name text not null check (length(name) between 1 and 100),
 state text not null default 'DRAFT' check (state in ('DRAFT','ACTIVE','ARCHIVED')),
 legs jsonb not null default '[]'::jsonb check (jsonb_typeof(legs)='array' and jsonb_array_length(legs)<=30),
 version integer not null default 1 check (version>0),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists tickets_owner_date on public.tickets(owner_id,updated_at desc);
create table if not exists public.ticket_versions (
 id uuid primary key default gen_random_uuid(),
 ticket_id uuid not null references public.tickets(id) on delete cascade,
 owner_id uuid not null references public.members(id) on delete cascade,
 version integer not null,
 snapshot jsonb not null,
 created_at timestamptz not null default now(),
 unique(ticket_id, version)
);
create table if not exists public.reports (
 id uuid primary key default gen_random_uuid(),
 ticket_id uuid not null references public.tickets(id) on delete cascade,
 owner_id uuid not null references public.members(id) on delete cascade,
 selection_id uuid not null,
 report jsonb not null,
 created_at timestamptz not null default now()
);
create index if not exists reports_lookup on public.reports(ticket_id,selection_id,created_at desc);
create table if not exists public.jobs (
 id uuid primary key default gen_random_uuid(),
 ticket_id uuid not null references public.tickets(id) on delete cascade,
 owner_id uuid not null references public.members(id) on delete cascade,
 selection_id uuid not null,
 state text not null default 'queued' check (state in ('queued','retrieving','checking_injuries','testing_scripts','retry','pending_evidence','complete','failed')),
 retries integer not null default 0,
 next_attempt timestamptz not null default now(),
 claimed_at timestamptz,
 updated_at timestamptz not null default now(),
 last_error text,
 created_at timestamptz not null default now()
);
create index if not exists jobs_next on public.jobs(state,next_attempt,created_at);
create table if not exists public.shares (
 id uuid primary key default gen_random_uuid(),
 ticket_id uuid not null references public.tickets(id) on delete cascade,
 owner_id uuid not null references public.members(id) on delete cascade,
 recipient_id uuid not null references public.members(id) on delete cascade,
 frozen_snapshot jsonb not null,
 revoked boolean not null default false,
 created_at timestamptz not null default now(),
 check (owner_id<>recipient_id)
);
create table if not exists public.audit_events (
 id uuid primary key default gen_random_uuid(),
 actor_id uuid,
 action text not null,
 target_id uuid,
 details jsonb not null default '{}'::jsonb,
 created_at timestamptz not null default now()
);

create or replace function public.member_enabled(p_uid uuid) returns boolean
 language sql security definer stable set search_path='' as $$
 select exists (select 1 from public.members m where m.id=p_uid and m.enabled
 and (m.activated_at is not null or m.invite_expires_at>now()));
 $$;
revoke all on function public.member_enabled(uuid) from public,anon;
grant execute on function public.member_enabled(uuid) to authenticated,service_role;

alter table public.members enable row level security;
alter table public.tickets enable row level security;
alter table public.ticket_versions enable row level security;
alter table public.reports enable row level security;
alter table public.jobs enable row level security;
alter table public.shares enable row level security;
alter table public.audit_events enable row level security;

create policy member_self_select on public.members for select to authenticated using (id=auth.uid());
create policy tickets_select on public.tickets for select to authenticated using(owner_id=auth.uid() and public.member_enabled(auth.uid()));
create policy tickets_create on public.tickets for insert to authenticated with check(owner_id=auth.uid() and public.member_enabled(auth.uid()) and legs='[]'::jsonb and version=1);
-- Never allow direct updates to versioned tickets; only RPC.
create policy version_select on public.ticket_versions for select to authenticated using(owner_id=auth.uid() and public.member_enabled(auth.uid()));
create policy reports_select on public.reports for select to authenticated using(owner_id=auth.uid() and public.member_enabled(auth.uid()));
create policy jobs_select on public.jobs for select to authenticated using(owner_id=auth.uid() and public.member_enabled(auth.uid()));
create policy jobs_enqueue on public.jobs for insert to authenticated with check (
 owner_id=auth.uid() and public.member_enabled(auth.uid()) and state='queued' and retries=0
 and exists(select 1 from public.tickets t where t.id=ticket_id and t.owner_id=auth.uid()
 and exists(select 1 from jsonb_array_elements(t.legs) leg where leg->>'id'=selection_id::text))
);
create policy shares_read on public.shares for select to authenticated using(
 public.member_enabled(auth.uid()) and (owner_id=auth.uid() or (recipient_id=auth.uid() and not revoked))
);
create policy shares_insert on public.shares for insert to authenticated with check(
 owner_id=auth.uid() and public.member_enabled(auth.uid())
 and exists(select 1 from public.tickets t where t.id=ticket_id and t.owner_id=auth.uid())
 and public.member_enabled(recipient_id)
);
create policy shares_owner_revoke on public.shares for update to authenticated using(owner_id=auth.uid() and public.member_enabled(auth.uid())) with check(owner_id=auth.uid() and revoked=true);

-- This RPC atomically writes each revision and prevents overwriting a newer version.
create or replace function public.save_ticket_version(
 p_ticket_id uuid, p_expected_version integer, p_name text, p_state text, p_legs jsonb
) returns public.tickets language plpgsql security definer set search_path='' as $$
declare t public.tickets;
begin
 if not public.member_enabled(auth.uid()) then raise exception 'not authorized'; end if;
 if p_legs is null or jsonb_typeof(p_legs)<>'array' or jsonb_array_length(p_legs)>30
   or length(coalesce(p_name,'')) not between 1 and 100
   or p_state not in ('DRAFT','ACTIVE','ARCHIVED') then raise exception 'invalid ticket'; end if;
 update public.tickets set name=p_name,state=p_state,legs=p_legs,version=version+1,updated_at=now()
 where id=p_ticket_id and owner_id=auth.uid() and version=p_expected_version returning * into t;
 if not found then raise exception 'ticket not found or version conflict'; end if;
 insert into public.ticket_versions(ticket_id,owner_id,version,snapshot)
 values(t.id,t.owner_id,t.version,to_jsonb(t));
 return t;
end $$;
revoke all on function public.save_ticket_version(uuid,integer,text,text,jsonb) from public,anon;
grant execute on function public.save_ticket_version(uuid,integer,text,text,jsonb) to authenticated;

-- Seed original version via AFTER INSERT, never mutable historical snapshots.
create or replace function public.initial_ticket_version() returns trigger language plpgsql security definer set search_path='' as $$
begin
 insert into public.ticket_versions(ticket_id,owner_id,version,snapshot)
 values(new.id,new.owner_id,new.version,to_jsonb(new)); return new;
end $$;
drop trigger if exists initial_ticket_version_trigger on public.tickets;
create trigger initial_ticket_version_trigger after insert on public.tickets for each row execute function public.initial_ticket_version();

-- Server-managed activation records first successful authenticated login; membership must already exist.
create or replace function public.activate_my_invitation() returns boolean language plpgsql security definer set search_path='' as $$
declare changed integer;
begin
 update public.members m set activated_at=coalesce(m.activated_at,now())
 where m.id=auth.uid() and m.enabled and (m.activated_at is not null or m.invite_expires_at>now());
 get diagnostics changed=row_count;
 return changed=1;
end $$;
revoke all on function public.activate_my_invitation() from public,anon;
grant execute on function public.activate_my_invitation() to authenticated;

-- Callable ONLY with service-role JWT by scheduled worker.
create or replace function public.claim_next_job() returns setof public.jobs language plpgsql security definer set search_path='' as $$
declare j public.jobs;
begin
 select * into j from public.jobs
 where (state in ('queued','retry') or (state in ('retrieving','checking_injuries','testing_scripts') and claimed_at<now()-interval '15 minutes'))
 and next_attempt<=now() order by created_at asc for update skip locked limit 1;
 if not found then return; end if;
 update public.jobs set state='retrieving', claimed_at=now(), updated_at=now() where id=j.id returning * into j;
 return next j;
end $$;
revoke all on function public.claim_next_job() from public,anon,authenticated;
grant execute on function public.claim_next_job() to service_role;

-- Audit events are written by service-role actions, never by members.
-- Row-level policies intentionally grant no reads of the private audit trail.
-- Revoke by exact RPC, cannot rewrite recipient/content of shared snapshots.
drop policy if exists shares_owner_revoke on public.shares;
create or replace function public.revoke_my_share(p_share_id uuid) returns void language plpgsql security definer set search_path='' as $$
begin
 update public.shares set revoked=true where id=p_share_id and owner_id=auth.uid();
 if not found then raise exception 'share not found'; end if;
end $$;
revoke all on function public.revoke_my_share(uuid) from public,anon;
grant execute on function public.revoke_my_share(uuid) to authenticated;


-- Run AFTER 001_schema.sql in the NEW BTA Supabase project.
-- Genuine pregame snapshots are append-only via service-role worker inserts.
create table if not exists public.pregame_freezes (
 id uuid primary key default gen_random_uuid(),
 ticket_id uuid not null references public.tickets(id) on delete cascade,
 owner_id uuid not null references public.members(id) on delete cascade,
 selection_id uuid not null,
 game_start timestamptz not null,
 frozen_at timestamptz not null,
 evidence_hash text not null check (length(evidence_hash)=64),
 research_snapshot jsonb not null,
 probability_state text not null default 'NOT_SUPPORTED',
 created_at timestamptz not null default now(),
 check (frozen_at < game_start)
);
create index if not exists freezes_by_leg on public.pregame_freezes
 (ticket_id, selection_id, frozen_at desc);
alter table public.pregame_freezes enable row level security;
drop policy if exists freezes_owner_select on public.pregame_freezes;
create policy freezes_owner_select on public.pregame_freezes
 for select to authenticated
 using (owner_id=auth.uid() and public.member_enabled(auth.uid()));
-- No INSERT/UPDATE/DELETE policies for member JWTs. Service-role worker only.


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
