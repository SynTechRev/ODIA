"""Tests for L-10 Balancing Test Analyzer."""

from __future__ import annotations

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l10_balancing_test import L10BalancingTest


def _ctx(
    text: str, doc_type: str = "response", doc_id: str = "test-doc-001"
) -> DocContext:
    return DocContext(
        document_id=doc_id,
        document_hash="abc123def456",
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff",
        version_date=None,
        text=text,
    )


@pytest.fixture
def detector():
    return L10BalancingTest()


# ---------------------------------------------------------------------------
# BT-1: CPRA balancing present but conclusory
# ---------------------------------------------------------------------------


class TestBT1ConclusoryBalancing:
    def test_fires_on_conclusory_catchall(self, detector):
        """Catch-all invoked with balancing language but no specific interest."""
        text = (
            "The request is denied under Government Code section 7922.000. "
            "The public interest in nondisclosure outweighs the public interest "
            "in disclosure due to privacy concerns."
        )
        findings = detector.detect(_ctx(text), None)
        ids = [f.sub_detector for f in findings]
        assert "l10-balancing-test" in ids
        bt1 = [f for f in findings if "BT-1" in (f.notes or "")]
        assert len(bt1) == 1
        assert bt1[0].severity == Severity.HIGH

    def test_fires_when_balance_language_without_specific_interest(self, detector):
        """Balancing exemption with weighing language but no concrete interest."""
        text = (
            "This document invokes the catch-all exemption under 7922.000. "
            "After weighing the competing interests, the agency determines that "
            "nondisclosure is warranted."
        )
        findings = detector.detect(_ctx(text), None)
        bt1 = [f for f in findings if "BT-1" in (f.notes or "")]
        assert len(bt1) == 1

    def test_no_fire_when_specific_interest_present(self, detector):
        """BT-1 should not fire when a specific interest is articulated."""
        text = (
            "The request is denied under section 7922.000. The public interest "
            "in nondisclosure outweighs disclosure because the records relate to "
            "an ongoing criminal investigation that could be compromised by release."
        )
        findings = detector.detect(_ctx(text), None)
        bt1 = [f for f in findings if "BT-1" in (f.notes or "")]
        assert len(bt1) == 0

    def test_no_fire_when_informant_safety_cited(self, detector):
        """BT-1 should not fire when informant identity protection is cited."""
        text = (
            "The agency denies release under section 7922.000. After balancing "
            "the interests, nondisclosure is required to protect informant identity "
            "and source safety in the ongoing operation."
        )
        findings = detector.detect(_ctx(text), None)
        bt1 = [f for f in findings if "BT-1" in (f.notes or "")]
        assert len(bt1) == 0

    def test_statutes_applied_includes_cbs_block(self, detector):
        """BT-1 should cite CBS Inc. v. Block."""
        text = (
            "Denied under 7922.000 because the public interest in nondisclosure "
            "outweighs the public interest in disclosure."
        )
        findings = detector.detect(_ctx(text), None)
        bt1 = [f for f in findings if "BT-1" in (f.notes or "")]
        assert len(bt1) == 1
        statutes = bt1[0].statutes_applied
        assert any("CBS" in s for s in statutes)


# ---------------------------------------------------------------------------
# BT-2: CPRA catch-all with no balancing at all
# ---------------------------------------------------------------------------


class TestBT2AbsentBalancing:
    def test_fires_on_bare_catchall(self, detector):
        """BT-2 fires when catch-all invoked with no balancing language."""
        text = "The request is denied under Government Code section 7922.000."
        findings = detector.detect(_ctx(text), None)
        bt2 = [f for f in findings if "BT-2" in (f.notes or "")]
        assert len(bt2) == 1
        assert bt2[0].severity == Severity.CRITICAL
        assert bt2[0].confidence >= 0.85

    def test_fires_when_balancing_exemption_phrase_no_analysis(self, detector):
        """BT-2 fires when 'balancing exemption' phrase appears but no weighing."""
        text = "Records withheld under the balancing exemption. No further analysis provided."
        findings = detector.detect(_ctx(text), None)
        bt2 = [f for f in findings if "BT-2" in (f.notes or "")]
        assert len(bt2) == 1

    def test_no_fire_when_balancing_present(self, detector):
        """BT-2 does not fire if any weighing language is present (BT-1 may fire instead)."""
        text = (
            "Denied under section 7922.000. Balancing the interests, nondisclosure "
            "outweighs disclosure."
        )
        findings = detector.detect(_ctx(text), None)
        bt2 = [f for f in findings if "BT-2" in (f.notes or "")]
        assert len(bt2) == 0

    def test_bt1_and_bt2_are_mutually_exclusive(self, detector):
        """BT-1 and BT-2 should not both fire on the same text."""
        text_bt1 = "Denied under 7922.000 because nondisclosure outweighs disclosure."
        text_bt2 = "Denied under 7922.000."
        f1 = detector.detect(_ctx(text_bt1), None)
        f2 = detector.detect(_ctx(text_bt2), None)
        bt1_count = len([f for f in f1 if "BT-1" in (f.notes or "")])
        bt2_count = len([f for f in f1 if "BT-2" in (f.notes or "")])
        # On text_bt1, only BT-1 should fire (has balance language, no specific interest)
        assert bt1_count == 1
        assert bt2_count == 0
        # On text_bt2, only BT-2 should fire (no balance language at all)
        assert len([f for f in f2 if "BT-2" in (f.notes or "")]) == 1
        assert len([f for f in f2 if "BT-1" in (f.notes or "")]) == 0


# ---------------------------------------------------------------------------
# BT-3: Automated decision without Mathews balancing
# ---------------------------------------------------------------------------


class TestBT3MathewsAbsent:
    def test_fires_on_predictive_risk_score(self, detector):
        """BT-3 fires on predictive risk score decision with no Mathews analysis."""
        text = (
            "The subject was flagged by the predictive risk score system and "
            "a detention recommendation was issued based on the algorithmic output."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        assert len(bt3) == 1
        assert bt3[0].severity == Severity.HIGH

    def test_fires_on_automated_detention(self, detector):
        """BT-3 fires on automated detention decision."""
        text = (
            "The AI-generated threat assessment indicated a high risk score "
            "and an automated decision was made to detain the individual."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        assert len(bt3) == 1

    def test_no_fire_when_mathews_factors_present(self, detector):
        """BT-3 does not fire when Mathews factors are analyzed."""
        text = (
            "The predictive risk score system was evaluated under Mathews v. Eldridge. "
            "The private interest in liberty, the risk of erroneous deprivation from "
            "false positives, and the administrative burden of additional review were "
            "all weighed. The government interest in public safety was considered."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        assert len(bt3) == 0

    def test_no_fire_when_liberty_interest_present(self, detector):
        """BT-3 does not fire when liberty interest language is present."""
        text = (
            "An algorithmic recommendation was made for bail determination. "
            "The private liberty interest of the defendant was analyzed against "
            "the government's interest in pretrial detention."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        assert len(bt3) == 0

    def test_statutes_applied_includes_mathews(self, detector):
        """BT-3 should cite Mathews v. Eldridge."""
        text = (
            "Machine-generated risk scores were used to determine parole eligibility."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        assert len(bt3) == 1
        statutes = bt3[0].statutes_applied
        assert any("Mathews" in s for s in statutes)


# ---------------------------------------------------------------------------
# BT-4: Location data without duration/scope parameters
# ---------------------------------------------------------------------------


class TestBT4CarpenterDurationScope:
    def test_fires_on_alpr_no_scope(self, detector):
        """BT-4 fires on ALPR reference with no retention duration or geographic scope."""
        text = "The department uses ALPR technology to capture and store license plate data."
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 1
        assert bt4[0].severity == Severity.HIGH

    def test_fires_on_geofence_no_scope(self, detector):
        """BT-4 fires on geofence reference without duration or bounds."""
        text = "GPS location data was collected via geofence warrant for the investigation."
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 1

    def test_no_fire_when_retention_duration_present(self, detector):
        """BT-4 does not fire when retention duration is specified."""
        text = (
            "ALPR data is retained for a maximum of 60 days and then automatically purged. "
            "The 60-day retention limit was established to balance investigative needs "
            "with privacy protections."
        )
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 0

    def test_no_fire_when_geographic_limit_present(self, detector):
        """BT-4 does not fire when geographic scope is defined."""
        text = (
            "ALPR cameras are deployed within a defined geographic boundary of "
            "the downtown patrol zone. Collection is limited to the target area."
        )
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 0

    def test_no_fire_when_targeted_individual_scope_present(self, detector):
        """BT-4 does not fire when collection is limited to targeted individual."""
        text = (
            "CSLI data was obtained for the targeted individual subject to the "
            "court order. Collection was limited to the named suspect."
        )
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 0

    def test_statutes_includes_carpenter(self, detector):
        """BT-4 should cite Carpenter v. United States."""
        text = "License plate reader data was collected citywide."
        findings = detector.detect(_ctx(text), None)
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt4) == 1
        statutes = bt4[0].statutes_applied
        assert any("Carpenter" in s for s in statutes)


# ---------------------------------------------------------------------------
# BT-5: AB 481 policy missing cost-benefit analysis
# ---------------------------------------------------------------------------


class TestBT5AB481CostBenefit:
    def test_fires_on_ab481_policy_no_analysis(self, detector):
        """BT-5 fires when AB 481 policy present without cost-benefit language."""
        text = (
            "The department adopted a military equipment use policy pursuant to "
            "AB 481. The policy covers MRAP vehicles and drones. The policy was "
            "approved by the city council."
        )
        findings = detector.detect(_ctx(text), None)
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt5) == 1
        assert bt5[0].severity == Severity.MEDIUM

    def test_fires_on_section_7071_no_analysis(self, detector):
        """BT-5 fires when § 7071 is cited but no cost-benefit found."""
        text = (
            "The surveillance equipment use policy was adopted per § 7071 requirements."
        )
        findings = detector.detect(_ctx(text), None)
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt5) == 1

    def test_no_fire_when_cost_benefit_present(self, detector):
        """BT-5 does not fire when cost-benefit analysis is documented."""
        text = (
            "The military equipment use policy under AB 481 includes a cost-benefit "
            "analysis as required by Cal. Gov. § 7071(b)(4). The benefits of drone "
            "deployment were weighed against potential adverse community impacts, "
            "and the least restrictive option was selected."
        )
        findings = detector.detect(_ctx(text), None)
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt5) == 0

    def test_no_fire_when_necessity_analysis_present(self, detector):
        """BT-5 does not fire when necessity analysis language is present."""
        text = (
            "Per AB 481, this military equipment use policy includes a necessity "
            "analysis and proportionality review for each equipment category."
        )
        findings = detector.detect(_ctx(text), None)
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt5) == 0

    def test_statutes_include_section_7071(self, detector):
        """BT-5 should cite § 7071(b)(4)."""
        text = "The department adopted a surveillance equipment use policy per AB 481."
        findings = detector.detect(_ctx(text), None)
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt5) == 1
        statutes = bt5[0].statutes_applied
        assert any("7071" in s for s in statutes)


# ---------------------------------------------------------------------------
# Multi-rule firing
# ---------------------------------------------------------------------------


class TestMultiRuleFiring:
    def test_bt3_and_bt4_can_fire_together(self, detector):
        """Automated decision + location data without any analysis fires both BT-3 and BT-4."""
        text = (
            "The predictive risk score system analyzed ALPR location data to "
            "generate a detain recommendation. No human review was documented."
        )
        findings = detector.detect(_ctx(text), None)
        bt3 = [f for f in findings if "BT-3" in (f.notes or "")]
        bt4 = [f for f in findings if "BT-4" in (f.notes or "")]
        assert len(bt3) == 1
        assert len(bt4) == 1

    def test_bt2_and_bt5_can_fire_together(self, detector):
        """Bare catch-all + AB 481 no analysis fires BT-2 and BT-5."""
        text = (
            "The CPRA request is denied under section 7922.000. "
            "The department also adopted an AB 481 military equipment use policy."
        )
        findings = detector.detect(_ctx(text), None)
        bt2 = [f for f in findings if "BT-2" in (f.notes or "")]
        bt5 = [f for f in findings if "BT-5" in (f.notes or "")]
        assert len(bt2) == 1
        assert len(bt5) == 1

    def test_finding_ids_are_unique(self, detector):
        """All finding IDs within a single document must be unique."""
        text = (
            "Denied under section 7922.000. "
            "Predictive risk score used for detention recommendation. "
            "ALPR data collected without retention limit. "
            "AB 481 military equipment policy adopted."
        )
        findings = detector.detect(_ctx(text), None)
        assert len(findings) > 1
        ids = [f.finding_id for f in findings]
        assert len(ids) == len(set(ids)), "Finding IDs must be unique"

    def test_empty_text_produces_no_findings(self, detector):
        """Empty text should not raise and should produce no findings."""
        findings = detector.detect(_ctx(""), None)
        assert findings == []

    def test_unrelated_text_produces_no_findings(self, detector):
        """Text unrelated to balancing tests should produce no findings."""
        text = (
            "The department purchased new patrol vehicles. The procurement "
            "followed standard competitive bidding procedures. Delivery is "
            "expected in Q1 next year."
        )
        findings = detector.detect(_ctx(text), None)
        assert findings == []

    def test_to_anomaly_dict_format(self, detector):
        """to_anomaly_dict() output should have required keys and correct layer."""
        text = "Denied under section 7922.000."
        findings = detector.detect(_ctx(text), None)
        assert len(findings) > 0
        d = findings[0].to_anomaly_dict()
        assert d["layer"] == "legal"
        assert "severity" in d
        assert "issue" in d
        assert "details" in d
        assert d["details"]["sub_detector"] == "l10-balancing-test"

    def test_source_finding_id_propagated(self, detector):
        """source_finding_id from DocContext.source_finding is set on LegalFinding."""
        ctx = DocContext(
            document_id="doc-999",
            document_hash="hash999",
            document_type="response",
            jurisdiction="fresnocounty",
            authority=None,
            version_date=None,
            text="Denied under section 7922.000.",
            source_finding={"id": "upstream-finding-42"},
        )
        findings = detector.detect(ctx, None)
        assert len(findings) > 0
        assert findings[0].source_finding_id == "upstream-finding-42"
