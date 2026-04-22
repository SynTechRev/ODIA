"""Layer 2 NER + relational extraction with automatic backend selection."""

from odia_ai.extraction.extractor import (
    ExtractionOutput,
    ExtractionService,
    FinetunedExtractionBackend,
    PatternExtractionBackend,
    RAGExtractionBackend,
)

__all__ = [
    "ExtractionOutput",
    "ExtractionService",
    "PatternExtractionBackend",
    "RAGExtractionBackend",
    "FinetunedExtractionBackend",
]
