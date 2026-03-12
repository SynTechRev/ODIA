"""Oraculus DI Auditor - Ingestion Module.

Provides public exports for legislative ingestion utilities.
"""

from .legislative_loader import load_legislation
from .legislative_loader import normalize_document as normalize_legislation

__all__ = ["load_legislation", "normalize_legislation"]
