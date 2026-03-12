"""Tests for surveillance outsourcing detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.surveillance import detect_surveillance_anomalies


def test_no_anomalies_for_clean_doc():
    """Document without surveillance keywords should not trigger anomalies."""
    doc = {
        "document_id": "test",
        "title": "Test",
        "document_type": "act",
        "sections": [{"section_id": "1", "content": "General provisions."}],
    }
    anomalies = detect_surveillance_anomalies(doc)
    assert anomalies == []


def test_surveillance_outsourced_without_safeguards():
    """Detect surveillance outsourcing without privacy safeguards."""
    doc = {
        "document_id": "test",
        "title": "Surveillance Contract",
        "document_type": "contract",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The contractor shall provide biometric data collection "
                    "and facial recognition monitoring services."
                ),
            }
        ],
    }
    anomalies = detect_surveillance_anomalies(doc)
    assert any(
        a["id"] == "surveillance:outsourced-without-safeguards" for a in anomalies
    ), "Should detect surveillance outsourcing without safeguards"
    if anomalies:
        assert anomalies[0]["severity"] == "high"


def test_surveillance_outsourced_with_safeguards():
    """Surveillance outsourcing with safeguards should be flagged as low severity."""
    doc = {
        "document_id": "test",
        "title": "Surveillance Contract",
        "document_type": "contract",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The contractor shall provide monitoring services, "
                    "subject to warrant requirements and judicial authorization. "
                    "All data collection must comply with minimization procedures."
                ),
            }
        ],
    }
    anomalies = detect_surveillance_anomalies(doc)
    assert any(
        a["id"] == "surveillance:outsourced-with-safeguards" for a in anomalies
    ), "Should flag surveillance with safeguards for review"
    if anomalies:
        assert anomalies[0]["severity"] == "low"


def test_surveillance_keywords_detected():
    """Test that various surveillance keywords are detected."""
    keywords = [
        "surveillance",
        "biometric tracking",
        "facial recognition",
        "metadata collection",
    ]

    for keyword in keywords:
        doc = {
            "document_id": "test",
            "title": "Test",
            "document_type": "act",
            "sections": [
                {
                    "section_id": "1",
                    "content": f"The third party contractor will handle {keyword}.",
                }
            ],
        }
        anomalies = detect_surveillance_anomalies(doc)
        assert (
            len(anomalies) > 0
        ), f"Should detect surveillance anomaly for keyword: {keyword}"


def test_no_contractor_no_anomaly():
    """Surveillance without contractor involvement should not trigger anomaly."""
    doc = {
        "document_id": "test",
        "title": "Law Enforcement",
        "document_type": "act",
        "sections": [
            {
                "section_id": "1",
                "content": "Law enforcement may conduct surveillance with a warrant.",
            }
        ],
    }
    anomalies = detect_surveillance_anomalies(doc)
    # Should not trigger without contractor keywords
    assert len(anomalies) == 0 or all(
        "contractor" in a.get("details", {}).get("contractor_keywords", [])
        for a in anomalies
    )
