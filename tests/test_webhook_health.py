"""Integration tests for the n8n webhook /health probe + token gate.

v2.10.x contract:
  1. Routes register unconditionally so the Settings UI can manage the
     token at runtime.  When no token is configured (env or per-user
     file), /api/v1/webhook/health returns 200 with
     ``webhook_token_configured: false`` and every authenticated
     endpoint returns 401.
  2. When a token is configured, /health reports it and the
     authenticated endpoints accept matching credentials.

The file-fallback path is monkeypatched to a tmp_path so the tests
don't see (or clobber) whatever the developer has stored in their real
``%APPDATA%\\ODIA\\webhook_token``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # FastAPI TestClient needs httpx

from fastapi.testclient import TestClient  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fresh_app():
    """Build a fresh FastAPI app.  Route registration reads the token
    state at call time, so a plain ``create_app()`` picks up monkey-
    patched env / paths without needing a module reload."""
    from oraculus_di_auditor.interface.api import create_app

    return create_app()


@pytest.fixture(autouse=True)
def _isolate_token_file(monkeypatch, tmp_path):
    """Redirect the per-user token file to a tmp path for every test
    in this module so we never read or write the real user data dir."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    tmp_token = tmp_path / "webhook_token"
    monkeypatch.setattr(
        webhook_mod, "_user_token_path", lambda: tmp_token, raising=True
    )
    return tmp_token


# ---------------------------------------------------------------------------
# Token-absent path  (v2.10.x — routes register anyway)
# ---------------------------------------------------------------------------


def test_health_returns_200_when_token_unset(monkeypatch):
    """v2.10.x — with no token configured anywhere, /health still
    responds 200 but reports ``webhook_token_configured: false``.

    Pre-v2.10.x this returned 404 because the route refused to
    register.  The new behaviour lets the Settings UI manage the
    token at runtime without a backend restart, and surfaces the
    "not configured" state as a structured field instead of a 404.
    """
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/webhook/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["webhook_token_configured"] is False

    # The protected endpoints must still 401 when no token is configured,
    # so a misconfigured install can't be exploited even though /health
    # responds 200 now.
    protected = client.post(
        "/api/v1/webhook/synthesize",
        headers={"X-ODIA-Webhook-Token": "anything"},
        json={"jurisdictions": ["woodlake"]},
    )
    assert protected.status_code == 401


def test_health_reflects_file_fallback_token(monkeypatch, _isolate_token_file):
    """If no env var is set but the per-user file holds a token, the
    resolver picks the file value and /health reports configured=true.
    """
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    Path(_isolate_token_file).write_text("file-fallback-token", encoding="utf-8")

    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/webhook/health")
    assert resp.status_code == 200
    assert resp.json()["webhook_token_configured"] is True


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
