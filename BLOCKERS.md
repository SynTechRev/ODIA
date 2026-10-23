# BLOCKERS.md -- 10-Day Challenge

Discrepancies between the handoff document and current platform state.
Mars sign-off required on each item before the affected day proceeds.

---

## B-1: Module Path Convention (affects every day)

**Handoff says:** `oraculus/api/`, `oraculus/retrieval/`, `oraculus/agents/`, etc.

**Actual structure:** `src/oraculus_di_auditor/` is the single source package.
New challenge modules are placed there with equivalent subdirectories:

| Handoff path | Actual path |
|---|---|
| `oraculus/api/reasoning_mode.py` | `src/oraculus_di_auditor/interface/reasoning_mode.py` |
| `oraculus/retrieval/hybrid.py` | `src/oraculus_di_auditor/retrieval/hybrid.py` |
| `oraculus/retrieval/colbert_index.py` | `src/oraculus_di_auditor/retrieval/colbert_index.py` |
| `oraculus/agents/raia_v0.py` | `src/oraculus_di_auditor/agents/raia_v0.py` |
| `oraculus/tools/detector_tools.py` | `src/oraculus_di_auditor/tools/detector_tools.py` |
| `oraculus/memory/three_tier.py` | `src/oraculus_di_auditor/memory/three_tier.py` |
| `oraculus/eval/harness.py` | `src/oraculus_di_auditor/eval/harness.py` |

All other paths in the handoff that reference `oraculus/` follow the same mapping.
This convention is already applied to Day 1. **No Mars sign-off needed -- convention is resolved.**

---

## B-2: Platform Corpus Stats (informational)

**Handoff says:** 212,838 findings / 65,108 documents / 17 jurisdictions

**Actual (CLAUDE.md, 2026-10-22):** 271,245 findings / 81,309 documents / 16 jurisdictions

The handoff was written before the City of Fresno NSU ingest (14,409 docs / 64,489 findings)
and TCPD harvest (1,262 docs) completed. The eval harness in Day 10 will use the current figures.
Day 1 query generation should reflect current corpus scale.

**No Mars sign-off needed -- informational update only.**

---

## B-3: odia-v2 Training State (affects Day 1 and Day 10)

**Handoff says:** "odia-v2 QLoRA fine-tune (6,672 examples across Types 1 through 6) now
trained and in validation."

**Actual:** odia-v2 training completed 2026-10-22. 327,717 examples
(56,282 reports + 271,221 finding explanations + 214 adversarial DAN Type 8).
Q4_K_M GGUF deployed in Ollama. Validation conducted via RAG pipeline testing
2026-10-22. Known gap: synthesis QA pairs absent from training data (odia-v3 target).

**Impact:** Day 1 "reasoning mode on vs. off" comparison runs against deployed odia-v2,
not a model in validation. Day 10 evaluation baseline reflects actual deployed model.

**No Mars sign-off needed -- informational update only.**

---

## B-4: Day 1 Gold Reference Answers (blocks Day 1 evaluation)

**Handoff requires:** `data/eval/reasoning_mode_queries.jsonl` -- 20 queries with
Mars-authored gold reference answers covering CPRA, signature patterns, JAG, Carpenter,
cross-jurisdictional, and open analytical questions.

**Current state:** File infrastructure created. Query slots defined. Reference answers
are blank. Day 1 build (reasoning_mode.py scaffold) is complete. Evaluation run against
20 queries is blocked until Mars populates reference answers.

**Mars action required:** Fill in `reference_answer` fields in
`data/eval/reasoning_mode_queries.jsonl` before running
`scripts/eval_reasoning_mode_day01.py`.

---

## B-5: Day 3 Retrieval Decision Checkpoint (blocks Day 4)

**Handoff requires:** Mars sign-off on production retriever selection after Day 3
three-way benchmark before Day 4 wires it into the R.A.I.A. agent.

**Current state:** Days 2 and 3 not yet started. Flagging in advance.

**Mars action required at end of Day 3.**

---

## B-6: Day 5 Document AI Decision Checkpoint (blocks downstream pipeline change)

**Handoff requires:** Mars sign-off on document extraction tool selection after Day 5
bakeoff before any downstream pipeline change.

**Mars action required at end of Day 5.**

---

## B-7: Day 7 Detector Tool-Calling Pattern Checkpoint (blocks Day 9)

**Handoff requires:** Mars sign-off on detector selection pattern after Day 7 before
Day 9 memory wiring.

**Mars action required at end of Day 7.**

---

## B-8: WSL2 Assumption (affects scripts)

**Handoff assumes:** WSL2 Ubuntu 22.04 for bash scripts and model downloads.

**Actual:** Primary dev environment is Windows 11, PowerShell primary, Git Bash available.
The `scripts/verify_no_dashes.sh` script runs via Git Bash (bash scripts/verify_no_dashes.sh).
Python environment uses `.venv\Scripts\` not `.venv/bin/`.
All scripts will be written with Windows compatibility unless explicitly a Vast.ai task.

**No Mars sign-off needed -- convention resolved.**

---

## B-9: `data/eval/` 100-Query Eval Set (affects Day 2 benchmark and Day 10 harness)

**Handoff requires:** 100-query held-out eval set with known-relevant document IDs
for retrieval benchmark (Days 2, 3) and evaluation harness (Day 10).

**Current state:** Directory created. Set not yet built. Needs to be constructed from
existing Mars-reviewed corpus outputs before Day 2 benchmark can run.

**Mars action required before Day 2:** Identify or confirm the 100-query set and
known-relevant doc IDs.

---

## B-10: `data/contra_training_v1.jsonl` Reference

**Handoff references:** `data/contra_training_v1.jsonl` (6,672 examples, 11.6 MB)
as the C.O.N.T.R.A. training dataset for Day 6 preference extraction baseline.

**Actual:** odia-v2 training data is `data/training/odia_v2_combined_327717.jsonl`
(327,717 examples, 694 MB, gitignored). No separate contra_training_v1.jsonl on disk.

**Mars action required for Day 6:** Confirm which dataset to use as preference
extraction baseline. Likely the existing odia-v2 training data; or Mars can provide
the contra_training_v1.jsonl separately.

---

*Last updated: 2026-10-23*
*Updated by: Claude Sonnet 4.6 (session start protocol, branch initialization)*
