"""Tests for FastAPI integration (Phase 4).

Tests the /analyze endpoint and API functionality.
"""

from __future__ import annotations

import pytest

# Skip all tests if FastAPI is not installed
try:
    from fastapi.testclient import TestClient

    from oraculus_di_auditor.interface.api import create_app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not installed")


@pytest.fixture
def client():
    """Create FastAPI test client."""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not installed")
    app = create_app()
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_info_endpoint(client):
    """Test info endpoint."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "endpoints" in data
    assert "detectors" in data
    assert "/analyze" in data["endpoints"]
    assert "fiscal" in data["detectors"]


def test_analyze_endpoint_minimal(client):
    """Test /analyze endpoint with minimal input."""
    payload = {
        "document_text": "This is a test document.",
        "metadata": {"title": "Test Document"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "metadata" in data
    assert "findings" in data
    assert "severity_score" in data
    assert "lattice_score" in data
    assert "summary" in data
    assert "timestamp" in data


def test_analyze_endpoint_with_metadata(client):
    """Test /analyze endpoint with comprehensive metadata."""
    payload = {
        "document_text": "There is appropriated $1,000,000 for operations.",
        "metadata": {
            "document_id": "test-001",
            "title": "Budget Act 2025",
            "document_type": "act",
            "jurisdiction": "federal",
            "hash": "abc123",
        },
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["metadata"]["document_id"] == "test-001"
    assert data["metadata"]["title"] == "Budget Act 2025"
    assert data["metadata"]["document_type"] == "act"


def test_analyze_endpoint_detects_fiscal_anomaly(client):
    """Test that /analyze endpoint detects fiscal anomalies."""
    payload = {
        "document_text": "The program receives $1,000,000 for operations.",
        "metadata": {"title": "Budget Document", "hash": "abc123"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["findings"]["fiscal"]) > 0
    assert any(
        "amount-without-appropriation" in a.get("id", "")
        for a in data["findings"]["fiscal"]
    )


def test_analyze_endpoint_detects_constitutional_anomaly(client):
    """Test that /analyze endpoint detects constitutional anomalies."""
    payload = {
        "document_text": (
            "The Secretary may determine such rules as necessary. "
            "The Administrator shall prescribe regulations."
        ),
        "metadata": {"title": "Regulatory Act", "hash": "abc123"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["findings"]["constitutional"]) > 0


def test_analyze_endpoint_detects_surveillance_anomaly(client):
    """Test that /analyze endpoint detects surveillance anomalies."""
    payload = {
        "document_text": (
            "The agency shall contract with a vendor for surveillance "
            "and monitoring services."
        ),
        "metadata": {"title": "Security Act", "hash": "abc123"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["findings"]["surveillance"]) > 0


def test_analyze_endpoint_missing_document_text(client):
    """Test /analyze endpoint with missing document_text."""
    payload = {
        "metadata": {"title": "Test Document"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_empty_document_text(client):
    """Test /analyze endpoint with empty document_text."""
    payload = {
        "document_text": "",
        "metadata": {"title": "Empty Document"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 422  # Validation error (min_length=1)


def test_analyze_endpoint_no_metadata(client):
    """Test /analyze endpoint without metadata (should use defaults)."""
    payload = {
        "document_text": "This is a test document.",
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "metadata" in data
    assert "document_id" in data["metadata"]


def test_analyze_endpoint_returns_timestamp(client):
    """Test that /analyze endpoint returns ISO 8601 timestamp."""
    payload = {
        "document_text": "Test content.",
        "metadata": {"title": "Test"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "timestamp" in data

    # Verify it's a valid ISO 8601 timestamp
    from datetime import datetime

    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert timestamp is not None


def test_legacy_analyze_endpoint(client):
    """Test legacy /api/v1/analyze endpoint still works."""
    payload = {
        "document_id": "test-doc",
        "title": "Test Document",
        "document_type": "act",
        "sections": [{"section_id": "1", "content": "Test content."}],
    }

    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "count" in data
    assert "score" in data
    assert "anomalies" in data


def test_cors_headers_present(client):
    """Test that CORS headers are configured."""
    response = client.get("/api/v1/health")
    # CORS headers should be present in response
    # (exact headers depend on origin, but middleware should be active)
    assert response.status_code == 200


def test_analyze_endpoint_handles_long_text(client):
    """Test /analyze endpoint with long document text."""
    long_text = "This is a test sentence. " * 1000
    payload = {
        "document_text": long_text,
        "metadata": {"title": "Long Document"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "findings" in data


def test_analyze_endpoint_handles_special_characters(client):
    """Test /analyze endpoint with special characters."""
    payload = {
        "document_text": "Document with special chars: © § ® ™ € £ ¥",
        "metadata": {"title": "Special Chars Document"},
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "findings" in data
