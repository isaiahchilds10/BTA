# BTA 2.0 — Capability status and acceptance gates

Status definitions: **CODED/OFFLINE TESTED** means static imports and repeatable Python tests were run; **NOT HOST-TESTED** means external service credentials or a live Streamlit browser are required; **UNAVAILABLE** means the required data/validated model is not integrated.

| Feature | Code status | Honest limitation |
| --- | --- | --- |
| Original brand logo + dark UI | Coded | No iPhone/Android browser visual acceptance test |
| 5 pages / matchup-to-props browser | Coded; market/position logic offline tested | Actual Streamlit deployment and iPhone/Android usability have not been observed |
| NBA / NFL / FBS schedules | Coded | ESPN public endpoint only; host/network/provider access not proved |
| Up to 30 legs, exact markets, paste, browse | Coded/testable | User-entered exact lines; optional SportsGameOdds quote adapter has not been host-tested |
| Single Submit Ticket + per-leg analysis | Coded | Private mode queues immediately; actual completion depends on configured worker and free data/model quotas |
| Whole-ticket correlation / what-if audit | Coded/offline tested | No validated combined probability |
| Auto BTA grades | **Certification path repaired and offline integration tested**; actual provider-derived gates, independent recomputation, source-linked NBA scenario samples | A real BTA+/TAIG label requires all source-backed gates; official NFL/CFB injury/matchup and market gaps remain; no forced grades |
| Correct NFL / CFB / NBA scripts | NBA historical game-flow matching implemented for source-backed cases; NFL/CFB distinct scripts preserved | NFL favorite/underdog cannot be inferred from final-score margin; official QB/CFB pressure scenarios remain unassessed where inputs absent |
| Three AI providers, independent critic, failover | Coded/offline fault tests | Real free quotas/provider output need live keys and tests; not optimized through historical benchmark |
| Floating Ask BTA | Coded | Real UI/mobile display and real AI keys not tested |
| Supabase invite-only magic-link login | Schema + app code | Requires owner project, custom SMTP, template, real invitee acceptance; hard refresh can require sign-in again |
| RLS private slips, versions, sharing | SQL + app code | No real A/B penetration/authorization audit performed |
| Durable worker 15-minute polling | Code + Actions | GitHub schedules may be delayed; actual hosted run not observed |
| BTA Live observed box progress | Coded | Third-party live data can be stale; not guaranteed real-time or official settlement |
| Full postgame settlement, calibrated hit percentages | UNAVAILABLE | Needs exact official stats, void rules and out-of-time validation; never shown as validated |
| Encrypted backup | Coded offline encryption + row-level integrity test | Not a proven isolated Supabase PostgreSQL recovery; private GitHub repo and secret required |
| Private beta / real cross-device UX | NOT HOST-TESTED | Owner and invited testers must eventually verify external functionality |

**Production release blocked** until email delivery, private authorization, real sports feeds, real research evidence/market-specific coverage, durable jobs, full encrypted restore, iPhone/Android usability and private beta have genuinely passed. A ZIP alone cannot certify these external dependencies.

No betting action is automated. Probability fields stay absent when unvalidated. `PENDING VERIFICATION` is not a BTA grade.


## Research coverage checkpoint — 2026-11-07
**Additional code (offline-tested, not host-tested):** Secondary NFL injury + nflverse weekly stats, best-effort official NFL HTML observation (not guaranteed access or official active-status feed), CollegeFootballData FBS pre-cutoff matchup evidence with optional free key, market-favorite conditional NFL script analogues, explicit NFL touchdown and quarter-level statistical settlement **without** bookmaker resolution, and provider-update age in BTA Live. These are evidence inputs and audit components, not universal NFL/CFB certification or validated live hit probabilities. See `docs/RESEARCH_COVERAGE_CHECKPOINT.md`.

## November 8, 2026: new no-card odds + AI orchestration + forecast freeze

- **Implemented/offline-tested:** PropLine and ParlayAPI exact offer feed/fallback; verified comparison against server-refetched vendor observation; task-adaptive specialist with independent critic objective and bounded free-vendor failover; immutable pregame evidence hashes; stronger numeric-probability gate; improved iPhone-safe-area bottom navigation.
- **Requires configured credentials/deployed verification:** API availability and terms, real member authentication and email, hosted mobile rendering, actual external AI quota handling, successful PostgreSQL encrypted restore.
- **Not established:** certified all-market hitting percentages, universal official injuries/advanced markets, bookmaker resolution parity, validated correlated parlay probability.
