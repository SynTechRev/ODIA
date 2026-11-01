# Day 01: Reasoning Foundations (Domain 1)

**Date:** 2026-10-23
**Paper:** DeepSeek-R1 (arxiv 2501.12948) -- Sections 2.3 (GRPO objective) and 3.1 (cold start then RL recipe)
**Build artifact:** `src/oraculus_di_auditor/interface/reasoning_mode.py`

## What I built

Added `reasoning_mode: bool` flag to `RAGQueryRequest` (POST /api/v1/rag/query).
When True, `build_reasoning_prompt()` injects a sub-question decomposition scaffold
into the assembled RAG prompt before the model call. Model output is parsed by
`strip_thinking_tags()` to separate `<thinking>` internals from the final answer.
The scaffold follows the DeepSeek-R1 cold-start chain-of-thought pattern: enumerate
sub-questions, map evidence per sub-question, synthesize, then answer.

Created `scripts/eval_reasoning_mode_day01.py` to run all 20 queries in both modes
and write paired outputs to `data/eval/reasoning_mode_day01_outputs.jsonl`.

## What I measured

Blocked pending Mars-authored gold reference answers in
`data/eval/reasoning_mode_queries.jsonl`. Infrastructure is built; evaluation run
cannot proceed until `reference_answer` fields are populated.

See BLOCKERS.md item B-4.

## What surprised me

The odia-v2 synthesis gap (identified 2026-10-22) is directly relevant here. Because
the model was trained on 271,221 individual explanation examples with zero synthesis
QA pairs, reasoning_mode=True may not produce the expected structured output format.
The scaffold assumes the model can follow multi-step instructions; odia-v2's training
bias toward explanation format could override the scaffold. This makes Day 1 a
diagnostic as much as a capability test: if reasoning_mode=True produces structured
decomposition, the model is scaffold-responsive. If it defaults to explanation format
regardless, that is a confirmed training gap that strengthens the case for odia-v3
synthesis corpus work.

## What I would change

Consider adding `reasoning_output` as a separate field in `RAGQueryResponse` to
surface the `<thinking>` block to the caller without mixing it into the answer text.
Currently the thinking block is stripped silently. For debugging and evaluation, the
caller should be able to see the reasoning trace.

## Mars review notes

[Reserved for Mars annotation.]
