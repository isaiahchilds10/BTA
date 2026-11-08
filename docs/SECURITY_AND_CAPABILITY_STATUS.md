# BTA 2.0 — Gmail-free edition security and capability truth table

| System | Status after offline build | External proof still required |
|---|---|---|
| Google OIDC sign-in | Implemented via `st.login()` and mandatory OIDC claims | Real Google Cloud client/Streamlit callback/session reload on iPhone |
| Invite-only membership | Exact approved email + bound Google subject; disabled/expired rejected | Real owner/admin approvals and revoked-access test |
| Private database | Service-role backend with explicit member owner scopes; direct authenticated grants revoked; RLS enabled | Independent A/B cross-member abuse testing, deployment secrets isolation |
| Supabase user creation | Admin pre-provisioning without email or SMTP | Confirm latest Supabase API key/admin behavior with deployed account |
| Five-screen UI | Implemented, role-filtered markets, 30-leg slip, original logo | Actual iPhone Safari, Android Chrome, screenreader checks |
| Three-AI orchestration | Task roles, bounded failover, independent critic implemented | Authenticated Groq/Gemini/Cloudflare free-tier test + quota/terms |
| NBA/NFL/CFB game/stat adapters | Source-aware parser and fixture tests | Live network access from Streamlit Cloud, current provider compatibility |
| PropLine + ParlayAPI | Authenticated adapter code and offer recheck tests | Exact quote coverage, jurisdiction, legality and redistribution rights |
| BTA grading | Source-gated deterministic audits, sport-specific scenarios, second pass | Full reliable inputs per market; true coverage varies by sport |
| Live observed progress | Timestamp and stale-state framework | Real-game observed data quality/latency |
| Probability validation | Chronological snapshot, replay and calibration gates | Genuine out-of-time forecasts; no unsupported percentages |
| Settlement | Partial rules/statistical resolution engine | Full official market-specific void/push/corrections and operator rules |
| Background jobs | Supabase durable queue + GitHub schedule; retries | Scheduled worker completion on external accounts and free-tier budget |
| Backup | Encrypted exported rows in a private Action artifact | Full DB/auth backup and successful isolated restore |

**Launch sign-off cannot be asserted from ZIP tests alone.** Source claims are never invented. An unverified or incomplete selection remains PENDING VERIFICATION and is not silently included in a strict BTA ticket.

**Auth distinction:** Streamlit Google OIDC establishes identity. Supabase project secret is held on the trusted Streamlit server/worker; secret-key requests bypass RLS, so `GoogleCloudStore` must apply its owner filtering and ownership checks on *every method*. Direct Supabase table access from anonymous/authenticated actors is denied by migration 003. The installed service key must never appear in client code, browser URLs, logs, or the public repo.
