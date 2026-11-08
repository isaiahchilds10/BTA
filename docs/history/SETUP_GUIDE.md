# BTA 2.0 — Owner setup, no programming required

**Goal:** upload *one* code package into a **new private GitHub repository**, host it on **Streamlit Community Cloud**, create the **new Supabase database/auth** system, and supply the **three optional free AI keys**. BTA is a research companion, not a sportsbook. **An installed package is not evidence that outside services are operational.**

## 0. Before you start

- Use a **desktop browser** if possible for GitHub's Upload files and Supabase SQL Editor (copying folders on iPhone can be difficult). You need **no Codespaces, Python editor, branches, or terminal**.
- Keep your old `BTA-2.0` repository/deployment unchanged.
- **Create the new GitHub repository as PRIVATE.** Streamlit Community Cloud supports private GitHub repositories once access is authorized. Private code also avoids exposing backups and email setup details.
- Your ZIP is a package to **extract**; GitHub needs its **files**, not a single zipped file committed as-is.
- No promise that third-party sports-data feeds will cover every market. Unverified facts never produce fake BTA grades.

## 1. GitHub (project storage)

1. Sign in at https://github.com/new.
2. New repository name: `bta-2-independent` (or another available name). Select **Private**.
3. Create repository. Do **not** initialize with a sample README if you want a clean upload.
4. Extract the downloaded `BTA_2_0_CONSOLIDATED.zip` onto your computer.
5. Open your repository and choose **Add file → Upload files**. Select the extracted files *and folders* (including hidden `.github` and `.streamlit` folders). Commit directly to `main`. Some browser upload interfaces have limitations when selecting folders; GitHub Desktop is a fallback, but never Codespaces is required.
6. Confirm that `streamlit_app.py` and `requirements.txt` appear at the repository root and that `assets/bta_belt_branding_logo.png` is present.
7. Do **not** upload `.env`, `secrets.toml`, database exports, API keys, or GitHub token values.

## 2. Supabase (new project and private storage)

1. Sign up / log in at https://supabase.com/dashboard and create a **new project** in the **Free** tier. Record the project name. It is independent from all older BTA data.
2. Within the project: **SQL Editor → New query**. Open this ZIP's `sql/001_schema.sql` in a text viewer, **copy the contents**, paste into Supabase SQL Editor, and select **Run**. This is a one-time database installation, not software programming. It creates tables, row-level security, controlled RPC functions, ticket version snapshots and job claims. **Do not use this SQL in an existing project.**
3. Under **Project Settings → API Keys** (UI labels may vary): locate:
   - **Project URL** → `SUPABASE_URL`
   - **Publishable / anon key** → `SUPABASE_ANON_KEY`
   - **service_role secret key** → `SUPABASE_SERVICE_ROLE_KEY` (strictly private server secret; never share in chat, public code, or browser console).
4. Under **Authentication → Providers → Email**, enable Email and disable **public signups/allow new users** where supported. BTA provisions invited users itself with the server-only admin API, and sign-in calls set `should_create_user=false`.
5. Under **Authentication → URL Configuration**, set **Site URL** to your actual Streamlit deployment URL, e.g. `https://your-chosen-app.streamlit.app/`, and add it to the authorized Redirect URLs.
6. Under **Authentication → Email Templates → Magic Link**, replace the content with a simple link compatible with Streamlit server-side token verification:

   ```html
   <h2>Your BTA sign-in link</h2>
   <p>Click once to sign in to your invited BTA account:</p>
   <p><a href="{{ .SiteURL }}?token_hash={{ .TokenHash }}&amp;type=email">Sign in to BTA</a></p>
   <p>If you did not request this, ignore this email.</p>
   ```

   This is required: a standard Supabase confirmation URL typically returns a session in a URL fragment the Streamlit server cannot read. Template customization is available for new free projects when custom SMTP is configured.
7. Configure SMTP in step 3. Without it, Supabase's default service only sends to preauthorized team emails and does not work for a general invited friend list. The first owner account is created automatically when the private app starts using `BTA_OWNER_EMAIL` from Streamlit Secrets.

Useful official docs: https://supabase.com/docs/guides/auth/auth-email-passwordless and https://supabase.com/docs/guides/auth/auth-smtp

## 3. Passwordless email delivery (Resend or private-beta Gmail fallback)

**Preferred:** Resend (https://resend.com). Its free plan is currently advertised at up to **100 emails/day and 3,000/month**, but sending to other people requires domain verification and may require that you already own a domain (which may cost money). Steps:

1. Create a **free** Resend account.
2. Add a domain you **already own** under **Domains** and complete the DNS verification shown by Resend. Don't buy a domain without deciding to relax the all-free condition.
3. Create an API key under **API Keys**; treat as an SMTP password. Under Resend's SMTP settings use host `smtp.resend.com`, username `resend`, password = Resend API key, port `465` (SSL) or `587` (TLS, if accepted in the Supabase form).
4. In Supabase → **Authentication → SMTP Settings**, enable custom SMTP and enter those settings; sender address must be on your verified domain. Turn **email tracking off** for auth links.
5. In Supabase → **Authentication → Rate Limits**, ensure email send limits fit your small invited user list, and do not loosen abuse controls.

**Free small-beta alternative if you have no domain:** an eligible Gmail account with Google 2-Step Verification and an App Password may work as Supabase SMTP using `smtp.gmail.com` (ports `465`/`587`). From address/SMTP login = the Google mailbox. This is a **best-effort personal SMTP fallback**, not a tested production service; app passwords are not available for every Google account, and Google may limit/block messages. Do not risk an important personal mailbox if you're uncomfortable. Google account app password guidance: https://support.google.com/mail/answer/185833 and Supabase SMTP troubleshooting: https://supabase.com/kb/troubleshooting/using-google-smtp-with-supabase-custom-smtp-ZZzU4Y

## 4. Streamlit Cloud (deploy website)

1. Go to https://share.streamlit.io and continue with GitHub. Authorize the **private repository** if requested.
2. **Create app → Yup, I have an app**. Choose the **new** repository, branch **main**, and main file **`streamlit_app.py`**.
3. Assign an available app subdomain. Copy the **actual URL**, e.g., `https://bta-2-independent.streamlit.app/`.
4. In the new app's settings → **Secrets**, copy all setting *names* from `.streamlit/secrets.example.toml`, replace placeholders with your personal values, and save. Use your own email for `BTA_OWNER_EMAIL` and the real URL for `BTA_PUBLIC_URL`.
5. If you created the Streamlit deployment **before** the Supabase SMTP and email URL setup, update the Supabase Site URL and return to the deployed app. It should show **BTA private sign-in**, not demo mode. Enter your invited owner email and request the single-use link.
6. **Secrets are never committed to GitHub source.** The owner role is provisioned from the configured owner email. Invite additional people from the owner controls in the Streamlit sidebar.

## 5. Three independent AI-provider accounts

BTA's provider adapters send **public sports evidence only**. They do not transmit a member's email, private account history, or full saved slip. Models are not authoritative injury/stats sources, cannot approve grades, and have rate/usage caps.

- **Groq:** https://console.groq.com/keys → create an API key → paste value into Streamlit Secrets as `GROQ_API_KEY`. Default model `llama-3.3-70b-versatile`; model availability can change.
- **Gemini:** https://aistudio.google.com/api-keys → select a project and create a Gemini Developer API key on the free tier → `GEMINI_API_KEY`. Default `gemini-2.5-flash` (verify it remains eligible for your project's free allocation). Google publishes free-tier data-use conditions; review before use.
- **Cloudflare Workers AI:** https://dash.cloudflare.com → Workers AI → **Use REST API** → create a token restricted to Workers AI → copy **Account ID** and **API Token** into `CF_ACCOUNT_ID` and `CF_AI_TOKEN`. Use currently available, non-paid-restricted model `@cf/openai/gpt-oss-20b` in `CF_AI_MODEL`; check model catalog/limits before deployment.

BTA retries one distinct eligible provider after error/quota/invalid output. It does not guarantee three models are available at any given moment. You may reorder priorities via `BTA_AI_ORDER` in Streamlit Secrets, e.g., `groq,gemini,cloudflare`.

## 6. GitHub Actions (background scans)

For regular queued research while Streamlit sleeps, in the **new private GitHub repository** open **Settings → Secrets and variables → Actions → New repository secret**, and add these **exactly named** secrets:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `GROQ_API_KEY`
- `GEMINI_API_KEY`
- `CF_ACCOUNT_ID`
- `CF_AI_TOKEN`

The checked-in `.github/workflows/research_worker.yml` schedules checks approximately every 15 minutes and supports manual execution via the Actions webpage. Scheduled GitHub workflows can be delayed, missed, or stopped by inactivity. This is **not** real-time/24-7 guaranteed monitoring.

## 7. Encrypted backup

This ZIP includes `scripts/secure_backup.py` and `.github/workflows/encrypted_backup.yml`: they encrypt a snapshot, check the checksum and replay row counts into an **isolated temporary SQLite database**. The workflow refuses to run outside a **private GitHub repository**, and encrypts the artifact for limited retention. To enable:

1. Generate a new Fernet key via a trusted offline cryptographic generator or a secure administrator tool. You can also use the *optional owner-only key generator* in the app after first sign-in if available. **Never invent, reuse, or include the key in GitHub files.**
2. Put the value in **GitHub Actions repository secret `BTA_BACKUP_KEY`**.
3. Trigger the encrypted backup workflow from the GitHub Actions UI after your account is configured; encrypted artifact will be stored for 14 days subject to platform retention terms.
4. **Important:** the automated SQLite drill proves data extraction/encryption/round-trip integrity, **not** a production-grade Supabase PostgreSQL restore. A separate isolated Postgres restore and access-control drill are still required for the approved production security acceptance.

## 8. Your app checklist (no coding, but cannot skip real operational evidence)

- You can sign in with email; an uninvited address is denied.
- You can add selections through a league fixture or My Slip, submit the full ticket, and see real status/uncertainty; no fabricated grading occurs.
- The floating Ask BTA bubble works with at least one configured free API key, or accurately says unavailable.
- Another invited member sees **only their own** private slips.
- GitHub Actions runs the worker and encrypted backup without exposing secrets.
- Real source availability, current official injuries, model quotas and market coverage have been reviewed before claiming full BTA certification.

The codebase includes automated tests and documentation, so you do **not** need to manually run Python tests. Actual email receipt, mobile Safari behavior and independent multiuser/backup acceptance require outside service accounts and cannot be truthfully certified by an offline ZIP alone.
