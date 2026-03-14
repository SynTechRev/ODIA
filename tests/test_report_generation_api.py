"""Tests for POST /reports/generate API endpoint."""

from __future__ import annotations

from typing import Any

import pytest

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from oraculus_di_auditor.interface.routes.reports import (
    register_report_routes,
)

pytestmark = pytest.mark.skipif(not _FASTAPI_AVAILABLE, reason="FastAPI not installed")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_app() -> Any:
    app = FastAPI()
    register_report_routes(app)
    return app


def _anomaly(id_: str, issue: str, severity: str, layer: str) -> dict:
    return {
        "id": id_,
        "issue": issue,
        "severity": severity,
        "layer": layer,
        "details": {},
    }


def _analysis_result(doc_id: str = "doc-1", findings: dict | None = None) -> dict:
    return {
        "metadata": {"document_id": doc_id, "title": f"Doc {doc_id}"},
        "findings": findings
        or {
            "fiscal": [_anomaly("fiscal:t1", "Fiscal issue", "high", "fiscal")],
            "constitutional": [],
            "surveillance": [],
        },
    }


# ---------------------------------------------------------------------------
# POST /reports/generate
# ---------------------------------------------------------------------------


def test_generate_report_returns_200():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [_analysis_result()],
            "jurisdiction": "Test City",
        },
    )
    assert resp.status_code == 200


def test_generate_report_returns_valid_report():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [_analysis_result()],
            "jurisdiction": "Test City",
        },
    )
    data = resp.json()
    assert "report_id" in data
    assert data["report_id"].startswith("RPT-")
    assert "generated_formats" in data
    assert "report" in data


def test_generate_report_report_structure():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [_analysis_result()],
            "jurisdiction": "City A",
            "formats": ["json", "markdown"],
        },
    )
    report = resp.json()["report"]
    assert report["report_type"] == "single_jurisdiction"
    assert report["jurisdiction"] == "City A"
    assert isinstance(report["findings"], list)
    assert len(report["findings"]) >= 1


def test_generate_report_severity_counts():
    client = TestClient(_make_app())
    findings = {
        "fiscal": [
            _anomaly("f:1", "F1", "critical", "fiscal"),
            _anomaly("f:2", "F2", "high", "fiscal"),
        ],
        "constitutional": [],
        "surveillance": [],
    }
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [_analysis_result("doc-1", findings)],
        },
    )
    sev = resp.json()["report"]["severity_summary"]
    assert sev["critical"] == 1
    assert sev["high"] == 1


def test_generate_report_empty_results():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # `total` is a @property — not serialized by Pydantic v2
    assert data["report"]["severity_summary"]["critical"] == 0
    assert data["report"]["severity_summary"]["high"] == 0
    assert data["report"]["findings"] == []


def test_generate_report_multi_type():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "multi",
            "analysis_results": [_analysis_result("doc-A")],
            "jurisdiction": "Multi Test",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["report"]["report_type"] == "multi_jurisdiction"


def test_generate_report_generated_formats_always_includes_json():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [],
            "formats": [
                "pdf"
            ],  # pdf not generated at API level, but json always present
        },
    )
    assert "json" in resp.json()["generated_formats"]


def test_generate_report_multiple_documents():
    client = TestClient(_make_app())
    resp = client.post(
        "/reports/generate",
        json={
            "report_type": "single",
            "analysis_results": [
                _analysis_result("doc-1"),
                _analysis_result("doc-2"),
                {
                    "metadata": {"document_id": "doc-3"},
                    "findings": {
                        "fiscal": [],
                        "constitutional": [],
                        "surveillance": [],
                    },
                },
            ],
            "jurisdiction": "Three-Doc City",
        },
    )
    report = resp.json()["report"]
    assert report["document_count"] == 3
    assert len(report["documents"]) == 3
