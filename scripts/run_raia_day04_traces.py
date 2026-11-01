"""Day 04: R.A.I.A. v0 trace capture against 5 real queries.

Selects one query per eval category from data/eval/retrieval_queries_v1.jsonl,
runs each through the R.A.I.A. agent, and writes the full state trace to
data/eval/raia_day04_traces.jsonl.

Inference backend priority:
  1. ANTHROPIC_API_KEY env var -> AnthropicProvider (claude-3-haiku-20240307)
  2. OPENAI_API_KEY env var -> OpenAIProvider (gpt-4o-mini)
  3. Ollama with odia-v2 model registered -> OllamaProvider
  4. None of the above -> exits with instructions

Usage:
    python -I scripts/run_raia_day04_traces.py
    python -I scripts/run_raia_day04_traces.py --max-iterations 2
    python -I scripts/run_raia_day04_traces.py --provider anthropic
    python -I scripts/run_raia_day04_traces.py --provider openai
    python -I scripts/run_raia_day04_traces.py --provider ollama --model odia-v2
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DOCS_PATH = Path("data/eval/fresno_signature_1k.jsonl")
QUERIES_PATH = Path("data/eval/retrieval_queries_v1.jsonl")
OUTPUT_PATH = Path("data/eval/raia_day04_traces.jsonl")
MODEL_DIR = Path("models")

TRACE_CATEGORIES = [
    "instrument_type",
    "dollar_range",
    "severity_critical",
    "gap_pattern",
    "combined",
]


def load_docs() -> list[dict]:
    docs = []
    with open(DOCS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def select_queries(n_per_category: int = 1) -> list[dict]:
    queries_by_cat: dict[str, list[dict]] = {}
    with open(QUERIES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                q = json.loads(line)
                queries_by_cat.setdefault(q["category"], []).append(q)
    selected = []
    for cat in TRACE_CATEGORIES:
        cat_queries = queries_by_cat.get(cat, [])
        if not cat_queries:
            logger.warning("No queries for category %s", cat)
            continue
        # Pick the most analytically interesting: last one in each category
        # (combined queries tend to be more analytical than the first entries)
        selected.extend(cat_queries[-n_per_category:])
    return selected


def _detect_provider(
    provider_override: str | None,
    model_override: str | None,
):
    from oraculus_di_auditor.llm_providers import (
        AnthropicProvider,
        OllamaProvider,
        OpenAIProvider,
        get_provider,
    )

    if provider_override:
        kwargs = {}
        if provider_override == "ollama" and model_override:
            kwargs["model"] = model_override
        elif provider_override == "ollama":
            kwargs["model"] = "odia-v2"
        p = get_provider(provider_override, **kwargs)
        if not p.is_available():
            logger.error(
                "Provider %s requested but not available. "
                "Check API key or Ollama service.",
                provider_override,
            )
            sys.exit(1)
        logger.info("Using provider: %s", provider_override)
        return p

    import os

    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("Auto-detected: AnthropicProvider (claude-3-haiku-20240307)")
        return AnthropicProvider(model="claude-3-haiku-20240307")

    if os.getenv("OPENAI_API_KEY"):
        logger.info("Auto-detected: OpenAIProvider (gpt-4o-mini)")
        return OpenAIProvider(model="gpt-4o-mini")

    ollama = OllamaProvider(model=model_override or "odia-v2")
    if ollama.is_available():
        import requests

        resp = requests.get("http://localhost:11434/api/tags", timeout=3)
        registered = [m["name"] for m in resp.json().get("models", [])]
        target = model_override or "odia-v2"
        if any(target in name for name in registered):
            logger.info("Auto-detected: OllamaProvider (model=%s)", target)
            return ollama
        logger.warning(
            "Ollama is running but model '%s' is not registered. "
            "Registered models: %s",
            target,
            registered,
        )

    logger.error(
        "No inference backend available.\n"
        "Options:\n"
        "  1. Set ANTHROPIC_API_KEY and re-run.\n"
        "  2. Set OPENAI_API_KEY and re-run.\n"
        "  3. Deploy odia-v2 in Ollama:\n"
        "       ollama pull llama3.1   (or place GGUF in D:\\ODIA\\models\\)\n"
        "       ollama create odia-v2 -f Modelfile\n"
        "  4. Pass --provider openai|anthropic|ollama explicitly."
    )
    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="R.A.I.A. Day 04 trace capture")
    parser.add_argument("--max-iterations", type=int, default=3, dest="max_iterations")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.75,
        dest="confidence_threshold",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Force provider: anthropic | openai | ollama",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model name override (for Ollama provider)",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="Retrieval depth per sub-question",
    )
    args = parser.parse_args()

    provider = _detect_provider(args.provider, args.model)

    logger.info("Loading %s", DOCS_PATH)
    docs = load_docs()
    corpus_ids = {d["document_id"] for d in docs}
    logger.info("Corpus: %d docs", len(docs))

    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    logger.info("Building Hybrid index (reranker=False)")
    retriever = HybridRetriever(model_dir=MODEL_DIR, use_reranker=False)
    t_idx = time.perf_counter()
    retriever.index(docs)
    logger.info("Index built in %.1fs", time.perf_counter() - t_idx)

    queries = select_queries(n_per_category=1)
    logger.info(
        "Selected %d queries across %d categories", len(queries), len(TRACE_CATEGORIES)
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    halt_counts: dict[str, int] = {}
    iteration_counts: list[int] = []
    latencies: list[float] = []

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_fh:
        for i, q in enumerate(queries, 1):
            logger.info(
                "[%d/%d] category=%s query=%r",
                i,
                len(queries),
                q["category"],
                q["query"],
            )
            from oraculus_di_auditor.agents.raia_v0 import run_raia

            t0 = time.perf_counter()
            try:
                state = run_raia(
                    query=q["query"],
                    retriever=retriever,
                    provider=provider,
                    corpus_ids=corpus_ids,
                    max_iterations=args.max_iterations,
                    confidence_threshold=args.confidence_threshold,
                )
            except Exception as exc:
                logger.error("Query %d failed: %s", i, exc)
                continue
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            halt_counts[state["halt_reason"]] = (
                halt_counts.get(state["halt_reason"], 0) + 1
            )
            iteration_counts.append(state["iteration"])
            logger.info(
                "  halt=%s iterations=%d confidence=%.2f latency=%.1fs",
                state["halt_reason"],
                state["iteration"],
                state["confidence"],
                elapsed,
            )

            record = {
                "run_date": datetime.now(UTC).isoformat(),
                "query_id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "halt_reason": state["halt_reason"],
                "iterations": state["iteration"],
                "final_confidence": state["confidence"],
                "citation_validity": state["citation_validity"],
                "final_answer": state["final_answer"],
                "trace": state["trace"],
                "latency_sec": round(elapsed, 2),
            }
            out_fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    if latencies:
        import statistics

        logger.info("--- Summary ---")
        logger.info("Halt distribution: %s", halt_counts)
        logger.info(
            "Mean iterations: %.1f",
            sum(iteration_counts) / len(iteration_counts),
        )
        logger.info(
            "Latency: mean=%.1fs p50=%.1fs",
            sum(latencies) / len(latencies),
            statistics.median(latencies),
        )
        logger.info("Traces written to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
