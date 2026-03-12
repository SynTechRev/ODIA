from __future__ import annotations

from datetime import UTC, datetime

from oraculus_di_auditor.analysis import analyze_document
from oraculus_di_auditor.analysis.fiscal import detect_fiscal_anomalies


def _base_doc() -> dict:
    return {
        "document_id": "doc-x",
        "title": "Fiscal Test",
        "document_type": "act",
        "sections": [{"section_id": "1", "content": "Appropriation."}],
    }


def test_fiscal_anomalies_when_provenance_missing():
    doc = _base_doc()
    # No provenance at all
    anomalies = detect_fiscal_anomalies(doc)
    assert any(a["id"] == "fiscal:missing-provenance-hash" for a in anomalies)


def test_fiscal_anomalies_when_hash_missing_in_provenance():
    doc = _base_doc()
    doc["provenance"] = {"source": "unit", "verified_on": datetime.now(UTC).isoformat()}
    anomalies = detect_fiscal_anomalies(doc)
    assert any(a["id"] == "fiscal:missing-provenance-hash" for a in anomalies)


def test_fiscal_no_anomalies_when_hash_present():
    doc = _base_doc()
    doc["provenance"] = {
        "source": "unit",
        "hash": "deadbeef",
        "verified_on": datetime.now(UTC).isoformat(),
    }
    anomalies = detect_fiscal_anomalies(doc)
    assert anomalies == []


def test_analyze_document_score_changes_with_anomalies():
    # With provenance hash present -> higher score
    doc_ok = _base_doc()
    doc_ok["provenance"] = {
        "source": "unit",
        "hash": "deadbeef",
        "verified_on": datetime.now(UTC).isoformat(),
    }
    res_ok = analyze_document(doc_ok)

    # Without provenance hash -> one anomaly -> lower score
    doc_bad = _base_doc()
    res_bad = analyze_document(doc_bad)

    assert res_ok["count"] <= res_bad["count"]
    assert res_ok["score"] >= res_bad["score"]


def test_fiscal_amount_without_appropriation():
    """Test detection of fiscal amounts without appropriation reference."""
    doc = _base_doc()
    doc["provenance"] = {"hash": "abc123"}
    doc["sections"] = [
        {
            "section_id": "1",
            "content": "The program shall receive $1,000,000 for operations.",
        }
    ]
    anomalies = detect_fiscal_anomalies(doc)
    assert any(
        a["id"] == "fiscal:amount-without-appropriation" for a in anomalies
    ), "Should detect fiscal amount without appropriation"


def test_fiscal_amount_with_appropriation():
    """Test that fiscal amounts with appropriation refs don't trigger anomaly."""
    doc = _base_doc()
    doc["provenance"] = {"hash": "abc123"}
    doc["sections"] = [
        {
            "section_id": "1",
            "content": "There is appropriated $1,000,000 for fiscal year 2025.",
        }
    ]
    anomalies = detect_fiscal_anomalies(doc)
    assert not any(
        a["id"] == "fiscal:amount-without-appropriation" for a in anomalies
    ), "Should not detect anomaly when appropriation is present"
