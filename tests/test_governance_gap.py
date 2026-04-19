"""Tests for governance gap detector."""

from __future__ import annotations

from oraculus_di_auditor.analysis.governance_gap import (
    detect_governance_gap_anomalies,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _doc(text: str) -> dict:
    return {"document_id": "test-doc", "raw_text": text}


def _ids(text: str) -> set[str]:
    return {a["id"] for a in detect_governance_gap_anomalies(_doc(text))}


# ---------------------------------------------------------------------------
# No-anomaly cases
# ---------------------------------------------------------------------------


def test_empty_document_no_anomalies():
    assert detect_governance_gap_anomalies({"document_id": "x"}) == []


def test_non_dict_input_returns_empty():
    assert detect_governance_gap_anomalies(None) == []
    assert detect_governance_gap_anomalies("not a doc") == []
    assert detect_governance_gap_anomalies(42) == []


def test_governance_only_no_capabilities_no_anomalies():
    """Governance keywords without any capability keywords should not flag."""
    doc = _doc(
        "This policy establishes a privacy policy and retention policy "
        "for oversight of city operations. Council approval is required. "
        "A privacy impact assessment must be completed."
    )
    assert detect_governance_gap_anomalies(doc) == []


def test_capabilities_with_full_governance_no_anomalies():
    """Capabilities covered by all governance artefacts should be clean."""
    doc = _doc(
        "The department will deploy ALPR units under the following use policy. "
        "A privacy impact assessment has been completed. Oversight is provided "
        "by the city council following council approval and community input. "
        "Data retention is governed by the retention policy filed with the clerk. "
        "All deployments are listed in the public transparency portal "
        "surveillance inventory."
    )
    assert detect_governance_gap_anomalies(doc) == []


def test_data_sharing_with_retention_policy_no_retention_gap():
    """Data sharing with explicit retention policy should not flag retention gap."""
    doc = _doc(
        "Data sharing agreement with county agencies. "
        "Retention policy: records purged after 60 days per the deletion policy."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert not any(a["id"] == "governance:data-retention-gap" for a in anomalies)


# ---------------------------------------------------------------------------
# governance:capability-without-council-approval — surveillance tech (critical)
# ---------------------------------------------------------------------------


def test_alpr_without_policy_is_critical():
    """ALPR deployment with no governance documentation → critical."""
    doc = _doc(
        "The city will procure 12 ALPR units for patrol vehicles. "
        "Plates will be scanned in real-time and retained for 90 days."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(
        a["id"] == "governance:capability-without-council-approval" for a in anomalies
    )
    finding = next(
        a
        for a in anomalies
        if a["id"] == "governance:capability-without-council-approval"
    )
    assert finding["severity"] == "critical"
    assert finding["layer"] == "governance"


def test_alpr_details_contain_required_fields():
    doc = _doc("Deploy ALPR units on all major corridors.")
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:capability-without-council-approval"
        ),
        None,
    )
    assert finding is not None
    assert "technologies" in finding["details"]
    assert "alpr" in finding["details"]["technologies"]
    assert "vendors" in finding["details"]


def test_facial_recognition_without_governance_critical():
    doc = _doc("Pilot program for facial recognition at city hall entrances.")
    assert "governance:capability-without-council-approval" in _ids(
        "Pilot program for facial recognition at city hall entrances."
    )
    finding = next(
        a
        for a in detect_governance_gap_anomalies(doc)
        if a["id"] == "governance:capability-without-council-approval"
    )
    assert finding["severity"] == "critical"


def test_body_camera_bwc_without_policy_critical():
    doc = _doc("Officers will be issued body cameras (BWC) per department policy.")
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(
        a["id"] == "governance:capability-without-council-approval" for a in anomalies
    )


def test_cell_site_simulator_without_governance_critical():
    assert "governance:capability-without-council-approval" in _ids(
        "Authorized use of cell site simulator for active investigations."
    )


def test_predictive_policing_without_governance_critical():
    doc = _doc("Predictive policing software will be integrated into dispatch.")
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:capability-without-council-approval"
        ),
        None,
    )
    assert finding is not None
    assert finding["severity"] == "critical"


# ---------------------------------------------------------------------------
# governance:data-retention-gap (high)
# ---------------------------------------------------------------------------


def test_alpr_without_retention_policy_flagged():
    """ALPR without a retention policy → data-retention-gap (high)."""
    doc = _doc(
        "The agency will deploy ALPR license plate readers on patrol routes. "
        "Vendor will store captured images indefinitely."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(a["id"] == "governance:data-retention-gap" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "governance:data-retention-gap")
    assert finding["severity"] == "high"
    assert finding["layer"] == "governance"


def test_surveillance_capability_without_retention_high():
    """Facial recognition without retention policy → data-retention-gap."""
    doc = _doc(
        "Facial recognition system installed at transit hubs. "
        "Data stored on vendor servers."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(a["id"] == "governance:data-retention-gap" for a in anomalies)


def test_data_retention_gap_details_contain_technologies():
    doc = _doc(
        "ALPR deployment on all major corridors. Vendor stores data indefinitely."
    )
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:data-retention-gap"
        ),
        None,
    )
    assert finding is not None
    assert "technologies" in finding["details"]
    assert len(finding["details"]["technologies"]) >= 1


def test_sole_source_without_justification_flagged():
    """Sole-source procurement without Gov Code justification → high."""
    assert "governance:sole-source-without-justification" in _ids(
        "Sole source procurement of ALPR cameras from Flock Safety. "
        "No competing vendors evaluated."
    )


# ---------------------------------------------------------------------------
# governance:auto-renewal-clause + governance:lexipol-boilerplate
# ---------------------------------------------------------------------------


def test_auto_renewal_clause_detected():
    """Auto-renewal clause in contract → medium finding."""
    assert "governance:auto-renewal-clause" in _ids(
        "ALPR contract auto-renews annually unless written notice of non-renewal "
        "is provided 90 days in advance."
    )


def test_lexipol_boilerplate_detected():
    """Lexipol California State Master boilerplate → medium finding."""
    assert "governance:lexipol-boilerplate" in _ids(
        "Lexipol California State Master policy adopted for BWC deployment."
    )


# ---------------------------------------------------------------------------
# Both capability findings together
# ---------------------------------------------------------------------------


def test_surveillance_and_data_sharing_both_ungoverned():
    """ALPR with no council approval and no retention policy → both findings fire."""
    text = (
        "Deploy ALPR units on patrol vehicles. "
        "Data sharing with federal agencies. "
        "No documentation has been prepared."
    )
    ids = _ids(text)
    assert "governance:capability-without-council-approval" in ids
    assert "governance:data-retention-gap" in ids
