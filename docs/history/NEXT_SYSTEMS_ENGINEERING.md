# BTA 2.0 — Five-System Engineering Checkpoint

**Scope:** incremental improvements to the existing latest research checkpoint; this is **not** the final all-in-one production release. No user's GitHub repository, keys, or deployed service was changed. All code lives in this project tree.

## 1. AI: researcher, logically independent critic, failover

`bta/ai/providers.py` retains the three independent Groq, Gemini and Cloudflare REST adapters, independent specialist / adversarial critique prompts, and the rule that **AI prose cannot establish source facts or override deterministic grades**. This checkpoint adds:

- A deterministic specialist-task selector (availability, role, opponent, exact market or scripts) chooses the most relevant missing-evidence review before calling a free AI provider.
- Role-specific provider preferences through `BTA_AI_ORDER_<UPPERCASE_ROLE>`, useful after held-out benchmarks. Default remains `BTA_AI_ORDER=groq,gemini,cloudflare`, and no default vendor is claimed empirically best.
- Bounded exponential cooldown per failing provider, `Retry-After` honoring (up to one hour), no unbounded same-provider retry loops, and sanitized aggregate health available in the owner panel.
- Failover on quota, HTTP, malformed/empty responses, secret-looking text in model output, and citations to URLs absent from the supplied evidence pack.
- A critic that does not see the researcher's narrative; it first attempts an alternative vendor, and can fall back to the same vendor using an independent objective. The report states whether the critic truly used a separate vendor.

**Limits:** Requires actual API credentials and approved free plans for end-to-end inference testing. Source lineage and model-source independence cannot be established by changing vendors alone. Quotas, provider availability, and privacy terms vary; automatic free failover is best effort.

## 2. Real bookmaker offers versus research thresholds

`bta/sources/free_odds.py` implements two API shapes documented by their publishers:

- **PropLine:** single bulk sport odds request with requested market filters, nested bookmaker/market/outcome, authenticated with `PROPLINE_API_KEY`. Verify *exact* home/away and game time; accepts only known full-game markets, supported book, recognized explicit player/roster identity and a source market timestamp no more than 15 minutes old. No reversed teams, guesswork or unknown period.
- **ParlayAPI:** separate nested game-line `/odds` and flat player `/props` endpoints, authenticated with `PARLAY_API_KEY`; explicit `FULL` period and board truncation checks. One exact fixture match is required. Fallback to ParlayAPI if PropLine lacks a fresh exact offer or fails.

The UI now allows users to click **Fetch real available lines** on the game and market of interest; it shows the upstream observation and its timestamp. Observed lines can be added as **unverified for certification**. Research performs a new server-side exact-market comparison before it can consider the source gate. Saved offers that are repriced or have changed source identity do not silently pass, and a market quote never establishes void/participation/settlement rules.

Without either API key, manual exact thresholds remain functional. No fake live odds, implied probabilities posed as true win probabilities, or artificial FanDuel offerings are manufactured.

**Limitations:** An API observation is *not* a bookmaker guarantee of acceptance, and some free upstream boards may be incomplete or delayed. Mapping is intentionally limited to known canonical markets; unrecognized alternate/period/milestone markets are excluded, not silently normalized. One API key is not a comprehensive current free prop-resolution archive. Provider display/redistribution licensing must be checked for invited-member use.

Published API documentation checked:
- <https://prop-line.com/docs>
- <https://parlay-api.com/docs/response-shapes>
- <https://parlay-api.com/docs>

## 3. Historical settlement and true calibration

`bta/models/frozen_evidence.py` creates tamper-evident SHA-256 hashes of **source-limited, real pregame research records** including exact market, source facts, cutoff, grade, and blockers. It never invents a hitting probability. A freeze cannot be generated for a game already underway, or without a valid report cutoff.

The private GitHub background worker adds an insert-only pregame record **before** the corresponding report is committed, using the new `public.pregame_freezes` table. Install the additional migration `sql/002_pregame_freezes.sql` after `001_schema.sql`. Clients may SELECT only their own snapshots through Supabase row-level security; ordinary members cannot insert/update/delete freeze records.

Existing retrospective `bta/models/validation.py` still audits out-of-time held-out forecasts, requiring actual pregame timestamps, outcomes, precise market identity, separate training/test chronology, baseline comparisons and calibration. The numerical display gate now ALSO requires verified externally frozen upstream evidence and an expressly validated model record; merely passing summary Brier/error thresholds cannot unlock a percent forecast.

**Not accomplished:** No genuine prospective market-specific forecasting model was trained, no immutable upstream-source timestamps were independently attested using a deployed server, no historical source archive with paid line data was obtained, and no model/pairwise joint-parlay probability is certified. The system can now **accumulate legitimate pregame research data**, but numerical forecasts must remain unavailable until real time-split validation and independent governance pass.

## 4. iPhone-first sportsbook-inspired UI

`bta/ui/style.py` refines the original charcoal/red/white theme and exact user-provided belt logo. Narrow viewports now use a full-width fixed five-tab bar without forced horizontal scrolling, responsive 2-column home KPIs, larger touch targets, reduced UI motion and iPhone Safe Area padding. The floating Ask BTA button remains above bottom navigation. Streamlit five-screen navigation is unchanged, with no added public pages.

**Limitations:** Responsive CSS was syntax-reviewed, but iOS Safari behavior and keyboard/popover overlap cannot be certified without a browser/device run of the actual deployed app. Streamlit version/component DOM differences should be rechecked after deployment.

## 5. Operational integration and evidence honesty

- Background GitHub workflow now accepts optional `PROPLINE_API_KEY` and `PARLAY_API_KEY` secrets for exact refreshed market checks; the existing CollegeFootballData key is forwarded to the worker too.
- `.env.example` and Streamlit Secrets example now list the new keys. `docs/INTEGRATION_CHECKLIST.md` includes the new SQL migration.
- No credential or personal member data was committed to source, shown in AI prompts, or added to test fixtures.
- QA now includes adversarial tests for changed quotes, provider failover, mismatched game time/teams, unknown quarter, stale timestamps, incomplete boards, source-derived quote verification, pregame freeze hashing, and probability gate failure.

## What needs actual owner-provisioned deployment

1. Sign up for free PropLine/ParlayAPI keys (no-card plans advertised, account signup still needs confirmation) and ensure terms permit *limited end-user display*. Set keys in **private Streamlit Secrets and GitHub Actions Secrets**, not the repository.
2. Supply your approved free AI provider credentials privately in those secret stores. Model identifiers must be checked against real account-accessible catalogs before claiming failover is tested.
3. Install database migrations 001 and 002 in the **new** Supabase project; validate email sign-in, RLS member isolation and durable background jobs.
4. Observe a real NBA, NFL and college-football matchup from the deployed hosting environment; verify source timestamp, exact market lookup, no-data fallback and bookmaker source availability.
5. Persist actual pregame snapshots and final verifiable outcomes over time, then run held-out chronological model audits before authorizing any numerical probability display.

## QA evidence

Run `python -m compileall -q bta scripts streamlit_app.py` and `pytest -q`. All newly added API-response tests use publisher-documented response shapes with **synthetic test-only values**; they are not live authenticated integration tests.
