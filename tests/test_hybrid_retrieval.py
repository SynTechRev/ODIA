"""Tests for Day 02: HybridRetriever (retrieval/hybrid.py).

These tests use a small in-memory document set so they run without
the BGE-M3 or reranker models on disk. The model-dependent paths are
covered by integration tests gated on the models/ directory being populated.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from oraculus_di_auditor.retrieval.hybrid import (
    HybridRetriever,
    _doc_text,
    _rrf_score,
    _tokenize,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_DOCS = [
    {
        "document_id": "aaa1",
        "title": "Unsigned instrument CONTRACT missing signature",
        "analysis_summary": None,
        "findings": [
            {
                "anomaly_id": "signature:unsigned-instrument",
                "issue": "Signature gap detected in CONTRACT instrument",
                "severity": "critical",
                "layer": "signature",
                "details": {"dollar_amount": "$10,000,000.00"},
            }
        ],
        "anomaly_count": 1,
    },
    {
        "document_id": "bbb2",
        "title": "JAG anti-supplanting audit finding",
        "analysis_summary": "Federal grant compliance issue",
        "findings": [
            {
                "anomaly_id": "grant:anti-supplanting",
                "issue": "JAG anti-supplanting violation",
                "severity": "high",
                "layer": "grant_compliance",
                "details": {"grant_program": "JAG"},
            }
        ],
        "anomaly_count": 1,
    },
    {
        "document_id": "ccc3",
        "title": "Flock Safety ALPR contract",
        "analysis_summary": None,
        "findings": [
            {
                "anomaly_id": "surveillance:alpr",
                "issue": "ALPR surveillance without SB 524 citation",
                "severity": "critical",
                "layer": "surveillance",
                "details": {"vendor": "Flock Safety"},
            }
        ],
        "anomaly_count": 1,
    },
]


def _make_retriever_with_mock_models(use_reranker: bool = False) -> HybridRetriever:
    """Return a HybridRetriever with mocked models for unit tests."""
    r = HybridRetriever(model_dir=Path("models"), use_reranker=use_reranker)
    # Inject a trivial dense model: encodes to a fixed unit vector per doc
    mock_dense = MagicMock()
    mock_dense.encode = MagicMock(
        side_effect=lambda texts, **kw: (
            np.eye(len(texts), 16)
            if isinstance(texts, list) and len(texts) > 1
            else np.eye(1, 16)[0]
        )
    )
    r._dense_model = mock_dense
    return r


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------


def test_rrf_score_decreases_with_rank():
    assert _rrf_score(0) > _rrf_score(1) > _rrf_score(10)


def test_rrf_score_is_positive():
    for rank in range(20):
        assert _rrf_score(rank) > 0


def test_tokenize_lowercases():
    assert "contract" in _tokenize("CONTRACT instrument")


def test_tokenize_splits_on_space():
    assert len(_tokenize("a b c")) == 3


def test_doc_text_includes_title():
    doc = {"document_id": "x", "title": "My Title", "findings": []}
    assert "My Title" in _doc_text(doc)


def test_doc_text_includes_finding_issue():
    doc = {
        "document_id": "x",
        "title": "",
        "findings": [{"issue": "unsigned contract", "details": {}}],
    }
    assert "unsigned contract" in _doc_text(doc)


def test_doc_text_includes_details_values():
    doc = {
        "document_id": "x",
        "title": "",
        "findings": [{"issue": "", "details": {"dollar_amount": "$1,000,000"}}],
    }
    assert "$1,000,000" in _doc_text(doc)


def test_doc_text_handles_null_fields():
    doc = {
        "document_id": "x",
        "title": None,
        "analysis_summary": None,
        "findings": [],
    }
    result = _doc_text(doc)
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Unit tests: indexing
# ---------------------------------------------------------------------------


def test_index_populates_doc_ids():
    r = _make_retriever_with_mock_models()
    r.index(_SAMPLE_DOCS)
    assert r._doc_ids == ["aaa1", "bbb2", "ccc3"]


def test_index_builds_bm25():
    r = _make_retriever_with_mock_models()
    r.index(_SAMPLE_DOCS)
    assert r._bm25 is not None


def test_index_stores_docs():
    r = _make_retriever_with_mock_models()
    r.index(_SAMPLE_DOCS)
    assert len(r._docs) == 3


def test_index_requires_document_id():
    r = _make_retriever_with_mock_models()
    bad_docs = [{"title": "No ID doc", "findings": []}]
    with pytest.raises(KeyError):
        r.index(bad_docs)


# ---------------------------------------------------------------------------
# Unit tests: query
# ---------------------------------------------------------------------------


def _indexed_retriever() -> HybridRetriever:
    r = _make_retriever_with_mock_models(use_reranker=False)
    r.index(_SAMPLE_DOCS)
    # Patch query-time encode to return a (1, 16) array; [0] gives the query vec
    r._dense_model.encode = MagicMock(
        return_value=np.array([[1.0] + [0.0] * 15], dtype=np.float32)
    )
    return r


def test_query_returns_list():
    r = _indexed_retriever()
    results = r.query("unsigned contract", top_k=2)
    assert isinstance(results, list)


def test_query_respects_top_k():
    r = _indexed_retriever()
    results = r.query("signature gap", top_k=2)
    assert len(results) <= 2


def test_query_result_has_required_keys():
    r = _indexed_retriever()
    results = r.query("JAG anti-supplanting", top_k=3)
    required = {"rank", "document_id", "score", "dense_score", "bm25_rank", "findings"}
    for res in results:
        assert required.issubset(res.keys())


def test_query_ranks_start_at_one():
    r = _indexed_retriever()
    results = r.query("ALPR Flock Safety", top_k=3)
    assert results[0]["rank"] == 1


def test_query_without_index_raises():
    r = HybridRetriever(model_dir=Path("models"), use_reranker=False)
    with pytest.raises(RuntimeError, match="index"):
        r.query("test")


# ---------------------------------------------------------------------------
# Unit tests: save/load round-trip
# ---------------------------------------------------------------------------


def test_save_load_roundtrip():
    r = _indexed_retriever()
    with tempfile.TemporaryDirectory() as tmpdir:
        r.save(Path(tmpdir))
        r2 = HybridRetriever(model_dir=Path("models"), use_reranker=False)
        r2._dense_model = r._dense_model
        r2.load(Path(tmpdir))
        assert r2._doc_ids == r._doc_ids
        assert len(r2._docs) == len(r._docs)
        assert r2._bm25 is not None
        assert r2._dense_matrix.shape == r._dense_matrix.shape


def test_save_creates_expected_files():
    r = _indexed_retriever()
    with tempfile.TemporaryDirectory() as tmpdir:
        r.save(Path(tmpdir))
        files = {p.name for p in Path(tmpdir).iterdir()}
        assert "dense_matrix.npy" in files
        assert "bm25.pkl" in files
        assert "doc_ids.json" in files
        assert "docs.jsonl" in files
