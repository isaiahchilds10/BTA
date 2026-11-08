# START HERE — ONE-TIME BTA 2.0 DEPLOYMENT (NO GMAIL)

This is the **current** deployment guide. Prior checkpoint setup files in `docs/history/` refer to an obsolete email-login build and must not be followed.

## Your choices, already implemented

- Private 1–5 member beta; no payment-required services and no Gmail SMTP.
- Five pages with the existing belt logo; 30-leg mixed league slip; Submit Ticket; Ask BTA.
- AI adapters: Groq, Gemini, Cloudflare Workers AI; sport providers: CollegeFootballData, PropLine and ParlayAPI.
- **Google OpenID Connect** handles sign-in; owner-controlled approved Google emails determine actual BTA membership. No sign-in email is sent.

## 1. Create or reuse your GitHub repository

Use the **new** BTA repository, keeping your old BTA app untouched. Keep the repository private. Download/extract the final ZIP and upload its **contents** into the repository root, not the ZIP itself. The root must contain `streamlit_app.py`, `requirements.txt`, `bta/`, `.streamlit/`, `sql/` and `.github/`. GitHub's web uploader may hide dotfolders on some devices, so use a desktop browser if needed and check `.github` and `.streamlit` uploaded correctly. Do not add secrets to any source file.

## 2. Install Supabase database (one paste)

Open https://supabase.com/dashboard → **your BTA project** → SQL Editor → New query. Open `sql/INSTALL_ALL.sql` from the ZIP, copy its contents into the SQL editor, and **Run** once in the dedicated BTA project. This creates all private tables, versioning/audit/queue functions, Google identity binding and zero direct client read grants. If you've already run 001 and 002 in this same new project, run **only** `sql/003_google_oidc_membership.sql` instead.

In Authentication → Sign In / Providers, leave **Allow new users to sign up** OFF. BTA doesn't use Supabase's email provider, Magic Link templates, SMTP or Google social provider. **Do not put your Supabase secret in the public repo**. Retrieve `Project URL` and the `sb_secret_...` key from Supabase settings/Connect; these will go in private Secrets.

## 3. Create a Google OIDC application (the one new setup item)

Open **https://console.cloud.google.com/auth/overview** (Google Auth Platform). This is separate from your Gemini API key. Choose an existing Google Cloud project or create a free project. Configure:

1. **Branding** — app name `BTA 2.0`, support email you control; supply any Google-required fields.
2. **Audience** — External, **Testing**. Add your own Google email as a **test user**, and later add 1–5 invited friends' Google emails. Google's testing limit is not your BTA membership gate: the app's own Supabase allowlist still applies. Testing-mode consent can require re-authorization depending on Google's rules.
3. **Clients** — Create client → **Web application** → name `BTA Streamlit`.
4. **Authorized redirect URI** — `https://YOUR-SUBDOMAIN.streamlit.app/oauth2callback`. This must match your exact future Streamlit app URL. If the app URL isn't known yet, reserve it when you create the Streamlit app, then return here to set this URI.
5. Copy the **client ID** and **client secret** into a secure password manager, never chat or source. Google OIDC discovery URL is `https://accounts.google.com/.well-known/openid-configuration`.

Streamlit's documented Google OAuth guide: https://docs.streamlit.io/develop/tutorials/authentication/google

## 4. Deploy on Streamlit Cloud

Open https://share.streamlit.io → sign in with GitHub → **Create app** → Existing repo → `main` → `streamlit_app.py` → choose a subdomain. Configure **Advanced Settings / Secrets** using the *names* in `.streamlit/secrets.example.toml`:

| Secret name | Private value source |
| --- | --- |
| `BTA_MODE` | `private` |
| `BTA_OWNER_EMAIL` | The same **verified Google email** you'll use to sign in |
| `BTA_PUBLIC_URL` | `https://YOUR-SUBDOMAIN.streamlit.app/` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SECRET_KEY` | Supabase new `sb_secret_...` server key |
| `[auth].redirect_uri` | `https://YOUR-SUBDOMAIN.streamlit.app/oauth2callback` |
| `[auth].cookie_secret` | Random 48+ character string generated privately (password manager generator is fine) |
| `[auth].client_id` | Google Auth Platform OAuth Web Client ID |
| `[auth].client_secret` | Google OAuth Web Client Secret |
| `[auth].server_metadata_url` | `https://accounts.google.com/.well-known/openid-configuration` |
| `GROQ_API_KEY`, `GEMINI_API_KEY` | Existing privately saved AI keys |
| `CF_ACCOUNT_ID`, `CF_AI_TOKEN` | Existing Cloudflare Account ID + Worker AI token |
| `CFBD_API_KEY` | Existing CollegeFootballData key |
| `PROPLINE_API_KEY`, `PARLAY_API_KEY` | Existing no-card odds API keys |

**TOML placement matters:** All top-level credentials go before the `[auth]` block, as demonstrated by the example file. The OAuth client secret must be within `[auth]`. Keep `cookie_secret` securely stored; changing it logs everyone out.

App visibility: A private GitHub repo produces a private Streamlit app by default. For **one simple BTA login**, choose *Sharing → Who can view this app → Public* once the BTA sign-in gate is configured. This makes the **URL reachable**, **not the member tickets**. Understand that Streamlit may list/search public apps, so avoid personal information on the login screen. Alternatively leave Streamlit app private, but then each friend will need a separate Streamlit viewer authorization *in addition to* the BTA Google sign-in.

## 5. Test the owner access with a Google account

Sign in with the **same Google email** entered as `BTA_OWNER_EMAIL`. The backend bootstraps exactly that one owner record in Supabase, and your verified Google subject binds on first login. If the Google email doesn't match, access is denied. The app owner may then open Sidebar → Owner controls → approve another person's verified Google email for seven days. **No email is sent**: message your friend the app URL privately. When they sign in, BTA checks their approved email, binding Google subject and invitation expiry. If expired, renew from owner controls. Disable/revoke from the same panel.

## 6. Enable durable research and encrypted backups

GitHub repository → Settings → Secrets and variables → Actions → add (secret names only, no strings in files):

`SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `CF_ACCOUNT_ID`, `CF_AI_TOKEN`, `CFBD_API_KEY`, `PROPLINE_API_KEY`, `PARLAY_API_KEY`, `BTA_BACKUP_KEY`.

`BTA_BACKUP_KEY` must be a valid Fernet secret: generate it from owner controls after signing in, or privately run `python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())"`. **Never post it to GitHub or this chat.** Save it separately so backups can be decrypted later. In the GitHub Actions tab enable `BTA research and live-status polling` and `BTA encrypted daily snapshot`; start each workflow via **Run workflow** once. Scheduled runs are best-effort and can be delayed or paused under free limits.

Backups are encrypted row-level application snapshots in Actions artifacts (14-day retention in included workflow); **not a verified full PostgreSQL database/PITR backup**, and not a substitute for an isolated restoration drill. Perform that drill before relying on multiuser production data.

## 7. Verify in deployed environment (owner can do the basic walkthrough)

- Owner Google sign-in succeeds; unapproved Google email is rejected. Disable an account and confirm it loses access.
- Add one NBA, NFL or CFB fixture and exact prop → My Slip → Submit Ticket → job queued → worker processes → report with source-age and blocked/qualified status.
- Confirm actual PropLine/Parlay quotes when available; never substitute manual entries for verified offers.
- Test with two real members: A cannot view/copy B's private tickets, except explicitly frozen shared snapshots; revoked share disappears.
- Check iPhone Safari layout, five tabs and floating Ask BTA.
- Check research worker GitHub Actions logs and crypto backup; perform a segregated restoration test.

### What is *not* a guaranteed feature of free accounts

Continuously updated official injury/prop coverage, comprehensive historical settled props, 24/7 monitoring and numeric model-calibrated probabilities are **not guaranteed** by these services. BTA must show verified current/delayed/unavailable and pending statuses where decisive evidence is missing. A test pass with mocked provider payloads does not prove a true live integration.

### You do NOT need Gmail

There are **no Gmail settings, Gmail application passwords, custom SMTP settings, or magic link templates** in this edition. You do need your Google account for the **identity sign-in**, not for email delivery.
