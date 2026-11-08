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
