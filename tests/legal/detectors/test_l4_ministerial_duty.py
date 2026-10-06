"""Tests for L-4 Ministerial Duty Analysis detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l4_ministerial_duty import L4MinisterialDuty


def _ctx(
    text: str = "", doc_type: str = "records_denial", jurisdiction: str = "fresnocounty"
) -> DocContext:
    return DocContext(
        document_id="doc-l4-001",
        document_hash="l4hash001",
        document_type=doc_type,
        jurisdiction=jurisdiction,
        authority="Fresno County Sheriff",
        version_date=date(2026, 6, 1),
        text=text,
    )


def _rule(findings, rule_id: str) -> list:
    return [f for f in findings if rule_id in (f.notes or "")]


@pytest.fixture
def detector() -> L4MinisterialDuty:
    return L4MinisterialDuty()


@pytest.fixture
def mock_resolver():
    return object()


class TestMD1CpraNoExemption:
    def test_denial_without_exemption_fires(self, detector, mock_resolver):
        text = "Your request for records is denied. We are unable to provide these records."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-1")
        assert len(rf) == 1
        assert rf[0].severity == Severity.HIGH
        assert "Cal. Gov. § 815.6" in rf[0].statutes_applied

    def test_denial_with_section_number_does_not_fire(self, detector, mock_resolver):
        text = (
            "Your request for records is denied under Government Code section 7923.600."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-1")
        assert len(rf) == 0

    def test_no_denial_no_firing(self, detector, mock_resolver):
        text = "All requested records are enclosed. No exemptions apply."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-1")
        assert len(rf) == 0


class TestMD2NonNoticedItem:
    def test_emergency_item_in_minutes_fires(self, detector, mock_resolver):
        text = "The board approved an urgency item not noticed on the agenda."
        rf = _rule(
            detector.detect(_ctx(text=text, doc_type="meeting_minutes"), mock_resolver),
            "MD-2",
        )
        assert len(rf) == 1
        assert rf[0].severity == Severity.HIGH
        assert "Cal. Gov. § 54954.2" in rf[0].statutes_applied

    def test_non_minutes_doc_does_not_fire_md2(self, detector, mock_resolver):
        text = "The board approved an urgency item not noticed on the agenda."
        rf = _rule(
            detector.detect(_ctx(text=text, doc_type="agenda"), mock_resolver), "MD-2"
        )
        assert len(rf) == 0

    def test_properly_noticed_minutes_no_fire(self, detector, mock_resolver):
        text = "All items were duly noticed and the meeting was called to order."
        rf = _rule(
            detector.detect(_ctx(text=text, doc_type="meeting_minutes"), mock_resolver),
            "MD-2",
        )
        assert len(rf) == 0


class TestMD3EquipmentNoReport:
    def test_mrap_deployment_without_report_fires(self, detector, mock_resolver):
        text = "The MRAP was deployed to the scene during the incident."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-3")
        assert len(rf) == 1
        assert "Cal. Gov. § 7072" in rf[0].statutes_applied

    def test_deployment_with_report_reference_no_fire(self, detector, mock_resolver):
        text = "The MRAP was deployed. See AB 481 annual report submitted May 1, 2026."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-3")
        assert len(rf) == 0

    def test_drone_deployment_without_report_fires(self, detector, mock_resolver):
        text = "The drone UAS was utilized for aerial surveillance of the perimeter."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-3")
        assert len(rf) == 1


class TestMD4AlprNoPolicy:
    def test_alpr_without_policy_fires(self, detector, mock_resolver):
        text = (
            "The Flock license plate reader system captured 12,000 plates last month."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-4")
        assert len(rf) == 1
        assert rf[0].severity == Severity.HIGH
        assert "Cal. Veh. Code § 2413" in rf[0].statutes_applied
        assert rf[0].confidence == 0.80

    def test_alpr_with_policy_reference_no_fire(self, detector, mock_resolver):
        text = "The ALPR system operates under the department's ALPR policy per Vehicle Code 2413."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-4")
        assert len(rf) == 0

    def test_no_alpr_no_firing(self, detector, mock_resolver):
        text = "The patrol division responded to multiple calls for service."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-4")
        assert len(rf) == 0


class TestMD5OfficerRecords:
    def test_officer_misconduct_denial_fires_critical(self, detector, mock_resolver):
        text = (
            "Records regarding officer misconduct and discipline are withheld "
            "under the Penal Code § 832.8 personnel file exemption."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "MD-5")
        assert len(rf) == 1
        assert rf[0].severity == Severity.CRITICAL
        assert "Cal. Pen. Code § 832.7" in rf[0].statutes_applied


class TestToAnomalyDictAndFindingId:
    def test_anomaly_dict_shape(self, detector, mock_resolver):
        text = "Records request denied. Unable to provide the documents."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        for f in findings:
            d = f.to_anomaly_dict()
            assert d["id"].startswith("legal:l4:")
            assert d["layer"] == "legal"

    def test_finding_id_deterministic(self, detector, mock_resolver):
        ctx = _ctx(text="The MRAP was deployed to the incident scene.")
        id1 = detector.detect(ctx, mock_resolver)
        id2 = detector.detect(ctx, mock_resolver)
        assert [f.finding_id for f in id1] == [f.finding_id for f in id2]


class TestGracefulFailure:
    def test_empty_text(self, detector, mock_resolver):
        findings = detector.detect(_ctx(text=""), mock_resolver)
        assert isinstance(findings, list)

    def test_clean_document(self, detector, mock_resolver):
        text = "FY2026 budget overview. General fund allocation approved."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert isinstance(findings, list)
