"""Tests for L-3 Exemption Misapplication detector."""

from __future__ import annotations

from odia_legal.detectors.l3_exemption_misapplication import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ---------------------------------------------------------------------------
# Check 1: blanket § 6254(f) / § 7923.650 for ALPR / bulk data
# ---------------------------------------------------------------------------


def test_law_enforcement_blanket_alpr_high():
    doc = _doc(
        "The agency withheld ALPR data under the 7923.650 law enforcement "
        "records exemption."
    )
    findings = detect(doc)
    f = next((x for x in findings if "blanket_alpr" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_law_enforcement_with_investigation_nexus_no_finding():
    doc = _doc(
        "The agency withheld ALPR data under 7923.650 related to active "
        "investigation case number 2024-001."
    )
    findings = detect(doc)
    f = [x for x in findings if "blanket_alpr" in x["id"]]
    assert not f


def test_law_enforcement_no_alpr_no_finding():
    doc = _doc("Records withheld under the 7923.650 law enforcement exemption.")
    findings = detect(doc)
    f = [x for x in findings if "blanket_alpr" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Check 2: § 7923.625 personnel file post-SB 1421
# ---------------------------------------------------------------------------


def test_personnel_file_post_sb1421_medium():
    doc = _doc(
        "The 2022 use of force records were withheld under the personnel file "
        "exemption, section 7923.625."
    )
    findings = detect(doc)
    f = next((x for x in findings if "post_sb1421" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_personnel_file_pre_sb1421_no_finding():
    doc = _doc(
        "The 2017 use of force records were withheld under the peace officer "
        "personnel file exemption 6254(c)."
    )
    findings = detect(doc)
    f = [x for x in findings if "post_sb1421" in x["id"]]
    assert not f


def test_personnel_file_no_sb1421_categories_no_finding():
    doc = _doc(
        "The personnel file for the officer's training records is exempt under "
        "section 7923.625 as of 2023."
    )
    findings = detect(doc)
    f = [x for x in findings if "post_sb1421" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Check 3: § 6255 / § 7922.000 catch-all without balancing test
# ---------------------------------------------------------------------------


def test_catch_all_no_balancing_high():
    doc = _doc(
        "The records are withheld under Government Code 7922.000 because "
        "the public interest in nondisclosure applies."
    )
    findings = detect(doc)
    f = next((x for x in findings if "catch_all_no_balancing" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_catch_all_with_balancing_language_no_finding():
    doc = _doc(
        "Under § 7922.000, the public interest in nondisclosure clearly "
        "outweighs the public interest in disclosure because frank internal "
        "deliberation would be chilled."
    )
    findings = detect(doc)
    f = [x for x in findings if "catch_all_no_balancing" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Check 4: attorney-client overbroad for factual records
# ---------------------------------------------------------------------------


def test_attorney_client_factual_medium():
    doc = _doc(
        "The settlement payment records are protected under attorney-client "
        "privilege per section 7923.700."
    )
    findings = detect(doc)
    f = next((x for x in findings if "overbroad_factual" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_attorney_client_no_factual_context_no_finding():
    doc = _doc(
        "Confidential legal advice from county counsel is protected under "
        "attorney-client privilege section 6254(k)."
    )
    findings = detect(doc)
    f = [x for x in findings if "overbroad_factual" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Check 5: Civil Code § 1798.90.55 scope
# ---------------------------------------------------------------------------


def test_alpr_cpra_exemption_non_operator_low():
    doc = _doc("The department cited Civil Code 1798.90.55 to withhold ALPR records.")
    findings = detect(doc)
    f = next((x for x in findings if "alpr_cpra_exemption_scope" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "low"


def test_alpr_cpra_exemption_operator_context_no_finding():
    doc = _doc(
        "As an ALPR operator under Civil Code 1798.90.51, Flock Safety invoked "
        "§ 1798.90.55 to limit CPRA disclosure."
    )
    findings = detect(doc)
    f = [x for x in findings if "alpr_cpra_exemption_scope" in x["id"]]
    assert not f


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_doc_returns_empty():
    assert detect({"text": ""}) == []
    assert detect({}) == []


def test_no_exemption_language_returns_empty():
    doc = _doc("The annual budget was approved by the board of supervisors.")
    assert detect(doc) == []


def test_finding_fields():
    doc = _doc(
        "The ALPR license plate reader data was withheld under 7923.650 law "
        "enforcement records exemption."
    )
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l3:")
        assert f["severity"] in ("low", "medium", "high")
        assert f["layer"] == "l3_exemption_misapplication"
        assert "statute" in f["details"]
        assert "detail" in f["details"]
