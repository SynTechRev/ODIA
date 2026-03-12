"""Tests for database adapters (Phase 4).

Tests the database models, session management, and CRUD operations.
"""

from __future__ import annotations

import pytest

# Skip all tests if SQLAlchemy is not installed
try:
    from oraculus_di_auditor.db import (
        create_analysis,
        create_document,
        create_sections,
        get_analyses_by_document,
        get_analysis_by_id,
        get_anomalies_by_analysis,
        get_db,
        get_document_by_id,
        init_db,
        list_recent_analyses,
    )

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not SQLALCHEMY_AVAILABLE, reason="SQLAlchemy not installed"
)


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    if not SQLALCHEMY_AVAILABLE:
        pytest.skip("SQLAlchemy not installed")

    # Initialize with in-memory database
    init_db("sqlite:///:memory:")

    # Yield the get_db context manager
    yield get_db

    # No cleanup needed for in-memory database


def test_init_db(test_db):
    """Test database initialization."""
    # If we got here, initialization succeeded
    assert test_db is not None


def test_create_document(test_db):
    """Test creating a document."""
    with test_db() as db:
        doc_data = {
            "document_id": "test-001",
            "title": "Test Document",
            "document_type": "act",
            "jurisdiction": "federal",
        }

        doc = create_document(db, doc_data)

        assert doc.document_id == "test-001"
        assert doc.title == "Test Document"
        assert doc.document_type == "act"
        assert doc.jurisdiction == "federal"


def test_create_document_with_provenance(test_db):
    """Test creating a document with provenance."""
    from datetime import UTC, datetime

    with test_db() as db:
        doc_data = {
            "document_id": "test-002",
            "title": "Test Document with Provenance",
            "document_type": "regulation",
        }

        prov_data = {
            "source_path": "/data/test.txt",
            "hash": "abc123def456",
            "verified_on": datetime.now(UTC),
            "file_size_bytes": 12345,
            "format": "txt",
        }

        doc = create_document(db, doc_data, prov_data)
        db.flush()  # Ensure changes are written

        # Check document
        assert doc.document_id == "test-002"

    # Retrieve in new session to check provenance was saved
    with test_db() as db:
        doc = get_document_by_id(db, "test-002")
        assert doc.provenance is not None
        assert doc.provenance.hash == "abc123def456"
        assert doc.provenance.source_path == "/data/test.txt"
        assert doc.provenance.format == "txt"


def test_get_document_by_id(test_db):
    """Test retrieving a document by ID."""
    with test_db() as db:
        # Create document
        doc_data = {
            "document_id": "test-003",
            "title": "Retrievable Document",
            "document_type": "statute",
        }
        create_document(db, doc_data)

    # Retrieve in new session
    with test_db() as db:
        doc = get_document_by_id(db, "test-003")

        assert doc is not None
        assert doc.document_id == "test-003"
        assert doc.title == "Retrievable Document"


def test_get_document_by_id_not_found(test_db):
    """Test retrieving a non-existent document."""
    with test_db() as db:
        doc = get_document_by_id(db, "nonexistent")
        assert doc is None


def test_create_sections(test_db):
    """Test creating sections for a document."""
    with test_db() as db:
        # Create document first
        doc_data = {
            "document_id": "test-004",
            "title": "Document with Sections",
            "document_type": "act",
        }
        create_document(db, doc_data)

        # Create sections
        sections_data = [
            {"section_id": "1", "content": "Section 1 content", "order_index": 0},
            {"section_id": "2", "content": "Section 2 content", "order_index": 1},
            {"section_id": "3", "content": "Section 3 content", "order_index": 2},
        ]

        sections = create_sections(db, "test-004", sections_data)

        assert len(sections) == 3
        assert sections[0].section_id == "1"
        assert sections[1].section_id == "2"
        assert sections[2].section_id == "3"


def test_create_analysis(test_db):
    """Test creating an analysis with anomalies."""
    with test_db() as db:
        # Create document first
        doc_data = {
            "document_id": "test-005",
            "title": "Analyzed Document",
            "document_type": "regulation",
        }
        create_document(db, doc_data)

        # Create analysis
        analysis_data = {
            "document_id": "test-005",
            "scalar_score": 0.85,
            "severity_score": 0.15,
            "coherence_bonus": 0.05,
            "engine_version": "1.0.0",
            "summary": "Analysis detected 2 anomalies",
        }

        anomalies_data = [
            {
                "anomaly_id": "fiscal:missing-provenance",
                "issue": "Missing provenance hash",
                "severity": "high",
                "layer": "fiscal",
            },
            {
                "anomaly_id": "constitutional:broad-delegation",
                "issue": "Broad delegation detected",
                "severity": "medium",
                "layer": "constitutional",
            },
        ]

        analysis = create_analysis(db, analysis_data, anomalies_data)
        analysis_id = analysis.id

        assert analysis.document_id == "test-005"
        assert analysis.scalar_score == 0.85
        assert analysis.severity_score == 0.15
        assert analysis.anomaly_count == 2

    # Check anomalies in new session
    with test_db() as db:
        analysis = get_analysis_by_id(db, analysis_id)
        assert len(analysis.anomalies) == 2


def test_get_analysis_by_id(test_db):
    """Test retrieving an analysis by ID."""
    with test_db() as db:
        # Create document and analysis
        doc_data = {"document_id": "test-006", "title": "Test", "document_type": "act"}
        create_document(db, doc_data)

        analysis_data = {
            "document_id": "test-006",
            "scalar_score": 0.9,
            "severity_score": 0.1,
        }
        analysis = create_analysis(db, analysis_data, [])
        analysis_id = analysis.id

    # Retrieve in new session
    with test_db() as db:
        retrieved = get_analysis_by_id(db, analysis_id)

        assert retrieved is not None
        assert retrieved.id == analysis_id
        assert retrieved.document_id == "test-006"


def test_get_analyses_by_document(test_db):
    """Test retrieving analyses for a document."""
    with test_db() as db:
        # Create document
        doc_data = {"document_id": "test-007", "title": "Test", "document_type": "act"}
        create_document(db, doc_data)

        # Create multiple analyses
        for i in range(3):
            analysis_data = {
                "document_id": "test-007",
                "scalar_score": 0.9 - (i * 0.1),
                "severity_score": 0.1 + (i * 0.1),
            }
            create_analysis(db, analysis_data, [])

    # Retrieve analyses
    with test_db() as db:
        analyses = get_analyses_by_document(db, "test-007")

        assert len(analyses) == 3
        # Should be ordered by timestamp (most recent first)
        # Most recent should be the last one created (0.7 score)
        assert analyses[0].scalar_score == 0.7
        assert analyses[2].scalar_score == 0.9


def test_list_recent_analyses(test_db):
    """Test listing recent analyses."""
    with test_db() as db:
        # Create multiple documents and analyses
        for i in range(5):
            doc_data = {
                "document_id": f"test-00{i + 8}",
                "title": f"Test {i}",
                "document_type": "act",
            }
            create_document(db, doc_data)

            analysis_data = {
                "document_id": f"test-00{i + 8}",
                "scalar_score": 0.8,
                "severity_score": 0.2,
            }
            create_analysis(db, analysis_data, [])

    # List recent analyses
    with test_db() as db:
        analyses = list_recent_analyses(db, limit=3)

        assert len(analyses) == 3


def test_get_anomalies_by_analysis(test_db):
    """Test retrieving anomalies for an analysis."""
    with test_db() as db:
        # Create document
        doc_data = {
            "document_id": "test-013",
            "title": "Test",
            "document_type": "act",
        }
        create_document(db, doc_data)

        # Create analysis with anomalies
        analysis_data = {
            "document_id": "test-013",
            "scalar_score": 0.7,
            "severity_score": 0.3,
        }
        anomalies_data = [
            {
                "anomaly_id": "fiscal:test-1",
                "issue": "Test issue 1",
                "severity": "low",
                "layer": "fiscal",
            },
            {
                "anomaly_id": "fiscal:test-2",
                "issue": "Test issue 2",
                "severity": "high",
                "layer": "fiscal",
            },
        ]
        analysis = create_analysis(db, analysis_data, anomalies_data)
        analysis_id = analysis.id

    # Retrieve anomalies in new session
    with test_db() as db:
        anomalies = get_anomalies_by_analysis(db, analysis_id)

        assert len(anomalies) == 2
        assert anomalies[0].severity in ["low", "high"]
        assert anomalies[1].severity in ["low", "high"]


def test_models_repr(test_db):
    """Test model __repr__ methods."""
    with test_db() as db:
        # Test Document repr
        doc_data = {
            "document_id": "test-014",
            "title": "Representation Test",
            "document_type": "act",
        }
        doc = create_document(db, doc_data)
        assert "test-014" in repr(doc)
        assert "Document" in repr(doc)

        # Test Analysis repr
        analysis_data = {
            "document_id": "test-014",
            "scalar_score": 0.95,
            "severity_score": 0.05,
        }
        analysis = create_analysis(db, analysis_data, [])
        assert "Analysis" in repr(analysis)
        assert "0.95" in repr(analysis)


def test_document_relationships(test_db):
    """Test that document relationships are properly established."""
    with test_db() as db:
        # Create document with provenance
        doc_data = {
            "document_id": "test-015",
            "title": "Relationship Test",
            "document_type": "act",
        }
        prov_data = {
            "source_path": "/test",
            "hash": "xyz789",
        }
        create_document(db, doc_data, prov_data)

        # Create sections
        sections_data = [{"section_id": "1", "content": "Content"}]
        create_sections(db, "test-015", sections_data)

        # Create analysis
        analysis_data = {
            "document_id": "test-015",
            "scalar_score": 0.9,
            "severity_score": 0.1,
        }
        create_analysis(db, analysis_data, [])

    # Check relationships
    with test_db() as db:
        doc = get_document_by_id(db, "test-015")

        assert doc.provenance is not None
        assert len(doc.sections) == 1
        assert len(doc.analyses) == 1
        assert doc.sections[0].document_id == "test-015"
        assert doc.analyses[0].document_id == "test-015"
