"""Oraculus DI Auditor - Legal Document Ingestion and Anomaly Auditing.

Author: Marcus A. Sanchez
Date: 2025-11-12

Public package exports are defined here for clarity.
"""

from .aei19 import Phase19Service
from .aer20 import Phase20Service
from .normalize import chunk_text
from .normalize import normalize_document as normalize_text
from .rgk18 import Phase18Service

__version__ = "0.1.0"
__all__ = [
    "chunk_text",
    "normalize_text",
    "Phase18Service",
    "Phase19Service",
    "Phase20Service",
]
