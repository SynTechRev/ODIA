"""C.O.N.T.R.A. commercial document ingest pipeline (Phase G).

Public surface:
  from oraculus_di_auditor.ingest import ingest_commercial_document, IngestionResult
  from oraculus_di_auditor.ingest.wayback import find_capture, retrieve_prior_versions

Legacy compatibility (previously oraculus_di_auditor.ingest module):
  from oraculus_di_auditor.ingest import ingest_folder
"""

from ._document_ingest import ingest_folder, normalize_text_file, sha256_text
from .commercial import IngestionResult, ingest_commercial_document
from .wayback import find_capture, retrieve_prior_versions

__all__ = [
    "IngestionResult",
    "find_capture",
    "ingest_commercial_document",
    "ingest_folder",
    "normalize_text_file",
    "retrieve_prior_versions",
    "sha256_text",
]
