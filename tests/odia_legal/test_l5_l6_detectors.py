"""Tests for L-5 Federal Grant Compliance and L-6 Constitutional Implication."""

from __future__ import annotations

from odia_legal.detectors.l5_federal_grant_compliance import detect as detect_l5
from odia_legal.detectors.l6_constitutional_implication import detect as detect_l6


def _doc(text: str) -> dict:
    return {"text": text}


# ===========================================================================
# L-5 Federal Grant Compliance
# ===========================================================================


# ---------------------------------------------------------------------------
# No JAG context — all checks skip
# ---------------------------------------------------------------------------


def test_l5_no_jag_returns_empty():
    doc = _doc("The department purchased equipment for patrol operations.")
    assert detect_l5(doc) == []


def test_l5_empty_doc_returns_empty():
    assert detect_l5({}) == []


# ---------------------------------------------------------------------------
# Supplanting
# ---------------------------------------------------------------------------


def test_l5_supplanting_high():
    doc = _doc(
        "The JAG grant funds replaced local funds that would have been "
        "used for the same patrol program."
    )
    findings = detect_l5(doc)
    f = next((x for x in findings if "supplanting" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_l5_supplement_no_supplanting_finding():
    doc = _doc(
        "JAG grant funds supplement existing local funding for the program. "
        "Anti-supplanting requirement satisfied."
    )
    findings = detect_l5(doc)
    f = [x for x in findings if "supplanting" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Sole-source procurement
# ---------------------------------------------------------------------------


def test_l5_sole_source_no_justification_medium():
    doc = _doc(
        "The federal grant funds were used to purchase Axon body cameras "
        "via sole source procurement from the vendor."
    )
    findings = detect_l5(doc)
    f = next((x for x in findings if "sole_source" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_l5_sole_source_with_justification_no_finding():
    doc = _doc(
        "The JAG-funded purchase was a sole source because Axon holds "
        "proprietary equipment rights — sole source justification on file."
    )
    findings = detect_l5(doc)
    f = [x for x in findings if "sole_source" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Equipment purchase
# ---------------------------------------------------------------------------


def test_l5_equipment_no_prior_approval_low():
    doc = _doc(
        "The department purchased $15,000 in ALPR equipment using JAG funds."
    )
    findings = detect_l5(doc)
    f = next((x for x in findings if "equipment" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "low"


# ---------------------------------------------------------------------------
# Subrecipient monitoring
# ---------------------------------------------------------------------------


def test_l5_subrecipient_no_monitoring_medium():
    doc = _doc(
        "The JAG award was passed through as a subaward to the county "
        "sheriff's department."
    )
    findings = detect_l5(doc)
    f = next((x for x in findings if "subrecipient" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_l5_subrecipient_with_monitoring_no_finding():
    doc = _doc(
        "The JAG subaward was monitored through quarterly performance reports "
        "and an annual site visit per 2 CFR 200.331."
    )
    findings = detect_l5(doc)
    f = [x for x in findings if "subrecipient" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Unallowable costs
# ---------------------------------------------------------------------------


def test_l5_unallowable_cost_high():
    doc = _doc(
        "The federal grant budget includes $5,000 for entertainment expense "
        "and an officer's criminal defense fee."
    )
    findings = detect_l5(doc)
    f = next((x for x in findings if "unallowable" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


# ---------------------------------------------------------------------------
# Finding contract
# ---------------------------------------------------------------------------


def test_l5_finding_fields():
    doc = _doc(
        "The JAG funds replaced the city's local funding that would have been "
        "used for the same patrol program."
    )
    findings = detect_l5(doc)
    for f in findings:
        assert f["id"].startswith("legal:l5:")
        assert f["layer"] == "l5_federal_grant_compliance"
        assert f["severity"] in ("low", "medium", "high")
        assert "statute" in f["details"]
        assert "detail" in f["details"]


# ===========================================================================
# L-6 Constitutional Implication
# ===========================================================================


def test_l6_empty_doc_returns_empty():
    assert detect_l6({}) == []


# ---------------------------------------------------------------------------
# Carpenter / location surveillance
# ---------------------------------------------------------------------------


def test_l6_alpr_without_carpenter_high():
    doc = _doc(
        "The agency deployed ALPR license plate readers to track vehicle "
        "movements throughout the city."
    )
    findings = detect_l6(doc)
    f = next((x for x in findings if "carpenter" in x["id"] or "location" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_l6_alpr_with_carpenter_no_finding():
    doc = _doc(
        "The ALPR system was reviewed under the Carpenter mosaic theory. "
        "Fourth Amendment analysis confirms warrant requirement applies."
    )
    findings = detect_l6(doc)
    f = [x for x in findings if "location_surveillance_no_carpenter" in x["id"]]
    assert not f


def test_l6_warrantless_location_high():
    doc = _doc(
        "License plate reader data collected without a warrant using the "
        "third-party doctrine exception."
    )
    findings = detect_l6(doc)
    assert any(f["severity"] == "high" for f in findings)


# ---------------------------------------------------------------------------
# Facial recognition
# ---------------------------------------------------------------------------


def test_l6_facial_recognition_no_analysis_medium():
    doc = _doc(
        "The department uses Clearview AI facial recognition for investigations."
    )
    findings = detect_l6(doc)
    f = next((x for x in findings if "facial_recognition" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_l6_facial_recognition_with_analysis_no_finding():
    doc = _doc(
        "Facial recognition use was reviewed for equal protection implications; "
        "disparate impact analysis completed."
    )
    findings = detect_l6(doc)
    f = [x for x in findings if "facial_recognition" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Stingray / cell-site simulator
# ---------------------------------------------------------------------------


def test_l6_stingray_no_warrant_high():
    doc = _doc(
        "The department deployed a stingray IMSI catcher to collect location data."
    )
    findings = detect_l6(doc)
    f = next((x for x in findings if "stingray" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_l6_stingray_with_warrant_no_finding():
    doc = _doc(
        "Cell-site simulator deployed pursuant to a court order and warrant "
        "signed by the magistrate judge."
    )
    findings = detect_l6(doc)
    f = [x for x in findings if "stingray_no_warrant" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Finding contract
# ---------------------------------------------------------------------------


def test_l6_finding_fields():
    doc = _doc(
        "The department deployed ALPR cameras tracking vehicles across the city."
    )
    findings = detect_l6(doc)
    for f in findings:
        assert f["id"].startswith("legal:l6:")
        assert f["layer"] == "l6_constitutional_implication"
        assert f["severity"] in ("low", "medium", "high")
        assert "statute" in f["details"]
        assert "detail" in f["details"]
