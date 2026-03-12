"""Database package for Oraculus-DI-Auditor.

Provides SQLAlchemy models, session management, and CRUD operations for
persistent storage of documents, analyses, and anomalies.

Phase 4 database integration layer.
"""

from .crud import (
    create_analysis,
    create_document,
    create_sections,
    get_analyses_by_document,
    get_analysis_by_id,
    get_anomalies_by_analysis,
    get_document_by_id,
    list_recent_analyses,
)
from .models import Analysis, Anomaly, Base, Document, Provenance, Reference, Section
from .session import get_db, init_db

__all__ = [
    # Models
    "Base",
    "Document",
    "Provenance",
    "Section",
    "Reference",
    "Analysis",
    "Anomaly",
    # Session
    "init_db",
    "get_db",
    # CRUD
    "create_document",
    "get_document_by_id",
    "create_sections",
    "create_analysis",
    "get_analysis_by_id",
    "get_analyses_by_document",
    "get_anomalies_by_analysis",
    "list_recent_analyses",
]
