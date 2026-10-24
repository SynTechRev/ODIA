# Day 04 Mars Checkpoint Summary

**Date**: 2026-10-23
**Traces file**: data/eval/raia_day04_traces.jsonl
**Inference backend used**: [FILL: anthropic claude-3-haiku-20240307 | openai gpt-4o-mini | ollama odia-v2]
**Total queries run**: 5 (one per category)

---

## Halt Distribution

| halt_reason | count |
|---|---|
| verify_passed | [FILL] |
| max_iterations | [FILL] |

---

## Per-Query Summary

| # | category | halt_reason | iterations | final_confidence | citation_validity |
|---|---|---|---|---|---|
| 1 | instrument_type | [FILL] | [FILL] | [FILL] | [FILL] |
| 2 | dollar_range | [FILL] | [FILL] | [FILL] | [FILL] |
| 3 | severity_critical | [FILL] | [FILL] | [FILL] | [FILL] |
| 4 | gap_pattern | [FILL] | [FILL] | [FILL] | [FILL] |
| 5 | combined | [FILL] | [FILL] | [FILL] | [FILL] |

**Mean iterations to halt**: [FILL]
**Latency p50 (sec)**: [FILL]

---

## Watch A: Hybrid Retriever Latency Under Agent Load

Per-query retrieval latencies (from trace cross_reference nodes):

- Query 1 unique_docs: [FILL], passages_retrieved: [FILL]
- Query 2 unique_docs: [FILL], passages_retrieved: [FILL]
- Query 3 unique_docs: [FILL], passages_retrieved: [FILL]
- Query 4 unique_docs: [FILL], passages_retrieved: [FILL]
- Query 5 unique_docs: [FILL], passages_retrieved: [FILL]

**Latency consistent across queries?** [FILL: yes / no; if no, describe pattern]

---

## Watch B: Citation Marker Format Compliance

**Did Claude emit `(doc_id:XXX)` format consistently?** [FILL]

Variants observed (if any):
- [FILL or "none"]

Regex extraction working? [FILL: yes / no]

---

## Watch C: Sub-question Coverage (citation_pool size vs k)

Default k=10 per sub-question. If 2-3 sub-questions, expected citation_pool >= 20-25 with diversity.

| # | sub_questions count | citation_pool size | coverage signal |
|---|---|---|---|
| 1 | [FILL] | [FILL] | [FILL: diverse / overlapping] |
| 2 | [FILL] | [FILL] | [FILL] |
| 3 | [FILL] | [FILL] | [FILL] |
| 4 | [FILL] | [FILL] | [FILL] |
| 5 | [FILL] | [FILL] | [FILL] |

---

## Checkpoint 1: Trace Readability

**Can Mars follow the reasoning chain end-to-end in one trace?** [FILL]

Specific trace reviewed (query #): [FILL]

Issues found:
- [FILL or "none"]

**Action required**: [FILL: none / add pretty_print_trace.py before Day 7]

---

## Checkpoint 2: Failure Mode Taxonomy

Tally across 5 traces:

| failure_mode | count | traces affected |
|---|---|---|
| hallucinated_citations | [FILL] | [FILL] |
| citation_drift (valid but off-topic) | [FILL] | [FILL] |
| poor_sub_question_decomposition | [FILL] | [FILL] |
| inflated_confidence (uniform high) | [FILL] | [FILL] |
| retrieval_misfire (wrong docs) | [FILL] | [FILL] |
| premature_halt | [FILL] | [FILL] |

**Primary failure mode**: [FILL]

**Day 5/6 priority based on tally**: [FILL]

---

## Checkpoint 3: Loop Behavior

For traces that looped (iteration > 1):

**Trace(s) that looped**: [FILL]

For each looped trace -- did iteration 2 sub_questions meaningfully differ from iteration 1?

- Trace [X]: [FILL: yes, diverged on [topic] / no, identical / not applicable]

**Reflection prompt quality**: [FILL: adequate / needs refinement before Day 7]

If refinement needed: specific sub_questions from iteration 1 need to be embedded in the reflection
prompt so the model explicitly avoids repeating them.

---

## Checkpoint 4: Production Path Decision

**Criterion**: 4-5 traces verify_passed with valid citations and high confidence = endpoint
production-ready behind allowlist. 2 or fewer = stays internal through 90-day deepening.

**Count of clean verify_passed halts**: [FILL] / 5

**Decision**: [FILL: open /api/v1/raia/analyze behind allowlist / stays internal through Day 11 guard rails]

---

## Next Steps

**Immediate**:
- [ ] Deploy odia-v2 in Ollama (see memory checklist)
- [ ] Re-run traces with Ollama backend: `python -I scripts/run_raia_day04_traces.py`
  Output: `data/eval/raia_day04_traces_odia_v2.jsonl`
- [ ] Build `learning_log/day04_comparison.md` (Claude vs odia-v2 per-query delta)

**Day 5 prerequisite gates** (from failure mode tally):
- If hallucinated_citations count > 2: tighten deepen prompt to include explicit doc_id list
- If inflated_confidence in all traces: replace self-report with citation_density heuristic
- If loop behavior identical across iterations: embed iteration 1 sub_questions in reflection prompt
- If retrieval_misfire > 1: re-examine HybridRetriever parameter tuning before Day 5

**Day 5 launch**: Document extraction tool bakeoff (pymupdf + pdfplumber). B-6 checkpoint at
end of Day 5 before any pipeline change.
