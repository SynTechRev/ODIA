"""Tests for L-1 Statutory Applicability detector."""

from __future__ import annotations

from odia_legal.detectors.l1_statutory_applicability import (
    detect,
    detect_applicable_statutes,
)


def _doc(text: str) -> dict:
    return {"text": text}


# ---------------------------------------------------------------------------
# ALPR / SB 34 triggers
# ---------------------------------------------------------------------------


def test_alpr_triggers_sb34():
    doc = _doc("The agency deployed ALPR systems to collect license plate reader data.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Civ. Code § 1798.90.51" in statutes
    assert "Veh. Code § 2413" in statutes


def test_alpr_retention_triggered():
    doc = _doc("Data retention policy for ALPR data is 90 days.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Civ. Code § 1798.90.53" in statutes


def test_flock_safety_triggers_alpr():
    doc = _doc("The department purchased Flock Safety cameras for surveillance.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Civ. Code § 1798.90.51" in statutes


# ---------------------------------------------------------------------------
# AB 481 surveillance technology
# ---------------------------------------------------------------------------


def test_ab481_triggers_on_military_equipment():
    doc = _doc(
        "The police department requested approval for military equipment acquisition."
    )
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Gov. Code § 36000" in statutes


def test_ab481_triggers_on_drone():
    doc = _doc("The agency acquired UAS drones for aerial surveillance operations.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Gov. Code § 36000" in statutes


def test_bwc_triggers_ab481():
    doc = _doc("Officers were equipped with Axon body cameras (BWC) in 2023.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Gov. Code § 36000" in statutes


# ---------------------------------------------------------------------------
# CPRA
# ---------------------------------------------------------------------------


def test_cpra_request_triggers_cpra():
    doc = _doc(
        "The requester filed a California Public Records Act request for records."
    )
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Gov. Code § 7920.000" in statutes


def test_withhold_triggers_law_enforcement_exemption():
    doc = _doc("The agency refused to disclose investigative records citing 7923.650.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Gov. Code § 7923.650" in statutes


# ---------------------------------------------------------------------------
# Federal grants
# ---------------------------------------------------------------------------


def test_jag_triggers_34usc():
    doc = _doc(
        "The department received a JAG grant from the Bureau of Justice Assistance."
    )
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "34 U.S.C. § 10152" in statutes


def test_federal_grant_triggers_uniform_guidance():
    doc = _doc(
        "The federal grant expenditures must comply with Uniform Guidance requirements."
    )
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "2 C.F.R. § 200.303" in statutes


# ---------------------------------------------------------------------------
# Peace officer records
# ---------------------------------------------------------------------------


def test_sb1421_triggers_pen_832_7():
    doc = _doc(
        "SB 1421 requires disclosure of use of force records for peace officers."
    )
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Pen. Code § 832.7" in statutes


def test_officer_discipline_triggers_sb1421():
    doc = _doc("Internal affairs investigation into officer misconduct sustained.")
    findings = detect(doc)
    statutes = {f["details"]["statute"] for f in findings}
    assert "Pen. Code § 832.7" in statutes


# ---------------------------------------------------------------------------
# Empty doc and no match
# ---------------------------------------------------------------------------


def test_empty_doc_returns_empty():
    assert detect({"text": ""}) == []
    assert detect({}) == []


def test_no_triggers_returns_empty():
    doc = _doc("Annual budget report for fiscal year 2024 approved.")
    findings = detect(doc)
    assert findings == []


# ---------------------------------------------------------------------------
# Finding contract
# ---------------------------------------------------------------------------


def test_finding_has_required_fields():
    doc = _doc("ALPR license plate reader system deployed without a privacy policy.")
    findings = detect(doc)
    assert findings
    for f in findings:
        assert f["id"].startswith("legal:l1:")
        assert f["severity"] == "low"
        assert f["layer"] == "l1_statutory_applicability"
        d = f["details"]
        assert "statute" in d
        assert "corpus_id" in d
        assert "trigger_terms" in d
        assert "relevance" in d
        assert isinstance(d["trigger_terms"], list)


def test_detect_applicable_statutes_returns_list():
    doc = _doc("The ALPR system collects license plate data for law enforcement.")
    statutes = detect_applicable_statutes(doc)
    assert isinstance(statutes, list)
    assert len(statutes) >= 1
    assert all(isinstance(s, str) for s in statutes)


def test_deduplication_same_statute_once():
    doc = _doc("ALPR license plate reader ALPR license plate reader ALPR")
    findings = detect(doc)
    statutes = [f["details"]["statute"] for f in findings]
    assert len(statutes) == len(set(statutes))
