# BTA 2.0 research-coverage checkpoint (2026-11-07)

**Purpose:** Improve NBA/NFL/CFB research evidence coverage in the existing certification-engine package. This is *not* the later requested entire-app production rebuild. All changes are integrated into a complete *interim* source tree so they can be carried into the future final rebuild without patch-by-patch GitHub work.

## New code paths

| Module | Evidence and constraints |
|---|---|
| `bta/sources/nfl_official.py` | Best-effort exact team/week/player parser for a league-published injury page. Blocks ambiguous markup, wrong week, missing player and blank status. A league designation of Questionable/Out **does not** establish an active-list state; publication timestamp may remain unknown. Must be host-tested and permitted by provider site policy. |
| `bta/sources/nfl_injuries.py` | nflverse official-report transcription; strictly matches season/week/team/name and `date_modified` cutoff. Distinguishes reported, not listed, outdated, contradictory. This is a secondary source, never primary verification. |
| `bta/sources/nfl_weekly.py` | nflverse current-season per-week player statistics with exact name, team, GSIS ID, and pregame week cutoff. This provides real third-party targets/attempts/yardage context where ESPN athlete gamelogs are absent. It never substitutes for official injury/playing-time status or frozen historical feeds. |
| `bta/research/football.py` | NFL weekly-stat to historical event linking requires same season/week/opponent, plus college-specific five adversities and missing-evidence reasons. NFL favorite/underdog cannot be guessed from game winners. |
| `bta/sources/cfbd.py` | Optional `CFBD_API_KEY`: unique game fixture + FBS verification, game-stats team profiles from prior completed games, turnover and yards-per-play metrics where explicit, plus descriptive opponent records excluding the result being evaluated. No use of paid adjusted metrics; no future-game leakage. |
| `bta/research/stress.py` | Optionally resolves the two NFL favorite/underdog analogues ONLY when an independently re-observed bookmaker moneyline pair establishes the **current** favorite. Observed historical margin is game-flow analogy, not claim of contemporaneous historic favoritism. All five scripts retain specific sample and source requirements. |
| `bta/research/market_specific.py` | Strict statistical evaluation for qualifying rushing/receiving TDs and any-single-regulation-quarter rushing yards. Requires *explicit* event and rule scopes, all necessary stat fields, and completed final observations. Never declares book or contract settlement/void resolution. |
| `bta/research/freshness.py` | Provider publication timestamp vs retrieval timestamp, `CURRENT`/`DELAYED`/`TIMESTAMP_UNVERIFIED`/`UNAVAILABLE`, frozen numeric probability absent a validated model. A fetched score is not proof of fresh play-level data. |

## Remaining launch blockers / external proof

1. **Authoritative NFL status:** The NFL website is human-oriented, not a guaranteed documented API. Its exact HTML can change; a credible secondary report is not a confirmed active/inactive list. Actual source fetch and mapping from the deployed host must be proven; failing HTML is a pending item, not healthy/active.
2. **CFB starter and injury sources:** No universal truly free official starting-QB, depth-chart or injury feed with stable machine-readable endpoints has been proven. Team profiles and even opponent-strength proxies alone are insufficient for strict moneyline certification. FCS blocked by default.
3. **NFL 5-script certification:** Book-specific *current* two-sided moneyline quotes can establish favorite direction, but are rate-limited on optional odds service; dated historical team/player events and role distributions must also join. Without all five evidenced scenarios, strict grades remain pending. Team winning a game cannot determine whether it was favored before kickoff.
4. **Advanced markets:** Historical NFL TD/quarter feeds still lack validated every-play coverage and platform/jurisdiction-specific settlement rules. Statistical result is intentionally distinct from sportsbook settlement. Quarter-level markets do not borrow full-game numbers.
5. **BTA Live:** Free feeds may not publish upstream timestamps or granular player events. Without a reliable timestamp report `TIMESTAMP_UNVERIFIED` and keep percentage absent. No validated market-specific or joint model exists.
6. **No-lookahead replay:** Retrospective research needs **captured pregame source snapshots**. A season-total fetched now is not a frozen past prediction input. New code refuses to retro-certify in-progress/completed games.
7. **Server validation:** Neither this environment nor the ZIP has been shown operating with owner CFBD/odds keys, NFL.com pages, deployed Streamlit, actual magic-link email, backup restores, or real active-game sources. Real hosted acceptance is pending.

## What the owner must set up (no code editing)

- **CFBD_API_KEY:** Create a genuinely free key at <https://collegefootballdata.com/> (free tier currently advertises 1,000 requests per month), then put it in Streamlit app Secrets and GitHub Actions Secrets alongside existing keys. Do not paste it into chat or the public repository.
- **SPORTSGAMEODDS_API_KEY (optional):** A compliant real bookmaker quote feed is needed for verifying exact offered prices and game-favorite identity. The free-tier limits / signup terms must be checked before using it; manual exact selections remain marked *market not verified* without it.
- **No additional required AI key for these modules:** Research/statistical validation remains deterministic. Existing Groq/Gemini/Cloudflare connections can improve contextual investigation but cannot turn unverified facts into certified data.
- **Real deployment/live observation:** After services are connected, the owner need only grant access or share aggregated diagnostic status; the software tests, source probes, quota measurement, and restoration exercises must be performed by the developer/automated deployment infrastructure. Nothing should be called production-ready on the basis of local unit tests alone.

## Verified implementation checks

The pytest suite includes: exact injury report identity and chronology, same-time conflicts, official-page parser fail-closed behavior, free CFB FBS fixture/date reconciliation, pregame-only team data, NFL market favorite evidence, independently linked historical game scripts, TD/quarter contract semantics, unknown live timestamp prevention, and existing private-store / gate checks. Tests use controlled fixture data, **not** claims of real remote source availability. See `docs/TEST_STATUS.md` for the original suite.

## Source documentation to review for provider terms / availability

- NFL injury page: <https://www.nfl.com/injuries/>
- nflverse release schedule: <https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html>
- nflverse injury dictionary: <https://nflreadr.nflverse.com/articles/dictionary_injuries.html>
- nflverse weekly-stat adapter: <https://github.com/nflverse/nflreadr/blob/main/R/load_stats.R>
- CFBD: <https://api.collegefootballdata.com/> and <https://collegefootballdata.com/api-tiers>
- SportsGameOdds: <https://sportsgameodds.com/docs/endpoints/getEvents>

This checkpoint adds real research *capabilities* and documented verification gates; it does not imply universal high-grade certification or uninterrupted live coverage on a no-cost infrastructure stack.
