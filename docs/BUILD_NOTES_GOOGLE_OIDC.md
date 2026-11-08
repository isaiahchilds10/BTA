# Build change log — Google sign-in instead of Gmail

## User-approved change

Original master specification required emailed passwordless magic links. The owner subsequently excluded Gmail and requested BTA be updated without it. This release implements **Google OIDC sign-in** with manual owner email approval and disables the old email OTP/magic-link workflow. It uses Google solely as the identity provider; there is no Gmail sending requirement. This is an explicit product change from the earlier 20-page specification.

## Code changes

- `streamlit_app.py`: Google `st.login()`/`st.logout()`, no `sign_in_with_otp`, approved-member gate before any private app page.
- `bta/security/google_identity.py`: only accept verified Google identities with stable subject.
- `bta/security/google_membership.py`: check approved, enabled, unexpired membership; atomically bind Google subject and audit first login.
- `bta/storage/google_oidc.py`: subject-independent, explicit server-side per-owner ticket/report/job/share scopes; cannot write certified reports from browser.
- `sql/003_google_oidc_membership.sql`: add unique Google subject binding, service-only atomic ticket version RPC, revoke all direct user table access and old RPCs. `sql/INSTALL_ALL.sql` combines all migrations.
- `.streamlit/secrets.example.toml`: new `[auth]` OIDC section; no SMTP/OTP settings.
- `.github/workflows`: use new Supabase secret key; lower-frequency worker polling for free-account budget.
- `bta/ai/providers.py`: fixed task-selection from nested verification gate dictionaries.
- `tests/test_google_oidc_private.py`: claims, nonmember, expiry, identity binding, cross-account access, task specialist regression checks.

## Architectural limitation

The backend uses a privileged Supabase secret **only on its trusted Python server**, not in a mobile client's direct database connection. This means per-member isolation must be enforced by the app service itself; PostgreSQL RLS cannot police a service-role request. The new migration denies direct client database access entirely to avoid conflicting authorization paths. This trust architecture needs external security review for real multiuser production use.
