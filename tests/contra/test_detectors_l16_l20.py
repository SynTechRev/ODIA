"""Tests for C.O.N.T.R.A. detectors L-16 through L-20 (Phase D).

Tests are organized in three tiers:
  1. Unit tests: targeted snippets that fire exactly one sub-detector
  2. Golden reference tests: full synthetic contracts from tests/contra/golden/
  3. Negative / clean contract tests: verify no spurious findings on G-03
  4. CASI reproducibility test: deterministic aggregate scoring across all 10 detectors
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from oraculus_di_auditor.contra import (
    Finding,
    L11ArbitrationArchitecture,
    L12ChoiceOfLawForum,
    L13UnilateralModification,
    L14DataCollectionDepth,
    L15DataRetention,
    L16OnwardTransfer,
    L17MlAiTraining,
    L18RemedyForeclosure,
    L19EnforcementAsymmetry,
    L20DarkPattern,
    Severity,
)
from oraculus_di_auditor.contra.anchors import ALL_ANCHORS
from oraculus_di_auditor.contra.casi import compute_casi

_GOLDEN = Path(__file__).parent / "golden"

_META = {
    "document_hash": "b" * 64,
    "entity_id": "test-entity",
    "entity_name": "Test Entity Corp",
    "doc_type": "tos",
}


def _load_golden(filename: str) -> str:
    return (_GOLDEN / filename).read_text(encoding="utf-8")


def _has_sub(findings: List[Finding], sub: str) -> bool:
    return any(f.sub_detector == sub for f in findings)


def _get_sub(findings: List[Finding], sub: str) -> List[Finding]:
    return [f for f in findings if f.sub_detector == sub]


def _anchors_valid(findings: List[Finding]) -> bool:
    return all(f.doctrinal_anchor in ALL_ANCHORS for f in findings)


def _excerpts_valid(findings: List[Finding]) -> bool:
    return all(len(f.evidence_span.verbatim_excerpt.split()) <= 15 for f in findings)


# ===========================================================================
# L-16 Onward Transfer
# ===========================================================================


def _l16() -> L16OnwardTransfer:
    return L16OnwardTransfer()


def test_l16_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector
    assert isinstance(_l16(), Detector)
    assert _l16().layer == "L-16"


def test_l16a_sale_of_personal_information() -> None:
    text = "We may sell your personal information to third-party marketing partners."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l16b_behavioral_advertising_sharing() -> None:
    text = "We share your data for cross-context behavioral advertising and targeted advertising."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.HIGH


def test_l16c_service_provider_transfer() -> None:
    text = "We share your personal information with service providers who process data on our behalf."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.LOW


def test_l16d_contractor_transfer() -> None:
    text = "Contractors may receive your personal data to support platform operations."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.MEDIUM


def test_l16e_affiliate_transfer() -> None:
    text = "Our affiliates and subsidiaries may access your personal information within our corporate family."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "E")


def test_l16f_data_broker_transfer() -> None:
    text = "We are a data broker and may sell consumer information to data broker networks."
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "F")
    assert _get_sub(findings, "F")[0].severity == Severity.HIGH


def test_l16g_government_disclosure_narrow() -> None:
    text = (
        "We may disclose your personal information to law enforcement "
        "when required by law or pursuant to legal process."
    )
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.LOW


def test_l16g_government_disclosure_broad() -> None:
    text = (
        "We may disclose your personal information to government agencies "
        "to protect our interests or assist with investigations."
    )
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.MEDIUM


def test_l16h_merger_acquisition() -> None:
    text = (
        "In the event of a merger, acquisition, or sale of the company, "
        "your personal information will be transferred to the acquiring entity."
    )
    findings = _l16().scan(text, _META)
    assert _has_sub(findings, "H")
    assert _get_sub(findings, "H")[0].severity == Severity.LOW


def test_l16_golden_g04_key_subs_present() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l16().scan(text, _META)
    for sub in ("A", "B", "C", "D", "E", "F", "H"):
        assert _has_sub(findings, sub), f"L-16{sub} not detected in G-04"


def test_l16_golden_g04_anchors_valid() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l16().scan(text, _META)
    assert _anchors_valid(findings)


def test_l16_golden_g04_excerpts_valid() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l16().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l16_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l16().scan(text, _META)
    assert findings == [], (
        f"Expected no L-16 findings on G-03, got {len(findings)}: "
        f"{[f.sub_detector for f in findings]}"
    )


def test_l16_finding_id_unique() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l16().scan(text, _META)
    ids = [f.finding_id for f in findings]
    assert len(ids) == len(set(ids)), "Duplicate finding_ids detected"


# ===========================================================================
# L-17 ML/AI Training Use
# ===========================================================================


def _l17() -> L17MlAiTraining:
    return L17MlAiTraining()


def test_l17_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector
    assert isinstance(_l17(), Detector)
    assert _l17().layer == "L-17"


def test_l17a_explicit_training_grant() -> None:
    text = (
        "We use your data to train our machine learning models and "
        "improve our artificial intelligence systems."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.CRITICAL


def test_l17b_perpetual_irrevocable_license() -> None:
    text = (
        "You grant us a perpetual, irrevocable, worldwide, royalty-free license "
        "to use your content."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.CRITICAL


def test_l17c_broad_modality_scope() -> None:
    text = (
        "All types of data you submit, including text, image, audio, and video "
        "across all modalities, may be used to improve our services."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "C")


def test_l17d_training_without_optout() -> None:
    text = (
        "We use your personal information for model training and AI development. "
        "No opt-out mechanism is provided."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.HIGH


def test_l17d_training_with_optout_no_finding() -> None:
    text = (
        "We use your data to train AI models. You may opt out of AI training "
        "at any time by visiting your data use preferences."
    )
    findings = _l17().scan(text, _META)
    d_findings = _get_sub(findings, "D")
    assert d_findings == [], "L-17D should not fire when opt-out is present"


def test_l17e_biometric_in_training_scope() -> None:
    text = (
        "We use your data to train our machine learning models. "
        "We collect biometric identifiers including facial recognition data "
        "for identity verification and AI model training."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.CRITICAL


def test_l17f_no_deletion_path_for_training() -> None:
    text = (
        "Your data is used to train our AI systems. "
        "No process exists to remove model training contributions."
    )
    findings = _l17().scan(text, _META)
    assert _has_sub(findings, "F")
    assert _get_sub(findings, "F")[0].severity == Severity.HIGH


def test_l17_golden_g04_key_subs_present() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l17().scan(text, _META)
    for sub in ("A", "B", "C", "D", "E", "F"):
        assert _has_sub(findings, sub), f"L-17{sub} not detected in G-04"


def test_l17_golden_g04_anchors_valid() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l17().scan(text, _META)
    assert _anchors_valid(findings)


def test_l17_golden_g04_excerpts_valid() -> None:
    text = _load_golden("g04_onward_transfer_ml_training.txt")
    findings = _l17().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l17_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l17().scan(text, _META)
    assert findings == [], (
        f"Expected no L-17 findings on G-03, got {len(findings)}: "
        f"{[f.sub_detector for f in findings]}"
    )


# ===========================================================================
# L-18 Remedy Foreclosure
# ===========================================================================


def _l18() -> L18RemedyForeclosure:
    return L18RemedyForeclosure()


def test_l18_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector
    assert isinstance(_l18(), Detector)
    assert _l18().layer == "L-18"


def test_l18a_damages_cap() -> None:
    text = (
        "The Company's total liability shall not exceed the amount paid by you "
        "in the preceding twelve months or $50, whichever is less."
    )
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l18b_consequential_damages_waiver() -> None:
    text = "The Company shall not be liable for any consequential or incidental damages."
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.HIGH


def test_l18c_punitive_damages_waiver() -> None:
    text = "Punitive damages are hereby waived and shall not be available in any proceeding."
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.HIGH


def test_l18d_shortened_sol() -> None:
    text = (
        "Any legal action or claim must be brought within one year of the date "
        "the claim arose or it is permanently barred."
    )
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.HIGH


def test_l18e_jury_trial_waiver() -> None:
    text = "By agreeing to these Terms you waive your right to a jury trial."
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "E")
    assert _get_sub(findings, "E")[0].severity == Severity.HIGH


def test_l18f_equitable_relief_waiver() -> None:
    text = (
        "You may not seek injunctive relief or any equitable remedy against the Company. "
        "No equitable relief shall be granted in any proceeding."
    )
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "F")
    assert _get_sub(findings, "F")[0].severity == Severity.CRITICAL


def test_l18g_paga_waiver() -> None:
    text = "Representative PAGA actions are prohibited and waived to the maximum extent permitted by law."
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.CRITICAL


def test_l18h_as_is_disclaimer() -> None:
    text = 'The services are provided "as is" without warranty of any kind. The Company disclaims all warranties.'
    findings = _l18().scan(text, _META)
    assert _has_sub(findings, "H")
    assert _get_sub(findings, "H")[0].severity == Severity.MEDIUM


def test_l18_golden_g05_all_subs_present() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l18().scan(text, _META)
    for sub in "ABCDEFGH":
        assert _has_sub(findings, sub), f"L-18{sub} not detected in G-05"


def test_l18_golden_g05_anchors_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l18().scan(text, _META)
    assert _anchors_valid(findings)


def test_l18_golden_g05_excerpts_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l18().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l18_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l18().scan(text, _META)
    assert findings == [], (
        f"Expected no L-18 findings on G-03, got {len(findings)}: "
        f"{[f.sub_detector for f in findings]}"
    )


# ===========================================================================
# L-19 Enforcement Asymmetry
# ===========================================================================


def _l19() -> L19EnforcementAsymmetry:
    return L19EnforcementAsymmetry()


def test_l19_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector
    assert isinstance(_l19(), Detector)
    assert _l19().layer == "L-19"


def test_l19a_one_way_fee_shifting() -> None:
    text = (
        "If the Company is the prevailing party, the Company shall be entitled to "
        "recover its reasonable attorney fees and costs."
    )
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.CRITICAL


def test_l19b_mutual_fee_shifting() -> None:
    text = (
        "The prevailing party shall be entitled to recover its reasonable attorney "
        "fees and costs from the other party."
    )
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "B")
    assert _get_sub(findings, "B")[0].severity == Severity.MEDIUM


def test_l19c_consumer_bears_arbitration_costs() -> None:
    text = "You shall pay all filing fees, administrative fees, and arbitrator fees."
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "C")
    assert _get_sub(findings, "C")[0].severity == Severity.HIGH


def test_l19c_company_payment_suppresses_finding() -> None:
    text = (
        "You are responsible for filing fees. The company will pay all administrative "
        "fees and arbitrator fees."
    )
    findings = _l19().scan(text, _META)
    c_findings = _get_sub(findings, "C")
    assert c_findings == [], "L-19C should not fire when company pays arbitration fees"


def test_l19d_non_disparagement_clause() -> None:
    text = (
        "You agree not to make any negative, disparaging, or defamatory statements "
        "about the Company in any public forum."
    )
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "D")
    assert _get_sub(findings, "D")[0].severity == Severity.HIGH


def test_l19e_discovery_limitation() -> None:
    text = "Discovery in arbitration is limited to a document exchange only. No depositions are permitted."
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "E")


def test_l19f_arbitration_confidentiality() -> None:
    text = (
        "The outcome and award of the arbitration proceeding are confidential. "
        "You shall maintain the arbitration outcome as confidential."
    )
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "F")


def test_l19g_no_1281_97_acknowledgment() -> None:
    text = "All disputes shall be submitted to binding mandatory arbitration."
    findings = _l19().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.HIGH


def test_l19g_1281_acknowledgment_suppresses_finding() -> None:
    text = (
        "All disputes shall be resolved by binding arbitration. "
        "The Company acknowledges its obligations under CCP 1281.97 and 1281.98."
    )
    findings = _l19().scan(text, _META)
    g_findings = _get_sub(findings, "G")
    assert g_findings == [], "L-19G should not fire when CCP 1281.97/98 is acknowledged"


def test_l19_golden_g05_key_subs_present() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l19().scan(text, _META)
    for sub in ("A", "B", "D", "E", "F", "G"):
        assert _has_sub(findings, sub), f"L-19{sub} not detected in G-05"


def test_l19_golden_g05_anchors_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l19().scan(text, _META)
    assert _anchors_valid(findings)


def test_l19_golden_g05_excerpts_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l19().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l19_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l19().scan(text, _META)
    assert findings == [], (
        f"Expected no L-19 findings on G-03, got {len(findings)}: "
        f"{[f.sub_detector for f in findings]}"
    )


# ===========================================================================
# L-20 Dark Pattern
# ===========================================================================


def _l20() -> L20DarkPattern:
    return L20DarkPattern()


def test_l20_is_detector_protocol() -> None:
    from oraculus_di_auditor.contra import Detector
    assert isinstance(_l20(), Detector)
    assert _l20().layer == "L-20"


def test_l20a_pre_checked_consent() -> None:
    text = "Unless you opt out or uncheck the pre-selected option, you are automatically opted in by default."
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "A")
    assert _get_sub(findings, "A")[0].severity == Severity.HIGH


def test_l20b_nested_acceptance() -> None:
    text = (
        "By accepting these Terms you also agree to our Privacy Policy, "
        "Data Sharing Agreement, and all policies linked or referenced therein."
    )
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "B")


def test_l20c_click_wrap_acceptance() -> None:
    text = 'By clicking "I Agree" or "Accept" you accept these Terms.'
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "C")


def test_l20d_fine_print_differential() -> None:
    text = "See footnote 1 for important limitations that govern your rights to seek remedies."
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "D")


def test_l20e_reading_level_above_threshold() -> None:
    high_complexity_text = (
        "Notwithstanding the foregoing, the indemnification obligations enumerated "
        "herein shall not be construed to limit the indemnifying party's aggregate "
        "liability pursuant to contractual exculpatory provisions promulgated "
        "contemporaneously with the establishment of consequential relationships. "
        "Furthermore, jurisdictional prerequisites mandate compliance with all "
        "applicable statutory and regulatory frameworks governing the indemnification "
        "of third-party beneficiaries under supplemental contractual arrangements "
        "pertaining to intellectual property licensing and technology commercialization. "
        "The aforementioned provisions are incorporated by reference and constitute "
        "binding obligations enforceable in perpetuity. Indemnification shall survive "
        "termination and remain operative regardless of subsequent contractual modifications."
    )
    findings = _l20().scan(high_complexity_text, _META)
    assert _has_sub(findings, "E"), "Expected L-20E for high Flesch-Kincaid grade text"


def test_l20e_simple_text_no_finding() -> None:
    simple_text = (
        "We use your email to send you updates. You can opt out at any time. "
        "Your data is safe with us. We do not sell your data. "
        "Contact us if you have questions. We are here to help. "
        "You own your content. We just help you share it. "
        "You can delete your account at any time. "
        "These are the rules for using our service."
    )
    findings = _l20().scan(simple_text, _META)
    e_findings = _get_sub(findings, "E")
    assert e_findings == [], f"L-20E should not fire for simple text (FK grade likely below 9)"


def test_l20g_english_only_clause() -> None:
    text = "This agreement is available in English only. English version shall control."
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "G")
    assert _get_sub(findings, "G")[0].severity == Severity.MEDIUM


def test_l20h_urgency_pressure() -> None:
    text = "LIMITED TIME OFFER: You must accept these Terms within 24 hours to maintain account access."
    findings = _l20().scan(text, _META)
    assert _has_sub(findings, "H")
    assert _get_sub(findings, "H")[0].severity == Severity.CRITICAL


def test_l20_golden_g05_key_subs_present() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l20().scan(text, _META)
    for sub in ("A", "B", "C", "D", "G", "H"):
        assert _has_sub(findings, sub), f"L-20{sub} not detected in G-05"


def test_l20_golden_g05_anchors_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l20().scan(text, _META)
    assert _anchors_valid(findings)


def test_l20_golden_g05_excerpts_valid() -> None:
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    findings = _l20().scan(text, _META)
    assert _excerpts_valid(findings)


def test_l20_clean_g03_no_findings() -> None:
    text = _load_golden("g03_clean_contract_no_findings.txt")
    findings = _l20().scan(text, _META)
    assert findings == [], (
        f"Expected no L-20 findings on G-03, got {len(findings)}: "
        f"{[f.sub_detector for f in findings]}"
    )


# ===========================================================================
# CASI Reproducibility Tests
# ===========================================================================


def test_casi_deterministic_same_doc_twice() -> None:
    """compute_casi must be deterministic: same document yields identical scores."""
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings: List[Finding] = []
    for det in all_detectors:
        all_findings.extend(det.scan(text, _META))

    score_a = compute_casi(all_findings)
    score_b = compute_casi(all_findings)

    assert score_a == score_b, "compute_casi must be deterministic"


def test_casi_aggregate_equals_sum_of_axes() -> None:
    """CASI aggregate score must equal sum of clamped axis scores."""
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings: List[Finding] = []
    for det in all_detectors:
        all_findings.extend(det.scan(text, _META))

    score = compute_casi(all_findings)
    axis_sum = sum([
        score["remedy_foreclosure"],
        score["data_extraction_depth"],
        score["modification_and_consent"],
        score["procedural_adhesion"],
        score["enforcement_cost_asymmetry"],
    ])
    assert score["aggregate"] == axis_sum, (
        f"CASI aggregate {score['aggregate']} != axis sum {axis_sum}"
    )


def test_casi_axes_clamped_0_to_20() -> None:
    """Each CASI axis must be in [0, 20]."""
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings: List[Finding] = []
    for det in all_detectors:
        all_findings.extend(det.scan(text, _META))

    score = compute_casi(all_findings)
    axes = [
        "remedy_foreclosure", "data_extraction_depth", "modification_and_consent",
        "procedural_adhesion", "enforcement_cost_asymmetry",
    ]
    for axis in axes:
        assert 0 <= score[axis] <= 20, f"Axis {axis}={score[axis]} outside [0, 20]"


def test_casi_aggregate_clamped_0_to_100() -> None:
    """CASI aggregate must be in [0, 100]."""
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings: List[Finding] = []
    for det in all_detectors:
        all_findings.extend(det.scan(text, _META))

    score = compute_casi(all_findings)
    assert 0 <= score["aggregate"] <= 100, f"Aggregate {score['aggregate']} outside [0, 100]"


def test_casi_clean_g03_all_axes_near_zero() -> None:
    """Clean contract should yield substantially lower CASI than a hostile contract."""
    text = _load_golden("g03_clean_contract_no_findings.txt")
    hostile_text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings_clean: List[Finding] = []
    all_findings_hostile: List[Finding] = []
    for det in all_detectors:
        all_findings_clean.extend(det.scan(text, _META))
        all_findings_hostile.extend(det.scan(hostile_text, _META))

    clean_score = compute_casi(all_findings_clean)
    hostile_score = compute_casi(all_findings_hostile)
    assert clean_score["aggregate"] < hostile_score["aggregate"], (
        f"G-03 CASI ({clean_score['aggregate']}) should be lower than G-05 "
        f"hostile CASI ({hostile_score['aggregate']})"
    )
    # High-scoring axes (remedy_foreclosure, enforcement_cost_asymmetry) must be zero on G-03
    assert clean_score["remedy_foreclosure"] == 0, (
        f"G-03 remedy_foreclosure={clean_score['remedy_foreclosure']} should be 0"
    )
    assert clean_score["enforcement_cost_asymmetry"] == 0, (
        f"G-03 enforcement_cost_asymmetry={clean_score['enforcement_cost_asymmetry']} should be 0"
    )


def test_casi_finding_ids_unique_across_all_detectors() -> None:
    """No two findings from any detector should share a finding_id on the same document."""
    text = _load_golden("g05_remedy_enforcement_dark_pattern.txt")
    all_detectors = [
        L11ArbitrationArchitecture(), L12ChoiceOfLawForum(), L13UnilateralModification(),
        L14DataCollectionDepth(), L15DataRetention(), L16OnwardTransfer(),
        L17MlAiTraining(), L18RemedyForeclosure(), L19EnforcementAsymmetry(), L20DarkPattern(),
    ]
    all_findings: List[Finding] = []
    for det in all_detectors:
        all_findings.extend(det.scan(text, _META))

    ids = [f.finding_id for f in all_findings]
    assert len(ids) == len(set(ids)), (
        f"Duplicate finding_ids across detectors: "
        f"{[i for i in ids if ids.count(i) > 1]}"
    )
