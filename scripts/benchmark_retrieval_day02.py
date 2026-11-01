"""Day 02: Retrieval benchmark comparing TF-IDF vs Hybrid (BGE-M3+BM25+reranker).

Requires:
    - models/bge-m3 on disk (run scripts/download_day02_models.py)
    - data/eval/fresno_signature_1k.jsonl (run scripts/generate_retrieval_queries_day02.py)
    - data/eval/retrieval_queries_v1.jsonl (run scripts/generate_retrieval_queries_day02.py)

Output:
    data/eval/retrieval_benchmark_day02.json

Metrics (per-query):
    - MRR@10: Mean Reciprocal Rank at cutoff 10
    - Recall@10: Fraction of relevant docs found in top 10
    - Recall@20: Fraction of relevant docs found in top 20
    - NDCG@10: Normalized Discounted Cumulative Gain at 10

Aggregate output:
    - Mean MRR@10, Recall@10, Recall@20, NDCG@10 per system
    - Per-category breakdown
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DOCS_PATH = Path("data/eval/fresno_signature_1k.jsonl")
QUERIES_PATH = Path("data/eval/retrieval_queries_v1.jsonl")
OUTPUT_PATH = Path("data/eval/retrieval_benchmark_day02.json")
MODEL_DIR = Path("models")


def load_docs() -> list[dict]:
    docs = []
    with open(DOCS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def load_queries() -> list[dict]:
    queries = []
    with open(QUERIES_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))
    return queries


def mrr_at_k(ranked_ids: list[str], relevant: set[str], k: int = 10) -> float:
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    found = sum(1 for d in ranked_ids[:k] if d in relevant)
    return found / min(len(relevant), k)


def ndcg_at_k(ranked_ids: list[str], relevant: set[str], k: int = 10) -> float:
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, doc_id in enumerate(ranked_ids[:k])
        if doc_id in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def run_tfidf_baseline(docs: list[dict], queries: list[dict]) -> list[dict]:
    """Simple TF-IDF baseline using rank_bm25 (BM25Okapi, no reranker)."""
    from rank_bm25 import BM25Okapi

    def tokenize(text: str) -> list[str]:
        return text.lower().split()

    def doc_text(doc: dict) -> str:
        parts = []
        if doc.get("title"):
            parts.append(str(doc["title"]))
        for f in doc.get("findings", []):
            if f.get("issue"):
                parts.append(str(f["issue"]))
        return " ".join(parts)

    doc_ids = [d["document_id"] for d in docs]
    corpus = [tokenize(doc_text(d)) for d in docs]
    bm25 = BM25Okapi(corpus)

    results = []
    for q in queries:
        scores = bm25.get_scores(tokenize(q["query"]))

        ranked = [
            doc_ids[i]
            for i in reversed(list(sorted(range(len(scores)), key=lambda x: scores[x])))
        ]
        results.append({"id": q["id"], "ranked_ids": ranked})
    return results


def run_hybrid(docs: list[dict], queries: list[dict]) -> list[dict]:
    """Hybrid retriever: BGE-M3 dense + BM25 + bge-reranker-v2-m3."""
    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    r = HybridRetriever(model_dir=MODEL_DIR, use_reranker=True)
    logger.info("Indexing %d docs with hybrid retriever...", len(docs))
    t0 = time.perf_counter()
    r.index(docs)
    logger.info("Indexed in %.1fs", time.perf_counter() - t0)

    results = []
    for q in queries:
        qresults = r.query(q["query"], top_k=20)
        results.append(
            {"id": q["id"], "ranked_ids": [r["document_id"] for r in qresults]}
        )
    return results


def score_results(
    system_name: str,
    ranked_results: list[dict],
    queries: list[dict],
) -> dict:
    query_map = {q["id"]: q for q in queries}
    per_query = []
    by_category: dict[str, list[dict]] = {}

    for r in ranked_results:
        q = query_map[r["id"]]
        relevant = set(q["relevant_doc_ids"])
        ranked = r["ranked_ids"]
        metrics = {
            "id": q["id"],
            "category": q["category"],
            "mrr_at_10": mrr_at_k(ranked, relevant, 10),
            "recall_at_10": recall_at_k(ranked, relevant, 10),
            "recall_at_20": recall_at_k(ranked, relevant, 20),
            "ndcg_at_10": ndcg_at_k(ranked, relevant, 10),
        }
        per_query.append(metrics)
        cat = q["category"]
        by_category.setdefault(cat, []).append(metrics)

    def mean(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    aggregate = {
        "mrr_at_10": mean([m["mrr_at_10"] for m in per_query]),
        "recall_at_10": mean([m["recall_at_10"] for m in per_query]),
        "recall_at_20": mean([m["recall_at_20"] for m in per_query]),
        "ndcg_at_10": mean([m["ndcg_at_10"] for m in per_query]),
    }
    category_agg = {
        cat: {
            "mrr_at_10": mean([m["mrr_at_10"] for m in mlist]),
            "recall_at_10": mean([m["recall_at_10"] for m in mlist]),
        }
        for cat, mlist in by_category.items()
    }
    return {
        "system": system_name,
        "aggregate": aggregate,
        "by_category": category_agg,
        "per_query": per_query,
    }


def main() -> None:
    docs = load_docs()
    queries = load_queries()
    logger.info("Loaded %d docs, %d queries", len(docs), len(queries))

    output = {"docs": len(docs), "queries": len(queries), "systems": []}

    logger.info("--- TF-IDF / BM25 baseline ---")
    t0 = time.perf_counter()
    tfidf_ranked = run_tfidf_baseline(docs, queries)
    tfidf_elapsed = time.perf_counter() - t0
    tfidf_scores = score_results("tfidf_bm25", tfidf_ranked, queries)
    tfidf_scores["elapsed_s"] = round(tfidf_elapsed, 2)
    output["systems"].append(tfidf_scores)
    agg = tfidf_scores["aggregate"]
    logger.info(
        "TF-IDF  MRR@10=%.3f Recall@10=%.3f Recall@20=%.3f NDCG@10=%.3f",
        agg["mrr_at_10"],
        agg["recall_at_10"],
        agg["recall_at_20"],
        agg["ndcg_at_10"],
    )

    dense_path = MODEL_DIR / "bge-m3"
    if not dense_path.exists():
        logger.warning("models/bge-m3 not found — skipping hybrid run. Download first.")
    else:
        logger.info("--- Hybrid (BGE-M3 + BM25 + reranker) ---")
        t0 = time.perf_counter()
        hybrid_ranked = run_hybrid(docs, queries)
        hybrid_elapsed = time.perf_counter() - t0
        hybrid_scores = score_results("hybrid_bge_m3", hybrid_ranked, queries)
        hybrid_scores["elapsed_s"] = round(hybrid_elapsed, 2)
        output["systems"].append(hybrid_scores)
        agg = hybrid_scores["aggregate"]
        logger.info(
            "Hybrid  MRR@10=%.3f Recall@10=%.3f Recall@20=%.3f NDCG@10=%.3f",
            agg["mrr_at_10"],
            agg["recall_at_10"],
            agg["recall_at_20"],
            agg["ndcg_at_10"],
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("Results written to %s", OUTPUT_PATH)

    # Print delta if both systems ran
    if len(output["systems"]) == 2:
        base = output["systems"][0]["aggregate"]
        hyb = output["systems"][1]["aggregate"]
        logger.info(
            "Delta (hybrid - tfidf): MRR@10=%+.3f Recall@10=%+.3f",
            hyb["mrr_at_10"] - base["mrr_at_10"],
            hyb["recall_at_10"] - base["recall_at_10"],
        )


if __name__ == "__main__":
    main()
