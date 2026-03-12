#!/usr/bin/env python3
"""Deep Packet Metadata Miner (DPMM) v1.0 - PDF-level Forensic Metadata Analysis.

This module provides deep metadata extraction and forensic analysis for PDF documents
in the 2014-2025 legislative corpus. It detects temporal anomalies, producer
inconsistencies, XMP metadata issues, and origin patterns.

Author: GitHub Copilot Agent
Date: 2025-12-06
"""

import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(_script_dir.parent / "src"))
sys.path.insert(0, str(_script_dir.parent))

try:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
except ImportError:
    PdfReader = None
    PdfReadError = Exception

from scripts.corpus_manager import HIST_FILES  # noqa: E402

# Constants
DPMM_VERSION = "1.0"
DPMM_SCHEMA_VERSION = "1.0"
CORPUS_ROOT = Path("oraculus/corpus")

# PDF Date format pattern: D:YYYYMMDDHHmmSS+HH'mm' or variants
PDF_DATE_PATTERN = re.compile(
    r"D:(\d{4})(\d{2})(\d{2})(\d{2})?(\d{2})?(\d{2})?" r"(?:([+-])(\d{2})'?(\d{2})?'?)?"
)

# Producer software patterns with release years
PRODUCER_RELEASE_YEARS: dict[str, int] = {
    "Adobe Acrobat Pro DC": 2015,
    "Adobe Acrobat Pro 2017": 2017,
    "Adobe Acrobat Pro 2020": 2020,
    "Adobe Acrobat Reader DC": 2015,
    "Adobe PDF Library 15": 2015,
    "Adobe PDF Library 16": 2016,
    "Adobe PDF Library 17": 2017,
    "Adobe PDF Library 18": 2018,
    "Adobe PDF Library 19": 2019,
    "Adobe PDF Library 21": 2021,
    "Microsoft Word 2010": 2010,
    "Microsoft Word 2013": 2013,
    "Microsoft Word 2016": 2016,
    "Microsoft Word 2019": 2019,
    "Microsoft Word 2021": 2021,
    "Microsoft Word for Microsoft 365": 2019,
    "Microsoft® Word 2010": 2010,
    "Microsoft® Word 2013": 2013,
    "Microsoft® Word 2016": 2016,
    "Microsoft® Word 2019": 2019,
    "Apple Quartz PDFContext": 2007,
    "Mac OS X": 2001,
    "macOS Version": 2016,
    "LibreOffice": 2011,
    "OpenOffice": 2002,
    "FPDF": 2004,
    "tcpdf": 2006,
    "iText": 2000,
    "PDFsharp": 2005,
    "Foxit PDF SDK": 2010,
    "Foxit PhantomPDF": 2009,
    "Nitro Pro": 2005,
    "Prince": 2003,
    "wkhtmltopdf": 2008,
    "Chrome": 2008,
    "Firefox": 2004,
    "Ghostscript": 1988,
    "Xerox": 1990,
    "Canon": 1990,
    "Ricoh": 1990,
    "HP": 1990,
    "Konica Minolta": 1990,
    "ABBYY": 1989,
    "OmniPage": 1995,
    "Nuance": 2005,
    "Tesseract": 2006,
}

# Vendor-linked software patterns
VENDOR_SOFTWARE_PATTERNS: dict[str, list[str]] = {
    "Microsoft": ["microsoft", "word", "office", "excel", "powerpoint"],
    "Adobe": ["adobe", "acrobat", "photoshop", "indesign", "illustrator"],
    "Apple": ["apple", "quartz", "mac os", "macos", "preview"],
    "Google": ["chrome", "google", "docs"],
    "Mozilla": ["firefox", "mozilla"],
    "Scanner Vendors": ["xerox", "canon", "ricoh", "hp", "konica", "brother", "epson"],
    "OCR Software": ["abbyy", "omnipage", "nuance", "tesseract", "readiris"],
}

# XMP namespace patterns
XMP_NAMESPACES = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "pdf": "http://ns.adobe.com/pdf/1.3/",
    "xmpMM": "http://ns.adobe.com/xap/1.0/mm/",
    "pdfaid": "http://www.aiim.org/pdfa/ns/id/",
}

# OCR detection patterns
OCR_PATTERNS = [
    r"ocr",
    r"optical.?character.?recognition",
    r"scanned",
    r"abbyy",
    r"omnipage",
    r"tesseract",
    r"readiris",
    r"finereader",
]

# Scanned PDF indicators
SCANNED_INDICATORS = [
    "image",
    "scan",
    "tiff",
    "jpeg",
    "ccitt",
    "dct",
    "flate",
    "jbig2",
]


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format with Z suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_year_range(year_range: str) -> tuple[int, int]:
    """Parse a year range string (e.g., '2014-2025') into start and end years."""
    if "-" in year_range:
        parts = year_range.split("-")
        return int(parts[0]), int(parts[1])
    else:
        year = int(year_range)
        return year, year


def filter_corpora_by_years(start_year: int, end_year: int) -> dict[str, str]:
    """Filter HIST_FILES to only include entries within the year range."""
    filtered = {}
    for hist_id, meeting_date in HIST_FILES.items():
        year = int(meeting_date[:4])
        if start_year <= year <= end_year:
            filtered[hist_id] = meeting_date
    return filtered


def normalize_pdf_date(pdf_date: str | None) -> datetime | None:
    """Normalize a PDF date string to a datetime object.

    PDF dates are typically in format: D:YYYYMMDDHHmmSS+HH'mm'
    Examples:
        - D:20141208153000Z
        - D:20140812
        - D:20141208153000-08'00'

    Returns:
        Parsed datetime object or None if parsing fails
    """
    if not pdf_date:
        return None

    pdf_date_str = str(pdf_date).strip()

    # Handle standard PDF date format
    match = PDF_DATE_PATTERN.match(pdf_date_str)
    if match:
        year = int(match.group(1))
        month = int(match.group(2)) if match.group(2) else 1
        day = int(match.group(3)) if match.group(3) else 1
        hour = int(match.group(4)) if match.group(4) else 0
        minute = int(match.group(5)) if match.group(5) else 0
        second = int(match.group(6)) if match.group(6) else 0

        try:
            return datetime(year, month, day, hour, minute, second, tzinfo=UTC)
        except ValueError:
            return None

    # Try ISO format fallback
    try:
        return datetime.fromisoformat(pdf_date_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Try common date formats
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y"]:
        try:
            return datetime.strptime(pdf_date_str, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue

    return None


def compute_file_hashes(file_path: Path) -> dict[str, str]:
    """Compute MD5 and SHA256 hashes for a file.

    Returns:
        Dictionary with 'md5' and 'sha256' keys
    """
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)

        return {
            "md5": md5_hash.hexdigest(),
            "sha256": sha256_hash.hexdigest(),
        }
    except OSError:
        return {"md5": "", "sha256": ""}


def parse_xmp_metadata(xmp_data: bytes | str | None) -> dict[str, Any]:
    """Parse XMP metadata block from PDF.

    XMP (Extensible Metadata Platform) is XML-based metadata embedded in PDFs.

    Returns:
        Dictionary with parsed XMP fields
    """
    if not xmp_data:
        return {"present": False, "raw": None, "parsed": {}}

    xmp_str = (
        xmp_data.decode("utf-8", errors="ignore")
        if isinstance(xmp_data, bytes)
        else str(xmp_data)
    )

    result: dict[str, Any] = {
        "present": True,
        "raw_length": len(xmp_str),
        "parsed": {},
        "namespaces_found": [],
        "packet_count": 0,
        "malformed": False,
        "truncated": False,
    }

    # Count XMP packets
    result["packet_count"] = xmp_str.count("<?xpacket begin")

    # Check for proper XMP structure
    if "<?xpacket begin" in xmp_str and "<?xpacket end" not in xmp_str:
        result["truncated"] = True
        result["malformed"] = True

    # Check for namespace declarations
    for ns_name, ns_uri in XMP_NAMESPACES.items():
        if ns_uri in xmp_str or f"xmlns:{ns_name}" in xmp_str:
            result["namespaces_found"].append(ns_name)

    # Extract common XMP fields using simple regex
    xmp_field_patterns = {
        "CreateDate": r"<xmp:CreateDate>([^<]+)</xmp:CreateDate>",
        "ModifyDate": r"<xmp:ModifyDate>([^<]+)</xmp:ModifyDate>",
        "CreatorTool": r"<xmp:CreatorTool>([^<]+)</xmp:CreatorTool>",
        "Producer": r"<pdf:Producer>([^<]+)</pdf:Producer>",
        "title": r"<dc:title[^>]*>.*?<rdf:li[^>]*>([^<]+)</rdf:li>",
        "creator": r"<dc:creator[^>]*>.*?<rdf:li[^>]*>([^<]+)</rdf:li>",
        "pdfa_part": r"<pdfaid:part>([^<]+)</pdfaid:part>",
        "pdfa_conformance": r"<pdfaid:conformance>([^<]+)</pdfaid:conformance>",
    }

    for field_name, pattern in xmp_field_patterns.items():
        match = re.search(pattern, xmp_str, re.IGNORECASE | re.DOTALL)
        if match:
            result["parsed"][field_name] = match.group(1).strip()

    # Detect PDF/A conformance
    if "pdfaid" in result["namespaces_found"]:
        part = result["parsed"].get("pdfa_part", "")
        conf = result["parsed"].get("pdfa_conformance", "")
        if part:
            result["pdfa_conformance"] = f"PDF/A-{part}{conf}".lower()

    return result


def extract_pdf_metadata(pdf_path: Path) -> dict[str, Any]:
    """Extract comprehensive metadata from a PDF file.

    Extracts:
    - PDF trailer metadata
    - Info dictionary (/Producer, /Creator, /Author, /ModDate, /CreationDate)
    - XMP metadata block
    - PDF/A conformance flags
    - Page count and structure info
    - File hashes

    Returns:
        Dictionary with all extracted metadata
    """
    metadata: dict[str, Any] = {
        "file_path": str(pdf_path),
        "file_name": pdf_path.name,
        "file_size": 0,
        "extraction_success": False,
        "extraction_error": None,
        "info_dict": {},
        "xmp": {},
        "structure": {},
        "hashes": {},
        "normalized": {},
    }

    # Get file size and hashes
    try:
        metadata["file_size"] = pdf_path.stat().st_size
        metadata["hashes"] = compute_file_hashes(pdf_path)
    except OSError as e:
        metadata["extraction_error"] = f"File access error: {e}"
        return metadata

    # Check if pypdf is available
    if PdfReader is None:
        metadata["extraction_error"] = "pypdf library not available"
        return metadata

    try:
        reader = PdfReader(str(pdf_path))

        # Extract Info dictionary
        if reader.metadata:
            info = reader.metadata
            metadata["info_dict"] = {
                "producer": getattr(info, "producer", None),
                "creator": getattr(info, "creator", None),
                "author": getattr(info, "author", None),
                "title": getattr(info, "title", None),
                "subject": getattr(info, "subject", None),
                "creation_date": getattr(info, "creation_date", None),
                "modification_date": getattr(info, "modification_date", None),
            }

            # Convert datetime objects to strings for serialization
            for key in ["creation_date", "modification_date"]:
                val = metadata["info_dict"].get(key)
                if val is not None:
                    if hasattr(val, "isoformat"):
                        metadata["info_dict"][key] = val.isoformat()
                    else:
                        metadata["info_dict"][key] = str(val)

        # Extract XMP metadata
        try:
            xmp_data = reader.xmp_metadata
            if xmp_data:
                # Use xmp_metadata attribute if available
                if hasattr(xmp_data, "dc_creator"):
                    metadata["xmp"]["parsed"] = {
                        "dc_creator": xmp_data.dc_creator,
                        "dc_title": getattr(xmp_data, "dc_title", None),
                        "xmp_create_date": getattr(xmp_data, "xmp_create_date", None),
                        "xmp_modify_date": getattr(xmp_data, "xmp_modify_date", None),
                        "xmp_creator_tool": getattr(xmp_data, "xmp_creator_tool", None),
                        "pdf_producer": getattr(xmp_data, "pdf_producer", None),
                    }
                    metadata["xmp"]["present"] = True
                else:
                    # Fall back to raw parsing
                    raw_xmp = str(xmp_data) if xmp_data else None
                    metadata["xmp"] = parse_xmp_metadata(raw_xmp)
            else:
                metadata["xmp"] = {"present": False}
        except Exception:
            metadata["xmp"] = {
                "present": False,
                "extraction_error": "XMP extraction failed",
            }

        # Extract structure info
        metadata["structure"] = {
            "page_count": len(reader.pages),
            "is_encrypted": reader.is_encrypted,
            "pdf_version": reader.pdf_header if hasattr(reader, "pdf_header") else None,
        }

        # Normalize dates
        creation_str = metadata["info_dict"].get("creation_date")
        modification_str = metadata["info_dict"].get("modification_date")

        creation_dt = normalize_pdf_date(creation_str)
        modification_dt = normalize_pdf_date(modification_str)

        metadata["normalized"] = {
            "creation_date": creation_dt.isoformat() if creation_dt else None,
            "modification_date": (
                modification_dt.isoformat() if modification_dt else None
            ),
            "creation_year": creation_dt.year if creation_dt else None,
            "modification_year": modification_dt.year if modification_dt else None,
        }

        metadata["extraction_success"] = True

    except PdfReadError as e:
        metadata["extraction_error"] = f"PDF read error: {e}"
    except Exception as e:
        metadata["extraction_error"] = f"Unexpected error: {e}"

    return metadata


def detect_scanned_vs_digital(
    metadata: dict[str, Any], pdf_path: Path | None = None
) -> dict[str, Any]:
    """Detect whether a PDF is scanned (image-based) or digitally created.

    Indicators of scanned PDFs:
    - Producer mentions scanner vendors
    - Low text-to-image ratio
    - Specific compression types (CCITT, JBIG2)
    - OCR software in producer/creator

    Returns:
        Classification result with confidence
    """
    result: dict[str, Any] = {
        "classification": "unknown",
        "confidence": 0.0,
        "indicators": [],
    }

    producer = str(metadata.get("info_dict", {}).get("producer", "")).lower()
    creator = str(metadata.get("info_dict", {}).get("creator", "")).lower()
    combined = f"{producer} {creator}"

    scanned_score = 0.0
    digital_score = 0.0

    # Check for scanner vendor patterns
    for indicator in SCANNED_INDICATORS:
        if indicator in combined:
            scanned_score += 0.15
            result["indicators"].append(f"scanned_pattern:{indicator}")

    # Check for OCR patterns
    for pattern in OCR_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            scanned_score += 0.2
            result["indicators"].append(f"ocr_pattern:{pattern}")

    # Check for digital creation software
    digital_software = [
        "word",
        "acrobat",
        "indesign",
        "illustrator",
        "chrome",
        "firefox",
    ]
    for software in digital_software:
        if software in combined:
            digital_score += 0.2
            result["indicators"].append(f"digital_software:{software}")

    # Normalize scores
    total = scanned_score + digital_score
    if total > 0:
        scanned_confidence = scanned_score / (total + 0.5)
        digital_confidence = digital_score / (total + 0.5)
    else:
        scanned_confidence = 0.0
        digital_confidence = 0.0

    if scanned_confidence > digital_confidence:
        result["classification"] = "scanned"
        result["confidence"] = min(scanned_confidence, 1.0)
    elif digital_confidence > scanned_confidence:
        result["classification"] = "digital"
        result["confidence"] = min(digital_confidence, 1.0)
    else:
        result["classification"] = "unknown"
        result["confidence"] = 0.0

    return result


def detect_ocr_presence(metadata: dict[str, Any]) -> dict[str, Any]:
    """Detect if OCR was applied to the PDF.

    Returns:
        Detection result with indicators
    """
    result: dict[str, Any] = {
        "ocr_detected": False,
        "confidence": 0.0,
        "indicators": [],
    }

    producer = str(metadata.get("info_dict", {}).get("producer", "")).lower()
    creator = str(metadata.get("info_dict", {}).get("creator", "")).lower()
    combined = f"{producer} {creator}"

    # Check for OCR patterns
    for pattern in OCR_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            result["ocr_detected"] = True
            result["confidence"] = min(result["confidence"] + 0.3, 1.0)
            result["indicators"].append(pattern)

    # Check XMP for OCR indicators
    xmp = metadata.get("xmp", {})
    if xmp.get("present"):
        xmp_parsed = xmp.get("parsed", {})
        for val in xmp_parsed.values():
            val_lower = str(val).lower() if val else ""
            for pattern in OCR_PATTERNS:
                if re.search(pattern, val_lower, re.IGNORECASE):
                    result["ocr_detected"] = True
                    result["confidence"] = min(result["confidence"] + 0.2, 1.0)
                    result["indicators"].append(f"xmp:{pattern}")

    return result


def detect_temporal_anomalies(
    metadata: dict[str, Any], meeting_date: str | None = None
) -> list[dict[str, Any]]:
    """Detect temporal anomalies in PDF metadata.

    Detects:
    - CreationDate > ModificationDate
    - ModDate > meeting date
    - Producer inconsistent with historical software release timeline
    - Future-dated documents
    - Mismatched timestamp formats

    Returns:
        List of detected temporal anomalies
    """
    anomalies = []

    normalized = metadata.get("normalized", {})
    creation_str = normalized.get("creation_date")
    modification_str = normalized.get("modification_date")

    creation_dt = datetime.fromisoformat(creation_str) if creation_str else None
    modification_dt = (
        datetime.fromisoformat(modification_str) if modification_str else None
    )

    now = datetime.now(UTC)

    # Check 1: Creation date after modification date
    if creation_dt and modification_dt and creation_dt > modification_dt:
        anomalies.append(
            {
                "type": "temporal_anomaly",
                "subtype": "creation_after_modification",
                "severity": "medium",
                "creation_date": creation_str,
                "modification_date": modification_str,
                "details": (
                    f"Creation date ({creation_str}) is after "
                    f"modification date ({modification_str})"
                ),
            }
        )

    # Check 2: Modification date after meeting date
    if modification_dt and meeting_date:
        try:
            meeting_dt = datetime.fromisoformat(meeting_date).replace(tzinfo=UTC)
            # Allow 30 days for post-meeting processing
            if modification_dt > meeting_dt.replace(year=meeting_dt.year + 1):
                years_later = modification_dt.year - meeting_dt.year
                anomalies.append(
                    {
                        "type": "temporal_anomaly",
                        "subtype": "modification_after_meeting",
                        "severity": "high" if years_later > 2 else "medium",
                        "modification_date": modification_str,
                        "meeting_date": meeting_date,
                        "years_later": years_later,
                        "details": (
                            f"Document modified {years_later} year(s) "
                            f"after meeting date"
                        ),
                    }
                )
        except ValueError:
            pass

    # Check 3: Future-dated documents
    if creation_dt and creation_dt > now:
        anomalies.append(
            {
                "type": "temporal_anomaly",
                "subtype": "future_dated",
                "severity": "high",
                "creation_date": creation_str,
                "details": f"Document has future creation date: {creation_str}",
            }
        )

    if modification_dt and modification_dt > now:
        anomalies.append(
            {
                "type": "temporal_anomaly",
                "subtype": "future_dated",
                "severity": "high",
                "modification_date": modification_str,
                "details": f"Document has future modification date: {modification_str}",
            }
        )

    # Check 4: Producer version vs document year mismatch
    producer = metadata.get("info_dict", {}).get("producer")
    creation_year = normalized.get("creation_year")

    if producer and creation_year:
        producer_anomaly = _check_producer_timeline(producer, creation_year)
        if producer_anomaly:
            anomalies.append(producer_anomaly)

    return anomalies


def _check_producer_timeline(
    producer: str, document_year: int
) -> dict[str, Any] | None:
    """Check if producer software release year is inconsistent with document year."""
    producer_lower = producer.lower()

    for software_pattern, release_year in PRODUCER_RELEASE_YEARS.items():
        if software_pattern.lower() in producer_lower:
            if release_year > document_year:
                return {
                    "type": "temporal_anomaly",
                    "subtype": "producer_timeline_mismatch",
                    "severity": "high",
                    "producer": producer,
                    "producer_release_year": release_year,
                    "document_year": document_year,
                    "details": (
                        f"Producer '{producer}' (released {release_year}) used on "
                        f"document dated {document_year}"
                    ),
                }

    return None


def detect_producer_anomalies(
    metadata: dict[str, Any], expected_platform: str | None = None
) -> list[dict[str, Any]]:
    """Detect producer/creator forensic anomalies.

    Detects:
    - Platform mismatches (e.g., Apple software on Windows agency)
    - Vendor-linked software patterns
    - Unexpected producer changes

    Returns:
        List of detected producer anomalies
    """
    anomalies = []

    producer = metadata.get("info_dict", {}).get("producer") or ""
    creator = metadata.get("info_dict", {}).get("creator") or ""

    # Check for platform mismatch
    if expected_platform:
        detected_platform = _detect_platform(producer, creator)
        if detected_platform and detected_platform != expected_platform:
            anomalies.append(
                {
                    "type": "producer_anomaly",
                    "subtype": "platform_mismatch",
                    "severity": "medium",
                    "producer": producer,
                    "creator": creator,
                    "expected_platform": expected_platform,
                    "detected_platform": detected_platform,
                    "details": f"Expected {expected_platform}, found {detected_platform}",
                }
            )

    # Check for vendor-linked software
    for vendor, patterns in VENDOR_SOFTWARE_PATTERNS.items():
        combined = f"{producer} {creator}".lower()
        for pattern in patterns:
            if pattern in combined:
                anomalies.append(
                    {
                        "type": "producer_anomaly",
                        "subtype": "vendor_software_detected",
                        "severity": "low",
                        "vendor": vendor,
                        "producer": producer,
                        "creator": creator,
                        "pattern_matched": pattern,
                        "details": f"Vendor-linked software detected: {vendor}",
                    }
                )
                break

    return anomalies


def _detect_platform(producer: str, creator: str) -> str | None:
    """Detect the platform (Windows/Mac/Linux) from producer/creator strings."""
    combined = f"{producer} {creator}".lower()

    if any(p in combined for p in ["mac os", "macos", "quartz", "apple", "preview"]):
        return "macOS"
    if any(p in combined for p in ["windows", "microsoft", "word"]):
        return "Windows"
    if any(p in combined for p in ["linux", "libreoffice", "openoffice"]):
        return "Linux"

    return None


def detect_xmp_anomalies(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect XMP metadata block anomalies.

    Detects:
    - Missing XMP block
    - Malformed or truncated XMP
    - Multiple XMP packets (version stacking)
    - Regenerated metadata after OCR

    Returns:
        List of detected XMP anomalies
    """
    anomalies = []

    xmp = metadata.get("xmp", {})

    # Check for missing XMP
    if not xmp.get("present", False):
        anomalies.append(
            {
                "type": "xmp_anomaly",
                "subtype": "missing_xmp",
                "severity": "low",
                "details": "PDF has no XMP metadata block",
            }
        )
        return anomalies

    # Check for malformed XMP
    if xmp.get("malformed"):
        anomalies.append(
            {
                "type": "xmp_anomaly",
                "subtype": "malformed_xmp",
                "severity": "medium",
                "details": "XMP metadata block is malformed",
            }
        )

    # Check for truncated XMP
    if xmp.get("truncated"):
        anomalies.append(
            {
                "type": "xmp_anomaly",
                "subtype": "truncated_xmp",
                "severity": "medium",
                "details": "XMP metadata block is truncated (missing end packet)",
            }
        )

    # Check for multiple XMP packets (version stacking)
    packet_count = xmp.get("packet_count", 0)
    if packet_count > 1:
        anomalies.append(
            {
                "type": "xmp_anomaly",
                "subtype": "multiple_xmp_packets",
                "severity": "medium",
                "packet_count": packet_count,
                "details": (
                    f"Multiple XMP packets detected ({packet_count}), "
                    f"may indicate version stacking"
                ),
            }
        )

    # Check for OCR regeneration in XMP
    xmp_parsed = xmp.get("parsed", {})
    for field, value in xmp_parsed.items():
        if value and any(
            re.search(pattern, str(value), re.IGNORECASE) for pattern in OCR_PATTERNS
        ):
            anomalies.append(
                {
                    "type": "xmp_anomaly",
                    "subtype": "ocr_regenerated",
                    "severity": "low",
                    "field": field,
                    "value": str(value)[:100],
                    "details": f"XMP field '{field}' indicates OCR regeneration",
                }
            )

    return anomalies


def detect_retroactive_edit_indicators(
    metadata: dict[str, Any], meeting_date: str | None = None
) -> list[dict[str, Any]]:
    """Detect possible retroactive editing indicators.

    Detects:
    - Re-scanning of previously digital documents
    - Rewrite with different software
    - Metadata resets
    - Timestamp drift patterns

    Returns:
        List of detected retroactive edit indicators
    """
    anomalies = []

    producer = metadata.get("info_dict", {}).get("producer") or ""
    creator = metadata.get("info_dict", {}).get("creator") or ""
    normalized = metadata.get("normalized", {})

    creation_year = normalized.get("creation_year")
    modification_year = normalized.get("modification_year")

    # Check for significant year gap between creation and modification
    if creation_year and modification_year:
        year_gap = modification_year - creation_year
        if year_gap >= 2:
            anomalies.append(
                {
                    "type": "retroactive_edit",
                    "subtype": "significant_year_gap",
                    "severity": "medium" if year_gap < 5 else "high",
                    "creation_year": creation_year,
                    "modification_year": modification_year,
                    "year_gap": year_gap,
                    "details": (
                        f"Document has {year_gap}-year gap between "
                        f"creation and modification"
                    ),
                }
            )

    # Check for OCR applied to document (possible re-scanning)
    scan_detection = detect_scanned_vs_digital(metadata)
    ocr_detection = detect_ocr_presence(metadata)

    if scan_detection["classification"] == "scanned" and ocr_detection["ocr_detected"]:
        # If document was created digitally but later scanned with OCR
        digital_software = ["word", "acrobat", "indesign"]
        if any(s in creator.lower() for s in digital_software):
            anomalies.append(
                {
                    "type": "retroactive_edit",
                    "subtype": "rescan_detected",
                    "severity": "medium",
                    "producer": producer,
                    "creator": creator,
                    "details": "Document may have been re-scanned from digital original",
                }
            )

    # Check for producer change between creation and modification tools
    xmp = metadata.get("xmp", {})
    xmp_parsed = xmp.get("parsed", {})

    info_producer = producer.lower()
    xmp_producer = str(xmp_parsed.get("Producer", "")).lower()

    if info_producer and xmp_producer and info_producer != xmp_producer:
        if not (info_producer in xmp_producer or xmp_producer in info_producer):
            anomalies.append(
                {
                    "type": "retroactive_edit",
                    "subtype": "producer_mismatch",
                    "severity": "medium",
                    "info_producer": producer,
                    "xmp_producer": xmp_parsed.get("Producer", ""),
                    "details": "Producer mismatch between Info dict and XMP metadata",
                }
            )

    return anomalies


def classify_origin_type(metadata: dict[str, Any]) -> dict[str, Any]:
    """Classify the origin type of a PDF.

    Returns classification based on:
    - Scanner signature
    - Software engine
    - Compression patterns

    Returns:
        Origin classification dictionary
    """
    producer = str(metadata.get("info_dict", {}).get("producer", "")).lower()
    creator = str(metadata.get("info_dict", {}).get("creator", "")).lower()

    result: dict[str, Any] = {
        "origin_type": "unknown",
        "scanner_signature": None,
        "software_engine": None,
        "vendor": None,
        "confidence": 0.0,
    }

    # Detect scanner signature
    scanner_patterns = {
        "Xerox": ["xerox"],
        "Canon": ["canon"],
        "Ricoh": ["ricoh"],
        "HP": ["hp", "hewlett"],
        "Konica Minolta": ["konica", "minolta"],
        "Brother": ["brother"],
        "Epson": ["epson"],
    }

    for vendor, patterns in scanner_patterns.items():
        if any(p in producer or p in creator for p in patterns):
            result["origin_type"] = "scanned"
            result["scanner_signature"] = vendor
            result["vendor"] = vendor
            result["confidence"] = 0.8
            break

    if result["origin_type"] == "unknown":
        # Detect software engine
        for vendor, patterns in VENDOR_SOFTWARE_PATTERNS.items():
            for pattern in patterns:
                if pattern in producer or pattern in creator:
                    result["origin_type"] = "digital"
                    result["software_engine"] = producer or creator
                    result["vendor"] = vendor
                    result["confidence"] = 0.7
                    break
            if result["origin_type"] != "unknown":
                break

    return result


def score_forensic_integrity(
    metadata: dict[str, Any],
    temporal_anomalies: list[dict],
    producer_anomalies: list[dict],
    xmp_anomalies: list[dict],
    retroactive_indicators: list[dict],
    ace_anomaly_count: int = 0,
) -> dict[str, Any]:
    """Calculate forensic integrity score.

    Score Formula:
    ForensicScore = (TimestampIntegrity × 0.25) +
                   (ProducerConsistency × 0.20) +
                   (XMPIntegrity × 0.20) +
                   (OriginSignatureStability × 0.20) +
                   (ACE_Linkage × 0.15)

    All components normalized 0-1, final score 0-100.

    Returns:
        Score dictionary with component breakdown
    """
    # TimestampIntegrity (0-1): Higher = fewer temporal anomalies
    temporal_severity_sum = sum(
        (
            2.0
            if a.get("severity") == "high"
            else 1.0 if a.get("severity") == "medium" else 0.5
        )
        for a in temporal_anomalies
    )
    timestamp_integrity = max(0.0, 1.0 - (temporal_severity_sum * 0.15))

    # ProducerConsistency (0-1): Higher = fewer producer anomalies
    producer_severity_sum = sum(
        (
            2.0
            if a.get("severity") == "high"
            else 1.0 if a.get("severity") == "medium" else 0.5
        )
        for a in producer_anomalies
    )
    producer_consistency = max(0.0, 1.0 - (producer_severity_sum * 0.2))

    # XMPIntegrity (0-1): Higher = better XMP quality
    xmp = metadata.get("xmp", {})
    xmp_present = 1.0 if xmp.get("present") else 0.5
    xmp_malformed_penalty = 0.3 if xmp.get("malformed") else 0.0
    xmp_truncated_penalty = 0.2 if xmp.get("truncated") else 0.0
    xmp_anomaly_penalty = min(len(xmp_anomalies) * 0.1, 0.3)
    xmp_integrity = max(
        0.0,
        xmp_present
        - xmp_malformed_penalty
        - xmp_truncated_penalty
        - xmp_anomaly_penalty,
    )

    # OriginSignatureStability (0-1): Higher = fewer retroactive edit indicators
    retroactive_severity_sum = sum(
        (
            2.0
            if a.get("severity") == "high"
            else 1.0 if a.get("severity") == "medium" else 0.5
        )
        for a in retroactive_indicators
    )
    origin_stability = max(0.0, 1.0 - (retroactive_severity_sum * 0.15))

    # ACE_Linkage (0-1): Higher = fewer ACE anomalies linked
    ace_linkage = max(0.0, 1.0 - (ace_anomaly_count * 0.1))

    # Calculate weighted score
    weighted_score = (
        (timestamp_integrity * 0.25)
        + (producer_consistency * 0.20)
        + (xmp_integrity * 0.20)
        + (origin_stability * 0.20)
        + (ace_linkage * 0.15)
    )

    # Normalize to 0-100
    final_score = round(weighted_score * 100, 1)

    return {
        "forensic_score": final_score,
        "components": {
            "timestamp_integrity": round(timestamp_integrity, 3),
            "producer_consistency": round(producer_consistency, 3),
            "xmp_integrity": round(xmp_integrity, 3),
            "origin_signature_stability": round(origin_stability, 3),
            "ace_linkage": round(ace_linkage, 3),
        },
        "weights": {
            "timestamp_integrity": 0.25,
            "producer_consistency": 0.20,
            "xmp_integrity": 0.20,
            "origin_signature_stability": 0.20,
            "ace_linkage": 0.15,
        },
        "anomaly_counts": {
            "temporal": len(temporal_anomalies),
            "producer": len(producer_anomalies),
            "xmp": len(xmp_anomalies),
            "retroactive": len(retroactive_indicators),
            "ace_linked": ace_anomaly_count,
        },
    }


def cluster_pdfs_by_origin(
    pdf_metadata_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """Cluster PDFs by origin characteristics.

    Groups PDFs by:
    - Scanner signature
    - Software engine
    - Compression patterns

    Returns:
        Clustering results with cluster signatures
    """
    clusters: dict[str, list[dict]] = defaultdict(list)

    for metadata in pdf_metadata_list:
        origin = classify_origin_type(metadata)
        cluster_key = (
            origin.get("origin_type", "unknown"),
            origin.get("vendor", "unknown"),
        )

        clusters[f"{cluster_key[0]}_{cluster_key[1]}".lower()].append(
            {
                "file_path": metadata.get("file_path"),
                "file_name": metadata.get("file_name"),
                "origin": origin,
            }
        )

    result: dict[str, Any] = {
        "cluster_count": len(clusters),
        "clusters": {},
    }

    for cluster_name, members in clusters.items():
        result["clusters"][cluster_name] = {
            "member_count": len(members),
            "origin_type": (
                members[0]["origin"]["origin_type"] if members else "unknown"
            ),
            "vendor": members[0]["origin"]["vendor"] if members else None,
            "members": members,
        }

    return result


def generate_forensic_report(
    corpus_root: Path,
    year_range: str,
    ace_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate comprehensive forensic report for the corpus.

    Returns:
        Complete forensic report dictionary
    """
    start_year, end_year = parse_year_range(year_range)
    corpora = filter_corpora_by_years(start_year, end_year)

    report: dict[str, Any] = {
        "version": DPMM_VERSION,
        "schema_version": DPMM_SCHEMA_VERSION,
        "generated_at": get_utc_timestamp(),
        "year_range": year_range,
        "corpora_analyzed": len(corpora),
        "pdfs_processed": 0,
        "pdfs_found_count": 0,
        "pdfs_metadata_count": 0,
        "mode": "unknown",
        "summary": {},
        "metadata_by_file": {},
        "anomalies": [],
        "scores": {},
        "clusters": {},
    }

    all_metadata = []
    all_anomalies = []
    file_scores = {}

    # Process each corpus
    for hist_id, meeting_date in corpora.items():
        corpus_dir = corpus_root / hist_id

        if not corpus_dir.exists():
            continue

        # Check if actual PDF files exist
        pdf_files = []
        for subdir in ["attachments", "agendas", "minutes", "staff_reports"]:
            subdir_path = corpus_dir / subdir
            if subdir_path.exists():
                pdf_files.extend(subdir_path.glob("*.pdf"))

        # If no actual PDFs found, try to use metadata from index.json
        if not pdf_files:
            index_path = corpus_dir / "index.json"
            if index_path.exists():
                try:
                    with open(index_path, encoding="utf-8") as f:
                        index_data = json.load(f)

                    files = index_data.get("files", [])
                    if files:
                        report["mode"] = "metadata_only"
                        report["pdfs_metadata_count"] += len(files)

                        # Process metadata for each file entry
                        for file_entry in files:
                            file_name = file_entry.get("file_name", "")
                            file_type = file_entry.get("file_type", "unknown")
                            file_hash = file_entry.get("file_hash", "")

                            # Create simulated metadata from index data
                            simulated_metadata = {
                                "file_name": file_name,
                                "file_type": file_type,
                                "file_hash": file_hash,
                                "hist_id": hist_id,
                                "meeting_date": meeting_date,
                                "extraction_complete": file_entry.get(
                                    "extraction_complete", False
                                ),
                                "mode": "metadata_only",
                                "source": "index.json",
                            }

                            file_key = f"{hist_id}/{file_type}/{file_name}"
                            report["metadata_by_file"][file_key] = simulated_metadata

                            # Create a basic forensic score based on metadata completeness
                            metadata_score = {
                                "forensic_score": 85.0 if file_hash else 50.0,
                                "components": {
                                    "metadata_completeness": 1.0 if file_hash else 0.5,
                                    "extraction_status": (
                                        1.0
                                        if file_entry.get("extraction_complete")
                                        else 0.5
                                    ),
                                },
                                "mode": "metadata_only",
                            }
                            file_scores[file_key] = metadata_score

                        report["pdfs_processed"] += len(files)
                        continue

                except (json.JSONDecodeError, OSError) as e:
                    # Skip corrupted or inaccessible index.json files and continue processing
                    print(
                        f"Warning: Failed to load or parse {index_path}: {e}",
                        file=sys.stderr,
                    )

        # Process actual PDF files if found
        if pdf_files:
            report["mode"] = "full_forensic"
            report["pdfs_found_count"] += len(pdf_files)

            for pdf_path in pdf_files:
                # Extract metadata
                metadata = extract_pdf_metadata(pdf_path)
                metadata["hist_id"] = hist_id
                metadata["meeting_date"] = meeting_date

                if metadata["extraction_success"]:
                    # Detect anomalies
                    temporal = detect_temporal_anomalies(metadata, meeting_date)
                    producer = detect_producer_anomalies(metadata)
                    xmp = detect_xmp_anomalies(metadata)
                    retroactive = detect_retroactive_edit_indicators(
                        metadata, meeting_date
                    )

                    # Get ACE anomaly count for this corpus
                    ace_count = 0
                    if ace_report:
                        ace_by_hist = ace_report.get("by_hist_id", {})
                        ace_count = len(ace_by_hist.get(hist_id, []))

                    # Calculate score
                    score = score_forensic_integrity(
                        metadata, temporal, producer, xmp, retroactive, ace_count
                    )

                    # Classify origin (used for clustering)
                    classify_origin_type(metadata)

                    # Store results
                    file_key = str(pdf_path)
                    report["metadata_by_file"][file_key] = metadata

                    for anomaly in temporal + producer + xmp + retroactive:
                        anomaly["file_path"] = str(pdf_path)
                        anomaly["hist_id"] = hist_id
                        anomaly["meeting_date"] = meeting_date
                        all_anomalies.append(anomaly)

                    file_scores[file_key] = score
                    all_metadata.append(metadata)

                report["pdfs_processed"] += 1

    # Cluster PDFs by origin (only if we have actual PDF metadata)
    if all_metadata:
        report["clusters"] = cluster_pdfs_by_origin(all_metadata)

    # Store anomalies and scores
    report["anomalies"] = all_anomalies
    report["scores"] = file_scores

    # Set mode if not already set
    if report["mode"] == "unknown":
        if report["pdfs_found_count"] > 0:
            report["mode"] = "full_forensic"
        elif report["pdfs_metadata_count"] > 0:
            report["mode"] = "metadata_only"
        else:
            report["mode"] = "no_pdfs"

    # Generate summary
    report["summary"] = {
        "total_pdfs": report["pdfs_processed"],
        "pdfs_found": report["pdfs_found_count"],
        "pdfs_from_metadata": report["pdfs_metadata_count"],
        "successful_extractions": len(all_metadata),
        "total_anomalies": len(all_anomalies),
        "anomalies_by_type": defaultdict(int),
        "average_score": 0.0,
        "cluster_count": report["clusters"].get("cluster_count", 0),
        "mode": report["mode"],
    }

    for anomaly in all_anomalies:
        report["summary"]["anomalies_by_type"][anomaly.get("type", "unknown")] += 1

    if file_scores:
        avg_score = sum(s["forensic_score"] for s in file_scores.values()) / len(
            file_scores
        )
        report["summary"]["average_score"] = round(avg_score, 2)

    # Convert defaultdict to dict for JSON serialization
    report["summary"]["anomalies_by_type"] = dict(
        report["summary"]["anomalies_by_type"]
    )

    # Add total_scanned for backward compatibility with existing report generator
    # TODO(technical-debt): Deprecate total_scanned in favor of pdfs_processed in future version
    # This field exists solely for backward compatibility and should be removed once all consumers
    # have been updated to use pdfs_processed instead.
    report["total_scanned"] = report["pdfs_processed"]

    return report


def generate_inconsistency_map(
    forensic_report: dict[str, Any],
) -> dict[str, Any]:
    """Generate metadata inconsistency map from forensic report.

    Returns:
        Inconsistency map grouped by year
    """
    inconsistency_map: dict[str, Any] = {
        "version": DPMM_VERSION,
        "generated_at": get_utc_timestamp(),
        "by_year": defaultdict(list),
        "by_type": defaultdict(list),
        "total_inconsistencies": 0,
    }

    for anomaly in forensic_report.get("anomalies", []):
        meeting_date = anomaly.get("meeting_date", "")
        year = meeting_date[:4] if meeting_date else "unknown"
        anomaly_type = anomaly.get("type", "unknown")

        inconsistency_map["by_year"][year].append(anomaly)
        inconsistency_map["by_type"][anomaly_type].append(anomaly)
        inconsistency_map["total_inconsistencies"] += 1

    # Convert defaultdicts to dicts
    inconsistency_map["by_year"] = dict(inconsistency_map["by_year"])
    inconsistency_map["by_type"] = dict(inconsistency_map["by_type"])

    return inconsistency_map


def generate_forensic_graph(
    forensic_report: dict[str, Any],
) -> dict[str, Any]:
    """Generate forensic relationship graph for visualization.

    Returns:
        Graph structure with nodes and edges
    """
    nodes = []
    edges = []
    node_ids = set()

    # Create nodes for each corpus
    for _file_path, metadata in forensic_report.get("metadata_by_file", {}).items():
        hist_id = metadata.get("hist_id", "unknown")
        if hist_id not in node_ids:
            nodes.append(
                {
                    "id": hist_id,
                    "type": "corpus",
                    "pdf_count": 1,
                }
            )
            node_ids.add(hist_id)
        else:
            # Update pdf count
            for node in nodes:
                if node["id"] == hist_id:
                    node["pdf_count"] = node.get("pdf_count", 0) + 1

    # Create nodes for anomaly types
    anomaly_types = set(a.get("type") for a in forensic_report.get("anomalies", []))
    for anomaly_type in anomaly_types:
        if anomaly_type and anomaly_type not in node_ids:
            nodes.append(
                {
                    "id": anomaly_type,
                    "type": "anomaly_type",
                }
            )
            node_ids.add(anomaly_type)

    # Create nodes for origin clusters
    clusters = forensic_report.get("clusters", {}).get("clusters", {})
    for cluster_name, cluster_data in clusters.items():
        if cluster_name not in node_ids:
            nodes.append(
                {
                    "id": cluster_name,
                    "type": "origin_cluster",
                    "member_count": cluster_data.get("member_count", 0),
                }
            )
            node_ids.add(cluster_name)

    # Create edges between corpora and anomaly types
    for anomaly in forensic_report.get("anomalies", []):
        hist_id = anomaly.get("hist_id")
        anomaly_type = anomaly.get("type")

        if (
            hist_id
            and anomaly_type
            and hist_id in node_ids
            and anomaly_type in node_ids
        ):
            edges.append(
                {
                    "source": hist_id,
                    "target": anomaly_type,
                    "type": "has_anomaly",
                }
            )

    return {
        "generated_at": get_utc_timestamp(),
        "dpmm_version": DPMM_VERSION,
        "nodes": nodes,
        "edges": edges,
        "statistics": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "corpus_nodes": len([n for n in nodes if n.get("type") == "corpus"]),
            "anomaly_type_nodes": len(
                [n for n in nodes if n.get("type") == "anomaly_type"]
            ),
            "cluster_nodes": len(
                [n for n in nodes if n.get("type") == "origin_cluster"]
            ),
        },
    }


def generate_dpmm_summary_md(forensic_report: dict[str, Any]) -> str:
    """Generate DPMM_SUMMARY.md content.

    Returns:
        Markdown string for the summary
    """
    summary = forensic_report.get("summary", {})
    clusters = forensic_report.get("clusters", {})

    lines = [
        "# DPMM v1.0 - Deep Packet Metadata Miner Summary",
        "",
        f"**Generated:** {forensic_report.get('generated_at', 'N/A')}",
        f"**Year Range:** {forensic_report.get('year_range', 'N/A')}",
        f"**Version:** {forensic_report.get('version', DPMM_VERSION)}",
        "",
        "## Executive Summary",
        "",
        f"- **Total PDFs Processed:** {summary.get('total_pdfs', 0)}",
        f"- **Successful Extractions:** {summary.get('successful_extractions', 0)}",
        f"- **Total Anomalies Detected:** {summary.get('total_anomalies', 0)}",
        f"- **Average Forensic Score:** {summary.get('average_score', 0):.1f}/100",
        f"- **Origin Clusters Identified:** {clusters.get('cluster_count', 0)}",
        "",
        "## Anomalies by Type",
        "",
        "| Type | Count |",
        "|------|-------|",
    ]

    anomalies_by_type = summary.get("anomalies_by_type", {})
    for anomaly_type, count in sorted(anomalies_by_type.items(), key=lambda x: -x[1]):
        lines.append(f"| {anomaly_type} | {count} |")

    lines.extend(
        [
            "",
            "## Origin Clusters",
            "",
        ]
    )

    cluster_data = clusters.get("clusters", {})
    if cluster_data:
        for cluster_name, cluster_info in sorted(cluster_data.items()):
            count = cluster_info.get("member_count", 0)
            vendor = cluster_info.get("vendor", "Unknown")
            origin_type = cluster_info.get("origin_type", "unknown")
            lines.append(
                f"- **{cluster_name}**: {count} PDFs ({origin_type}, vendor: {vendor})"
            )
    else:
        lines.append("*No origin clusters identified.*")

    lines.extend(
        [
            "",
            "## Scoring Model",
            "",
            "The forensic score (0-100) is calculated as:",
            "",
            "```",
            "ForensicScore = (TimestampIntegrity × 0.25) +",
            "               (ProducerConsistency × 0.20) +",
            "               (XMPIntegrity × 0.20) +",
            "               (OriginSignatureStability × 0.20) +",
            "               (ACE_Linkage × 0.15)",
            "```",
            "",
            "---",
            "",
            "*Generated by DPMM v1.0 - Deep Packet Metadata Miner*",
        ]
    )

    return "\n".join(lines)


def run_pdf_forensics(
    corpus_root: Path,
    year_range: str,
    output_dir: Path | None = None,
    ace_report_path: Path | None = None,
) -> dict[str, Any]:
    """Run the complete PDF forensics analysis pipeline.

    Returns:
        The generated forensic report
    """
    print(f"DPMM v{DPMM_VERSION} - Deep Packet Metadata Miner")
    print("=" * 60)
    print(f"Corpus Root: {corpus_root}")
    print(f"Year Range: {year_range}")
    print("=" * 60)

    # Load ACE report if available
    ace_report = None
    if ace_report_path and ace_report_path.exists():
        try:
            with open(ace_report_path, encoding="utf-8") as f:
                ace_report = json.load(f)
            print(f"\nLoaded ACE report from {ace_report_path}")
        except (json.JSONDecodeError, OSError):
            print(f"\nWarning: Could not load ACE report from {ace_report_path}")

    # Step 1: Generate forensic report
    print("\n[1/5] Extracting PDF metadata and analyzing...")
    forensic_report = generate_forensic_report(corpus_root, year_range, ace_report)
    print(f"  - Processed {forensic_report['pdfs_processed']} PDFs")
    print(f"  - Found {forensic_report['summary']['total_anomalies']} anomalies")

    # Step 2: Generate inconsistency map
    print("\n[2/5] Generating inconsistency map...")
    inconsistency_map = generate_inconsistency_map(forensic_report)
    print(f"  - Mapped {inconsistency_map['total_inconsistencies']} inconsistencies")

    # Step 3: Generate forensic graph
    print("\n[3/5] Generating forensic graph...")
    forensic_graph = generate_forensic_graph(forensic_report)
    print(f"  - Created {forensic_graph['statistics']['total_nodes']} nodes")
    print(f"  - Created {forensic_graph['statistics']['total_edges']} edges")

    # Step 4: Generate cluster report
    print("\n[4/5] Generating origin cluster report...")
    clusters = forensic_report.get("clusters", {})
    print(f"  - Identified {clusters.get('cluster_count', 0)} origin clusters")

    # Step 5: Generate summary
    print("\n[5/5] Generating summary...")
    summary_md = generate_dpmm_summary_md(forensic_report)

    # Determine output directory
    if output_dir is None:
        output_dir = Path("analysis/pdf_forensics")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Write output files
    report_path = output_dir / "forensic_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(forensic_report, f, indent=2, default=str)
        f.write("\n")
    print(f"\n  - Wrote {report_path}")

    inconsistency_path = output_dir / "metadata_inconsistency_map.json"
    with open(inconsistency_path, "w", encoding="utf-8") as f:
        json.dump(inconsistency_map, f, indent=2, default=str)
        f.write("\n")
    print(f"  - Wrote {inconsistency_path}")

    cluster_path = output_dir / "pdf_origin_clusters.json"
    with open(cluster_path, "w", encoding="utf-8") as f:
        json.dump(clusters, f, indent=2, default=str)
        f.write("\n")
    print(f"  - Wrote {cluster_path}")

    graph_path = output_dir / "pdf_forensics_graph.json"
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(forensic_graph, f, indent=2, default=str)
        f.write("\n")
    print(f"  - Wrote {graph_path}")

    summary_path = output_dir / "DPMM_SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_md)
        f.write("\n")
    print(f"  - Wrote {summary_path}")

    print("\n" + "=" * 60)
    print("PDF FORENSICS ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\nTotal PDFs: {forensic_report['pdfs_processed']}")
    print(f"Anomalies: {forensic_report['summary']['total_anomalies']}")
    print(f"Average Score: {forensic_report['summary']['average_score']:.1f}/100")
    print(f"Origin Clusters: {clusters.get('cluster_count', 0)}")

    return forensic_report


def main():
    """Main entry point for DPMM CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DPMM v1.0 - Deep Packet Metadata Miner"
    )
    parser.add_argument(
        "--corpus-root",
        type=str,
        default="oraculus/corpus",
        help="Root directory for corpus files",
    )
    parser.add_argument(
        "--years",
        type=str,
        default="2014-2025",
        help="Year range to analyze (e.g., 2014-2025)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="analysis/pdf_forensics",
        help="Output directory for forensic reports",
    )
    parser.add_argument(
        "--ace-report",
        type=str,
        default=None,
        help="Path to ACE_REPORT.json for cross-linking",
    )

    args = parser.parse_args()
    corpus_root = Path(args.corpus_root).resolve()
    output_dir = Path(args.output).resolve()
    ace_report_path = Path(args.ace_report).resolve() if args.ace_report else None

    if not corpus_root.exists():
        print(f"Error: Corpus root not found: {corpus_root}")
        sys.exit(1)

    run_pdf_forensics(corpus_root, args.years, output_dir, ace_report_path)


if __name__ == "__main__":
    main()
