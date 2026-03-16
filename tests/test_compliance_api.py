"""Tests for CCOPS compliance API routes (Prompt 9.5)."""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient

    from oraculus_di_auditor.interface.api import create_app

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not _FASTAPI_AVAILABLE, reason="FastAPI not installed")


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /compliance/assess
# ---------------------------------------------------------------------------


def test_assess_returns_200(client):
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": []},
    )
    assert resp.status_code == 200


def test_assess_returns_scorecard(client):
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": []},
    )
    data = resp.json()
    assert data["jurisdiction"] == "test_city"
    assert data["total_mandates"] == 11
    assert "mandate_statuses" in data
    assert len(data["mandate_statuses"]) == 11


def test_assess_with_flat_finding(client):
    """Flat anomaly finding with 'layer' key is routed to the right mandate."""
    finding = {
        "id": "proc:missing-approval",
        "issue": "No council approval found",
        "severity": "high",
        "layer": "procurement_timeline",
        "details": {},
    }
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": [finding]},
    )
    assert resp.status_code == 200
    data = resp.json()
    m01 = next(s for s in data["mandate_statuses"] if s["mandate_id"] == "M-01")
    assert m01["status"] == "non_compliant"


def test_assess_with_nested_findings(client):
    """Nested findings dict (analysis-result format) is correctly flattened."""
    doc = {
        "document_id": "doc1",
        "findings": {
            "governance_gap": [
                {
                    "id": "gov:missing-sir",
                    "issue": "No SIR",
                    "severity": "high",
                    "layer": "governance_gap",
                    "details": {},
                }
            ]
        },
    }
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": [doc]},
    )
    assert resp.status_code == 200
    data = resp.json()
    m02 = next(s for s in data["mandate_statuses"] if s["mandate_id"] == "M-02")
    assert m02["status"] == "non_compliant"


def test_assess_has_overall_risk(client):
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": []},
    )
    data = resp.json()
    assert data["overall_risk"] in ("low", "moderate", "high", "critical", "unknown")


def test_assess_has_ccops_ordinance_flag(client):
    resp = client.post(
        "/compliance/assess",
        json={
            "jurisdiction": "test_city",
            "documents": [],
            "has_ccops_ordinance": True,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["has_ccops_ordinance"] is True


def test_assess_returns_recommendations(client):
    finding = {
        "id": "proc:x",
        "issue": "issue",
        "severity": "high",
        "layer": "procurement_timeline",
        "details": {},
    }
    resp = client.post(
        "/compliance/assess",
        json={"jurisdiction": "test_city", "documents": [finding]},
    )
    data = resp.json()
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1


# ---------------------------------------------------------------------------
# GET /compliance/mandates
# ---------------------------------------------------------------------------


def test_list_mandates_returns_200(client):
    resp = client.get("/compliance/mandates")
    assert resp.status_code == 200


def test_list_mandates_returns_11(client):
    resp = client.get("/compliance/mandates")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 11


def test_list_mandates_ids_are_m01_through_m11(client):
    resp = client.get("/compliance/mandates")
    ids = [m["mandate_id"] for m in resp.json()]
    assert ids == [f"M-{i:02d}" for i in range(1, 12)]


def test_list_mandates_have_required_fields(client):
    resp = client.get("/compliance/mandates")
    for mandate in resp.json():
        assert "mandate_id" in mandate
        assert "title" in mandate
        assert "description" in mandate
        assert "required_evidence" in mandate
        assert "verification_detectors" in mandate
        assert "severity_if_missing" in mandate


# ---------------------------------------------------------------------------
# GET /compliance/mandates/{mandate_id}
# ---------------------------------------------------------------------------


def test_get_mandate_m01_returns_200(client):
    resp = client.get("/compliance/mandates/M-01")
    assert resp.status_code == 200


def test_get_mandate_m01_correct_content(client):
    resp = client.get("/compliance/mandates/M-01")
    data = resp.json()
    assert data["mandate_id"] == "M-01"
    assert "procurement_timeline" in data["verification_detectors"]
    assert data["severity_if_missing"] == "critical"


def test_get_mandate_m06_has_surveillance_detector(client):
    resp = client.get("/compliance/mandates/M-06")
    data = resp.json()
    assert "surveillance" in data["verification_detectors"]


def test_get_mandate_invalid_id_returns_404(client):
    resp = client.get("/compliance/mandates/M-99")
    assert resp.status_code == 404


def test_get_mandate_empty_id_returns_404(client):
    resp = client.get("/compliance/mandates/INVALID")
    assert resp.status_code == 404
