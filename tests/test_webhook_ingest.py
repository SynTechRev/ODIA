"""Integration tests for POST /api/v1/webhook/ingest-and-analyze.

Three paths from handoff §3 Track A/A5:
  1. Valid token + file + jurisdiction → 200 with `document.sha256` and
     `findings.count >= 0`.
  2. Invalid / missing token → 401.
  3. Same bytes twice → second response has `already_seen=true`.

Fixture: tests/fixtures/sample_audit_doc.txt — a small staff-report style
text file that exercises the surveillance / scope / admin detectors
(Axon / sole-source / amendment / blank metadata fields) without
requiring pypdf or the OCR stack to be installed under pytest.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402

TOKEN = "a-test-token-for-pytest"
FIXTURE = Path(__file__).parent / "fixtures" / "sample_audit_doc.txt"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def webhook_app(monkeypatch, tmp_path):
    """Fresh app + initialised SQLite DB for each test.

    Each test gets its own temp database so SeenHash state doesn't leak
    across tests (dedup test 3 depends on starting from an empty table).
    """
    monkeypatch.setenv("ODIA_WEBHOOK_TOKEN", TOKEN)

    # Point the DB at a fresh file per test; init_db reads DATABASE_URL
    # at call time.
    db_path = tmp_path / "odia_test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    # Re-init session module so DATABASE_URL env is picked up.
    import importlib

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return app


@pytest.fixture
def client(webhook_app):
    return TestClient(webhook_app)


# ---------------------------------------------------------------------------
# 1. Happy path — valid token, valid file, valid jurisdiction
# ---------------------------------------------------------------------------


def test_ingest_happy_path(client):
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": TOKEN},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Contract required by WF-001
    assert body["status"] == "ok"
    assert body["already_seen"] is False
    assert body["tier"] == 1

    # Document block
    doc = body["document"]
    assert doc["filename"] == "sample_audit_doc.txt"
    assert doc["jurisdiction_id"] == "woodlake"
    assert len(doc["sha256"]) == 64
    assert doc["byte_length"] == FIXTURE.stat().st_size

    # Findings block — analyze_document returns dict with count/score/anomalies.
    findings = body["findings"]
    assert "count" in findings
    assert findings["count"] >= 0
    assert "anomalies" in findings

    # Scalar score in [0, 1]
    assert 0.0 <= body["recursive_scalar_score"] <= 1.0


# ---------------------------------------------------------------------------
# 2. Auth — missing / wrong token
# ---------------------------------------------------------------------------


def test_ingest_rejects_missing_token(client):
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert resp.status_code == 401


def test_ingest_rejects_wrong_token(client):
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": "wrong-token"},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 3. Dedup — same bytes twice
# ---------------------------------------------------------------------------


def test_ingest_dedup_on_second_post(client):
    """The first POST records sha256 in SeenHash; the second short-circuits.

    This validates the full dedup loop (read + write) end-to-end. WF-001's
    retry semantics depend on this: a 200 with `already_seen=true` signals
    'not an error, we already have this'."""
    # First call — fresh bytes
    with FIXTURE.open("rb") as f:
        first = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": TOKEN},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["already_seen"] is False
    sha = first_body["document"]["sha256"]

    # Second call — identical bytes
    with FIXTURE.open("rb") as f:
        second = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": TOKEN},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["already_seen"] is True
    assert second_body["sha256"] == sha
    # Dedup short-circuit does not include findings — just the pointer
    assert "findings" not in second_body
