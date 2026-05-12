"""Tests for the runtime-config routes (v2.10.x).

Covers GET/POST /api/v1/config/webhook-token end-to-end through the
real FastAPI app, with the per-user token file redirected to a tmp
path so we never touch the developer's real %APPDATA%/.local data dir.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402


def _fresh_app():
    from oraculus_di_auditor.interface.api import create_app

    return create_app()


@pytest.fixture(autouse=True)
def _isolate_token_file(monkeypatch, tmp_path):
    """Redirect the token file to a tmp path so the tests are hermetic."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    tmp_token = tmp_path / "webhook_token"
    monkeypatch.setattr(
        webhook_mod, "_user_token_path", lambda: tmp_token, raising=True
    )
    return tmp_token


def test_get_token_status_reports_not_configured(monkeypatch):
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/config/webhook-token")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is False
    assert body["source"] is None
    assert body["env_var"] == "ODIA_WEBHOOK_TOKEN"
    assert "webhook_token" in body["file_path"]


def test_get_token_status_reports_env_source(monkeypatch):
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "env-wins")
    app = _fresh_app()
    client = TestClient(app)

    resp = client.get("/api/v1/config/webhook-token")
    assert resp.status_code == 200
    body = resp.json()
    assert body["configured"] is True
    assert body["source"] == "env"


def test_post_token_persists_to_file_and_activates(monkeypatch, _isolate_token_file):
    """Saving a token via the API should:

    1. Write the value to the per-user token file.
    2. Make /webhook/health report configured=true on the next request.
    3. Make the authenticated /webhook/synthesize endpoint accept the
       new token without a backend restart.
    """
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    app = _fresh_app()
    client = TestClient(app)

    save = client.post(
        "/api/v1/config/webhook-token",
        json={"token": "ui-managed-token"},
    )
    assert save.status_code == 200
    assert save.json()["status"] == "ok"
    assert save.json()["source"] == "file"

    # File written.
    assert _isolate_token_file.read_text(encoding="utf-8") == "ui-managed-token"

    # Health now reports configured without any restart.
    health = client.get("/api/v1/webhook/health")
    assert health.json()["webhook_token_configured"] is True

    # Authenticated endpoint accepts the freshly-saved token. Hit
    # /webhook/synthesize with an empty jurisdiction list — the route
    # short-circuits before doing any I/O, so this only exercises the
    # auth gate (which is all we want to assert here).
    auth_ok = client.post(
        "/api/v1/webhook/synthesize",
        headers={"X-ODIA-Webhook-Token": "ui-managed-token"},
        json={"jurisdictions": []},
    )
    # 401 means the gate is still failing; anything else means the
    # gate let us through. We accept 200/4xx/5xx that aren't 401 — the
    # business logic past auth isn't the focus of this test.
    assert auth_ok.status_code != 401


def test_post_empty_token_clears_file(monkeypatch, _isolate_token_file):
    monkeypatch.delenv("ODIA_WEBHOOK_TOKEN", raising=False)
    _isolate_token_file.write_text("to-be-cleared", encoding="utf-8")
    app = _fresh_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/config/webhook-token",
        json={"token": "   "},
    )
    assert resp.status_code == 200
    assert resp.json()["source"] is None
    assert not _isolate_token_file.exists()


def test_env_shadows_file_when_both_set(monkeypatch, _isolate_token_file):
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", "env-value")
    app = _fresh_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/config/webhook-token",
        json={"token": "file-value"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Resolver still reports env as source even after writing the file.
    assert body["source"] == "env"
    # Surface the conflict so the UI can warn the user.
    assert body["env_shadows_file"] is True
