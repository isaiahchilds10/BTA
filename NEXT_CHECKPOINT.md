# BTA 2.0 — Five-System Upgrade

This is an **integrated research-engine development checkpoint**, not the final post-setup production release. It builds directly on the previously supplied three-gap 100-file package and includes all earlier application code, exact BTA belt logo, research modules, SQL, five-screen Streamlit app, workflows, and test suite.

## What is new

1. **Adaptive AI:** task-specific injury/role/matchup/market/script specialist, different-goal adversarial critic, three-provider failover, bounded cooldown, read-only non-sensitive health reporting and fabricated-citation safeguards.
2. **No-card odds feeds:** optional PropLine and ParlayAPI; actual bookmaker price/line data; exact game/time/player/market/period joins; refuse stale, truncated or ambiguous data; server rechecks saved quotes and notices changed prices.
3. **Pregame evidence freezes:** source-limited SHA-256 snapshots stored by the background worker; `sql/002_pregame_freezes.sql` migration; no fake probability, no retroactive pregame freeze after kickoff.
4. **Numerical prediction governance:** harder validation gate, explicitly blocking percent forecasts until source provenance and independently validated models qualify.
5. **iPhone UI:** five-tab bar without forced scrolling on small screens, safe-area spacing, floating Ask BTA accessible above bar, responsive home cards, original branding unchanged.

Run the final instructions in [`docs/NEXT_SYSTEMS_ENGINEERING.md`](docs/NEXT_SYSTEMS_ENGINEERING.md) before any external deployment. All external accounts are still optional for executing the offline code but required for their respective live functionality. Authenticated sports-data and AI calls, real mobile rendering, PostgreSQL restoration, external mailbox delivery, and statistical model calibration are **not** passed just because local unit tests pass.
