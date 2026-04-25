"""Tests for the Dashboard summary endpoint (v2.7.6 X1).

The Dashboard home's Analysis Summary card now backs onto
``/api/v1/dashboard/summary`` rather than a Zustand store. These
tests pin the response shape, the DB-empty path, and the aggregation
arithmetic so the card stays in lockstep with persisted rows.
"""

from __future__ import annotations

import importlib
from datetime import UTC, datetime

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def client(monkeypatch, tmp_path):
    """Fresh per-test SQLite + reloaded session module so init_db()
    picks up the monkeypatched DATABASE_URL."""
    db_path = tmp_path / "dashboard_summary.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.interface.api import create_app

    app = create_app()
    return TestClient(app)


def test_dashboard_summary_empty_db(client):
    """With no rows the endpoint must return zeroed counters but
    ``available=True`` (DB is initialised, just empty)."""
    resp = client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    assert body["analyses"] == 0
    assert body["documents"] == 0
    assert body["findings"] == 0
    assert body["by_severity"] == {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    assert body["avg_severity_score"] == 0.0
    assert body["last_audit_at"] is None


def test_dashboard_summary_aggregates_persisted_rows(client):
    """Insert a Document + Analysis + 4 Anomaly rows of varying
    severities and confirm the endpoint sums them correctly."""
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as session:
        doc = db_models.Document(
            document_id="doc-X1-test",
            title="X1 fixture",
            document_type="contract",
            jurisdiction="example_city_a",
        )
        session.add(doc)
        session.flush()

        analysis = db_models.Analysis(
            document_id="doc-X1-test",
            anomaly_count=4,
            scalar_score=0.8,
            severity_score=0.65,
            engine_version="2.7.6",
            analysis_timestamp=datetime(2026, 4, 25, 12, 0, 0, tzinfo=UTC),
        )
        session.add(analysis)
        session.flush()

        for sev in ("critical", "high", "medium", "low"):
            session.add(
                db_models.Anomaly(
                    analysis_id=analysis.id,
                    anomaly_id=f"X1:test-{sev}",
                    issue=f"X1 fixture {sev}",
                    severity=sev,
                    layer="fiscal",
                )
            )
        session.commit()

    resp = client.get("/api/v1/dashboard/summary")
    body = resp.json()
    assert body["available"] is True
    assert body["documents"] == 1
    assert body["analyses"] == 1
    assert body["findings"] == 4
    assert body["by_severity"] == {
        "critical": 1,
        "high": 1,
        "medium": 1,
        "low": 1,
    }
    assert body["avg_severity_score"] == pytest.approx(0.65, rel=1e-3)
    assert body["last_audit_at"] is not None
    assert body["last_audit_at"].startswith("2026-04-25T12:00:00")


def test_dashboard_summary_severity_grouping(client):
    """Multiple anomalies of the same severity must aggregate, and
    unknown severity values must be silently dropped (defensive
    parsing — webhook ingest can write anything into that column)."""
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db

    with get_db() as session:
        doc = db_models.Document(
            document_id="doc-X1-grouping",
            title="grouping fixture",
            document_type="resolution",
            jurisdiction="example_city_b",
        )
        session.add(doc)
        analysis = db_models.Analysis(
            document_id="doc-X1-grouping",
            anomaly_count=5,
            scalar_score=0.5,
            severity_score=0.4,
            engine_version="2.7.6",
        )
        session.add(analysis)
        session.flush()

        # 3 critical, 2 high, 1 unknown ("info" — not in the legend)
        severities = ["critical", "critical", "critical", "high", "high", "info"]
        for sev in severities:
            session.add(
                db_models.Anomaly(
                    analysis_id=analysis.id,
                    anomaly_id=f"X1:grouping-{sev}",
                    issue="grouping fixture",
                    severity=sev,
                    layer="surveillance",
                )
            )
        session.commit()

    body = client.get("/api/v1/dashboard/summary").json()
    assert body["by_severity"]["critical"] == 3
    assert body["by_severity"]["high"] == 2
    assert body["by_severity"]["medium"] == 0
    assert body["by_severity"]["low"] == 0
    # Unknown severities count toward `findings` but not the legend buckets.
    assert body["findings"] == 6
