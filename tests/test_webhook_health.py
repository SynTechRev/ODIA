"""Integration tests for the n8n webhook /health probe + token gate.

Two paths to cover:
  1. ODIA_WEBHOOK_TOKEN unset → register_webhook_routes refuses to
     register; /api/v1/webhook/health returns 404.
  2. ODIA_WEBHOOK_TOKEN set → routes register; health returns 200 with
     `tier1_ready`, `tier2_ready`, `webhook_token_configured` keys.

The test pattern mirrors test_upload_routes.py: monkeypatch the env,
call create_app(), drive TestClient.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # FastAPI TestClient needs httpx

from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_app():
    """Build a fresh FastAPI app. We re-import create_app each call to
    pick up env var changes that the webhook registrar gates on at
    import time (the env check runs inside register_webhook_routes, so
    a plain re-call of create_app is sufficient — no module reload
    needed)."""
    from oraculus_di_auditor.interface.api import create_app

    return create_app()


# ---------------------------------------------------------------------------
# Token-absent path
# ---------------------------------------------------------------------------


def test_health_returns_404_when_token_unset(monkeypatch):
    """Without ODIA_WEBHOOK_TOKEN, the webhook surface must not register.

    The whole point of the guard is that a misconfigured deployment
    fails loud rather than silently exposing an unauthenticated
    pipeline. A 404 here is the observable signal that the guard fired.
    """
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/webhook/health")
    assert resp.status_code == 404

    # Also confirm no /api/v1/webhook/* route sneaked in through some
    # other registration path.
    webhook_paths = [
        str(getattr(r, "path", ""))
        for r in app.routes
        if "/webhook/" in str(getattr(r, "path", ""))
    ]
    assert webhook_paths == []


# ---------------------------------------------------------------------------
# Token-present path
# ---------------------------------------------------------------------------


def test_health_returns_200_when_token_set(monkeypatch):
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "a-test-token-for-pytest")
    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/webhook/health")
    assert resp.status_code == 200

    body = resp.json()
    # Contract keys that WF-014 (Provenance Chain Export) asserts on.
    for key in ("status", "tier1_ready", "tier2_ready", "webhook_token_configured"):
        assert key in body, f"expected key '{key}' in health response, got {body}"

    assert body["webhook_token_configured"] is True
    assert isinstance(body["tier1_ready"], bool)
    assert isinstance(body["tier2_ready"], bool)
    # If tier1 imports resolve, status should be "healthy"; if not, "degraded".
    # Either is acceptable for a health probe — we just assert it's a
    # well-formed value.
    assert body["status"] in ("healthy", "degraded")


def test_health_does_not_require_token_header(monkeypatch):
    """The /health endpoint is intentionally the ONE webhook route that
    doesn't demand the X-ODIA-Webhook-Token header — it's a liveness
    probe for orchestration layers that may not carry credentials.

    Verifies by calling without the header and expecting 200.
    """
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "a-test-token-for-pytest")
    app = _fresh_app()
    client = TestClient(app)

    # No X-ODIA-Webhook-Token header
    resp = client.get("/api/v1/webhook/health")
    assert resp.status_code == 200


def test_protected_endpoint_rejects_missing_token(monkeypatch):
    """Sanity check the complement: a real protected endpoint 401s when
    the token is missing. Proves the shared-secret gate is actually
    wired, not just inert."""
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "a-test-token-for-pytest")
    app = _fresh_app()
    client = TestClient(app)

    # /synthesize requires the token; hit it without one.
    resp = client.post(
        "/api/v1/webhook/synthesize",
        json={"jurisdictions": ["woodlake"]},
    )
    assert resp.status_code == 401


def test_protected_endpoint_rejects_wrong_token(monkeypatch):
    """A wrong token also 401s (constant-time compare guards against
    timing leaks, but the functional requirement is just a rejection)."""
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "a-test-token-for-pytest")
    app = _fresh_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/webhook/synthesize",
        headers={"X-ODIA-Webhook-Token": "wrong-token"},
        json={"jurisdictions": ["woodlake"]},
    )
    assert resp.status_code == 401
