"""Alert-to-document back-reference extraction from MAS corpus."""

from odia_ai.backref.extractor import (
    ExtractedAlert,
    compute_corpus_stats,
    extract_alerts_from_file,
    extract_corpus,
    write_jsonl,
)

__all__ = [
    "ExtractedAlert",
    "extract_alerts_from_file",
    "extract_corpus",
    "compute_corpus_stats",
    "write_jsonl",
]
