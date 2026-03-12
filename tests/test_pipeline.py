"""Tests for unified analysis pipeline (Phase 4).

Validates the run_full_analysis function and its integration with all detectors.
"""

from __future__ import annotations

from oraculus_di_auditor.analysis.pipeline import run_full_analysis


def test_run_full_analysis_minimal():
    """Test pipeline with minimal valid input."""
    result = run_full_analysis(
        document_text="This is a test document.",
        metadata={"title": "Test Document"},
    )

    # Verify result structure
    assert isinstance(result, dict)
    assert "metadata" in result
    assert "findings" in result
    assert "severity_score" in result
    assert "lattice_score" in result
    assert "coherence_bonus" in result
    assert "flags" in result
    assert "summary" in result
    assert "timestamp" in result

    # Verify findings structure
    assert "fiscal" in result["findings"]
    assert "constitutional" in result["findings"]
    assert "surveillance" in result["findings"]
    assert isinstance(result["findings"]["fiscal"], list)
    assert isinstance(result["findings"]["constitutional"], list)
    assert isinstance(result["findings"]["surveillance"], list)

    # Verify score ranges
    assert 0.0 <= result["severity_score"] <= 1.0
    assert 0.0 <= result["lattice_score"] <= 1.0
    assert 0.0 <= result["coherence_bonus"] <= 1.0


def test_run_full_analysis_with_metadata():
    """Test pipeline with comprehensive metadata."""
    metadata = {
        "document_id": "test-doc-001",
        "title": "Test Act 2025",
        "document_type": "act",
        "jurisdiction": "federal",
        "hash": "abc123",
    }

    result = run_full_analysis(
        document_text="There is appropriated $1,000,000 for operations.",
        metadata=metadata,
    )

    # Verify metadata is preserved
    assert result["metadata"]["document_id"] == "test-doc-001"
    assert result["metadata"]["title"] == "Test Act 2025"
    assert result["metadata"]["document_type"] == "act"


def test_run_full_analysis_generates_document_id():
    """Test that pipeline generates document_id if not provided."""
    result = run_full_analysis(
        document_text="Test content",
        metadata={"title": "Test"},
    )

    assert "document_id" in result["metadata"]
    assert result["metadata"]["document_id"].startswith("doc-")


def test_run_full_analysis_clean_document():
    """Test pipeline with clean document (no anomalies expected)."""
    result = run_full_analysis(
        document_text="There is appropriated $1,000,000 for the fiscal year 2025.",
        metadata={
            "title": "Budget Act 2025",
            "hash": "abc123",
        },
    )

    # Clean document should have high lattice score
    assert result["lattice_score"] >= 0.9
    assert result["severity_score"] < 0.5
    assert len(result["flags"]) == 0
    assert "No anomalies" in result["summary"] or result["lattice_score"] > 0.5


def test_run_full_analysis_fiscal_anomaly():
    """Test pipeline detects fiscal anomalies."""
    result = run_full_analysis(
        document_text="The program receives $1,000,000 for operations.",
        metadata={
            "title": "Budget Document",
            "hash": "abc123",
        },
    )

    # Should detect fiscal amount without appropriation
    assert len(result["findings"]["fiscal"]) > 0
    assert any(
        "amount-without-appropriation" in a.get("id", "")
        for a in result["findings"]["fiscal"]
    )


def test_run_full_analysis_missing_provenance():
    """Test pipeline detects missing provenance."""
    result = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test"},
    )

    # Should detect missing provenance hash
    assert len(result["findings"]["fiscal"]) > 0
    assert any(
        "missing-provenance" in a.get("id", "") for a in result["findings"]["fiscal"]
    )


def test_run_full_analysis_constitutional_anomaly():
    """Test pipeline detects constitutional anomalies."""
    result = run_full_analysis(
        document_text=(
            "The Secretary may determine such rules as necessary. "
            "The Administrator shall prescribe regulations in his discretion."
        ),
        metadata={
            "title": "Regulatory Act",
            "hash": "abc123",
        },
    )

    # Should detect broad delegation patterns
    findings = result["findings"]["constitutional"]
    assert len(findings) > 0


def test_run_full_analysis_surveillance_anomaly():
    """Test pipeline detects surveillance anomalies."""
    result = run_full_analysis(
        document_text=(
            "The agency shall contract with a private vendor for surveillance "
            "and monitoring services including facial recognition."
        ),
        metadata={
            "title": "Security Act",
            "hash": "abc123",
        },
    )

    # Should detect surveillance outsourcing
    findings = result["findings"]["surveillance"]
    assert len(findings) > 0


def test_run_full_analysis_severity_scoring():
    """Test that severity score increases with anomalies."""
    # Clean document
    result_clean = run_full_analysis(
        document_text="There is appropriated $1,000,000.",
        metadata={"title": "Test", "hash": "abc123"},
    )

    # Document with anomalies
    result_anomalies = run_full_analysis(
        document_text="The program receives $1,000,000 for operations.",
        metadata={"title": "Test", "hash": "abc123"},
    )

    # Severity should be higher for document with anomalies
    assert result_anomalies["severity_score"] >= result_clean["severity_score"]


def test_run_full_analysis_lattice_score_with_provenance():
    """Test that lattice score is better with good provenance."""
    # Without hash
    result_no_hash = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test"},
    )

    # With hash
    result_with_hash = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test", "hash": "abc123"},
    )

    # Lattice score should be higher with provenance hash
    assert result_with_hash["lattice_score"] >= result_no_hash["lattice_score"]


def test_run_full_analysis_flags_extraction():
    """Test that high-severity anomalies are extracted as flags."""
    result = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test"},  # Missing hash triggers high-severity anomaly
    )

    # Should have flags for high-severity issues
    total_high_severity = sum(
        1
        for findings_list in result["findings"].values()
        for a in findings_list
        if a.get("severity") == "high"
    )

    assert len(result["flags"]) == total_high_severity


def test_run_full_analysis_summary_generation():
    """Test summary string generation."""
    result = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test"},
    )

    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0
    # Summary should contain some relevant information
    assert (
        "anomal" in result["summary"].lower()
        or "confidence" in result["summary"].lower()
    )


def test_run_full_analysis_timestamp_format():
    """Test that timestamp is in ISO 8601 UTC format."""
    result = run_full_analysis(
        document_text="Test content.",
        metadata={"title": "Test"},
    )

    # Should be parseable as ISO 8601
    from datetime import datetime

    timestamp = datetime.fromisoformat(result["timestamp"].replace("Z", "+00:00"))
    assert timestamp is not None


def test_run_full_analysis_empty_text():
    """Test pipeline handles empty text gracefully."""
    result = run_full_analysis(
        document_text="",
        metadata={"title": "Empty Document"},
    )

    # Should still return valid structure
    assert isinstance(result, dict)
    assert "findings" in result
    assert "severity_score" in result


def test_run_full_analysis_coherence_bonus():
    """Test coherence bonus calculation."""
    # Minimal metadata
    result_minimal = run_full_analysis(
        document_text="Test content.",
        metadata={},
    )

    # Complete metadata with provenance
    result_complete = run_full_analysis(
        document_text="Test content.",
        metadata={
            "title": "Complete Document",
            "document_type": "act",
            "hash": "abc123",
        },
    )

    # Coherence bonus should be higher with complete metadata
    assert result_complete["coherence_bonus"] >= result_minimal["coherence_bonus"]
