"""Tests for the SeenHash dedup path in ingestion/engine.py (v2.7.3 D2).

The post-v2.7.2 audit surfaced two duplicate PDF pairs in an 11-document
corpus (Agenda (5)/Agenda (8) and Agenda (4)/Agenda (9) share SHA). The
webhook path already checks SeenHash; the general-path ingestion via
``ingest_document`` / ``ingest_text`` did not. This test file locks down
the dedup semantics for the general path so every caller — desktop app,
CLI, frontend upload — gets dedup for free.
"""

from __future__ import annotations

import importlib

import pytest

pytest.importorskip("sqlalchemy")


@pytest.fixture
def fresh_db(monkeypatch, tmp_path):
    """Fresh SQLite DB per test; reloads the session module so
    init_db() reads DATABASE_URL from the current environment."""
    db_path = tmp_path / "odia_ingest_dedup.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)
    db_session.init_db()
    return db_session


# ---------------------------------------------------------------------------
# ingest_text (no file needed) — covers the simplest case end-to-end
# ---------------------------------------------------------------------------


def test_ingest_text_first_call_marks_not_already_seen(fresh_db):
    from oraculus_di_auditor.ingestion.engine import ingest_text

    doc = ingest_text("Test document content — first call.")
    assert doc["metadata"]["already_seen"] is False
    assert doc["metadata"]["first_seen_at"] is None
    assert len(doc["metadata"]["hash"]) == 64


def test_ingest_text_second_call_marks_already_seen(fresh_db):
    from oraculus_di_auditor.ingestion.engine import ingest_text

    text = "Identical bytes — second call should see dedup."
    first = ingest_text(text)
    assert first["metadata"]["already_seen"] is False

    second = ingest_text(text)
    assert second["metadata"]["already_seen"] is True
    assert second["metadata"]["first_seen_at"] is not None
    # Hash stable across calls
    assert second["metadata"]["hash"] == first["metadata"]["hash"]


def test_ingest_text_force_reanalyze_bypasses_dedup(fresh_db):
    from oraculus_di_auditor.ingestion.engine import ingest_text

    text = "Force-reanalyze path — dedup must be skipped."
    first = ingest_text(text)
    assert first["metadata"]["already_seen"] is False

    second = ingest_text(text, force_reanalyze=True)
    # Dedup short-circuit bypassed — the caller asked for fresh work.
    assert second["metadata"]["already_seen"] is False


def test_ingest_text_records_jurisdiction_id(fresh_db):
    from oraculus_di_auditor.db import models as db_models
    from oraculus_di_auditor.db.session import get_db
    from oraculus_di_auditor.ingestion.engine import ingest_text

    doc = ingest_text(
        "Woodlake staff report — scope detector test.",
        jurisdiction_id="woodlake",
    )
    with get_db() as session:
        row = (
            session.query(db_models.SeenHash)
            .filter_by(sha256=doc["metadata"]["hash"])
            .one()
        )
        assert row.jurisdiction_id == "woodlake"
        assert row.document_id == doc["metadata"]["hash"]


# ---------------------------------------------------------------------------
# ingest_document (real file on disk)
# ---------------------------------------------------------------------------


def test_ingest_document_first_and_second_ingest(fresh_db, tmp_path):
    from oraculus_di_auditor.ingestion.engine import ingest_document

    # Two different files with the SAME bytes → SAME hash → dedup fires
    payload = "This is a small staff report fixture.\nLine two.\n"
    file_a = tmp_path / "agenda-5.txt"
    file_b = tmp_path / "agenda-8.txt"  # Different filename, same bytes
    file_a.write_text(payload, encoding="utf-8")
    file_b.write_text(payload, encoding="utf-8")

    doc_a = ingest_document(file_a, jurisdiction_id="lindsay")
    assert doc_a["metadata"]["already_seen"] is False

    doc_b = ingest_document(file_b, jurisdiction_id="lindsay")
    assert doc_b["metadata"]["already_seen"] is True
    assert doc_b["metadata"]["hash"] == doc_a["metadata"]["hash"]
    assert doc_b["metadata"]["first_seen_at"] is not None


def test_ingest_document_force_reanalyze_path(fresh_db, tmp_path):
    from oraculus_di_auditor.ingestion.engine import ingest_document

    payload = "Rerun requested — force_reanalyze path."
    path = tmp_path / "rerun.txt"
    path.write_text(payload, encoding="utf-8")

    first = ingest_document(path)
    assert first["metadata"]["already_seen"] is False

    # Force path — dedup short-circuit must be skipped even though the
    # hash is already in the table.
    second = ingest_document(path, force_reanalyze=True)
    assert second["metadata"]["already_seen"] is False


# ---------------------------------------------------------------------------
# Graceful degrade — DB unavailable
# ---------------------------------------------------------------------------


def test_check_seen_hash_returns_none_when_db_not_initialized(monkeypatch):
    """With no init_db() call and DATABASE_URL unset, the helper must
    return None (never-seen) rather than raising."""
    # Reload session to guarantee the global _SessionFactory is None.
    import importlib

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.ingestion.engine import check_seen_hash

    assert check_seen_hash("a" * 64) is None


def test_record_seen_hash_swallows_db_errors(monkeypatch):
    """record_seen_hash must not raise when the DB session blows up."""
    import importlib

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.ingestion.engine import record_seen_hash

    # No init_db — get_db() raises RuntimeError. record_seen_hash must
    # catch it and return None.
    record_seen_hash("b" * 64, document_id="b" * 64, jurisdiction_id="test")
    # No assertion beyond "did not raise" — that's the contract.


def test_ingest_text_still_works_without_db(monkeypatch):
    """Without an initialised DB, ingestion must still succeed and
    report ``already_seen=False`` (since nothing can be looked up)."""
    import importlib

    from oraculus_di_auditor.db import session as db_session

    importlib.reload(db_session)

    from oraculus_di_auditor.ingestion.engine import ingest_text

    doc = ingest_text("No DB — graceful path.")
    assert doc["text"]
    assert doc["metadata"]["already_seen"] is False
    assert doc["metadata"]["first_seen_at"] is None
