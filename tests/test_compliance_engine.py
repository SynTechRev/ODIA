"""Tests for ComplianceAssessmentEngine (Prompt 9.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from oraculus_di_auditor.adapters.atlas_adapter import AtlasAdapter
from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter
from oraculus_di_auditor.adapters.compliance_engine import (
    ComplianceAssessmentEngine,
    ComplianceScorecard,
    ComplianceStatus,
)

# All ODIA detector names used in CCOPS mandates
ALL_DETECTORS: set[str] = {
    "administrative_integrity",
    "fiscal",
    "governance_gap",
    "procurement_timeline",
    "signature_chain",
    "surveillance",
}

SAMPLE_ATLAS = Path(__file__).parent.parent / "data" / "reference" / "atlas_sample.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finding(layer: str, issue: str = "test issue") -> dict:
    return {
        "id": f"{layer}:test",
        "issue": issue,
        "severity": "high",
        "layer": layer,
        "details": {},
    }


def _status(scorecard: ComplianceScorecard, mandate_id: str) -> ComplianceStatus:
    return next(s for s in scorecard.mandate_statuses if s.mandate_id == mandate_id)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def ccops(tmp_path: Path) -> CCOPSAdapter:
    return CCOPSAdapter(cache_dir=tmp_path)


@pytest.fixture()
def engine(ccops: CCOPSAdapter) -> ComplianceAssessmentEngine:
    return ComplianceAssessmentEngine(ccops=ccops)


@pytest.fixture()
def engine_with_atlas(
    ccops: CCOPSAdapter, tmp_path: Path
) -> ComplianceAssessmentEngine:
    atlas = AtlasAdapter(local_dataset_path=SAMPLE_ATLAS, cache_dir=tmp_path)
    return ComplianceAssessmentEngine(ccops=ccops, atlas=atlas)


# ---------------------------------------------------------------------------
# All compliant when no violations and all detectors ran
# ---------------------------------------------------------------------------


def test_assess_no_violations_returns_all_compliant(engine):
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors=ALL_DETECTORS,
    )
    assert all(s.status == "compliant" for s in scorecard.mandate_statuses)


def test_assess_no_violations_compliance_percentage_100(engine):
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors=ALL_DETECTORS,
    )
    assert scorecard.compliance_percentage == 100.0


# ---------------------------------------------------------------------------
# procurement_timeline violation -> M-01 non_compliant
# ---------------------------------------------------------------------------


def test_procurement_timeline_violation_marks_m01_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    assert _status(scorecard, "M-01").status == "non_compliant"
    assert len(_status(scorecard, "M-01").violations) == 1


def test_procurement_timeline_violation_marks_m03_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    assert _status(scorecard, "M-03").status == "non_compliant"


# ---------------------------------------------------------------------------
# governance_gap violation -> M-02, M-04, M-05 non_compliant
# ---------------------------------------------------------------------------


def test_governance_gap_violation_marks_m02_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("governance_gap")])
    assert _status(scorecard, "M-02").status == "non_compliant"


def test_governance_gap_violation_marks_m04_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("governance_gap")])
    assert _status(scorecard, "M-04").status == "non_compliant"


def test_governance_gap_violation_marks_m05_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("governance_gap")])
    assert _status(scorecard, "M-05").status == "non_compliant"


# ---------------------------------------------------------------------------
# signature_chain violation -> M-09 non_compliant
# ---------------------------------------------------------------------------


def test_signature_chain_violation_marks_m09_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("signature_chain")])
    m09 = _status(scorecard, "M-09")
    assert m09.status == "non_compliant"
    assert len(m09.violations) >= 1


# ---------------------------------------------------------------------------
# compliance_percentage
# ---------------------------------------------------------------------------


def test_compliance_percentage_calculated_correctly(engine):
    # Only governance_gap ran, no violations.
    # Mandates using ONLY governance_gap -> compliant: M-02, M-04, M-05, M-08
    # Mandates mixing governance_gap with another detector -> partial: M-06, M-09
    # Mandates not using governance_gap at all -> unknown: M-01, M-03, M-07, M-10, M-11
    # compliant = 4, compliance_percentage = 4/11 * 100
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors={"governance_gap"},
    )
    assert scorecard.compliant_count == 4
    expected = round(4 / 11 * 100, 2)
    assert scorecard.compliance_percentage == expected


def test_compliance_percentage_zero_when_no_detectors_ran(engine):
    scorecard = engine.assess("test_city", [])
    assert scorecard.compliance_percentage == 0.0


# ---------------------------------------------------------------------------
# risk_level
# ---------------------------------------------------------------------------


def test_risk_level_critical_when_critical_mandate_violated(engine):
    # M-01 severity is "critical"
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    assert scorecard.overall_risk == "critical"


def test_risk_level_critical_when_m02_violated(engine):
    # M-02 severity is "critical"
    scorecard = engine.assess("test_city", [_finding("governance_gap")])
    assert scorecard.overall_risk == "critical"


def test_risk_level_low_when_all_compliant(engine):
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors=ALL_DETECTORS,
    )
    assert scorecard.overall_risk == "low"


def test_risk_level_moderate_for_single_medium_violation(engine):
    # M-10 uses fiscal, severity "medium" — not critical
    scorecard = engine.assess("test_city", [_finding("fiscal")])
    assert scorecard.overall_risk == "moderate"


def test_risk_level_unknown_when_no_detectors_ran(engine):
    scorecard = engine.assess("test_city", [])
    # No violations, no non_compliant → risk is "low" (0 failing)
    assert scorecard.overall_risk == "low"


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


def test_recommendations_generated_for_non_compliant(engine):
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    assert len(scorecard.recommendations) >= 1
    assert any("M-01" in r for r in scorecard.recommendations)


def test_recommendations_reference_required_evidence(engine):
    scorecard = engine.assess("test_city", [_finding("governance_gap")])
    combined = " ".join(scorecard.recommendations)
    # M-02 requires surveillance_impact_report; M-04 requires use_policy
    assert "surveillance_impact_report" in combined or "use_policy" in combined


def test_no_recommendations_when_all_compliant(engine):
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors=ALL_DETECTORS,
    )
    assert scorecard.recommendations == []


def test_unknown_mandates_generate_recommendations(engine):
    # No detectors ran -> all unknown -> should have 11 recommendations
    scorecard = engine.assess("test_city", [])
    assert len(scorecard.recommendations) == 11


# ---------------------------------------------------------------------------
# scorecard_markdown
# ---------------------------------------------------------------------------


def test_scorecard_markdown_contains_jurisdiction(engine):
    scorecard = engine.assess("test_city", [])
    md = engine.generate_scorecard_markdown(scorecard)
    assert "test_city" in md


def test_scorecard_markdown_contains_mandate_table(engine):
    scorecard = engine.assess("test_city", [])
    md = engine.generate_scorecard_markdown(scorecard)
    assert "M-01" in md
    assert "M-11" in md


def test_scorecard_markdown_contains_summary_table(engine):
    scorecard = engine.assess(
        "test_city",
        analysis_results=[],
        ran_detectors=ALL_DETECTORS,
    )
    md = engine.generate_scorecard_markdown(scorecard)
    assert "Compliance Score" in md
    assert "100.0%" in md


def test_scorecard_markdown_contains_recommendations_section(engine):
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    md = engine.generate_scorecard_markdown(scorecard)
    assert "## Recommendations" in md


def test_scorecard_markdown_is_nonempty_string(engine):
    scorecard = engine.assess("test_city", [])
    md = engine.generate_scorecard_markdown(scorecard)
    assert isinstance(md, str)
    assert len(md) > 100


def test_scorecard_markdown_contains_risk_level(engine):
    scorecard = engine.assess("test_city", [_finding("procurement_timeline")])
    md = engine.generate_scorecard_markdown(scorecard)
    assert "CRITICAL" in md


# ---------------------------------------------------------------------------
# Atlas integration
# ---------------------------------------------------------------------------


def test_atlas_data_included_when_provided(engine_with_atlas):
    # "Riverside County Sheriff" has 4 records in atlas_sample.json
    scorecard = engine_with_atlas.assess(
        "Riverside County Sheriff",
        analysis_results=[],
        state="CA",
    )
    assert len(scorecard.technology_inventory) == 4


def test_no_atlas_data_when_adapter_not_provided(engine):
    scorecard = engine.assess("Riverside County Sheriff", [], state="CA")
    assert scorecard.technology_inventory == []


def test_atlas_data_in_markdown_when_provided(engine_with_atlas):
    scorecard = engine_with_atlas.assess(
        "Riverside County Sheriff",
        analysis_results=[],
        state="CA",
    )
    md = engine_with_atlas.generate_scorecard_markdown(scorecard)
    assert "## Technology Inventory" in md


# ---------------------------------------------------------------------------
# Unknown status when detectors haven't run
# ---------------------------------------------------------------------------


def test_unknown_status_when_no_detectors_ran(engine):
    scorecard = engine.assess("test_city", [])
    assert all(s.status == "unknown" for s in scorecard.mandate_statuses)


def test_unknown_count_equals_11_when_no_detectors_ran(engine):
    scorecard = engine.assess("test_city", [])
    assert scorecard.unknown_count == 11
    assert scorecard.compliant_count == 0
    assert scorecard.non_compliant_count == 0


# ---------------------------------------------------------------------------
# Scorecard structure
# ---------------------------------------------------------------------------


def test_scorecard_has_11_mandate_statuses(engine):
    scorecard = engine.assess("test_city", [])
    assert len(scorecard.mandate_statuses) == 11


def test_scorecard_mandate_statuses_are_compliance_status(engine):
    scorecard = engine.assess("test_city", [])
    for ms in scorecard.mandate_statuses:
        assert isinstance(ms, ComplianceStatus)
        assert ms.status in ("compliant", "non_compliant", "partial", "unknown")


def test_scorecard_assessment_date_format(engine):
    scorecard = engine.assess("test_city", [])
    # Must be YYYY-MM-DD
    assert len(scorecard.assessment_date) == 10
    assert scorecard.assessment_date[4] == "-"
    assert scorecard.assessment_date[7] == "-"


def test_scorecard_jurisdiction_matches_input(engine):
    scorecard = engine.assess("example_county", [])
    assert scorecard.jurisdiction == "example_county"


def test_scorecard_has_ccops_ordinance_flag(engine):
    scorecard = engine.assess("test_city", [], has_ccops_ordinance=True)
    assert scorecard.has_ccops_ordinance is True
