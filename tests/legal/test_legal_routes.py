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


# ===========================================================================
# POST /api/v1/legal/reeval
# ===========================================================================


def test_reeval_missing_document_404(client):
    r = client.post(
        "/api/v1/legal/reeval",
        json={
            "document_id": "nonexistent-doc-xyz",
            "text": "sample document text for re-evaluation",
            "prior_run_date": "2024-01-01",
        },
    )
    # DB may be unavailable (503) or document not found (404) — both are correct
    assert r.status_code in (404, 503)


def test_reeval_missing_fields_422(client):
    r = client.post("/api/v1/legal/reeval", json={"document_id": "x"})
    assert r.status_code == 422


def test_reeval_missing_document_id_422(client):
    r = client.post("/api/v1/legal/reeval", json={"prior_run_date": "2024-01-01"})
    assert r.status_code == 422


# ===========================================================================
# POST /api/v1/legal/detect  (Phase 2 native route)
# ===========================================================================

_CPRA_DENIAL_TEXT = (
    "The department denies the CPRA request under Government Code section 7922.000. "
    "No balancing analysis was provided."
)

_ALPR_POLICY_TEXT = (
    "The department operates ALPR cameras under AB 481 and collects license plate data. "
    "No retention limit or geographic scope has been established."
)

_PREDICTIVE_POLICING_TEXT = (
    "An algorithmic risk score system generates detention recommendations based on "
    "predictive threat assessment scores. No human review process is documented."
)


def test_detect_returns_200(client):
    r = client.post("/api/v1/legal/detect", json={"text": _CPRA_DENIAL_TEXT})
    assert r.status_code == 200, r.text


def test_detect_returns_required_keys(client):
    r = client.post("/api/v1/legal/detect", json={"text": _CPRA_DENIAL_TEXT})
    body = r.json()
    assert "findings" in body
    assert "counts" in body
    assert "errors" in body
    assert "detectors_run" in body


def test_detect_cpra_bare_denial_fires(client):
    """BT-2 from L-10 (or EX-2 from L-3) should fire on bare catch-all denial."""
    r = client.post("/api/v1/legal/detect", json={"text": _CPRA_DENIAL_TEXT})
    body = r.json()
    assert body["counts"]["total"] >= 1


def test_detect_alpr_fires_multiple_detectors(client):
    """ALPR + AB 481 text without scope/cost-benefit triggers L-10 BT-4 and BT-5."""
    r = client.post("/api/v1/legal/detect", json={"text": _ALPR_POLICY_TEXT})
    body = r.json()
    assert body["counts"]["total"] >= 2


def test_detect_findings_sorted_by_severity(client):
    """Findings should be returned sorted critical > high > medium > low."""
    r = client.post("/api/v1/legal/detect", json={"text": _PREDICTIVE_POLICING_TEXT})
    body = r.json()
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sevs = [severity_order.get(f["severity"], 4) for f in body["findings"]]
    assert sevs == sorted(sevs), "Findings should be sorted by descending severity"


def test_detect_finding_structure(client):
    """Each finding must have all ODIA anomaly dict keys."""
    r = client.post("/api/v1/legal/detect", json={"text": _CPRA_DENIAL_TEXT})
    for f in r.json()["findings"]:
        assert "id" in f
        assert "issue" in f
        assert f["severity"] in ("low", "medium", "high", "critical")
        assert f["layer"] == "legal"
        assert "details" in f
        assert "sub_detector" in f["details"]


def test_detect_document_id_propagated(client):
    """document_id in request should be echoed in the response."""
    r = client.post(
        "/api/v1/legal/detect",
        json={"text": _CPRA_DENIAL_TEXT, "document_id": "test-doc-999"},
    )
    assert r.json()["document_id"] == "test-doc-999"


def test_detect_detector_allow_list(client):
    """detectors allow-list should restrict which detectors run."""
    r = client.post(
        "/api/v1/legal/detect",
        json={
            "text": _CPRA_DENIAL_TEXT,
            "detectors": ["l10-balancing-test"],
        },
    )
    body = r.json()
    assert body["detectors_run"] == ["l10-balancing-test"]
    for f in body["findings"]:
        assert f["details"]["sub_detector"] == "l10-balancing-test"


def test_detect_empty_text_returns_200(client):
    """Empty text should not raise an error (L-1 baseline may still fire)."""
    r = client.post("/api/v1/legal/detect", json={"text": ""})
    assert r.status_code == 200
    body = r.json()
    assert "errors" in body
    assert body["errors"] == []


def test_detect_missing_text_422(client):
    """Request without required 'text' field should return 422."""
    r = client.post("/api/v1/legal/detect", json={"document_id": "x"})
    assert r.status_code == 422


def test_detect_counts_add_up(client):
    """Sum of per-severity counts should equal total."""
    r = client.post("/api/v1/legal/detect", json={"text": _ALPR_POLICY_TEXT})
    body = r.json()
    counts = body["counts"]
    per_sev = counts["critical"] + counts["high"] + counts["medium"] + counts["low"]
    assert per_sev == counts["total"]
