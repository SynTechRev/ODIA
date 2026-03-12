"""Tests for provenance tracking and reference graph building."""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.provenance import ProvenanceTracker


def test_provenance_tracker_initialization():
    """Test that ProvenanceTracker initializes correctly."""
    tracker = ProvenanceTracker()
    assert tracker.documents == {}
    assert tracker.reference_graph == {}


def test_add_document():
    """Test adding a document to the tracker."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "test-001",
        "title": "Test Document",
        "document_type": "act",
        "provenance": {
            "source": "test_source",
            "hash": "abc123",
            "verified_on": datetime.now(UTC).isoformat(),
        },
    }

    doc_id = tracker.add_document(document)

    assert doc_id == "test-001"
    assert "test-001" in tracker.documents
    assert tracker.documents["test-001"]["title"] == "Test Document"


def test_add_document_without_id():
    """Test that adding a document without ID raises ValueError."""
    tracker = ProvenanceTracker()

    document = {
        "title": "No ID Document",
    }

    try:
        tracker.add_document(document)
        raise AssertionError("Expected ValueError")
    except ValueError as e:
        assert "document_id" in str(e)


def test_get_document():
    """Test retrieving a document by ID."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "test-002",
        "title": "Retrievable Document",
        "document_type": "bill",
        "provenance": {"source": "test", "hash": "xyz", "verified_on": "2023-01-01"},
    }

    tracker.add_document(document)
    retrieved = tracker.get_document("test-002")

    assert retrieved is not None
    assert retrieved["title"] == "Retrievable Document"


def test_get_nonexistent_document():
    """Test retrieving a non-existent document returns None."""
    tracker = ProvenanceTracker()
    retrieved = tracker.get_document("nonexistent")
    assert retrieved is None


def test_reference_graph_building():
    """Test that reference graph is built correctly."""
    tracker = ProvenanceTracker()

    doc1 = {
        "document_id": "act-001",
        "title": "Original Act",
        "document_type": "act",
        "provenance": {"source": "test", "hash": "hash1", "verified_on": "2023-01-01"},
    }

    doc2 = {
        "document_id": "amend-001",
        "title": "Amendment",
        "document_type": "amendment",
        "references": [
            {
                "document_id": "act-001",
                "reference_type": "amends",
                "section": "Section 2",
            }
        ],
        "provenance": {"source": "test", "hash": "hash2", "verified_on": "2023-01-02"},
    }

    tracker.add_document(doc1)
    tracker.add_document(doc2)

    # Check forward references
    amend_refs = tracker.get_references("amend-001")
    assert len(amend_refs["references_to"]) == 1
    assert amend_refs["references_to"][0]["document_id"] == "act-001"
    assert amend_refs["references_to"][0]["reference_type"] == "amends"

    # Check backward references
    act_refs = tracker.get_references("act-001")
    assert len(act_refs["referenced_by"]) == 1
    assert act_refs["referenced_by"][0]["document_id"] == "amend-001"


def test_get_dependencies():
    """Test getting dependencies for a document."""
    tracker = ProvenanceTracker()

    doc1 = {
        "document_id": "base-001",
        "title": "Base Document",
        "provenance": {"source": "test", "hash": "h1", "verified_on": "2023-01-01"},
    }

    doc2 = {
        "document_id": "derived-001",
        "title": "Derived Document",
        "references": [
            {"document_id": "base-001", "reference_type": "cites"},
        ],
        "provenance": {"source": "test", "hash": "h2", "verified_on": "2023-01-02"},
    }

    tracker.add_document(doc1)
    tracker.add_document(doc2)

    deps = tracker.get_dependencies("derived-001")
    assert len(deps) == 1
    assert "base-001" in deps


def test_get_dependents():
    """Test getting dependents for a document."""
    tracker = ProvenanceTracker()

    doc1 = {
        "document_id": "base-002",
        "title": "Base Document",
        "provenance": {"source": "test", "hash": "h1", "verified_on": "2023-01-01"},
    }

    doc2 = {
        "document_id": "derived-002",
        "title": "Derived Document",
        "references": [
            {"document_id": "base-002", "reference_type": "cites"},
        ],
        "provenance": {"source": "test", "hash": "h2", "verified_on": "2023-01-02"},
    }

    tracker.add_document(doc1)
    tracker.add_document(doc2)

    dependents = tracker.get_dependents("base-002")
    assert len(dependents) == 1
    assert "derived-002" in dependents


def test_detect_anomalies_missing_title():
    """Test anomaly detection for missing title."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "bad-001",
        "document_type": "act",
        "provenance": {"source": "test", "hash": "h1", "verified_on": "2023-01-01"},
    }

    tracker.add_document(document)
    anomalies = tracker.detect_anomalies("bad-001")

    assert any(a["type"] == "missing_title" for a in anomalies)


def test_detect_anomalies_missing_provenance():
    """Test anomaly detection for missing provenance fields."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "bad-002",
        "title": "Incomplete Provenance",
        "provenance": {},
    }

    tracker.add_document(document)
    anomalies = tracker.detect_anomalies("bad-002")

    assert any(a["type"] == "missing_source" for a in anomalies)
    assert any(a["type"] == "missing_hash" for a in anomalies)


def test_detect_anomalies_broken_reference():
    """Test anomaly detection for broken references."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "ref-001",
        "title": "Broken Reference Doc",
        "references": [
            {"document_id": "nonexistent-doc", "reference_type": "cites"},
        ],
        "provenance": {"source": "test", "hash": "h1", "verified_on": "2023-01-01"},
    }

    tracker.add_document(document)
    anomalies = tracker.detect_anomalies("ref-001")

    assert any(a["type"] == "broken_reference" for a in anomalies)


def test_calculate_confidence_score_perfect():
    """Test confidence score for a perfect document."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "perfect-001",
        "title": "Perfect Document",
        "document_type": "act",
        "jurisdiction": "Federal",
        "authority": "Congress",
        "provenance": {
            "source": "official_source",
            "hash": "a" * 64,
            "verified_on": "2023-01-01T00:00:00Z",
        },
    }

    tracker.add_document(document)
    score = tracker.calculate_confidence_score("perfect-001")

    assert score >= 0.95


def test_calculate_confidence_score_with_issues():
    """Test confidence score for a document with issues."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "flawed-001",
        "title": "Flawed Document",
        "provenance": {},
    }

    tracker.add_document(document)
    score = tracker.calculate_confidence_score("flawed-001")

    assert score < 1.0


def test_generate_audit_report():
    """Test generating a complete audit report."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "audit-001",
        "title": "Audit Test Document",
        "document_type": "act",
        "jurisdiction": "State",
        "provenance": {
            "source": "test_source",
            "hash": "b" * 64,
            "verified_on": "2023-01-01T00:00:00Z",
        },
    }

    tracker.add_document(document)
    report = tracker.generate_audit_report("audit-001")

    assert "document_id" in report
    assert report["document_id"] == "audit-001"
    assert "audit_result" in report
    assert "anomalies_detected" in report["audit_result"]
    assert "confidence_score" in report["audit_result"]
    assert "compliance_status" in report["audit_result"]
    assert "provenance" in report


def test_generate_audit_report_missing_document():
    """Test generating an audit report for a missing document."""
    tracker = ProvenanceTracker()
    report = tracker.generate_audit_report("missing-doc")

    assert report["audit_result"]["compliance_status"] == "Failed - Document Not Found"
    assert report["audit_result"]["confidence_score"] == 0.0


def test_verify_hash():
    """Test hash verification."""
    tracker = ProvenanceTracker()

    document = {
        "document_id": "hash-001",
        "title": "Hash Test",
        "provenance": {
            "source": "test",
            "hash": "a" * 64,
            "verified_on": "2023-01-01T00:00:00Z",
        },
    }

    tracker.add_document(document)
    is_valid = tracker.verify_hash("hash-001")

    # Should return True since we check hash format
    assert is_valid is True


def test_export_graph():
    """Test exporting the reference graph."""
    tracker = ProvenanceTracker()

    doc1 = {
        "document_id": "graph-001",
        "title": "Document 1",
        "provenance": {"source": "test", "hash": "h1", "verified_on": "2023-01-01"},
    }

    doc2 = {
        "document_id": "graph-002",
        "title": "Document 2",
        "references": [
            {"document_id": "graph-001", "reference_type": "cites"},
        ],
        "provenance": {"source": "test", "hash": "h2", "verified_on": "2023-01-02"},
    }

    tracker.add_document(doc1)
    tracker.add_document(doc2)

    graph = tracker.export_graph()

    assert "documents" in graph
    assert "graph" in graph
    assert len(graph["documents"]) == 2
    assert "graph-001" in graph["documents"]
    assert "graph-002" in graph["documents"]


def test_compliance_status_thresholds():
    """Test that compliance status is assigned based on confidence thresholds."""
    tracker = ProvenanceTracker()

    # Perfect document - should get "Pass"
    perfect_doc = {
        "document_id": "threshold-001",
        "title": "Perfect",
        "document_type": "act",
        "jurisdiction": "Federal",
        "provenance": {"source": "test", "hash": "x" * 64, "verified_on": "2023-01-01"},
    }
    tracker.add_document(perfect_doc)
    report = tracker.generate_audit_report("threshold-001")
    assert report["audit_result"]["compliance_status"] == "Pass"

    # Document with minor issues - should get "Pass with Notes"
    minor_issues_doc = {
        "document_id": "threshold-002",
        "title": "Minor Issues",
        "document_type": "act",
        "provenance": {"source": "test", "hash": "y" * 64, "verified_on": "2023-01-01"},
        # Missing jurisdiction - minor issue
    }
    tracker.add_document(minor_issues_doc)
    report = tracker.generate_audit_report("threshold-002")
    assert (
        "Pass" in report["audit_result"]["compliance_status"]
        or "Review" in report["audit_result"]["compliance_status"]
    )
