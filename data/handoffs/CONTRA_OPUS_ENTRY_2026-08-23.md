# CONTRA OPUS SESSION ENTRY — 2026-08-23

## What to paste at the start of an Opus project thread

---

Continuing C.O.N.T.R.A. (Commercial Obligation & Non-Transparency Risk Analysis) work within ODIA. Full briefing in `CONTRA_OPUS_HANDOFF_2026-08-23.md`. Summary of where we are:

**What CONTRA is**: A 10-detector commercial document analysis framework (L-11 through L-20) that scores consumer contracts on 5 CASI axes (0–20 each, aggregate 0–100) and computes CIFU — Cross-Instrument Foreclosure Union — for multi-entity vendor chains. Built on top of ODIA's infrastructure. Operates against a separate `contra_corpus.db`.

**Corpus state at this handoff**: 311 documents / 7,134 findings / 28 entities. CIFU 90.5 / 100 (Foreclosure Regime) for the Uber Consumer Full Chain (20-entity powered-by network). Zero Foreclosure Regime documents individually — the highest single-instrument score in the corpus is Fullstory at CASI 80.

**What just happened**: The prior Opus assessment identified two critical detector defects — L-13:A (unanchored "we may/can/will" generated 4,090 false findings) and L-17:C (bare "text|image|audio|video" alternatives generated 6,477 false findings). Both were fixed. The corpus was fully rescored (283 documents). Cricket Wireless was purged and re-ingested cleanly. The corpus went from 16,407 findings (56% noise) to 7,134 findings. The 14 false Foreclosure Regime documents dropped to zero. The CIFU corrected from 93.5 to 90.5 — still Foreclosure Regime, now driven by network breadth rather than individual instrument inflation.

**The critical finding that survived the correction**:

No single consumer contract in 311 documents reaches Foreclosure Regime individually. The highest max CASI is Fullstory at 80 (session replay — captures every keystroke, scroll, tap, form entry). The Uber chain's 90.5 CIFU is achieved entirely through cross-instrument compounding across 20 entities:
- 19/20 entities active on data extraction depth
- 14/20 entities active on modification and consent
- 19/20 entities active on procedural adhesion
- 16/20 entities active on remedy foreclosure
- 13/20 entities active on enforcement cost asymmetry

Single-entity CASI cannot detect this. CIFU exists to name the architecture.

**The three questions that make this session time-sensitive**:

1. CIFU v2 design — the current formula uses binary entity depth (present/absent) instead of severity-weighted depth, and a 20-entity denominator instead of the 44 Uber sub-processors actually disclosed. These overclaim precision. The formula needs a redesign before this is used externally.

2. The detector audit identified two additional Watch candidates — L-15:A (`_P_COLLECT` fires on "we use" without data collection context) and L-12:C (`_P_C` has a 300-char DOTALL gap on "claim|suit|action"). Neither is as severe as the fixed defects, but they need corpus-level verification before the next public release.

3. The compliance-vendor paradox — Sprinto (avg 46.5, max 73), Vanta (max 53), and Drata (max 39) are deployed by enterprise clients to audit compliance posture. They hold access to their clients' full data inventories. Their own consumer instruments contain the same arbitration, modification, and extraction provisions they are paid to help clients manage. This is a structural finding — the certifier is non-compliant by the same standard it certifies.

---

## What I need from this session

**Request A — CIFU v2 Full Design Specification**  
The current formula is `CIFU = (breadth_pct × 50) + (depth_pct × 50)`. Design a v2 that addresses:
- Severity-weighted depth (entity CASI axis score / 20, not binary 0/1)
- N_disclosed denominator (44 Uber vendors, not 20 retrieved)
- Geometric mean across axes (eliminates structural 50-point floor)
- Shannon entropy concentration term (penalizes single-entity axis dominance)
Full implementation spec including `compute_cifu.py` function signature changes, band re-calibration, and the Uber chain's expected score under v2. See handoff Section 7 Request A for full requirements.

**Request B — AT&T → Cricket CIFU Chain**  
Both entities are already in the corpus (zero additional retrieval). Define the `att_cricket_telecom` chain as a `_CIFU_CHAINS` dict entry, compute its score using current corpus data, and compare to the Uber chain. This is the cheapest analytical deliverable possible — it requires no new documents. See handoff Section 7 Request B.

**Request C — Remaining Detector Verification Queries**  
For L-15:A and L-12:C (Watch status from handoff Section 4), produce SQL verification queries against `contra_corpus.db` and a verdict: should either be escalated to Priority Fix? See handoff Section 7 Request C.

**Request D — Anti-Pattern Regression Test Suite**  
Design the complete pytest fixture set for all 10 detectors. Minimum: 2 positive + 2 negative fixtures per detector; defect-class negative fixtures for L-13 and L-17. Output format: ready-to-paste pytest parametrize entries. See handoff Section 7 Request D.

**Request E — CCM Metric Design**  
TrustArc is simultaneously Uber's consent management platform, Meta's consent infrastructure vendor, and historically Facebook/Meta's privacy certifier (as TrustE). Design the Certification Capture Metric (CCM) — a formula that quantifies assessor independence loss when a privacy certifier becomes a paid client's infrastructure vendor. Include formula, TrustArc illustrative score, DB schema addition, and CIFU interaction. See handoff Section 7 Request E.

---

## Files attached to this session

- `CONTRA_OPUS_HANDOFF_2026-08-23.md` — full briefing (primary reference)
- `data/cifu_report.json` — current CIFU state (90.5, all axis detail, all 20 member entities)
- Detector source files: `l13_unilateral_modification.py`, `l15_data_retention.py`, `l12_choice_of_law_forum.py`, `l17_ml_ai_training.py` (for Requests C and D)

---

*C.O.N.T.R.A. V1.0 / CASI v1.1 / SynTechRev / MARS — 2026-08-23*
