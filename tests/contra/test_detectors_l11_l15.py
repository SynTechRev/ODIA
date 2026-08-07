"""Tests for C.O.N.T.R.A. detectors L-11 through L-15 (Phase C).

Tests are organized in three tiers:
  1. Unit tests: targeted snippets that fire exactly one sub-detector
  2. Golden reference tests: full synthetic contracts from tests/contra/golden/
  3. Negative / clean contract tests: verify no spurious findings on G-03
"""

from __future__ import annotations

from pathlib import Path

from oraculus_di_auditor.contra import (
    Finding,
    L11ArbitrationArchitecture,
    L12ChoiceOfLawForum,
    L13UnilateralModification,
    L14DataCollectionDepth,
    L15DataRetention,
    Severity,
)
from oraculus_di_auditor.contra.anchors import ALL_ANCHORS

_GOLDEN = Path(__file__).parent / "golden"

_META = {
    "document_hash": "a" * 64,
    "entity_id": "test-entity",
    "entity_name": "Test Entity Corp",
    "doc_type": "tos",
}


def _load_golden(filename: str) -> str:
    return (_GOLDEN / filename).read_text(encoding="utf-8")


def _has_sub(findings: list[Finding], sub: str) -> bool:
    return any(f.sub_detector == sub for f in findings)


def _get_sub(findings: list[Finding], sub: str) -> list[Finding]:
    return [f for f in findings if f.sub_detector == sub]


def _anchors_valid(findings: list[Finding]) -> bool:
    return all(f.doctrinal_anchor in ALL_ANCHORS for f in findings)


def _excerpts_valid(findings: list[Finding]) -> bool:
    return all(len(f.evidence_span.verbatim_excerpt.split()) <= 15 for f in findings)


# ===========================================================================
# L-11 Arbitration Architecture
# ===========================================================================


def _l11() -> L11ArbitrationArchitecture:
    return L11ArbitrationArchitecture()


def test_l11_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    assert isinstance(_l11(), Detector)
    assert _l11().layer == "L-11"


def test_l11a_binding_arbitration() -> None:
    text = "Any dispute shall be resolved by binding mandatory arbitration."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l11b_class_action_waiver() -> None:
    text = (
        "You waive any right to participate in a class action or collective action. "
        "Class-wide arbitration is prohibited."
    )
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.CRITICAL


def test_l11c_faa_invocation() -> None:
    text = "The Federal Arbitration Act governs this arbitration agreement."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.MEDIUM


def test_l11d_administrator_jams() -> None:
    text = "Arbitration shall be administered by JAMS under its Consumer Rules."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.LOW


def test_l11d_administrator_aaa() -> None:
    text = "American Arbitration Association rules shall govern."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "D")


def test_l11e_fee_allocation_split() -> None:
    text = "Each party shall bear its own arbitration costs and fees."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.HIGH


def test_l11f_non_ca_venue() -> None:
    text = (
        "Any arbitration proceeding shall take place in New York, New York. "
        "The venue for arbitration is New York."
    )
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "F")


def test_l11g_loser_pays() -> None:
    text = "The losing party shall pay all arbitration costs and attorney fees."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.CRITICAL


def test_l11h_discovery_limits() -> None:
    text = "Discovery shall be limited to two document requests per side. No depositions are permitted."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "H")


def test_l11i_confidentiality() -> None:
    text = (
        "All arbitration proceedings shall be kept confidential. The award is private."
    )
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "I")


def test_l11j_no_appeal() -> None:
    text = "The arbitration award shall be final and binding. No appeal shall be available."
    findings = _l11().scan(text, _META)
    assert _has_sub(findings, "J")
    assert _get_sub(findings, "J")[0].severity == Severity.HIGH


def test_l11_golden_g01_all_subs_present() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l11().scan(text, _META)
    for sub in "ABCDEFGHIJ":
        assert _has_sub(findings, sub), f"L-11{sub} not detected in G-01"


def test_l11_golden_g01_anchors_valid() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l11().scan(text, _META)
    assert _anchors_valid(findings)


def test_l11_golden_g01_excerpts_valid() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l11().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l11_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l11().scan(text, _META)
    assert (
        findings == []
    ), f"Expected no L-11 findings on G-03, got {len(findings)}: {[f.sub_detector for f in findings]}"


def test_l11_finding_id_unique() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l11().scan(text, _META)
    ids = [f.finding_id for f in findings]
    assert len(ids) == len(set(ids)), "Duplicate finding_ids detected"


# ===========================================================================
# L-12 Choice of Law / Forum
# ===========================================================================


def _l12() -> L12ChoiceOfLawForum:
    return L12ChoiceOfLawForum()


def test_l12_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    assert isinstance(_l12(), Detector)
    assert _l12().layer == "L-12"


def test_l12a_delaware_governing_law() -> None:
    text = "These Terms are governed by the laws of the State of Delaware."
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.MEDIUM


def test_l12b_exclusive_new_york_forum() -> None:
    text = "You submit to the exclusive jurisdiction of the courts of New York."
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "B")


def test_l12c_shortened_limitation_period() -> None:
    text = "Any claim must be brought within one (1) year of the event giving rise to the claim."
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.HIGH


def test_l12c_shortened_180_days() -> None:
    text = "You must file any action within 180 days of the event."
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "C")


def test_l12d_ccpa_rights_waiver() -> None:
    text = "You waive any rights under the California Consumer Privacy Act (CCPA)."
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.CRITICAL


def test_l12e_integration_clause() -> None:
    text = (
        "This Agreement constitutes the entire agreement and supersedes all prior "
        "representations and understandings."
    )
    findings = _l12().scan(text, _META)
    assert _has_sub(findings, "E")


def test_l12_golden_g01_anchors_valid() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l12().scan(text, _META)
    assert _anchors_valid(findings)
    # G-01 has Delaware governing law, exclusive venue, SOL, CCPA waiver, integration
    for sub in "ACDE":
        assert _has_sub(findings, sub), f"L-12{sub} not detected in G-01"


def test_l12_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l12().scan(text, _META)
    assert findings == [], f"Expected no L-12 findings on G-03, got {len(findings)}"


# ===========================================================================
# L-13 Unilateral Modification
# ===========================================================================


def _l13() -> L13UnilateralModification:
    return L13UnilateralModification()


def test_l13_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    assert isinstance(_l13(), Detector)
    assert _l13().layer == "L-13"


def test_l13a_unilateral_modify() -> None:
    text = "We may modify these Terms at any time."
    findings = _l13().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l13b_website_only_notice() -> None:
    text = (
        "We will notify you by posting an updated version on our website. "
        "Such posting constitutes notice to you."
    )
    findings = _l13().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.MEDIUM


def test_l13c_continued_use_acceptance() -> None:
    text = "Continued use of the Service constitutes your acceptance of the modified Terms."
    findings = _l13().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.CRITICAL


def test_l13d_retroactive_modification() -> None:
    text = "Modifications shall apply retroactively to any prior claims or disputes."
    findings = _l13().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.HIGH


def test_l13e_no_optout_when_modify_present() -> None:
    text = "We reserve the right to change these terms at any time without notice."
    findings = _l13().scan(text, _META)
    # A fires (unilateral modify), E fires (no opt-out path)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.LOW


def test_l13e_no_fire_when_optout_present() -> None:
    text = "We may update these Terms. If you disagree, you may opt-out by closing your account."
    findings = _l13().scan(text, _META)
    # A fires but E should NOT fire (opt-out present)
    assert not _has_sub(
        findings, "E"
    ), "E should not fire when opt-out mechanism is present"


def test_l13_golden_g01_all_subs_present() -> None:
    text = _load_golden("g01_full_arbitration_tos.txt")
    findings = _l13().scan(text, _META)
    for sub in "ABCD":
        assert _has_sub(findings, sub), f"L-13{sub} not detected in G-01"


def test_l13_clean_g03_no_c_or_d() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l13().scan(text, _META)
    # G-03 has modification language but with advance email notice and opt-out
    # should NOT fire C (continued use) or D (retroactive)
    assert not _has_sub(findings, "C"), "L-13C (continued-use) should not fire on G-03"
    assert not _has_sub(findings, "D"), "L-13D (retroactive) should not fire on G-03"


# ===========================================================================
# L-14 Data Collection Depth
# ===========================================================================


def _l14() -> L14DataCollectionDepth:
    return L14DataCollectionDepth()


def test_l14_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    assert isinstance(_l14(), Detector)
    assert _l14().layer == "L-14"


def test_l14a_identifiers() -> None:
    text = "We collect your name, email address, and IP address."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "A")


def test_l14b_financial_records() -> None:
    text = "We collect financial information including your bank account and credit history."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "B")


def test_l14c_protected_classifications() -> None:
    text = "We may collect your race, ethnicity, and gender identity."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.HIGH


def test_l14d_commercial_transactions() -> None:
    text = "We collect your purchase history and transaction records."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "D")


def test_l14e_biometric() -> None:
    text = "We collect biometric information including fingerprint data and facial recognition templates."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.CRITICAL


def test_l14f_internet_activity() -> None:
    text = "We collect your browsing history, search history, and pages visited."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "F")


def test_l14g_geolocation() -> None:
    text = "We collect precise geolocation data and real-time location information."
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.HIGH


def test_l14h_inferences() -> None:
    text = (
        "We create profiles about you and build predictive models of your preferences."
    )
    findings = _l14().scan(text, _META)
    assert _has_sub(findings, "H")


def test_l14i_spi_aggregate_multiple_categories() -> None:
    text = (
        "We collect biometric identifiers including facial recognition. "
        "We also collect precise geolocation data."
    )
    findings = _l14().scan(text, _META)
    assert _has_sub(
        findings, "I"
    ), "L-14I (SPI aggregate) should fire with 2 SPI sub-types"
    assert _get_sub(findings, "I")[0].severity == Severity.CRITICAL


def test_l14i_no_fire_on_single_spi_type() -> None:
    text = "We collect biometric fingerprint data only."
    findings = _l14().scan(text, _META)
    # E (biometric) should fire; I should NOT (only 1 SPI type)
    assert _has_sub(findings, "E")
    assert not _has_sub(findings, "I"), "L-14I should not fire with only 1 SPI sub-type"


def test_l14_golden_g02_all_major_cats() -> None:
    text = _load_golden("g02_privacy_notice_full_data.txt")
    findings = _l14().scan(text, _META)
    for sub in "ABCDEFGHI":
        assert _has_sub(findings, sub), f"L-14{sub} not detected in G-02"


def test_l14_golden_g02_anchors_valid() -> None:
    text = _load_golden("g02_privacy_notice_full_data.txt")
    findings = _l14().scan(text, _META)
    assert _anchors_valid(findings)


def test_l14_golden_g02_excerpts_valid() -> None:
    text = _load_golden("g02_privacy_notice_full_data.txt")
    findings = _l14().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l14_clean_g03_minimal_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l14().scan(text, _META)
    # G-03 mentions name and email only -- may fire A (identifiers)
    critical_findings = [f for f in findings if f.severity == Severity.CRITICAL]
    assert (
        not critical_findings
    ), f"No CRITICAL findings expected on G-03: {critical_findings}"
    for sub in "BCEFGHI":
        assert not _has_sub(
            findings, sub
        ), f"L-14{sub} should not fire on clean contract G-03"


# ===========================================================================
# L-15 Data Retention
# ===========================================================================


def _l15() -> L15DataRetention:
    return L15DataRetention()


def test_l15_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    assert isinstance(_l15(), Detector)
    assert _l15().layer == "L-15"


def test_l15a_no_retention_period() -> None:
    text = "We collect your name, email address, and usage data."
    findings = _l15().scan(text, _META)
    assert _has_sub(
        findings, "A"
    ), "L-15A should fire when collection present but no retention period"
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l15a_no_fire_when_retention_defined() -> None:
    text = (
        "We collect your name and email address. "
        "We retain your information for no more than two years after account closure."
    )
    findings = _l15().scan(text, _META)
    assert not _has_sub(
        findings, "A"
    ), "L-15A should not fire when retention period is defined"


def test_l15b_vague_retention() -> None:
    text = (
        "We retain your information for as long as necessary for our business purposes."
    )
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.MEDIUM


def test_l15b_indefinite_retention() -> None:
    text = "Your data may be retained indefinitely."
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "B")


def test_l15c_third_party_retention() -> None:
    text = (
        "We share your data with third-party partners who retain data "
        "according to their own data retention policies."
    )
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.HIGH


def test_l15d_post_termination_retention() -> None:
    text = (
        "After termination of your account, we may retain your personal information "
        "for fraud prevention and legal compliance."
    )
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.MEDIUM


def test_l15e_data_broker_trigger() -> None:
    text = (
        "We sell consumer personal data to data broker partners for marketing purposes."
    )
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.HIGH


def test_l15f_biometric_no_limit() -> None:
    text = "We collect and store biometric data including fingerprint information."
    findings = _l15().scan(text, _META)
    assert _has_sub(findings, "F")
    assert _get_sub(findings, "F")[0].severity == Severity.CRITICAL


def test_l15f_no_fire_when_biometric_has_deletion_limit() -> None:
    text = (
        "We collect biometric fingerprint data. "
        "Biometric data is purged within 90 days of collection."
    )
    findings = _l15().scan(text, _META)
    assert not _has_sub(
        findings, "F"
    ), "L-15F should not fire when deletion limit exists"


def test_l15_golden_g02_all_subs() -> None:
    text = _load_golden("g02_privacy_notice_full_data.txt")
    findings = _l15().scan(text, _META)
    for sub in "ABCDEF":
        assert _has_sub(findings, sub), f"L-15{sub} not detected in G-02"


def test_l15_golden_g02_anchors_valid() -> None:
    text = _load_golden("g02_privacy_notice_full_data.txt")
    findings = _l15().scan(text, _META)
    assert _anchors_valid(findings)


def test_l15_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l15().scan(text, _META)
    # G-03 has defined retention period (2 years) and deletion within 30 days
    assert findings == [], (
        f"Expected no L-15 findings on G-03, got: "
        f"{[(f.sub_detector, f.severity) for f in findings]}"
    )


# ===========================================================================
# Cross-detector: Detector protocol compliance
# ===========================================================================


def test_all_detectors_implement_protocol() -> None:
    from oraculus_di_auditor.contra import Detector

    for cls in [
        L11ArbitrationArchitecture,
        L12ChoiceOfLawForum,
        L13UnilateralModification,
        L14DataCollectionDepth,
        L15DataRetention,
    ]:
        assert isinstance(
            cls(), Detector
        ), f"{cls.__name__} does not implement Detector protocol"


def test_all_detectors_return_list_of_findings_on_empty_text() -> None:
    for cls in [
        L11ArbitrationArchitecture,
        L12ChoiceOfLawForum,
        L13UnilateralModification,
        L14DataCollectionDepth,
        L15DataRetention,
    ]:
        result = cls().scan("", _META)
        assert isinstance(result, list), f"{cls.__name__}.scan() did not return a list"
        assert result == [], f"{cls.__name__}.scan('') should return empty list"


def test_prompt_version_dataclass() -> None:
    from oraculus_di_auditor.llm.contra_prompts import (
        L11_CLAUSE_EXTRACT,
        L13_MODIFICATION_NOTICE,
        L14_CCPA_CATEGORY,
        L15_RETENTION_DURATION,
        PromptVersion,
    )

    for pv in [
        L11_CLAUSE_EXTRACT,
        L13_MODIFICATION_NOTICE,
        L14_CCPA_CATEGORY,
        L15_RETENTION_DURATION,
    ]:
        assert isinstance(pv, PromptVersion)
        assert pv.prompt_id
        assert pv.version
        assert pv.system_prompt
        assert pv.user_template


def test_prompt_version_render_user() -> None:
    from oraculus_di_auditor.llm.contra_prompts import L11_CLAUSE_EXTRACT

    rendered = L11_CLAUSE_EXTRACT.render_user(doc_excerpt="sample clause text here")
    assert "sample clause text here" in rendered
