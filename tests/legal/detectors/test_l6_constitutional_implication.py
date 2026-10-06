"""Tests for L-6 Constitutional Implication detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l6_constitutional_implication import (
    L6ConstitutionalImplication,
)


def _ctx(text: str = "", doc_type: str = "policy") -> DocContext:
    return DocContext(
        document_id="doc-l6-001",
        document_hash="l6hash001",
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Sheriff's Office",
        version_date=date(2026, 8, 15),
        text=text,
    )


def _rule(findings, rule_id: str) -> list:
    return [f for f in findings if rule_id in (f.notes or "")]


@pytest.fixture
def detector() -> L6ConstitutionalImplication:
    return L6ConstitutionalImplication()


@pytest.fixture
def mock_resolver():
    return object()


class TestCI1CarpenterMosaic:
    def test_alpr_retention_without_warrant_fires_critical(
        self, detector, mock_resolver
    ):
        text = "ALPR data is retained in the database for 365 days for analysis."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-1")
        assert len(rf) == 1
        assert rf[0].severity == Severity.CRITICAL
        assert (
            "Carpenter v. United States, 138 S. Ct. 2206 (2018)"
            in rf[0].statutes_applied
        )

    def test_csli_collection_without_warrant_fires(self, detector, mock_resolver):
        text = "Officers obtained historical location data through cell-site records collection."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-1")
        assert len(rf) == 1

    def test_location_aggregation_with_warrant_no_fire(self, detector, mock_resolver):
        text = (
            "ALPR data retained 90 days. A search warrant was issued based on "
            "probable cause found sufficient by the court."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-1")
        assert len(rf) == 0

    def test_no_location_data_no_fire(self, detector, mock_resolver):
        text = "Officers responded to a report of trespassing at the property."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-1")
        assert len(rf) == 0


class TestCI2ThirdPartyDigital:
    def test_google_subpoena_no_ecpa_fires(self, detector, mock_resolver):
        text = "The department issued a legal process request to Google for subscriber account records."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-2")
        assert len(rf) == 1
        assert "18 USC § 2703" in rf[0].statutes_applied

    def test_with_sca_citation_no_fire(self, detector, mock_resolver):
        text = (
            "The department obtained subscriber records from Google via 18 U.S.C. § 2703 "
            "Stored Communications Act process."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-2")
        assert len(rf) == 0

    def test_verizon_subpoena_fires(self, detector, mock_resolver):
        text = "A subpoena was served on Verizon for the subscriber's call metadata records."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-2")
        assert len(rf) == 1


class TestCI3FirstAmendment:
    def test_protest_monitoring_no_predicate_fires_critical(
        self, detector, mock_resolver
    ):
        text = "Officers monitored the downtown protest and documented participants."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-3")
        assert len(rf) == 1
        assert rf[0].severity == Severity.CRITICAL
        assert "NAACP v. Alabama, 357 U.S. 449 (1958)" in rf[0].statutes_applied

    def test_political_organization_surveillance_fires(self, detector, mock_resolver):
        text = "Intelligence division surveilled political organizing activities in the district."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-3")
        assert len(rf) == 1

    def test_protest_with_criminal_nexus_no_fire(self, detector, mock_resolver):
        text = (
            "Officers monitored the protest. Surveillance was based on articulable suspicion "
            "of specific criminal activity by identified individuals."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-3")
        assert len(rf) == 0

    def test_religious_community_surveillance_fires(self, detector, mock_resolver):
        text = "Investigators documented the religious congregation and its members."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-3")
        assert len(rf) == 1


class TestCI4DemographicSurveillance:
    def test_racial_demographic_plus_alpr_no_analysis_fires(
        self, detector, mock_resolver
    ):
        text = (
            "ALPR cameras are concentrated in Black and Hispanic neighborhoods "
            "with high plate read volumes."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-4")
        assert len(rf) == 1
        assert "42 USC § 2000d" in rf[0].statutes_applied

    def test_with_equity_analysis_no_fire(self, detector, mock_resolver):
        text = (
            "ALPR deployment in minority communities. A disparate impact analysis "
            "was conducted and reviewed for equity."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-4")
        assert len(rf) == 0

    def test_surveillance_without_demographic_no_fire(self, detector, mock_resolver):
        text = "ALPR cameras are deployed at major intersections throughout the county."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-4")
        assert len(rf) == 0


class TestCI5AutomatedDecision:
    def test_predictive_risk_score_no_human_review_fires(self, detector, mock_resolver):
        text = (
            "The predictive risk score is used to determine detention recommendations."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-5")
        assert len(rf) == 1
        assert "Mathews v. Eldridge, 424 U.S. 319 (1976)" in rf[0].statutes_applied

    def test_automated_with_human_review_no_fire(self, detector, mock_resolver):
        text = (
            "The AI-generated risk score feeds into the process. "
            "Final determination requires human review by a supervising officer."
        )
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-5")
        assert len(rf) == 0

    def test_algorithmic_bail_recommendation_no_review_fires(
        self, detector, mock_resolver
    ):
        text = "The algorithmic threat assessment is used for bail recommendations."
        rf = _rule(detector.detect(_ctx(text=text), mock_resolver), "CI-5")
        assert len(rf) == 1


class TestMultipleViolations:
    def test_surveillance_with_multiple_constitutional_issues(
        self, detector, mock_resolver
    ):
        text = (
            "ALPR data is retained for 365 days. "
            "Officers monitored the protest and documented political organizing activities. "
            "The predictive risk score system generates detention recommendations."
        )
        findings = detector.detect(_ctx(text=text), mock_resolver)
        rule_ids = {f.notes.split(":")[0] for f in findings if f.notes}
        assert "CI-1" in rule_ids
        assert "CI-3" in rule_ids
        assert "CI-5" in rule_ids


class TestToAnomalyDict:
    def test_anomaly_dict_shape(self, detector, mock_resolver):
        text = "ALPR system retains data for 90 days for pattern analysis."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        for f in findings:
            d = f.to_anomaly_dict()
            assert d["id"].startswith("legal:l6:")
            assert d["layer"] == "legal"
            assert d["details"]["sub_detector"] == "l6-constitutional-implication"


class TestGracefulFailure:
    def test_empty_text(self, detector, mock_resolver):
        findings = detector.detect(_ctx(text=""), mock_resolver)
        assert findings == []

    def test_routine_document(self, detector, mock_resolver):
        text = "Routine budget report for Q3 2026. No personnel matters discussed."
        findings = detector.detect(_ctx(text=text), mock_resolver)
        assert isinstance(findings, list)
