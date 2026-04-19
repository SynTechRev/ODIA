"""Tests for surveillance anomaly detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.surveillance import detect_surveillance_anomalies


def _doc(text: str) -> dict:
    return {"document_id": "test", "raw_text": text}


def _ids(text: str) -> set[str]:
    return {a["id"] for a in detect_surveillance_anomalies(_doc(text))}


def test_no_anomalies_for_clean_doc():
    """Document without surveillance vendors or tech should not trigger anomalies."""
    doc = {
        "document_id": "test",
        "title": "Test",
        "document_type": "act",
        "sections": [{"section_id": "1", "content": "General provisions."}],
    }
    anomalies = detect_surveillance_anomalies(doc)
    assert anomalies == []


def test_alpr_vendor_without_sb524_policy():
    """Flock Safety ALPR referenced without SB 524 policy → critical finding."""
    doc = _doc(
        "The contractor shall provide Flock Safety ALPR license plate reader "
        "services for patrol vehicle deployment."
    )
    anomalies = detect_surveillance_anomalies(doc)
    assert any(
        a["id"] == "surveillance:alpr-without-sb524-policy" for a in anomalies
    ), "Should detect ALPR deployment missing SB 524 policy citation"
    finding = next(
        a for a in anomalies if a["id"] == "surveillance:alpr-without-sb524-policy"
    )
    assert finding["severity"] in ("critical", "high")


def test_vendor_detected_is_low_severity():
    """Surveillance vendor reference alone is flagged at low severity."""
    doc = _doc("The agency contracted with Flock Safety for traffic monitoring.")
    anomalies = detect_surveillance_anomalies(doc)
    vendor_finding = next(
        (a for a in anomalies if "vendor-detected" in a["id"]),
        None,
    )
    assert vendor_finding is not None, "Should emit a vendor-detected finding"
    assert vendor_finding["severity"] == "low"


def test_facial_recognition_reference_detected():
    """Facial recognition reference without governance → critical finding."""
    doc = _doc("Facial recognition system installed at city hall entrances.")
    anomalies = detect_surveillance_anomalies(doc)
    assert any(
        a["id"] == "surveillance:facial-recognition-reference" for a in anomalies
    ), "Should detect facial recognition reference"
    finding = next(
        a for a in anomalies if a["id"] == "surveillance:facial-recognition-reference"
    )
    assert finding["severity"] == "critical"


def test_surveillance_known_vendors_detected():
    """Known surveillance vendors in text are detected."""
    vendor_texts = [
        "Flock Safety ALPR cameras deployed on patrol routes.",
        "Axon body cameras issued to all officers.",
        "Motorola Solutions radio system for dispatch.",
    ]
    for text in vendor_texts:
        doc = _doc(text)
        anomalies = detect_surveillance_anomalies(doc)
        assert len(anomalies) > 0, f"Should detect anomaly for: {text!r}"


def test_no_contractor_no_anomaly():
    """Surveillance mention without vendor or tech keyword should not trigger."""
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
    assert anomalies == []


def test_finding_shape():
    """Every finding has required fields with correct types."""
    doc = _doc("Flock Safety ALPR deployed on all major corridors.")
    anomalies = detect_surveillance_anomalies(doc)
    assert len(anomalies) > 0
    for a in anomalies:
        assert "id" in a
        assert "issue" in a
        assert a["severity"] in ("low", "medium", "high", "critical")
        assert a["layer"] == "surveillance"
        assert isinstance(a["details"], dict)
