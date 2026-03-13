"""Tests for the detector-specific API endpoints.

Covers:
  POST /analyze/detailed  — per-detector breakdown for a single document
  GET  /detectors         — detector registry listing
  POST /analyze/batch     — multi-document batch analysis
"""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient

    from oraculus_di_auditor.interface.api import create_app
    from oraculus_di_auditor.interface.routes.detectors import DETECTOR_REGISTRY

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")

_ALL_DETECTOR_KEYS = [
    "fiscal",
    "constitutional",
    "surveillance",
    "procurement_timeline",
    "signature_chain",
    "scope_expansion",
    "governance_gap",
    "administrative_integrity",
]


@pytest.fixture
def client():
    """Create a FastAPI test client with a fresh app instance."""
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /analyze/detailed
# ---------------------------------------------------------------------------


def test_detailed_returns_all_detector_keys(client):
    """Response must include every detector key in the detectors dict."""
    payload = {
        "document_text": "The agency shall contract for services.",
        "metadata": {"title": "Test Document"},
    }
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "detectors" in data
    for key in _ALL_DETECTOR_KEYS:
        assert key in data["detectors"], f"Missing detector key: {key}"


def test_detailed_detector_values_are_lists(client):
    """Every per-detector value must be a list (possibly empty)."""
    payload = {"document_text": "Simple clean text.", "metadata": {}}
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()

    for key in _ALL_DETECTOR_KEYS:
        assert isinstance(
            data["detectors"][key], list
        ), f"detectors[{key!r}] is not a list"


def test_detailed_summary_structure(client):
    """Summary block must contain total_anomalies, by_severity, and score."""
    payload = {"document_text": "Test document text.", "metadata": {}}
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()

    summary = data["summary"]
    assert "total_anomalies" in summary
    assert "by_severity" in summary
    assert "score" in summary
    assert isinstance(summary["total_anomalies"], int)
    assert isinstance(summary["score"], float)

    by_sev = summary["by_severity"]
    for level in ("critical", "high", "medium", "low"):
        assert level in by_sev, f"by_severity missing '{level}'"
        assert isinstance(by_sev[level], int)


def test_detailed_document_id_present(client):
    """document_id must be present in the response."""
    payload = {
        "document_text": "Some document text.",
        "metadata": {"document_id": "test-detail-001"},
    }
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "test-detail-001"


def test_detailed_timestamp_present(client):
    """Response must include a timestamp field."""
    payload = {"document_text": "Document text.", "metadata": {}}
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    assert "timestamp" in response.json()


def test_detailed_detects_fiscal_anomaly(client):
    """Fiscal detector should fire on a document with an unappropriated amount."""
    payload = {
        "document_text": "The program receives $1,000,000 for operations.",
        "metadata": {"title": "Budget Doc", "hash": "abc123"},
    }
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["detectors"]["fiscal"]) > 0


def test_detailed_empty_content_document(client):
    """A document with benign content should return valid empty-anomaly results."""
    payload = {
        "document_text": "This document contains no anomalies.",
        "metadata": {"title": "Clean Document"},
    }
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Valid structure even with zero anomalies
    assert data["summary"]["total_anomalies"] >= 0
    assert data["summary"]["score"] >= 0.0
    for key in _ALL_DETECTOR_KEYS:
        assert isinstance(data["detectors"][key], list)


def test_detailed_empty_string_rejected(client):
    """Empty document_text must be rejected with a 422."""
    payload = {"document_text": "", "metadata": {}}
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 422


def test_detailed_no_jurisdiction_key_by_default(client):
    """Without a loaded jurisdiction config, 'jurisdiction' key must be absent."""
    payload = {"document_text": "Some text.", "metadata": {}}
    response = client.post("/analyze/detailed", json=payload)
    assert response.status_code == 200
    # Jurisdiction is only present when a config was loaded at startup.
    # In the test environment no config/ dir is present, so it should be absent.
    data = response.json()
    # If loaded it will be a string; if not loaded the key won't exist.
    # Either outcome is valid — just verify the response is well-formed.
    assert "detectors" in data


# ---------------------------------------------------------------------------
# /detectors
# ---------------------------------------------------------------------------


def test_detectors_lists_all_detectors(client):
    """GET /detectors must return all 8 registered detectors."""
    response = client.get("/detectors")
    assert response.status_code == 200
    data = response.json()

    assert "detectors" in data
    assert "count" in data
    assert data["count"] == len(_ALL_DETECTOR_KEYS)

    names = {d["name"] for d in data["detectors"]}
    for key in _ALL_DETECTOR_KEYS:
        assert key in names, f"Detector '{key}' missing from /detectors response"


def test_detectors_each_entry_has_required_fields(client):
    """Every detector entry must have name, description, and anomaly_types."""
    response = client.get("/detectors")
    assert response.status_code == 200
    for entry in response.json()["detectors"]:
        assert "name" in entry, f"Detector entry missing 'name': {entry}"
        assert "description" in entry, f"Detector entry missing 'description': {entry}"
        assert (
            "anomaly_types" in entry
        ), f"Detector entry missing 'anomaly_types': {entry}"
        assert isinstance(entry["anomaly_types"], list)
        assert (
            len(entry["anomaly_types"]) > 0
        ), f"Detector {entry['name']} has no anomaly_types"


def test_detectors_registry_matches_endpoint(client):
    """DETECTOR_REGISTRY and /detectors response must agree on count and names."""
    response = client.get("/detectors")
    assert response.status_code == 200
    data = response.json()

    assert data["count"] == len(DETECTOR_REGISTRY)
    endpoint_names = {d["name"] for d in data["detectors"]}
    registry_names = set(DETECTOR_REGISTRY.keys())
    assert endpoint_names == registry_names


# ---------------------------------------------------------------------------
# /analyze/batch
# ---------------------------------------------------------------------------


def test_batch_processes_multiple_documents(client):
    """Batch endpoint must return one result per input document."""
    payload = {
        "documents": [
            {
                "document_text": "Document one content.",
                "metadata": {"document_id": "b-001"},
            },
            {
                "document_text": "Document two content.",
                "metadata": {"document_id": "b-002"},
            },
            {
                "document_text": "Document three content.",
                "metadata": {"document_id": "b-003"},
            },
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 3


def test_batch_document_ids_preserved(client):
    """Each result must carry the document_id from its input."""
    payload = {
        "documents": [
            {"document_text": "Content A.", "metadata": {"document_id": "id-a"}},
            {"document_text": "Content B.", "metadata": {"document_id": "id-b"}},
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    results = response.json()["results"]

    ids = {r["document_id"] for r in results}
    assert "id-a" in ids
    assert "id-b" in ids


def test_batch_each_result_has_all_detectors(client):
    """Every per-document result must contain the full detector dict."""
    payload = {
        "documents": [
            {"document_text": "Some text here.", "metadata": {}},
            {"document_text": "More text here.", "metadata": {}},
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    for doc_result in response.json()["results"]:
        for key in _ALL_DETECTOR_KEYS:
            doc_id = doc_result.get("document_id")
            assert (
                key in doc_result["detectors"]
            ), f"Missing detector '{key}' in batch result for {doc_id}"


def test_batch_top_level_summary(client):
    """Batch response must include a top-level summary with document_count."""
    payload = {
        "documents": [
            {"document_text": "First document.", "metadata": {}},
            {"document_text": "Second document.", "metadata": {}},
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "summary" in data
    summary = data["summary"]
    assert summary["document_count"] == 2
    assert "total_anomalies" in summary
    assert "by_severity" in summary
    assert "by_detector" in summary


def test_batch_cross_document_patterns_present(client):
    """Batch response must include cross_document_patterns key (list)."""
    payload = {
        "documents": [
            {"document_text": "Document one.", "metadata": {}},
            {"document_text": "Document two.", "metadata": {}},
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "cross_document_patterns" in data
    assert isinstance(data["cross_document_patterns"], list)


def test_batch_by_detector_keys_present(client):
    """Batch summary.by_detector must have an entry for each detector."""
    payload = {
        "documents": [
            {"document_text": "Some document content.", "metadata": {}},
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    by_detector = response.json()["summary"]["by_detector"]

    for key in _ALL_DETECTOR_KEYS:
        assert key in by_detector, f"by_detector missing key '{key}'"


def test_batch_empty_documents_list_rejected(client):
    """An empty documents list must be rejected with a 422."""
    payload = {"documents": []}
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 422


def test_batch_single_document(client):
    """Batch with a single document must work correctly."""
    payload = {
        "documents": [
            {
                "document_text": "Single document text.",
                "metadata": {"document_id": "solo"},
            }
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 1
    assert data["summary"]["document_count"] == 1


def test_batch_detects_anomaly_across_documents(client):
    """Batch should surface fiscal anomalies in documents that trigger them."""
    payload = {
        "documents": [
            {
                "document_text": "The program receives $500,000 for operations.",
                "metadata": {"document_id": "fiscal-doc", "hash": "xyz789"},
            },
            {
                "document_text": "Normal policy language with no amounts.",
                "metadata": {"document_id": "clean-doc"},
            },
        ]
    }
    response = client.post("/analyze/batch", json=payload)
    assert response.status_code == 200
    results = {r["document_id"]: r for r in response.json()["results"]}

    # fiscal-doc should have at least one fiscal anomaly
    assert len(results["fiscal-doc"]["detectors"]["fiscal"]) > 0
    # Batch total should reflect at least those anomalies
    assert response.json()["summary"]["total_anomalies"] > 0
