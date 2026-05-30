"""Tests for vote_date_alignment detector."""

import pytest

from oraculus_di_auditor.analysis.vote_date_alignment import (
    detect_vote_date_alignment_anomalies,
)


def _doc(text: str, **kwargs) -> dict:
    return {"raw_text": text, **kwargs}


# -- guards -----------------------------------------------------------------


def test_empty_text_returns_empty():
    assert detect_vote_date_alignment_anomalies({"text": ""}) == []


def test_non_dict_returns_empty():
    assert detect_vote_date_alignment_anomalies("bad") == []  # type: ignore


def test_clean_document_returns_no_findings():
    doc = _doc(
        "The council approved the budget on March 5, 2024. "
        "The contract was executed on April 1, 2024."
    )
    # No retroactive, no urgency without finding, no consent + high value
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:retroactive-approval" not in ids
    assert "vote_date:urgency-without-finding" not in ids


# -- finding: retroactive approval -----------------------------------------


def test_retroactive_language_flagged():
    doc = _doc(
        "The council hereby ratifies the agreement retroactively effective "
        "as of January 1, 2024, pursuant to the city manager's prior action."
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:retroactive-approval" in ids


def test_nunc_pro_tunc_flagged():
    doc = _doc(
        "The board approved the contract nunc pro tunc to the prior fiscal year."
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:retroactive-approval" in ids


# -- finding: urgency without finding --------------------------------------


def test_urgency_without_finding():
    doc = _doc(
        "This urgency ordinance is adopted by a four-fifths vote of the council "
        "and shall take effect immediately."
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:urgency-without-finding" in ids


def test_urgency_with_finding_not_flagged():
    doc = _doc(
        "This urgency ordinance is adopted by a four-fifths vote. "
        "The council finds that an emergency exists threatening public safety "
        "and the public welfare requires immediate action."
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:urgency-without-finding" not in ids


# -- finding: consent calendar + high value --------------------------------


def test_consent_calendar_high_value():
    doc = _doc(
        "Consent Calendar Item 4B: Approval of contract with Axon Enterprise "
        "for $1,500,000 for body-worn cameras."
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:consent-calendar-high-value" in ids


def test_consent_calendar_low_value_not_flagged():
    doc = _doc("Consent Calendar: Approval of petty cash fund replenishment of $500.")
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:consent-calendar-high-value" not in ids


# -- finding: metadata date misalignment -----------------------------------


def test_execution_before_authorization_flagged():
    doc = _doc(
        "Agreement for services.",
        authorization_date="2024-03-15",
        execution_date="2024-02-01",
    )
    findings = detect_vote_date_alignment_anomalies(doc)
    ids = [f["id"] for f in findings]
    assert "vote_date:execution-before-authorization" in ids
    match = next(
        f for f in findings if f["id"] == "vote_date:execution-before-authorization"
    )
    assert match["details"]["days_early"] == 43


def test_normal_date_order_not_flagged():
    doc = _doc(
        "Agreement for services.",
        authorization_date="2024-03-15",
        execution_date="2024-04-01",
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:execution-before-authorization" not in ids


# -- finding: excessive gap ------------------------------------------------


def test_excessive_authorization_execution_gap():
    doc = _doc(
        "Contract for IT services.",
        authorization_date="2024-01-01",
        execution_date="2024-06-15",
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:authorization-execution-gap" in ids


def test_gap_under_90_days_not_flagged():
    doc = _doc(
        "Contract for IT services.",
        authorization_date="2024-01-01",
        execution_date="2024-03-01",
    )
    ids = [f["id"] for f in detect_vote_date_alignment_anomalies(doc)]
    assert "vote_date:authorization-execution-gap" not in ids


# -- finding shape ----------------------------------------------------------


def test_finding_shape():
    doc = _doc(
        "This urgency ordinance is adopted by four-fifths vote and takes effect "
        "retroactively. Consent Calendar: $2,000,000 surveillance contract."
    )
    findings = detect_vote_date_alignment_anomalies(doc)
    assert findings
    for f in findings:
        assert "id" in f
        assert "issue" in f
        assert f["severity"] in ("low", "medium", "high", "critical")
        assert f["layer"] == "vote_date_alignment"
        assert "details" in f
