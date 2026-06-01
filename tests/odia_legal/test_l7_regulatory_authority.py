"""Tests for L-7 Regulatory Authority Chains detector."""

from __future__ import annotations

from odia_legal.detectors.l7_regulatory_authority import detect


def _doc(text: str) -> dict:
    return {"text": text}


# ===========================================================================
# Ultra vires
# ===========================================================================


def test_explicit_ultra_vires_language_high():
    doc = _doc(
        "The city acted beyond its authority in entering into the contract. "
        "The action was ultra vires and should be declared void."
    )
    findings = detect(doc)
    f = next((x for x in findings if "ultra_vires_action" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "high"


def test_exceeded_authority_language_high():
    doc = _doc(
        "The department exceeded its jurisdiction by issuing the directive "
        "without legislative authorization."
    )
    findings = detect(doc)
    f = next((x for x in findings if "ultra_vires_action" in x["id"]), None)
    assert f is not None


def test_action_without_authority_cite_low():
    doc = _doc(
        "The agency deployed facial recognition technology at all city intersections."
    )
    findings = detect(doc)
    f = next((x for x in findings if "action_without_authority_cite" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "low"


def test_action_with_authority_cite_no_finding():
    doc = _doc(
        "The agency deployed ALPR pursuant to Ordinance No. 4821 and "
        "in accordance with Gov. Code § 7070."
    )
    findings = detect(doc)
    f = [x for x in findings if "ultra_vires" in x["id"] or "action_without" in x["id"]]
    assert not f


def test_no_action_verb_no_finding():
    doc = _doc("The annual report summarizes department activities.")
    findings = detect(doc)
    f = [x for x in findings if "ultra_vires" in x["id"]]
    assert not f


# ===========================================================================
# Sub-delegation without authorization
# ===========================================================================


def test_delegation_no_authority_medium():
    doc = _doc(
        "The chief of police delegated authority to the technology vendor "
        "to manage and operate the ALPR network."
    )
    findings = detect(doc)
    f = next((x for x in findings if "subdelegation_no_authority" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_delegation_with_53060_no_finding():
    doc = _doc(
        "Pursuant to Gov. Code § 53060, the director delegated operational "
        "authority to the contracted vendor."
    )
    findings = detect(doc)
    f = [x for x in findings if "subdelegation" in x["id"]]
    assert not f


def test_delegation_with_charter_no_finding():
    doc = _doc(
        "The city manager assigned authority to the department director "
        "as authorized under Charter Section 612."
    )
    findings = detect(doc)
    f = [x for x in findings if "subdelegation" in x["id"]]
    assert not f


def test_no_delegation_language_no_finding():
    doc = _doc("The department budget was approved by the council.")
    findings = detect(doc)
    f = [x for x in findings if "subdelegation" in x["id"]]
    assert not f


# ===========================================================================
# Chain-of-authority gap (MOU / directive without cite)
# ===========================================================================


def test_mou_without_authority_medium():
    doc = _doc(
        "The department entered into a memorandum of understanding with the "
        "county sheriff to share ALPR data."
    )
    findings = detect(doc)
    f = next((x for x in findings if "authority_chain_gap" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "medium"


def test_mou_with_authority_cite_no_finding():
    doc = _doc(
        "The memorandum of understanding was entered into pursuant to "
        "Gov. Code § 6502, which authorizes joint exercise of powers."
    )
    findings = detect(doc)
    f = [x for x in findings if "authority_chain_gap" in x["id"]]
    assert not f


def test_general_order_without_cite_medium():
    doc = _doc(
        "General Order 14-22 directs officers to collect and upload all "
        "ALPR data to the regional sharing platform."
    )
    findings = detect(doc)
    f = next((x for x in findings if "authority_chain_gap" in x["id"]), None)
    assert f is not None


def test_admin_directive_with_statute_no_finding():
    doc = _doc(
        "Administrative Directive 2024-03 was issued under the authority of "
        "§ 7070 of the Government Code."
    )
    findings = detect(doc)
    f = [x for x in findings if "authority_chain_gap" in x["id"]]
    assert not f


# ===========================================================================
# State law preemption
# ===========================================================================


def test_ordinance_conflicts_with_state_law_high():
    doc = _doc(
        "The city enacted an ordinance that notwithstanding state law "
        "permits law enforcement to retain ALPR data for five years."
    )
    findings = detect(doc)
    f = next(
        (x for x in findings if "ordinance_exceeds_state_preemption" in x["id"]), None
    )
    assert f is not None
    assert f["severity"] == "high"


def test_ordinance_with_home_rule_no_finding():
    doc = _doc(
        "As a charter city exercising its home rule authority under "
        "Cal. Const. art. XI § 5, the city adopted an ordinance that "
        "supersedes the state retention requirement."
    )
    findings = detect(doc)
    f = [x for x in findings if "ordinance_exceeds_state_preemption" in x["id"]]
    assert not f


def test_local_ordinance_no_conflict_no_finding():
    doc = _doc(
        "The city enacted an ordinance establishing a community oversight board "
        "for police accountability."
    )
    findings = detect(doc)
    f = [x for x in findings if "preemption" in x["id"]]
    assert not f


# ===========================================================================
# Federal grant scope
# ===========================================================================


def test_grant_scope_exceeded_low():
    doc = _doc(
        "The department used JAG grant funds to purchase equipment that was "
        "not included in the grant award scope."
    )
    findings = detect(doc)
    f = next((x for x in findings if "federal_grant_scope_exceeded" in x["id"]), None)
    assert f is not None
    assert f["severity"] == "low"


def test_grant_scope_with_amendment_no_finding():
    doc = _doc(
        "The equipment purchase was outside the original grant scope but was "
        "approved via a scope change amendment under 2 CFR § 200.308."
    )
    findings = detect(doc)
    f = [x for x in findings if "federal_grant_scope_exceeded" in x["id"]]
    assert not f


def test_no_federal_grant_no_finding():
    doc = _doc("The department purchased vehicles using the general fund.")
    findings = detect(doc)
    f = [x for x in findings if "grant_scope" in x["id"]]
    assert not f


# ===========================================================================
# Finding structure and edge cases
# ===========================================================================


def test_empty_doc_returns_empty():
    assert detect({}) == []
    assert detect({"text": ""}) == []


def test_finding_ids_start_with_l7():
    doc = _doc(
        "The agency delegated authority to a contractor without citing § 53060. "
        "The action was taken beyond its jurisdiction."
    )
    findings = detect(doc)
    for f in findings:
        assert f["id"].startswith("legal:l7:")
        assert f["layer"] == "l7_regulatory_authority"
        assert f["severity"] in ("low", "medium", "high")
        assert "detail" in f["details"]


def test_multiple_violations_returned():
    doc = _doc(
        "The agency deployed surveillance systems without citing any ordinance. "
        "The chief delegated authority to the vendor with no mention of § 53060. "
        "The department also entered a memorandum of understanding with no "
        "statutory citation."
    )
    findings = detect(doc)
    assert len(findings) >= 2
