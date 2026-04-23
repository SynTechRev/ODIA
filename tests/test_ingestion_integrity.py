"""Tests for the ingestion-integrity detector (v2.7.3 D3).

Scope:

  1. The pure-function detector: synthetic doc dicts exercising the
     success-path (above threshold → no finding), fail-path (large
     PDF with near-empty text → one HIGH finding), and the several
     early-return gates (wrong format, small file, missing metadata).

  2. End-to-end: ``analyze_document`` in audit_engine.py now invokes
     the detector, so a doc that looks like a silent extraction
     failure shows up in ``findings["anomalies"]`` as an
     ``ingestion:extraction-failure`` row.

  3. Threshold constants imported from the module under test so the
     tests travel with any future threshold tweak.
"""

from __future__ import annotations

from oraculus_di_auditor.analysis.ingestion_integrity import (
    _MIN_EXTRACTED_CHARS,
    _MIN_SUSPICIOUS_BYTES,
    detect_ingestion_integrity_anomalies,
)

# ---------------------------------------------------------------------------
# Detector unit tests
# ---------------------------------------------------------------------------


def _doc(*, text: str, file_format: str, file_size_bytes: int) -> dict:
    """Build the minimal doc shape ingest_document produces."""
    return {
        "text": text,
        "segments": [],
        "metadata": {
            "source_path": "/tmp/test.pdf",
            "file_name": "test.pdf",
            "file_size_bytes": file_size_bytes,
            "format": file_format,
            "hash": "a" * 64,
            "char_count": len(text),
            "segment_count": 0,
        },
    }


def test_no_finding_when_text_above_threshold():
    doc = _doc(
        text="x" * (_MIN_EXTRACTED_CHARS + 10),
        file_format="pdf",
        file_size_bytes=_MIN_SUSPICIOUS_BYTES * 5,
    )
    assert detect_ingestion_integrity_anomalies(doc) == []


def test_no_finding_for_small_file_even_with_no_text():
    doc = _doc(
        text="",
        file_format="pdf",
        file_size_bytes=_MIN_SUSPICIOUS_BYTES - 1,
    )
    assert detect_ingestion_integrity_anomalies(doc) == []


def test_no_finding_for_non_text_format():
    doc = _doc(
        text="",
        file_format="png",
        file_size_bytes=_MIN_SUSPICIOUS_BYTES * 10,
    )
    assert detect_ingestion_integrity_anomalies(doc) == []


def test_no_finding_for_empty_doc():
    assert detect_ingestion_integrity_anomalies({}) == []
    assert detect_ingestion_integrity_anomalies({"metadata": None}) == []


def test_flock_sized_pdf_with_empty_text_fires_high_finding():
    """Reproduces the post-v2.7.2 audit gap — a 1 MB Flock Agreement
    PDF came out with ~200 chars. Detector must catch this class."""
    doc = _doc(
        text="Page 1\n\nPage 2\n\n(no meaningful text extracted)",
        file_format="pdf",
        file_size_bytes=1_040_000,  # 1.04 MB, matches the real case
    )
    findings = detect_ingestion_integrity_anomalies(doc)
    assert len(findings) == 1
    f = findings[0]
    assert f["id"] == "ingestion:extraction-failure"
    assert f["severity"] == "high"
    assert f["layer"] == "ingestion"
    assert f["details"]["extracted_chars"] < _MIN_EXTRACTED_CHARS
    assert f["details"]["file_bytes"] == 1_040_000
    assert f["details"]["file_format"] == "pdf"
    assert f["details"]["file_name"] == "test.pdf"
    assert f["details"]["min_expected_chars"] == _MIN_EXTRACTED_CHARS


def test_whitespace_only_text_treated_as_empty():
    """text.strip() not raw len — whitespace-only documents should fire."""
    doc = _doc(
        text=" " * 2000 + "\n" * 500,  # lots of chars, all whitespace
        file_format="pdf",
        file_size_bytes=_MIN_SUSPICIOUS_BYTES * 3,
    )
    findings = detect_ingestion_integrity_anomalies(doc)
    assert len(findings) == 1
    assert findings[0]["details"]["extracted_chars"] == 0


def test_docx_format_also_checked():
    doc = _doc(
        text="",
        file_format="docx",
        file_size_bytes=_MIN_SUSPICIOUS_BYTES * 2,
    )
    findings = detect_ingestion_integrity_anomalies(doc)
    assert len(findings) == 1
    assert findings[0]["details"]["file_format"] == "docx"


# ---------------------------------------------------------------------------
# End-to-end via analyze_document
# ---------------------------------------------------------------------------


def test_audit_engine_surfaces_extraction_failure_anomaly():
    """Silent-failure-shaped doc fed into analyze_document emits
    an ingestion:extraction-failure anomaly among the findings."""
    from oraculus_di_auditor.analysis.audit_engine import analyze_document

    doc = {
        "text": "x",  # 1 char
        "segments": [],
        "metadata": {
            "source_path": "/tmp/flock-agreement.pdf",
            "file_name": "flock-agreement.pdf",
            "file_size_bytes": 1_200_000,
            "format": "pdf",
            "hash": "f" * 64,
            "char_count": 1,
            "segment_count": 0,
        },
    }
    result = analyze_document(doc)
    ids = [a["id"] for a in result["anomalies"]]
    assert "ingestion:extraction-failure" in ids


def test_audit_engine_does_not_emit_extraction_failure_on_healthy_doc():
    from oraculus_di_auditor.analysis.audit_engine import analyze_document

    doc = {
        "text": "Lorem ipsum dolor sit amet. " * 200,  # > 500 chars
        "segments": [],
        "metadata": {
            "source_path": "/tmp/staff-report.pdf",
            "file_name": "staff-report.pdf",
            "file_size_bytes": 200_000,
            "format": "pdf",
            "hash": "b" * 64,
            "char_count": 5600,
            "segment_count": 1,
        },
    }
    result = analyze_document(doc)
    ids = [a["id"] for a in result["anomalies"]]
    assert "ingestion:extraction-failure" not in ids


# ---------------------------------------------------------------------------
# Plain-language translator already has an entry for this ID (from D1)
# ---------------------------------------------------------------------------


def test_plain_language_entry_exists_for_ingestion_extraction_failure():
    """D1 added TRANSLATIONS["ingestion"]["extraction-failure"] —
    confirm the narrative resolves rather than falling through to the
    generic boilerplate."""
    from oraculus_di_auditor.reporting.plain_language import translate_finding

    finding = {
        "id": "ingestion:extraction-failure",
        "issue": "test",
        "severity": "high",
        "layer": "ingestion",
        "details": {
            "extracted_chars": 47,
            "file_bytes": 1_040_000,
            "file_format": "pdf",
            "file_name": "flock-agreement.pdf",
            "source_path": "/tmp/flock-agreement.pdf",
            "min_expected_chars": 500,
        },
    }
    result = translate_finding(finding)
    assert "anomaly was detected" not in result["plain_summary"].lower()
    # Interpolation carries through
    assert "47" in result["plain_summary"]
    assert (
        "1040000" in result["plain_summary"] or "1,040,000" in result["plain_summary"]
    )
    assert "pdf" in result["plain_summary"]
