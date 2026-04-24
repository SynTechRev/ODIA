"""Confirm ``create_app()`` bootstraps the DB (v2.7.3 V1).

Pre-v2.7.3, SeenHash / Document / Analysis / Anomaly / MeshExecutionJob
tables weren't created at startup — every downstream endpoint that
called ``get_db()`` silently degraded to "DB not initialised". This
test locks in the fix: after ``create_app()``, ``/api/v1/orchestrator/
executions`` reports ``available=True`` even with zero rows.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Fresh per-test SQLite file + reloaded session module."""
    db_path = tmp_path / "startup_init_db.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Reload so init_db() picks up the monkeypatched DATABASE_URL.
    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


def test_orchestrator_executions_available_after_create_app(client):
    """The new create_app() path auto-inits the DB; /executions should
    therefore report available=True with an empty items list rather
    than the old available=False fallback."""
    resp = client.get("/api/v1/orchestrator/executions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["count"] == 0
    assert body["items"] == []


def test_seen_hash_table_present_after_create_app(client):
    """init_db() creates every table in Base.metadata — SeenHash is
    the canary since it's the model most recently added."""
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as session:
        # Empty query — if the table doesn't exist, this raises
        # OperationalError. If it does exist, returns [].
        rows = session.query(db_models.SeenHash).all()
        assert rows == []


def test_orchestrator_status_reflects_initialised_db(client):
    """With an empty-but-initialised AgentNode table, /status still
    falls back to the static 6 (the Python pipeline exists regardless
    of DB rows), but available should be True."""
    resp = client.get("/api/v1/orchestrator/status")
    body = resp.json()
    assert body["available"] is True
    assert body["agents_online"] == 6  # static fallback
