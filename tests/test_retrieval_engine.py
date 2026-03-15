"""Tests for the enhanced retrieval engine.

Tests multi-source indexing and search across documents, findings,
and analysis results.
"""

from oraculus_di_auditor.rag import RetrievalEngine, RetrievalResult

# -- fixtures ----------------------------------------------------------------


def _sample_documents():
    return [
        {
            "id": "doc-001",
            "title": "City Budget Resolution 2026",
            "text": (
                "The annual budget resolution allocates"
                " funds for infrastructure and public safety."
            ),
        },
        {
            "id": "doc-002",
            "title": "Vendor Contract Agreement",
            "text": (
                "This procurement contract establishes terms"
                " between the city and the vendor for services."
            ),
        },
        {
            "id": "doc-003",
            "title": "Meeting Minutes December 2025",
            "text": (
                "Council meeting minutes covering zoning"
                " amendments and ordinance discussions."
            ),
        },
    ]


def _sample_findings():
    return [
        {
            "id": "fiscal:missing-hash-001",
            "issue": "Document lacks provenance hash",
            "severity": "high",
            "layer": "fiscal",
            "details": {"document_id": "doc-001"},
        },
        {
            "id": "procurement:timeline-gap",
            "issue": "Vendor contract signed before approval date",
            "severity": "high",
            "layer": "procurement",
            "details": {"document_id": "doc-002", "gap_days": 14},
        },
        {
            "id": "constitutional:missing-notice",
            "issue": "Public notice period not met for ordinance",
            "severity": "medium",
            "layer": "constitutional",
            "details": {"document_id": "doc-003"},
        },
        {
            "id": "fiscal:duplicate-entry",
            "issue": "Duplicate budget line item detected",
            "severity": "low",
            "layer": "fiscal",
            "details": {"document_id": "doc-001", "line": 42},
        },
    ]


def _sample_analysis_results():
    return [
        {
            "id": "analysis-001",
            "summary": "Fiscal analysis found irregularities in budget allocations",
            "findings": ["fiscal:missing-hash-001", "fiscal:duplicate-entry"],
        },
        {
            "id": "analysis-002",
            "summary": "Procurement timeline analysis detected contract approval gaps",
            "findings": ["procurement:timeline-gap"],
        },
    ]


# -- test: index documents and search returns results -----------------------


def test_index_documents_and_search():
    engine = RetrievalEngine()
    count = engine.index_documents(_sample_documents())
    assert count == 3

    results = engine.search("budget funds infrastructure")
    assert len(results) > 0
    assert all(isinstance(r, RetrievalResult) for r in results)
    assert results[0].source_type == "document"


# -- test: index findings and search by severity ----------------------------


def test_index_findings_and_search_by_severity():
    engine = RetrievalEngine()
    engine.index_findings(_sample_findings())

    high = engine.search_by_severity("high")
    assert len(high) == 2
    assert all(r.source_type == "finding" for r in high)
    assert all(r.metadata.get("severity") == "high" for r in high)

    medium = engine.search_by_severity("medium")
    assert len(medium) == 1

    low = engine.search_by_severity("low")
    assert len(low) == 1


# -- test: search_by_detector filters correctly ------------------------------


def test_search_by_detector():
    engine = RetrievalEngine()
    engine.index_findings(_sample_findings())

    fiscal = engine.search_by_detector("fiscal")
    assert len(fiscal) == 2
    assert all("fiscal" in r.source_id for r in fiscal)

    procurement = engine.search_by_detector("procurement")
    assert len(procurement) == 1

    constitutional = engine.search_by_detector("constitutional")
    assert len(constitutional) == 1


# -- test: source_filter limits search scope ---------------------------------


def test_source_filter_limits_scope():
    engine = RetrievalEngine()
    engine.index_documents(_sample_documents())
    engine.index_findings(_sample_findings())
    engine.index_analysis_results(_sample_analysis_results())

    docs_only = engine.search("budget", source_filter="documents")
    assert all(r.source_type == "document" for r in docs_only)

    findings_only = engine.search("provenance hash", source_filter="findings")
    assert all(r.source_type == "finding" for r in findings_only)

    analysis_only = engine.search("fiscal irregularities", source_filter="analysis")
    assert all(r.source_type == "analysis" for r in analysis_only)


# -- test: empty index returns empty results ---------------------------------


def test_empty_index_returns_empty():
    engine = RetrievalEngine()

    assert engine.search("anything") == []
    assert engine.search_by_detector("fiscal") == []
    assert engine.search_by_severity("high") == []


# -- test: top_k limits result count ----------------------------------------


def test_top_k_limits_results():
    engine = RetrievalEngine()
    engine.index_documents(_sample_documents())
    engine.index_findings(_sample_findings())
    engine.index_analysis_results(_sample_analysis_results())

    results = engine.search("budget contract", top_k=2)
    assert len(results) <= 2

    results_all = engine.search("budget contract", top_k=100)
    assert len(results_all) <= 9  # 3 docs + 4 findings + 2 analysis


# -- test: results are sorted by score descending ---------------------------


def test_results_sorted_by_score_descending():
    engine = RetrievalEngine()
    engine.index_documents(_sample_documents())
    engine.index_findings(_sample_findings())

    results = engine.search("budget fiscal provenance")
    if len(results) > 1:
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# -- test: search_by_severity top_k -----------------------------------------


def test_search_by_severity_top_k():
    engine = RetrievalEngine()
    engine.index_findings(_sample_findings())

    results = engine.search_by_severity("high", top_k=1)
    assert len(results) == 1


# -- test: search_by_detector top_k -----------------------------------------


def test_search_by_detector_top_k():
    engine = RetrievalEngine()
    engine.index_findings(_sample_findings())

    results = engine.search_by_detector("fiscal", top_k=1)
    assert len(results) == 1


# -- test: index_analysis_results -------------------------------------------


def test_index_analysis_results():
    engine = RetrievalEngine()
    count = engine.index_analysis_results(_sample_analysis_results())
    assert count == 2

    results = engine.search("fiscal irregularities budget")
    assert len(results) > 0


# -- test: RetrievalResult fields -------------------------------------------


def test_retrieval_result_fields():
    engine = RetrievalEngine()
    engine.index_documents(_sample_documents())

    results = engine.search("budget")
    assert len(results) > 0
    r = results[0]
    assert isinstance(r.content, str)
    assert isinstance(r.source_type, str)
    assert isinstance(r.source_id, str)
    assert isinstance(r.score, float)
    assert isinstance(r.metadata, dict)
