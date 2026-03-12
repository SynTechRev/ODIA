#!/usr/bin/env python3
"""
Run pdf_extractor.extract_text across corpus_manifest files

Usage:
 python -m scripts.bulk_pdf_extract
"""

import json
import logging
import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

from scripts.pdf_extractor import extract_text  # noqa: E402

LOG = logging.getLogger("oraculus.bulk_extract")
logging.basicConfig(level=logging.INFO)

MANIFEST = Path("transparency_release/corpus_manifest.json")
EXTRACT_DIR = Path("analysis/extracted_text")


def process_single_pdf(pdf_path, extraction_stats):
    """Process a single PDF and update extraction statistics."""
    from config.ocr_config import OCR_MIN_CONFIDENCE

    try:
        result = extract_text(pdf_path)
        extraction_stats["total_pdfs"] += 1

        if result["success"]:
            # write extracted text
            out_file = EXTRACT_DIR / f"{pdf_path.stem}.txt"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(result["text"], encoding="utf-8")
            extraction_stats["successful"] += 1

            # Track extraction method
            method = result.get("method", "unknown")
            extraction_stats["methods"][method] = (
                extraction_stats["methods"].get(method, 0) + 1
            )

            # Track confidence
            confidence = result.get("confidence", 0.0)
            extraction_stats["avg_confidence"] += confidence

            # Flag low confidence extractions
            if confidence < OCR_MIN_CONFIDENCE:
                extraction_stats["low_confidence_files"].append(
                    {"file": str(pdf_path), "confidence": confidence, "method": method}
                )

            LOG.info(
                "Extracted %s (%s, confidence: %.2f)", pdf_path.name, method, confidence
            )
            return True
        else:
            extraction_stats["failed"] += 1
            LOG.warning("Failed to extract %s: %s", pdf_path.name, result.get("error"))
            return False
    except OSError as e:
        LOG.error(
            "IO error processing %s: %s (check file permissions and disk space)",
            pdf_path,
            e,
        )
        return False
    except ImportError as e:
        LOG.error(
            "Missing dependencies for %s: %s "
            "(install with: pip install pytesseract pdf2image)",
            pdf_path,
            e,
        )
        return False
    except Exception as e:
        LOG.exception("Unexpected error processing %s: %s", pdf_path, e)
        return False


def main():
    if not MANIFEST.exists():
        LOG.error("Manifest not found: %s", MANIFEST)
        raise SystemExit(1)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest.get("files", [])
    corpus_root = Path(manifest.get("corpus_root", "oraculus/corpus"))

    LOG.info("Found %d files in manifest", len(files))

    pdf_count = 0
    success_count = 0
    extraction_stats = {
        "total_pdfs": 0,
        "successful": 0,
        "failed": 0,
        "methods": {},
        "avg_confidence": 0.0,
        "low_confidence_files": [],
    }

    for entry in files:
        rel = entry.get("relative_path")
        if not rel or not rel.lower().endswith(".pdf"):
            continue

        pdf_count += 1
        pdf_path = corpus_root / rel
        if not pdf_path.exists():
            LOG.warning("PDF not found: %s", pdf_path)
            continue

        if process_single_pdf(pdf_path, extraction_stats):
            success_count += 1

    # Calculate average confidence
    if extraction_stats["successful"] > 0:
        extraction_stats["avg_confidence"] /= extraction_stats["successful"]
    else:
        # Ensure avg_confidence is a true average (0.0 when there are no successes)
        extraction_stats["avg_confidence"] = 0.0

    LOG.info("Bulk extraction complete: %d/%d PDFs extracted", success_count, pdf_count)
    print(f"Extracted {success_count}/{pdf_count} PDFs to {EXTRACT_DIR}")
    print(f"Average confidence: {extraction_stats['avg_confidence']:.2f}")
    print(f"Extraction methods used: {extraction_stats['methods']}")
    print(f"Low confidence files: {len(extraction_stats['low_confidence_files'])}")

    # Write extraction quality report
    quality_report_path = EXTRACT_DIR / "extraction_quality_report.json"
    quality_report_path.write_text(
        json.dumps(extraction_stats, indent=2), encoding="utf-8"
    )
    LOG.info("Extraction quality report saved to %s", quality_report_path)


if __name__ == "__main__":
    main()
