"""Ingestion-integrity detector (v2.7.3 D3).

Fail-loud companion to the PDF extraction path in
``ingestion.engine.extract_text_from_pdf``. When a large PDF comes out
the other side of extraction + OCR with near-empty text, the detectors
downstream have almost nothing to work with and the audit report
silently understates the finding count.

This detector reads the already-normalised document dict and emits a
single HIGH-severity finding whenever it looks like extraction failed:

  * The file is large enough that we expected meaningful text.
  * The extracted text is shorter than the minimum readable threshold.
  * The format is a type we expect to contain text (PDF, HTML, DOCX).

The finding ID ``ingestion:extraction-failure`` has a ready plain-
language narrative wired up in
``reporting.plain_language.TRANSLATIONS[ingestion]`` (landed in D1).
"""

from __future__ import annotations

from typing import Any

# Minimum extracted text length below which we assume extraction failed.
# Keyed to the handoff's §D3 specification: "less than 500 characters
# for a PDF larger than 100 KB". Matches the threshold bumped in
# ``ingestion.engine._OCR_MIN_TEXT_LENGTH``.
_MIN_EXTRACTED_CHARS = 500

# Only complain about files big enough that there should be real text.
# Under 100 KB is likely a short staff note, a cover letter, or a scan
# that legitimately carries very little text. Above that, an
# under-500-char result is almost certainly an extraction bug.
_MIN_SUSPICIOUS_BYTES = 100 * 1024

# Formats we expect to contain extractable text. Image-only formats
# (JPG/PNG/TIFF) are not checked — those correctly produce empty text
# under a non-OCR pipeline.
_TEXT_BEARING_FORMATS = frozenset({"pdf", "html", "docx", "txt"})


def detect_ingestion_integrity_anomalies(
    doc: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flag documents that look like silent extraction failures.

    Pure function. Returns a list of anomaly dicts in the standard
    ODIA shape. Returns an empty list when the document passed
    extraction cleanly (the usual case).
    """
    if not isinstance(doc, dict):
        return []

    metadata = doc.get("metadata") or {}
    if not isinstance(metadata, dict):
        return []

    file_format = (metadata.get("format") or "").lower()
    if file_format not in _TEXT_BEARING_FORMATS:
        return []

    file_bytes = int(metadata.get("file_size_bytes") or 0)
    if file_bytes < _MIN_SUSPICIOUS_BYTES:
        return []

    text = doc.get("text", "") or ""
    extracted_chars = len(text.strip())
    if extracted_chars >= _MIN_EXTRACTED_CHARS:
        return []

    return [
        {
            "id": "ingestion:extraction-failure",
            "issue": (
                f"Text extraction returned only {extracted_chars} "
                f"character(s) from a {file_bytes}-byte {file_format} "
                f"file — detectors had nothing to analyse"
            ),
            "severity": "high",
            "layer": "ingestion",
            "details": {
                "extracted_chars": extracted_chars,
                "file_bytes": file_bytes,
                "file_format": file_format,
                "file_name": metadata.get("file_name"),
                "source_path": metadata.get("source_path"),
                "min_expected_chars": _MIN_EXTRACTED_CHARS,
            },
        }
    ]


__all__ = ["detect_ingestion_integrity_anomalies"]
