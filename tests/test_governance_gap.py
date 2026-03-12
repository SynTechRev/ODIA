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
    """Capabilities covered by governance documentation should be clean."""
    doc = _doc(
        "The department will deploy ALPR units under the following use policy. "
        "A privacy impact assessment has been completed. Oversight is provided "
        "by the city council following council approval and community input. "
        "Data retention is governed by the retention policy filed with the clerk."
    )
    assert detect_governance_gap_anomalies(doc) == []


def test_data_sharing_with_retention_policy_no_retention_gap():
    """Data sharing covered by explicit retention policy should not flag retention gap."""
    doc = _doc(
        "Data sharing agreement with county agencies. "
        "Retention policy: records purged after 60 days per the deletion policy."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert not any(a["id"] == "governance:data-retention-gap" for a in anomalies)


# ---------------------------------------------------------------------------
# governance:capability-without-policy — surveillance tech (critical)
# ---------------------------------------------------------------------------


def test_alpr_without_policy_is_critical():
    """ALPR deployment with no governance documentation → critical."""
    doc = _doc(
        "The city will procure 12 ALPR units for patrol vehicles. "
        "Plates will be scanned in real-time and retained for 90 days."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(a["id"] == "governance:capability-without-policy" for a in anomalies)
    finding = next(
        a for a in anomalies if a["id"] == "governance:capability-without-policy"
    )
    assert finding["severity"] == "critical"
    assert finding["layer"] == "governance"


def test_alpr_details_contain_required_fields():
    doc = _doc("Deploy ALPR units on all major corridors.")
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:capability-without-policy"
        ),
        None,
    )
    assert finding is not None
    assert "capabilities_found" in finding["details"]
    assert "governance_keywords_missing" in finding["details"]
    assert isinstance(finding["details"]["capability_count"], int)
    assert isinstance(finding["details"]["governance_count"], int)
    assert finding["details"]["governance_count"] == 0
    assert "alpr" in finding["details"]["capabilities_found"]


def test_facial_recognition_without_governance_critical():
    doc = _doc("Pilot program for facial recognition at city hall entrances.")
    assert "governance:capability-without-policy" in _ids(
        "Pilot program for facial recognition at city hall entrances."
    )
    finding = next(
        a
        for a in detect_governance_gap_anomalies(doc)
        if a["id"] == "governance:capability-without-policy"
    )
    assert finding["severity"] == "critical"


def test_body_camera_bwc_without_policy_critical():
    doc = _doc("Officers will be issued body cameras (BWC) per department policy.")
    # "BWC" present, no governance keywords → critical
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(a["id"] == "governance:capability-without-policy" for a in anomalies)


def test_cell_site_simulator_without_governance_critical():
    doc = _doc("Authorized use of cell site simulator for active investigations.")
    assert "governance:capability-without-policy" in _ids(
        "Authorized use of cell site simulator for active investigations."
    )


def test_predictive_policing_without_governance_critical():
    doc = _doc("Predictive policing software will be integrated into dispatch.")
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:capability-without-policy"
        ),
        None,
    )
    assert finding is not None
    assert finding["severity"] == "critical"


# ---------------------------------------------------------------------------
# governance:capability-without-policy — data / AI capabilities (high)
# ---------------------------------------------------------------------------


def test_data_sharing_without_governance_high():
    """Data sharing alone (no surveillance tech) should be high, not critical."""
    doc = _doc(
        "This agreement establishes data sharing with the county sheriff's office "
        "and federal access to local records."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    cap_finding = next(
        (a for a in anomalies if a["id"] == "governance:capability-without-policy"),
        None,
    )
    assert cap_finding is not None
    assert cap_finding["severity"] == "high"


def test_ai_report_writing_without_oversight_high():
    """AI/automation capabilities without governance → high severity."""
    doc = _doc(
        "Officers will use Draft One for automated report writing. "
        "AI-generated reports will be submitted directly to records."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    cap_finding = next(
        (a for a in anomalies if a["id"] == "governance:capability-without-policy"),
        None,
    )
    assert cap_finding is not None
    assert cap_finding["severity"] == "high"


def test_machine_learning_without_oversight_high():
    doc = _doc(
        "Machine learning model for call prioritization. No human review required."
    )
    cap_finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:capability-without-policy"
        ),
        None,
    )
    assert cap_finding is not None
    assert cap_finding["severity"] == "high"


# ---------------------------------------------------------------------------
# governance:data-retention-gap
# ---------------------------------------------------------------------------


def test_data_sharing_without_retention_policy_flagged():
    """Data sharing with no retention policy → data-retention-gap."""
    doc = _doc(
        "Data sharing agreement with county. "
        "Interagency access to be established via MOU."
    )
    anomalies = detect_governance_gap_anomalies(doc)
    assert any(a["id"] == "governance:data-retention-gap" for a in anomalies)
    finding = next(a for a in anomalies if a["id"] == "governance:data-retention-gap")
    assert finding["severity"] == "high"
    assert finding["layer"] == "governance"


def test_data_retention_gap_details_contain_keywords_found():
    doc = _doc("Third-party access to records and federal access permitted.")
    finding = next(
        (
            a
            for a in detect_governance_gap_anomalies(doc)
            if a["id"] == "governance:data-retention-gap"
        ),
        None,
    )
    assert finding is not None
    assert len(finding["details"]["data_keywords_found"]) >= 1
    assert "retention_keywords_checked" in finding["details"]


def test_cloud_storage_without_retention_policy_flagged():
    """Cloud storage + data retention capability without a retention policy."""
    doc = _doc(
        "All records will be migrated to cloud storage. "
        "Data retention period is 7 years per state law."
    )
    # "data retention" is present but no "retention policy" keyword
    assert "governance:data-retention-gap" in _ids(
        "All records will be migrated to cloud storage. "
        "Data retention period is 7 years per state law."
    )


# ---------------------------------------------------------------------------
# Both findings together
# ---------------------------------------------------------------------------


def test_surveillance_and_data_sharing_both_ungoverned():
    """ALPR + data sharing with no governance → both findings fire."""
    text = (
        "Deploy ALPR units on patrol vehicles. "
        "Data sharing with federal agencies. "
        "No documentation has been prepared."
    )
    ids = _ids(text)
    assert "governance:capability-without-policy" in ids
    assert "governance:data-retention-gap" in ids
