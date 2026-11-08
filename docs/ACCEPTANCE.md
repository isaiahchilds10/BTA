# Launch acceptance worklist — do not confuse unit tests with production tests

## Included automated source checks

Run: `python -m pytest -q` and `python -m compileall -q bta scripts streamlit_app.py`.

Tests cover numeric American-odds break-even, YES/NO thresholds and push, distinct college/NFL scenarios, duplicate exposure, quick-add parsing, 3/3, hit sample counts, Wilson descriptive uncertainty, time cutoff filters, two-WORSE rejection, no certification with missing decisive inputs, game mapping, NFL rushing/passing/receiving category separation, team schedule samples, demo ticket immutable versions, optimistic concurrency and 30-leg guard.

**These are isolated fixture tests, NOT checks that ESPN, Supabase Auth, email delivery, mobile UI, Groq/Gemini, GitHub schedules or official injuries work right now.**

## Needed external acceptance gates

- [ ] From the ACTUAL new Streamlit Cloud deployed host, load correct/upcoming/live/final real fixtures for each sport and prove all important team and time fields are correct.
- [ ] Measure provider latency/errors/schema variation over at least representative upcoming game windows and verify permission/licensing.
- [ ] Confirm at least one real official injury + QB/role source per applicable sport and current source timestamps.
- [ ] Verify actual offered FanDuel/Polymarket lines, resolution rules, cancellation/push handling, and alternate independence.
- [ ] Complete opponent-adjusted role/line-specific research and exact five-script verdicts from logged evidence; independently critic-review high grades.
- [ ] Use chronological, snapshot-preserving out-of-time model validation to independently establish probability reliability; never relabel observed 10/10 as probability.
- [ ] Process and restore a real 30-leg multi-sport slip after browser refresh, worker restart, host sleep and one backend outage.
- [ ] Execute invite/sign-in from actual external email; uninvited rejection, expired/replayed auth link, lost session, owner revocation and user A/B access isolation.
- [ ] Validate read-only share freeze, revocation and fresh-research copy.
- [ ] Test worker scheduled runs from GitHub Actions when Streamlit is sleeping, quotas/rate limits, retries and deduplication.
- [ ] Observe live player stats / evidence age, injury change and actual pregame cutoff. Implement/verify official settlement and stat correction before any settled claims.
- [ ] Complete encrypted durable database/auth backup and **actual isolated restore**, compare checksums, test secret/key rotation.
- [ ] Test real iPhone Safari, Android Chrome, desktop browsers, low-bandwidth failure and mobile nav.
- [ ] Complete owner + invited-user private beta, close all high-severity security/data-loss/research-integrity defects.

Only after these pass may the production release be called BTA 2.0 complete under the handoff specification. Missing advanced features may remain explicitly unavailable only if the core acceptance contract permits them.

For basic **live external feed smoke checks** from your chosen hosting environment, run `python -m scripts.smoke_sources`. It reports which of the three scoreboards fetched and how many events were returned. A successful HTTP response without fixtures is not proof of good upcoming event coverage. This script is not a substitute for detailed real-game validation.
