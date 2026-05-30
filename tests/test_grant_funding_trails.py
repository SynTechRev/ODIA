"""Tests for grant_funding_trails detector."""

from oraculus_di_auditor.analysis.grant_funding_trails import (
    detect_grant_funding_trail_anomalies,
)


def _doc(text: str, **kwargs) -> dict:
    return {"raw_text": text, **kwargs}


# -- guard: non-grant document returns no findings --------------------------


def test_no_findings_for_non_grant_document():
    doc = _doc("The council approved the park maintenance schedule.")
    assert detect_grant_funding_trail_anomalies(doc) == []


def test_empty_text_returns_empty():
    assert detect_grant_funding_trail_anomalies({"text": ""}) == []


def test_non_dict_returns_empty():
    assert detect_grant_funding_trail_anomalies("not a dict") == []  # type: ignore


# -- finding: amount without tracking --------------------------------------


def test_grant_amount_without_expenditure_tracking():
    doc = _doc(
        "The JAG grant award of $250,000 was approved for equipment purchases. "
        "No further expenditure documentation was submitted."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:amount-without-tracking" in ids


def test_grant_amount_with_tracking_no_finding():
    doc = _doc(
        "The grant award of $250,000 is subject to quarterly reporting requirements. "
        "Drawdown requests must be submitted to the granting agency monthly."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:amount-without-tracking" not in ids


# -- finding: passthrough without attribution --------------------------------


def test_passthrough_without_federal_attribution():
    doc = _doc(
        "The county will act as a pass-through entity for subgrant funds "
        "distributed to municipal agencies."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:passthrough-without-attribution" in ids


def test_passthrough_with_attribution_no_finding():
    doc = _doc(
        "The county acts as a pass-through entity for DOJ/BJA funds "
        "awarded under the Edward Byrne JAG program."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:passthrough-without-attribution" not in ids


# -- finding: JAG without award number -------------------------------------


def test_jag_without_award_number():
    doc = _doc(
        "The JAG grant funds will be used to purchase body-worn cameras "
        "for the police department."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:jag-without-award-number" in ids


def test_jag_with_award_number_no_finding():
    doc = _doc(
        "Pursuant to JAG award no. 2023-DJ-BX-0042 the department will "
        "purchase equipment as itemised in the approved budget."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:jag-without-award-number" not in ids


# -- finding: amount reconciliation gap ------------------------------------


def test_amount_reconciliation_gap():
    doc = _doc(
        "The federal grant award totalled $1,000,000. "
        "Local matching funds of $50,000 were allocated. "
        "An administrative fee of $5,000 applies. "
        "Equipment purchases of $800,000 were approved under the grant."
    )
    ids = [f["id"] for f in detect_grant_funding_trail_anomalies(doc)]
    assert "grant_trail:amount-reconciliation-gap" in ids


# -- finding shape ----------------------------------------------------------


def test_finding_shape():
    doc = _doc(
        "JAG grant award of $500,000 approved. No drawdown or expenditure "
        "report referenced. Pass-through to subrecipients expected."
    )
    findings = detect_grant_funding_trail_anomalies(doc)
    assert findings
    for f in findings:
        assert "id" in f
        assert "issue" in f
        assert f["severity"] in ("low", "medium", "high", "critical")
        assert f["layer"] == "grant_funding_trails"
        assert "details" in f
