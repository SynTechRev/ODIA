"""Tests for the D-13 cross-entity detector.

Each test corresponds to a precedent finding documented in the
Cross-Entity Analysis Protocol V1.0 section 3 finding-type table.
The fixture documents are minimal -- enough text to trigger one
specific code path -- so a failure here points at exactly one
classifier branch rather than a generic regression.
"""

from __future__ import annotations

import pytest

from oraculus_di_auditor.analysis.cross_entity import (
    _reset_caches_for_tests,
    detect_cross_entity_anomalies,
)


@pytest.fixture(autouse=True)
def _reset_module_caches() -> None:
    """Each test gets a fresh registry + alias-pattern cache.

    Cross-test cache leak isn't a correctness issue here (the
    registry is read-only), but resetting between tests means a
    future change to the loader can't accidentally hide stale state
    in a previous test's run.
    """
    _reset_caches_for_tests()
    yield
    _reset_caches_for_tests()


def _doc(primary: str, text: str, doc_id: str = "TEST-DOC") -> dict:
    """Minimal helper to produce a doc dict that survives extract_text_content."""
    return {
        "metadata": {"primary_entity": primary, "document_id": doc_id},
        "raw_text": text,
    }


# ---------------------------------------------------------------------------
# Activation gate
# ---------------------------------------------------------------------------


def test_returns_empty_when_no_primary_entity_tag() -> None:
    doc = {"metadata": {}, "raw_text": "Visalia PD authorized Flock Safety."}
    assert detect_cross_entity_anomalies(doc) == []


def test_returns_empty_for_non_dict() -> None:
    assert detect_cross_entity_anomalies(None) == []  # type: ignore[arg-type]
    assert detect_cross_entity_anomalies("a string") == []  # type: ignore[arg-type]
    assert detect_cross_entity_anomalies([1, 2]) == []  # type: ignore[arg-type]


def test_returns_empty_for_short_text() -> None:
    doc = _doc("E-001", "Visalia PD short.")
    assert detect_cross_entity_anomalies(doc) == []


def test_self_reference_suppressed() -> None:
    # Document tagged to VPD that only mentions VPD aliases should
    # not emit a cross-entity finding (the primary entity referring
    # to itself is not a cross-reference).
    doc = _doc(
        "E-001",
        "Visalia Police Department announces. VPD officers were dispatched. "
        "The Visalia PD chief signed the report. City of Visalia Police "
        "personnel attended the meeting.",
    )
    findings = detect_cross_entity_anomalies(doc)
    target_ids = {f["details"]["target_entity"] for f in findings}
    assert "E-001" not in target_ids


# ---------------------------------------------------------------------------
# Type A -- Budget/fiscal cross-reference
# ---------------------------------------------------------------------------


def test_type_a_budget_fiscal_cross_reference() -> None:
    """TCSO budget book naming TCDAO line item -> Type A HIGH."""
    doc = _doc(
        "E-009",
        (
            "FY2024-25 Budget Summary. Tulare County Sheriff's Office "
            "operating budget: $148M. District Attorney Bureau of "
            "Investigations line item: $2,100,000. Public Defender "
            "allocation: $11,800,000."
        ),
        doc_id="TCSO-BOS-2024-0543",
    )
    findings = detect_cross_entity_anomalies(doc)
    type_a_to_tcdao = [
        f
        for f in findings
        if f["details"]["target_entity"] == "E-011"
        and f["details"]["finding_type"] == "A"
    ]
    assert type_a_to_tcdao, (
        f"expected Type A finding for TCDAO; got {[f['details'] for f in findings]}"
    )
    assert type_a_to_tcdao[0]["severity"] == "high"


# ---------------------------------------------------------------------------
# Type B -- Personnel migration
# ---------------------------------------------------------------------------


def test_type_b_personnel_migration_critical_when_prosecution() -> None:
    """Fahoum precedent: procurement authority migrating to prosecution target."""
    doc = _doc(
        "E-001",
        (
            "Internal Affairs records: Former Captain Luma Fahoum has been "
            "transferred from procurement oversight. Fahoum is the subject "
            "of a felony prosecution by the Tulare County District "
            "Attorney's office, Case 24-0032442. The indictment cites "
            "ten counts."
        ),
        doc_id="VPD-IA-2024-007",
    )
    findings = detect_cross_entity_anomalies(doc)
    # Fahoum is P-003, with history at both E-001 (VPD) and E-011 (TCDAO).
    # The cross-reference is to E-011 (the prosecution).
    type_b_to_tcdao = [
        f
        for f in findings
        if f["details"]["target_entity"] == "E-011"
        and f["details"]["finding_type"] == "B"
    ]
    assert type_b_to_tcdao, (
        f"expected Type B finding for Fahoum migration to TCDAO; "
        f"got {[f['details'] for f in findings]}"
    )
    # Elevation rule: prosecution/felony/indictment language -> CRITICAL
    assert type_b_to_tcdao[0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# Type C -- Vendor cross-contamination
# ---------------------------------------------------------------------------


def test_type_c_does_not_fire_for_known_vendor_in_jurisdiction() -> None:
    """Axon at Farmersville is already in V-001's presence list -- no Type C."""
    doc = _doc(
        "E-005",  # Farmersville
        (
            "CIP consistency review for FY2025 includes equipment "
            "expenditures: Axon Fleet 3 in-vehicle cameras, $202,409. "
            "Procurement authorized via attachment B."
        ),
        doc_id="FPD-PlanningCmsn-2025-0001",
    )
    findings = detect_cross_entity_anomalies(doc)
    type_c_to_axon = [
        f
        for f in findings
        if f["details"]["target_entity"] == "V-001"
        and f["details"]["finding_type"] == "C"
    ]
    assert not type_c_to_axon, (
        f"Axon is already in E-005's presence list; Type C should not fire. "
        f"got {[f['details'] for f in type_c_to_axon]}"
    )


def test_type_c_fires_when_new_vendor_in_jurisdiction() -> None:
    """BRINC at TCDAO is new presence -- always Type C CRITICAL."""
    doc = _doc(
        "E-011",  # TCDAO
        (
            "The District Attorney's Bureau of Investigations has "
            "deployed BRINC drones for surveillance of cold case scenes. "
            "The deployment was approved on March 1, 2026."
        ),
        doc_id="TCDAO-PR-2026-04-07",
    )
    findings = detect_cross_entity_anomalies(doc)
    # BRINC = V-006, presence = [E-002] only. E-011 not in presence ->
    # Type C cross-contamination, severity CRITICAL.
    type_c_to_brinc = [
        f
        for f in findings
        if f["details"]["target_entity"] == "V-006"
        and f["details"]["finding_type"] == "C"
    ]
    assert type_c_to_brinc, (
        f"expected Type C critical finding for BRINC at TCDAO; "
        f"got {[f['details'] for f in findings]}"
    )
    assert type_c_to_brinc[0]["severity"] == "critical"


# ---------------------------------------------------------------------------
# Type E -- Governance chain
# ---------------------------------------------------------------------------


def test_type_e_governance_chain_to_bos() -> None:
    """TCDAO PR announcing AB 481 meeting per Ordinance 3611 -> Type E -> E-020."""
    doc = _doc(
        "E-011",
        (
            "The Tulare County District Attorney's Office will hold a "
            "public meeting on April 7, 2026, to discuss the AB 481 "
            "Annual Military Equipment Report. Per Ordinance 3611, "
            "the Bureau of Investigations is required to provide annual "
            "reporting on military equipment use. Tulare County Board "
            "of Supervisors action authorized this reporting framework."
        ),
        doc_id="TCDAO-PR-2026-04-07",
    )
    findings = detect_cross_entity_anomalies(doc)
    type_e_to_bos = [
        f
        for f in findings
        if f["details"]["target_entity"] == "E-020"
        and f["details"]["finding_type"] == "E"
    ]
    assert type_e_to_bos, (
        f"expected Type E governance-chain finding to BOS (E-020); "
        f"got {[f['details'] for f in findings]}"
    )


# ---------------------------------------------------------------------------
# Confidence demotion
# ---------------------------------------------------------------------------


def test_low_confidence_findings_demoted_to_low_severity() -> None:
    """An alias hit with no signal pattern in excerpt gets Type D / low severity."""
    doc = _doc(
        "E-001",
        (
            "Routine compliance check note. The Tulare County Board of "
            "Supervisors was referenced by name in this document but no "
            "specific governance action language follows. End of record."
        ),
    )
    findings = detect_cross_entity_anomalies(doc)
    # If a finding fires at all, the default-D-with-low-confidence path
    # should produce severity="low". (Or no finding at all, if the
    # alias scan misses the bare name -- but BOS aliases include "Board
    # of Supervisors" which will match.)
    low_findings = [f for f in findings if f["severity"] == "low"]
    high_findings = [f for f in findings if f["severity"] in ("high", "critical")]
    assert not high_findings, (
        f"expected no high/critical findings on signal-less excerpt; "
        f"got {[f['details'] for f in high_findings]}"
    )
    # And the confidence on the (likely Type D) hit should be < 0.40.
    if low_findings:
        assert low_findings[0]["details"]["confidence"] < 0.40


# ---------------------------------------------------------------------------
# Output shape contract
# ---------------------------------------------------------------------------


def test_finding_output_shape_matches_analysis_contract() -> None:
    """Every emitted finding must match the {id, issue, severity, layer, details} shape."""
    doc = _doc(
        "E-011",
        (
            "The District Attorney has deployed BRINC drones for cold "
            "case surveillance. The deployment was approved on March 1."
        ),
    )
    findings = detect_cross_entity_anomalies(doc)
    assert findings, "expected at least one finding"
    for finding in findings:
        # Standard analysis-package contract (per CLAUDE.md).
        assert set(finding.keys()) >= {"id", "issue", "severity", "layer", "details"}
        assert finding["layer"] == "cross_entity"
        assert finding["severity"] in {"low", "medium", "high", "critical"}
        details = finding["details"]
        # Cross-entity-specific anchors required for downstream XREF
        # register persistence.
        for required_key in (
            "source_entity",
            "target_entity",
            "target_entity_name",
            "finding_type",
            "alias_matched",
            "occurrence_count",
            "confidence",
            "xref_notation",
            "excerpts",
        ):
            assert required_key in details, (
                f"missing required detail key '{required_key}' in {details}"
            )
        assert details["finding_type"] in "ABCDEFG"
        assert details["xref_notation"].startswith("XREF-")
