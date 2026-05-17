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
    """_fetch_url raises → worker marks status=failed.

    v3.1.0: patches _fetch_url directly (not urllib.request.urlopen)
    because v3.1.0 wraps urllib in a two-tier fetcher that falls
    through to curl_cffi on tier-1 failure. Tests that want a
    deterministic "fetcher failed" outcome patch the helper that the
    worker actually calls.
    """
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _raise(url, timeout=120):  # noqa: ARG001
        raise OSError("simulated upstream failure")

    monkeypatch.setattr(webhook_mod, "_fetch_url", _raise)

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
    """v3.0.4 regression guard, v3.1.0-updated patch layer.

    Verifies the worker handles fetcher failures gracefully (no thread
    crash). v3.0.4 caught OSError on a single-tier urllib failure;
    v3.1.0 has a two-tier fetcher, so this test now drives the failure
    at the _fetch_url boundary (where both tiers have already failed
    and OSError surfaces to the caller). RemoteDisconnected is a
    ConnectionResetError → OSError; the original v3.0.4 failure mode.
    """
    import http.client

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _raise(url, timeout=120):  # noqa: ARG001
        raise http.client.RemoteDisconnected(
            "Remote end closed connection without response"
        )

    monkeypatch.setattr(webhook_mod, "_fetch_url", _raise)

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

    def _raise(url, timeout=120):  # noqa: ARG001
        raise OSError("simulated DNS resolution failure")

    monkeypatch.setattr(webhook_mod, "_fetch_url", _raise)

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


# ---------------------------------------------------------------------------
# 6. v3.1.0 — two-tier fetcher (urllib tier-1 → curl_cffi tier-2)
# ---------------------------------------------------------------------------


class _MockCurlResponse:
    """Minimal stand-in for curl_cffi.requests.Response."""

    def __init__(self, content: bytes, status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code
        self.ok = 200 <= status_code < 400


def _patch_curl_cffi(monkeypatch, *, get_callable):
    """Inject a fake curl_cffi.requests.get into sys.modules.

    Lets tests exercise the v3.1.0 tier-2 fallback path deterministically
    without requiring the real curl_cffi binary or making network calls.
    """
    import sys
    import types

    fake_requests = types.SimpleNamespace(get=get_callable)
    fake_curl_cffi = types.ModuleType("curl_cffi")
    fake_curl_cffi.requests = fake_requests  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "curl_cffi", fake_curl_cffi)
    monkeypatch.setitem(sys.modules, "curl_cffi.requests", fake_requests)


def test_fetch_url_tier1_happy_returns_bytes(webhook_app, mock_upstream):
    """Tier 1 (urllib) success: short-circuits before tier 2 is reached."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    fixture_bytes = FIXTURE.read_bytes()
    body = webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert body == fixture_bytes


def test_fetch_url_tier1_403_falls_through_to_tier2_success(
    webhook_app, monkeypatch
):
    """v3.1.0 core behaviour: HTTPError(403) on tier 1 triggers tier 2.

    Tier 2 returns the bytes that tier 1 was blocked from getting.
    Mirrors the live Tulare/AkamaiGHost failure mode from v3.0.4 bring-up.
    """
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _tier1_blocked(req, timeout=None):  # noqa: ARG001
        raise urllib.error.HTTPError(
            url=SAMPLE_URL, code=403, msg="Forbidden", hdrs=None, fp=None
        )

    monkeypatch.setattr("urllib.request.urlopen", _tier1_blocked)

    tier2_payload = b"%PDF-1.4 (tier-2 chrome-impersonated bytes)"

    def _tier2_ok(url, headers=None, impersonate=None, timeout=None):  # noqa: ARG001
        assert impersonate == "chrome131", (
            "v3.1.0 must impersonate Chrome 131 in tier 2"
        )
        return _MockCurlResponse(tier2_payload, status_code=200)

    _patch_curl_cffi(monkeypatch, get_callable=_tier2_ok)

    body = webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert body == tier2_payload


def test_fetch_url_tier1_429_falls_through_to_tier2(webhook_app, monkeypatch):
    """429 Too Many Requests should also trigger tier-2 fallback."""
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _tier1_throttled(req, timeout=None):  # noqa: ARG001
        raise urllib.error.HTTPError(
            url=SAMPLE_URL,
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr("urllib.request.urlopen", _tier1_throttled)
    _patch_curl_cffi(
        monkeypatch,
        get_callable=lambda url, **_kw: _MockCurlResponse(b"tier-2 saved us"),
    )

    body = webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert body == b"tier-2 saved us"


def test_fetch_url_tier1_404_does_not_fall_through(webhook_app, monkeypatch):
    """Real upstream errors (404 Not Found, 401 Unauthorized) must NOT
    trigger tier-2 fallback — they're legitimate responses, not bot blocks.
    Falling through wastes a curl_cffi request on a URL that doesn't exist.
    """
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    tier2_called = {"count": 0}

    def _tier1_404(req, timeout=None):  # noqa: ARG001
        raise urllib.error.HTTPError(
            url=SAMPLE_URL, code=404, msg="Not Found", hdrs=None, fp=None
        )

    def _tier2_should_not_be_called(url, **_kw):  # noqa: ARG001
        tier2_called["count"] += 1
        return _MockCurlResponse(b"should not be returned")

    monkeypatch.setattr("urllib.request.urlopen", _tier1_404)
    _patch_curl_cffi(monkeypatch, get_callable=_tier2_should_not_be_called)

    with pytest.raises(urllib.error.HTTPError) as exc:
        webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert exc.value.code == 404
    assert tier2_called["count"] == 0, (
        "tier-2 must not be invoked on non-fallback HTTP codes"
    )


def test_fetch_url_tier1_oserror_falls_through_to_tier2(webhook_app, monkeypatch):
    """Connection-class OSError on tier 1 (TLS reset, RemoteDisconnected,
    DNS failure) triggers tier-2 fallback. curl_cffi's Chrome
    fingerprint may succeed where Python's OpenSSL did not.
    """
    import http.client

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _tier1_reset(req, timeout=None):  # noqa: ARG001
        raise http.client.RemoteDisconnected("server closed mid-handshake")

    monkeypatch.setattr("urllib.request.urlopen", _tier1_reset)
    _patch_curl_cffi(
        monkeypatch,
        get_callable=lambda url, **_kw: _MockCurlResponse(b"chrome got through"),
    )

    body = webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert body == b"chrome got through"


def test_fetch_url_both_tiers_fail_raises_oserror_with_context(
    webhook_app, monkeypatch
):
    """Both tiers failing → OSError whose message names both failures
    so the operator can diagnose without grepping logs."""
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _tier1_blocked(req, timeout=None):  # noqa: ARG001
        raise urllib.error.HTTPError(
            url=SAMPLE_URL, code=403, msg="Forbidden", hdrs=None, fp=None
        )

    def _tier2_also_blocked(url, **_kw):  # noqa: ARG001
        return _MockCurlResponse(b"", status_code=403)

    monkeypatch.setattr("urllib.request.urlopen", _tier1_blocked)
    _patch_curl_cffi(monkeypatch, get_callable=_tier2_also_blocked)

    with pytest.raises(OSError) as exc:
        webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    msg = str(exc.value)
    assert "tier-2" in msg
    assert "403" in msg


def test_fetch_url_no_curl_cffi_reraises_tier1_error(webhook_app, monkeypatch):
    """If curl_cffi is uninstalled / unavailable, the original tier-1
    failure must be re-raised so the operator sees the real underlying
    problem, not a misleading "tier-2 module missing" trail."""
    import sys
    import urllib.error

    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    def _tier1_blocked(req, timeout=None):  # noqa: ARG001
        raise urllib.error.HTTPError(
            url=SAMPLE_URL, code=403, msg="Forbidden", hdrs=None, fp=None
        )

    monkeypatch.setattr("urllib.request.urlopen", _tier1_blocked)
    # Force the lazy `from curl_cffi import requests` inside _fetch_url
    # to raise ImportError.
    monkeypatch.setitem(sys.modules, "curl_cffi", None)

    with pytest.raises(urllib.error.HTTPError) as exc:
        webhook_mod._fetch_url(SAMPLE_URL, timeout=10)
    assert exc.value.code == 403
