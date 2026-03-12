"""Tests for analyzer module.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

from oraculus_di_auditor.analyzer import find_anomalies


def test_find_anomalies_long_sentence():
    """Test detection of long sentences."""
    long_sentence = "A" * 1500
    record = {"id": "test-1", "text": long_sentence, "citations": []}

    result = find_anomalies(record)

    assert result["id"] == "test-1"
    assert result["count"] > 0
    assert any(a["type"] == "long_sentence" for a in result["anomalies"])


def test_find_anomalies_cross_reference():
    """Test detection of cross-reference mismatches."""
    record = {
        "id": "test-2",
        "text": "See 42 U.S.C. section 1983 for details.",
        "citations": ["18 U.S.C. 1001"],  # Different citation
    }

    result = find_anomalies(record)

    assert result["id"] == "test-2"
    # Should detect mismatch
    assert any(a["type"] == "cross_reference_mismatch" for a in result["anomalies"])


def test_find_anomalies_contradictory_dates():
    """Test detection of contradictory dates."""
    record = {
        "id": "test-3",
        "text": "This statute was enacted in 1950 and has been in effect since.",
        "date": "2020-01-01",
    }

    result = find_anomalies(record)

    assert result["id"] == "test-3"
    # 1950 vs 2020 should trigger date contradiction
    assert any(a["type"] == "contradictory_dates" for a in result["anomalies"])


def test_find_anomalies_none():
    """Test document with no anomalies."""
    record = {
        "id": "test-4",
        "text": "This is a normal short document with no issues.",
        "date": "2020-01-01",
        "citations": [],
    }

    result = find_anomalies(record)

    assert result["id"] == "test-4"
    assert result["count"] == 0
    assert len(result["anomalies"]) == 0
