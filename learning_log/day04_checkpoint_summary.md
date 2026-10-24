# Day 04 Mars Checkpoint Summary

**Date**: 2026-10-23
**Traces file**: data/eval/raia_day04_traces.jsonl
**Inference backend used**: ollama odia-v2 (Q4_K_M, 64% CPU / 36% GPU)
**Total queries run**: 5 (one per category)

---

## Halt Distribution

| halt_reason | count |
|---|---|
| verify_passed | 4 |
| max_iterations | 1 |

---

## Per-Query Summary

| # | category | halt_reason | iterations | final_confidence | citation_validity |
|---|---|---|---|---|---|
| 1 | instrument_type | verify_passed | 1 | 0.850 | vacuous (0 citations) |
| 2 | dollar_range | verify_passed | 1 | 0.850 | vacuous (0 citations) |
| 3 | severity_critical | verify_passed | 1 | 0.850 | vacuous (0 citations) |
| 4 | gap_pattern | max_iterations | 3 | 0.500 | 0/2 valid (partial IDs) |
| 5 | combined | verify_passed | 2 | 0.850 | vacuous (0 citations) |

**Mean iterations to halt**: 1.6
**Latency p50 (sec)**: 82.6s

---

## Watch A: Hybrid Retriever Latency Under Agent Load

Per-query retrieval latencies (from trace cross_reference nodes):

- Query 1 unique_docs: 19, passages_retrieved: 19
- Query 2 unique_docs: 20, passages_retrieved: 20
- Query 3 unique_docs: 15, passages_retrieved: 15
- Query 4 unique_docs: 20/10/10, passages_retrieved: 20/10/10 (3 iterations)
- Query 5 unique_docs: 18/10, passages_retrieved: 18/10 (2 iterations)

**Latency consistent across queries?** Yes for single-iteration queries (58-83s).
Multi-iteration queries scale linearly: gap_pattern (3 iter) = 190s, combined (2 iter) = 305s.

---

## Watch B: Citation Marker Format Compliance

**Did odia-v2 emit `(doc_id:XXX)` format consistently?** No.

Variants observed:
- 4/5 queries: zero citations in findings (model did not cite at all)
- gap_pattern iter 1+2: emitted (doc_id:<id>) and (doc_id:42ca9a880818002b...) -- both
  from prompt artifacts: <id> token in rule text and [:16] truncation with ellipsis
- combined iter 0: same two artifact patterns

Root causes identified and fixed in commit 7e5b840:
- <id> token removed from rule text; full example ID used instead
- [:16] truncation removed; ellipsis removed from example

Regex extraction working? Yes -- extracts correctly when format is followed.

---

## Watch C: Sub-question Coverage (citation_pool size vs k)

Default k=10 per sub-question. If 2-3 sub-questions, expected citation_pool >= 20-25 with diversity.

| # | sub_questions count | citation_pool size | coverage signal |
|---|---|---|---|
| 1 | 2 | 19 | diverse (19 unique from 2 sub-Qs) |
| 2 | 2 | 20 | diverse (20 unique from 2 sub-Qs) |
| 3 | 2 | 15 | diverse (15 unique from 2 sub-Qs) |
| 4 | 2/2/2 | 20/10/10 | iter 0 diverse; iters 1-2 collapsed (sub-Qs = placeholder text) |
| 5 | 2/1 | 18/10 | iter 0 diverse; iter 1 collapsed (1 sub-Q echoing prompt) |

---

## Checkpoint 1: Trace Readability

**Can Mars follow the reasoning chain end-to-end in one trace?** Yes -- pretty_print_trace.py
renders each node clearly with iteration tags, passage counts, and confidence values.

Specific trace reviewed (query #): 4 (gap_pattern, max_iterations path -- most complex)

Issues found:
- Sub-questions in loop iterations 1 and 2 degrade to "[sub-question]" placeholders;
  reflection is being consumed but the analyze prompt format guide is being echoed.
- Combined (query 5) iter 1: sub-question became "Explain the following audit finding in
  plain language..." -- model used reflection text as a sub-question.

**Action required**: pretty_print_trace.py already in place. No additional tooling needed before Day 7.

---

## Checkpoint 2: Failure Mode Taxonomy

Tally across 5 traces:

| failure_mode | count | traces affected |
|---|---|---|
| hallucinated_citations | 2 | gap_pattern (iters 1-2), combined (iter 0) |
| citation_drift (valid but off-topic) | 0 | none |
| poor_sub_question_decomposition | 3 | instrument_type (partial), gap_pattern (iters 1-2), combined (iter 1) |
| inflated_confidence (uniform high) | 4 | all verify_passed traces report exactly 0.850 |
| retrieval_misfire (wrong docs) | 0 | none observed |
| premature_halt | 0 | none |

**Primary failure mode**: Inflated/copied confidence (0.850 uniform) and zero citations in
findings. Model passes verify vacuously (no citations = vacuously valid) and reports the
example confidence value rather than a computed one.

**Day 5/6 priority based on tally**:
1. Citation discipline -- model must emit doc_ids in findings (rerun after 7e5b840 fixes)
2. Confidence calibration -- if rerun shows continued uniform reporting, replace
   self-report with citation_density heuristic (valid_citations / retrieved_passages)
3. Sub-question collapse in loop iterations -- reflection prompt needs prior sub-questions
   embedded so model explicitly avoids repeating them

---

## Checkpoint 3: Loop Behavior

For traces that looped (iteration > 1):

**Trace(s) that looped**: gap_pattern (3 iterations), combined (2 iterations)

For each looped trace -- did iteration 2 sub_questions meaningfully differ from iteration 1?

- gap_pattern (q080): No. Iters 1 and 2 both produced "[sub-question]" placeholders.
  Reflection was consumed (verify noted it) but analyze degraded to template echoing.
- combined (q100): Partially. Iter 1 produced one sub-question echoing the reflection
  text rather than a new investigative angle. However deepen on iter 1 produced a clean
  0.850 confidence finding with no invalid citations -- verify_passed.

**Reflection prompt quality**: Needs refinement before Day 7.

Sub-questions from iteration N must be embedded in the reflection block so the model
explicitly avoids repeating them. Current reflection only notes the failure without
showing what was tried.

---

## Checkpoint 4: Production Path Decision

**Criterion**: 4-5 traces verify_passed with valid citations and high confidence = endpoint
production-ready behind allowlist. 2 or fewer = stays internal through 90-day deepening.

**Count of clean verify_passed halts**: 4 / 5

**Caveat**: All 4 verify_passed halts are vacuously valid -- zero citations extracted in
findings, so citation_validity={} which evaluates all_valid=True by the empty-dict rule.
The model is not citing documents, so the citation gate is not actually being exercised.

**Decision**: Stays internal through Day 11 guard rails.

Reasoning: 4/5 verify_passed on the surface looks production-ready, but the underlying
citation discipline is failing (4 traces have zero citations). Opening the endpoint while
the model is not grounding its findings in specific documents would undermine the
accountability purpose of the tool. The citation prompt fixes in commit 7e5b840 need a
rerun to verify before any production-path decision is revisited.

---

## Next Steps

**Immediate**:
- [x] odia-v2 deployed in Ollama (Q4_K_M, commit 7e5b840 fixes applied)
- [ ] Re-run traces after citation prompt fixes:
  `python -I scripts/run_raia_day04_traces.py`
  Output: overwrite `data/eval/raia_day04_traces.jsonl` or write to
  `data/eval/raia_day04_traces_run2.jsonl` for comparison
- [ ] Verify citations appear in findings (Watch B resolved)

**Day 5 prerequisite gates** (from failure mode tally):
- If hallucinated_citations count > 2: tighten deepen prompt to include explicit doc_id list
- If inflated_confidence in all traces: replace self-report with citation_density heuristic
- If loop behavior identical across iterations: embed iteration 1 sub_questions in reflection prompt
- If retrieval_misfire > 1: re-examine HybridRetriever parameter tuning before Day 5

**Day 5 launch**: Document extraction tool bakeoff (pymupdf + pdfplumber). B-6 checkpoint at
end of Day 5 before any pipeline change.
