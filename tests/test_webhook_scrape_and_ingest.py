"""Integration tests for POST /api/v1/webhook/scrape-and-ingest (v3.0.2).

The endpoint downloads a URL server-side (Python urllib, friendlier TLS
fingerprint than n8n's Node.js HTTP node) and runs the Tier 1 audit on
the response body. urllib.request.urlopen is monkeypatched with a stub
that returns fixture bytes so tests never hit the network.

Coverage:
  - Happy path: valid {url, jurisdiction_id} → 200 with audit payload
  - Auth: missing / wrong token → 401
  - Validation: missing url → 400, non-http(s) url → 400, missing jurisdiction → 400
  - Dedup: same upstream bytes twice → second is `already_seen=true`
  - Upstream failure: urlopen raises → 502 with descriptive detail
"""

from __future__ import annotations

import io
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
    """Fresh app + initialised SQLite DB for each test, isolated env."""
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


@pytest.fixture
def mock_upstream(monkeypatch):
    """Replace urllib.request.urlopen with a stub returning fixture bytes.

    The stub mimics urlopen's context-manager + .read() interface so the
    handler can use it identically to the real call. Test-supplied bytes
    can be customised by setting ``mock_upstream.payload`` before the
    request fires.
    """
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

    def _fake_urlopen(req, timeout=None):  # noqa: ARG001 — match real signature
        return _MockResponse(state["payload"])

    monkeypatch.setattr(
        "urllib.request.urlopen",
        _fake_urlopen,
    )
    return state


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------


def test_scrape_happy_path(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={
            "url": SAMPLE_URL,
            "jurisdiction_id": "visalia",
            "filename_hint": "visalia_agenda_test.pdf",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["status"] == "ok"
    assert body["already_seen"] is False
    assert body["url"] == SAMPLE_URL
    assert body["tier"] == 1

    doc = body["document"]
    assert doc["filename"] == "visalia_agenda_test.pdf"
    assert doc["jurisdiction_id"] == "visalia"
    assert len(doc["sha256"]) == 64
    assert doc["byte_length"] == FIXTURE.stat().st_size

    findings = body["findings"]
    assert "count" in findings
    assert findings["count"] >= 0


def test_scrape_filename_hint_optional(client, mock_upstream):
    """Without filename_hint, derive from URL tail; ensure .pdf suffix."""
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # URL tail is "_05062026-821" — handler appends .pdf because no extension
    assert body["document"]["filename"].endswith(".pdf")
    assert "05062026-821" in body["document"]["filename"]


# ---------------------------------------------------------------------------
# 2. Auth
# ---------------------------------------------------------------------------


def test_scrape_rejects_missing_token(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 401


def test_scrape_rejects_wrong_token(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": "wrong"},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. Validation
# ---------------------------------------------------------------------------


def test_scrape_rejects_missing_url(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 400
    assert "url" in resp.json()["detail"].lower()


def test_scrape_rejects_non_http_url(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": "file:///etc/passwd", "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 400


def test_scrape_rejects_missing_jurisdiction(client, mock_upstream):
    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL},
    )
    assert resp.status_code == 400
    assert "jurisdiction" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Dedup
# ---------------------------------------------------------------------------


def test_scrape_dedup_on_same_bytes(client, mock_upstream):
    """Same URL → same bytes → second request returns already_seen."""
    first = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert first.status_code == 200
    assert first.json()["already_seen"] is False
    sha = first.json()["document"]["sha256"]

    second = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert second.status_code == 200
    body = second.json()
    assert body["already_seen"] is True
    assert body["sha256"] == sha


# ---------------------------------------------------------------------------
# 5. Upstream failures
# ---------------------------------------------------------------------------


def test_scrape_502_on_urlopen_failure(client, monkeypatch):
    """When urlopen raises (network down, 404, etc.), return 502 with detail."""
    import urllib.error

    def _raise(req, timeout=None):  # noqa: ARG001
        raise urllib.error.URLError("simulated upstream failure")

    monkeypatch.setattr("urllib.request.urlopen", _raise)

    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 502
    assert "simulated upstream failure" in resp.json()["detail"]


def test_scrape_502_on_empty_body(client, mock_upstream):
    """Upstream returning zero bytes is treated as failure (502)."""
    mock_upstream["payload"] = b""

    resp = client.post(
        "/api/v1/webhook/scrape-and-ingest",
        headers={"X-ODIA-Webhook-Token": TOKEN},
        json={"url": SAMPLE_URL, "jurisdiction_id": "visalia"},
    )
    assert resp.status_code == 502
    assert "empty body" in resp.json()["detail"].lower()
