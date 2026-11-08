# Validation status — consolidated build

- Python compilation of all BTA, scripts, and main app files: passed.
- Offline pytest suite: 52 passing tests (including 12 additional certification path checks).
- Added tests: NBA/NFL/CFB market taxonomy, QB/WR/TE/RB position filters, exact ESPN/SportsGameOdds game identity join, quote suppression on stale or unavailable market and ambiguous events.
- Verified input and output field shapes against published service API documentation, **not** a live authenticated API response.
- Live Streamlit browser/e-mail delivery/Supabase RLS/three-model quota failover: not executed without user-provided private credentials or hosted accounts.
- Isolated production-grade encrypted PostgreSQL restoration: not executed; SQLite snapshot round-trip does not prove a real Supabase restoration.
- Full TAIG/BTA grade certification from real current official injuries, complete matchup evidence and bookmaker settlement: not established for all markets; pending gate remains required.

A test passing is a statement about the specific checked code path, not production authorization to wager or a claim that externally sourced sports facts are verified.

## Certification path repaired

The grader is no longer permanently given empty gates. `tests/test_certification_pipeline.py` exercises the first fully reachable BTA+ path using controlled offline adapter fixtures, plus contradictory sources, stale/forged offers, source-joined NBA stress scripts, role evidence, and state-specific settlement rules. **This tests code, not external source uptime or future forecast accuracy.** See `docs/CERTIFICATION_ENGINE_FIX.md`.


## Research coverage checkpoint — 2026-11-07
New NFL official-site parser, nflverse secondary injury and weekly player history, NFL week/opponent mapping, CFBD FBS statistical audit, strict touchdown/quarter contracts, favorite/underdog conditional analogues, freshness states, and an offline end-to-end NFL history fallback test added. **77 passed (`pytest -q`)** plus Python compile verification. No real provider-account or hosted browser acceptance test was run.

## Five-system enhancement checkpoint — November 8, 2026

- Updated suite **106 passing automated offline tests** (compiled `bta`, `scripts` and `streamlit_app.py`). New tests include provider quote normalization, strict fixture time/side, stale/ambiguous/suspended market refusal, 429 fallback, bookmaker reprice, no-key behavior, independent AI context citation filtering, specialist task routing, cryptographic pregame freezes and model probability display gates.
- Mobile navigation CSS is viewport-/safe-area-aware; there has not been a rendered iPhone Safari test because Streamlit and the deployed hosting environment are not installed/available locally.
- New optional no-card odds connectors use documented published JSON shapes, **not real authenticated provider responses**. Publisher free plans and production display rights require owner-side setup and confirmation.
- AI provider uptime, quota failover with actual account tokens, Supabase RLS, live replay, encrypted DB restore, and model calibration have not been independently certified in a deployed environment.
- See `NEXT_SYSTEMS_ENGINEERING.md` for all behavior and caveats.
