"""Tests for Day 04: R.A.I.A. v0 LangGraph agent (agents/raia_v0.py).

Unit tests use a mock LLM provider and a mock HybridRetriever so they run
without GPU, downloaded models, or a live Ollama/API endpoint.
Integration test (test_hybrid_retriever_integration) is skipped unless
models/bge-m3 exists on disk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from oraculus_di_auditor.agents.raia_v0 import (
    RAIAState,
    _extract_citations,
    _parse_analyze_response,
    _parse_deepen_response,
    analyze_node,
    cross_reference_node,
    deepen_node,
    finalize_node,
    run_raia,
    verify_node,
)
from oraculus_di_auditor.llm_providers import BaseLLMProvider

_MODELS_DIR = Path(__file__).parent.parent / "models"
_BGE_M3_AVAILABLE = (_MODELS_DIR / "bge-m3").exists()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_state(**overrides: Any) -> RAIAState:
    base: RAIAState = {
        "query": "unsigned contracts in Fresno city",
        "max_iterations": 3,
        "confidence_threshold": 0.75,
        "iteration": 0,
        "sub_questions": [],
        "analytical_angle": "",
        "retrieved_passages": [],
        "citation_pool": [],
        "deepened_findings": "",
        "confidence": 0.0,
        "citation_validity": {},
        "verification_notes": "",
        "reflection": None,
        "final_answer": "",
        "halt_reason": "",
        "trace": [],
    }
    base.update(overrides)
    return base


class _MockProvider(BaseLLMProvider):
    """Provider that returns a fixed response for every generate() call."""

    def __init__(self, responses: list[str] | None = None) -> None:
        self._responses = list(responses or [])
        self._call_count = 0

    def generate(self, prompt: str, context: str, **kwargs: Any) -> str:
        if self._responses:
            idx = min(self._call_count, len(self._responses) - 1)
            resp = self._responses[idx]
        else:
            resp = (
                "SUB_QUESTIONS:\n1. Are there unsigned instruments?\n\n"
                "ANALYTICAL_ANGLE: Signature gap analysis\n"
                "This corpus contains many gaps. (doc_id:abc123)\n"
                '{"confidence": 0.85}'
            )
        self._call_count += 1
        return resp

    def is_available(self) -> bool:
        return True


def _mock_retriever(doc_ids: list[str] | None = None) -> MagicMock:
    mock = MagicMock()
    ids = doc_ids or ["abc123", "def456", "ghi789"]
    mock.query.return_value = [
        {"document_id": d, "title": f"Doc {d}", "score": 1.0, "findings": []}
        for d in ids
    ]
    return mock


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------


def test_citation_extraction_basic() -> None:
    text = "Analysis shows (doc_id:abc123) and (doc_id:def456) are relevant."
    result = _extract_citations(text)
    assert set(result) == {"abc123", "def456"}


def test_citation_extraction_dedup() -> None:
    text = "(doc_id:abc123) repeated (doc_id:abc123) again"
    result = _extract_citations(text)
    assert result == ["abc123"]


def test_citation_extraction_empty() -> None:
    assert _extract_citations("no citations here") == []


def test_parse_analyze_response_well_formed() -> None:
    response = (
        "SUB_QUESTIONS:\n"
        "1. Are contracts missing signatures?\n"
        "2. What dollar amounts are affected?\n\n"
        "ANALYTICAL_ANGLE: Signature gap fiscal impact analysis"
    )
    sqs, angle = _parse_analyze_response(response)
    assert len(sqs) == 2
    assert "signatures" in sqs[0].lower()
    assert "fiscal" in angle.lower()


def test_parse_analyze_response_fallback_on_malformed() -> None:
    sqs, angle = _parse_analyze_response(
        "This is a free-form response with no structure."
    )
    assert len(sqs) >= 1
    assert isinstance(angle, str) and len(angle) > 0


def test_parse_deepen_response_extracts_confidence() -> None:
    response = (
        'Multiple unsigned instruments found. (doc_id:abc123)\n{"confidence": 0.88}'
    )
    findings, confidence = _parse_deepen_response(response)
    assert abs(confidence - 0.88) < 0.001
    assert "(doc_id:abc123)" in findings
    assert "confidence" not in findings


def test_parse_deepen_response_clamps_confidence() -> None:
    _, conf_high = _parse_deepen_response('text {"confidence": 1.5}')
    _, conf_low = _parse_deepen_response('text {"confidence": -0.5}')
    assert conf_high == 1.0
    assert conf_low == 0.0


def test_parse_deepen_response_plain_confidence_fallback() -> None:
    findings, conf = _parse_deepen_response(
        "Analysis of documents.\nCONFIDENCE: 0.85\nSUMMARY: Issues found."
    )
    assert abs(conf - 0.85) < 0.001
    assert "CONFIDENCE" not in findings.upper()


# ---------------------------------------------------------------------------
# Unit tests: individual nodes
# ---------------------------------------------------------------------------


def test_analyze_node_populates_state() -> None:
    provider = _MockProvider(
        ["SUB_QUESTIONS:\n1. Missing signatures?\n\nANALYTICAL_ANGLE: Gap analysis"]
    )
    state = _empty_state()
    result = analyze_node(state, provider)
    assert len(result["sub_questions"]) >= 1
    assert result["analytical_angle"] != ""
    assert any(e["node"] == "analyze" for e in result["trace"])


def test_analyze_node_consumes_reflection() -> None:
    provider = _MockProvider(
        ["SUB_QUESTIONS:\n1. Deeper question?\n\nANALYTICAL_ANGLE: Refined lens"]
    )
    state = _empty_state(reflection="Previous attempt was too broad.")
    prompt_captured: list[str] = []
    original_generate = provider.generate

    def capturing_generate(prompt: str, context: str, **kw: Any) -> str:
        prompt_captured.append(prompt)
        return original_generate(prompt, context, **kw)

    provider.generate = capturing_generate
    analyze_node(state, provider)
    assert "PREVIOUS ATTEMPT REFLECTION" in prompt_captured[0]


def test_cross_reference_node_deduplicates() -> None:
    retriever = _mock_retriever(["doc1", "doc2", "doc1"])
    state = _empty_state(sub_questions=["q1", "q2"])
    result = cross_reference_node(state, retriever, k=5)
    assert len(result["citation_pool"]) == len(set(result["citation_pool"]))
    assert any(e["node"] == "cross_reference" for e in result["trace"])


def test_cross_reference_node_citation_pool_grows_with_sub_questions() -> None:
    retriever = MagicMock()
    retriever.query.side_effect = [
        [{"document_id": "a", "title": "A", "score": 1.0, "findings": []}],
        [{"document_id": "b", "title": "B", "score": 1.0, "findings": []}],
    ]
    state = _empty_state(sub_questions=["question one", "question two"])
    result = cross_reference_node(state, retriever, k=1)
    assert len(result["citation_pool"]) == 2


def test_deepen_node_sets_confidence() -> None:
    provider = _MockProvider(
        ['Analysis of findings. (doc_id:abc123)\n{"confidence": 0.91}']
    )
    state = _empty_state(
        sub_questions=["Are there gaps?"],
        analytical_angle="gap analysis",
        retrieved_passages=[
            {"document_id": "abc123", "title": "Doc A", "score": 1.0, "findings": []}
        ],
    )
    result = deepen_node(state, provider)
    assert abs(result["confidence"] - 0.91) < 0.001
    assert "(doc_id:abc123)" in result["deepened_findings"]


def test_verify_node_passes_on_valid_citation_and_confidence() -> None:
    corpus_ids = {"abc123", "def456"}
    state = _empty_state(
        deepened_findings="Analysis. (doc_id:abc123)",
        confidence=0.80,
        confidence_threshold=0.75,
    )
    result = verify_node(state, corpus_ids)
    assert result["reflection"] is None
    assert result["citation_validity"] == {"abc123": True}
    assert result["iteration"] == 1


def test_verify_node_sets_reflection_on_invalid_citation() -> None:
    corpus_ids = {"abc123"}
    state = _empty_state(
        deepened_findings="Analysis. (doc_id:nonexistent)",
        confidence=0.90,
        confidence_threshold=0.75,
    )
    result = verify_node(state, corpus_ids)
    assert result["reflection"] is not None
    assert "nonexistent" in result["reflection"]


def test_verify_node_sets_reflection_on_low_confidence() -> None:
    corpus_ids = {"abc123"}
    state = _empty_state(
        deepened_findings="Analysis. (doc_id:abc123)",
        confidence=0.50,
        confidence_threshold=0.75,
    )
    result = verify_node(state, corpus_ids)
    assert result["reflection"] is not None
    assert "0.50" in result["reflection"] or "threshold" in result["reflection"].lower()


def test_finalize_node_halt_reason_verify_passed() -> None:
    state = _empty_state(
        deepened_findings="Final analysis.",
        confidence=0.90,
        reflection=None,
        iteration=1,
    )
    result = finalize_node(state)
    assert result["halt_reason"] == "verify_passed"
    assert result["final_answer"] == "Final analysis."


def test_finalize_node_halt_reason_max_iterations() -> None:
    state = _empty_state(
        deepened_findings="Partial analysis.",
        reflection="Still not confident enough.",
        iteration=3,
    )
    result = finalize_node(state)
    assert result["halt_reason"] == "max_iterations"


# ---------------------------------------------------------------------------
# Integration tests: full graph execution
# ---------------------------------------------------------------------------


def test_state_schema_initialization() -> None:
    state = _empty_state()
    assert state["query"] == "unsigned contracts in Fresno city"
    assert state["iteration"] == 0
    assert state["trace"] == []
    assert state["reflection"] is None


def test_single_cycle_execution_halts_after_one_cycle() -> None:
    analyze_resp = (
        "SUB_QUESTIONS:\n1. Are there unsigned instruments?\n\n"
        "ANALYTICAL_ANGLE: Signature gap analysis"
    )
    deepen_resp = 'Unsigned instruments found. (doc_id:abc123)\n{"confidence": 0.90}'
    provider = _MockProvider([analyze_resp, deepen_resp])
    retriever = _mock_retriever(["abc123"])
    corpus_ids = {"abc123"}

    result = run_raia(
        query="unsigned contracts",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=3,
        confidence_threshold=0.75,
    )
    assert result["halt_reason"] == "verify_passed"
    assert result["iteration"] == 1
    node_names = [e["node"] for e in result["trace"]]
    assert node_names == ["analyze", "cross_reference", "deepen", "verify", "finalize"]


def test_max_iteration_halt() -> None:
    analyze_resp = "SUB_QUESTIONS:\n1. Any issues?\n\nANALYTICAL_ANGLE: overview"
    deepen_resp = 'Low confidence finding.\n{"confidence": 0.30}'
    provider = _MockProvider([analyze_resp, deepen_resp])
    retriever = _mock_retriever()
    corpus_ids: set[str] = set()

    result = run_raia(
        query="some query",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=2,
        confidence_threshold=0.75,
    )
    assert result["halt_reason"] == "max_iterations"
    assert result["iteration"] == 2


def test_loop_on_invalid_citation() -> None:
    analyze_resp = "SUB_QUESTIONS:\n1. Any issues?\n\nANALYTICAL_ANGLE: overview"
    deepen_bad = 'Analysis. (doc_id:ghost_id)\n{"confidence": 0.90}'
    deepen_good = 'Analysis. (doc_id:real_id)\n{"confidence": 0.90}'
    provider = _MockProvider([analyze_resp, deepen_bad, analyze_resp, deepen_good])
    retriever = _mock_retriever(["real_id"])
    corpus_ids = {"real_id"}

    result = run_raia(
        query="some query",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=3,
        confidence_threshold=0.75,
    )
    assert result["halt_reason"] == "verify_passed"
    assert result["iteration"] == 2


def test_loop_on_low_confidence() -> None:
    analyze_resp = "SUB_QUESTIONS:\n1. Any issues?\n\nANALYTICAL_ANGLE: overview"
    deepen_low = 'Analysis. (doc_id:abc123)\n{"confidence": 0.50}'
    deepen_high = 'Deeper analysis. (doc_id:abc123)\n{"confidence": 0.85}'
    provider = _MockProvider([analyze_resp, deepen_low, analyze_resp, deepen_high])
    retriever = _mock_retriever(["abc123"])
    corpus_ids = {"abc123"}

    result = run_raia(
        query="some query",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=3,
        confidence_threshold=0.75,
    )
    assert result["halt_reason"] == "verify_passed"
    assert result["iteration"] == 2


def test_trace_captures_each_node() -> None:
    analyze_resp = "SUB_QUESTIONS:\n1. Any issues?\n\nANALYTICAL_ANGLE: overview"
    deepen_resp = 'Findings. (doc_id:abc123)\n{"confidence": 0.90}'
    provider = _MockProvider([analyze_resp, deepen_resp])
    retriever = _mock_retriever(["abc123"])
    corpus_ids = {"abc123"}

    result = run_raia(
        query="q",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=3,
        confidence_threshold=0.75,
    )
    node_names = [e["node"] for e in result["trace"]]
    assert "analyze" in node_names
    assert "cross_reference" in node_names
    assert "deepen" in node_names
    assert "verify" in node_names
    assert "finalize" in node_names
    for entry in result["trace"]:
        if entry["node"] != "finalize":
            assert "iteration" in entry


# ---------------------------------------------------------------------------
# Integration test: real HybridRetriever (requires models on disk)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _BGE_M3_AVAILABLE,
    reason="models/bge-m3 not on disk",
)
def test_hybrid_retriever_integration() -> None:
    import json

    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    docs_path = (
        Path(__file__).parent.parent / "data" / "eval" / "fresno_signature_1k.jsonl"
    )
    if not docs_path.exists():
        pytest.skip("data/eval/fresno_signature_1k.jsonl not on disk")

    docs = []
    with open(docs_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    sample = docs[:50]

    retriever = HybridRetriever(
        model_dir=Path(__file__).parent.parent / "models",
        use_reranker=False,
    )
    retriever.index(sample)

    corpus_ids = {d["document_id"] for d in sample}
    analyze_resp = (
        "SUB_QUESTIONS:\n1. Which contracts lack signatures?\n\n"
        "ANALYTICAL_ANGLE: Signature gap audit"
    )
    deepen_resp = (
        f'Gaps found. (doc_id:{next(iter(corpus_ids))})\n{{"confidence": 0.80}}'
    )
    provider = _MockProvider([analyze_resp, deepen_resp])

    result = run_raia(
        query="unsigned instruments in the corpus",
        retriever=retriever,
        provider=provider,
        corpus_ids=corpus_ids,
        max_iterations=2,
        confidence_threshold=0.75,
    )
    assert result["halt_reason"] in {"verify_passed", "max_iterations"}
    assert len(result["trace"]) >= 5
    assert len(result["citation_pool"]) > 0
