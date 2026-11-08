# BTA 2.0 — BELT TO ASS

**One independent GitHub-ready Streamlit application. No Gmail, no SMTP, no emailed magic links.**

The private member login is **Continue with Google**, backed by Google's OpenID Connect identity through Streamlit `st.login()` and an owner-controlled membership allowlist in Supabase. The original red/black/charcoal sportsbook-style interface and exact `assets/bta_belt_branding_logo.png` artwork remain intact.

**START HERE: [`START_HERE.md`](START_HERE.md)** — the only deployment checklist you need to follow.

## Five screens, no maze of menus

- **Home:** NBA/NFL/college schedules, live/upcoming fixtures, existing BTA Finds, saved slips and evidence states.
- **NBA:** Open a game → Points, Threes, Rebounds, Assists, Combos, Defense, Game Lines → roster-qualified players → exact lines.
- **NFL:** Open a game → Passing, Receiving, Rushing, Touchdowns, Game Lines, with position filters.
- **College Football:** FBS-first matchups, game lines and supported position-filtered player markets.
- **My Slip:** Up to 30 legs, mixed leagues, exact original market saved, submit entire ticket, individual BTA reports, combined parlay correlation and risk audit, revisions, decisions and read-only sharing.

A floating **Ask BTA** popover is available on every page and never upgrades grades or verifies stats by itself.

## Research and trust model

- Evidence retrieved from ESPN official/unofficial endpoints as explicitly labeled; NFL league injury pages, nflverse supplemental weekly datasets, conference-level college availability hubs, CollegeFootballData, NBA league injury documents and more, where provider access allows.
- Independently rechecked PropLine/ParlayAPI quotes when actual data is provided; manual thresholds otherwise marked **MARKET NOT VERIFIED**.
- Adaptive Groq/Gemini/Cloudflare AI specialists and independent adversarial critic with bounded, quota-aware failover. Models may analyze evidence but cannot mint source facts, market offers or verified BTA grades.
- Deterministic BTA research, distinct NFL/CFB/NBA game-script analysis, two-WORSE prop cut rule, exact threshold/YES/NO/settlement and historical performance checks, plus chronological freeze and forecast calibration safeguards.
- **No invented hit percentages.** Numeric forecasts are absent unless actual sport/market-level held-out validation supports them. Unverified decisive source inputs lead to **PENDING VERIFICATION**, not fake TAIG or BTA+.

## Private access architecture

Google OIDC tokens are verified by Streamlit, and an email + stable Google subject are checked against preapproved membership at each app rerun. The project secret key stays on the **trusted server only**; every member ticket request is explicitly scoped to its approved member ID. Supabase direct anonymous/authenticated data grants are revoked in migration 003, and the tables retain RLS. **Service-role requests bypass RLS**, so the server-side owner-scoped checks are a required part of authorization; Google login alone never grants database access.

The owner approves exact Google account emails in the existing hidden owner panel, shares the BTA URL manually and may disable or renew access. No invitation emails or Gmail accounts are required. The owner and invited members still need Google accounts.

## Single install + code contents

`streamlit_app.py` • `bta/` • `sql/INSTALL_ALL.sql` • `scripts/` • `.github/workflows/` • `.streamlit/secrets.example.toml` • `assets/` • `tests/` • `docs/`

One SQL install runs all three numbered migrations and includes a server-only atomic versioning RPC for Google OIDC.

## Status and acceptance

This source bundle is a consolidated runnable design with unit/integration fixture tests. It is **not** a claim that a deployed environment already passed actual Google sign-in, cross-member attack tests, external sports feeds, real bookmaker offers, live iPhone Safari QA, GitHub scheduled worker observation, or encrypted Postgres restore. The owner must configure their external accounts before those gates can be exercised. The code never pretends a failing external feature is verified.

Historical acceptance criteria and original full master plan are included in `docs/`. Prior checkpoint writeups are archived under `docs/history/` and superseded by **START_HERE.md** for setup.

No betting is placed or payment processed by this app.
