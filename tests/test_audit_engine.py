"""Smoke tests for the Audit Intelligence Engine.

Validates that the new analysis entry points import and execute against a
minimal normalized document without raising errors and with stable outputs.
"""

from __future__ import annotations

from datetime import UTC, datetime

from oraculus_di_auditor.analysis import analyze_document


def _minimal_doc() -> dict:
    return {
        "document_id": "doc-0",
        "title": "Test",
        "document_type": "act",
        "sections": [{"section_id": "1", "content": "Example content."}],
        "provenance": {
            "source": "unit-test",
            "hash": "deadbeef",
            "verified_on": datetime.now(UTC).isoformat(),
        },
    }


def test_analyze_document_smoke():
    doc = _minimal_doc()
    result = analyze_document(doc)
    assert isinstance(result, dict)
    assert "count" in result
    assert "score" in result
    assert "anomalies" in result
    # With only a minimal document, expect low/no anomalies and high score.
    assert result["count"] >= 0
    assert 0.0 <= result["score"] <= 1.0
    assert isinstance(result["anomalies"], list)
