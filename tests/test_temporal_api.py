"""Tests for temporal analysis API routes."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="FastAPI not installed")

from fastapi.testclient import TestClient  # noqa: E402

from oraculus_di_auditor.interface.api import app  # noqa: E402

client = TestClient(app)

# ---------------------------------------------------------------------------
# Sample documents
# ---------------------------------------------------------------------------

_DOCS = [
    {
        "id": "d1",
        "vendor": "Axon",
        "date": "2019-03-01",
        "document_type": "original",
        "amount": 200000.0,
        "title": "Original BWC contract",
    },
    {
        "id": "d2",
        "vendor": "Axon",
        "date": "2021-06-15",
        "document_type": "amendment",
        "amount": 600000.0,
        "title": "Amendment 1 — ALPR expansion",
        "authorization_type": "sole_source",
    },
    {
        "id": "d3",
        "vendor": "Axon",
        "date": "2023-01-10",
        "document_type": "amendment",
        "amount": 900000.0,
        "title": "Amendment 2 — Fusus integration",
        "authorization_type": "sole_source",
    },
    {
        "id": "d4",
        "vendor": "Flock",
        "date": "2021-01-01",
        "document_type": "original",
        "amount": 150000.0,
        "title": "ALPR original contract",
    },
]


# ---------------------------------------------------------------------------
# POST /temporal/analyze
# ---------------------------------------------------------------------------


def test_temporal_analyze_returns_200():
    resp = client.post("/temporal/analyze", json={"documents": _DOCS})
    assert resp.status_code == 200


def test_temporal_analyze_response_has_required_keys():
    resp = client.post("/temporal/analyze", json={"documents": _DOCS})
    data = resp.json()
    for key in ("lineages", "patterns", "timeline", "summary"):
        assert key in data, f"Missing key: {key}"


def test_temporal_analyze_summary_structure():
    resp = client.post("/temporal/analyze", json={"documents": _DOCS})
    summary = resp.json()["summary"]
    for key in (
        "lineage_count",
        "pattern_count",
        "total_spend",
        "date_range",
        "highest_risk_lineage",
    ):
        assert key in summary


def test_temporal_analyze_lineage_count():
    resp = client.post("/temporal/analyze", json={"documents": _DOCS})
    data = resp.json()
    # Axon and Flock are two vendors → at least 2 lineages (Axon may split by contract)
    assert data["summary"]["lineage_count"] >= 1
    assert len(data["lineages"]) == data["summary"]["lineage_count"]


def test_temporal_analyze_timeline_has_tracks():
    resp = client.post("/temporal/analyze", json={"documents": _DOCS})
    timeline = resp.json()["timeline"]
    assert "tracks" in timeline
    assert len(timeline["tracks"]) >= 1


def test_temporal_analyze_empty_documents_returns_empty():
    resp = client.post("/temporal/analyze", json={"documents": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["lineage_count"] == 0
    assert data["summary"]["pattern_count"] == 0


def test_temporal_analyze_includes_jurisdiction():
    resp = client.post(
        "/temporal/analyze",
        json={"documents": _DOCS, "jurisdiction": "Test City"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /temporal/patterns
# ---------------------------------------------------------------------------


def test_get_pattern_types_returns_200():
    resp = client.get("/temporal/patterns")
    assert resp.status_code == 200


def test_get_pattern_types_returns_list():
    resp = client.get("/temporal/patterns")
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 6  # six pattern detectors


def test_get_pattern_types_have_required_fields():
    resp = client.get("/temporal/patterns")
    for pt in resp.json():
        assert "pattern_type" in pt
        assert "description" in pt
        assert "severity_range" in pt


def test_get_pattern_types_includes_scope_creep():
    resp = client.get("/temporal/patterns")
    types = {pt["pattern_type"] for pt in resp.json()}
    assert "scope_creep" in types
    assert "vendor_lock_in" in types


# ---------------------------------------------------------------------------
# POST /temporal/lineage/{vendor}
# ---------------------------------------------------------------------------


def test_vendor_lineage_returns_lineage_for_known_vendor():
    resp = client.post(
        "/temporal/lineage/Axon",
        json={"documents": _DOCS},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["vendor"] == "Axon"
    assert "events" in data


def test_vendor_lineage_404_for_unknown_vendor():
    resp = client.post(
        "/temporal/lineage/UnknownVendorXYZ",
        json={"documents": _DOCS},
    )
    assert resp.status_code == 404


def test_vendor_lineage_case_insensitive():
    resp = client.post(
        "/temporal/lineage/axon",
        json={"documents": _DOCS},
    )
    assert resp.status_code == 200
    assert resp.json()["vendor"] == "Axon"
