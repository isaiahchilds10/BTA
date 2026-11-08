# BTA 2.0 — Three research gaps: best-effort implementation checkpoint

**Scope:** Research, source fallback, advanced-statistic semantics, and probability validation. This is not the requested later full app rebuild or certification of live services. No existing GitHub repository or deployed Streamlit app was changed.

## 1. Participation: official-first, evidence-preserving source ladder

### NFL

1. **Primary:** league-published NFL injury page (`bta/sources/nfl_official.py`). Exact league week, player, and team table are required. Team nickname headings are now recognized without fuzzy substring associations. Official `OUT`, `DOUBTFUL`, or `QUESTIONABLE` are game designations, **not active/inactive confirmation**.
2. **Fallback A:** NFL-published weekly injury article (`bta/sources/nfl_editorial.py`). Dated article, weekly season, exact team section, and exact named player must match. This is **editorial reporting**, not a final inactive list; the URL pattern or HTML can change, and unavailable data remains unavailable.
3. **Fallback B:** nflverse injury-report transcription (`bta/sources/nfl_injuries.py`) with date, season, week, team and name checks; third-party copy is not official status.
4. **Authority arbiter:** `bta/research/participation.py` uses publisher allowlists, game-identity checks, publication cutoff, freshness, and conflicting-source detection. A more authoritative newer report takes precedence; disagreements at equal authority and time are disclosed. An unlisted player is not automatically healthy or unrestricted.

### College football

Conference-owned availability reporting is now identifiable for **SEC, ACC and Big Ten**, with applicability restricted to verified intra-conference matches (not every FBS game). Sources/policies are linked in the research report and `bta/sources/cfb_availability.py`. A conservative fixture-specific HTML table parser requires the exact matchup, *date*, player, and published status; arbitrary report-hub pages cannot certify a player. HTML/PDF formats and current link discovery still require real deployed integration. Some leagues do not publish standardized universal participation reports, so official team updates and independently corroborated reporting remain useful but less authoritative.

### What this closes—and does not close

This establishes a clearer source hierarchy and code paths for actual dated findings. **The application's current automatic NFL/CFB eligibility gates are not universally clearable**: a machine-readable original issue time, matched fixture, verified named player and workload security are still required. NFL.com, conference reporting hubs, and other upstream sources need live tests from the eventual deployment host. This development environment could not make outbound network requests.

## 2. Advanced markets, game script, and settlement

- `bta/research/settlement.py` distinguishes **statistical result** from operator settlement and requires a verified completed game, correction reconciliation, exact contract terms, and player void/participation rules before computing a result.
- The underlying `bta/research/market_specific.py` requires both *rushing* and *receiving* TD counts for `RUSH_OR_RECEIVE` touchdown YES/NO, explicitly excluding quarterback passing touchdowns. For an **any single regulation quarter** rushing selection it requires all four quarter totals; full-game yardage does not substitute.
- FanDuel's Ohio published house rules are a real, jurisdiction-specific authority for many NFL categories, but a generic quarter-player-prop rule **does not establish that a special ANY-quarter threshold contract is offered**. A Polymarket contract is separately governed by its current resolution text. No auto-conversion between these market families is allowed.
- `bta/research/cfb_plays.py` adds optional budgeted CollegeFootballData `/plays` research for observed first-half 10+ deficits and one-possession fourth-quarter games, joined to previously completed game IDs and clipped to the forecast time. It strengthens **context** and reverse-analysis; it does not claim these are the historical pregame favorites or assign numerical future odds. The CFB five-script report has gained separate play-level context without silently changing incomplete scripts into certified grades.
- **Resource choice:** `CFBD_PLAY_WEEKS` defaults to `0` (no extra play-by-play calls) to avoid exhausting the free quota during repeated scheduled research. Owner may set `CFBD_PLAY_WEEKS = "1"` or `"2"` in Streamlit/GitHub secrets after obtaining a free `CFBD_API_KEY`, checking entitlement, and observing quota usage. Historical team profiles continue with the standard configured CFBD source regardless.

## 3. Live verification and prediction validation

- `bta/sources/nba_scoreboard.py` provides a direct NBA-controlled scoreboard lookup by **exact two-team identity**, preserving provider updated-at independently of the time BTA fetched it. Live UI can show the league scoreboard alongside existing third-party box-score observations when accessible.
- `bta/research/live.py` now distinguishes **scoreboard freshness** from **player-stat freshness**. Unless the provider actually exposes an independently verifiable per-player update time, that field remains timestamp-unverified; a fresh score cannot unlock a stale prop probability.
- `bta/models/validation.py` implements a strictly chronological market/model-specific holdout evaluator with event/market deduplication, required pregame input and prediction timestamps, distinct training/test sets, a constant-base-rate benchmark, Brier and log losses, 10-bin calibration error, fixed minimum observations, and an independent approval gate. **It does not generate a forecast or approve any numerical percentages by default.** Genuine externally timestamped pregame prediction snapshots and observed results are required before validation can be completed; retrospective fabricated timestamps are not acceptable proof.
- Unvalidated pregame/live percentages and entire-ticket probability remain unavailable as required. Historical 3/3 or 10/10 hit fractions are descriptions, not validated future forecasts.

## Offline QA and actual external verification

**91 automated offline tests passed**, plus Python syntax compilation. Checks include: authority and publisher spoofing, future-data exclusion, contradicting statuses, dated fixture-specific conference tables, NFL editorial isolation, game script research, exact touchdown and quarter statistical semantics, NBA official scoreboard source age, and model chronological-data rejection. The tests use controlled data. They do not establish successful hosted access to external feeds, paid/free entitlements, provider licensing, authentication security, or an actually calibrated predictive model.

## What owner needs to do

1. No additional account is necessary to preserve this code checkpoint. **For real CFB data, request a free API key** from <https://collegefootballdata.com/> and later configure `CFBD_API_KEY` in Streamlit and GitHub Actions secrets; never publish or paste it in chat.
2. For exact currently offered FanDuel lines, a lawful licensed data provider or valid real manual offer evidence is needed. SportsGameOdds remains optional and must be tested for market/alternative coverage and the limits/conditions of its free plan.
3. For provider-dependent AI, Supabase private member login, email delivery, and recovery, reuse the previously documented account requirements. These are not prerequisites for working on the deterministic research functions here, but they are prerequisites for a multiuser public URL with private access.
4. When the new Streamlit deployment exists, run automated service probes and real beta acceptance checks **from the deployed host**, including injury/report parsing, fresh box score updates, backup restore and cross-account security; these cannot be verified from offline unit tests.

## Authoritative/public sources reviewed

- NFL official injury page: https://www.nfl.com/injuries/
- NFL published injury roundup example: https://www.nfl.com/news/nfl-week-9-injury-report-2026-season
- nflverse data update schedule: https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html
- SEC availability reporting policy/hub: https://www.secsports.com/reports , https://www.secsports.com/fbreports
- ACC availability reporting: https://admin.theacc.com/sports/2025/8/28/availability-reporting.aspx
- Big Ten 2026 policy: https://bigten.org/news/2026/8/28/big-ten-announces-changes-to-football-availability-reporting-process.aspx
- CFBD games/plays API: https://api.collegefootballdata.com/api/plays
- NBA official live scoreboard endpoint: https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json
- FanDuel Ohio rules (July 22, 2026): https://d38ayms4az88sz.cloudfront.net/SB/OH/2026-07-22T12-49-10.html

**Not certified as complete:** universal official college/NFL active status, full advanced-market source coverage, actual third-party sportsbook settlement, production live-provider freshness, or a calibrated market-specific forecasting model. These require authentic source coverage and deployed acceptance evidence, not simply connecting AI keys.
