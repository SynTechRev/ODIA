"""Tests for the RAG context builder.

Tests context assembly, token budgeting, source attribution,
and per-type formatting.
"""

from oraculus_di_auditor.rag import BuiltContext, ContextBuilder, RetrievalResult

# -- helpers -----------------------------------------------------------------


def _doc_result(doc_id="DOC-001", score=0.85):
    return RetrievalResult(
        content="The contract was executed on March 15, 2023.",
        source_type="document",
        source_id=doc_id,
        score=score,
        metadata={"title": "Vendor Contract"},
    )


def _finding_result(finding_id="F-003", score=0.90):
    return RetrievalResult(
        content=(
            "Pre-authorization execution detected:"
            " contract executed 14 days before council authorization."
        ),
        source_type="finding",
        source_id=finding_id,
        score=score,
        metadata={
            "severity": "critical",
            "layer": "procurement_timeline",
        },
    )


def _analysis_result(analysis_id="A-001", score=0.75):
    return RetrievalResult(
        content=(
            "3 surveillance capabilities deployed" " without governance framework."
        ),
        source_type="analysis",
        source_id=analysis_id,
        score=score,
        metadata={
            "jurisdiction": "City of Example",
            "detector": "governance_gap",
        },
    )


# -- test: build_context produces formatted string with attributions ---------


def test_build_context_with_attributions():
    builder = ContextBuilder(max_tokens=4000)
    results = [_doc_result(), _finding_result(), _analysis_result()]
    ctx = builder.build_context(results, query="contract issues")

    assert isinstance(ctx, BuiltContext)
    assert "[Source: DOC-001 | Type: document" in ctx.context_text
    assert (
        "[Finding: F-003 | Severity: critical" " | Detector: procurement_timeline]"
    ) in ctx.context_text
    assert (
        "[Analysis: City of Example | Detector: governance_gap]"
    ) in ctx.context_text
    assert ctx.tokens_used > 0
    assert ctx.tokens_remaining >= 0


# -- test: token budget is respected ----------------------------------------


def test_token_budget_respected():
    builder = ContextBuilder(max_tokens=30)
    results = [_doc_result(), _finding_result(), _analysis_result()]
    ctx = builder.build_context(results, query="test")

    assert ctx.tokens_used <= 30
    assert len(ctx.sources_used) < len(results)
    assert ctx.tokens_remaining >= 0


# -- test: sources_used only includes results that fit ----------------------


def test_sources_used_matches_context():
    builder = ContextBuilder(max_tokens=50)
    results = [_doc_result(), _finding_result(), _analysis_result()]
    ctx = builder.build_context(results, query="test")

    for source in ctx.sources_used:
        assert source.source_id in ctx.context_text

    excluded_ids = {r.source_id for r in results} - {
        s.source_id for s in ctx.sources_used
    }
    for eid in excluded_ids:
        assert eid not in ctx.context_text


# -- test: different source types get different formatting -------------------


def test_source_type_formatting():
    builder = ContextBuilder()

    doc_fmt = builder.format_document_context(_doc_result())
    assert "[Source:" in doc_fmt
    assert "Type: document" in doc_fmt

    finding_fmt = builder.format_finding_context(_finding_result())
    assert "[Finding:" in finding_fmt
    assert "Severity: critical" in finding_fmt
    assert "Detector: procurement_timeline" in finding_fmt

    analysis_fmt = builder.format_analysis_context(_analysis_result())
    assert "[Analysis:" in analysis_fmt
    assert "City of Example" in analysis_fmt
    assert "Detector: governance_gap" in analysis_fmt


# -- test: empty results produce valid empty context -------------------------


def test_empty_results():
    builder = ContextBuilder()
    ctx = builder.build_context([], query="anything")

    assert ctx.context_text == ""
    assert ctx.sources_used == []
    assert ctx.tokens_used == 0
    assert ctx.tokens_remaining == builder.max_tokens


# -- test: estimate_tokens ---------------------------------------------------


def test_estimate_tokens():
    builder = ContextBuilder()
    assert builder.estimate_tokens("") == 1  # min 1
    assert builder.estimate_tokens("abcd") == 1
    assert builder.estimate_tokens("a" * 400) == 100


# -- test: score shown in document header ------------------------------------


def test_score_in_document_header():
    builder = ContextBuilder()
    fmt = builder.format_document_context(_doc_result(score=0.92))
    assert "Score: 0.92" in fmt
