# BTA Source & AI Provider Register — November 7, 2026

## Actual code adapters

**Sports:** ESPN public web scoreboards, team rosters, team schedules, game logs, summaries and live box scores, with source URLs and retrieval timestamps. These endpoints are **third-party and unofficial for injuries and sportsbook offers**; usage permission, completeness and host performance must be checked. No ESPN data is silently relabeled official.

**Sportsbook quote option:** SportsGameOdds v2, free Amateur tier (https://sportsgameodds.com/pricing), supplies limited player prop/line odds and matching market metadata. BTA uses its REST API only when an owner supplies `SPORTSGAMEODDS_API_KEY`, caches for 10 minutes, checks source timestamps and refuses ambiguous event/player joins. A sportsbook offer may have changed, and settlement still requires separate verification; quota/licensing must be reviewed for your deployment. Without an enabled feed, BTA accepts exact user-entered lines.

**Official status:** No reliable universal free official injuries/depth chart adapter for all three sports has been verified; the relevant BTA grade gate remains PENDING when official status is decisive. Credibly reported injuries cannot be promoted to official. User-entered FanDuel/Polymarket alternate offers are marked MARKET_NOT_VERIFIED.

## 3 configurable free inference candidates (adapter code implemented)

| Provider | API key in server environment | Default model | Verified external live test? |
| --- | --- | --- | --- |
| Groq | `GROQ_API_KEY` | `qwen/qwen3.8-27b` | No; requires owner account/key |
| Gemini | `GEMINI_API_KEY` | `gemini-3.8-flash` | No; requires owner account/key |
| Cloudflare Workers AI | `CF_ACCOUNT_ID`, `CF_AI_TOKEN` | `@cf/openai/gpt-oss-20b` | No; requires owner account/token |

Each request uses public sports context only. Specialist and critic use distinct providers when practical, with a separate adversarial question, and failures trigger failover. Actual ranking is currently a **configurable default**, not an empirical task-specific benchmark; task-accuracy ranking must be measured before claiming optimal adaptive provider selection. Free quotas may change, and Gemini free-tier terms may allow data use for service improvement.

**No all-free full-market sports-data assurance:** comprehensive official injuries, FanDuel alternate lines, real-time quarter-by-quarter NFL usage and FBS team-level depth charts cannot be universally verified from current integrated sources. Features must visibly show limits rather than pretend complete AI research.

Sources / provider docs:
- https://sportsgameodds.com/docs/endpoints/getEvents
- https://sportsgameodds.com/docs/data-types/stats
- https://console.groq.com/docs/quickstart
- https://console.groq.com/docs/rate-limits
- https://ai.google.dev/gemini-api/docs/pricing
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/workers-ai/models/gpt-oss-20b/
- https://docs.streamlit.io/deploy/streamlit-community-cloud

## Research-coverage addition (2026-11-07)

Additional adapters: league-published NFL injury-page reader with fail-closed parsing; nflverse weekly injury/volume datasets; optional free-tier CollegeFootballData pregame FBS matchup context. `CFBD_API_KEY` may be configured in both Streamlit Secrets and the GitHub scheduled worker Secrets. See `docs/RESEARCH_COVERAGE_CHECKPOINT.md` for exact evidence policy and limitations. These adapters have **offline parser tests**, not a demonstrated live host response.

## No-card market adapter update (November 8, 2026)

The primary market browser now offers on-demand **PropLine** (`PROPLINE_API_KEY`) and fallback **ParlayAPI** (`PARLAY_API_KEY`) adapters. Unlike the legacy SportsGameOdds connector, neither requires a card on its advertised free signup. The market normalizer is deliberately narrow: canonical event home/away/time, exact known full-game market/player, acceptable bookmaker, explicit source timestamp and quoted price. Data beyond the free tier or missing settlement rules remain unavailable. See [`NEXT_SYSTEMS_ENGINEERING.md`](NEXT_SYSTEMS_ENGINEERING.md) for behavior, QA and unresolved live tests.

- PropLine docs: https://prop-line.com/docs
- ParlayAPI response shapes: https://parlay-api.com/docs/response-shapes
- ParlayAPI credit accounting: https://parlay-api.com/limits
- Three AI models: The configured default names are candidates, not a promise of free-account entitlement; check available account models on deployment.
