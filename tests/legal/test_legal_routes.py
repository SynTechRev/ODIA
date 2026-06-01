"""Tests for /api/v1/legal/status endpoint."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from oraculus_di_auditor.legal import legal_resolver as _resolver_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    _resolver_mod.reset_resolver_for_testing()
    yield
    _resolver_mod.reset_resolver_for_testing()


@pytest.fixture
def client():
    from oraculus_di_auditor.interface.api import create_app

    return TestClient(create_app())


def test_legal_status_reports_us_code(client):
    """Without the USC submodule the endpoint should still return 200
    (the resolver is initialised-but-empty). With it, us-code stats
    appear in the corpora dict."""
    r = client.get("/api/v1/legal/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert "corpora" in body
    # If the submodule is initialized, us-code will be present.
    submodule_present = Path("data/legal_corpora/us-code/uscode").exists()
    if submodule_present:
        assert "us-code" in body["corpora"], body
        assert body["corpora"]["us-code"]["sections_indexed"] > 5000
    # If not, corpora is just empty (no enabled corpus successfully loaded)
    # but the endpoint itself doesn't fail.


def test_legal_status_includes_detectors(client):
    r = client.get("/api/v1/legal/status")
    body = r.json()
    assert "detectors" in body
    assert "detectors_available" in body
    assert body["detectors_available"] >= 8  # L-1..L-7, L-9, L-10 all available


# ===========================================================================
# POST /api/v1/legal/analyze
# ===========================================================================

_ALPR_TEXT = (
    "The agency deployed ALPR cameras. CPRA requests were denied citing "
    "public interest under § 7922.000 without balancing test analysis. "
    "No AB 481 policy was adopted prior to deployment."
)


def test_analyze_returns_findings(client):
    r = client.post("/api/v1/legal/analyze", json={"text": _ALPR_TEXT})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "findings" in body
    assert "counts" in body
    assert body["counts"]["total"] >= 1


def test_analyze_empty_text_returns_no_findings(client):
    r = client.post("/api/v1/legal/analyze", json={"text": ""})
    assert r.status_code == 200
    assert r.json()["counts"]["total"] == 0


def test_analyze_layer_filter(client):
    r = client.post(
        "/api/v1/legal/analyze",
        json={"text": _ALPR_TEXT, "layers": ["l3_exemption_misapplication"]},
    )
    assert r.status_code == 200
    body = r.json()
    for f in body["findings"]:
        assert f["layer"] == "l3_exemption_misapplication"


def test_analyze_document_id_echoed(client):
    r = client.post(
        "/api/v1/legal/analyze",
        json={"text": _ALPR_TEXT, "document_id": "test-doc-123"},
    )
    assert r.json()["document_id"] == "test-doc-123"


def test_analyze_finding_structure(client):
    r = client.post("/api/v1/legal/analyze", json={"text": _ALPR_TEXT})
    body = r.json()
    for finding in body["findings"]:
        assert "id" in finding
        assert "issue" in finding
        assert finding["severity"] in ("low", "medium", "high")
        assert "layer" in finding
        assert "details" in finding


# ===========================================================================
# POST /api/v1/legal/memorandum
# ===========================================================================

_FINDINGS = [
    {
        "id": "legal:l3:exemption_misapplication:cpra_catchall_no_balancing",
        "issue": "CPRA catch-all exemption invoked without balancing test",
        "severity": "high",
        "layer": "l3_exemption_misapplication",
        "details": {"statute": "Gov. Code § 7922.000"},
    }
]


def test_memorandum_returns_output(client):
    r = client.post(
        "/api/v1/legal/memorandum",
        json={
            "text": _ALPR_TEXT,
            "findings": _FINDINGS,
            "doc_meta": {"title": "ALPR Policy", "agency": "Test PD"},
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "output" in body
    assert "MEMORANDUM" in body["output"]


def test_memorandum_markdown_format(client):
    r = client.post(
        "/api/v1/legal/memorandum",
        json={
            "text": _ALPR_TEXT,
            "findings": _FINDINGS,
            "doc_meta": {},
            "format": "markdown",
        },
    )
    assert r.status_code == 200
    assert r.json()["output"].startswith("# MEMORANDUM")


def test_memorandum_finding_count(client):
    r = client.post(
        "/api/v1/legal/memorandum",
        json={"text": _ALPR_TEXT, "findings": _FINDINGS, "doc_meta": {}},
    )
    assert r.json()["finding_count"] == 1


def test_memorandum_toa_present(client):
    r = client.post(
        "/api/v1/legal/memorandum",
        json={"text": _ALPR_TEXT, "findings": _FINDINGS, "doc_meta": {}},
    )
    assert "toa_citations" in r.json()


# ===========================================================================
# POST /api/v1/legal/explain
# ===========================================================================


def test_explain_community_audience(client):
    r = client.post(
        "/api/v1/legal/explain",
        json={
            "findings": _FINDINGS,
            "doc_meta": {"title": "ALPR Policy"},
            "audience": "community",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "output" in body
    assert body["audience"] == "community"
    assert "FINDINGS AT A GLANCE" in body["output"]


def test_explain_council_audience(client):
    r = client.post(
        "/api/v1/legal/explain",
        json={"findings": _FINDINGS, "doc_meta": {}, "audience": "council"},
    )
    assert r.status_code == 200
    assert r.json()["audience"] == "council"


def test_explain_html_format(client):
    r = client.post(
        "/api/v1/legal/explain",
        json={
            "findings": _FINDINGS,
            "doc_meta": {},
            "audience": "media",
            "format": "html",
        },
    )
    assert r.status_code == 200
    assert "<h1>" in r.json()["output"]


def test_explain_invalid_audience_422(client):
    r = client.post(
        "/api/v1/legal/explain",
        json={"findings": _FINDINGS, "doc_meta": {}, "audience": "robot"},
    )
    assert r.status_code == 422


def test_explain_summary_in_response(client):
    r = client.post(
        "/api/v1/legal/explain",
        json={"findings": _FINDINGS, "doc_meta": {}, "audience": "community"},
    )
    assert "summary" in r.json()
