"""OCR Engine — Optical Character Recognition for image-embedded PDFs.

Uses pymupdf (fitz) for PDF-to-image rendering and pytesseract for text
extraction. No Poppler dependency required.

Tesseract must be installed:
  Windows: https://github.com/UB-Mannheim/tesseract/wiki
           (default: %LOCALAPPDATA%\\Programs\\Tesseract-OCR)
  macOS:   brew install tesseract
  Linux:   apt install tesseract-ocr
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path

_MIN_TEXT_CHARS_PER_PAGE = 50  # pages with fewer chars are treated as image-only
_MAX_OCR_PIXELS = 30_000_000  # ~5477×5477px — images above this are downsampled


# ---------------------------------------------------------------------------
# Tesseract discovery and configuration
# ---------------------------------------------------------------------------


def _tesseract_cmd() -> str | None:
    """Find the tesseract executable — PATH first, then Windows default."""
    found = shutil.which("tesseract")
    if found:
        return found
    win_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Programs"
        / "Tesseract-OCR"
        / "tesseract.exe"
    )
    return str(win_path) if win_path.exists() else None


def _configure() -> bool:
    """Point pytesseract at the tesseract binary. Returns True if ready."""
    try:
        import pytesseract

        cmd = _tesseract_cmd()
        if cmd is None:
            return False
        pytesseract.pytesseract.tesseract_cmd = cmd
        return True
    except ImportError:
        return False


def is_available() -> bool:
    """Return True when the full OCR stack is ready (pytesseract + fitz + Tesseract)."""
    if not _configure():
        return False
    try:
        import fitz  # noqa: F401
        from PIL import Image  # noqa: F401

        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------


def _cap_image(img: object) -> object:
    """Downsample img to _MAX_OCR_PIXELS if it exceeds the cap.

    A letter page at 300 DPI is ~8.4 MP — well under the cap, no change.
    A 150 MP large-format scan is reduced to ~30 MP — still legible for
    Tesseract, but processing time drops from many minutes to seconds.
    """
    from PIL import Image  # type: ignore[import]

    w, h = img.size  # type: ignore[attr-defined]
    if w * h <= _MAX_OCR_PIXELS:
        return img
    scale = (_MAX_OCR_PIXELS / (w * h)) ** 0.5
    return img.resize(  # type: ignore[return-value]
        (max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS
    )


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


def detect_scanned_pages(pdf_path: Path) -> list[int]:
    """Return 1-based page numbers that appear to be image-only.

    Uses pdfplumber to measure extracted-text density per page.
    Pages with fewer than _MIN_TEXT_CHARS_PER_PAGE characters are flagged.
    Falls back to marking all pages if pdfplumber cannot open the file.
    """
    try:
        import pdfplumber  # type: ignore[import]

        scanned: list[int] = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if len(text.strip()) < _MIN_TEXT_CHARS_PER_PAGE:
                    scanned.append(i)
        return scanned
    except Exception:
        pass

    # Fallback: use pymupdf page count and flag everything
    try:
        import fitz

        doc = fitz.open(str(pdf_path))
        return list(range(1, len(doc) + 1))
    except Exception:
        return []


# ---------------------------------------------------------------------------
# OCR functions
# ---------------------------------------------------------------------------


def ocr_pdf_page(pdf_path: Path, page_num: int) -> str:
    """OCR a single page (1-based). Returns extracted text or empty string."""
    if not _configure():
        return ""
    try:
        import fitz
        import pytesseract
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = None  # cap managed by _cap_image
        doc = fitz.open(str(pdf_path))
        page = doc[page_num - 1]
        # 300 DPI gives reliable accuracy for government document fonts
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = _cap_image(Image.open(io.BytesIO(pix.tobytes("png"))))
        return pytesseract.image_to_string(img, lang="eng")
    except Exception:
        return ""


def ocr_full_pdf(pdf_path: Path) -> str:
    """OCR all pages of a PDF. Returns concatenated text from all pages.

    Renders each page at 300 DPI via pymupdf (no Poppler required),
    then extracts text via pytesseract.
    """
    if not _configure():
        return ""
    try:
        import fitz
        import pytesseract
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = None  # cap managed by _cap_image
        doc = fitz.open(str(pdf_path))
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pages: list[str] = []
        for page in doc:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = _cap_image(Image.open(io.BytesIO(pix.tobytes("png"))))
            page_text = pytesseract.image_to_string(img, lang="eng")
            if page_text.strip():
                pages.append(page_text)
        return "\n\n".join(pages)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# CLI — for standalone use and testing
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="OCR a PDF file via Tesseract + pymupdf"
    )
    parser.add_argument("pdf", nargs="?", default=None, help="Path to PDF file")
    parser.add_argument(
        "--page", type=int, default=None, help="Single page to OCR (1-based)"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check OCR stack availability and exit"
    )
    args = parser.parse_args()

    if args.check:
        if is_available():
            print(f"OCR ready — tesseract at: {_tesseract_cmd()}")
        else:
            print("OCR NOT ready. Install: pip install pymupdf pytesseract Pillow")
            print(
                "Then install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
            )
        return

    path = Path(args.pdf)
    if not path.exists():
        print(f"File not found: {path}")
        return

    if not is_available():
        print("OCR stack not ready. Run with --check for details.")
        return

    if args.page:
        print(ocr_pdf_page(path, args.page))
    else:
        print(ocr_full_pdf(path))


if __name__ == "__main__":
    main()
