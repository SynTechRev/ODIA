"""CRUD operations for Oraculus-DI-Auditor database.

Provides functions for creating, reading, updating, and deleting database records.
All operations are pure functions that accept a database session.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

try:
    from sqlalchemy.orm import Session

    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Session = Any  # type: ignore

from .models import Analysis, Anomaly, Document, Provenance, Section

# ============================================================================
# DOCUMENT CRUD
# ============================================================================


def create_document(
    db: Session,
    document_data: dict[str, Any],
    provenance_data: dict[str, Any] | None = None,
) -> Document:
    """Create a new document with optional provenance.

    Args:
        db: Database session
        document_data: Document fields (document_id, title, document_type, etc.)
        provenance_data: Optional provenance fields (source_path, hash, etc.)

    Returns:
        Created Document instance

    Example:
        with get_db() as db:
            doc = create_document(
                db,
                {
                    "document_id": "test-001",
                    "title": "Test Act",
                    "document_type": "act",
                },
                {
                    "source_path": "/data/test.txt",
                    "hash": "abc123",
                    "verified_on": datetime.now(UTC),
                }
            )
    """
    # Create document
    document = Document(
        document_id=document_data["document_id"],
        title=document_data.get("title", "Untitled"),
        document_type=document_data.get("document_type", "document"),
        jurisdiction=document_data.get("jurisdiction"),
        authority=document_data.get("authority"),
        version_date=document_data.get("version_date"),
        signatory=document_data.get("signatory"),
        metadata_json=json.dumps(document_data.get("metadata", {})),
    )

    db.add(document)
    db.flush()  # Get the ID without committing

    # Create provenance if provided
    if provenance_data:
        provenance = Provenance(
            document_id=document.document_id,
            source_path=provenance_data.get("source_path", "unknown"),
            hash=provenance_data["hash"],
            verified_on=provenance_data.get("verified_on", datetime.now(UTC)),
            file_size_bytes=provenance_data.get("file_size_bytes"),
            format=provenance_data.get("format"),
        )
        db.add(provenance)

    return document


def get_document_by_id(db: Session, document_id: str) -> Document | None:
    """Get document by document_id.

    Args:
        db: Database session
        document_id: Unique document identifier

    Returns:
        Document instance or None if not found
    """
    return db.query(Document).filter(Document.document_id == document_id).first()


def create_sections(
    db: Session, document_id: str, sections: list[dict[str, Any]]
) -> list[Section]:
    """Create sections for a document.

    Args:
        db: Database session
        document_id: Document identifier
        sections: List of section dicts with section_id, content, order_index

    Returns:
        List of created Section instances
    """
    section_objects = []
    for idx, section_data in enumerate(sections):
        section = Section(
            document_id=document_id,
            section_id=section_data.get("section_id", f"section-{idx}"),
            content=section_data["content"],
            order_index=section_data.get("order_index", idx),
        )
        db.add(section)
        section_objects.append(section)

    return section_objects


# ============================================================================
# ANALYSIS CRUD
# ============================================================================


def create_analysis(
    db: Session, analysis_data: dict[str, Any], anomalies: list[dict[str, Any]]
) -> Analysis:
    """Create analysis record with anomalies.

    Args:
        db: Database session
        analysis_data: Analysis fields (document_id, scalar_score, etc.)
        anomalies: List of anomaly dicts

    Returns:
        Created Analysis instance

    Example:
        with get_db() as db:
            analysis = create_analysis(
                db,
                {
                    "document_id": "test-001",
                    "scalar_score": 0.95,
                    "severity_score": 0.1,
                    "anomaly_count": 1,
                },
                [
                    {
                        "anomaly_id": "fiscal:amount-without-appropriation",
                        "issue": "Fiscal amount without appropriation",
                        "severity": "medium",
                        "layer": "fiscal",
                    }
                ]
            )
    """
    # Create analysis
    analysis = Analysis(
        document_id=analysis_data["document_id"],
        anomaly_count=len(anomalies),
        scalar_score=analysis_data.get("scalar_score", 0.0),
        severity_score=analysis_data.get("severity_score", 0.0),
        coherence_bonus=analysis_data.get("coherence_bonus", 0.0),
        engine_version=analysis_data.get("engine_version", "1.0.0"),
        summary=analysis_data.get("summary", ""),
        metadata_json=json.dumps(analysis_data.get("metadata", {})),
    )

    db.add(analysis)
    db.flush()  # Get the ID

    # Create anomalies
    for anomaly_data in anomalies:
        anomaly = Anomaly(
            analysis_id=analysis.id,
            anomaly_id=anomaly_data.get(
                "id", anomaly_data.get("anomaly_id", "unknown")
            ),
            issue=anomaly_data.get("issue", ""),
            severity=anomaly_data.get("severity", "medium"),
            layer=anomaly_data.get("layer", "unknown"),
            details_json=json.dumps(anomaly_data.get("details", {})),
        )
        db.add(anomaly)

    return analysis


def get_analysis_by_id(db: Session, analysis_id: int) -> Analysis | None:
    """Get analysis by ID.

    Args:
        db: Database session
        analysis_id: Analysis primary key

    Returns:
        Analysis instance or None if not found
    """
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_analyses_by_document(
    db: Session, document_id: str, limit: int = 10
) -> list[Analysis]:
    """Get recent analyses for a document.

    Args:
        db: Database session
        document_id: Document identifier
        limit: Maximum number of results

    Returns:
        List of Analysis instances, most recent first
    """
    return (
        db.query(Analysis)
        .filter(Analysis.document_id == document_id)
        .order_by(Analysis.analysis_timestamp.desc())
        .limit(limit)
        .all()
    )


def list_recent_analyses(db: Session, limit: int = 20) -> list[Analysis]:
    """List most recent analyses across all documents.

    Args:
        db: Database session
        limit: Maximum number of results

    Returns:
        List of Analysis instances, most recent first
    """
    return (
        db.query(Analysis)
        .order_by(Analysis.analysis_timestamp.desc())
        .limit(limit)
        .all()
    )


def get_anomalies_by_analysis(db: Session, analysis_id: int) -> list[Anomaly]:
    """Get all anomalies for an analysis.

    Args:
        db: Database session
        analysis_id: Analysis primary key

    Returns:
        List of Anomaly instances
    """
    return db.query(Anomaly).filter(Anomaly.analysis_id == analysis_id).all()


__all__ = [
    "create_document",
    "get_document_by_id",
    "create_sections",
    "create_analysis",
    "get_analysis_by_id",
    "get_analyses_by_document",
    "list_recent_analyses",
    "get_anomalies_by_analysis",
]
