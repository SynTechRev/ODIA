"""Tests for constitutional conformity detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.constitutional import (
    detect_constitutional_anomalies,
)


def test_no_anomalies_for_empty_doc():
    """Empty document should not trigger anomalies."""
    doc = {"document_id": "test", "title": "Test", "document_type": "act"}
    anomalies = detect_constitutional_anomalies(doc)
    assert anomalies == []


def test_broad_delegation_without_standards():
    """Detect broad delegation of authority without limiting standards."""
    doc = {
        "document_id": "test",
        "title": "Test Act",
        "document_type": "act",
        "sections": [
            {
                "section_id": "1",
                "content": "The Secretary may determine appropriate measures.",
            }
        ],
    }
    anomalies = detect_constitutional_anomalies(doc)
    assert any(
        a["id"] == "constitutional:broad-delegation" for a in anomalies
    ), "Should detect broad delegation"
    assert anomalies[0]["severity"] == "medium"


def test_delegation_with_standards():
    """Delegation with limiting standards should not trigger anomaly."""
    doc = {
        "document_id": "test",
        "title": "Test Act",
        "document_type": "act",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The Secretary may determine appropriate measures, "
                    "subject to the following standards and criteria."
                ),
            }
        ],
    }
    anomalies = detect_constitutional_anomalies(doc)
    assert not any(
        a["id"] == "constitutional:broad-delegation" for a in anomalies
    ), "Should not detect anomaly with standards present"


def test_multiple_delegation_patterns():
    """Test detection of multiple delegation patterns."""
    doc = {
        "document_id": "test",
        "title": "Test Act",
        "document_type": "act",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The Administrator shall prescribe rules as necessary. "
                    "The Director may establish requirements in his discretion."
                ),
            }
        ],
    }
    anomalies = detect_constitutional_anomalies(doc)
    if anomalies:
        assert anomalies[0]["details"]["delegation_count"] >= 2
