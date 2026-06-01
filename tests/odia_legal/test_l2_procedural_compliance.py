"""Tests for L-2 Procedural Compliance detector."""

from __future__ import annotations

from odia_legal.detectors.l2_procedural_compliance import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ---------------------------------------------------------------------------
# CPRA response timing
# ---------------------------------------------------------------------------


def test_cpra_late_response_high_severity():
    doc = _doc(
        "In response to the public records request, we responded within 45 days."
    )
    findings = detect(doc)
    late = [f for f in findings if "late_response" in f["id"]]
    assert late, "Expected late response finding"
    assert late[0]["severity"] == "high"
    assert late[0]["details"]["days_found"] == [45]


def test_cpra_ten_days_reference_no_timing_finding():
    doc = _doc(
        "The agency responded to the CPRA request within the required 10 calendar days."
    )
    findings = detect(doc)
    late = [f for f in findings if "late_response" in f["id"]]
    assert not late


def test_cpra_request_without_timing_ref_medium():
    doc = _doc(
        "The California Public Records Act request was received and reviewed by staff."
    )
    findings = detect(doc)
    timing_abs = [f for f in findings if "timing_absent" in f["id"]]
    assert timing_abs
    assert timing_abs[0]["severity"] == "medium"


def test_non_cpra_doc_no_timing_finding():
    doc = _doc("The annual budget was approved by the board of supervisors.")
    findings = detect(doc)
    assert findings == []


# ---------------------------------------------------------------------------
# CPRA denial form
# ---------------------------------------------------------------------------


def test_denial_without_statutory_basis_high():
    doc = _doc("The agency denied the CPRA request. The records are exempt.")
    findings = detect(doc)
    basis = [f for f in findings if "missing_statutory_basis" in f["id"]]
    assert basis
    assert basis[0]["severity"] == "high"


def test_denial_with_basis_no_basis_finding():
    doc = _doc(
        "The CPRA request is denied under Government Code 7923.650. "
        "You may seek judicial review under section 7923.115."
    )
    findings = detect(doc)
    basis = [f for f in findings if "missing_statutory_basis" in f["id"]]
    assert not basis


def test_denial_without_appeal_rights_medium():
    doc = _doc("The agency withheld the records. Exemption: 7923.650 applies.")
    findings = detect(doc)
    appeal = [f for f in findings if "missing_appeal_rights" in f["id"]]
    assert appeal
    assert appeal[0]["severity"] == "medium"


def test_denial_with_appeal_rights_no_appeal_finding():
    doc = _doc(
        "Request denied under 7923.650. You have the right to appeal via "
        "writ of mandate under section 7923.115."
    )
    findings = detect(doc)
    appeal = [f for f in findings if "missing_appeal_rights" in f["id"]]
    assert not appeal


# ---------------------------------------------------------------------------
# AB 481
# ---------------------------------------------------------------------------


def test_ab481_missing_annual_report_medium():
    doc = _doc(
        "The department acquired military equipment (AB 481) for patrol operations."
    )
    findings = detect(doc)
    report = [f for f in findings if "annual_report" in f["id"]]
    assert report
    assert report[0]["severity"] == "medium"


def test_ab481_with_annual_report_no_finding():
    doc = _doc(
        "AB 481 military equipment deployed; annual report published in January 2024."
    )
    findings = detect(doc)
    report = [f for f in findings if "annual_report" in f["id"]]
    assert not report


def test_ab481_missing_governing_body_high():
    doc = _doc("The department is using AB 481 surveillance technology.")
    findings = detect(doc)
    gov = [f for f in findings if "governing_body" in f["id"]]
    assert gov
    assert gov[0]["severity"] == "high"


def test_ab481_with_governing_body_approval_no_finding():
    doc = _doc(
        "AB 481 military equipment was approved by the city council via resolution."
    )
    findings = detect(doc)
    gov = [f for f in findings if "governing_body" in f["id"]]
    assert not gov


# ---------------------------------------------------------------------------
# Federal grant — anti-supplanting
# ---------------------------------------------------------------------------


def test_jag_without_anti_supplanting_low():
    doc = _doc("The department received a JAG grant from OJP for equipment.")
    findings = detect(doc)
    anti = [f for f in findings if "anti_supplanting" in f["id"]]
    assert anti
    assert anti[0]["severity"] == "low"


def test_jag_with_anti_supplanting_no_finding():
    doc = _doc(
        "JAG grant funds were used in compliance with anti-supplanting requirements."
    )
    findings = detect(doc)
    anti = [f for f in findings if "anti_supplanting" in f["id"]]
    assert not anti


# ---------------------------------------------------------------------------
# Empty and no-match
# ---------------------------------------------------------------------------


def test_empty_doc_returns_empty():
    assert detect({"text": ""}) == []
    assert detect({}) == []


def test_irrelevant_doc_returns_empty():
    assert detect(_doc("The weather today is sunny.")) == []


# ---------------------------------------------------------------------------
# Finding contract
# ---------------------------------------------------------------------------


def test_finding_fields():
    doc = _doc("Agency denied the CPRA request. Records are exempt.")
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l2:")
        assert f["severity"] in ("low", "medium", "high")
        assert f["layer"] == "l2_procedural_compliance"
        assert "statute" in f["details"]
        assert "detail" in f["details"]
