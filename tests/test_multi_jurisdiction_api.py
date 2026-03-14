"""Tests for the multi-jurisdiction API routes.

Covers:
  POST /multi/analyze        — comparative analysis across jurisdictions
  GET  /multi/jurisdictions  — registry summary
"""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient

    from oraculus_di_auditor.config.jurisdiction_loader import JurisdictionConfig
    from oraculus_di_auditor.interface.routes.multi_jurisdiction import (
        register_multi_jurisdiction_routes,
    )
    from oraculus_di_auditor.multi_jurisdiction.registry import JurisdictionRegistry

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not _FASTAPI_AVAILABLE, reason="FastAPI not installed")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_registry(*id_name_pairs: tuple[str, str]) -> JurisdictionRegistry:
    registry = JurisdictionRegistry()
    for jid, name in id_name_pairs:
        registry.register(jid, JurisdictionConfig(name=name, state="CA", country="US"))
    return registry


@pytest.fixture
def client():
    """FastAPI test client with multi-jurisdiction routes registered against a
    pre-built registry (avoids filesystem lookups in tests)."""
    from fastapi import FastAPI

    app = FastAPI(title="Test App")
    registry = _make_registry(
        ("city_a", "City Alpha"),
        ("city_b", "City Beta"),
    )
    register_multi_jurisdiction_routes(app, registry=registry)
    return TestClient(app)


# ---------------------------------------------------------------------------
# POST /multi/analyze
# ---------------------------------------------------------------------------


def test_multi_analyze_returns_comparative_report(client):
    payload = {
        "jurisdictions": {
            "city_a": [{"document_text": "Policy document text.", "metadata": {}}],
            "city_b": [
                {
                    "document_text": "The program receives $1,000,000 for operations.",
                    "metadata": {"title": "Budget Doc"},
                }
            ],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["report_type"] == "multi_jurisdiction_comparison"


def test_multi_analyze_has_all_required_sections(client):
    payload = {
        "jurisdictions": {
            "city_a": [{"document_text": "Some text.", "metadata": {}}],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    for key in (
        "report_type",
        "generated_at",
        "jurisdictions",
        "comparison_matrix",
        "cross_jurisdiction_patterns",
        "risk_ranking",
        "recommendations",
    ):
        assert key in data, f"Missing key: {key}"


def test_multi_analyze_includes_both_jurisdictions(client):
    payload = {
        "jurisdictions": {
            "city_a": [{"document_text": "Text for city a.", "metadata": {}}],
            "city_b": [{"document_text": "Text for city b.", "metadata": {}}],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "city_a" in data["jurisdictions"]
    assert "city_b" in data["jurisdictions"]


def test_multi_analyze_unregistered_jurisdiction_still_returns_result(client):
    """Unknown jurisdiction IDs get a bare default config; result is still returned."""
    payload = {
        "jurisdictions": {
            "unknown_city": [{"document_text": "Some text here.", "metadata": {}}],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "unknown_city" in data["jurisdictions"]


def test_multi_analyze_empty_jurisdictions_rejected(client):
    """Empty jurisdictions dict must be rejected with 422."""
    payload = {"jurisdictions": {}}
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 422


def test_multi_analyze_missing_document_text_rejected(client):
    """Document with no text must be rejected with 422."""
    payload = {
        "jurisdictions": {
            "city_a": [{"document_text": "", "metadata": {}}],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 422


def test_multi_analyze_risk_ranking_present(client):
    payload = {
        "jurisdictions": {
            "city_a": [{"document_text": "Text.", "metadata": {}}],
            "city_b": [{"document_text": "Text.", "metadata": {}}],
        }
    }
    response = client.post("/multi/analyze", json=payload)
    assert response.status_code == 200
    ranking = response.json()["risk_ranking"]
    assert isinstance(ranking, list)
    assert len(ranking) == 2


# ---------------------------------------------------------------------------
# GET /multi/jurisdictions
# ---------------------------------------------------------------------------


def test_multi_jurisdictions_returns_registry_summary(client):
    response = client.get("/multi/jurisdictions")
    assert response.status_code == 200
    data = response.json()

    assert "count" in data
    assert "jurisdictions" in data
    assert isinstance(data["count"], int)
    assert isinstance(data["jurisdictions"], dict)


def test_multi_jurisdictions_count_matches_registered(client):
    response = client.get("/multi/jurisdictions")
    assert response.status_code == 200
    data = response.json()
    # The fixture registered city_a and city_b
    assert data["count"] == 2
    assert "city_a" in data["jurisdictions"]
    assert "city_b" in data["jurisdictions"]


def test_multi_jurisdictions_entries_have_required_fields(client):
    response = client.get("/multi/jurisdictions")
    assert response.status_code == 200
    for _jid, entry in response.json()["jurisdictions"].items():
        for field in ("name", "state", "country", "agency_count", "corpus_entry_count"):
            assert field in entry, f"Missing field: {field}"
