#!/usr/bin/env python3
"""
Manual Review Queue Generator

Scans extraction quality reports and generates a manifest of low-confidence
extractions that require manual review.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root))

# Import after path setup
from config.ocr_config import OCR_MIN_CONFIDENCE  # noqa: E402

LOG = logging.getLogger("oraculus.manual_review")
logging.basicConfig(level=logging.INFO)

QUALITY_REPORT = Path("analysis/extracted_text/extraction_quality_report.json")
OUTPUT_PATH = Path("oraculus/corpus/manual_review_queue.json")


def generate_manual_review_queue() -> dict:
    """
    Generate manual review queue from extraction quality report.

    Returns:
        Dictionary with manual review queue data
    """
    if not QUALITY_REPORT.exists():
        LOG.warning("Extraction quality report not found: %s", QUALITY_REPORT)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "threshold": OCR_MIN_CONFIDENCE,
            "total_reviewed": 0,
            "low_confidence_documents": [],
            "message": (
                "No extraction quality report available - "
                "run bulk_pdf_extract.py first"
            ),
        }

    try:
        with open(QUALITY_REPORT, encoding="utf-8") as f:
            quality_data = json.load(f)

        low_confidence = quality_data.get("low_confidence_files", [])

        # Enrich with issue descriptions
        enriched_docs = []
        for item in low_confidence:
            file_value = item.get("file")
            if not file_value:
                LOG.warning("Skipping low_confidence item without 'file': %s", item)
                continue
            file_path = Path(file_value)
            confidence = item.get("confidence", 0.0)
            method = item.get("method", "unknown")

            # Determine issues based on confidence and method
            issues = []
            if confidence < 0.3:
                issues.append("very low confidence")
            elif confidence < 0.5:
                issues.append("low confidence")
            elif confidence < OCR_MIN_CONFIDENCE:
                issues.append("below threshold confidence")

            if method == "ocr_enhanced":
                issues.append("scanned document")

            enriched_docs.append(
                {
                    "corpus_id": (
                        file_path.parent.name if file_path.parent else "unknown"
                    ),
                    "pdf_path": str(file_path),
                    "confidence": round(confidence, 3),
                    "method": method,
                    "issues": issues,
                    "requires_manual_extraction": confidence < 0.5,
                }
            )

        total_pdfs = quality_data.get("total_pdfs", 0)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "threshold": OCR_MIN_CONFIDENCE,
            "total_reviewed": total_pdfs,
            "total_low_confidence": len(low_confidence),
            "low_confidence_documents": enriched_docs,
            "summary": {
                "avg_confidence": quality_data.get("avg_confidence", 0.0),
                "extraction_methods": quality_data.get("methods", {}),
                "success_rate": (
                    quality_data.get("successful", 0) / total_pdfs
                    if total_pdfs > 0
                    else 0.0
                ),
            },
        }

    except Exception as e:
        LOG.error("Failed to generate manual review queue: %s", e)
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "threshold": OCR_MIN_CONFIDENCE,
            "error": str(e),
            "low_confidence_documents": [],
        }


def main():
    """Main entry point."""
    LOG.info("Generating manual review queue...")

    queue_data = generate_manual_review_queue()

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(queue_data, f, indent=2, ensure_ascii=False)

    LOG.info("Manual review queue saved to: %s", OUTPUT_PATH)

    # Print summary
    print("\nManual Review Queue Summary:")
    print(f"  Total documents reviewed: {queue_data.get('total_reviewed', 0)}")
    print(f"  Low confidence documents: {queue_data.get('total_low_confidence', 0)}")
    print(f"  Confidence threshold: {queue_data.get('threshold', 0.0)}")

    if "summary" in queue_data:
        summary = queue_data["summary"]
        print(f"  Average confidence: {summary.get('avg_confidence', 0.0):.2f}")
        print(f"  Success rate: {summary.get('success_rate', 0.0):.1%}")
        print(f"  Extraction methods: {summary.get('extraction_methods', {})}")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
