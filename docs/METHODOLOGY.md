# BTA 40-section methodology — implementation crosswalk

The exact complete original 1–40 text is in the conversation that authorized this build, while `FINAL_MASTER_SPECIFICATION.md` preserves the final approved technical build contract. Both are normative. This table identifies what this delivery encodes and what is still blocked by evidence availability; it does not misrepresent full 40/40 completion.

| Sections | Code / implementation | Current evidence completeness |
|---|---|---|
| 1–4 Objective, tiers, verify, statistical audit | `bta/domain.py`, `bta/research/engine.py`, `bta/sources/espn.py` | Partial; official status and adjusted efficiencies missing |
| 5–8 Five scripts, CFB ML, NFL props, failure modes | `domain.scripts_for`, `engine.script_audit` | Script frameworks exact for NFL/CFB; real verdicts NOT_ASSESSED |
| 9–12 Odds, parlay, live, final reports | `domain.implied_probability`, `engine.assess_ticket`, `research/live.py`, UI | Partial; value, calibrated probability, official settlement unavailable |
| 13–18 batch-ledger, QC, hierarchy and ethics | Per-ticket unique leg IDs/versioning; grade gate and tests | Full large-slate ledger / audit history not complete |
| 19–20 Sport-specific scripts and strict WORSE | `scripts_for`, `admissible_grade` | Offline-tested; live script source not available |
| 21–23 3/3, cushion, failures | `compute_history`, report details | Numeric checks implemented for supported records; contextual/structural audits missing |
| 24–26 Opponent-adjusted, reverse, adversity | Audit blockers and missing-data labels | Not enough source evidence for qualification |
| 27 tiers and subtiers | Grade gate TAIG/BTA+/BTA/CONDITIONAL/CUT; PENDING separate | Subtier UI incomplete, no actual certification |
| 28 contract direction | `selection_hit`, selection exact semantics, quick add | Settlement provider verification unavailable |
| 29–30 TDs and quarter markets | Market choices with research blocked | Specialist history and reliable settlement not implemented |
| 31–32 Correlation and qualified vs ticket | `overlaps`, `assess_ticket`, user-approved edits | Basic shared risk only; no joint probabilities |
| 33–35 Platform specificity, critic, exact N/N | Selection metadata, descriptive samples, optional AI critique | True independent source-based second pass not complete |
| 36–40 CFB ledger, missing data, final audit and philosophy | Source FBS-only, strict conservative `PENDING VERIFICATION`, capability documentation | Large-slate ledger and independently certified all-market scoring incomplete |

**BTA numeric forecasts must come from independently calibrated models**, not from a mapping from qualitative tier to percent. Extreme TAIG label is intentionally impossible while important evidence gates remain unverified.
