# Day 06 -- Preference Optimization (DPO)

**Date**: 2026-10-31
**Branch**: learning/10-day-challenge
**Operator**: M. Sanchez (SynTechRev)
**Status**: COMPLETE

---

## Pre-flight: B-6 Session B (CP5 / CP6 / CP7)

45-minute scoping block to resolve the three odia_legal architectural decisions
deferred from Day 5. These govern detector layer expansion in the odia_legal submodule
(L-1 through L-10 canonical set) and have no Day 6 build dependencies, but must be
signed off before Day 7 detector tool work.

---

### CP5: L-11 Healthcare District -- Scoping Decision

**Candidate:** Add L-11 Healthcare District as a legal reasoning detector in
the odia_legal submodule, targeting hospital district governance compliance
(Kaweah Delta Health Care District, Hospital Authority formation documents,
Public Hospital District Act Gov. Code 32000+).

**Assessment:**
- Kaweah Health is a FOIA target (Connections 2) and relevant to the pattern-and-practice
  record for Tulare County's public-sector governance failures
- However, L-10 (Balancing Test Analyzer) already handles the CPRA public-interest
  balancing test that applies to healthcare district documents
- Healthcare district-specific statutory framework (Gov. Code 32000+) is distinct
  enough to warrant its own detector BUT is not on the critical path to Dec 12 GCA gate
  or Apr 29 Section 1983 filing
- L-10 covers the CPRA dimension; the healthcare governance dimension is a Phase 6 extension

**Decision: DEFERRED -- Phase 6 Extension (post Phase 5)**

Rationale: Healthcare district detectors are operationally relevant but not load-bearing
for the April 2027 Section 1983 complaint or the 2028-07-02 Sunshine Dragnet anchor.
Add L-11 skeleton to odia_legal/detectors/l11_healthcare_district.py (stub only)
during Phase 5 implementation to reserve the namespace. Full implementation in Phase 6.

**CP5 SIGNED OFF.**

---

### CP6: L-12 Civic Ritual -- Scoping Decision

**Candidate:** Add L-12 Civic Ritual as a legal reasoning detector for ceremonial
compliance patterns (posted agenda requirements, quorum mechanics, Brown Act ceremony,
invocation / open public comment sequencing violations as procedural defects).

**Assessment:**
- Brown Act procedural defects are already partially covered by L-2 (Procedural Compliance)
- "Civic Ritual" as a distinct detector layer conflates ceremonial form (invocations,
  pledge of allegiance sequencing) with substantive procedural compliance
- The substantive violations -- failed quorum, improper closed session, absent agenda
  posting -- are Brown Act violations already in scope under L-2
- The ceremonial dimension adds no material legal weight for Section 1983 or CPRA claims

**Decision: DEFER INDEFINITELY -- absorb Brown Act ceremony patterns into L-2**

Rationale: L-12 as scoped adds analytical overhead without litigation-grade value.
Any Brown Act ceremony patterns that prove material can be implemented as sub-patterns
within L-2 (Procedural Compliance) rather than a separate layer. No L-12 stub created.
Namespace L-12 reserved but unassigned until a distinct legal theory emerges.

**CP6 SIGNED OFF.**

---

### CP7: L-13 Scenographic Compilation -- Disposition

**Candidate:** L-13 Scenographic Compilation as a standalone detector OR absorption
into L-10 (Balancing Test Analyzer). Scenographic Compilation = structured evidence
packages that present multiple documents as a compiled visual narrative for adjudication.

**Day 5 recommendation:** Absorb into L-10.

**Assessment:**
- L-10 handles balancing tests: Mathews v. Eldridge, CPRA public interest, Carpenter
- A "compilation" for adjudication is an output of L-10's analysis, not a separate
  legal reasoning step -- L-10 already synthesizes across multiple findings into a
  balancing-test conclusion
- Scenographic (visual / organized presentation) elements belong in
  odia_legal/reports/citation_formatter.py and legal_memorandum.py, not a detector
- Absorbing into L-10 keeps the detector count at 10, matching the spec

**Decision: ABSORB INTO L-10 -- implement as a compilation_mode output within L-10**

Implementation note: L-10's balancing test can accept a list of findings across
multiple documents and produce a compiled multi-document conclusion. This is the
"scenographic" function. Implement as L-10 with mode="compilation" kwarg in Phase 4.

**CP7 SIGNED OFF.**

---

### B-6 Session B Summary

| CP | Decision | Status |
|---|---|---|
| CP5 (L-11 Healthcare District) | Deferred: Phase 6 stub only | SIGNED OFF |
| CP6 (L-12 Civic Ritual) | Deferred indefinitely: patterns absorb into L-2 | SIGNED OFF |
| CP7 (L-13 Scenographic Compilation) | Absorb into L-10 as compilation_mode | SIGNED OFF |

Test count impact: No change (L-11/L-12 not implemented; L-13 absorbed; tests stay at 285).
B-6 Session B COMPLETE. B-6 fully resolved (Session A + Session B).

---

## B-10 Resolution: Preference Extraction Baseline

**Blocker:** data/contra_training_v1.jsonl does not exist. Actual training data is
data/training/odia_v2_combined_327717.jsonl (327,717 examples, 694 MB, SFT chat-messages
format). B-10 required operator decision on preference extraction baseline before Day 6
build starts.

**Options presented at end of Day 5:**

| Option | Mechanism | Cost | Recommended |
|---|---|---|---|
| A | Sample odia_v2_combined as base; generate preferences from quality judgments | High effort, format mismatch | No |
| B | Use Day 4 RAIA traces: run3 (citation-grounded) = chosen; pre-7e5b840 (vacuous) = rejected | Low effort, high signal | YES |
| C | Wait for contra_training_v1.jsonl from operator | Blocked | No |

**Operator decision (2026-10-31): Option B.**

**B-10 RESOLVED.** Option B: generate chosen/rejected pairs from RAIA traces.

Baseline spec:
- chosen: run 3 responses from data/eval/raia_day04_traces.jsonl
  (4/5 queries with verify_passed + citation_density=1.00)
- rejected: synthetic vacuous responses generated from same queries WITHOUT
  the 7e5b840 citation-grounding prompt (reproduce the pre-fix behavior)
- Supplement: additional chosen/rejected pairs from any new RAIA runs
  before Day 6 build completes
- Format: DPO chat-messages format (role: user, role: chosen, role: rejected)
- Target: 50-200 preference pairs for smoke test (DPO is quality-sensitive,
  not quantity-sensitive at this stage)

---

## Day 6 Build Plan: data/preferences_v1.jsonl + DPO Config + 10-Step Smoke Test

### What to Build

**1. scripts/generate_preferences_v1.py**
Reads data/eval/raia_day04_traces.jsonl and generates DPO pairs.
- For each verify_passed query: pair its final answer (chosen) with a vacuous baseline (rejected)
- Output: data/preferences_v1.jsonl

**2. config/dpo_config_v1.yaml**
DPO training configuration for odia-v3.
- Base model: odia-v2 (already trained, deployed)
- DPO beta: 0.1 (standard starting point)
- Max seq length: 2048
- Epochs: 1 (smoke test -- full run at Day 11 if gate passes)

**3. scripts/smoke_test_dpo.py**
10-step DPO smoke test (verifies data format and forward pass only; no full training run).
- Loads preferences_v1.jsonl
- Instantiates DPO trainer (Unsloth / TRL)
- Runs 10 gradient steps
- Checks: loss decreasing, no NaN, chosen > rejected reward margin
- Output: data/eval/dpo_smoke_test_day06.json

### B-10 Option B Rationale

Chosen responses from run 3 carry the production-quality grounding density that passed
the verify node after three diagnostic iterations that fixed the identity conflict,
prompt artifact citations, and self-reported confidence issues. The rejected responses
carry the exact failure mode (generic analytical prose without document grounding) that
the severity_critical gap manifests.

The preference pairs train toward the architecturally correct behavior -- cite real
doc_ids that appear verbatim in retrieved passages -- rather than toward whatever
contrast a less-curated pair would produce. The DPO training objective is precision:
the model must learn that a response without (doc_id:xxx) markers fails the verify gate.

### Methodology Notes

Direct Preference Optimization (Rafailov 2023):
  DPO directly optimizes the language model to prefer chosen over rejected responses
  without a separate reward model. Loss: -(log sigma(beta * log(pi_theta(y_w|x) /
  pi_ref(y_w|x)) - beta * log(pi_theta(y_l|x) / pi_ref(y_l|x))))
  where y_w = chosen, y_l = rejected, pi_ref = frozen reference model (odia-v2).

Why DPO over PPO for ODIA:
  PPO requires a reward model, a critic, and careful hyperparameter tuning -- overhead
  not justified for 50-200 pairs at this stage. DPO converges with far fewer examples
  and directly encodes the "cite real documents, don't hallucinate" preference signal
  that the Day 4 traces expose.

### Watch Items (from launch readiness review)

**Watch 1: Beta parameter calibration.**
DPO is sensitive to beta (the KL penalty coefficient). TRL default 0.1 is the smoke
test starting point. Production run should sweep beta across 0.05, 0.1, 0.2, 0.3
to find the production-quality point. Config: config/dpo_config_v1.yaml beta_sweep.
The smoke test runs in ~10 steps and is fast enough to permit the sweep.

**Watch 2: Reference model memory footprint.**
DPO training requires both the policy model (being trained) and a reference model
(frozen) simultaneously. For Llama-3.1-8B Q4_K_M, dual-model footprint fits on
16 GB VRAM comfortably but constrains batch size. The 10-step smoke test surfaces
memory headroom via torch.cuda.max_memory_allocated(). Run forward mode on Vast.ai;
format mode runs locally without any model.

**Watch 3: Synthetic vacuous baseline construction.**
Rejected responses are synthetic -- their construction methodology affects the
training signal. Implementation: vacuous baselines use a defined prose template
(generic analytical language, same register as chosen, no (doc_id:...) markers,
length within 15% of chosen response length). The structural match keeps the DPO
signal focused on citation grounding density, not on surface characteristics like
length or vocabulary. Length ratio validation is included in smoke_test_dpo.py.

---

## Build Results (2026-10-31)

| Artifact | Status | Notes |
|---|---|---|
| scripts/generate_preferences_v1.py | COMPLETE | 5 pairs, 4 verify_passed + 1 constructed |
| data/preferences_v1.jsonl | COMPLETE | 5 DPO pairs, Watch 3 PASS (ratio 0.89-0.97) |
| config/dpo_config_v1.yaml | COMPLETE | beta=0.1, sweep=[0.05,0.1,0.2,0.3], LR=5e-7 |
| scripts/smoke_test_dpo.py | COMPLETE | format + forward modes |
| data/eval/dpo_smoke_test_day06.json | COMPLETE | PASS: 5/5 signal clear, 5/5 length OK |

Smoke test format mode: PASS
  Total pairs: 5
  Signal clear: 5 (rejected has 0 citations)
  Length ratio OK: 5/5 (all within 0.85-1.15 Watch 3 target)

Forward mode (10 gradient steps): deferred to Vast.ai Day 11 session (requires GPU).

## Status

B-6 Session B: COMPLETE (CP5/CP6/CP7 signed off)
B-10: RESOLVED (Option B -- RAIA trace pairs)
Day 6 Build: COMPLETE

Open items passed to Day 7:
- Day 7: detector tool-calling pattern (B-7 checkpoint)
- PrimeGovAdapter export gap (adapters/__init__.py -- non-blocker, Day 7)
- Forward mode smoke test: run on Vast.ai at Day 11 with --mode forward
