#!/usr/bin/env python3
"""B-14: Generate post-DPO RAIA traces with odia-v3 for eval harness comparison.

Runs the same 5-query set used for the Day 10 baseline scorecard
(data/eval/raia_day04_traces.jsonl) through the RAIA agent using odia-v3,
then saves results to data/eval/raia_day11_traces.jsonl.

After this script completes, run the eval harness to produce the Day 11
post-DPO scorecard and confirm iteration_efficiency >= 0.40:

  python -I scripts/generate_raia_traces.py
  python -I scripts/run_eval_harness.py \\
      --traces data/eval/raia_day11_traces.jsonl \\
      --out data/eval/scorecard_day11.json

The decisive signal: q060 (severity_critical) should shift from
halt=max_iterations (iters=3) to halt=verify_passed (iters=1 or 2)
after DPO on citation-positive preference pairs. This is the training
distribution shift the Day 11 DPO targeted.

Usage:
  python -I scripts/generate_raia_traces.py
  python -I scripts/generate_raia_traces.py --model odia-v3
  python -I scripts/generate_raia_traces.py --model odia-v2  # baseline re-run
  python -I scripts/generate_raia_traces.py --max-iterations 5
  python -I scripts/generate_raia_traces.py --out data/eval/raia_custom.jsonl
"""
import argparse
import json
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oraculus_di_auditor.agents.raia_v0 import run_raia
from oraculus_di_auditor.llm_providers import OllamaProvider

# Exact query set from raia_day04_traces.jsonl.
# Re-running these queries (same IDs, same category labels) allows the
# eval harness to produce a directly comparable scorecard to Day 10 baseline.
EVAL_QUERIES = [
    {
        "query_id": "q020",
        "category": "instrument_type",
        "query": "fiscal agreement with signature compliance gap",
    },
    {
        "query_id": "q040",
        "category": "dollar_range",
        "query": "unsigned agreement large dollar amount signature finding",
    },
    {
        "query_id": "q060",
        "category": "severity_critical",
        "query": "critical unsigned agreement instrument",
    },
    {
        "query_id": "q080",
        "category": "gap_pattern",
        "query": "signature gap pattern instrument finding 10",
    },
    {
        "query_id": "q100",
        "category": "combined",
        "query": "city clerk compliance unsigned instrument review",
    },
]

DB_PATHS = [
    Path("oraculus_audit.db"),
    Path.home() / "AppData" / "Roaming" / "odia-desktop" / "oraculus_audit.db",
    Path.home() / "oraculus_audit.db",
]

VECTOR_PATHS = [
    Path("data") / "vectors",
    Path.home() / "AppData" / "Roaming" / "ODIA" / "data" / "vectors",
]

HYBRID_INDEX_PATHS = [
    Path("data") / "vectors" / "hybrid_index",
    Path.home() / "AppData" / "Roaming" / "ODIA" / "data" / "vectors" / "hybrid_index",
]


def _find_db() -> Path | None:
    for p in DB_PATHS:
        if p.exists():
            return p
    return None


def _find_vectors() -> Path | None:
    for p in VECTOR_PATHS:
        if (p / "collection_vocab.pkl").exists():
            return p
    return None


def _find_hybrid_index() -> Path | None:
    for p in HYBRID_INDEX_PATHS:
        if (p / "dense_matrix.npy").exists():
            return p
    return None


def _load_corpus_ids(db_path: Path) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT document_id FROM documents").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


class _TFIDFRetrieverShim:
    """TF-IDF shim for RAIA queries when HybridRetriever index is not yet built.

    Used until B-13 (build_hybrid_index.py) completes and produces
    data/vectors/hybrid_index/dense_matrix.npy.
    """

    def __init__(self, vectors_path: Path) -> None:
        import pickle

        from sklearn.feature_extraction.text import TfidfVectorizer

        with open(vectors_path / "collection_vocab.pkl", "rb") as fh:
            vocab_data = pickle.load(fh)
        self._vectorizer = TfidfVectorizer(
            vocabulary=vocab_data["vocabulary"],
            norm=vocab_data["norm"],
            lowercase=True,
            stop_words="english",
        )
        self._vectorizer.fit(["x"])
        self._vectorizer._tfidf.idf_ = __import__("numpy").array(
            vocab_data["idf"], dtype=__import__("numpy").float64
        )
        self._vectors = (
            __import__("numpy")
            .load(vectors_path / "collection_vectors.npy")
            .astype(__import__("numpy").float32)
        )
        raw_meta = __import__("numpy").load(
            vectors_path / "collection_metadata.npy", allow_pickle=True
        )
        self._metadata: list = raw_meta.tolist()

    def query(self, question: str, top_k: int = 15) -> list[dict]:
        import numpy as np

        q_vec = self._vectorizer.transform([question]).toarray().astype(np.float32)[0]
        norm = np.linalg.norm(q_vec)
        if norm > 0:
            q_vec = q_vec / norm
        scores = self._vectors @ q_vec
        top_idx = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_idx:
            meta = self._metadata[idx] if idx < len(self._metadata) else {}
            if not isinstance(meta, dict):
                meta = {}
            results.append(
                {
                    "document_id": meta.get("document_id", meta.get("id", "")),
                    "score": float(scores[idx]),
                    "title": meta.get("title", ""),
                    "findings": meta.get("findings", []),
                }
            )
        return results


def _build_hybrid_retriever(model_dir: Path, index_path: Path) -> object:
    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    r = HybridRetriever(model_dir=model_dir, use_reranker=False)
    r.load(index_path)
    return r


def _run_query(
    query_id: str,
    category: str,
    query: str,
    retriever: object,
    provider: OllamaProvider,
    corpus_ids: set[str],
    max_iterations: int,
    confidence_threshold: float,
) -> dict:
    ts_start = datetime.now(UTC)
    t0 = time.monotonic()
    try:
        state = run_raia(
            query=query,
            retriever=retriever,
            provider=provider,
            corpus_ids=corpus_ids,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold,
        )
        return {
            "run_date": ts_start.isoformat(),
            "query_id": query_id,
            "category": category,
            "query": query,
            "halt_reason": state.get("halt_reason", ""),
            "iterations": state.get("iteration", 0),
            "final_confidence": state.get("confidence", 0.0),
            "citation_validity": state.get("citation_validity", {}),
            "final_answer": state.get("final_answer", ""),
            "trace": state.get("trace", []),
            "latency_sec": round(time.monotonic() - t0, 2),
            "error": None,
        }
    except Exception as exc:
        return {
            "run_date": ts_start.isoformat(),
            "query_id": query_id,
            "category": category,
            "query": query,
            "halt_reason": "error",
            "iterations": 0,
            "final_confidence": 0.0,
            "citation_validity": {},
            "final_answer": "",
            "trace": [],
            "latency_sec": round(time.monotonic() - t0, 2),
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="B-14: Generate post-DPO RAIA traces for eval harness"
    )
    parser.add_argument(
        "--model",
        default="odia-v3",
        help="Ollama model to use (default: odia-v3)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/eval/raia_day11_traces.jsonl"),
        help="Output JSONL path",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.75,
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models"),
        help="Model directory for HybridRetriever (used if hybrid index exists)",
    )
    args = parser.parse_args()

    db_path = _find_db()
    if db_path is None:
        print(
            "ERROR: oraculus_audit.db not found. Checked:\n"
            + "\n".join(f"  {p}" for p in DB_PATHS),
            file=sys.stderr,
        )
        return 1

    vectors_path = _find_vectors()
    if vectors_path is None:
        print(
            "ERROR: TF-IDF vector index not found (collection_vocab.pkl missing).",
            file=sys.stderr,
        )
        return 1

    provider = OllamaProvider(model=args.model)
    if not provider.is_available():
        print(
            f"ERROR: Ollama not reachable. Is Ollama running? Is {args.model} registered?",
            file=sys.stderr,
        )
        return 1

    hybrid_index_path = _find_hybrid_index()
    if hybrid_index_path:
        print(f"Using HybridRetriever index: {hybrid_index_path}")
        retriever = _build_hybrid_retriever(args.model_dir, hybrid_index_path)
        retriever_label = "hybrid"
    else:
        print("HybridRetriever index not found (B-13 not yet run) -- using TF-IDF shim")
        retriever = _TFIDFRetrieverShim(vectors_path)
        retriever_label = "tfidf_shim"

    print(f"DB: {db_path}")
    print(f"Model: {args.model}")
    print(f"Retriever: {retriever_label}")
    print(f"Queries: {len(EVAL_QUERIES)}")
    print(f"Max iterations: {args.max_iterations}")
    print(f"Output: {args.out}")
    print()

    corpus_ids = _load_corpus_ids(db_path)
    print(f"Corpus: {len(corpus_ids):,} documents loaded")
    print()

    results = []
    for i, eq in enumerate(EVAL_QUERIES):
        print(
            f"[{i + 1}/{len(EVAL_QUERIES)}] {eq['query_id']} ({eq['category']}): "
            f"{eq['query'][:60]}..."
        )
        result = _run_query(
            query_id=eq["query_id"],
            category=eq["category"],
            query=eq["query"],
            retriever=retriever,
            provider=provider,
            corpus_ids=corpus_ids,
            max_iterations=args.max_iterations,
            confidence_threshold=args.confidence_threshold,
        )
        results.append(result)
        status = (
            "PASS"
            if result["halt_reason"] == "verify_passed"
            else result["halt_reason"].upper()
        )
        print(
            f"  halt={result['halt_reason']:15s} iters={result['iterations']} "
            f"conf={result['final_confidence']:.3f} "
            f"latency={result['latency_sec']:.1f}s  [{status}]"
        )
        if result["error"]:
            print(f"  ERROR: {result['error']}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    n_passed = sum(1 for r in results if r["halt_reason"] == "verify_passed")
    mean_iters = sum(r["iterations"] for r in results) / len(results) if results else 0
    efficiency = round(1.0 - (mean_iters / args.max_iterations), 4)

    print()
    print("=" * 60)
    print(f"  B-14 trace generation  |  {len(results)} queries")
    print("=" * 60)
    print(f"  verify_passed : {n_passed}/{len(results)}")
    print(f"  mean_iters    : {mean_iters:.2f}")
    print(f"  efficiency    : {efficiency} (threshold >= 0.40)")
    print(f"  Retriever     : {retriever_label}")
    print(f"  Model         : {args.model}")
    print("=" * 60)
    print(f"\nTraces saved: {args.out}")
    print("\nNext:")
    print(
        f"  python -I scripts/run_eval_harness.py "
        f"--traces {args.out} --out data/eval/scorecard_day11.json"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
