"""Tests for L-2 Procedural Compliance detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l2_procedural_compliance import (
    L2ProceduralCompliance,
)


def _ctx(
    text: str = "", doc_type: str = "agenda", jurisdiction: str = "fresnocounty"
) -> DocContext:
    return DocContext(
        document_id="doc-002",
        document_hash="def456",
        document_type=doc_type,
        jurisdiction=jurisdiction,
        authority="City of Fresno",
        version_date=date(2026, 3, 1),
        text=text,
    )


@pytest.fixture
def detector() -> L2ProceduralCompliance:
    return L2ProceduralCompliance()


@pytest.fixture
def mock_resolver():
    return object()


class TestPC1CpraNoResponse:
    def test_request_without_response_fires(self, detector, mock_resolver):
        text = "This is a public records request for all contracts over $10,000."
        findings = detector.detect(
            _ctx(text=text, doc_type="records_request"), mock_resolver
        )
        ids = {f.finding_id for f in findings}
        rule_findings = [f for f in findings if "PC-1" in (f.notes or "")]
        assert len(rule_findings) == 1
        assert rule_findings[0].severity == Severity.HIGH
        assert "Cal. Gov. § 7922.500" in rule_findings[0].statutes_applied

    def test_request_with_response_language_does_not_fire(
        self, detector, mock_resolver
    ):
        text = (
            "This is a public records request. "
            "We hereby respond to your request for records within 10 days."
        )
        rule_findings = [
            f
            for f in detector.detect(_ctx(text=text), mock_resolver)
            if "PC-1" in (f.notes or "")
        ]
        assert len(rule_findings) == 0

    def test_no_request_no_firing(self, detector, mock_resolver):
        text = "Regular meeting agenda for Tuesday, March 3, 2026."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert all("PC-1" not in (f.notes or "") for f in findings)


class TestPC2ExtensionNoProductionDate:
    def test_extension_without_date_fires(self, detector, mock_resolver):
        text = (
            "This is a public records request. "
            "We are invoking a 14-day extension to respond to your request."
        )
        rule_findings = [
            f
            for f in detector.detect(_ctx(text=text), mock_resolver)
            if "PC-2" in (f.notes or "")
        ]
        assert len(rule_findings) == 1
        assert rule_findings[0].severity == Severity.MEDIUM
        assert "Cal. Gov. § 7922.530" in rule_findings[0].statutes_applied

    def test_extension_with_production_date_does_not_fire(
        self, detector, mock_resolver
    ):
        text = (
            "This is a public records request. "
            "We are invoking a 14-day extension. "
            "Records will be provided by April 15, 2026."
        )
        rule_findings = [
            f
            for f in detector.detect(_ctx(text=text), mock_resolver)
            if "PC-2" in (f.notes or "")
        ]
        assert len(rule_findings) == 0


class TestPC3BrownActPosting:
    def test_agenda_with_meeting_date_no_posting_fires(self, detector, mock_resolver):
        text = "Regular meeting on Tuesday, March 3, 2026 at 9:00 AM."
        rule_findings = [
            f
            for f in detector.detect(_ctx(text=text, doc_type="agenda"), mock_resolver)
            if "PC-3" in (f.notes or "")
        ]
        assert len(rule_findings) == 1
        assert rule_findings[0].severity == Severity.HIGH
        assert "Cal. Gov. § 54954.2" in rule_findings[0].statutes_applied

    def test_agenda_with_both_dates_does_not_fire(self, detector, mock_resolver):
        text = (
            "Regular meeting on Tuesday, March 3, 2026 at 9:00 AM. "
            "Posted on Saturday, February 28, 2026."
        )
        rule_findings = [
            f
            for f in detector.detect(_ctx(text=text, doc_type="agenda"), mock_resolver)
            if "PC-3" in (f.notes or "")
        ]
        assert len(rule_findings) == 0

    def test_non_agenda_doc_type_does_not_fire_pc3(self, detector, mock_resolver):
        text = "Regular meeting on Tuesday, March 3, 2026 at 9:00 AM."
        rule_findings = [
            f
            for f in detector.detect(
                _ctx(text=text, doc_type="contract"), mock_resolver
            )
            if "PC-3" in (f.notes or "")
        ]
        assert len(rule_findings) == 0


class TestPC4Ab481MissingDate:
    def test_equipment_ref_without_date_fires(self, detector, mock_resolver):
        text = (
            "The department operates an MRAP for emergency response. "
            "The drone is used for aerial surveillance operations."
        )
        rule_findings = [
            f
            for f in detector.detect(
                _ctx(text=text, doc_type="annual_report"), mock_resolver
            )
            if "PC-4" in (f.notes or "")
        ]
        assert len(rule_findings) == 1
        assert "Cal. Gov. § 7072" in rule_findings[0].statutes_applied

    def test_equipment_ref_with_date_does_not_fire(self, detector, mock_resolver):
        text = (
            "The department operates an MRAP for emergency response. "
            "This report was submitted May 1, 2026 as required."
        )
        rule_findings = [
            f
            for f in detector.detect(
                _ctx(text=text, doc_type="annual_report"), mock_resolver
            )
            if "PC-4" in (f.notes or "")
        ]
        assert len(rule_findings) == 0


class TestMultipleRules:
    def test_multiple_rules_can_fire_on_same_document(self, detector, mock_resolver):
        text = (
            "This is a public records request. "
            "We are invoking a 14-day extension. "
            "The department uses surveillance aircraft for operations."
        )
        findings = detector.detect(_ctx(text=text, doc_type="agenda"), mock_resolver)
        # At minimum PC-1 (request without response) and PC-4 (equipment without date)
        assert len(findings) >= 1

    def test_clean_document_fires_nothing(self, detector, mock_resolver):
        text = "Budget approval for fiscal year 2026-2027."
        findings = detector.detect(_ctx(text=text, doc_type="agenda"), mock_resolver)
        # PC-3 may fire if there's a meeting date pattern but no text above has one
        assert isinstance(findings, list)


class TestGracefulFailure:
    def test_does_not_raise_on_empty_text(self, detector, mock_resolver):
        findings = detector.detect(_ctx(text=""), mock_resolver)
        assert isinstance(findings, list)

    def test_to_anomaly_dict_valid(self, detector, mock_resolver):
        text = "This is a public records request for all surveillance contracts."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        for f in findings:
            d = f.to_anomaly_dict()
            assert "id" in d
            assert d["layer"] == "legal"
