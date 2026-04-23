"""Tests for /api/v1/automation/* n8n proxy routes (v2.7.3 D7).

Two test scopes:

  1. Pure transformers — ``_transform_workflow`` and
     ``_transform_execution`` round-trip from canonical n8n shapes
     into the WorkflowSummary / ExecutionEvent shapes the frontend
     expects. No I/O.

  2. End-to-end via TestClient with httpx.AsyncClient monkeypatched —
     covers the happy path, 503 fallback when n8n is unreachable, and
     the ``N8N_API_KEY not configured`` 503 gate.

The n8n container is never actually contacted — every test replaces
``httpx.AsyncClient`` with a stub that returns canned responses.
"""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from oraculus_di_auditor.interface.routes.automation import (  # noqa: E402
    _transform_execution,
    _transform_workflow,
)


# ---------------------------------------------------------------------------
# Pure transformer tests
# ---------------------------------------------------------------------------


def test_transform_workflow_carries_id_name_active():
    n8n = {
        "id": 17,
        "name": "CivicPlus Scraper → Tier 1",
        "active": True,
        "updatedAt": "2026-04-23T06:00:00Z",
    }
    out = _transform_workflow(n8n)
    assert out["id"] == "17"
    assert out["name"] == "CivicPlus Scraper → Tier 1"
    assert out["active"] is True
    assert out["status"] == "idle"
    assert out["lastRun"] == "2026-04-23T06:00:00Z"


def test_transform_workflow_uses_tags_as_description():
    n8n = {
        "id": "wf-005",
        "name": "CPRA Deadline Watcher",
        "active": False,
        "tags": [{"name": "cpra"}, {"name": "legal"}],
    }
    out = _transform_workflow(n8n)
    assert "cpra" in out["description"]
    assert "legal" in out["description"]
    assert out["status"] == "unavailable"


def test_transform_execution_success_level():
    n8n = {
        "id": "exec-42",
        "workflowId": "wf-001",
        "status": "success",
        "finished": True,
        "mode": "trigger",
        "startedAt": "2026-04-23T07:00:00Z",
        "stoppedAt": "2026-04-23T07:00:15Z",
    }
    out = _transform_execution(n8n)
    assert out["execution_id"] == "exec-42"
    assert out["workflow_id"] == "wf-001"
    assert out["level"] == "success"
    assert out["ts"] == "2026-04-23T07:00:15Z"
    assert "status=success" in out["message"]


def test_transform_execution_error_level():
    n8n = {
        "id": "exec-99",
        "workflowId": "wf-011",
        "status": "error",
        "finished": False,
        "startedAt": "2026-04-23T08:00:00Z",
    }
    out = _transform_execution(n8n)
    assert out["level"] == "error"
    assert out["ts"] == "2026-04-23T08:00:00Z"


# ---------------------------------------------------------------------------
# httpx.AsyncClient stub utilities
# ---------------------------------------------------------------------------


class _StubResponse:
    def __init__(self, status_code: int, json_body: Any):
        self.status_code = status_code
        self._json = json_body

    def json(self) -> Any:
        return self._json


class _StubAsyncClient:
    """Minimal async-context-manager stub matching the subset of
    httpx.AsyncClient the automation module exercises."""

    def __init__(
        self,
        *,
        timeout: float = 0,
        responses: dict[tuple[str, str], _StubResponse] | None = None,
        raise_on_all: bool = False,
    ):
        self._responses = responses or {}
        self._raise = raise_on_all

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url: str, headers=None, params=None):
        if self._raise:
            raise ConnectionError("stub refused the connection")
        return self._responses[("GET", url)]

    async def post(self, url: str, headers=None, json=None):
        if self._raise:
            raise ConnectionError("stub refused the connection")
        return self._responses[("POST", url)]


def _install_httpx_stub(monkeypatch, factory):
    """Replace httpx.AsyncClient with the caller's factory closure."""
    from oraculus_di_auditor.interface.routes import automation as mod

    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        factory,
    )


@pytest.fixture
def client(monkeypatch):
    # Start each test with a clean N8N_API_KEY so /health works but
    # workflow/execution endpoints 503 unless the test explicitly sets
    # the key. Set N8N_BASE_URL to a known value so assertions work.
    monkeypatch.delenv("N8N_API_KEY", raising=False)
    monkeypatch.setenv("N8N_BASE_URL", "http://n8n.test:5678")

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# /api/v1/automation/health
# ---------------------------------------------------------------------------


def test_health_reports_offline_when_stub_refuses(client, monkeypatch):
    def _factory(*a, **kw):
        return _StubAsyncClient(raise_on_all=True)

    _install_httpx_stub(monkeypatch, _factory)

    resp = client.get("/api/v1/automation/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["n8n_online"] is False
    assert body["n8n_base_url"] == "http://n8n.test:5678"
    assert body["api_key_configured"] is False


def test_health_reports_online_on_200(client, monkeypatch):
    def _factory(*a, **kw):
        return _StubAsyncClient(
            responses={
                ("GET", "http://n8n.test:5678/healthz"): _StubResponse(
                    200, {"status": "ok", "version": "1.24.0"}
                ),
            }
        )

    _install_httpx_stub(monkeypatch, _factory)
    resp = client.get("/api/v1/automation/health")
    body = resp.json()
    assert body["n8n_online"] is True
    assert body["n8n_version"] == "1.24.0"


# ---------------------------------------------------------------------------
# /api/v1/automation/workflows
# ---------------------------------------------------------------------------


def test_workflows_503_when_api_key_missing(client):
    resp = client.get("/api/v1/automation/workflows")
    assert resp.status_code == 503
    assert "N8N_API_KEY" in resp.text


def test_workflows_happy_path(client, monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "test-api-key")

    def _factory(*a, **kw):
        return _StubAsyncClient(
            responses={
                ("GET", "http://n8n.test:5678/api/v1/workflows"): _StubResponse(
                    200,
                    {
                        "data": [
                            {
                                "id": "1",
                                "name": "CivicPlus Scraper",
                                "active": True,
                                "updatedAt": "2026-04-22T00:00:00Z",
                            },
                            {
                                "id": "2",
                                "name": "CPRA Watcher",
                                "active": False,
                            },
                        ]
                    },
                ),
            }
        )

    _install_httpx_stub(monkeypatch, _factory)
    resp = client.get("/api/v1/automation/workflows")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["id"] == "1"
    assert body[0]["active"] is True
    assert body[0]["status"] == "idle"
    assert body[1]["active"] is False
    assert body[1]["status"] == "unavailable"


def test_workflows_503_when_n8n_unreachable(client, monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "test-api-key")

    def _factory(*a, **kw):
        return _StubAsyncClient(raise_on_all=True)

    _install_httpx_stub(monkeypatch, _factory)
    resp = client.get("/api/v1/automation/workflows")
    assert resp.status_code == 503
    assert "unreachable" in resp.text.lower()


# ---------------------------------------------------------------------------
# /api/v1/automation/executions
# ---------------------------------------------------------------------------


def test_executions_503_when_api_key_missing(client):
    resp = client.get("/api/v1/automation/executions")
    assert resp.status_code == 503


def test_executions_happy_path(client, monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "test-api-key")

    def _factory(*a, **kw):
        return _StubAsyncClient(
            responses={
                ("GET", "http://n8n.test:5678/api/v1/executions"): _StubResponse(
                    200,
                    {
                        "data": [
                            {
                                "id": "exec-1",
                                "workflowId": "wf-001",
                                "status": "success",
                                "finished": True,
                                "mode": "trigger",
                                "startedAt": "2026-04-23T10:00:00Z",
                                "stoppedAt": "2026-04-23T10:00:05Z",
                            },
                            {
                                "id": "exec-2",
                                "workflowId": "wf-005",
                                "status": "error",
                                "finished": False,
                                "startedAt": "2026-04-23T11:00:00Z",
                            },
                        ]
                    },
                ),
            }
        )

    _install_httpx_stub(monkeypatch, _factory)
    resp = client.get("/api/v1/automation/executions?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["level"] == "success"
    assert body[1]["level"] == "error"


# ---------------------------------------------------------------------------
# /api/v1/automation/workflows/{id}/run
# ---------------------------------------------------------------------------


def test_run_workflow_503_when_api_key_missing(client):
    resp = client.post("/api/v1/automation/workflows/wf-001/run")
    assert resp.status_code == 503


def test_run_workflow_happy_path(client, monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "test-api-key")

    def _factory(*a, **kw):
        return _StubAsyncClient(
            responses={
                (
                    "POST",
                    "http://n8n.test:5678/api/v1/workflows/wf-001/activate",
                ): _StubResponse(200, {"id": "wf-001", "active": True}),
            }
        )

    _install_httpx_stub(monkeypatch, _factory)
    resp = client.post("/api/v1/automation/workflows/wf-001/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "triggered"
    assert body["workflow_id"] == "wf-001"
    assert body["n8n_response"]["active"] is True
