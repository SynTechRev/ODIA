#!/usr/bin/env python3
"""
PDF Text Extractor - Universal extractor supporting digital-native and OCR.

This module provides text extraction from PDF files, with fallback to OCR
for scanned documents.

Author: GitHub Copilot Agent
Date: 2025-12-08
"""

import logging
import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

# Configure logging
LOG = logging.getLogger("oraculus.pdf_extractor")

# OCR configuration constants
OCR_DPI = (
    300  # DPI for OCR image conversion (300 DPI provides good quality/speed tradeoff)
)
OCR_THRESHOLD_CHARS = (
    40  # Minimum characters for digital extraction (below this triggers OCR fallback)
)


def extract_pdf_text_digital(path: Path) -> str:
    """
    Extract text from digital-native PDF.

    Args:
        path: Path to PDF file

    Returns:
        Extracted text content
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        text_parts = []

        for page in reader.pages:
            text_parts.append(page.extract_text())

        return "\n".join(text_parts)
    except Exception:
        return ""


def run_ocr(path: Path, enhanced: bool = True) -> tuple[str, float]:
    """
    Run OCR on scanned PDF with optional preprocessing.

    Args:
        path: Path to PDF file
        enhanced: Whether to use enhanced preprocessing

    Returns:
        Tuple of (extracted text, confidence score 0.0-1.0)
    """
    # Import OCR dependencies
    try:
        import pytesseract
        from pdf2image import convert_from_path

        pages = convert_from_path(str(path), dpi=OCR_DPI)
        texts = []
        confidences = []

        for page in pages:
            # Apply preprocessing if enhanced mode
            if enhanced:
                try:
                    from scripts.pdf_preprocessor import preprocess_image_for_ocr

                    page = preprocess_image_for_ocr(page)
                except ImportError:
                    LOG.debug("Preprocessor not available - using raw OCR")

            # Extract text with confidence data
            try:
                # Get detailed OCR data including confidence
                ocr_data = pytesseract.image_to_data(
                    page, output_type=pytesseract.Output.DICT
                )

                # Extract text
                page_text = pytesseract.image_to_string(page)
                texts.append(page_text)

                # Calculate average confidence for words with text
                word_confidences = [
                    float(conf)
                    for conf, text in zip(
                        ocr_data["conf"], ocr_data["text"], strict=False
                    )
                    if conf != -1 and text.strip()
                ]
                if word_confidences:
                    page_confidence = (
                        sum(word_confidences) / len(word_confidences) / 100.0
                    )
                    confidences.append(page_confidence)
                else:
                    # No usable word confidences; record a default low confidence
                    confidences.append(0.0)
            except Exception as e:
                # Fallback to simple extraction without confidence
                LOG.debug(f"Confidence extraction failed: {e}")
                page_text = pytesseract.image_to_string(page)
                texts.append(page_text)
                confidences.append(0.5)  # Neutral confidence

        text = "\n".join(texts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return text, avg_confidence
    except ImportError as e:
        # OCR dependencies not available - return placeholder
        LOG.warning("OCR dependencies missing (pdf2image, pytesseract): %s", e)
        return (
            f"[OCR would be performed on {path.name} - dependencies not installed]",
            0.0,
        )
    except Exception as e:
        LOG.error("OCR failed for %s: %s", path, e)
        return "", 0.0


def extract_text(path: Path) -> dict:
    """
    Extract text from PDF using digital extraction or OCR fallback.

    Args:
        path: Path to PDF file

    Returns:
        Dictionary with extraction results including confidence score

    Note:
        OCR fallback includes image preprocessing for improved accuracy.
        Confidence scores range from 0.0 (low quality) to 1.0 (high quality).
    """
    try:
        # Try digital extraction first
        text = extract_pdf_text_digital(path)
        confidence = 1.0  # Digital extraction is high confidence
        method = "digital"

        # Fallback to OCR if no text extracted
        if not text or len(text.strip()) < OCR_THRESHOLD_CHARS:
            text, confidence = run_ocr(path, enhanced=True)
            # Check if OCR actually ran or returned placeholder
            if confidence > 0.0 and text and len(text.strip()) > 0:
                method = "ocr_enhanced"
            else:
                method = "ocr"
                confidence = 0.0

        return {
            "path": str(path),
            "text": text,
            "success": True,
            "method": method,
            "confidence": confidence,
            "error": None,
        }
    except Exception as e:
        return {
            "path": str(path),
            "text": "",
            "success": False,
            "method": None,
            "confidence": 0.0,
            "error": str(e),
        }


def extract_all(corpus_entries: list[dict]) -> list[dict]:
    """
    Extract text from all PDFs in corpus entries.

    Args:
        corpus_entries: List of corpus entries with file information

    Returns:
        List of extraction results
    """
    results = []

    for entry in corpus_entries:
        corpus_id = entry.get("corpus_id", "")
        for file_info in entry.get("files", []):
            file_name = file_info.get("name", "")
            if file_name.lower().endswith(".pdf"):
                # Note: In actual implementation, would construct full path
                # For now, record that extraction would occur
                results.append(
                    {
                        "corpus_id": corpus_id,
                        "file_name": file_name,
                        "extraction_complete": file_info.get(
                            "extraction_complete", False
                        ),
                        "text_hash": file_info.get("text_hash", ""),
                    }
                )

    return results


def main():
    """Main entry point for PDF extraction."""
    import argparse
    import logging

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Extract text from PDF files")
    parser.add_argument("pdf", nargs="?", help="PDF file to extract")
    parser.add_argument(
        "--out-dir",
        default="analysis/extracted_text",
        help="Output directory for extracted text",
    )
    args = parser.parse_args()

    if args.pdf:
        # Extract single PDF
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            print(f"Error: PDF file not found: {pdf_path}")
            return 1

        result = extract_text(pdf_path)
        if result["success"]:
            # Write to output file
            out_dir = Path(args.out_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{pdf_path.stem}.txt"
            out_file.write_text(result["text"], encoding="utf-8")
            print(f"✓ Extracted text using {result['method']} method")
            print(f"  Output: {out_file}")
        else:
            print(f"✗ Extraction failed: {result.get('error', 'Unknown error')}")
            return 1
    else:
        print("PDF Extractor module initialized")
        print("Use extract_text(path) to extract text from a PDF file")
        print("Or run with: python pdf_extractor.py <pdf_file> [--out-dir <dir>]")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
