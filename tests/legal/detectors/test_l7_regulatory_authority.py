"""Tests for L-7 Regulatory Authority detector.

Coverage: RA-1 through RA-5 fire and no-fire cases,
edge cases, and resolver no-op behavior.
"""

from __future__ import annotations

from datetime import date

import pytest
from oraculus_di_auditor.legal.detectors._base import DocContext, Severity
from oraculus_di_auditor.legal.detectors.l7_regulatory_authority import (
    L7RegulatoryAuthority,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def detector():
    return L7RegulatoryAuthority()


def _ctx(text: str, doc_type: str = "policy") -> DocContext:
    import hashlib

    return DocContext(
        document_id="test-l7-001",
        document_hash=hashlib.sha256(text.encode()).hexdigest(),
        document_type=doc_type,
        jurisdiction="fresnocounty",
        authority="Fresno County Board of Supervisors",
        version_date=date(2026, 1, 15),
        text=text,
        source_finding=None,
    )


# ---------------------------------------------------------------------------
# RA-1: Significant action without enabling authority
# ---------------------------------------------------------------------------

_RA1_FIRE = (
    "The department entered into a contract for $2,500,000 to deploy ALPR cameras "
    "across the county. No statutory authority was referenced."
)

_RA1_NO_FIRE_HAS_AUTHORITY = (
    "The department entered into a contract for $2,500,000 to deploy ALPR cameras "
    "pursuant to Cal. Gov. Code § 53069.4 and AB 481 (Gov. Code § 36045)."
)

_RA1_NO_FIRE_DATA_SHARING = (
    "The agency executed a data-sharing agreement with the FBI under 28 C.F.R. "
    "Part 23 and authorized by Government Code § 7282."
)


def test_ra1_fires_on_significant_action_no_authority(detector):
    findings = detector.detect(_ctx(_RA1_FIRE), resolver=None)
    ids = [f.finding_id for f in findings]
    assert any("RA-1" in f.notes for f in findings if f.notes), findings
    assert any(f.severity == Severity.HIGH for f in findings)


def test_ra1_no_fire_when_authority_cited(detector):
    findings = detector.detect(_ctx(_RA1_NO_FIRE_HAS_AUTHORITY), resolver=None)
    ra1 = [f for f in findings if f.notes and "RA-1" in f.notes]
    assert not ra1


def test_ra1_no_fire_data_sharing_with_authority(detector):
    findings = detector.detect(_ctx(_RA1_NO_FIRE_DATA_SHARING), resolver=None)
    ra1 = [f for f in findings if f.notes and "RA-1" in f.notes]
    assert not ra1


# ---------------------------------------------------------------------------
# RA-2: Binding directive without APA rulemaking
# ---------------------------------------------------------------------------

_RA2_FIRE = (
    "All officers shall comply with the department's body-worn camera policy. "
    "The policy is required for all personnel in the field."
)

_RA2_NO_FIRE_RULEMAKING = (
    "All officers shall comply with the department's body-worn camera policy, "
    "which was adopted following a public comment period and OAL approval "
    "pursuant to Government Code § 11346."
)

_RA2_NO_FIRE_APA = (
    "This directive was adopted pursuant to the California APA rulemaking process "
    "with notice published in the California Regulatory Notice Register."
)


def test_ra2_fires_on_binding_directive_no_rulemaking(detector):
    findings = detector.detect(_ctx(_RA2_FIRE), resolver=None)
    ra2 = [f for f in findings if f.notes and "RA-2" in f.notes]
    assert ra2, "RA-2 should fire on binding directive without rulemaking citation"
    assert ra2[0].severity == Severity.HIGH


def test_ra2_no_fire_when_rulemaking_cited(detector):
    findings = detector.detect(_ctx(_RA2_NO_FIRE_RULEMAKING), resolver=None)
    ra2 = [f for f in findings if f.notes and "RA-2" in f.notes]
    assert not ra2


def test_ra2_no_fire_when_apa_referenced(detector):
    findings = detector.detect(_ctx(_RA2_NO_FIRE_APA), resolver=None)
    ra2 = [f for f in findings if f.notes and "RA-2" in f.notes]
    assert not ra2


def test_ra2_statute_cited(detector):
    findings = detector.detect(_ctx(_RA2_FIRE), resolver=None)
    ra2 = [f for f in findings if f.notes and "RA-2" in f.notes]
    statutes = ra2[0].statutes_applied if ra2 else []
    assert any("11340" in s for s in statutes)


# ---------------------------------------------------------------------------
# RA-3: Local policy in state-preempted field
# ---------------------------------------------------------------------------

_RA3_FIRE = (
    "The county policy creates additional CPRA exemptions for law enforcement "
    "records that are more restrictive than state law. The local ordinance "
    "establishes new disclosure requirements under the California Public Records Act."
)

_RA3_NO_FIRE_ACKNOWLEDGED = (
    "The county policy is consistent with state law under the California Public "
    "Records Act (CPRA). All provisions are subject to state requirements and "
    "no local exemption exceeds state law."
)

_RA3_NO_FIRE_NO_PREEMPTED = (
    "The local ordinance restricts parking near school zones and requires "
    "all drivers to yield to pedestrians."
)

_RA3_FIRE_AB481 = (
    "The city ordinance restricts the types of surveillance equipment that may be "
    "used under AB 481. The local policy limits deployment of ALPR systems in ways "
    "that expand the restrictions beyond the state framework."
)


def test_ra3_fires_on_cpra_local_conflict(detector):
    findings = detector.detect(_ctx(_RA3_FIRE), resolver=None)
    ra3 = [f for f in findings if f.notes and "RA-3" in f.notes]
    assert (
        ra3
    ), "RA-3 should fire on local CPRA restriction without preemption acknowledgment"
    assert ra3[0].severity == Severity.HIGH


def test_ra3_no_fire_when_preemption_acknowledged(detector):
    findings = detector.detect(_ctx(_RA3_NO_FIRE_ACKNOWLEDGED), resolver=None)
    ra3 = [f for f in findings if f.notes and "RA-3" in f.notes]
    assert not ra3


def test_ra3_no_fire_non_preempted_subject(detector):
    findings = detector.detect(_ctx(_RA3_NO_FIRE_NO_PREEMPTED), resolver=None)
    ra3 = [f for f in findings if f.notes and "RA-3" in f.notes]
    assert not ra3


def test_ra3_fires_on_ab481_local_conflict(detector):
    findings = detector.detect(_ctx(_RA3_FIRE_AB481), resolver=None)
    ra3 = [f for f in findings if f.notes and "RA-3" in f.notes]
    assert ra3


# ---------------------------------------------------------------------------
# RA-4: Contractor discretion without oversight standards
# ---------------------------------------------------------------------------

_RA4_FIRE = (
    "The contractor has sole discretion to determine which license plate data "
    "to retain and for how long. Flock Safety may decide when to share data "
    "with third parties at its sole discretion."
)

_RA4_NO_FIRE_OVERSIGHT = (
    "The contractor shall operate subject to city oversight and approval. "
    "All data retention decisions are subject to agency review and supervision "
    "by the appointed oversight committee."
)

_RA4_FIRE_DELEGATION = (
    "The agency delegates authority to the vendor to make final decisions "
    "regarding threat assessments for all flagged vehicles. The service provider "
    "has final authority over alert thresholds."
)

_RA4_NO_FIRE_STANDARDS = (
    "Vendor authority is delegated subject to standards established by state law "
    "and the terms of this contract. All decisions are subject to agency review."
)


def test_ra4_fires_on_sole_discretion(detector):
    findings = detector.detect(_ctx(_RA4_FIRE), resolver=None)
    ra4 = [f for f in findings if f.notes and "RA-4" in f.notes]
    assert ra4, "RA-4 should fire on contractor sole discretion without oversight"
    assert ra4[0].severity == Severity.HIGH


def test_ra4_no_fire_when_oversight_present(detector):
    findings = detector.detect(_ctx(_RA4_NO_FIRE_OVERSIGHT), resolver=None)
    ra4 = [f for f in findings if f.notes and "RA-4" in f.notes]
    assert not ra4


def test_ra4_fires_on_final_authority_delegation(detector):
    findings = detector.detect(_ctx(_RA4_FIRE_DELEGATION), resolver=None)
    ra4 = [f for f in findings if f.notes and "RA-4" in f.notes]
    assert ra4


def test_ra4_no_fire_when_standards_defined(detector):
    findings = detector.detect(_ctx(_RA4_NO_FIRE_STANDARDS), resolver=None)
    ra4 = [f for f in findings if f.notes and "RA-4" in f.notes]
    assert not ra4


def test_ra4_statute_cites_nondelegation(detector):
    findings = detector.detect(_ctx(_RA4_FIRE), resolver=None)
    ra4 = [f for f in findings if f.notes and "RA-4" in f.notes]
    statutes = ra4[0].statutes_applied if ra4 else []
    assert any("Whitman" in s for s in statutes)


# ---------------------------------------------------------------------------
# RA-5: Emergency action without required finding
# ---------------------------------------------------------------------------

_RA5_FIRE = (
    "The emergency regulation is immediately effective. The urgency ordinance "
    "was adopted to address conditions in the community."
)

_RA5_NO_FIRE_FINDING = (
    "The emergency regulation is immediately effective based on a finding of "
    "immediate threat to public health and public safety. The agency declared "
    "an emergency due to an imminent danger to general welfare."
)

_RA5_FIRE_URGENCY = (
    "The urgency ordinance is adopted as immediately effective. The measure "
    "takes effect upon passage without the standard 30-day waiting period."
)

_RA5_NO_FIRE_SECTION = (
    "Pursuant to Government Code § 11346.1, this emergency regulation includes "
    "the required urgency finding and has been submitted to OAL for review."
)


def test_ra5_fires_on_emergency_no_finding(detector):
    findings = detector.detect(_ctx(_RA5_FIRE), resolver=None)
    ra5 = [f for f in findings if f.notes and "RA-5" in f.notes]
    assert ra5, "RA-5 should fire on emergency regulation without required finding"
    assert ra5[0].severity == Severity.MEDIUM


def test_ra5_no_fire_when_finding_present(detector):
    findings = detector.detect(_ctx(_RA5_NO_FIRE_FINDING), resolver=None)
    ra5 = [f for f in findings if f.notes and "RA-5" in f.notes]
    assert not ra5


def test_ra5_fires_on_urgency_ordinance_no_finding(detector):
    findings = detector.detect(_ctx(_RA5_FIRE_URGENCY), resolver=None)
    ra5 = [f for f in findings if f.notes and "RA-5" in f.notes]
    assert ra5


def test_ra5_no_fire_when_section_cited(detector):
    findings = detector.detect(_ctx(_RA5_NO_FIRE_SECTION), resolver=None)
    ra5 = [f for f in findings if f.notes and "RA-5" in f.notes]
    assert not ra5


def test_ra5_statute_cites_gov_code(detector):
    findings = detector.detect(_ctx(_RA5_FIRE), resolver=None)
    ra5 = [f for f in findings if f.notes and "RA-5" in f.notes]
    statutes = ra5[0].statutes_applied if ra5 else []
    assert any("11346" in s for s in statutes)


# ---------------------------------------------------------------------------
# Structural / protocol tests
# ---------------------------------------------------------------------------


def test_detector_id():
    assert L7RegulatoryAuthority.detector_id == "l7-regulatory-authority"


def test_returns_list_on_empty_text(detector):
    findings = detector.detect(_ctx(""), resolver=None)
    assert isinstance(findings, list)


def test_returns_empty_on_clean_civic_text(detector):
    clean = (
        "The Board approved the minutes of the previous meeting. "
        "No contracts were awarded. No policy changes were enacted."
    )
    findings = detector.detect(_ctx(clean), resolver=None)
    assert findings == []


def test_finding_shape(detector):
    findings = detector.detect(_ctx(_RA4_FIRE), resolver=None)
    for f in findings:
        d = f.to_anomaly_dict()
        assert d["layer"] == "legal"
        assert d["severity"] in ("low", "medium", "high", "critical")
        assert "sub_detector" in d["details"]
        assert d["details"]["sub_detector"] == "l7-regulatory-authority"


def test_exception_returns_empty_list(detector):
    """Detector must never raise; it returns [] on any exception."""
    ctx = _ctx("normal text")
    # Pass an object that would cause an error if the resolver were used
    # (resolver is currently unused in L-7, but the guard must still hold)
    findings = detector.detect(ctx, resolver=object())
    assert isinstance(findings, list)
