"""Tests for L-8 Case-Law Currency detector."""

from __future__ import annotations

from odia_legal.detectors.l8_case_law_currency import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ===========================================================================
# Pre-Carpenter third-party doctrine — Smith v. Maryland
# ===========================================================================


def test_smith_v_maryland_in_alpr_context_medium():
    doc = _doc(
        "The department relies on Smith v. Maryland to support its position "
        "that ALPR data collected in public spaces is not subject to Fourth "
        "Amendment protection because citizens voluntarily expose their "
        "location to the public."
    )
    findings = detect(doc)
    f = next(
        (x for x in findings if "smith_v_maryland_third_party_stale" in x["id"]), None
    )
    assert f is not None
    assert f["severity"] == "medium"
    assert f["layer"] == "l8_case_law_currency"


def test_smith_v_maryland_with_carpenter_acknowledged_no_finding():
    doc = _doc(
        "Although Smith v. Maryland (1979) established the third-party doctrine "
        "for pen registers, the Supreme Court held in Carpenter v. United States "
        "(2018) that long-term CSLI and location data require a warrant."
    )
    findings = detect(doc)
    f = [x for x in findings if "smith_v_maryland" in x["id"]]
    assert not f


def test_smith_v_maryland_no_surveillance_context_no_finding():
    doc = _doc(
        "The court cited Smith v. Maryland in analyzing the evidentiary standards "
        "for telephone records subpoenas in a fraud investigation."
    )
    findings = detect(doc)
    f = [x for x in findings if "smith_v_maryland" in x["id"]]
    assert not f


# ===========================================================================
# Pre-Carpenter third-party doctrine — United States v. Miller
# ===========================================================================


def test_miller_in_location_data_context_medium():
    doc = _doc(
        "Under United States v. Miller, the government contends that data "
        "voluntarily shared with third parties — including location tracking "
        "from license plate readers — carries no reasonable expectation of privacy."
    )
    findings = detect(doc)
    f = next((x for x in findings if "us_v_miller_third_party_stale" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_miller_with_carpenter_no_finding():
    doc = _doc(
        "The agency cited United States v. Miller but acknowledged that "
        "Carpenter v. United States limits its application to comprehensive "
        "digital datasets that reveal personal patterns."
    )
    findings = detect(doc)
    f = [x for x in findings if "us_v_miller" in x["id"]]
    assert not f


def test_miller_no_surveillance_no_finding():
    doc = _doc(
        "United States v. Miller (1976) addressed the constitutional status of "
        "bank records subpoenaed by a federal grand jury."
    )
    findings = detect(doc)
    f = [x for x in findings if "us_v_miller" in x["id"]]
    assert not f


# ===========================================================================
# Knotts location-tracking doctrine
# ===========================================================================


def test_knotts_in_gps_tracking_context_medium():
    doc = _doc(
        "The city installed GPS tracking devices on fleet vehicles. Under "
        "Knotts v. United States, movement on public roads carries no "
        "reasonable expectation of privacy."
    )
    findings = detect(doc)
    f = next((x for x in findings if "knotts_location_tracking_stale" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_knotts_in_alpr_context_medium():
    doc = _doc(
        "ALPR data collection is lawful under Knotts v. United States because "
        "vehicles are observed on public streets where persistent surveillance "
        "is occurring."
    )
    findings = detect(doc)
    f = next((x for x in findings if "knotts_location_tracking_stale" in x["id"]), None)
    assert f is not None


def test_knotts_with_carpenter_no_finding():
    doc = _doc(
        "Knotts v. United States supports short-term tracking but, as the Court "
        "held in Carpenter v. United States, long-term location data aggregation "
        "implicates the Fourth Amendment."
    )
    findings = detect(doc)
    f = [x for x in findings if "knotts" in x["id"]]
    assert not f


def test_knotts_no_surveillance_context_no_finding():
    doc = _doc(
        "Knotts v. United States is a beeper tracking case from 1983 that "
        "addressed a single trip's worth of surveillance."
    )
    findings = detect(doc)
    f = [x for x in findings if "knotts" in x["id"]]
    assert not f


# ===========================================================================
# Multiple pre-Carpenter citations in same document
# ===========================================================================


def test_multiple_stale_citations_same_surveillance_doc():
    doc = _doc(
        "The department's ALPR retention policy relies on Smith v. Maryland "
        "for the third-party doctrine and Knotts v. United States to justify "
        "persistent location tracking without a warrant. Under United States v. "
        "Miller, the ALPR records are treated as voluntarily shared information."
    )
    findings = detect(doc)
    ids = [f["id"] for f in findings]
    assert any("smith_v_maryland" in i for i in ids)
    assert any("knotts" in i for i in ids)
    assert any("us_v_miller" in i for i in ids)
    assert len(findings) == 3


# ===========================================================================
# Pre-recodification CPRA case currency
# ===========================================================================


def test_cbs_inc_cpra_case_no_recodification_note_low():
    doc = _doc(
        "Pursuant to CBS Inc. v. Block, the agency may withhold records "
        "that would identify confidential informants under the CPRA exemptions."
    )
    findings = detect(doc)
    f = next(
        (x for x in findings if "pre_recodification_cpra_case_currency" in x["id"]),
        None,
    )
    assert f is not None
    assert f["severity"] == "low"


def test_times_mirror_cpra_case_no_note_low():
    doc = _doc(
        "Times Mirror Co. v. Superior Court established that preliminary "
        "police investigation records are exempt under the CPRA."
    )
    findings = detect(doc)
    f = next(
        (x for x in findings if "pre_recodification_cpra_case_currency" in x["id"]),
        None,
    )
    assert f is not None


def test_old_cpra_case_with_recodification_note_no_finding():
    doc = _doc(
        "Times Mirror Co. v. Superior Court remains good law but the relevant "
        "CPRA exemptions were recodified effective January 1, 2023 under "
        "Gov. Code § 7922.000 et seq. (AB 473, 2021)."
    )
    findings = detect(doc)
    f = [x for x in findings if "pre_recodification" in x["id"]]
    assert not f


def test_old_cpra_case_with_7920_cite_no_finding():
    doc = _doc(
        "CBS Inc. v. Block is controlling, see also the current codification "
        "at Government Code § 7922.000 for the exemption framework."
    )
    findings = detect(doc)
    f = [x for x in findings if "pre_recodification" in x["id"]]
    assert not f


# ===========================================================================
# Live CourtListener lookup — off by default
# ===========================================================================


def test_live_lookup_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("COURTLISTENER_API_KEY", raising=False)
    doc = _doc(
        "The agency relies on Smith v. Maryland and third-party doctrine "
        "for its ALPR data sharing policy."
    )
    findings = detect(doc)
    live = [f for f in findings if "courtlistener" in f["id"]]
    assert not live


def test_live_lookup_disabled_empty_key(monkeypatch):
    monkeypatch.setenv("COURTLISTENER_API_KEY", "")
    doc = _doc(
        "Under CSLI location tracking doctrine, the department relies on "
        "Smith v. Maryland without citing Carpenter."
    )
    findings = detect(doc)
    live = [f for f in findings if "courtlistener" in f["id"]]
    assert not live


# ===========================================================================
# Finding structure and edge cases
# ===========================================================================


def test_empty_doc_returns_empty():
    assert detect({}) == []
    assert detect({"text": ""}) == []
    assert detect({"text": "   "}) == []


def test_non_text_field_ignored():
    doc = {"title": "Smith v. Maryland", "date": "2024-01-01"}
    findings = detect(doc)
    assert findings == []


def test_content_field_used_when_text_absent():
    doc = {
        "content": (
            "The ALPR retention policy relies on Smith v. Maryland to argue "
            "that location tracking data collected from public streets is not "
            "protected under the Fourth Amendment."
        )
    }
    findings = detect(doc)
    f = next((x for x in findings if "smith_v_maryland" in x["id"]), None)
    assert f is not None


def test_finding_ids_start_with_l8():
    doc = _doc(
        "The department uses Smith v. Maryland in its ALPR third-party doctrine "
        "analysis. CBS Inc. v. Block is cited for the CPRA exemption."
    )
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l8:case_law_currency:")
        assert f["layer"] == "l8_case_law_currency"
        assert f["severity"] in ("low", "medium", "high")
        assert isinstance(f["details"], dict)


def test_finding_details_include_current_authority():
    doc = _doc(
        "The agency's ALPR policy relies on Smith v. Maryland, holding that "
        "third-party data collected via license plate readers is not protected "
        "under persistent surveillance programs."
    )
    findings = detect(doc)
    f = next((x for x in findings if "smith_v_maryland" in x["id"]), None)
    assert f is not None
    assert "current_authority" in f["details"]
    assert "limitation" in f["details"]
    assert "cited_case" in f["details"]
    assert "Carpenter" in f["details"]["current_authority"]
