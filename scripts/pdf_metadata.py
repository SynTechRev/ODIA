#!/usr/bin/env python3
"""
PDF Metadata Extractor - Extracts XMP and PDF metadata.

This module extracts metadata from PDF files including producer, creator,
dates, and scanning detection.

Author: GitHub Copilot Agent
Date: 2025-12-08
"""

import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))


def get_xmp_metadata(path: Path) -> dict:
    """
    Extract XMP metadata from PDF.

    Args:
        path: Path to PDF file

    Returns:
        Dictionary of XMP metadata
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        metadata = reader.metadata

        if metadata:
            return {
                "Producer": metadata.get("/Producer", ""),
                "Creator": metadata.get("/Creator", ""),
                "CreateDate": metadata.get("/CreationDate", ""),
                "ModDate": metadata.get("/ModDate", ""),
                "Title": metadata.get("/Title", ""),
                "Author": metadata.get("/Author", ""),
                "Subject": metadata.get("/Subject", ""),
            }
        return {}
    except Exception:
        return {}


def guess_scanned(xmp: dict) -> bool:
    """
    Guess if PDF is scanned based on metadata.

    Args:
        xmp: XMP metadata dictionary

    Returns:
        True if likely scanned, False otherwise
    """
    producer = xmp.get("Producer", "").lower()
    creator = xmp.get("Creator", "").lower()

    # Common scanning indicators
    scan_indicators = ["scanner", "scan", "xerox", "canon", "hp", "epson"]

    for indicator in scan_indicators:
        if indicator in producer or indicator in creator:
            return True

    return False


def extract_metadata(path: Path) -> dict:
    """
    Extract complete metadata from PDF.

    Args:
        path: Path to PDF file

    Returns:
        Dictionary of metadata
    """
    xmp = get_xmp_metadata(path)

    return {
        "path": str(path),
        "producer": xmp.get("Producer", ""),
        "creator": xmp.get("Creator", ""),
        "created": xmp.get("CreateDate", ""),
        "modified": xmp.get("ModDate", ""),
        "title": xmp.get("Title", ""),
        "author": xmp.get("Author", ""),
        "is_scanned": guess_scanned(xmp),
    }


def extract_all_metadata(corpus_entries: list[dict]) -> list[dict]:
    """
    Extract metadata from all PDFs in corpus entries.

    Args:
        corpus_entries: List of corpus entries with file information

    Returns:
        List of metadata dictionaries
    """
    results = []

    for entry in corpus_entries:
        corpus_id = entry.get("corpus_id", "")
        for file_info in entry.get("files", []):
            file_name = file_info.get("name", "")
            if file_name.lower().endswith(".pdf"):
                # Note: In actual implementation, would construct full path
                # For now, record that metadata extraction would occur
                results.append(
                    {
                        "corpus_id": corpus_id,
                        "file_name": file_name,
                        "file_hash": file_info.get("file_hash", ""),
                    }
                )

    return results


def main():
    """Main entry point for metadata extraction."""
    print("PDF Metadata Extractor module initialized")
    print("Use extract_metadata(path) to extract metadata from a PDF file")


if __name__ == "__main__":
    main()
