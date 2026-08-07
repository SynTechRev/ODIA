"""Tests for ingest.commercial — 12-step commercial document ingest pipeline."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from oraculus_di_auditor.db.models import (  # noqa: E402
    Base,
    CasiScore,
    CommercialDocument,
    ContraFinding,
)
from oraculus_di_auditor.entity.registry import Entity, EntityRegistry  # noqa: E402
from oraculus_di_auditor.ingest.commercial import (  # noqa: E402
    IngestionResult,
    ingest_commercial_document,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test_commercial.db")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)  # noqa: N806
    sess = SessionFactory()
    yield sess
    sess.close()
    engine.dispose()


@pytest.fixture()
def text_file(tmp_path) -> Path:
    """A minimal plain-text contract."""
    content = (
        "TERMS OF SERVICE\n\n"
        "By using this service you agree to binding arbitration. "
        "All disputes shall be resolved through AAA consumer rules. "
        "Class action waiver applies. We may collect and sell your data. "
        "We may modify these terms at any time without notice. "
        "Your continued use constitutes acceptance.\n"
    )
    p = tmp_path / "contract.txt"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def entity_registry_with_entity():
    """In-memory EntityRegistry pre-populated with one entity."""
    reg = EntityRegistry(db_session=None)
    entity = Entity.new(
        canonical_name="TestCorp Inc.", naics="5112", in_contra_corpus=True
    )
    reg.add_entity(entity)
    return reg, entity


# ---------------------------------------------------------------------------
# IngestionResult dataclass
# ---------------------------------------------------------------------------


class TestIngestionResult:
    def test_defaults(self):
        r = IngestionResult(
            document_hash="abc" * 21 + "a",
            entity_id="eid-1",
            entity_name="Corp",
            doc_type="tos",
            text_length=100,
            extraction_method="plaintext",
            l1_l10_findings=0,
            l11_l20_findings=3,
            total_findings=3,
            casi_aggregate=45,
            casi_band="Substantial Asymmetry",
            wayback_url=None,
            analytical_card_path=None,
        )
        assert r.skipped_duplicate is False
        assert r.warnings == []


# ---------------------------------------------------------------------------
# Happy-path: plain-text file, no detectors fire
# ---------------------------------------------------------------------------


class TestIngestCommercialDocument:
    def _run(self, text_file, db_session, entity_registry_with_entity, **kwargs):
        reg, entity = entity_registry_with_entity
        with (
            patch(
                "oraculus_di_auditor.ingest.commercial._run_legal_detectors",
                return_value=[],
            ),
            patch(
                "oraculus_di_auditor.ingest.commercial._run_contra_detectors",
                return_value=[],
            ),
        ):
            return ingest_commercial_document(
                source_path=text_file,
                entity_name="TestCorp Inc.",
                doc_type="tos",
                session=db_session,
                entity_registry=reg,
                fetch_wayback=False,
                **kwargs,
            )

    def test_returns_ingestion_result(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert isinstance(result, IngestionResult)

    def test_document_hash_is_sha256(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        expected = hashlib.sha256(text_file.read_bytes()).hexdigest()
        assert result.document_hash == expected

    def test_entity_resolved(self, text_file, db_session, entity_registry_with_entity):
        reg, entity = entity_registry_with_entity
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.entity_id == entity.entity_id

    def test_doc_type_preserved(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.doc_type == "tos"

    def test_extraction_method_is_plaintext(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.extraction_method == "plaintext"

    def test_text_length_positive(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.text_length > 0

    def test_not_duplicate(self, text_file, db_session, entity_registry_with_entity):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.skipped_duplicate is False

    def test_document_persisted_to_db(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        doc = db_session.get(CommercialDocument, result.document_hash)
        assert doc is not None
        assert doc.doc_type == "tos"

    def test_casi_score_persisted(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        score = db_session.get(CasiScore, result.document_hash)
        assert score is not None
        assert score.aggregate == result.casi_aggregate
        assert score.band == result.casi_band

    def test_no_contra_findings_when_detectors_return_empty(
        self, text_file, db_session, entity_registry_with_entity
    ):
        result = self._run(text_file, db_session, entity_registry_with_entity)
        assert result.l11_l20_findings == 0
        findings = (
            db_session.query(ContraFinding)
            .filter(ContraFinding.document_hash == result.document_hash)
            .all()
        )
        assert findings == []


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


class TestDuplicateDetection:
    def test_second_ingest_returns_skipped(
        self, text_file, db_session, entity_registry_with_entity
    ):
        reg, _ = entity_registry_with_entity

        def _run():
            with (
                patch(
                    "oraculus_di_auditor.ingest.commercial._run_legal_detectors",
                    return_value=[],
                ),
                patch(
                    "oraculus_di_auditor.ingest.commercial._run_contra_detectors",
                    return_value=[],
                ),
            ):
                return ingest_commercial_document(
                    source_path=text_file,
                    entity_name="TestCorp Inc.",
                    doc_type="tos",
                    session=db_session,
                    entity_registry=reg,
                    fetch_wayback=False,
                )

        r1 = _run()
        r2 = _run()
        assert not r1.skipped_duplicate
        assert r2.skipped_duplicate

    def test_duplicate_does_not_add_second_db_row(
        self, text_file, db_session, entity_registry_with_entity
    ):
        reg, _ = entity_registry_with_entity

        def _run():
            with (
                patch(
                    "oraculus_di_auditor.ingest.commercial._run_legal_detectors",
                    return_value=[],
                ),
                patch(
                    "oraculus_di_auditor.ingest.commercial._run_contra_detectors",
                    return_value=[],
                ),
            ):
                return ingest_commercial_document(
                    source_path=text_file,
                    entity_name="TestCorp Inc.",
                    doc_type="tos",
                    session=db_session,
                    entity_registry=reg,
                    fetch_wayback=False,
                )

        _run()
        _run()
        count = db_session.query(CommercialDocument).count()
        assert count == 1


# ---------------------------------------------------------------------------
# Source file not found
# ---------------------------------------------------------------------------


class TestSourceNotFound:
    def test_raises_value_error(self, tmp_path, db_session):
        reg = EntityRegistry(db_session=None)
        with pytest.raises(ValueError, match="not found"):
            ingest_commercial_document(
                source_path=tmp_path / "nonexistent.txt",
                entity_name="Corp",
                doc_type="tos",
                session=db_session,
                entity_registry=reg,
                fetch_wayback=False,
            )


# ---------------------------------------------------------------------------
# Entity unresolved — warning, not failure
# ---------------------------------------------------------------------------


class TestEntityUnresolved:
    def test_entity_auto_created_with_warning(self, text_file, db_session):
        """Unknown entity is auto-created so entity_id (NOT NULL FK) is satisfied."""
        reg = EntityRegistry(db_session=None)  # empty registry
        with (
            patch(
                "oraculus_di_auditor.ingest.commercial._run_legal_detectors",
                return_value=[],
            ),
            patch(
                "oraculus_di_auditor.ingest.commercial._run_contra_detectors",
                return_value=[],
            ),
        ):
            result = ingest_commercial_document(
                source_path=text_file,
                entity_name="Unknown Corp XYZ",
                doc_type="tos",
                session=db_session,
                entity_registry=reg,
                fetch_wayback=False,
            )
        assert result.entity_id is not None
        assert any("auto-created" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Effective date round-trips to DB
# ---------------------------------------------------------------------------


class TestEffectiveDatePersistence:
    def test_effective_date_stored(
        self, text_file, db_session, entity_registry_with_entity
    ):
        reg, _ = entity_registry_with_entity
        eff = datetime(2024, 1, 15, tzinfo=UTC)
        with (
            patch(
                "oraculus_di_auditor.ingest.commercial._run_legal_detectors",
                return_value=[],
            ),
            patch(
                "oraculus_di_auditor.ingest.commercial._run_contra_detectors",
                return_value=[],
            ),
        ):
            result = ingest_commercial_document(
                source_path=text_file,
                entity_name="TestCorp Inc.",
                doc_type="tos",
                session=db_session,
                entity_registry=reg,
                effective_date=eff,
                fetch_wayback=False,
            )
        doc = db_session.get(CommercialDocument, result.document_hash)
        assert doc.effective_date.year == 2024
        assert doc.effective_date.month == 1
        assert doc.effective_date.day == 15


# ---------------------------------------------------------------------------
# CLI integration: contra-ingest subcommand registration
# ---------------------------------------------------------------------------


class TestContraIngestCLI:
    def test_subcommand_registered(self):
        from oraculus_di_auditor.cli import _build_parser

        parser = _build_parser()
        # Verify the subparser exists and help doesn't raise
        help_text = parser.format_help()
        assert "contra-ingest" in help_text

    def test_missing_required_args_exits_nonzero(self):
        from oraculus_di_auditor.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main(["contra-ingest"])
        assert exc_info.value.code != 0
