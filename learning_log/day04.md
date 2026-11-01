# Day 04: R.A.I.A. v0 -- Recursive Analysis Investigative Audit

**Date**: 2026-10-23
**Branch**: learning/10-day-challenge
**Status**: COMPLETE (trace capture pending inference backend -- see Watch 4)

## What Was Built

`src/oraculus_di_auditor/agents/raia_v0.py` - R.A.I.A. LangGraph agent:
- Four-node cycle: analyze -> cross_reference -> deepen -> verify
- Loop-or-halt routing via `_should_continue` conditional edge
- Reflection pattern (Shinn 2023): verify writes reflection on failure,
  analyze consumes it on the next iteration to guide deeper decomposition
- Wired to production Hybrid retriever with use_reranker=False per Day 3 decision

`tests/test_raia_v0.py` - 24 tests, all passing:
- 17 unit tests covering helpers, individual nodes, state schema
- 6 graph integration tests: single cycle, max iteration halt, loop on invalid
  citation, loop on low confidence, trace structure, state schema init
- 1 integration test with real HybridRetriever (requires models/bge-m3 on disk)

`scripts/run_raia_day04_traces.py` - 5-query trace capture script:
- Auto-detects inference backend: ANTHROPIC_API_KEY -> OpenAI -> Ollama/odia-v2
- Selects one query per eval category (instrument_type, dollar_range,
  severity_critical, gap_pattern, combined)
- Writes per-query state + trace to data/eval/raia_day04_traces.jsonl

## ReAct + Reflexion Methodology Mapping

ReAct (Yao 2022) pattern applied:
  Thought (analyze_node) -> Action (cross_reference_node) -> Observation
  (retrieved_passages) -> Thought (deepen_node) -> Action (verify_node) -> ...

Reflexion (Shinn 2023) pattern applied:
  verify_node writes state["reflection"] on citation invalidity or low
  confidence. analyze_node prepends the reflection to the prompt on the next
  iteration, forcing a different sub-question decomposition. This is the
  specific loop-closure that distinguishes R.A.I.A. from single-pass RAG.

## Watch 4: Inference Backend -- No Model Available at Build Time

Ollama has zero models registered. ANTHROPIC_API_KEY and OPENAI_API_KEY are
not set. The agent architecture is complete and 24/24 tests pass with a mock
provider. Trace capture requires Mars to configure one of:
  1. Set ANTHROPIC_API_KEY (run instantly, ~2 min for 5 queries)
  2. Set OPENAI_API_KEY (run instantly, ~2 min for 5 queries)
  3. Deploy odia-v2 in Ollama (see odia-v2 deployment checklist in memory)
     Estimated latency: 2-4 min per query on CPU, 30-60 min for 5 queries

Run traces: `python -I scripts/run_raia_day04_traces.py`

## Halt Logic

verify_node increments state["iteration"] before routing. `_should_continue`
reads iteration and reflection to decide:
- iteration >= max_iterations -> finalize (halt_reason: max_iterations)
- reflection is None (citations valid + confidence met) -> finalize
  (halt_reason: verify_passed)
- else -> loop back to analyze

finalize_node sets halt_reason based on whether reflection is still populated
(max_iterations path) or None (verify_passed path).

## Specific Failure Modes Watched (predicted; trace results TBD)

**Hallucinated citations**: deepen_node cites doc_ids not in retrieved_passages.
The verify_node catches this. The reflection includes the specific invalid IDs.
On loop iteration, the deepen prompt reminder "only cite doc_ids that appear
verbatim" is designed to correct this.

**Confidence miscalibration**: model self-reports high confidence (0.9+) on
every response regardless of actual analysis depth. If this is observed in
traces, the confidence gate is useless. Mitigation: replace with citation-count
heuristic (valid_citations / total_claims) in a Day 11 consolidation item.

**Sub-question collapse**: analyze_node produces sub-questions that are
rephrasings of the original query. cross_reference_node then retrieves the same
docs for each sub-question. Signal: unique_docs in the trace equals k (the
per-sub-question top-k) rather than a multiple of k.

**Reflection not consumed**: second iteration produces identical sub_questions
and analytical_angle as the first. The reflection prompt injection is not
causing the model to diverge. Signal: compare trace[0]["sub_questions"] with
trace[trace.index where node==analyze and iteration==1]["sub_questions"].

## Category Predictions (pre-trace)

- instrument_type: likely strong (queries are lexically direct, retriever finds
  relevant docs, deepen has clear evidence to cite)
- dollar_range: likely moderate (Hybrid dense retriever improves dollar_range
  MRR@10 to 0.829 vs TF-IDF 0.489 per Day 3 benchmark)
- severity_critical: likely strong on retrieval, may struggle on deepen
  (queries are short, lexically exact; model may not generate deep analysis)
- gap_pattern: moderate (gap_pattern queries are structural, model may produce
  generic findings)
- combined: likely strong (analytical queries like "how many unsigned
  instruments" map well to structured analysis)

## Guard Rails Required for Day 5+

1. Citation discipline: the (doc_id:XXX) format must be enforced by prompt
   wording. The deepen prompt includes the reminder. If traces show frequent
   invalid citations, tighten the prompt to include an explicit list of valid
   doc_ids.

2. Confidence calibration: if traces show uniform high confidence, replace
   self-reported confidence with a computed score. Candidate: ratio of cited
   docs to retrieved passages (citation_density = len(citations) / len(passages)).

3. Reflection quality: if loop iterations produce identical decompositions,
   the reflection prompt needs to include the specific previous sub_questions
   so the model can explicitly avoid repeating them.

4. Max iterations guard: already enforced (max_iterations=3 default). The
   graph cannot loop infinitely.

## Day 5 Preview

Document extraction tool bakeoff (marker-pdf replacement per B-11: pymupdf +
pdfplumber). Mars B-6 checkpoint at end of Day 5 before pipeline change.
