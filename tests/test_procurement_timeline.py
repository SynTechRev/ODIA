"""Tests for procurement timeline detector."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.analysis.procurement_timeline import (
    detect_procurement_timeline_anomalies,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VIOLATION_ID = "procurement:execution-precedes-authorization"


def _make_doc(execution_date, authorization_date, doc_id="contract-001", title="Test Contract"):
    return {
        "document_id": doc_id,
        "title": title,
        "execution_date": execution_date,
        "authorization_date": authorization_date,
    }


# ---------------------------------------------------------------------------
# No-violation cases
# ---------------------------------------------------------------------------


def test_empty_list_returns_no_anomalies():
    assert detect_procurement_timeline_anomalies([]) == []


def test_execution_after_authorization_no_flag():
    """Contract signed after authorization — clean."""
    docs = [_make_doc("2024-03-15", "2024-03-01")]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_execution_same_day_as_authorization_no_flag():
    """Same-day execution and authorization is not a violation."""
    docs = [_make_doc("2024-03-01", "2024-03-01")]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_multiple_clean_documents():
    """All clean docs produce no anomalies."""
    docs = [
        _make_doc("2024-04-10", "2024-04-01", doc_id="c1"),
        _make_doc("2024-05-20", "2024-05-15", doc_id="c2"),
        _make_doc("2024-06-01", "2024-06-01", doc_id="c3"),
    ]
    assert detect_procurement_timeline_anomalies(docs) == []


# ---------------------------------------------------------------------------
# Violation cases
# ---------------------------------------------------------------------------


def test_execution_precedes_authorization_flagged():
    """Execution before authorization produces a high-severity finding."""
    docs = [_make_doc("2024-02-01", "2024-03-01")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert len(anomalies) == 1
    assert anomalies[0]["id"] == _VIOLATION_ID


def test_violation_severity_is_high():
    docs = [_make_doc("2024-01-01", "2024-06-01")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert anomalies[0]["severity"] == "high"


def test_violation_layer_is_procurement():
    docs = [_make_doc("2024-01-01", "2024-06-01")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert anomalies[0]["layer"] == "procurement"


def test_violation_details_contain_expected_fields():
    docs = [_make_doc("2024-01-15", "2024-03-15", doc_id="c-99", title="Bridge Contract")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    details = anomalies[0]["details"]
    assert details["document_id"] == "c-99"
    assert details["title"] == "Bridge Contract"
    assert details["execution_date"] == "2024-01-15"
    assert details["authorization_date"] == "2024-03-15"
    assert details["days_early"] == 60


def test_days_early_calculated_correctly():
    """Verify the day-delta arithmetic."""
    docs = [_make_doc("2024-01-01", "2024-01-11")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert anomalies[0]["details"]["days_early"] == 10


def test_violation_issue_mentions_days():
    docs = [_make_doc("2024-01-01", "2024-01-11")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert "10 day(s)" in anomalies[0]["issue"]


def test_only_violating_docs_flagged_in_mixed_list():
    """Only contracts with execution before authorization should appear."""
    docs = [
        _make_doc("2024-01-01", "2024-01-15", doc_id="violation"),
        _make_doc("2024-03-01", "2024-02-15", doc_id="clean"),
    ]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert len(anomalies) == 1
    assert anomalies[0]["details"]["document_id"] == "violation"


def test_multiple_violations_all_flagged():
    docs = [
        _make_doc("2024-01-01", "2024-02-01", doc_id="v1"),
        _make_doc("2024-03-01", "2024-04-01", doc_id="v2"),
    ]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert len(anomalies) == 2
    ids = {a["details"]["document_id"] for a in anomalies}
    assert ids == {"v1", "v2"}


# ---------------------------------------------------------------------------
# Missing / malformed date handling
# ---------------------------------------------------------------------------


def test_missing_execution_date_skipped():
    docs = [{"document_id": "x", "authorization_date": "2024-01-01"}]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_missing_authorization_date_skipped():
    docs = [{"document_id": "x", "execution_date": "2024-01-01"}]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_both_dates_missing_skipped():
    docs = [{"document_id": "x", "title": "No dates"}]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_invalid_execution_date_format_skipped():
    docs = [_make_doc("not-a-date", "2024-01-01")]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_invalid_authorization_date_format_skipped():
    docs = [_make_doc("2024-01-01", "01/15/2024")]
    assert detect_procurement_timeline_anomalies(docs) == []


def test_non_dict_entry_skipped():
    """Non-dict entries in the list are skipped without error."""
    docs = [None, "not a doc", 42, _make_doc("2024-01-01", "2024-02-01")]
    anomalies = detect_procurement_timeline_anomalies(docs)
    assert len(anomalies) == 1


def test_non_list_input_returns_empty():
    """Passing a non-list should return empty rather than raise."""
    assert detect_procurement_timeline_anomalies(None) == []
    assert detect_procurement_timeline_anomalies({"execution_date": "2024-01-01"}) == []


# ---------------------------------------------------------------------------
# Document identifier fallback
# ---------------------------------------------------------------------------


def test_fallback_to_id_field_when_document_id_missing():
    doc = {"id": "alt-id", "execution_date": "2024-01-01", "authorization_date": "2024-02-01"}
    anomalies = detect_procurement_timeline_anomalies([doc])
    assert anomalies[0]["details"]["document_id"] == "alt-id"


def test_fallback_index_label_when_no_id_fields():
    doc = {"execution_date": "2024-01-01", "authorization_date": "2024-02-01"}
    anomalies = detect_procurement_timeline_anomalies([doc])
    assert anomalies[0]["details"]["document_id"] == "doc[0]"
