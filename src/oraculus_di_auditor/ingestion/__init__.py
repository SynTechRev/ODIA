"""Ingestion modules for document processing.

This package provides tools for parsing and converting documents from various
formats (XML, HTML, PDF, TXT) into normalized text, including text extraction,
segmentation, and metadata generation (Phase 4 & Phase 7).
"""

from .engine import (
    compute_file_hash,
    compute_text_hash,
    extract_text_from_file,
    extract_text_from_html,
    extract_text_from_html_file,
    extract_text_from_pdf,
    ingest_document,
    ingest_text,
    segment_text,
)
from .xml_parser import extract_text_from_xml, parse_xml_to_text

__all__ = [
    # XML parsing (Phase 7)
    "parse_xml_to_text",
    "extract_text_from_xml",
    # Multi-format ingestion (Phase 4)
    "ingest_document",
    "ingest_text",
    "extract_text_from_pdf",
    "extract_text_from_html",
    "extract_text_from_html_file",
    "extract_text_from_file",
    "segment_text",
    "compute_file_hash",
    "compute_text_hash",
]
