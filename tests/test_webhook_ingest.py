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


# ---------------------------------------------------------------------------
# 4. C5 prerequisite — Tier 1 result persists to Document + Analysis + Anomaly
# ---------------------------------------------------------------------------


def test_ingest_persists_document_analysis_anomaly_rows(client):
    """After a successful /ingest-and-analyze, the DB must have:
      - One Document row keyed on the sha256 (document_id)
      - One Analysis row linked to that document
      - N Anomaly rows linked to that Analysis (one per finding)

    RAIAService.synthesize() reads from these tables; without persistence
    the whole cross-jurisdiction synthesis pipeline is inert.
    """
    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": TOKEN},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert resp.status_code == 200
    sha = resp.json()["document"]["sha256"]
    expected_anomaly_count = resp.json()["findings"].get("count", 0)

    from oraculus_di_auditor.db.models import Analysis, Anomaly, Document
    from oraculus_di_auditor.db.session import get_db

    with get_db() as session:
        doc = session.query(Document).filter_by(document_id=sha).one()
        assert doc.jurisdiction == "woodlake"
        assert doc.title == "sample_audit_doc.txt"

        analyses = session.query(Analysis).filter_by(document_id=sha).all()
        assert len(analyses) == 1
        analysis = analyses[0]
        assert analysis.anomaly_count == expected_anomaly_count
        assert 0.0 <= analysis.scalar_score <= 1.0

        anomalies = session.query(Anomaly).filter_by(analysis_id=analysis.id).all()
        assert len(anomalies) == expected_anomaly_count
        # Each anomaly row must have a non-empty layer — detectors set it.
        for a in anomalies:
            assert a.layer
            assert a.severity in ("low", "medium", "high", "critical")


def test_persist_tier1_result_never_raises_on_db_failure(client, monkeypatch):
    """_persist_tier1_result is advisory — if the DB write fails for any
    reason, the helper logs a warning and returns. The webhook response
    must still be 200 with findings. This test confirms the 'never
    raises' contract directly on the helper, not through the route.
    """
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    # Monkeypatch get_db to raise when entered — simulates connection lost
    # mid-write. The helper's internal try/except must catch it.
    class _BrokenSession:
        def __enter__(self):
            raise RuntimeError("simulated DB connection lost")

        def __exit__(self, *a):
            return False

    def _broken_get_db():
        return _BrokenSession()

    monkeypatch.setattr("oraculus_di_auditor.db.session.get_db", _broken_get_db)

    # Invoking the helper with the broken session MUST NOT raise. If this
    # line raises, the "never raises" contract is broken.
    webhook_mod._persist_tier1_result(
        sha256="a" * 64,
        filename="test.txt",
        jurisdiction_id="woodlake",
        result={
            "findings": {"anomalies": [], "count": 0},
            "recursive_scalar_score": 1.0,
        },
    )
    # If we got here, the helper swallowed the DB error as intended.


def test_ingest_still_returns_200_when_persistence_fails(client, monkeypatch):
    """End-to-end cousin of the above: even with a broken persistence
    helper, the webhook endpoint returns 200 with findings (persistence
    is advisory, not blocking)."""
    from oraculus_di_auditor.interface.routes import webhook as webhook_mod

    # Replace the whole helper with a no-op — ensures the ROUTE does not
    # gate its response on the helper's output.
    monkeypatch.setattr(webhook_mod, "_persist_tier1_result", lambda **kw: None)

    with FIXTURE.open("rb") as f:
        resp = client.post(
            "/api/v1/webhook/ingest-and-analyze",
            headers={"X-ODIA-Webhook-Token": TOKEN},
            files={"file": ("sample_audit_doc.txt", f, "text/plain")},
            data={"jurisdiction_id": "woodlake"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
