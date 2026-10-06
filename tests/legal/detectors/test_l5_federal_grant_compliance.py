"""Tests for L-5 Federal Grant Compliance detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l5_federal_grant_compliance import (
    L5FederalGrantCompliance,
)


def _ctx(text: str = "", doc_type: str = "grant_agreement") -> DocContext:
    return DocContext(
        document_id="doc-l5-001",
        document_hash="l5hash001",
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff's Office",
        version_date=date(2026, 7, 1),
        text=text,
    )


def _rule(findings, rule_id: str) -> list:
    return [f for f in findings if rule_id in (f.notes or "")]


@pytest.fixture
def detector() -> L5FederalGrantCompliance:
    return L5FederalGrantCompliance()


@pytest.fixture
def mock_resolver():
    return object()


class TestGC1JagNoCertification:
    def test_jag_without_civil_rights_cert_fires(self, detector, mock_resolver):
        text = (
            "The county applied for a JAG Byrne grant under 34 USC 10152. "
            "Funds will be used to purchase body cameras."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-1")
        assert len(rf) == 1
        assert rf[0].severity == Severity.HIGH
        assert "34 USC § 10152" in rf[0].statutes_applied

    def test_jag_with_civil_rights_cert_no_fire(self, detector, mock_resolver):
        text = (
            "The county applied for a JAG grant. "
            "The required civil rights certification is attached and on file."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-1")
        assert len(rf) == 0

    def test_no_jag_no_firing(self, detector, mock_resolver):
        text = "General fund budget appropriation for FY2026."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-1")
        assert len(rf) == 0


class TestGC2CopsWithSurveillance:
    def test_cops_with_facial_recognition_fires(self, detector, mock_resolver):
        text = (
            "COPS grant-funded officers will operate facial recognition "
            "systems for identification at public events."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-2")
        assert len(rf) == 1
        assert "34 USC § 10381" in rf[0].statutes_applied

    def test_cops_without_surveillance_no_fire(self, detector, mock_resolver):
        text = "COPS grant funding supports community policing programs and officer training."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-2")
        assert len(rf) == 0

    def test_cops_with_alpr_fires(self, detector, mock_resolver):
        text = "COPS-funded officers use ALPR technology to support patrol operations."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-2")
        assert len(rf) == 1


class TestGC3SoleSourceNojustification:
    def test_federally_funded_sole_source_large_amount_fires(
        self, detector, mock_resolver
    ):
        text = (
            "Federal grant funds will be used for a sole-source award "
            "to Axon Enterprise for $450,000 in TASER equipment."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-3")
        assert len(rf) == 1
        assert "2 CFR § 200.320" in rf[0].statutes_applied

    def test_sole_source_with_2cfr_citation_no_fire(self, detector, mock_resolver):
        text = (
            "Federal grant funds will be used for a sole-source award. "
            "Exception documented per 2 CFR 200.320(f) -- only responsible source."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-3")
        assert len(rf) == 0

    def test_sole_source_small_amount_no_fire(self, detector, mock_resolver):
        # Small amount -- doesn't trigger large-amount threshold
        text = "Federal grant funds for a sole-source purchase of $5,000 in supplies."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-3")
        assert len(rf) == 0


class TestGC4GrantCivilRightsViolation:
    def test_grant_with_1983_language_fires_critical(self, detector, mock_resolver):
        text = (
            "The federal grant-funded program resulted in a 42 U.S.C. § 1983 claim "
            "for deprivation of rights under color of law."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-4")
        assert len(rf) == 1
        assert rf[0].severity == Severity.CRITICAL
        assert "42 USC § 1983" in rf[0].statutes_applied

    def test_no_civil_rights_violation_no_fire(self, detector, mock_resolver):
        text = "Federal grant funds disbursed per program guidelines with no incidents."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-4")
        assert len(rf) == 0


class TestGC5IceCollaboration:
    def test_287g_with_grant_fires(self, detector, mock_resolver):
        text = (
            "The county entered a 287(g) agreement with ICE. "
            "Bureau of Justice Assistance grant funds support these operations."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-5")
        assert len(rf) == 1
        assert "8 USC § 1373" in rf[0].statutes_applied

    def test_ice_mou_no_grant_no_fire(self, detector, mock_resolver):
        text = "The county entered an ICE MOU for detainer cooperation."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "GC-5")
        assert len(rf) == 0


class TestMultipleRules:
    def test_compound_grant_violations(self, detector, mock_resolver):
        text = (
            "JAG grant funds a sole-source award of $500,000 to purchase ALPR systems. "
            "No compliance documentation is included with this award package. "
            "COPS-funded officers will operate the surveillance system."
        )
        findings = detector.detect(_ctx(text=text), mock_resolver)
        rule_ids = {f.notes.split(":")[0] for f in findings if f.notes}
        assert "GC-1" in rule_ids
        assert "GC-3" in rule_ids


class TestToAnomalyDict:
    def test_anomaly_dict_valid(self, detector, mock_resolver):
        text = "The Byrne JAG grant is used for body camera procurement."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        for f in findings:
            d = f.to_anomaly_dict()
            assert d["id"].startswith("legal:l5:")
            assert d["layer"] == "legal"
            assert d["details"]["sub_detector"] == "l5-federal-grant-compliance"


class TestGracefulFailure:
    def test_empty_text(self, detector, mock_resolver):
        findings = detector.detect(_ctx(text=""), mock_resolver)
        assert isinstance(findings, list)
        assert findings == []
