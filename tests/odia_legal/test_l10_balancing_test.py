"""Tests for L-10 Balancing Test Analyzer."""

from __future__ import annotations

from odia_legal.detectors.l10_balancing_test import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ===========================================================================
# Mathews v. Eldridge
# ===========================================================================


def test_mathews_complete_no_finding():
    doc = _doc(
        "Under Mathews v. Eldridge due process balancing, the private interest "
        "in continued benefits is weighty. The risk of erroneous deprivation is "
        "low given the existing safeguards and the value of additional procedure "
        "is minimal. The government's fiscal cost of additional hearings is "
        "substantial. Therefore written notice satisfies procedural due process."
    )
    findings = detect(doc)
    f = [x for x in findings if "mathews" in x["id"]]
    assert not f


def test_mathews_missing_elements_medium():
    doc = _doc(
        "Under Mathews v. Eldridge, we conclude that procedural due process "
        "is satisfied by the current process."
    )
    findings = detect(doc)
    f = next((x for x in findings if "mathews_incomplete" in x["id"]), None)
    assert f is not None
    assert f["severity"] in ("medium", "high")
    assert len(f["details"]["missing_elements"]) >= 1


def test_mathews_all_missing_high():
    doc = _doc("Mathews v. Eldridge applies and the process is adequate.")
    findings = detect(doc)
    f = next((x for x in findings if "mathews_incomplete" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"
    assert len(f["details"]["missing_elements"]) == 3


def test_mathews_not_triggered_no_finding():
    doc = _doc("The ALPR system collects license plate data daily.")
    findings = detect(doc)
    f = [x for x in findings if "mathews" in x["id"]]
    assert not f


# ===========================================================================
# CPRA § 7922.000 balancing
# ===========================================================================


def test_cpra_conclusory_balancing_high():
    doc = _doc(
        "The records are withheld under § 7922.000 because disclosure "
        "is not in the public interest."
    )
    findings = detect(doc)
    f = next((x for x in findings if "cpra_conclusory" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_cpra_balancing_with_times_mirror_no_finding():
    doc = _doc(
        "Under § 7922.000, the public interest in nondisclosure clearly "
        "outweighs the disclosure interest because frank internal deliberation "
        "would be chilled and the deliberative process would be compromised."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra" in x["id"]]
    assert not f


def test_cpra_7922_without_any_analysis_medium():
    doc = _doc("Withheld pursuant to Government Code 7922.000.")
    findings = detect(doc)
    f = next((x for x in findings if "cpra_balancing_absent" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


# ===========================================================================
# Carpenter mosaic
# ===========================================================================


def test_alpr_without_carpenter_medium():
    doc = _doc(
        "The agency deployed ALPR systems to collect persistent location data "
        "on all vehicles passing through the city."
    )
    findings = detect(doc)
    f = next((x for x in findings if "alpr_carpenter_not_analyzed" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_alpr_with_carpenter_no_finding():
    doc = _doc(
        "Carpenter mosaic theory analysis: the ALPR system aggregates data "
        "creating a comprehensive record of daily movements. Individualized "
        "suspicion is required; the third-party doctrine does not apply."
    )
    findings = detect(doc)
    f = [x for x in findings if "alpr_carpenter" in x["id"]]
    assert not f


def test_carpenter_cited_without_elements_medium():
    doc = _doc(
        "Under Carpenter v. United States, the Fourth Amendment applies. "
        "The department has reviewed this policy."
    )
    findings = detect(doc)
    f = next((x for x in findings if "carpenter_elements_missing" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_no_surveillance_no_carpenter_finding():
    doc = _doc("The annual budget was approved by the board.")
    findings = detect(doc)
    f = [x for x in findings if "l10" in x["id"]]
    assert not f


# ===========================================================================
# Edge cases
# ===========================================================================


def test_empty_doc_returns_empty():
    assert detect({}) == []
    assert detect({"text": ""}) == []


def test_finding_fields():
    doc = _doc("The ALPR license plate reader data is collected persistently.")
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l10:")
        assert f["layer"] == "l10_balancing_test"
        assert f["severity"] in ("low", "medium", "high")
        assert "framework" in f["details"] or "statute" in f["details"]
        assert "detail" in f["details"]
