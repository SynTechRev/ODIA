"""Tests for the main RAG service.

Tests corpus loading, query routing, LLM-less querying, and status reporting.
"""

from unittest.mock import MagicMock

from oraculus_di_auditor.rag import RAGResponse, RAGService

# -- sample data -------------------------------------------------------------


def _docs():
    return [
        {
            "id": "doc-001",
            "title": "Budget Resolution",
            "text": (
                "Annual budget allocates funds" " for infrastructure and public safety."
            ),
        },
        {
            "id": "doc-002",
            "title": "Vendor Contract",
            "text": ("Procurement contract between" " the city and Acme Services Inc."),
        },
    ]


def _findings():
    return [
        {
            "id": "fiscal:hash-001",
            "issue": "Missing provenance hash",
            "severity": "high",
            "layer": "fiscal",
            "details": {"document_id": "doc-001"},
        },
        {
            "id": "procurement:gap-001",
            "issue": "Contract signed before approval",
            "severity": "critical",
            "layer": "procurement",
            "details": {"document_id": "doc-002"},
        },
    ]


def _analysis():
    return [
        {
            "id": "analysis-001",
            "summary": "Fiscal irregularities in budget",
        },
    ]


# -- test: load_corpus indexes and returns counts ---------------------------


def test_load_corpus_returns_counts():
    svc = RAGService()
    counts = svc.load_corpus(
        documents=_docs(),
        findings=_findings(),
        analysis_results=_analysis(),
    )

    assert counts["documents"] == 2
    assert counts["findings"] == 2
    assert counts["analysis"] == 1


# -- test: query_without_llm returns retrieval results -----------------------


def test_query_without_llm_returns_results():
    svc = RAGService()
    svc.load_corpus(documents=_docs(), findings=_findings())

    result = svc.query_without_llm("budget allocation")

    assert result["query"] == "budget allocation"
    assert result["query_type"] in {
        "factual",
        "analytical",
        "comparative",
        "compliance",
        "recommendation",
        "vendor",
        "temporal",
    }
    assert isinstance(result["retrieved_sources"], list)
    assert "message" in result


# -- test: query_without_llm includes context preview ------------------------


def test_query_without_llm_context_preview():
    svc = RAGService()
    svc.load_corpus(documents=_docs())

    result = svc.query_without_llm("budget funds")

    assert "context_preview" in result
    assert isinstance(result["context_preview"], str)
    assert "prompt_that_would_be_used" in result


# -- test: get_status returns indexed counts ---------------------------------


def test_get_status():
    svc = RAGService()
    status = svc.get_status()

    assert status["indexed"]["documents"] == 0
    assert status["indexed"]["findings"] == 0
    assert status["indexed"]["analysis"] == 0
    assert "llm_available" in status

    svc.load_corpus(documents=_docs())
    status = svc.get_status()
    assert status["indexed"]["documents"] == 2


# -- test: query with mock LLM returns RAGResponse ---------------------------


def test_query_with_mock_llm():
    svc = RAGService()
    svc.load_corpus(documents=_docs(), findings=_findings())

    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.generate.return_value = "The budget allocates funds for infrastructure."
    svc._llm = mock_llm
    svc._llm_model_name = "mock-model"

    resp = svc.query("What does the budget allocate?")

    assert isinstance(resp, RAGResponse)
    assert "budget" in resp.answer.lower()
    assert resp.query == "What does the budget allocate?"
    assert resp.model_used == "mock-model"
    assert isinstance(resp.sources, list)
    mock_llm.generate.assert_called_once()


# -- test: empty corpus returns appropriate message --------------------------


def test_empty_corpus_query():
    svc = RAGService()
    resp = svc.query("anything at all")

    assert isinstance(resp, RAGResponse)
    assert any(
        phrase in resp.answer
        for phrase in ("No LLM", "0 sources", "LLM generation failed")
    )
    assert resp.sources == []


# -- test: source_filter limits retrieval scope ------------------------------


def test_source_filter_limits_scope():
    svc = RAGService()
    svc.load_corpus(documents=_docs(), findings=_findings())

    mock_llm = MagicMock()
    mock_llm.is_available.return_value = True
    mock_llm.generate.return_value = "Filtered answer."
    svc._llm = mock_llm

    resp = svc.query("budget", source_filter="documents")
    for src in resp.sources:
        assert src.source_type == "document"


# -- test: service initializes with defaults ---------------------------------


def test_default_initialization():
    svc = RAGService()

    assert svc._engine is not None
    assert svc._context_builder is not None
    assert svc._prompt_router is not None
    status = svc.get_status()
    assert status["indexed"]["documents"] == 0
