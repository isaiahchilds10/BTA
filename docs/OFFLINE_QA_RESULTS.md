# BTA 2.0 — Offline quality checks (Google OIDC edition)

- Source: Final consolidated Gmail-free package, built 2026-11-08.
- Python syntax compilation: **PASS** for `streamlit_app.py`, `bta/` and `scripts/`.
- Automated `pytest -q` in current environment: **113 passed**.
- Google OIDC security tests: verified email/sub identity requirements, nonmember denial, expired/disabled approval rejection, first-login Google subject binding, cross-member ticket access rejection, and member scope on ticket operations.
- Historical source-gated research/odds/AI/settlement/forecast tests inherited from previous checkpoints passed.
- `.streamlit/secrets.example.toml` parses successfully as TOML, `[auth]` contains the five documented Google OIDC keys.
- BTA original belt-logo SHA-256 identical to the approved handoff archive.
- `sql/INSTALL_ALL.sql` contains each numbered SQL migration once, including the Google member authorization rules and direct-client grant revocations.
- No actual Supabase, AI, odds or Google OAuth secrets stored in the bundle.

**Not performed:** Real Streamlit visual test (package installation unavailable due network restrictions), real Google OAuth redirect with owner account, real Supabase schema application/authorization test, genuine external provider response tests, active GitHub Actions schedule observation, physical iPhone/Android UX acceptance, encrypted database restoration. None of these tests is claimed to pass.

No numerical hitting probabilities are claimed as calibrated; missing decisive evidence still blocks certification.
