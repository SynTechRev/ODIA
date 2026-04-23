"""Tests for v2.7.1 webhook-support models (SeenHash + WebhookAuditLog).

Both tables are created by the same `init_db()` path as the rest of the
schema — no migration flow. These tests exercise insert + query so a
regression in column names or indexing surfaces immediately.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

# Skip the whole module if SQLAlchemy is unavailable — matches the existing
# db/ test pattern.
pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.exc import IntegrityError  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from oraculus_di_auditor.db.models import (  # noqa: E402
    Base,
    SeenHash,
    WebhookAuditLog,
)


@pytest.fixture
def session():
    """In-memory SQLite session seeded with the full ODIA schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# SeenHash
# ---------------------------------------------------------------------------


def test_seen_hash_insert_and_query(session):
    row = SeenHash(
        sha256="a" * 64,
        first_seen_at=datetime.now(UTC),
        document_id="doc-001",
        jurisdiction_id="woodlake",
    )
    session.add(row)
    session.commit()

    fetched = session.query(SeenHash).filter_by(sha256="a" * 64).one()
    assert fetched.document_id == "doc-001"
    assert fetched.jurisdiction_id == "woodlake"
    assert fetched.first_seen_at is not None


def test_seen_hash_duplicate_raises_integrity_error(session):
    session.add(SeenHash(sha256="b" * 64))
    session.commit()

    session.add(SeenHash(sha256="b" * 64))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_seen_hash_nullable_optional_fields(session):
    """document_id and jurisdiction_id are nullable — first webhook POST
    doesn't yet know the document_id."""
    session.add(SeenHash(sha256="c" * 64))
    session.commit()

    fetched = session.query(SeenHash).filter_by(sha256="c" * 64).one()
    assert fetched.document_id is None
    assert fetched.jurisdiction_id is None


# ---------------------------------------------------------------------------
# WebhookAuditLog
# ---------------------------------------------------------------------------


def test_webhook_audit_log_insert_and_query(session):
    session.add(
        WebhookAuditLog(
            endpoint="ingest-and-analyze",
            workflow_id="WF-001-Woodlake",
            execution_id="exec-42",
            status=200,
            source_ip="192.0.2.10",
        )
    )
    session.commit()

    rows = session.query(WebhookAuditLog).all()
    assert len(rows) == 1
    r = rows[0]
    assert r.endpoint == "ingest-and-analyze"
    assert r.workflow_id == "WF-001-Woodlake"
    assert r.execution_id == "exec-42"
    assert r.status == 200
    assert r.source_ip == "192.0.2.10"
    assert r.timestamp is not None


def test_webhook_audit_log_filter_by_workflow_id(session):
    # Seed two workflows
    for _ in range(3):
        session.add(
            WebhookAuditLog(
                endpoint="ingest-and-analyze", workflow_id="WF-001", status=200
            )
        )
    session.add(
        WebhookAuditLog(endpoint="batch-ingest", workflow_id="WF-002", status=202)
    )
    session.commit()

    wf001 = session.query(WebhookAuditLog).filter_by(workflow_id="WF-001").all()
    wf002 = session.query(WebhookAuditLog).filter_by(workflow_id="WF-002").all()
    assert len(wf001) == 3
    assert len(wf002) == 1
    assert wf002[0].endpoint == "batch-ingest"


def test_webhook_audit_log_nullable_fields(session):
    """workflow_id, execution_id, and source_ip are nullable — not every
    caller is an n8n workflow behind a proxy that sets X-Forwarded-For."""
    session.add(WebhookAuditLog(endpoint="health", status=200))
    session.commit()

    r = session.query(WebhookAuditLog).one()
    assert r.workflow_id is None
    assert r.execution_id is None
    assert r.source_ip is None
    assert r.status == 200
