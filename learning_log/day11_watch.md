# Day 11 -- Vast.ai Consolidation Session Watch Items

**Date prepared**: 2026-10-31
**Source**: B-10 Mars sign-off memo (Day 10 review)
**Branch**: learning/10-day-challenge

---

## Five Phases (in order)

1. **SSH key upload** -- operator prerequisite before instance launch
2. **ColPali + Nougat** -- hardware-gated evaluations deferred from Day 5 (B-6 CP2)
3. **odia-v3 DPO training** -- Day 6 preference pairs (Option B: run3 chosen, synthetic
   vacuous rejected); target: iteration_efficiency gate PASS
4. **Post-DPO harness re-run** -- `scripts/run_eval_harness.py` against 100-query eval
   set; all gates must PASS for consolidation PR authorization
5. **Consolidation PR** -- merge `learning/10-day-challenge` to main; absorbs all 10 days

---

## Watch 1: Post-DPO iteration_efficiency (decisive diagnostic)

**Signal to watch**: Does iteration_efficiency move from 0.333 to >= 0.40 after odia-v3?

- **If PASS**: capability advance confirmed; odia-v3 training generalizes from the 5 DPO
  pairs. Proceed to consolidation PR.
- **If FAIL**: preference pair construction methodology needs review before re-run.
  Budget 1 additional training iteration. Items to check:
  - Synthetic vacuous baseline construction (are rejected traces truly low-quality?)
  - Beta parameter calibration (current: default; may need tightening)
  - Training data volume (5 pairs is minimal; may need Day 6 Session B extension)

---

## Watch 2: ColPali signature-page precision at k=5 (second decisive diagnostic)

**Signal to watch**: What is ColPali precision@5 on signature detection?

| Range | Interpretation | Action |
|---|---|---|
| >= 0.80 | Production integration confirmed | Wire ColPali as default extractor for signature-bearing docs |
| 0.50 -- 0.80 | Experimental | Open design conversation on hybrid ColPali + pymupdf approach |
| < 0.50 | Not production-ready | Keep pymupdf as default; ColPali to watchlist |

**Why it matters**: The $33.6B Fresno signature exposure finding relies on signature
detection accuracy at scale. ColPali precision on this use case determines whether the
Day 5 pymupdf-wins decision holds or whether the pipeline adds a ColPali layer for
signature-bearing documents specifically.

---

## Watch 3: Consolidation PR review scope

**Expected PR scope**: ~12 new files, ~30 modified files, ~150-200 new tests,
10 day-logs, CLAUDE.md and BLOCKERS.md updates, full branch history.

**Operator note from B-10**: Review will likely take 60-90 minutes. Schedule for a
dedicated focus block. Integration issues missed in a quick review carry forward to
production.

**PR merge gate**: post-DPO harness PASS verdict required before authorization.

---

## Open Items Carried from Days 9-10

From Day 9:
- Store legal_findings to archival_entries after each RAIA cycle (currently only in
  episodic trace_json; archival storage would enable cross-cycle finding reconciliation)
- Wire memory.compose() into raia_v0.py deepen_node prompt (currently injected keys
  are available in state but not yet used by the deepen_node prompt template)

From Day 10:
- OllamaJudge rubric prompt review before 100-query eval set run (current prompt was
  designed for HeuristicJudge parity; odia-v3 may require domain-specific tuning to
  distinguish generic analysis from grounded citation-based analysis)

---

## Day 11 Independence Confirmation

Per B-10 sign-off: Day 11 scope does not include:
- L-11 Healthcare District detector (deferred Phase 6, B-6 CP5)
- L-12 Civic Ritual detector (deferred indefinitely, B-6 CP6)
- L-13 Scenographic Compilation detector (absorbed into L-10, B-6 CP7)
- Detector wiring architecture decisions (answered in Day 9 EpisodicMemory)
