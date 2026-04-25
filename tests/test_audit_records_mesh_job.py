"""Tests for the v2.7.6 X4 ``/audit/run`` → MeshExecutionJob bridge.

Pre-X4 the Orchestrator page's "Recent Mesh Jobs" panel stayed empty
even after dozens of audits because only the legacy n8n-coordinated
path wrote to ``MeshExecutionJob``. These tests pin the new behavior:
a row is inserted on audit start (``status='executing'``), updated on
completion (``status='completed'``), and surfaced through the existing
``/api/v1/orchestrator/executions`` endpoint.
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def audit_client(monkeypatch, tmp_path):
    """create_app() with a fresh SQLite DB + sandboxed upload dir."""
    db_path = tmp_path / "audit_mesh.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.routes import upload as upload_routes

    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(upload_routes, "_UPLOAD_DIR", upload_dir)
    monkeypatch.setattr(upload_routes, "_FILES", {})
    monkeypatch.setattr(upload_routes, "_JOBS", {})

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app), upload_routes, upload_dir


def _stage_txt_file(upload_routes, upload_dir: Path, filename: str, body: str) -> str:
    """Helper: drop a TXT into the upload store and return its file_id."""
    src = upload_dir.parent / filename
    src.write_text(body, encoding="utf-8")
    meta = upload_routes.register_uploaded_path(src, move=True)
    return meta["file_id"]


def test_audit_records_mesh_job_completion(audit_client):
    """End-to-end: stage a TXT, POST /audit/run, wait for completion,
    confirm the MeshExecutionJob row appears in /executions."""
    client, upload_routes, upload_dir = audit_client

    file_id = _stage_txt_file(
        upload_routes,
        upload_dir,
        "x4_test.txt",
        "City Council adopted Resolution 2024-32 authorizing a $298,000 "
        "Flock Safety sole-source procurement on consent calendar Item 7.1. "
        "SB 524 not referenced. CJIS Security Addendum absent.",
    )

    resp = client.post("/api/v1/audit/run", json={"file_ids": [file_id]})
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["job_id"]

    deadline = time.time() + 30.0
    while time.time() < deadline:
        body = client.get(f"/api/v1/audit/status/{job_id}").json()
        if body["status"] in ("complete", "error"):
            break
        time.sleep(0.1)
    assert body["status"] == "complete", body

    execs = client.get("/api/v1/orchestrator/executions").json()
    assert execs["available"] is True
    assert execs["count"] == 1
    row = execs["items"][0]
    assert row["job_id"] == job_id
    assert row["job_type"] == "audit"
    assert row["status"] == "completed"
    assert row["agent_count"] == 6  # ingestion → analysis → … → interface
    assert row["task_count"] == 1
    assert row["completed_at"] is not None


def test_audit_failure_records_failed_status(audit_client, monkeypatch):
    """When the audit pipeline raises, the MeshExecutionJob row must
    be updated to status=failed with the error captured in metadata."""
    client, upload_routes, upload_dir = audit_client

    file_id = _stage_txt_file(
        upload_routes, upload_dir, "x4_failure.txt", "trivial body"
    )

    # Force the analyzer to blow up.
    from oraculus_di_auditor import analysis

    def _bomb(_doc):
        raise RuntimeError("synthetic failure for X4 test")

    monkeypatch.setattr(analysis, "analyze_document", _bomb)

    resp = client.post("/api/v1/audit/run", json={"file_ids": [file_id]})
    job_id = resp.json()["job_id"]

    deadline = time.time() + 10.0
    while time.time() < deadline:
        body = client.get(f"/api/v1/audit/status/{job_id}").json()
        if body["status"] in ("complete", "error"):
            break
        time.sleep(0.1)
    assert body["status"] == "error"

    execs = client.get("/api/v1/orchestrator/executions").json()
    assert execs["count"] == 1
    row = execs["items"][0]
    assert row["job_id"] == job_id
    assert row["status"] == "failed"
    assert row["completed_at"] is not None


def test_orchestrator_status_reflects_recent_completion(audit_client):
    """``tasks_completed_today`` should pick up the audit's
    MeshExecutionJob row once it's marked completed."""
    client, upload_routes, upload_dir = audit_client

    file_id = _stage_txt_file(
        upload_routes,
        upload_dir,
        "x4_status.txt",
        "Resolution 2024-99 authorizing routine matter. No surveillance vendors.",
    )

    resp = client.post("/api/v1/audit/run", json={"file_ids": [file_id]})
    job_id = resp.json()["job_id"]
    deadline = time.time() + 30.0
    while time.time() < deadline:
        body = client.get(f"/api/v1/audit/status/{job_id}").json()
        if body["status"] in ("complete", "error"):
            break
        time.sleep(0.1)
    assert body["status"] == "complete"

    status = client.get("/api/v1/orchestrator/status").json()
    assert status["tasks_completed_today"] >= 1
