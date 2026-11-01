"""Day 03: Three-way retrieval benchmark: TF-IDF vs Hybrid vs ColBERTv2.

Requires:
    - models/bge-m3, models/bge-reranker-v2-m3, models/colbertv2.0 on disk
    - data/eval/fresno_signature_1k.jsonl
    - data/eval/retrieval_queries_v1.jsonl

Output:
    data/eval/retrieval_benchmark_day03.json

Metrics per query:
    - P@10 (Precision at 10)
    - MRR@10 (Mean Reciprocal Rank at 10)
    - Recall@50
    - Latency per query (wall clock)

Additional:
    - Index build time per system
    - Category-level breakdown
    - Projected full-corpus (65108 docs) build times
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DOCS_PATH = Path("data/eval/fresno_signature_1k.jsonl")
QUERIES_PATH = Path("data/eval/retrieval_queries_v1.jsonl")
OUTPUT_PATH = Path("data/eval/retrieval_benchmark_day03.json")
MODEL_DIR = Path("models")
FULL_CORPUS_SIZE = 65108


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


def p_at_k(ranked_ids: list[str], relevant: set[str], k: int = 10) -> float:
    if not relevant:
        return 0.0
    hits = sum(1 for d in ranked_ids[:k] if d in relevant)
    return hits / k


def mrr_at_k(ranked_ids: list[str], relevant: set[str], k: int = 10) -> float:
    for rank, doc_id in enumerate(ranked_ids[:k], start=1):
        if doc_id in relevant:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranked_ids: list[str], relevant: set[str], k: int = 50) -> float:
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


def run_tfidf_baseline(
    docs: list[dict], queries: list[dict]
) -> tuple[list[dict], float]:
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

    t0 = time.perf_counter()
    doc_ids = [d["document_id"] for d in docs]
    corpus = [tokenize(doc_text(d)) for d in docs]
    bm25 = BM25Okapi(corpus)
    build_time = time.perf_counter() - t0

    results = []
    latencies = []
    for q in queries:
        qt0 = time.perf_counter()
        scores = bm25.get_scores(tokenize(q["query"]))
        ranked = [doc_ids[i] for i in np.argsort(scores)[::-1]]
        latencies.append(time.perf_counter() - qt0)
        results.append({"id": q["id"], "ranked_ids": ranked})

    return results, build_time, latencies


def run_hybrid(
    docs: list[dict], queries: list[dict]
) -> tuple[list[dict], float, list[float]]:
    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    r = HybridRetriever(model_dir=MODEL_DIR, use_reranker=True)
    t0 = time.perf_counter()
    r.index(docs)
    build_time = time.perf_counter() - t0

    results = []
    latencies = []
    for q in queries:
        qt0 = time.perf_counter()
        qresults = r.query(q["query"], top_k=50)
        latencies.append(time.perf_counter() - qt0)
        results.append(
            {"id": q["id"], "ranked_ids": [rr["document_id"] for rr in qresults]}
        )

    return results, build_time, latencies


def run_colbert(
    docs: list[dict], queries: list[dict]
) -> tuple[list[dict], float, list[float]]:
    from oraculus_di_auditor.retrieval.colbert_index import ColBERTRetriever

    r = ColBERTRetriever(model_path=MODEL_DIR / "colbertv2.0")
    t0 = time.perf_counter()
    r.index(docs)
    build_time = time.perf_counter() - t0

    results = []
    latencies = []
    for q in queries:
        qt0 = time.perf_counter()
        qresults = r.query(q["query"], top_k=50)
        latencies.append(time.perf_counter() - qt0)
        results.append(
            {"id": q["id"], "ranked_ids": [rr["document_id"] for rr in qresults]}
        )

    return results, build_time, latencies


def score_results(
    system_name: str,
    ranked_results: list[dict],
    queries: list[dict],
    build_time: float,
    latencies: list[float],
    corpus_size: int,
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
            "p_at_10": p_at_k(ranked, relevant, 10),
            "mrr_at_10": mrr_at_k(ranked, relevant, 10),
            "recall_at_50": recall_at_k(ranked, relevant, 50),
            "ndcg_at_10": ndcg_at_k(ranked, relevant, 10),
        }
        per_query.append(metrics)
        by_category.setdefault(q["category"], []).append(metrics)

    def mean(vals: list[float]) -> float:
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    lat_ms = [l * 1000 for l in latencies]
    lat_ms_sorted = sorted(lat_ms)
    p50 = float(np.percentile(lat_ms_sorted, 50))
    p99 = float(np.percentile(lat_ms_sorted, 99))
    scale = FULL_CORPUS_SIZE / corpus_size
    projected_build_h = build_time * scale / 3600

    agg = {
        "p_at_10_overall": mean([m["p_at_10"] for m in per_query]),
        "mrr_at_10_overall": mean([m["mrr_at_10"] for m in per_query]),
        "recall_at_50_overall": mean([m["recall_at_50"] for m in per_query]),
        "ndcg_at_10_overall": mean([m["ndcg_at_10"] for m in per_query]),
        "index_build_time_sec": round(build_time, 2),
        "latency_p50_ms": round(p50, 2),
        "latency_p99_ms": round(p99, 2),
        "projected_full_corpus_build_hours": round(projected_build_h, 2),
    }
    cat_agg = {
        cat: {
            "p_at_10": mean([m["p_at_10"] for m in mlist]),
            "mrr_at_10": mean([m["mrr_at_10"] for m in mlist]),
            "recall_at_50": mean([m["recall_at_50"] for m in mlist]),
        }
        for cat, mlist in by_category.items()
    }
    return {
        "system": system_name,
        "aggregate": agg,
        "by_category": cat_agg,
        "per_query": per_query,
    }


def print_summary(result: dict) -> None:
    agg = result["aggregate"]
    logger.info(
        "%s | P@10=%.3f MRR@10=%.3f R@50=%.3f | build=%.1fs p50=%.0fms p99=%.0fms",
        result["system"].ljust(14),
        agg["p_at_10_overall"],
        agg["mrr_at_10_overall"],
        agg["recall_at_50_overall"],
        agg["index_build_time_sec"],
        agg["latency_p50_ms"],
        agg["latency_p99_ms"],
    )


def main() -> None:
    docs = load_docs()
    queries = load_queries()
    corpus_size = len(docs)
    logger.info("Loaded %d docs, %d queries", corpus_size, len(queries))

    output = {
        "benchmark_date": "2026-10-23",
        "corpus_size": corpus_size,
        "query_count": len(queries),
        "full_corpus_size": FULL_CORPUS_SIZE,
        "configurations": {},
    }

    # TF-IDF baseline
    logger.info("--- TF-IDF / BM25 baseline ---")
    tfidf_ranked, tfidf_build, tfidf_lat = run_tfidf_baseline(docs, queries)
    tfidf_result = score_results(
        "tfidf_bm25", tfidf_ranked, queries, tfidf_build, tfidf_lat, corpus_size
    )
    print_summary(tfidf_result)
    output["configurations"]["tfidf_bm25"] = tfidf_result["aggregate"]
    output["configurations"]["tfidf_bm25"]["by_category"] = tfidf_result["by_category"]

    # Hybrid
    if (MODEL_DIR / "bge-m3").exists():
        logger.info("--- Hybrid (BGE-M3 + BM25 + reranker) ---")
        hybrid_ranked, hybrid_build, hybrid_lat = run_hybrid(docs, queries)
        hybrid_result = score_results(
            "hybrid_bge_m3",
            hybrid_ranked,
            queries,
            hybrid_build,
            hybrid_lat,
            corpus_size,
        )
        print_summary(hybrid_result)
        output["configurations"]["hybrid_bge_m3"] = hybrid_result["aggregate"]
        output["configurations"]["hybrid_bge_m3"]["by_category"] = hybrid_result[
            "by_category"
        ]
    else:
        logger.warning("models/bge-m3 not found - skipping hybrid")

    # ColBERTv2
    if (MODEL_DIR / "colbertv2.0").exists():
        logger.info("--- ColBERTv2 late interaction ---")
        colbert_ranked, colbert_build, colbert_lat = run_colbert(docs, queries)
        colbert_result = score_results(
            "colbertv2",
            colbert_ranked,
            queries,
            colbert_build,
            colbert_lat,
            corpus_size,
        )
        print_summary(colbert_result)
        output["configurations"]["colbertv2"] = colbert_result["aggregate"]
        output["configurations"]["colbertv2"]["by_category"] = colbert_result[
            "by_category"
        ]
    else:
        logger.warning("models/colbertv2.0 not found - skipping ColBERT")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    logger.info("Results written to %s", OUTPUT_PATH)

    # Delta summary
    systems = list(output["configurations"].keys())
    if len(systems) >= 2:
        base = output["configurations"]["tfidf_bm25"]
        for sys_name in systems[1:]:
            sys_agg = output["configurations"][sys_name]
            logger.info(
                "Delta %s vs tfidf: P@10=%+.3f MRR@10=%+.3f R@50=%+.3f",
                sys_name,
                sys_agg["p_at_10_overall"] - base["p_at_10_overall"],
                sys_agg["mrr_at_10_overall"] - base["mrr_at_10_overall"],
                sys_agg["recall_at_50_overall"] - base["recall_at_50_overall"],
            )


if __name__ == "__main__":
    main()
