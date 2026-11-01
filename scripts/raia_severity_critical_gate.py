#!/usr/bin/env python3
"""Post-DPO severity_critical gate: verify odia-v3 produces cited findings.

Run LOCALLY after:
  1. Day 11 Vast.ai: odia-v3 GGUF downloaded from HuggingFace
  2. Ollama: registered with `ollama create odia-v3 -f models/Modelfile.v3`
  3. Local corpus vector index present at data/vectors/

Gate criterion (default): >= 1 of 3 severity_critical queries must produce
halt_reason=verify_passed with >= 1 verified doc_id citation.

If odia-v2 is active before odia-v3 is deployed, pass --model odia-v2 to
run the pre-DPO baseline (expected to FAIL -- confirms regression test works).

Usage:
  python -I scripts/raia_severity_critical_gate.py
  python -I scripts/raia_severity_critical_gate.py --model odia-v3
  python -I scripts/raia_severity_critical_gate.py --model odia-v2 --baseline
  python -I scripts/raia_severity_critical_gate.py --min-pass 2 --out data/eval/gate_day11.json
"""
import argparse
import json
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oraculus_di_auditor.agents.raia_v0 import run_raia
from oraculus_di_auditor.llm_providers import OllamaProvider


class _TFIDFRetrieverShim:
    """Wraps the production TF-IDF index with HybridRetriever's query interface.

    The HybridRetriever (BGE-M3 dense + BM25) requires a separately-built
    dense_matrix.npy index that does not yet exist for the full 81K corpus.
    This shim uses the existing collection_vocab.pkl + collection_vectors.npy
    (TF-IDF, built 2026-10-16) so the gate can run immediately.
    """

    def __init__(self, vectors_path: Path) -> None:
        import pickle

        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer

        with open(vectors_path / "collection_vocab.pkl", "rb") as fh:
            vocab_data = pickle.load(fh)

        # Reconstruct fitted TfidfVectorizer from saved vocabulary + idf weights.
        # The vectorizer is serialized as a dict (not a full sklearn object) so
        # we rebuild it: pass vocabulary to constructor (sets fixed_vocabulary_),
        # fit on a dummy text to initialize _tfidf, then overwrite idf_.
        self._vectorizer = TfidfVectorizer(
            vocabulary=vocab_data["vocabulary"],
            norm=vocab_data["norm"],
            lowercase=True,
            stop_words="english",
        )
        self._vectorizer.fit(["x"])
        self._vectorizer._tfidf.idf_ = np.array(vocab_data["idf"], dtype=np.float64)

        self._vectors = np.load(vectors_path / "collection_vectors.npy").astype(
            np.float32
        )
        raw_meta = np.load(vectors_path / "collection_metadata.npy", allow_pickle=True)
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


# Gate queries: q060 (Day 4 failure case) + 2 new severity_critical variants.
# All target critical-severity anomaly patterns present in the 11,636-finding
# critical tier of the corpus.
GATE_QUERIES = [
    {
        "query_id": "sc-01",
        "query": "critical unsigned agreement instrument compliance violation",
        "note": "Day 4 q060 restatement -- primary gate target",
    },
    {
        "query_id": "sc-02",
        "query": "JAG grant anti-supplanting critical compliance finding",
        "note": "JAG anti-supplanting -- 614 critical findings across 14 jurisdictions",
    },
    {
        "query_id": "sc-03",
        "query": "surveillance procurement without council authorization critical",
        "note": "ALPR/surveillance critical procurement gap pattern",
    },
]

_CITATION_RE = re.compile(r"\(doc_id:([^)]+)\)")

DB_PATHS = [
    Path("oraculus_audit.db"),
    Path.home() / "AppData" / "Roaming" / "odia-desktop" / "oraculus_audit.db",
    Path.home() / "oraculus_audit.db",
]

VECTOR_PATHS = [
    Path("data") / "vectors",
    Path.home() / "AppData" / "Roaming" / "ODIA" / "data" / "vectors",
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


def _load_corpus_ids(db_path: Path) -> set[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT document_id FROM documents").fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _run_gate_query(
    query_id: str,
    query: str,
    retriever: object,
    provider: OllamaProvider,
    corpus_ids: set[str],
    max_iterations: int,
    confidence_threshold: float,
) -> dict:
    ts_start = datetime.now(UTC)
    try:
        state = run_raia(
            query=query,
            retriever=retriever,
            provider=provider,
            corpus_ids=corpus_ids,
            max_iterations=max_iterations,
            confidence_threshold=confidence_threshold,
        )
        cited = _CITATION_RE.findall(state.get("final_answer", ""))
        valid_cited = [c for c in cited if c in corpus_ids]
        return {
            "query_id": query_id,
            "query": query,
            "halt_reason": state.get("halt_reason", ""),
            "iterations": state.get("iteration", 0),
            "citations_found": len(cited),
            "citations_valid": len(valid_cited),
            "gate_pass": state.get("halt_reason") == "verify_passed"
            and len(valid_cited) >= 1,
            "latency_s": (datetime.now(UTC) - ts_start).total_seconds(),
            "error": None,
        }
    except Exception as exc:
        return {
            "query_id": query_id,
            "query": query,
            "halt_reason": "error",
            "iterations": 0,
            "citations_found": 0,
            "citations_valid": 0,
            "gate_pass": False,
            "latency_s": (datetime.now(UTC) - ts_start).total_seconds(),
            "error": str(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-DPO severity_critical RAIA gate")
    parser.add_argument(
        "--model",
        default="odia-v3",
        help="Ollama model name to test (default: odia-v3)",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Mark result as pre-DPO baseline run (expects FAIL)",
    )
    parser.add_argument(
        "--min-pass",
        type=int,
        default=1,
        help="Minimum queries that must pass gate (default: 1)",
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
        "--out",
        type=Path,
        default=Path("data/eval/severity_critical_gate.json"),
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
            "ERROR: vector index not found (collection_vocab.pkl missing). Checked:\n"
            + "\n".join(f"  {p}" for p in VECTOR_PATHS),
            file=sys.stderr,
        )
        return 1

    print(f"DB: {db_path}")
    print(f"Vectors: {vectors_path}")
    print(f"Model: {args.model}")
    print(f"Gate: >= {args.min_pass} of {len(GATE_QUERIES)} queries must pass")
    print()

    provider = OllamaProvider(model=args.model)
    if not provider.is_available():
        print(
            f"ERROR: Ollama not reachable at {provider.base_url}. "
            f"Is Ollama running? Is {args.model} registered?",
            file=sys.stderr,
        )
        return 1
    print(f"Ollama: reachable at {provider.base_url}")

    print("Loading corpus IDs...")
    corpus_ids = _load_corpus_ids(db_path)
    print(f"Corpus: {len(corpus_ids):,} documents")

    print(
        "Initializing retriever (TF-IDF shim -- HybridRetriever index not yet built)..."
    )
    retriever = _TFIDFRetrieverShim(vectors_path)
    print(f"Retriever: ready ({len(retriever._metadata):,} docs indexed)")
    print()

    results = []
    for i, gq in enumerate(GATE_QUERIES):
        print(f"[{i+1}/{len(GATE_QUERIES)}] {gq['query_id']}: {gq['query'][:60]}...")
        result = _run_gate_query(
            query_id=gq["query_id"],
            query=gq["query"],
            retriever=retriever,
            provider=provider,
            corpus_ids=corpus_ids,
            max_iterations=args.max_iterations,
            confidence_threshold=args.confidence_threshold,
        )
        results.append(result)
        status = "PASS" if result["gate_pass"] else "FAIL"
        print(
            f"  halt={result['halt_reason']} iters={result['iterations']} "
            f"valid_cited={result['citations_valid']} [{status}]"
        )
        if result["error"]:
            print(f"  ERROR: {result['error']}")

    passed = sum(1 for r in results if r["gate_pass"])
    gate_passed = passed >= args.min_pass
    verdict = "PASS" if gate_passed else "FAIL"

    print()
    print("=" * 60)
    print(f"  severity_critical gate  |  {verdict}")
    print("=" * 60)
    print(f"  Model    : {args.model}")
    print(f"  Baseline : {args.baseline}")
    print(f"  Passed   : {passed}/{len(GATE_QUERIES)} (threshold: {args.min_pass})")
    print("-" * 60)
    for r in results:
        status = "PASS" if r["gate_pass"] else "FAIL"
        print(
            f"  {r['query_id']:6s}  halt={r['halt_reason']:20s}  "
            f"cited={r['citations_valid']:2d}  [{status}]"
        )
    print("=" * 60)

    if gate_passed and not args.baseline:
        print()
        print("GATE PASSED: odia-v3 is authorized for /api/v1/raia/analyze promotion.")
    elif not gate_passed and args.baseline:
        print()
        print(
            "BASELINE CONFIRMED: pre-DPO model fails severity_critical gate as expected."
        )
    elif not gate_passed:
        print()
        print(
            "GATE FAILED: odia-v3 does not yet meet severity_critical citation threshold."
        )
        print("Review DPO training convergence before promoting to production.")

    report = {
        "run_date": datetime.now(UTC).isoformat(),
        "model": args.model,
        "baseline": args.baseline,
        "gate_threshold": args.min_pass,
        "gate_passed": gate_passed,
        "verdict": verdict,
        "passed_count": passed,
        "total_queries": len(GATE_QUERIES),
        "max_iterations": args.max_iterations,
        "confidence_threshold": args.confidence_threshold,
        "results": results,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport saved: {args.out}")

    return 0 if gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
