"""Tests for L-3 Exemption Misapplication detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l3_exemption_misapplication import (
    L3ExemptionMisapplication,
)


def _ctx(text: str = "", doc_type: str = "records_denial") -> DocContext:
    return DocContext(
        document_id="doc-003",
        document_hash="ghi789",
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff's Office",
        version_date=date(2026, 5, 10),
        text=text,
    )


@pytest.fixture
def detector() -> L3ExemptionMisapplication:
    return L3ExemptionMisapplication()


@pytest.fixture
def mock_resolver():
    return object()


def _rule_findings(findings, rule_id: str) -> list:
    return [f for f in findings if rule_id in (f.notes or "")]


class TestEX1LawEnforcementRecords:
    def test_bare_invocation_fires(self, detector, mock_resolver):
        text = "Records are exempt under Government Code section 7923.600 as law enforcement investigative files."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-1")
        assert len(rf) == 1
        assert rf[0].severity == Severity.HIGH
        assert "Cal. Gov. § 7923.600" in rf[0].statutes_applied

    def test_invocation_with_active_investigation_does_not_fire(
        self, detector, mock_resolver
    ):
        text = (
            "Records are exempt under 7923.600. "
            "Disclosure would endanger an active investigation into the matter."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-1")
        assert len(rf) == 0

    def test_invocation_with_confidential_informant_does_not_fire(
        self, detector, mock_resolver
    ):
        text = (
            "Records are exempt as investigative files. "
            "Release would identify a confidential informant."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-1")
        assert len(rf) == 0

    def test_no_exemption_no_finding(self, detector, mock_resolver):
        text = "All records are provided in full. No exemptions apply."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-1")
        assert len(rf) == 0


class TestEX2PublicInterestBalancing:
    def test_bare_catch_all_fires(self, detector, mock_resolver):
        # Pure statutory citation, no weighing analysis
        text = "Disclosure is denied under Government Code section 7922.000."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-2")
        assert len(rf) == 1
        assert "Cal. Gov. § 7922.000" in rf[0].statutes_applied

    def test_with_weighing_analysis_does_not_fire(self, detector, mock_resolver):
        text = (
            "Under Government Code 7922.000, we have weighed the public interest in "
            "disclosure against the public interest in nondisclosure. The nondisclosure "
            "interest is stronger because release would compromise the ongoing budget process."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-2")
        assert len(rf) == 0


class TestEX3FaceRecognition:
    def test_frt_exemption_without_ab481_fires_critical(self, detector, mock_resolver):
        text = (
            "Records related to the face recognition system are exempt under "
            "Civil Code section 1798.90.55."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-3")
        assert len(rf) == 1
        assert rf[0].severity == Severity.CRITICAL
        assert "Cal. Civ. Code § 1798.90.55" in rf[0].statutes_applied

    def test_frt_with_ab481_disclosure_does_not_fire(self, detector, mock_resolver):
        text = (
            "Records related to the face recognition system are exempt under 1798.90.55. "
            "The annual report required under AB 481 has been submitted and the equipment "
            "policy approved."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-3")
        assert len(rf) == 0


class TestEX4DeliberativeProcess:
    def test_bare_invocation_fires(self, detector, mock_resolver):
        # No chill-of-deliberation language -- bare label only
        text = "This document is exempt as predecisional deliberative process material."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-4")
        assert len(rf) == 1
        assert rf[0].severity == Severity.MEDIUM

    def test_with_full_showing_does_not_fire(self, detector, mock_resolver):
        # Explicit chill language satisfies the § 7927.705 showing requirement
        text = (
            "This draft staff recommendation is predecisional. "
            "Release would chill candid deliberation among department heads prior to the decision."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-4")
        assert len(rf) == 0


class TestEX5AttorneyClient:
    def test_bare_privilege_invocation_fires(self, detector, mock_resolver):
        text = "The requested documents are protected by attorney-client privilege."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-5")
        assert len(rf) == 1
        assert rf[0].severity == Severity.MEDIUM

    def test_with_elements_does_not_fire(self, detector, mock_resolver):
        text = (
            "The documents reflect confidential attorney-client communications. "
            "Legal advice was sought from retained counsel and privilege has not been waived."
        )
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-5")
        assert len(rf) == 0

    def test_work_product_without_elements_fires(self, detector, mock_resolver):
        text = "These materials constitute protected attorney work-product."
        rf = _rule_findings(detector.detect(_ctx(text=text), mock_resolver), "EX-5")
        assert len(rf) == 1


class TestMultipleExemptions:
    def test_compound_deficiency_fires_multiple(self, detector, mock_resolver):
        text = (
            "Records are exempt under Government Code 7923.600 as law enforcement files. "
            "Additionally, the records are predecisional deliberative process material. "
            "Disclosure is also denied under section 7922.000."
        )
        findings = detector.detect(_ctx(text=text), mock_resolver)
        rule_ids = {f.notes.split(":")[0] for f in findings if f.notes}
        # EX-1, EX-2, and EX-4 should all fire
        assert "EX-1" in rule_ids
        assert "EX-2" in rule_ids
        assert "EX-4" in rule_ids

    def test_confidence_is_0_85_for_confirmed_misapplication(
        self, detector, mock_resolver
    ):
        text = "Records are exempt under 7923.600 as investigative records."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert all(f.confidence == 0.85 for f in findings)


class TestToAnomalyDict:
    def test_anomaly_dict_shape(self, detector, mock_resolver):
        text = (
            "Records are exempt under 7923.600 as law enforcement investigative files."
        )
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert len(findings) >= 1
        d = findings[0].to_anomaly_dict()
        assert d["id"].startswith("legal:l3:")
        assert d["layer"] == "legal"
        assert "statutes_applied" in d["details"]
        assert d["details"]["sub_detector"] == "l3-exemption-misapplication"


class TestGracefulFailure:
    def test_empty_text_returns_empty_list(self, detector, mock_resolver):
        findings = detector.detect(_ctx(text=""), mock_resolver)
        assert findings == []

    def test_clean_approval_document_returns_empty(self, detector, mock_resolver):
        text = "All requested records are hereby provided in full. No exemptions apply."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert findings == []
