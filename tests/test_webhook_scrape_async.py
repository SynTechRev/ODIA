"""Integration tests for POST /api/v1/webhook/scrape-and-ingest-async (v3.0.3).

The async variant returns 202 + job_id immediately and runs the download +
Tier-1 audit on a daemon thread. ``/api/v1/webhook/status/{job_id}`` polls
the same in-memory registry the synchronous endpoints use.

Tests directly drive the module-level worker function (synchronous) so we
get deterministic state transitions without sleeping on a background
thread. A separate end-to-end test exercises the real thread path with a
bounded poll loop.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

TOKEN = "a-test-token-for-pytest"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_audit_doc.txt"
SAMPLE_URL = "https://www.visalia.gov/AgendaCenter/ViewFile/Agenda/_05062026-821"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def webhook_app(monkeypatch, tmp_path):
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", TOKEN)

    db_path = tmp_path / "odia_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    import importlib

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    return create_app()


@pytest.fixture
def client(webhook_app):
    return TestClient(webhook_app)


@pytest.fixture(autouse=True)
def reset_batch_jobs():
    """Each test gets a clean in-memory job registry."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    webhook_mod._BATCH_JOBS.clear()
    yield
    webhook_mod._BATCH_JOBS.clear()


@pytest.fixture
def mock_upstream(monkeypatch):
    """Replace urllib.request.urlopen with a stub returning fixture bytes."""
    fixture_bytes = FIXTURE.read_bytes()

    class _MockResponse:
        def __init__(self, payload: bytes) -> None:
            self._buf = io.BytesIO(payload)

        def read(self) -> bytes:
            return self._buf.read()

        def __enter__(self) -> _MockResponse:
            return self

        def __exit__(self, *args: object) -> None:
            self._buf.close()

    state: dict[str, bytes] = {"payload": fixture_bytes}

    def _fake_urlopen(req, timeout=None):  # noqa: ARG001
        return _MockResponse(state["payload"])

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    return state


# ---------------------------------------------------------------------------
# 1. Endpoint accept-and-dispatch
# ---------------------------------------------------------------------------


def test_async_accepts_and_returns_job_id(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={
            "url": SAMPLE_URL,
            "jurisdiction_id": "visalia",
            "filename_hint": "visalia_agenda_test.pdf",
        },
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "accepted"
    assert body["url"] == SAMPLE_URL
    assert len(body["job_id"]) == 16  # secrets.token_hex(8)
    assert body["poll_url"] == f"/api/v1/webhook/status/{body['job_id']}"


def test_async_rejects_missing_token(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 401


def test_async_rejects_missing_url(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 400


def test_async_rejects_non_http_url(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": "file:///etc/passwd", "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 400


def test_async_rejects_missing_jurisdiction(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 2. Background worker — directly exercised (deterministic)
# ---------------------------------------------------------------------------


def test_worker_completes_happy_path(webhook_app, mock_upstream):
    """Drive the worker synchronously; assert final state shape."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    job_id = "test-job-happy"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=job_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="visalia_agenda_test.pdf",
    )

    state = webhook_mod._BATCH_JOBS[job_id]
    assert state["status"] == "completed"
    assert state["already_seen"] is False
    assert len(state["sha256"]) == 64
    assert state["filename"] == "visalia_agenda_test.pdf"
    assert state["result"]["status"] == "ok"
    assert state["result"]["tier"] == 1
    assert state["result"]["document"]["jurisdiction_id"] == "visalia"


def test_worker_marks_failed_on_upstream_error(webhook_app, monkeypatch):
    """urlopen raises → status flips to failed with an error message."""
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _raise(req, timeout=None):  # noqa: ARG001
        raise urllib.error.URLError("simulated upstream failure")

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    job_id = "test-job-fail"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=job_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )

    state = webhook_mod._BATCH_JOBS[job_id]
    assert state["status"] == "failed"
    assert "simulated upstream failure" in state["error"]


def test_worker_marks_failed_on_empty_body(webhook_app, mock_upstream):
    """Zero-byte upstream response → failed."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    mock_upstream["payload"] = b""

    job_id = "test-job-empty"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=job_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )

    state = webhook_mod._BATCH_JOBS[job_id]
    assert state["status"] == "failed"
    assert "empty body" in state["error"].lower()


def test_worker_short_circuits_on_dedup(webhook_app, mock_upstream):
    """Second run with same bytes flips to completed + already_seen=True."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    # First run primes the SeenHash table.
    first_id = "test-job-first"
    webhook_mod._BATCH_JOBS[first_id] = {
        "job_id": first_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=first_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )
    assert webhook_mod._BATCH_JOBS[first_id]["status"] == "completed"

    # Second run sees the hash and short-circuits before audit.
    second_id = "test-job-dedup"
    webhook_mod._BATCH_JOBS[second_id] = {
        "job_id": second_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=second_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )

    state = webhook_mod._BATCH_JOBS[second_id]
    assert state["status"] == "completed"
    assert state["already_seen"] is True
    assert state["result"]["already_seen"] is True
    # Dedup branch doesn't carry full audit payload.
    assert "tier" not in state["result"]


# ---------------------------------------------------------------------------
# 3. Status polling
# ---------------------------------------------------------------------------


def test_status_returns_404_for_unknown_job(client):
    resp = client.get(
        "/api/v1/webhook/status/nonexistent-job-id",
        headers={"X-ODIA-Webhook-Token": TOKEN},
    )
    assert resp.status_code == 404


def test_status_returns_state_for_seeded_job(client):
    """Status endpoint should surface scrape-job fields verbatim."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    job_id = "test-job-seeded"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "auditing",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
        "sha256": "a" * 64,
        "filename": "visalia_agenda_test.pdf",
    }

    resp = client.get(
        f"/api/v1/webhook/status/{job_id}",
        headers={"X-ODIA-Webhook-Token": TOKEN},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["type"] == "scrape"
    assert body["status"] == "auditing"
    assert body["url"] == SAMPLE_URL
    assert body["filename"] == "visalia_agenda_test.pdf"


# ---------------------------------------------------------------------------
# 4. End-to-end (real thread, bounded poll)
# ---------------------------------------------------------------------------


def test_endpoint_to_completion_via_real_thread(client, mock_upstream):
    """Full HTTP path: POST → 202 → poll until status=completed."""
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest-async",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={
            "url": SAMPLE_URL,
            "jurisdiction_id": "visalia",
            "filename_hint": "visalia_e2e.pdf",
        },
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # Poll up to ~10s; the fixture is tiny so the audit completes fast.
    deadline = time.monotonic() + 10.0
    final = None
    while time.monotonic() < deadline:
        poll = client.get(
            f"/api/v1/webhook/status/{job_id}",
            headers={"X-ODIA-Webhook-Token": TOKEN},
        )
        assert poll.status_code == 200
        state = poll.json()
        if state["status"] in ("completed", "failed"):
            final = state
            break
        time.sleep(0.1)

    assert final is not None, "scrape job did not finish in 10s"
    assert final["status"] == "completed", f"unexpected final state: {final}"
    assert final["result"]["status"] == "ok"
    assert final["filename"] == "visalia_e2e.pdf"


# ---------------------------------------------------------------------------
# 5. v3.0.4 — wider OSError catch + download throttle
# ---------------------------------------------------------------------------


def test_worker_marks_failed_on_remote_disconnected(webhook_app, monkeypatch):
    """v3.0.4 regression guard: http.client.RemoteDisconnected is a
    ConnectionResetError → OSError, NOT a urllib.error.URLError. v3.0.3's
    narrower catch let it escape and crash the worker thread. The widened
    OSError catch must now mark the job failed cleanly.
    """
    import http.client

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _raise(req, timeout=None):  # noqa: ARG001
        raise http.client.RemoteDisconnected(
            "Remote end closed connection without response"
        )

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    job_id = "test-job-remote-disconnected"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    # Must NOT raise — that would crash the daemon thread in production.
    webhook_mod._run_scrape_job_background(
        job_id=job_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )

    state = webhook_mod._BATCH_JOBS[job_id]
    assert state["status"] == "failed"
    assert "Remote end closed connection" in state["error"]


def test_worker_marks_failed_on_generic_oserror(webhook_app, monkeypatch):
    """Belt-and-braces: any other OSError (DNS failure, broken pipe,
    connection refused) also resolves to status=failed instead of
    propagating out of the worker.
    """
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _raise(req, timeout=None):  # noqa: ARG001
        raise OSError("simulated DNS resolution failure")

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    job_id = "test-job-generic-oserror"
    webhook_mod._BATCH_JOBS[job_id] = {
        "job_id": job_id,
        "type": "scrape",
        "status": "queued",
        "url": SAMPLE_URL,
        "jurisdiction_id": "visalia",
    }
    webhook_mod._run_scrape_job_background(
        job_id=job_id,
        url=SAMPLE_URL,
        jurisdiction_id="visalia",
        filename_hint="",
    )

    state = webhook_mod._BATCH_JOBS[job_id]
    assert state["status"] == "failed"
    assert "DNS resolution failure" in state["error"]


def test_download_semaphore_is_module_level_and_sized():
    """v3.0.4: the download throttle must exist at module scope (so all
    worker threads share it) and be sized at the documented concurrency.
    """
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    assert hasattr(webhook_mod, "_DOWNLOAD_SEMAPHORE")
    assert hasattr(webhook_mod, "_DOWNLOAD_CONCURRENCY")
    assert webhook_mod._DOWNLOAD_CONCURRENCY == 4
    # Semaphore's internal counter is _value; with no waiters it equals capacity.
    assert webhook_mod._DOWNLOAD_SEMAPHORE._value == 4
