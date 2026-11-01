"""Day 02: Hybrid retriever combining BGE-M3 dense, BM25 sparse, and reranker.

Architecture:
    1. Dense: BGE-M3 via sentence-transformers (cosine similarity)
    2. Sparse: BM25Okapi (rank_bm25)
    3. Fusion: Reciprocal Rank Fusion (RRF, k=60)
    4. Rerank: bge-reranker-v2-m3 CrossEncoder on top-N fused candidates

Models (downloaded to models/ by scripts/download_day02_models.py):
    Dense:   models/bge-m3
    Rerank:  models/bge-reranker-v2-m3

Usage:
    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever
    r = HybridRetriever(model_dir=Path("models"))
    r.index(documents)          # list of dicts with "document_id", "text"
    results = r.query("...", top_k=15)
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np

# rank_bm25 is optional at import time; only needed when HybridRetriever.index()
# is called. This allows the module to be imported in CI environments without
# rank_bm25 installed (e.g. when only testing ColBERT or other retrievers).
try:
    from rank_bm25 import BM25Okapi as _BM25Okapi

    _BM25_AVAILABLE = True
except ImportError:
    _BM25_AVAILABLE = False

logger = logging.getLogger(__name__)

_RRF_K = 60
_DENSE_CANDIDATE_K = 100
_BM25_CANDIDATE_K = 100
_RERANK_TOP_N = 30


def _rrf_score(rank: int, k: int = _RRF_K) -> float:
    return 1.0 / (k + rank)


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def _doc_text(doc: dict[str, Any]) -> str:
    parts: list[str] = []
    if doc.get("title"):
        parts.append(str(doc["title"]))
    if doc.get("analysis_summary"):
        parts.append(str(doc["analysis_summary"]))
    for f in doc.get("findings", []):
        if f.get("issue"):
            parts.append(str(f["issue"]))
        details = f.get("details", {})
        if isinstance(details, dict):
            parts.extend(str(v) for v in details.values() if v)
    return " ".join(parts)


class HybridRetriever:
    """BGE-M3 dense + BM25 sparse + bge-reranker-v2-m3 reranker.

    Args:
        model_dir: Directory containing bge-m3/ and bge-reranker-v2-m3/ subdirs.
        dense_weight: Weight for dense score in pre-rerank fusion (unused when
            reranker is active; kept for offline-reranker fallback).
        use_reranker: Enable cross-encoder reranking step (default True).
    """

    def __init__(
        self,
        model_dir: Path = Path("models"),
        use_reranker: bool = True,
    ) -> None:
        self._model_dir = Path(model_dir)
        self._use_reranker = use_reranker

        self._dense_model = None
        self._rerank_model = None
        self._bm25: Any | None = None
        self._doc_ids: list[str] = []
        self._doc_texts: list[str] = []
        self._docs: list[dict[str, Any]] = []
        self._dense_matrix: np.ndarray | None = None

    # ------------------------------------------------------------------
    # Model loading (lazy, called on first index/query)
    # ------------------------------------------------------------------

    def _load_dense(self) -> None:
        if self._dense_model is not None:
            return
        from sentence_transformers import SentenceTransformer

        dense_path = self._model_dir / "bge-m3"
        if not dense_path.exists():
            raise FileNotFoundError(
                f"BGE-M3 not found at {dense_path}. "
                "Run scripts/download_day02_models.py first."
            )
        logger.info("Loading BGE-M3 from %s", dense_path)
        self._dense_model = SentenceTransformer(
            str(dense_path), device="cpu", trust_remote_code=True
        )

    def _load_reranker(self) -> None:
        if self._rerank_model is not None:
            return
        from sentence_transformers import CrossEncoder

        rerank_path = self._model_dir / "bge-reranker-v2-m3"
        if not rerank_path.exists():
            logger.warning(
                "bge-reranker-v2-m3 not found at %s - reranking disabled.", rerank_path
            )
            self._use_reranker = False
            return
        logger.info("Loading bge-reranker-v2-m3 from %s", rerank_path)
        self._rerank_model = CrossEncoder(
            str(rerank_path), device="cpu", trust_remote_code=True
        )

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index(self, documents: list[dict[str, Any]], batch_size: int = 64) -> None:
        """Build dense and sparse indices from a list of document dicts.

        Each document must have at least "document_id". Text is derived from
        title, analysis_summary, and findings[].issue fields.

        Args:
            documents: List of document dicts (from MAS export or OracRAG).
            batch_size: Batch size for BGE-M3 encoding.
        """
        self._load_dense()
        if self._use_reranker:
            self._load_reranker()

        self._docs = documents
        self._doc_ids = [d["document_id"] for d in documents]
        self._doc_texts = [_doc_text(d) for d in documents]

        if not _BM25_AVAILABLE:
            raise ImportError(
                "rank_bm25 is required to use HybridRetriever. "
                "Install it with: pip install rank-bm25"
            )
        logger.info("Building BM25 index over %d docs", len(documents))
        tokenized = [_tokenize(t) for t in self._doc_texts]
        self._bm25 = _BM25Okapi(tokenized)

        logger.info(
            "Encoding %d docs with BGE-M3 (batch_size=%d)", len(documents), batch_size
        )
        self._dense_matrix = self._dense_model.encode(
            self._doc_texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        logger.info(
            "Index built: dense=%s BM25=%d",
            self._dense_matrix.shape,
            len(self._doc_texts),
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, index_dir: Path) -> None:
        """Save the built index to disk."""
        index_dir = Path(index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)
        np.save(index_dir / "dense_matrix.npy", self._dense_matrix)
        with open(index_dir / "bm25.pkl", "wb") as f:
            pickle.dump(self._bm25, f)
        with open(index_dir / "doc_ids.json", "w", encoding="utf-8") as f:
            json.dump(self._doc_ids, f)
        with open(index_dir / "doc_texts.json", "w", encoding="utf-8") as f:
            json.dump(self._doc_texts, f)
        with open(index_dir / "docs.jsonl", "w", encoding="utf-8") as f:
            for doc in self._docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
        logger.info("Index saved to %s", index_dir)

    def load(self, index_dir: Path) -> None:
        """Load a previously saved index from disk."""
        index_dir = Path(index_dir)
        self._dense_matrix = np.load(index_dir / "dense_matrix.npy")
        with open(index_dir / "bm25.pkl", "rb") as f:
            self._bm25 = pickle.load(f)
        with open(index_dir / "doc_ids.json", encoding="utf-8") as f:
            self._doc_ids = json.load(f)
        with open(index_dir / "doc_texts.json", encoding="utf-8") as f:
            self._doc_texts = json.load(f)
        self._docs = []
        with open(index_dir / "docs.jsonl", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._docs.append(json.loads(line))
        logger.info("Index loaded from %s (%d docs)", index_dir, len(self._doc_ids))

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        question: str,
        top_k: int = 15,
        dense_k: int = _DENSE_CANDIDATE_K,
        bm25_k: int = _BM25_CANDIDATE_K,
        rerank_n: int = _RERANK_TOP_N,
    ) -> list[dict[str, Any]]:
        """Retrieve and rerank documents for a query.

        Args:
            question: Natural language query string.
            top_k: Number of final results to return.
            dense_k: Number of candidates from dense retrieval.
            bm25_k: Number of candidates from BM25 retrieval.
            rerank_n: Number of RRF-fused candidates to rerank.

        Returns:
            List of result dicts: {document_id, title, score, rank,
            dense_score, bm25_rank, rerank_score, findings}
        """
        if self._dense_matrix is None or self._bm25 is None:
            raise RuntimeError("Call index() or load() before query().")

        self._load_dense()

        # Dense retrieval
        q_vec = self._dense_model.encode(
            [question], normalize_embeddings=True, show_progress_bar=False
        )[0]
        dense_scores = self._dense_matrix @ q_vec
        dense_top = np.argsort(dense_scores)[::-1][:dense_k]

        # BM25 retrieval
        bm25_scores = self._bm25.get_scores(_tokenize(question))
        bm25_top = np.argsort(bm25_scores)[::-1][:bm25_k]

        # RRF fusion
        rrf: dict[int, float] = {}
        dense_rank_map: dict[int, int] = {}
        bm25_rank_map: dict[int, int] = {}
        for rank, idx in enumerate(dense_top):
            rrf[idx] = rrf.get(idx, 0.0) + _rrf_score(rank)
            dense_rank_map[idx] = rank
        for rank, idx in enumerate(bm25_top):
            rrf[idx] = rrf.get(idx, 0.0) + _rrf_score(rank)
            bm25_rank_map[idx] = rank

        fused = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:rerank_n]
        candidate_indices = [idx for idx, _ in fused]

        # Reranking
        if self._use_reranker and self._rerank_model is not None:
            pairs = [(question, self._doc_texts[i]) for i in candidate_indices]
            rerank_scores = self._rerank_model.predict(pairs, show_progress_bar=False)
            reranked = sorted(
                zip(candidate_indices, rerank_scores, strict=False),
                key=lambda x: x[1],
                reverse=True,
            )
            final = reranked[:top_k]
        else:
            final = [(idx, rrf[idx]) for idx, _ in fused[:top_k]]

        results = []
        for rank, (idx, score) in enumerate(final):
            doc = self._docs[idx]
            results.append(
                {
                    "rank": rank + 1,
                    "document_id": self._doc_ids[idx],
                    "title": doc.get("title", ""),
                    "score": float(score),
                    "dense_score": float(dense_scores[idx]),
                    "bm25_rank": bm25_rank_map.get(idx, -1),
                    "rerank_score": float(score) if self._use_reranker else None,
                    "anomaly_count": doc.get("anomaly_count", 0),
                    "findings": doc.get("findings", []),
                }
            )
        return results
