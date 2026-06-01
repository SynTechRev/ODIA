"""Tests for L-4 Ministerial Duty Analysis detector."""

from __future__ import annotations

from odia_legal.detectors.l4_ministerial_duty import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ===========================================================================
# CPRA 10-day response deadline
# ===========================================================================


def test_cpra_delay_no_extension_high():
    doc = _doc(
        "The public records act request was submitted on March 1. "
        "The agency provided no response for 45 days."
    )
    findings = detect(doc)
    f = next((x for x in findings if "cpra_response_deadline" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_cpra_delay_with_valid_extension_no_finding():
    doc = _doc(
        "The CPRA request was acknowledged. Due to unusual circumstances "
        "involving voluminous records, the agency invoked the 14-day extension "
        "under § 7922.535."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_response_deadline" in x["id"]]
    assert not f


def test_cpra_no_delay_no_finding():
    doc = _doc(
        "The public records request was received and a determination was made "
        "within the required timeframe."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_response_deadline" in x["id"]]
    assert not f


def test_cpra_no_request_no_finding():
    doc = _doc("The annual budget was approved by the city council.")
    findings = detect(doc)
    f = [x for x in findings if "cpra_response_deadline" in x["id"]]
    assert not f


def test_cpra_month_delay_detected():
    doc = _doc("The records request went unanswered for three months.")
    findings = detect(doc)
    f = next((x for x in findings if "cpra_response_deadline" in x["id"]), None)
    assert f is not None


# ===========================================================================
# CPRA extension abuse (§ 7922.535)
# ===========================================================================


def test_extension_no_grounds_medium():
    doc = _doc(
        "The agency invoked unusual circumstances to extend the response "
        "deadline by 14 days."
    )
    findings = detect(doc)
    f = next((x for x in findings if "cpra_extension_no_grounds" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_extension_voluminous_records_no_finding():
    doc = _doc(
        "The agency invoked unusual circumstances due to voluminous records "
        "requiring additional processing time."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_extension_no_grounds" in x["id"]]
    assert not f


def test_extension_offsite_records_no_finding():
    doc = _doc(
        "The department extended the deadline because the records are located "
        "at an off-site facility."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_extension_no_grounds" in x["id"]]
    assert not f


def test_extension_third_party_consultation_no_finding():
    doc = _doc(
        "An additional 14-day extension was needed to consult with a third-party "
        "agency that originated the records."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_extension_no_grounds" in x["id"]]
    assert not f


# ===========================================================================
# AB 481 annual reporting duty
# ===========================================================================


def test_ab481_report_missing_high():
    doc = _doc(
        "The department adopted an AB 481 military equipment use policy in 2022. "
        "The annual report required under Gov. Code § 7072 was not submitted to "
        "the city council."
    )
    findings = detect(doc)
    f = next((x for x in findings if "ab481_annual_report_missing" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_ab481_report_overdue_detected():
    doc = _doc(
        "The AB 481 annual report is overdue. The governing body has not received "
        "the required surveillance equipment usage report."
    )
    findings = detect(doc)
    f = next((x for x in findings if "ab481_annual_report_missing" in x["id"]), None)
    assert f is not None


def test_ab481_no_missing_report_no_finding():
    doc = _doc(
        "The department submitted its AB 481 annual report to the city council "
        "on May 15, 2024 in compliance with Gov. Code § 7072."
    )
    findings = detect(doc)
    f = [x for x in findings if "ab481_annual_report" in x["id"]]
    assert not f


def test_no_ab481_context_no_finding():
    doc = _doc("The annual budget was approved.")
    findings = detect(doc)
    f = [x for x in findings if "ab481" in x["id"]]
    assert not f


# ===========================================================================
# Writ of mandate exposure (§ 1085)
# ===========================================================================


def test_mandatory_language_with_nonperformance_medium():
    doc = _doc(
        "The agency shall provide written notification within 30 days of any "
        "surveillance equipment deployment. The department did not provide "
        "the required notification."
    )
    findings = detect(doc)
    f = next((x for x in findings if "mandatory_duty_nonperformance" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_mandatory_language_with_discretion_qualifier_no_finding():
    doc = _doc(
        "The agency shall provide reports as required by law. However, the "
        "department exercised its discretionary authority to defer reporting "
        "pending further review."
    )
    findings = detect(doc)
    f = [x for x in findings if "mandatory_duty_nonperformance" in x["id"]]
    assert not f


def test_mandatory_language_no_nonperformance_no_finding():
    doc = _doc(
        "The agency shall provide annual reports to the governing body. "
        "The report was submitted on June 1."
    )
    findings = detect(doc)
    f = [x for x in findings if "mandatory_duty_nonperformance" in x["id"]]
    assert not f


def test_must_language_with_failure_detected():
    doc = _doc(
        "The department must adopt a written use policy before deploying any "
        "surveillance technology. The agency failed to adopt any such policy."
    )
    findings = detect(doc)
    f = next((x for x in findings if "mandatory_duty_nonperformance" in x["id"]), None)
    assert f is not None


# ===========================================================================
# CPRA fee limitation (§ 7922.570)
# ===========================================================================


def test_fee_exceeds_direct_cost_low():
    doc = _doc(
        "The agency charged a records copy fee that included staff time and "
        "administrative overhead for locating and reviewing the documents."
    )
    findings = detect(doc)
    f = next((x for x in findings if "cpra_fee_exceeds_direct_cost" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "low"


def test_fee_with_exception_cited_no_finding():
    doc = _doc(
        "The per-page fee included computer extraction costs under the "
        "§ 7922.570 exception for electronic compilation."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_fee_exceeds_direct_cost" in x["id"]]
    assert not f


def test_standard_copy_fee_no_finding():
    doc = _doc(
        "Copies are available at the standard per-page duplication fee of "
        "$0.10 per page."
    )
    findings = detect(doc)
    f = [x for x in findings if "cpra_fee" in x["id"]]
    assert not f


# ===========================================================================
# Finding structure and edge cases
# ===========================================================================


def test_empty_doc_returns_empty():
    assert detect({}) == []
    assert detect({"text": ""}) == []


def test_finding_ids_start_with_l4():
    doc = _doc(
        "The public records act request received no response for 30 days. "
        "The agency shall notify requesters but did not provide any notification."
    )
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l4:")
        assert f["layer"] == "l4_ministerial_duty"
        assert f["severity"] in ("low", "medium", "high")
        assert "statute" in f["details"]
        assert "detail" in f["details"]


def test_multiple_violations_returned():
    doc = _doc(
        "The public records request was not responded to for 60 days. "
        "The agency invoked additional time without stating any grounds. "
        "The agency shall provide AB 481 reports but failed to file the annual report."
    )
    findings = detect(doc)
    assert len(findings) >= 2
