#!/usr/bin/env python3
"""
Oraculus DI Auditor - OCR Sample Script

Lightweight OCR runner using Pillow + pytesseract for extracting text from PDFs.
Supports optional deskewing with opencv-python if available.

Usage:
    python scripts/ocr_sample.py --input /path/to/file.pdf --page 1 \\
        --out manifests/DOC123.json
    python scripts/ocr_sample.py --input /path/to/file.pdf \\
        --all-pages --deskew
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print(
        "Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr
    )
    sys.exit(1)

try:
    import pytesseract
except ImportError:
    print(
        "Error: pytesseract is required. Install with: pip install pytesseract",
        file=sys.stderr,
    )
    print("Also ensure tesseract-ocr is installed on your system.", file=sys.stderr)
    sys.exit(1)

try:
    from pdf2image import convert_from_path
except ImportError:
    print(
        "Warning: pdf2image not available. Install with: pip install pdf2image",
        file=sys.stderr,
    )
    print("PDF support will be limited.", file=sys.stderr)
    convert_from_path = None

# Optional: OpenCV for deskewing
try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class OCRProcessor:
    """Processes images and PDFs with OCR."""

    def __init__(self, deskew: bool = False, dpi: int = 300, language: str = "eng"):
        self.deskew = deskew and OPENCV_AVAILABLE
        self.dpi = dpi
        self.language = language

    def deskew_image(self, image: Image.Image) -> Image.Image:
        """Deskew an image using OpenCV (if available)."""
        if not OPENCV_AVAILABLE or not self.deskew:
            return image

        # Convert PIL Image to OpenCV format
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Detect angle using Hough transform
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate image
        (h, w) = gray.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            img_array,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return Image.fromarray(rotated)

    def extract_text_from_image(self, image: Image.Image) -> tuple[str, float]:
        """Extract text from an image using pytesseract."""
        # Optionally deskew
        if self.deskew:
            image = self.deskew_image(image)

        # Perform OCR
        text = pytesseract.image_to_string(image, lang=self.language)

        # Get confidence data
        try:
            data = pytesseract.image_to_data(
                image, lang=self.language, output_type=pytesseract.Output.DICT
            )
            confidences = [float(c) for c in data["conf"] if c != "-1"]
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )
        except Exception:
            avg_confidence = 0.0

        return text, avg_confidence

    def extract_text_from_pdf(
        self, pdf_path: Path, pages: list[int] | None = None
    ) -> tuple[str, float, int]:
        """Extract text from PDF pages."""
        if convert_from_path is None:
            raise RuntimeError("pdf2image is required for PDF processing")

        # Convert PDF to images
        if pages:
            images = convert_from_path(
                pdf_path, dpi=self.dpi, first_page=min(pages), last_page=max(pages)
            )
        else:
            images = convert_from_path(pdf_path, dpi=self.dpi)

        all_text = []
        confidences = []

        for i, image in enumerate(images):
            print(f"  Processing page {i + 1}/{len(images)}...", end="\r")
            text, confidence = self.extract_text_from_image(image)
            all_text.append(text)
            confidences.append(confidence)

        print()  # Clear progress line

        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return combined_text, avg_confidence, len(images)


def update_manifest(
    manifest_path: Path,
    doc_id: str,
    extracted_text_path: Path,
    pages: int,
    confidence: float,
    ocr_engine: str = "tesseract",
) -> None:
    """Update manifest with extraction metadata."""
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        # Create basic manifest
        manifest = {
            "document_id": doc_id,
            "source": "ocr_extraction",
            "original_path": "",
            "ingest_date": datetime.utcnow().isoformat() + "Z",
            "uploader": "system",
            "checksum_sha256": "",
            "flags": [],
            "notes": [],
            "chain_of_custody": [],
        }

    # Update extraction metadata
    manifest["extraction"] = {
        "text_present": True,
        "ocr_used": True,
        "extraction_confidence": round(confidence, 3),
        "ocr_engine": ocr_engine,
        "pages": pages,
        "extracted_text_path": str(extracted_text_path),
    }

    # Add chain of custody entry
    if "chain_of_custody" not in manifest:
        manifest["chain_of_custody"] = []

    manifest["chain_of_custody"].append(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "actor": "ocr_sample.py",
            "action": "text_extraction",
            "details": (
                f"OCR with {ocr_engine}, {pages} pages, "
                f"confidence: {confidence:.2f}"
            ),
        }
    )

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - OCR Sample Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from page 1 of a PDF
  python scripts/ocr_sample.py --input /storage/file.pdf --page 1 \\
      --out manifests/DOC123.json

  # Extract all pages with deskewing
  python scripts/ocr_sample.py --input /storage/file.pdf --all-pages --deskew

  # Extract specific pages
  python scripts/ocr_sample.py --input /storage/file.pdf --page 1 --page 3 --page 5
        """,
    )

    parser.add_argument(
        "--input", required=True, type=str, help="Path to input PDF or image file"
    )
    parser.add_argument(
        "--page",
        type=int,
        action="append",
        help="Specific page number(s) to extract (1-indexed)",
    )
    parser.add_argument("--all-pages", action="store_true", help="Extract all pages")
    parser.add_argument(
        "--out", type=str, help="Path to manifest file to update (optional)"
    )
    parser.add_argument(
        "--extraction-dir",
        type=str,
        default="extraction",
        help="Directory to save extracted text (default: extraction)",
    )
    parser.add_argument(
        "--deskew",
        action="store_true",
        help="Apply deskewing (requires opencv-python)",
    )
    parser.add_argument(
        "--dpi", type=int, default=300, help="DPI for PDF rendering (default: 300)"
    )
    parser.add_argument(
        "--language",
        type=str,
        default="eng",
        help="Tesseract language code (default: eng)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.all_pages and not args.page:
        print("Error: Must specify --page or --all-pages", file=sys.stderr)
        sys.exit(1)

    if args.deskew and not OPENCV_AVAILABLE:
        print(
            "Warning: --deskew specified but opencv-python not available. "
            "Skipping deskew."
        )

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Determine document ID
    doc_id = input_path.stem.upper().replace(" ", "_")

    # Create extraction directory
    extraction_dir = Path(args.extraction_dir)
    extraction_dir.mkdir(parents=True, exist_ok=True)

    # Initialize OCR processor
    print("Initializing OCR processor...")
    print(f"  Input: {input_path}")
    print(f"  Deskew: {args.deskew and OPENCV_AVAILABLE}")
    print(f"  DPI: {args.dpi}")
    print(f"  Language: {args.language}")

    processor = OCRProcessor(deskew=args.deskew, dpi=args.dpi, language=args.language)

    # Process file
    try:
        if input_path.suffix.lower() == ".pdf":
            pages_to_extract = args.page if not args.all_pages else None
            print("\nExtracting text from PDF...")
            text, confidence, page_count = processor.extract_text_from_pdf(
                input_path, pages=pages_to_extract
            )
        else:
            # Single image file
            print("\nExtracting text from image...")
            image = Image.open(input_path)
            text, confidence = processor.extract_text_from_image(image)
            page_count = 1

        # Save extracted text
        extracted_text_path = extraction_dir / f"{doc_id}.txt"
        with open(extracted_text_path, "w", encoding="utf-8") as f:
            f.write(text)

        print("\n[OK] Extraction complete")
        print(f"  Pages processed: {page_count}")
        print(f"  Average confidence: {confidence:.2%}")
        print(f"  Characters extracted: {len(text)}")
        print(f"  Output: {extracted_text_path}")

        # Update manifest if specified
        if args.out:
            manifest_path = Path(args.out)
            update_manifest(
                manifest_path, doc_id, extracted_text_path, page_count, confidence
            )
            print(f"  Updated manifest: {manifest_path}")

    except Exception as e:
        print(f"\nError during OCR processing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
