# Certification engine repair — 2026-11-07

This is an **engineering repair**, not a declaration that all sports/markets have working live certification.

## Root cause eliminated
The old `analyze()` passed `gates={}` to `admissible_grade()` and the script evaluator always produced five `NOT_ASSESSED` rows. The program therefore had no reachable high-grade path regardless of the actual evidence or AI keys.

The code now derives the seven mandatory gates **from server-side evidence** and performs an independent deterministic recomputation. The offline integration test `test_end_to_end_verified_provider_path_can_now_reach_bta_plus` proves that complete adapter results can produce BTA+, while falsified client booleans, missing observations, wrong IDs, and incomplete scripts still prevent certification. **Mocked source results are not proof that live providers are usable.**

## New automatic research

- Fetches exact selected event and identifies the player only when one fixture roster matches the name and optional ESPN athlete ID.
- Parses current-season player game logs for individual and common NBA/NFL combined markets, preserves the exact threshold, distinguishes descriptive hit rates from calibrated future probabilities, and extracts available minutes/attempts/targets.
- Joins actual historical athlete performances to team results using the **same event ID** and classifies NBA game-script performance as BETTER / SAME / MIXED / WORSE only when at least three matching games exist for each scenario. NFL historical favorite identity **is not guessed from who won**; CFB retains its distinct five stress tests.
- Checks the current NBA official injury PDF for the exact game/date and player, without confusing an unofficial prediction or a missing report with confirmed full availability. NBA official `Available` is a report status, not a minutes guarantee.
- Uses real recent opposing NBA boxscores to investigate an opposing team's record **against comparable position groups** for NBA player markets when enough comparable source data exists.
- Re-fetches an exact, fresh FanDuel/DraftKings price from the optional SportsGameOdds adapter when configured. An old or user-entered `market_verified=true` cannot bypass this check.
- Verifies relevant standard **FanDuel NBA full-game player-prop rules for explicitly selected Ohio jurisdiction only**, through the operator's own published rules page. No other state/platform receives those terms automatically.
- Includes a separate preliminary research screen so relevant observations are useful even when the strict grade remains PENDING.
- Prevents replay of a *past* game from using new injury/market evidence to claim a pregame certification.
- Exposes gate-by-gate status, league injury observation, opponent evidence, second-pass result, and first/second-pass limitations on existing expandable report pages.

## Certification requirements that still need real deployment/sources

- The NBA injury PDF parser, position-boxscore parser, market-quote adapter, and operator-terms fetch **must be checked against actual source responses from the deployed Streamlit host**, including during live competition. External HTTP calls were not possible from this offline coding environment.
- NFL official injuries, actual pregame favorite lines for historic NFL scripts, FBS quarterback/trenches/injury intelligence, and many prop markets still have material evidence gaps; they must NOT be automatically promoted.
- Some NBA players do not appear on the injury PDF; the code distinguishes a game-present, submitted **not listed** state from an `Available` designation. Never interpret either as guaranteed playing time.
- A line may be user-entered and analyzed but not market-certified. A quoted live offer may expire. Settlement/void and jurisdiction rules can vary.
- Position-boxscore samples are descriptive and not a full opponent-strength-adjusted predictive model. Full expected-value and numeric hit probability models are not validated.
- Automated AI explanation is deliberately **not** a credential for grades. No amount of LLM confidence can bypass missing decisive inputs.

## Test status

The updated offline tests exercise source trust, exact market checks, role and historical script evidence, fail-closed behavior, and a successful source-adapter simulation for BTA+. Real hosted API, multiuser security, actual mail and beta acceptance remain separate launch requirements.
