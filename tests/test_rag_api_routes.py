"""Tests for RAG API routes (POST /api/v1/rag/query, GET /api/v1/rag/status)."""

import pytest

try:
    from fastapi.testclient import TestClient

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

pytestmark = pytest.mark.skipif(not _HAS_FASTAPI, reason="fastapi not installed")


@pytest.fixture()
def client():
    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


# -- test: POST /api/v1/rag/query returns valid response ---------------------


def test_rag_query_returns_response(client):
    resp = client.post(
        "/api/v1/rag/query",
        json={"question": "What anomalies were found?", "top_k": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body
    assert "sources" in body
    assert "query" in body
    assert body["query"] == "What anomalies were found?"


# -- test: POST /api/v1/rag/query with source_filter -------------------------


def test_rag_query_with_source_filter(client):
    resp = client.post(
        "/api/v1/rag/query",
        json={
            "question": "budget allocation",
            "source_filter": "documents",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "answer" in body


# -- test: GET /api/v1/rag/status returns status -----------------------------


def test_rag_status(client):
    resp = client.get("/api/v1/rag/status")
    assert resp.status_code == 200
    body = resp.json()
    assert "indexed" in body
    assert "llm_available" in body
    assert "llm_provider" in body
    assert isinstance(body["indexed"], dict)
