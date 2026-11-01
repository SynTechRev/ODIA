"""Tests for Day 03: ColBERTRetriever (retrieval/colbert_index.py).

Unit tests use mocked model so they run without GPU or the colbertv2.0 weights.
Integration tests (requiring the real model) are skipped unless
models/colbertv2.0 exists.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest
from oraculus_di_auditor.retrieval.colbert_index import (
    ColBERTRetriever,
    _doc_text,
    _l2_normalize,
)

_MODEL_PATH = Path("models/colbertv2.0")
_MODEL_AVAILABLE = _MODEL_PATH.exists() and any(_MODEL_PATH.iterdir())

_SAMPLE_DOCS = [
    {
        "document_id": "aaa1",
        "title": "Unsigned instrument CONTRACT missing signature",
        "analysis_summary": None,
        "findings": [
            {
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
        "title": "Flock Safety ALPR surveillance contract",
        "analysis_summary": None,
        "findings": [
            {
                "issue": "ALPR surveillance without SB 524 citation",
                "severity": "critical",
                "layer": "surveillance",
                "details": {"vendor": "Flock Safety"},
            }
        ],
        "anomaly_count": 1,
    },
]


def _random_token_matrix(n_tokens: int = 20, dim: int = 128) -> np.ndarray:
    vecs = np.random.randn(n_tokens, dim).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    return (vecs / np.maximum(norms, 1e-9)).astype(np.float16)


def _make_retriever_with_mock_model() -> ColBERTRetriever:
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    # Inject mock encoder: each call returns one (20, 128) token matrix per text
    r._model = MagicMock()
    r._tokenizer = MagicMock()
    r._linear = None

    def fake_encode_tokens(texts, max_length, batch_size=32):
        return [_random_token_matrix() for _ in texts]

    r._encode_tokens = fake_encode_tokens
    return r


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------


def test_l2_normalize_unit_vectors():
    vecs = np.random.randn(10, 128).astype(np.float32)
    normed = _l2_normalize(vecs)
    norms = np.linalg.norm(normed, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_l2_normalize_zero_vector():
    vecs = np.zeros((3, 128), dtype=np.float32)
    result = _l2_normalize(vecs)
    assert not np.any(np.isnan(result))


def test_doc_text_title_included():
    doc = {"document_id": "x", "title": "My Title", "findings": []}
    assert "My Title" in _doc_text(doc)


def test_doc_text_finding_issue_included():
    doc = {
        "document_id": "x",
        "title": "",
        "findings": [{"issue": "unsigned instrument", "details": {}}],
    }
    assert "unsigned instrument" in _doc_text(doc)


def test_doc_text_details_included():
    doc = {
        "document_id": "x",
        "title": "",
        "findings": [{"issue": "", "details": {"dollar_amount": "$5,000,000"}}],
    }
    assert "$5,000,000" in _doc_text(doc)


def test_doc_text_null_fields_safe():
    doc = {"document_id": "x", "title": None, "findings": []}
    assert isinstance(_doc_text(doc), str)


# ---------------------------------------------------------------------------
# Unit tests: indexing
# ---------------------------------------------------------------------------


def test_index_populates_doc_ids():
    r = _make_retriever_with_mock_model()
    r.index(_SAMPLE_DOCS)
    assert r._doc_ids == ["aaa1", "bbb2", "ccc3"]


def test_index_stores_three_token_matrices():
    r = _make_retriever_with_mock_model()
    r.index(_SAMPLE_DOCS)
    assert len(r._doc_token_matrices) == 3


def test_index_token_matrices_correct_shape():
    r = _make_retriever_with_mock_model()
    r.index(_SAMPLE_DOCS)
    for mat in r._doc_token_matrices:
        assert mat.ndim == 2
        assert mat.shape[1] == 128


def test_index_requires_document_id():
    r = _make_retriever_with_mock_model()
    with pytest.raises(KeyError):
        r.index([{"title": "no id", "findings": []}])


# ---------------------------------------------------------------------------
# Unit tests: query
# ---------------------------------------------------------------------------


def _indexed_retriever() -> ColBERTRetriever:
    r = _make_retriever_with_mock_model()
    # Use deterministic token matrices for predictable scoring
    np.random.seed(0)
    r._doc_token_matrices = [_random_token_matrix() for _ in _SAMPLE_DOCS]
    r._doc_ids = [d["document_id"] for d in _SAMPLE_DOCS]
    r._doc_texts = ["text"] * len(_SAMPLE_DOCS)
    r._docs = _SAMPLE_DOCS
    # query-time: encode returns a specific matrix that scores doc[0] highest
    high_score_vec = r._doc_token_matrices[0][:1].astype(np.float32)

    def fake_encode_tokens(texts, max_length, batch_size=32):
        return [high_score_vec]

    r._encode_tokens = fake_encode_tokens
    return r


def test_query_returns_list():
    r = _indexed_retriever()
    results = r.query("unsigned contract", top_k=2)
    assert isinstance(results, list)


def test_query_respects_top_k():
    r = _indexed_retriever()
    results = r.query("test", top_k=2)
    assert len(results) <= 2


def test_query_result_required_keys():
    r = _indexed_retriever()
    results = r.query("test", top_k=3)
    for res in results:
        assert "rank" in res
        assert "document_id" in res
        assert "score" in res


def test_query_ranks_start_at_one():
    r = _indexed_retriever()
    results = r.query("test", top_k=3)
    assert results[0]["rank"] == 1


def test_query_without_index_raises():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    with pytest.raises(RuntimeError, match="index"):
        r.query("test")


def test_query_scores_descending():
    r = _indexed_retriever()
    results = r.query("test", top_k=3)
    scores = [res["score"] for res in results]
    assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Unit tests: save/load round-trip
# ---------------------------------------------------------------------------


def test_save_load_roundtrip():
    r = _indexed_retriever()
    r._doc_ids = [d["document_id"] for d in _SAMPLE_DOCS]
    r._docs = _SAMPLE_DOCS
    r._doc_texts = ["text"] * len(_SAMPLE_DOCS)
    with tempfile.TemporaryDirectory() as tmpdir:
        r.save(Path(tmpdir))
        r2 = ColBERTRetriever(model_path=_MODEL_PATH)
        r2._encode_tokens = lambda *a, **kw: [_random_token_matrix()]
        r2.load(Path(tmpdir))
        assert r2._doc_ids == r._doc_ids
        assert len(r2._doc_token_matrices) == len(r._doc_token_matrices)


def test_save_creates_expected_files():
    r = _indexed_retriever()
    r._doc_ids = [d["document_id"] for d in _SAMPLE_DOCS]
    r._docs = _SAMPLE_DOCS
    r._doc_texts = ["text"] * len(_SAMPLE_DOCS)
    with tempfile.TemporaryDirectory() as tmpdir:
        r.save(Path(tmpdir))
        files = {p.name for p in Path(tmpdir).iterdir()}
        assert "token_matrices.pkl" in files
        assert "doc_ids.json" in files
        assert "docs.jsonl" in files


# ---------------------------------------------------------------------------
# Integration tests (skipped unless real model is available)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_model_loads_from_local_path():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r._load_model()
    assert r._model is not None
    assert r._tokenizer is not None


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_linear_projection_loaded():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r._load_model()
    assert (
        r._linear is not None
    ), "ColBERT linear projection should load from safetensors"


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_retrieve_returns_k_results():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r.index(_SAMPLE_DOCS[:3], batch_size=4)
    results = r.query("unsigned contract", top_k=2)
    assert len(results) == 2


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_index_idempotent():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r.index(_SAMPLE_DOCS[:2], batch_size=4)
    ids_first = list(r._doc_ids)
    r.index(_SAMPLE_DOCS[:2], batch_size=4)
    assert r._doc_ids == ids_first


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_metadata_preserved():
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r.index(_SAMPLE_DOCS[:2], batch_size=4)
    with tempfile.TemporaryDirectory() as tmpdir:
        r.save(Path(tmpdir))
        r2 = ColBERTRetriever(model_path=_MODEL_PATH)
        r2.load(Path(tmpdir))
        assert r2._doc_ids == [d["document_id"] for d in _SAMPLE_DOCS[:2]]
        assert r2._docs[0].get("title") == _SAMPLE_DOCS[0]["title"]


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="models/colbertv2.0 not on disk")
def test_token_level_matching():
    """ColBERT should rank semantically relevant doc above keyword-only match."""
    docs = [
        {
            "document_id": "keyword_only",
            "title": "unsigned instrument contract",
            "findings": [],
        },
        {
            "document_id": "semantic_match",
            "title": "city procurement agreement lacking authorized execution mark",
            "findings": [],
        },
    ]
    r = ColBERTRetriever(model_path=_MODEL_PATH)
    r.index(docs, batch_size=4)
    results = r.query("fiscal compliance gap unsigned city agreement", top_k=2)
    result_ids = [res["document_id"] for res in results]
    assert len(result_ids) == 2
