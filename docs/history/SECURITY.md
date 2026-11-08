# BTA 2.0 — Security / Privacy / Recovery

## Implemented controls (code-level)

- New independent Supabase project per installation. Public signups must be **disabled** by owner setup. Owner automatically provisions exact `BTA_OWNER_EMAIL` on server; only owner can add members. Sign-in uses `should_create_user=False` and email verification; server refuses accounts not present/enabled/unexpired in `members`.
- Row Level Security on `tickets`, `ticket_versions`, `reports`, `jobs`, `shares`, `members`, `audit_events`. Each member sees only their own slips and explicitly shared frozen snapshots. The authorization boundary is the database, not a hidden UI tab. Owner administration is restricted by a server-verified owner role.
- Every ticket update is committed through `save_ticket_version` with expected-version optimistic concurrency, and a new immutable version row. Prior pregame research reports are appended, never overwritten.
- Only trusted server-side research writes `reports`. The service-role key is never stored in GitHub source or sent to third-party AI.
- AI only receives allowlisted **public sports facts**, not user email, tokens, personal notes, or raw member histories. The input is screened for obvious personal identifiers and credentials, and all model text is unverified by design.
- Public sports URL adapters use explicit fixed HTTPS hosts and limited numeric IDs. Missing official injuries, exact market offers and proven live probability remain PENDING/UNAVAILABLE.
- Admin calls are server-scoped. Disabled members are rejected by login and RLS; revoked shared records are no longer visible to recipients. Revoking a share is a controlled SQL function, not client-side editing of a share row.
- Passwordless links are single-use Supabase Auth verification tokens. The app strips the one-time token query parameter after processing.
- Encrypted database snapshots can be collected through a GitHub Actions workflow that refuses PUBLIC repositories. Artifact retention is 14 days. Automatic checksum and isolated **SQLite row replay** validates the extraction; this is **not** an independently tested full Postgres restoration.

## Critical production gates still outstanding

- Real Supabase RLS A/B account testing, invite replay/expiry/revoke and abuse/rate limit tests in deployed environment.
- Reliable free-tier SMTP delivery to arbitrary external recipients; actual Gmail/Resend account and from domain eligibility.
- No HttpOnly secure session cookie is implemented by Streamlit; after hard refresh a member may need a new magic link. True persistent browser session requires a suitably authenticated frontend/session architecture.
- Full encrypted Supabase **PostgreSQL** restoration into a segregated service, re-check RLS, row counts, schema, and secrets rotation. Current isolated SQLite drill does not meet this gate.
- Mobile-browser visual tests, exact odds and official source license/redistribution tests, real live-feed freshness monitoring, provider failover/account quotas.
- Independent pentest and private beta. Do not put real member data into a public demo before completion.

## Operational guidance

Put credentials **only** in Streamlit Secrets and GitHub Actions secrets. Make the GitHub repo PRIVATE. Never place credentials, SMTP app passwords, database exports, screenshots of credentials or backup keys inside the ZIP/repository. Owner should use a dedicated minimal-permission service. Rotate immediately if leaked. No AI API automatically places bets.
