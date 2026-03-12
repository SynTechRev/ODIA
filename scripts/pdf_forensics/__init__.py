#!/usr/bin/env python3
"""PDF Forensics Layer - Deep Packet Metadata Miner (DPMM) v1.0.

This module provides PDF-level forensic metadata analysis for the
11-year legislative corpus (2014-2025).
"""

from scripts.pdf_forensics.pdf_metadata_miner import (
    DPMM_VERSION,
    detect_ocr_presence,
    detect_producer_anomalies,
    detect_scanned_vs_digital,
    detect_temporal_anomalies,
    detect_xmp_anomalies,
    extract_pdf_metadata,
    generate_forensic_report,
    normalize_pdf_date,
    parse_xmp_metadata,
    run_pdf_forensics,
    score_forensic_integrity,
)

__all__ = [
    "DPMM_VERSION",
    "extract_pdf_metadata",
    "normalize_pdf_date",
    "parse_xmp_metadata",
    "detect_temporal_anomalies",
    "detect_producer_anomalies",
    "detect_xmp_anomalies",
    "detect_scanned_vs_digital",
    "detect_ocr_presence",
    "score_forensic_integrity",
    "generate_forensic_report",
    "run_pdf_forensics",
]
