"""Tests for administrative integrity detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.administrative_integrity import (
    detect_administrative_anomalies,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(text: str = "", **metadata) -> dict:
    """Build a doc dict with raw_text and any extra metadata fields."""
    d = {"document_id": "test-doc", "raw_text": text}
    d.update(metadata)
    return d


def _complete_doc(text: str = "This item was approved by the council.") -> dict:
    """A fully populated document with all required fields present."""
    return _doc(
        text,
        final_action="Approved",
        status="Closed",
        vote_result="9-0",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )


def _ids(doc: dict) -> set[str]:
    return {a["id"] for a in detect_administrative_anomalies(doc)}


# ---------------------------------------------------------------------------
# No-anomaly cases
# ---------------------------------------------------------------------------


def test_complete_document_no_anomalies():
    """A document with all required fields and no red flags is clean."""
    assert detect_administrative_anomalies(_complete_doc()) == []


def test_non_dict_input_returns_empty():
    assert detect_administrative_anomalies(None) == []
    assert detect_administrative_anomalies("not a doc") == []
    assert detect_administrative_anomalies(42) == []


def test_empty_text_with_all_metadata_no_anomalies():
    """Populated metadata with no text body should not flag anything."""
    doc = _complete_doc(text="")
    assert detect_administrative_anomalies(doc) == []


def test_missing_final_action_without_approval_text_no_flag():
    """Blank final_action is only flagged when approval language appears in text."""
    doc = _doc(
        "This item is pending review.",
        status="Open",
        vote_result="",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    # No approval signals → should not fire missing-final-action
    anomalies = detect_administrative_anomalies(doc)
    assert not any(a["id"] == "admin:missing-final-action" for a in anomalies)


# ---------------------------------------------------------------------------
# admin:missing-final-action
# ---------------------------------------------------------------------------


def test_missing_final_action_with_approved_text():
    """Blank final_action + 'approved' in text → high severity."""
    doc = _doc(
        "Resolution was approved by the city council on March 15.",
        status="Closed",
        vote_result="7-2",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    anomalies = detect_administrative_anomalies(doc)
    assert any(a["id"] == "admin:missing-final-action" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "admin:missing-final-action")
    assert finding["severity"] == "high"
    assert finding["layer"] == "administrative"


def test_missing_final_action_details_include_approval_signals():
    doc = _doc(
        "Ordinance adopted and enacted by the council.",
        status="Closed",
        vote_result="8-1",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    finding = next(
        a
        for a in detect_administrative_anomalies(doc)
        if a["id"] == "admin:missing-final-action"
    )
    assert len(finding["details"]["approval_signals_found"]) >= 1
    assert "adopted" in finding["details"]["approval_signals_found"]


def test_null_final_action_with_authorized_text():
    doc = _doc(
        "Expenditure authorized by council vote.",
        final_action=None,
        status="Closed",
        vote_result="6-3",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    assert "admin:missing-final-action" in _ids(doc)


def test_whitespace_final_action_treated_as_blank():
    doc = _doc(
        "Contract was approved.",
        final_action="   ",
        status="Closed",
        vote_result="9-0",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    assert "admin:missing-final-action" in _ids(doc)


# ---------------------------------------------------------------------------
# admin:blank-required-fields
# ---------------------------------------------------------------------------


def test_blank_required_fields_flagged():
    """Missing status and vote_result → medium severity."""
    doc = _doc(
        "Item tabled.",
        final_action="Tabled",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    anomalies = detect_administrative_anomalies(doc)
    assert any(a["id"] == "admin:blank-required-fields" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "admin:blank-required-fields")
    assert finding["severity"] == "medium"
    assert finding["layer"] == "administrative"


def test_blank_fields_details_list_missing_fields():
    doc = _doc(
        "Item tabled.",
        final_action="Tabled",
        meeting_date="2024-03-15",
    )
    finding = next(
        a
        for a in detect_administrative_anomalies(doc)
        if a["id"] == "admin:blank-required-fields"
    )
    assert "status" in finding["details"]["blank_fields"]
    assert "vote_result" in finding["details"]["blank_fields"]
    assert "agenda_number" in finding["details"]["blank_fields"]
    assert finding["details"]["field_count"] == 3


def test_final_action_not_double_reported_in_blank_fields():
    """When final_action triggers missing-final-action, it must not also
    appear in blank-required-fields details."""
    doc = _doc(
        "Resolution was approved.",
        status="Closed",
        vote_result="9-0",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    anomalies = detect_administrative_anomalies(doc)
    blank_finding = next(
        (a for a in anomalies if a["id"] == "admin:blank-required-fields"), None
    )
    # Either no blank-fields finding, or final_action is not in its list
    if blank_finding is not None:
        assert "final_action" not in blank_finding["details"]["blank_fields"]


def test_empty_string_fields_treated_as_blank():
    doc = _doc(
        "Passed unanimously.",
        final_action="Passed",
        status="",
        vote_result="",
        meeting_date="2024-03-15",
        agenda_number="24-0312",
    )
    finding = next(
        a
        for a in detect_administrative_anomalies(doc)
        if a["id"] == "admin:blank-required-fields"
    )
    assert "status" in finding["details"]["blank_fields"]
    assert "vote_result" in finding["details"]["blank_fields"]


# ---------------------------------------------------------------------------
# admin:retroactive-authorization
# ---------------------------------------------------------------------------


def test_retroactive_keyword_flagged():
    doc = _complete_doc(
        "This contract is retroactive to January 1, 2024."
    )
    anomalies = detect_administrative_anomalies(doc)
    assert any(a["id"] == "admin:retroactive-authorization" for a in anomalies)
    finding = next(
        a for a in anomalies if a["id"] == "admin:retroactive-authorization"
    )
    assert finding["severity"] == "high"
    assert finding["layer"] == "administrative"


def test_nunc_pro_tunc_flagged():
    doc = _complete_doc("Order entered nunc pro tunc to correct the record.")
    assert "admin:retroactive-authorization" in _ids(doc)


def test_ratified_after_flagged():
    doc = _complete_doc("Expenditure ratified after completion of the project.")
    assert "admin:retroactive-authorization" in _ids(doc)


def test_approved_after_the_fact_flagged():
    doc = _complete_doc("Services approved after the fact due to emergency conditions.")
    assert "admin:retroactive-authorization" in _ids(doc)


def test_back_dated_flagged():
    doc = _complete_doc("Agreement was back-dated to reflect original intent.")
    assert "admin:retroactive-authorization" in _ids(doc)


def test_effective_prior_to_flagged():
    doc = _complete_doc("Amendment effective prior to council approval.")
    assert "admin:retroactive-authorization" in _ids(doc)


def test_retroactive_details_include_matched_phrase():
    doc = _complete_doc("This resolution is retroactive to the prior fiscal year.")
    finding = next(
        a
        for a in detect_administrative_anomalies(doc)
        if a["id"] == "admin:retroactive-authorization"
    )
    assert "retroactive" in finding["details"]["matched_phrase"].lower()
    assert isinstance(finding["details"]["position"], int)


# ---------------------------------------------------------------------------
# admin:potential-misfiling
# ---------------------------------------------------------------------------


def test_misfiled_keyword_flagged():
    doc = _complete_doc("This document was misfiled under the wrong agenda item.")
    anomalies = detect_administrative_anomalies(doc)
    assert any(a["id"] == "admin:potential-misfiling" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "admin:potential-misfiling")
    assert finding["severity"] == "medium"
    assert finding["layer"] == "administrative"


def test_wrong_agenda_keyword_flagged():
    doc = _complete_doc("Staff note: wrong agenda — should be item 14B.")
    assert "admin:potential-misfiling" in _ids(doc)


def test_incorrect_item_keyword_flagged():
    doc = _complete_doc("Clerk note: incorrect item number assigned at intake.")
    assert "admin:potential-misfiling" in _ids(doc)


def test_clerical_error_keyword_flagged():
    doc = _complete_doc("Corrected due to clerical error in the original filing.")
    assert "admin:potential-misfiling" in _ids(doc)


def test_misfiling_details_include_indicators():
    doc = _complete_doc("Document misfiled and incorrect item referenced.")
    finding = next(
        a
        for a in detect_administrative_anomalies(doc)
        if a["id"] == "admin:potential-misfiling"
    )
    assert len(finding["details"]["misfiling_indicators"]) >= 1


# ---------------------------------------------------------------------------
# Multiple findings
# ---------------------------------------------------------------------------


def test_retroactive_and_misfiling_both_fire():
    doc = _complete_doc(
        "This item was retroactive and appears to be misfiled on the agenda."
    )
    ids = _ids(doc)
    assert "admin:retroactive-authorization" in ids
    assert "admin:potential-misfiling" in ids


def test_missing_final_action_and_blank_fields_together():
    """Blank final_action with approval text AND other blank fields → two findings."""
    doc = _doc("Resolution approved by council.")
    # No metadata at all → final_action blank + all other fields blank
    ids = _ids(doc)
    assert "admin:missing-final-action" in ids
    assert "admin:blank-required-fields" in ids
