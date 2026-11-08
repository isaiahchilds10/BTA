# BTA 2.0 — FINAL Master Build Specification
## BELT TO ASS | Independent rebuild | Approved product and engineering baseline v2.0 | 2026-11-07

**Specification status:** **All product choices and all eight final technical-policy decisions are approved.** This is the build contract, not a claim that the application, sources, models, infrastructure, or AI integrations have been implemented or live-tested. Unverified capabilities remain explicit acceptance gates.

**Core directive:** Build a brand-new, independent BTA application in a **new GitHub repository and new Streamlit deployment**, with new application and research-engine code. Preserve the existing repository and deployed app unchanged. Use the previous work and original 40-section BTA methodology as requirements and test references—not as code dependencies. Develop NBA, NFL, and college football in parallel, test components in stages, and release one integrated replacement when its required features meet acceptance criteria. Keep the project within free tools, free data sources, and free service tiers; do not silently add a paid dependency.


## Approved final decisions — eight of eight

| Final # | Decision | Binding implementation meaning |
|---|---|---|
| 1 | **Official sources plus corroborated credible reporting** | Official reports control official status; corroborated reputable reporting may trigger early warnings and scenario checks, but cannot be relabeled official. Preserve citations, timestamps and uncertainty. |
| 2 | **Adaptive multi-agent AI research** | Specialists investigate relevant topics and a logically independent critic searches for errors and overlooked failure paths. Verified evidence and deterministic BTA rules, not an AI narrative, decide qualification. |
| 3 | **Dual certification** | Keep qualitative, source-gated BTA tiers distinct from independently validated numeric hitting probabilities. No mapping from grades or short historical streaks to invented percentages. |
| 4 | **Adaptive live coverage** | Current/delayed/unavailable states; display last verified data and its timestamp; retry, but suspend probability updates when required inputs are stale. |
| 5 | **Smart free resource management plus multi-AI failover** | Rank genuinely free AI providers using measured quality for each task; switch automatically on qualifying failures/quota exhaustion; persist verified work; run deterministic BTA even if all models are exhausted. No guaranteed uninterrupted access. |
| 6 | **Full security and recovery** | Invite-only account protections, encrypted backups, real restoration tests, per-member isolation, audit logs and an owner-only administration/health interface. |
| 7 | **Full QA plus private beta** | Automated tests, chronological historical replay, independent audit, live-feed observation, account/security testing, cross-platform UX and free-quota/agent-failover stress tests. |
| 8 | **Strict core launch gates with honest limitations** | Single consolidated launch only after the three-sport core research, My Slip, authentication/privacy, durable automation, data integrity and recoverability pass. Unsupported advanced markets and predictions must be visibly unavailable, never simulated. |

**Interpretation:** These eight decisions **supplement rather than replace** all earlier BTA design approvals. They are implementation requirements; provider names, quotas and exact deployment techniques must still pass empirical feasibility testing.

## 1. Product vision and nonnegotiable operating principles

BTA stands for **Belt To Ass**, never a fabricated alternate expansion. It is an **invite-only sports research and decision-support platform**, not a sportsbook and not an automated wagering service. The central value is comprehensive, autonomous, evidence-backed analysis of individual games and props, cross-sport tickets and parlays, and live developments. Users should make selections and understand research without having to collect statistics, complete an audit manually, or interact with a chatbot.

Nonnegotiables:

1. **Automatic first:** BTA collects, verifies, deduplicates, contextualizes, and analyzes available real data by default. Ask BTA is a small, optional explanatory tool; the research engine must work without a paid language-model API or chatbot prompt.
2. **Presentation simplicity does not reduce research rigor:** preserve BTA's original 40 methodology sections and independent sport-/market-specific tests. Hide technical controls behind intuitive screens; make deeper evidence expandable.
3. **Never invent:** games, player status, official injuries, lines, odds, statistical values, source timestamps, model probabilities, certainty, BTA grades, settlement, or provider functionality.
4. **Evidence-gated certification:** missing vital injury/role/market/settlement evidence leads to `PENDING VERIFICATION`, `NOT ASSESSED`, or a clearly distinguished provisional finding, never unsupported BTA+ or TAIG certification.
5. **Original records are immutable:** pregame predictions, source snapshots, evaluations, offered thresholds and timestamped evidence are preserved; refreshes create versions, not hindsight edits.
6. **No-lookahead historical testing:** evaluate only information actually available at the original forecast cutoff. Use contemporaneous market offers where value/odds are tested; no hindsight line choice or final-score leakage.
7. **User control:** cuts, changes, substitutions, and sharing permissions are recommended, not silently executed. No automated real-money bets.
8. **All-free constraint:** no paid APIs, hosting, authentication, SMTP, inference, odds feed, or commercial service required. If critical features cannot be made genuinely reliable within free limits, expose a precise limitation, keep safe partial functionality, and do not call the feature ready.
9. **Privacy/security:** each invited member has private slips/history; server-side authorization is enforced, not merely UI hiding.
10. **Accuracy before cosmetic polish:** meaningful live and retrospective claims must be proven with fresh real feeds, out-of-sample evaluation, and adversarial acceptance tests.
11. **Multi-agent AI is not a shortcut around missing data:** context research and red-team criticism are bounded by verified retrieved evidence, an independently functioning Python research core, and confidence/provenance rules.
12. **Safe degradation is part of the product:** stale/incompatible source, exhausted AI quota, delayed scheduler, failed email delivery and insufficient market coverage have explicit truthful states and retry behavior; do not silently substitute invented evidence or an unvalidated model.

## 2. Branding, platform, and navigation

- **Brand:** BTA / BELT TO ASS. Preserve the previously approved logo design: a regular black leather belt (not a wrestling/championship belt), red stitching, silver buckle, bold white BTA lettering, and BELT TO ASS underneath. The previously approved exact logo asset has now been located and visually inspected in the working files (`bta_belt_branding_logo.png`); preserve this asset without regeneration. Include it in the delivery package and in the future fresh repository as a branding resource.
- **Color and typography:** premium sportsbook-inspired red, black, charcoal, and white. Athletic bold headings; clean, readable body text. Strong hierarchy, controlled density, premium appearance, accessible contrast.
- **Primary delivery:** publicly reachable browser URL with **private login**, optimized for iPhone and Android browsers and responsive on desktop. **No App Store submission or mandatory download.** Optional Add to Home Screen behavior may be offered if achievable, but ordinary browser use is first-class.
- **Fresh deployment:** a completely new GitHub repository and Streamlit Community Cloud app, each independent of the old version. No v0.5–v1.1 code is to be transplanted as a hidden foundation. A standalone Python research package and persistent database may support the Streamlit UI. Streamlit capability limits must be tested, not ignored.
- **Five navigation destinations:** Home, NBA, NFL, College Football, My Slip. Mobile: fixed bottom navigation when feasible and tested. Desktop: polished left sidebar. No maze of Command Center, Model Lab, Risk Lab, Stress Deck, Audit, and Certification tabs. Their functions belong behind main workflows.
- **Visual conventions:** expandable game cards on mobile, broader scoreboard-style rows on desktop; role- and team-filtered player/market browsers; no exposed raw JSON or code. Research pages must show source age, grades/status, failure routes, and expandable complete reports.

## 3. Screens and user journeys

### Home

Automatically load relevant upcoming games and any live games; show research activity, important changes, and a ranked **BTA Finds** feed. BTA Finds uses three separate discovery stages: **Worth Investigating**, **Strong Research Candidate**, and **BTA+ Certified** (only after every applicable evidence and grade gate is passed). Display no artificial quota or guaranteed three picks per game. Rank by validated evidence strength, recency, verified market availability and game time; permit league/game filters. Show a manageable featured subset on Home and full feeds in league sections.

### NBA

NBA games, schedules, live states, player markets and team/game lines. Market families include points, made threes, rebounds, assists, combinations, defensive stats, and game lines when data supports the requested terms. Player and market views both supported. Evaluate minutes/rotation, usage, shot volume and efficiency, recent comparable samples, pace, matchup, opponent quality, injuries, fouls, blowout risk, role changes and meaningful adversity.

### NFL

NFL matchups, player and game lines. Relevant markets include passing yards/TDs, rushing yards, attempts, receptions, receiving yards, TD scorer, alternative thresholds, and game lines, always subject to exact market semantics and data availability. Evaluate routes/targets/snaps, carries, QB and offensive-line health, defensive coverage/front, matchup-adjusted opportunity, coaching/rotation shifts, red-zone/inside-five roles, and game-state effects.

### College Football

Prioritize FBS matchups, display schedules and game lines, moneylines, spreads and totals. Analyze quarterback availability, trenches, opposing units, opponent quality, coaching, turnovers, venue, weather, strength of schedule, roster availability, game scripts, and upset paths. Do not substitute an NFL player-prop scenario model for a college moneyline model. FCS candidates require materially stronger evidence and demonstrated matchup separation; no forced approval.

### My Slip

Support **up to 30 legs per ticket** and multiple saved tickets per member. Default to a **Smart Dashboard** that elevates active tickets and alerts, then upcoming/drafts and completed history. Search, filters, compact leg summaries, expandable full reports, and status by leg. Slips can mix leagues. Each active ticket shows research progress, individual risk, user-approved cuts/changes, live status, shared exposure, final result, and immutable version history.

## 4. Adding selections and confirming exact markets

Three methods are available:

1. Browse games → select team/player → choose market and the real verified offered line when available → add to slip.
2. **Quick Add:** paste multiple plain-text selections; parse sport, game date, team/player, direction, market, threshold, and optional sportsbook price; highlight uncertain fields.
3. **Screenshot import:** optional, only when dependable **free** image recognition can be integrated and tested. Show extracted selections for explicit confirmation, including team/player identification, over/under, line, book and game. If unreliable, do not ship it as operational.

Manual exact FanDuel or alternate thresholds are allowed when a lawful verified odds feed does not cover them; mark such entries `USER-ENTERED / MARKET NOT VERIFIED`, and distinguish model support for the threshold from proof of a current sportsbook offering. Never silently adjust, round, invert or substitute markets. Capture whether the book's total is inclusive or exclusive, whether push is possible, settlement/void rules, applicable scoring period and market-specific conditions. Keep FanDuel and Polymarket terminology distinct.

## 5. Two-stage ticket assessment

**Stage 1 — Analyze My Legs:** Adding a leg queues automatic individual research. Running the explicit Analyze action requests a fresh check of every leg and provides a quick verdict plus expandable complete BTA audit. The UI presents original grade/status, proposed keep/adjust/replace/cut, evidence quality, source dates, five-script labels, risks and failure modes. Let users approve, reject or override suggestions; record the decision.

**Stage 2 — Assess My Parlay:** After individual review, evaluate the remaining ticket as a whole: same-game dependencies, correlated injuries/roles, game scripts, overlapping nested thresholds, mutual incompatibilities, combined uncertainty, settlement exposure, and concentration. Do not multiply historical hit rates or assume independence to claim an accurate joint probability. Show combined probability **only** if a joint model has passed prospective/out-of-time validation; otherwise show an evidence-based qualitative risk assessment. Evaluate a ticket with incomplete legs, but separately show the effect of excluding them—without actually removing them—so users see a **dual assessment**.

The qualified BTA research board and the final user ticket are separate objects. There is no mandated count of approved selections. **Incomplete legs:** display original slip risk and a separate illustrative assessment excluding incomplete legs, without silently editing either the original ticket or any pregame prediction.

## 6. Binding policy: KEEP, ADJUST, REPLACE, CUT

**Core philosophy: Never save a bad bet merely to keep a larger ticket. A smaller defensible ticket is preferable to forced replacements.**

- **KEEP:** Original exact selection survives evidence requirements and all applicable BTA gatekeeping; do not adjust merely for novelty.
- **ADJUST:** The *underlying player role and scenario are credibly favorable*, but a threshold is aggressive. Re-evaluate a verified *real offered alternate threshold* (for example, over 20.5 points versus over 15.5) **as its own independent selection**. Compare hit likelihood, typical/missing margin, floor/cushion, adverse scripts, price/payout/value when available, and correlation with the existing ticket. A lower target can increase hit rate while reducing value. If alternate offer/price is not verified, say so. Never auto-change the user's selection.
- **REPLACE:** The original leg fails, but there may be a genuinely independent, stronger opportunity in the same or another game. BTA may research alternatives automatically, but only recommend replacements that pass the **full same evidence gates and second-pass audit** and do not introduce unacceptable shared risk. A replacement is not mandatory. Avoid chasing unrelated picks merely to maintain leg count.
- **CUT:** The original proposition is structurally unsound, has a credibly ordinary failure mechanism, a harmful injury/availability/role problem, unsuitable matchup, material confidence blocker, or fails BTA stress criteria. Do not disguise a bad play with arbitrarily low alt lines or another marginal market. If evidence is insufficient rather than adverse, use `PENDING` instead of claiming it is definitively bad.

**Stress-test hard rule for player props:** Each of five sport-specific situations gets evidence-linked **BETTER / SAME / MIXED / WORSE**. **Two or more meaningful WORSE verdicts = CUT from the strict ticket. One meaningful WORSE = special review; zero meaningful WORSE = priority candidate, not automatic certification.** A genuinely bad alternate does not gain an exception just because its threshold is lower. Preserve grade history after every reassessment. Users approve all edits.

## 7. Original BTA 40-section methodology — mandatory requirement crosswalk

**Preservation note:** Retrieved source files contain the original sections **19–40** in summarized form, plus an implementation audit identifying requirements **1–18** by title and function. The original word-for-word 1–18 prompt was not included in those files. This crosswalk preserves all retrieved functional requirements; a verbatim comparison remains an explicit acceptance step if the original text is later supplied.

### Sections 1–18: foundational framework (requirements reconstructed from the prior audit, not claimed verbatim)

| # | Mandatory functional requirement |
|---|---|
| 01 | Analyst objective, disciplined selection and expected value separated from raw confidence. |
| 02 | Approved BTA grade hierarchy and independent, evidence-supported promotion rules. |
| 03 | Current source-verified data, status, identity and market terms. |
| 04 | Full statistical/situational matchup audit; strength and quality of opponents in both directions. |
| 05 | Five game-script stress test with explicit failure mechanisms. |
| 06 | Distinct college-football moneyline/matchup analysis. |
| 07 | Distinct NFL player-prop opportunity and downside evaluation. |
| 08 | Ordinary failure audit: show a credible common way the selection loses. |
| 09 | Implied odds versus genuinely estimated probability and EV; never conflate. |
| 10 | Parlay construction, dependencies, correlations, and ticket risk. |
| 11 | Live-game research as a separately timestamped, in-game assessment. |
| 12 | Complete final report with evidence, script verdicts, board and recommendation. |
| 13 | Batch/schedule management: persistent unique-game ledger, resume, dedupe, counts. |
| 14 | Quality control, independent evidence checks, model and source reliability. |
| 15 | Ten-question evidence/decision hierarchy applied rather than just displayed. |
| 16 | Nonnegotiable research, integrity, transparency and no-fabrication behavior. |
| 17 | Autonomous slate ingestion and grading workflow for submitted game lists. |
| 18 | BTA's conservative philosophy: rare ordinary failure routes outweigh enticing ceilings. |

### Sections 19–40: user-requested continuation (source-grounded)

| # | Mandatory functional requirement |
|---|---|
| 19 | Keep **college moneyline five scripts** independent of **NFL player-prop five environments** and appropriate NBA scripts. |
| 20 | Script BETTER/SAME/MIXED/WORSE with explanatory evidence; ≥2 meaningful WORSE = prop cut, 1 review, 0 prioritized. |
| 21 | Game-by-game exact-threshold 3-for-3 comparison and larger role-comparable sample; inspect exceptions and miss margins; never claim 3/3 means certain. |
| 22 | Median, typical opportunity, realistic downside floor, line clearance margin, and explosive-play dependence. |
| 23 | Separate ordinary losses, exceptional contextual misses and structural bad-fit failures. |
| 24 | Opponent/defensive quality and efficiency adjustments, for both over and under cases. |
| 25 | Base, realistic adverse, and reverse-failure arguments with corroborating evidence. |
| 26 | Apply relevant supplemental 15 adversity scenarios without pretending all have equal likelihood; retain exact original list if supplied. |
| 27 | Approved tiers: **TAIG** (no TAIG+), **Elite/Core BTA+**, **Strong BTA+**, **Lower BTA+/Strong BTA**, **Standard BTA**, **Conditional**, **CUT**; pending/unverified remains separate. |
| 28 | Match actual Polymarket YES/NO, inclusive/under, injury, void and settlement semantics. |
| 29 | Separate passing, rushing, receiving, and anytime TD markets; evaluate red zone/inside-five role and opposing defense. |
| 30 | Quarter-specific markets use actual quarter-level data and exact scoring/settlement semantics. |
| 31 | Detect nested alternate lines and shared game, usage, injury, and script correlation. |
| 32 | Preserve full independently qualified board separately from narrower actual ticket. |
| 33 | Distinguish platform-specific FanDuel versus Polymarket offers, exact lines, settlement and availability. |
| 34 | Require a truly independent second pass for TAIG/Core BTA+ promotion. |
| 35 | Display exact N/N denominators, eligibility definitions, sample comparability and uncertainty. |
| 36 | Preserve college game order and unique-slate ledger, reconcile totals; FBS preferred. |
| 37 | Prioritize decisive evidence and do not certify with high-impact unanswered questions. |
| 38 | Full statistical audit, script matrix, failure routes, evidence quality, revised grade, ranked board and actual ticket. |
| 39 | Prefer a selection with **few credible ordinary failure mechanisms**, not merely a high projected ceiling. |
| 40 | Apply the entire system conservatively and consistently; no fake precision, grades or probabilities. |

**Exact football five-script families (not interchangeable):**

- **College football moneylines:** (1) normal expected game; (2) underdog races to a 10–0 or 14–0 lead; (3) favorite suffers two negative turnovers; (4) favorite's primary strength is neutralized; (5) game remains within one score in the fourth quarter.
- **NFL player props:** (1) favorite blowout; (2) underdog blowout or upset; (3) close/competitive game; (4) low-scoring game; (5) high-scoring game. Evaluate the prop's actual opportunity and failure mechanisms under each, not only the game-winner outcome.
- **NBA player props:** preserve the sport-specific five-script framework from the original methodology and validate exact script definitions against the original source prior to claiming complete fidelity. Include relevant injuries, minutes, rotations, blowouts, fouls, pace and usage when assessing each market.

**TAIG and grading:** TAIG = **That Ass Is Grassed** (exceptionally rare). BTA is **Belt To Ass**. Distinguish research tier/robustness from demonstrated positive expected value. BTA/ BTA+ certification cannot be based on 3-for-3, recency streak, unverified sportsbook offer, or automatically generated prose. Maintain an independently audited, source-grounded change log for grade promotions and demotions.

## 8. Freshness, evidence acquisition, and manual refresh

**Approved trust policy (Final Decision 1):** Start with league, team, game-official and otherwise authoritative primary sources for facts they actually establish. Use vetted credible reporting as an **early intelligence signal** when official sources have not yet updated. Corroboration must reflect genuinely separate evidence, not several outlets repeating one unnamed report.

- Every material injury/availability claim carries a **claim state** (`OFFICIALLY_CONFIRMED`, `CREDIBLY_REPORTED`, `CONFLICTING`, `UNCONFIRMED`, `OUTDATED`, `UNKNOWN`), the assertion being made, linked evidence/provenance, publication and retrieval times, and a reason when confidence is insufficient.
- An unofficial "expected to play" report must **never** be silently converted to `ACTIVE`, and observed warmups do not establish unrestricted snaps/minutes. Conversely, a player leaving the court/field does not establish `OUT_FOR_GAME`.
- When sources conflict, retain both claims, try independent reconciliation immediately within free rate limits, and explicitly identify the unresolved question. If it matters to the grade, keep the grade blocked or conditional as prescribed by BTA rules.


BTA automatically runs a **smart adaptive scheduler**: baseline research early; more attention near game time; targeted retries for unresolved player status or source conflicts; prioritize active slips across members; share source retrieval and caches without sharing member-private slips.

- Each evidence item tracks provider, original upstream timestamp (if known), retrieval timestamp, game/player ID, market unit, trust tier, freshness policy, and error status.
- Injury states distinguish **unconfirmed report / questionable / doubtful / inactive / out / ruled out / available / under review**, only when warranted by a dated trustworthy source. The interface must never infer “ruled out” merely from an apparent departure.
- If a critical item is stale or unavailable, automatically request the freshest compliant sources, use a tested fallback, state what was checked, and surface the unresolved risk.
- Provide a **Recheck Injury Status** or **Refresh Evidence** action that updates only relevant research state, not the whole page, session, selections, prior reports, or cuts. Deduplicate concurrent refreshes and respect free-source limits.
- A new sourced fact can change the live/pregame current assessment; it cannot rewrite earlier timestamped conclusions.
- Show accurate checked-at and provider-updated-at times; never claim real-time if the free feed is delayed.

## 9. Progressive research and background jobs

Adding a leg immediately creates a durable queued analysis job. Stream verified partial findings with stage-specific truthful states (`queued`, `retrieving`, `checking injury`, `testing scripts`, `pending evidence`, `complete`, `failed/retry`). Continue work when users navigate away; persist job state and the report in durable external storage. Do not represent a fake progress percentage. On provider failure, retry with sensible backoff and produce an explainable pending report rather than losing the job. Multiple same-game users should reuse cached source facts, not each trigger an identical download.

## 10. Game-start locking, BTA Live, and postgame results

**Approved adaptive live coverage (Final Decision 4):** `CURRENT` = required inputs meet each market's measured source-specific freshness policy; `DELAYED` = last known values remain visible with a conspicuous age warning, but model updates freeze when critical inputs age out; `UNAVAILABLE` = no trustworthy current feed for that feature. A fresh score does not make stale player availability or usage data fresh. UI must never claim per-second updates unless the provider genuinely delivers them.


**At each leg's scheduled actual game start:** preserve the final available pregame assessment and cutoff; incomplete forecasts stay incomplete. Do **not** freeze all remaining games on the ticket. After game start, maintain a separate **BTA Live** time series of verified in-game facts and forecasts.

- Live prop panels display score/period/time, observed progress against exact line, remaining requirement, relevant play/minutes/usage rates, foul/injury/rotation changes, source freshness, and confidence state.
- **Live probability percentages** appear only for market-specific models that have passed proper out-of-time testing and calibration. Otherwise show labeled observed progress, trends and uncertainties; progress-to-line alone is not a probability.
- Give priority monitoring to active member slips, with on-demand detailed monitoring for additional games. Share source facts across accounts, not their ticket contents.
- **Live cross-leg event intelligence:** detect an injury, usage change, substitution, blowout, pace change or lineup event; identify plausible related prop effects (QB/receiver, replacements, nested alt lines, same-game total), verify causal reasoning and update live estimates/risk. Do not assert a teammate will benefit without evidence.
- Full-ticket live screen displays settled/hit/miss/push/void, in-progress and not-started counts, important risk events, and a defensible qualitative joint outlook. A numerical parlay hit probability needs a validated joint model that handles dependencies and already-resolved legs.
- **Automatic postgame settlement:** ingest authoritative final stats and exact market-specific rules, handle pushes/voids/stat corrections and unresolved cases, preserve original pregame and live snapshots, and maintain per-tier sample sizes and performance analytics.
- Historical intelligence includes observed vs predicted results, model calibration (e.g. Brier/log loss where valid), baselines, changing role/error explanations, market-level performance, source availability and scenario failure categories. Do not retrain on future information that would contaminate past backtests; assess changes on held-out chronological periods.

## 11. Accounts, security, inviting, and sharing

- Invite-only membership; owner/admin controls issuance, expiration and revocation of **single-use private invitation links**. Members can open a link in Safari/Chrome, no app required.
- **Passwordless email magic-link sign-in**, verified email ownership, securely persisted sessions, session revocation, minimum-required email scopes, and sensible rate limiting. Disable open self-registration. Separate invitation redemption and authentication; a valid ordinary magic link must not bypass the invite rule.
- Each member's saved slips, research history, alerts and settings are private by default; access control is enforced for all database reads/writes. Use a tested managed free database/auth provider only if it passes operational and security gates.
- Share **read-only frozen research snapshots** or an authorized view with explicitly selected BTA members. Permit revocation. A recipient can copy picks to a new private slip; copies run fresh research and keep the original owner's slip unchanged. Avoid exposing private notes or historical account information by mistake.
- Optional email alerts for high-impact injuries, status/grade changes, finished research and BTA Finds; in-app alerts are always available. Email opt-in, per-event preferences and spam/rate controls required. No unsolicited blasting.
- **Approved full security/recovery (Final Decision 6):** secret rotation, least-privilege service credentials, server-enforced row-level authorization, signed/expiring one-use invites, session revocation, account deletion/export procedures, audit logs for authentication and admin activity, admin least privilege, and explicit abuse/rate-limit protections.
- **Backups:** encrypted at rest and in transit; retention and recovery objectives defined in the free-provider feasibility assessment; automated snapshots for the actual durable database (including member slips and grade history); routine restoration into a segregated test environment with checksum/integrity verification. A backup schedule without a successful restore test is not sufficient.
- **Owner dashboard:** issue/revoke invitations, disable members, review access/backup/restore health, inspect scheduler and provider failures, see quota/rate-limit warnings, and monitor incident records **without** bypassing member privacy. Distinguish admin maintenance privileges from member-shared data permission.
- **AI privacy:** pass the minimum necessary *sports research facts* to external models; never forward members' private emails, magic-link tokens, sessions, secret API keys or their complete personal slip histories. Review each free provider's retention, training and data-usage terms before enabling it.

## 12. Free-only architecture candidates and feasibility constraints

The following are **candidates**, not deployed/confirmed integrations:

- **UI:** new Python/Streamlit app on Community Cloud, responsive CSS and appropriate supported components. Test mobile bottom navigation, expansion, refresh state, iOS Safari browser chrome, session restoration and resource usage. Community Cloud apps can sleep after inactivity; do not rely on app process alone as an always-on scheduler.
- **Research library:** pure Python packages for data connectors, canonical entities, deterministic audits, grading policies, forecasting, correlation, historical validation, settlement and exportable evidence. Independent test suite; no reliance on the old engine.
- **Persistent storage and auth:** evaluate Supabase free tier or another free-compatible solution with real user isolation and durable histories. **Critical issue:** Supabase's default SMTP is restricted to authorized team addresses and is not appropriate for real invitations to arbitrary friends; a dependable no-cost external SMTP service or other genuinely free-compatible arrangement must be verified before declaring passwordless login complete.
- **Scheduling:** GitHub Actions scheduled jobs plus a durable job store/queue for batch scans, subject to rate and delay limitations. Free standard runners in public repositories exist, but scheduled events may run late, be dropped, or be disabled after inactivity; no guarantee of continuous second-by-second live monitoring. Keep secrets out of public source, disable billable extras and enforce spending caps where possible.
- **NBA:** official schedule/box/live feeds and historical game logs; confirm access from chosen hosting environment and track provider restrictions.
- **NFL:** nflverse schedules, rosters, team/player stats, game logs, PBP, snap counts, injuries and other appropriate public resources; evaluate the **actual update schedule**. Some in-season participation/route-grade coverage is delayed or unavailable; do not assume historical participation data is real-time.
- **CFB:** College Football Data and trustworthy schedules, official/team information, current injury/depth reports and history as licensing/tiers permit. Strict quota budgeting, batching, caching and fallbacks; verify current free allocation before selecting an integration.
- **Sportsbook markets:** use only legally/compliantly accessible free data. A free authenticated FanDuel feed with comprehensive alt lines is **not assumed**. Manual exact threshold plus a clear unavailable-odds warning is a valid research fallback; current bet availability/value claims need a verified quote.
- **Screenshot recognition:** test an open-source local OCR/parsing pipeline on representative real screenshots; optional if accuracy, supported host resources and privacy are adequate. Never trust low-confidence OCR silently.
- **Ask BTA:** lightweight optional explanation/search over saved BTA findings; an unrestricted LLM chat assistant is not assumed feasible for zero cost. Explanations must cite actual evidence, not infer missing facts.
- **Adaptive AI orchestration:** implement an engine-agnostic research interface with a ranked list of explicitly approved, zero-cost provider/model candidates (e.g., Gemini, GroqCloud, Cloudflare Workers AI, or a locally hosted open model **only if deployable on free infrastructure**). Names are **evaluation candidates**, not claims that any specific current free quota, model or provider will remain available. The orchestrator must switch qualified backends without leaking member-private context or losing verified work; exact quota and privacy terms require current documentation and deployed tests.
- **Agent workflow:** use limited specialist calls for nonroutine injury/role/matchup/source conflict research; one independent critique pass challenges conclusions. Ordinary stats, canonical ID joins, thresholds, five-script gates, settlements and scoring remain deterministic and independently testable. Minimize token use, cache reusable facts safely, and avoid agent-on-agent recursive loops.

**Source documentation to verify before implementation:**
- Streamlit Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud
- Streamlit resources/hibernation: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
- Supabase Auth + SMTP: https://supabase.com/docs/guides/auth and https://supabase.com/docs/guides/auth/auth-smtp
- GitHub scheduled-workflow limits: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- nflverse update schedule: https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html
- College Football Data: https://collegefootballdata.com/

## 13. Data architecture, APIs, and safety

**Source-of-truth ordering:** canonical game/player/market identities and original market terms first; verified provider facts second; derived deterministic features third; contextual AI summaries fourth. AI text is never itself proof of a stat, injury or offered odds. The confidence label of a derivative must not exceed the confidence of its decisive inputs.


Define canonical IDs for sport, season, competition, game, team, player, provider, market, offered selection, research snapshot, user, slip, version, and grade. Maintain a **provider adapter** per data source with typed schemas, field-level validation, unit conversion, source timestamp, and provenance. Clearly distinguish zero, missing, not applicable, unconfirmed and unavailable. No fallback defaults that convert missing data into favorable evidence.

All requests must have approved domain allowlists, TLS, safe redirects, retries/timeouts, rate limits, caching and secrets isolation. Never reveal API tokens in logs, links or public repository files. Use server-verified provenance—not caller-supplied `verified=true` fields—to determine eligibility for certification. Implement row-level/account-level authorization and tests against cross-member data leaks. Validate licensing/redistribution terms before caching or showing provider content to invited users. Keep no raw sensitive identity data in public workflows or CI artifacts.

## 14. Free-source feasibility gates and honest fallback behavior

| Required outcome | Launch acceptance | Honest fallback if free source is unavailable |
|---|---|---|
| Reliable automated upcoming schedules for all 3 sports | Tested live from deploy host, correct IDs/timezones/status | Game unavailable / last checked, not fabricated fixture |
| Market-specific full research | Evidence collected and explained without manual checkboxes | Partial research + missing-data blockers, no certified grade |
| Official injuries and status | Latest authoritative source and timestamp where obtainable | Unconfirmed/pending with recheck action |
| Verified sportsbook alternate line/price | Actual current permitted offer and source timestamp | User-entered selection; no claim of current availability/value |
| Live player context | Real working feed with measured delay from host | Display observed available stats with `stale/not available` notice |
| Hitting probability | Backtested and calibrated against held-out periods and naive baseline | No numeric probability; show verified stats and trends |
| Joint ticket probability | Defensible joint model handling dependencies | Qualitative overlap and ticket risk only |
| Passwordless login/email | Real invitee receives a free magic link and signs in securely | Block member launch; don't claim invite-only signup works |
| Background tasks | Durable progress across navigation/restart, real scheduled execution | Expose suspended/delayed jobs; no fabricated continuous monitoring |
| Historical settlement | Reliable stat + market rule matching and corrections | Unverified result, not forced win/loss |
| Screenshot import | High accuracy on genuine example images and error detection | Hide feature; keep browse and paste |
| Adaptive multi-AI research | At least one tested free task-qualified provider and independent critic path, with deterministic fallback | Continue verified deterministic analysis; report optional AI delay/unavailable |
| Multi-AI failover | Quota, timeout, invalid response and outage tests prove safe switch, persisted work and preserved provenance | Do not promote unverified output; queue/resume or continue without AI |
| Encrypted backups and restoration | Actual backup and isolated restore exercise passes data-consistency checks | Block private multiuser launch until a viable free recovery plan passes |
| Owner/admin controls and audit trail | Role-based tests, revoked-invite tests, protected logs, admin flow verification | Block member launch if access boundaries or audit functions fail |
| Private beta | Representative invitees successfully exercise core flows on mobile and desktop, and defects are triaged | Remain private/test-only until critical defects are resolved |

## 15. Implementation phases (parallel sports development, single coordinated launch)

**Phase 0 — independent foundation:** create new repository, test branch/protection, repo hygiene, requirements/architecture, versioned configuration, service-account permissions, secrets and free quota matrix. Original repository/deployment untouched. Revalidate previous logo asset.

**Phase 1 — shared infrastructure and three sports in parallel:** schemas, source adapters, canonical IDs, schedules, source freshness, data acquisition, league modules and game/market browser; each sport has its own tests. Independent daily and live status smoke checks.

**Phase 2 — all 40 audit and grade gates:** sport-specific five scripts, quantitative opportunity and downside, exact thresholds, source-gated grades, independent second pass, and evidence reports; no automatic certification until all relevant tests pass.

**Phase 3 — private account and slip system:** expiring invites, production-capable free email authentication, private storage, session restore, paste/optional screenshot import, parallel leg jobs, cut/adjust/replace policy, dual ticket assessment, safe read-only sharing.

**Phase 4 — automation and BTA Live:** smart adaptive scheduled scans, targeted refresh buttons, durable jobs, live per-leg and cross-leg event detection, source freshness reports, phased calibrated probabilities by supported market (never synthetic), user alerts. In parallel, implement task-specific multi-AI routing with budget accounting, quality benchmarks, independent critic and safe failover; deterministic execution remains the completion baseline.

**Phase 5 — results and retrospective validation:** final outcomes, snapshot preservation, model performance and baseline benchmarks, chronological validation, failure classification, edge-case audit, UI polish and accessibility.

**Phase 6 — end-to-end independent acceptance:** test all major flows on iPhone Safari, Android Chrome, desktop browsers, Streamlit Cloud, more than one invited member, and actual free providers. Include independent security review, encrypted backup restoration, resource/AI failover drills, chronological replay, real-game observation, and an invite-only beta. Launch the **new** integrated app only after **all mandatory core gates pass**. Advanced unavailable markets may be withheld behind truthful capability labels; a missing core system is not an acceptable limitation. No claim of full feature parity if source coverage fails.

## 16. Acceptance checklist and adversarial tests

1. A fresh authorized user can join through a single-use invitation, receive a genuinely delivered free magic link, sign in, and reopen their account on another device. An uninvited user cannot register.
2. User A cannot read, modify, or infer User B's private slips, historical reports, emails or alerts; shared snapshots only reveal explicitly permitted content; revocation succeeds.
3. One real upcoming game per sport appears with correct teams, kickoff/tipoff time, live/final transition, player identity, relevant available market families, and source timestamps from the deployed host.
4. Two concurrent users researching the same game share safe public cached facts, not member-private tickets.
5. A 30-leg mixed-sport slip survives browser refresh, Streamlit rerun, navigation, sleep/restart, failed source requests and cross-device sign-in without duplicated legs or lost edits.
6. When a receiver status goes from questionable to ruled out, only dated verified evidence changes that field; linked leg reports and live ticket flags change; old pregame snapshots remain immutable.
7. Manual Recheck refreshes a relevant source without dropping the slip or resetting the entire app; it cannot bypass provider limits or fabricate success.
8. 20.5-point over vs verified 15.5-point alternate: independent reassessment, probabilities separated from prices, lower hit threshold not automatically labeled better EV, and user explicitly accepts change.
9. Clear failing role/game-script leg is **CUT**, with no arbitrary low-line salvage or filler replacement. Zero acceptable alternatives results in **no replacement**.
10. Five-script labels are evidence-backed; ≥2 meaningful WORSE player-prop scenarios prevent strict ticket approval. Different CFB and NFL script families are actually executed.
11. Real odds missing: source state and manual line shown; no book-specific currently offered price or fabricated EV.
12. Late or contradictory injury data triggers pending, never false ruled-out/confirmed status or retroactive TAIG/BTA+ certification.
13. Starting an early game locks only its leg's pregame evaluation; later games keep refreshing; live estimations never rewrite pregame research.
14. A live prop displays real observed stats with a visible age; stale states never present as second-by-second data.
15. Only validated market-level models show percent predictions; only a validated correlated joint model shows entire parlay percentage. Grade labels and recent hit rate are not silently converted to probabilities.
16. Shared research is read-only; copying into a new slip performs fresh checks; the original owner sees no edits.
17. Final settlement accounts for void/push, stat corrections, quarter-specific semantics, and exact offer rules; insufficient information stays unresolved.
18. Historical backtests use timestamped pre-event sources and offerings, compare to baselines, track sample N/N, calibration, contamination and plausible failure scripts.
19. No UI asks users to manually enter a 40-question evidence form or paste raw JSON. Any failures show human-readable explanations and retry options.
20. No paid cloud/API key/service is silently required or any 24/7 claim made without measuring the free scheduler's real behavior.
21. An official `QUESTIONABLE` report plus an independently corroborated expected-to-play report is shown as "officially questionable; credible expectation to play"; BTA does not label the player confirmed active, and a grade remains appropriately gated.
22. Two superficially different articles relying on the same journalist are not counted as independent source corroboration. Contradictions remain visible until resolved.
23. Separate AI specialists provide inconsistent sourced claims: the critic detects them, the deterministic verifier applies source precedence, and no unsupported grade is issued.
24. Primary AI provider returns HTTP rate limit, timeout, malformed tool output or a privacy-incompatible result: BTA routes to a tested eligible backup, preserves evidence and state, and never repeats paid calls or loops without bounds.
25. All free AI providers unavailable: the deterministic engine still runs; an optional AI investigation is queued or marked unavailable; no one sees a fake AI-reviewed badge.
26. Primary live feed stops updating while game clock changes elsewhere: `DELAYED` state shows last genuine stat timestamp and freezes live probability, then resumes only after validated fresh inputs return.
27. A user's stored session cannot open an expired or revoked share; unauthenticated and cross-member direct database/API access is denied independent of Streamlit interface restrictions.
28. Run an automated backup and restore it to an isolated database; reconcile member, slip, snapshot and grade-record counts and integrity, with no private data included in public logs.
29. Historical model backtests exclude all post-cutoff injuries, results, lines and source corrections; performance metrics include sample counts, uncertainty and baseline comparison.
30. In private beta, a new user can open the link, receive sign-in email, create a 30-leg mixed ticket, navigate away, return across devices, run two-stage analysis, inspect warnings and share a read-only snapshot without losing any selection.

## 17. Explicitly unresolved implementation dependencies

1. **Verbatim original 1–18 and exact 15 adversity scenario wording** were not present in the retrieved requirement artifact; this document preserves their recovered functional audit but cannot certify word-for-word equivalence without originals.
2. **Approved logo asset has been recovered and visually verified** in working files. Include the exact asset in the fresh repository and final brand package; do not regenerate or substitute it.
3. **Truly free production email delivery** for invite-only passwordless links and optional alerts must be verified with real invitees. Default Supabase SMTP is not an acceptable assumed solution.
4. **Free live player-usage and injury coverage** for all NBA, NFL and CFB markets may be incomplete; capability should be indicated market-by-market.
5. **Free exact FanDuel lines and alternatives** may be unavailable. Manual inputs do not prove a line is actually offered or good value.
6. **Free scheduling and Streamlit hibernation** prevent a promise of uninterrupted high-frequency monitoring; measured freshness and honest degradation are required.
7. **Model calibration and joint probabilities** require historical offered-line datasets and no-leakage validation before numeric claims.
8. **Provider permissions/licensing** must permit collection, caching and member display. Do not depend on prohibited automated scraping.
9. **Free-model reality:** current rates, permitted app use, training/retention policies, tool calling, concurrent limits and request quotas for AI candidate providers must be inspected before selection; backups must be independently tested and ranked.
10. **Free-stack operations:** prove compliant free authorization for storage, email delivery, backups, scheduler and inference with actual invitees and measured loads; quotas and inactivity limits may prevent continuous monitoring.
11. **Quality thresholds:** lock the predeclared statistical acceptance metrics, data freshness policies and beta pass criteria during Phase 0/1 rather than choosing them after observing favorable results.


## 18. Detailed multi-AI research and failover contract (Final Decisions 2 and 5)

**Mission:** improve the completeness and critical scrutiny of evidence, not create artificial certainty. BTA's model choices are empirical and replaceable, not locked to a single vendor's marketing or an assumed GitHub AI facility.

### 18.1 Specialist task families

| Specialist | Authorized research | Prohibited shortcut |
|---|---|---|
| Injury/availability | Retrieve and reconcile dated official/credible reports, list conflicts and decisive gaps | Declare active/out based on rumors or inferred body language |
| Role/opportunity | Compare snaps, routes, targets, minutes, rotations, teammate absences and role changes | Invent route counts or infer future opportunity from a 3-game streak alone |
| Matchup/game script | Summarize verified defensive context, coaching, pace, trenches and adverse environments | Reuse one sport's scripts for another or override hard cut gates |
| Historical/market terms | Identify comparable samples, exact threshold semantics, offered-line provenance and void rules | Assert an alternate is currently offered when not verified |
| Adversarial critic | Seek an ordinary credible failure route, contradiction, dependency or data leakage | Rubber-stamp an earlier agent's conclusion or pretend independence |
| Verifier (code) | Join canonical IDs, enforce data/source types, compute features and gates | Treat model-generated claims as verified sports data |

### 18.2 Dynamic engine ranking, not marketing ranking

1. Build a **provider capability registry** keyed by task family and model version: approved privacy terms, free allowance, rate and token limits, structured-output/tool support, context limits, observed latency/reliability and failure modes. Log providers' explicit quota data when exposed; otherwise budget conservatively and use observed `429` / retry guidance.
2. Create a **blind BTA research benchmark** with dated source packs and answer keys for real sports questions. Evaluate grounded factual accuracy, contradiction detection, decisive-evidence recall, citation accuracy, cost-free quota feasibility, latency and output stability. Use held-out cases to choose the primary and fallback per task; never assume the largest or fastest model is best.
3. Prefer the highest **eligible** model for that task, not simply the globally highest benchmark score. Skip ineligible models with insufficient context/tool ability, unacceptable privacy terms, exhausted allowance or inaccessible endpoints.
4. When a model fails, stop and persist the verified research state; write a safe provider-independent job checkpoint containing structured sources and resolved facts—not speculative agent prose treated as confirmed. Move to the next eligible model, continue the task, validate the new output and retain the complete audit trail.
5. Add retry ceilings, cooldowns, circuit breakers, idempotent job IDs and per-member fair-use scheduling. Never create unlimited retries, adversarial agent loops, uncontrollable runaway prompts or unexpectedly billable requests.
6. If all models are unavailable, **degrade to deterministic source-gated research** and show `AI_CONTEXT_PENDING` or `AI_CONTEXT_UNAVAILABLE` only when this missing specialist work truly matters; do not block correctly completed deterministic fields or automatically invent an AI critic pass.

### 18.3 Data isolation and independence

Agent work should be performed against **retrieved public sports evidence or permitted cached facts**. Strip member account metadata and tokens. The critic should not simply reword the primary researcher; give it an independent challenge objective, where possible distinct evidence retrieval, and explicit authority to report 'insufficient evidence'. Independent model vendors do not by themselves guarantee independent evidence: record upstream source lineage. No result becomes `OFFICIALLY_VERIFIED` by a model assertion.

### 18.4 AI feature acceptance

Automated tests must demonstrate first-provider quota exhaustion -> second-provider takeover -> exact original leg preserved -> research checkpoint preserved -> valid citations -> source-based decision. The same test must pass when *every* free model is unavailable: core BTA remains usable, but cannot claim the missing AI work was performed.

## 19. Dual grading, forecasts, and no-lookahead model governance (Final Decision 3)

**Two orthogonal outputs are shown for each selection:**

- **BTA research grade:** `TAIG / Elite-Core BTA+ / Strong BTA+ / Lower BTA+-Strong BTA / Standard BTA / Conditional / CUT / PENDING`. Determined solely by the specified complete source-gated methodology, sport-specific stress tests, role/availability, downside exposure and independent audit when required. `PENDING` is not a weak BTA tier or an implied cut.
- **Probability validation state:** `VALIDATED_FOR_MARKET`, `RESEARCH_ONLY`, `MODEL_UNDER_TEST`, `STALE_INPUTS`, `NOT_SUPPORTED`. A numeric pregame/live percentage appears only for a specific exact market, horizon and model whose chronological evaluation demonstrates suitable calibration, predictive utility and reproducibility. Never infer 95% probability from a 'very strong' grade.

For each model version store: allowed features and cutoffs; sports/markets; training/validation/test date ranges; offered-line methodology; eligible sample sizes; held-out metrics (reliability/calibration, Brier or log loss where appropriate, baseline comparison); uncertainty intervals; missing-source behavior; and documented model approval/revocation. Keep pregame and in-game models separate. A ticket joint probability needs validated dependency treatment, not a product of isolated marginal probabilities.

**Acceptance:** no future information, hindsight-selected lines, contaminated training/test split, fabricated confidence or untested percentage. Qualitative certification itself is withheld when any decisive evidence gate is unresolved.

## 20. Operational security, backups, owner control (Final Decision 6)

**Privacy baseline:** private by default with *server-enforced* identity checks on every persistent read/write, shared snapshot and background job; owner privileges are limited and logged. Freeze each shared snapshot or use an explicitly scoped live shared view; no private notes or emails should be exposed in copied slips.

**Backup minimum:** scheduled encrypted durable backup, a separate retention location within compliant free-tier capabilities, monitoring for missed backups, and a **documented successful restoration drill**. Audit schema migrations, transaction consistency and access control after restore. No full public backup in a GitHub repository; test keys/credentials rotation.

**Incident handling:** owner-only dashboard exposes scheduler/AI source health and aggregate errors without disclosing member data. Offer secure revocation of sessions/invites, response to lost access, evidence of unauthorized login attempts, and a way to take a compromised integration offline. Do not promise uninterrupted monitoring or unlimited retention if free providers do not support it.

**A missing viable free email/backup/security stack is a launch blocker**, not a cosmetic 'known issue'.

## 21. Complete QA, private beta and single-launch release contract (Final Decisions 7 and 8)

### 21.1 Mandatory core release gates — ALL must pass

| Gate | Proof required before one integrated launch |
|---|---|
| New independent project | New repository, separate Streamlit deployment, separate secrets and storage, no legacy production dependency; original repo untouched. |
| Three-sport usable data | NBA, NFL and CFB each retrieve authentic, timestamped upcoming games and have a real, functioning evidence-driven core research path for their principal supported markets; exact tested coverage published. |
| BTA methodology | All available original 40-section functional requirements represented in code/tests; original missing verbatim details reconciled before claiming exact fidelity; no automatic grade without applicable required evidence and scripts. |
| My Slip | Real up-to-30-leg cross-sport ticket persistence; browse/paste, separate two-stage audit, Keep/Adjust/Replace/Cut, user-authorized edits, share/copy and historical snapshot protection. |
| Member account and security | Real external invitee can register with working no-cost magic-link delivery; strict per-account authorization; secure sessions; revoked invites/shares blocked; audit controls tested. |
| Background reliability | Jobs durably queue, retry, recover after process/scheduler failures and report actual status; critical scheduled workflows observed operating from the deployed stack within documented limits. |
| Source and prediction integrity | Canonical IDs, timestamps, correct units, citation lineage, conflict handling, no-lookahead testing, documented market-specific gaps; never fabricate percentages or grade. |
| Recoverability | Successful encrypted backup and isolated restore drill with reconciled key data; owner controls and relevant service/incident visibility work. |
| Mobile and desktop usability | Real user flows tested on iOS Safari, Android Chrome and desktop browsers; standard browser usage without download; clean, accessible, responsive layouts. |
| Private beta | At least an owner plus invited testers complete end-to-end scenarios on the deployed new app; no unresolved severity-one security/data-loss/research-integrity defects. |

**Not sufficient for launch:** a screenshot of the UI, synthetic fixture pass counts alone, AI explanations without actual verified source data, a report using a made-up line, or a pipeline that only runs when Streamlit is open.

### 21.2 Permitted, honestly labeled advanced limitations

- **Some live player markets:** may show verified or delayed stats but no continuous prop tracking where the free feed lacks required events; feature marked `UNAVAILABLE` when necessary.
- **Live numerical probabilities:** absent until specific models are validated; qualitative risk and progress continue when supported.
- **Combined parlay hit percentage:** absent unless a held-out validated dependency-aware joint model exists.
- **Current sportsbook alt lines:** manually entered exact line allowed with `MARKET_NOT_VERIFIED` marker, never a false live book quote.
- **Screenshot/OCR import:** optional, disabled if representative free OCR testing fails; browse and paste remain mandatory.
- **AI specialist capacity:** explicit occasional `AI_CONTEXT_PENDING` status during free quota outages; the deterministic research core works regardless.
- **Nonessential advanced markets:** absent until their historical, injury, settlement and source requirements pass tests.

These limitations **cannot** be used as excuses for incomplete core three-sport research, insecure accounts, nonpersistent slips, missing evidence rules or broken background jobs.

### 21.3 Measurable QA evidence to preserve

- Replay historical games **in time order** at actual prediction cutoffs using versioned sources and truly contemporaneous lines where required; compare against obvious baselines and inspect grading errors, calibration and out-of-time sample uncertainty.
- Run live observation windows for each sport/market that claims live support, recording source publish time, fetch time, age and error rate from the actual deployed host.
- Stress a real representative member load and worst-case 30-leg mixed slip without paid-tier activation; document request budgets, missed deadlines, backoffs and recovery.
- Test malicious and accidental cross-member reads, invite replay, expired link, share revocation, session theft protections, backup exposure and unsafe model-output handling.
- Test provider outage/fallback, inconsistent injury reports, mismatched player IDs, changed line, postponed game, tie/push/void, official correction, halftime injury and overtime settlement.
- Beta users must complete a scripted sequence of real sign-up, leg selection, automatic analysis, manual refresh, cross-device return, read-only sharing and postgame history; collect and close blocking usability defects.

**Test-threshold governance:** before performance tests, pre-register specific sample windows, minimum representative test counts, objective critical bug definitions, acceptable feed delays (by provider), forecast metrics and backup restoration objectives; don't choose permissive thresholds after seeing test failures. Some technical pass criteria, such as **zero successful cross-account unauthorized reads** and **zero grades on missing decisive evidence**, are unconditional.

## 22. Owner-facing final system status and capability disclosure

A small owner-only administrative status view will list: deployed app version; active free services and last successful check; provider/model ranking and cooldown status; safe aggregate quotas; current/failed/pending jobs; backup and last restore-test status; recent critical integrity/security events; and the sport/market capability matrix (`supported`, `delayed`, `research only`, `unavailable`). This is not a sixth public navigation destination and does not expose credentials or other members' personal picks.

Each user-facing market report will display: league/game/player; canonical exact market and manually supplied line label; research status/grade; validated probability status; evidence timestamp; independent audit completed/pending; injury/conflict notes; and a leg-appropriate Keep/Adjust/Replace/Cut recommendation, with complete methods inside expandable report detail.

## 23. Final implementation handoff and change-control rule

The approved **final product design and eight final technical decisions are frozen as the build baseline**. Any implementation limitation must be documented in a capability register, evaluated against the strict core release gate and disclosed before calling BTA operational. Provider changes and internal engineering substitutions are permissible if they satisfy the same behavior, security, free-only requirement and tests; they do not silently relax the methodology.

Suggested folder-level architecture for the new repository (illustrative, not existing code):

```text
bta-2.0/
  app/                  # Streamlit UI, authentication and page adapters
  domain/               # Canonical games, selections, markets and immutable snapshots
  data_sources/         # NBA, NFL, CFB and market source adapters
  research/             # Sport-specific evidence pipelines and BTA rules
  agents/               # Specialist task prompts, routing, critics, output validators
  models/               # Versioned forecasts, calibration and replay tests
  jobs/                 # Durable job execution, scheduled scan and recheck policies
  persistence/          # Accounts, slips, versions, admin and backup migrations
  tests/                # Unit, integration, time-split, security, fault injection, UI
  docs/                 # Requirements, capability matrix, provider terms and runbooks
  assets/               # Exact approved BTA logo and interface assets
  .github/workflows/     # Checked-in scheduled/CI workflows; secrets kept out of repo
```

**No existing repository is renamed, modified or copied as the production foundation. No paid service is authorized. No new repository, deployment or verified sports provider is implied by this spec alone.**

## Final product acceptance statement

**BTA 2.0 is one new browser-first Streamlit application for NBA, NFL and college football, under the Belt To Ass brand. It autonomously gathers and verifies source data; performs conservative sport-specific BTA research; assigns qualitative grades separately from validated probabilities; builds, evaluates, improves or cuts tickets without unilateral edits; tracks supported games and outcomes; supports private invited members; and degrades transparently under free-tier limits.**

**BTA never forces a bet and never manufactures certainty. A less crowded slip with defensible evidence is a successful outcome.**

### Final acceptance philosophy

> **BTA should automatically find, verify and stress-test the strongest available opportunities; recommend KEEP, ADJUST, REPLACE or CUT with evidence; and prefer no bet over a bad one. Its greatest asset is trustworthiness, not how many legs it can keep alive.**

**No repository, hosted app, source integration, live model, or login system has been created by this specification.** This is the approved product/build baseline for implementation and testing.
