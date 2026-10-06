"""Tests for L-1 Statutory Applicability detector."""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext
from oraculus_di_auditor.legal.detectors.l1_statutory_applicability import (
    _CPRA_BASELINE,
    L1StatutoryApplicability,
)


def _ctx(
    text: str = "",
    doc_type: str = "agenda",
    jurisdiction: str = "fresnocounty",
    source_finding: dict | None = None,
) -> DocContext:
    return DocContext(
        document_id="doc-001",
        document_hash="abc123",
        document_type=doc_type,
        jurisdiction=jurisdiction,
        authority="Fresno County Board of Supervisors",
        version_date=date(2026, 1, 15),
        text=text,
        source_finding=source_finding,
    )


@pytest.fixture
def detector() -> L1StatutoryApplicability:
    return L1StatutoryApplicability()


@pytest.fixture
def mock_resolver():
    """Resolver stub -- L-1 does not call resolver in current implementation."""
    return object()


class TestL1Basics:
    def test_always_includes_cpra_baseline(self, detector, mock_resolver):
        findings = detector.detect(_ctx(), mock_resolver)
        assert len(findings) == 1
        assert _CPRA_BASELINE in findings[0].statutes_applied

    def test_layer_is_legal(self, detector, mock_resolver):
        findings = detector.detect(_ctx(), mock_resolver)
        assert findings[0].layer == "legal"

    def test_sub_detector_id(self, detector, mock_resolver):
        findings = detector.detect(_ctx(), mock_resolver)
        assert findings[0].sub_detector == "l1-statutory-applicability"

    def test_finding_id_is_stable(self, detector, mock_resolver):
        ctx = _ctx(text="same text")
        id1 = detector.detect(ctx, mock_resolver)[0].finding_id
        id2 = detector.detect(ctx, mock_resolver)[0].finding_id
        assert id1 == id2

    def test_finding_id_changes_with_different_doc_hash(self, detector, mock_resolver):
        ctx1 = DocContext(
            document_id="doc-001",
            document_hash="aaa",
            document_type="agenda",
            jurisdiction="fresnocounty",
            authority=None,
            version_date=None,
            text="",
        )
        ctx2 = DocContext(
            document_id="doc-002",
            document_hash="bbb",
            document_type="agenda",
            jurisdiction="fresnocounty",
            authority=None,
            version_date=None,
            text="",
        )
        id1 = detector.detect(ctx1, mock_resolver)[0].finding_id
        id2 = detector.detect(ctx2, mock_resolver)[0].finding_id
        assert id1 != id2

    def test_to_anomaly_dict_shape(self, detector, mock_resolver):
        finding = detector.detect(_ctx(), mock_resolver)[0]
        d = finding.to_anomaly_dict()
        assert "id" in d
        assert "issue" in d
        assert d["severity"] in ("low", "medium", "high", "critical")
        assert d["layer"] == "legal"
        assert "statutes_applied" in d["details"]


class TestTier2DocumentType:
    def test_agenda_adds_brown_act(self, detector, mock_resolver):
        findings = detector.detect(_ctx(doc_type="agenda"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Gov. § 54950" in statutes
        assert "Cal. Gov. § 54954.2" in statutes

    def test_records_request_adds_cpra_response(self, detector, mock_resolver):
        findings = detector.detect(_ctx(doc_type="records_request"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Gov. § 7922.500" in statutes

    def test_grant_agreement_adds_jag(self, detector, mock_resolver):
        findings = detector.detect(_ctx(doc_type="grant_agreement"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "34 USC § 10152" in statutes

    def test_unknown_type_still_has_cpra_baseline(self, detector, mock_resolver):
        findings = detector.detect(_ctx(doc_type="unknown"), mock_resolver)
        assert _CPRA_BASELINE in findings[0].statutes_applied


class TestTier3ContentSignals:
    def test_flock_triggers_alpr_statutes(self, detector, mock_resolver):
        text = "The agency purchased Flock Safety license plate readers."
        findings = detector.detect(_ctx(text=text, doc_type="contract"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Veh. Code § 2413" in statutes
        assert "Cal. Pen. § 832.18" in statutes

    def test_face_recognition_triggers_1798(self, detector, mock_resolver):
        text = "The system uses face recognition technology for identification."
        findings = detector.detect(_ctx(text=text, doc_type="policy"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Civ. Code § 1798.90.55" in statutes

    def test_taser_triggers_ab481(self, detector, mock_resolver):
        text = "Officers are equipped with TASER devices approved under current policy."
        findings = detector.detect(_ctx(text=text, doc_type="policy"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Gov. § 7070" in statutes

    def test_arbitration_triggers_ccp_1281(self, detector, mock_resolver):
        text = "All disputes shall be resolved by binding arbitration."
        findings = detector.detect(_ctx(text=text, doc_type="contract"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. CCP § 1281.96" in statutes

    def test_body_camera_triggers_pen_code(self, detector, mock_resolver):
        text = "Officers wear body-worn cameras (BWC) during all patrol shifts."
        findings = detector.detect(_ctx(text=text, doc_type="policy"), mock_resolver)
        statutes = findings[0].statutes_applied
        assert "Cal. Pen. Code § 832.7" in statutes

    def test_no_signals_only_baseline(self, detector, mock_resolver):
        findings = detector.detect(
            _ctx(text="Routine administrative document.", doc_type="unknown"),
            mock_resolver,
        )
        assert findings[0].statutes_applied == [_CPRA_BASELINE]


class TestConfidence:
    def test_known_type_and_jurisdiction_gives_1_0(self, detector, mock_resolver):
        ctx = _ctx(doc_type="agenda", jurisdiction="fresnocounty")
        findings = detector.detect(ctx, mock_resolver)
        assert findings[0].confidence == 1.0

    def test_unknown_type_gives_0_8(self, detector, mock_resolver):
        ctx = _ctx(doc_type="unknown", jurisdiction="fresnocounty")
        findings = detector.detect(ctx, mock_resolver)
        assert findings[0].confidence == 0.8


class TestSourceFinding:
    def test_source_finding_id_populated(self, detector, mock_resolver):
        source = {"id": "fiscal:missing-hash:abc12345:00000010"}
        ctx = _ctx(source_finding=source)
        finding = detector.detect(ctx, mock_resolver)[0]
        assert finding.source_finding_id == source["id"]

    def test_no_source_finding_gives_none(self, detector, mock_resolver):
        finding = detector.detect(_ctx(), mock_resolver)[0]
        assert finding.source_finding_id is None


class TestGracefulFailure:
    def test_does_not_raise_on_empty_text(self, detector, mock_resolver):
        ctx = _ctx(text="")
        findings = detector.detect(ctx, mock_resolver)
        assert isinstance(findings, list)

    def test_returns_list_always(self, detector, mock_resolver):
        ctx = _ctx(text="Some text with no special signals at all.")
        result = detector.detect(ctx, mock_resolver)
        assert isinstance(result, list)
