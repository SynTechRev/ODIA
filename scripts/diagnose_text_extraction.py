"""Diagnose silent text-extraction failures in a corpus.

Run text extraction against every PDF in a directory and report the
non-whitespace character count per document. Documents below
``THRESHOLD_CHARS`` are flagged as silent-failure candidates — they
are almost certainly scanned PDFs without an OCR text layer, and the
detector pipeline will emit only noise-floor findings on them.

Usage::

    python scripts/diagnose_text_extraction.py /path/to/corpus
    python scripts/diagnose_text_extraction.py /path/to/corpus --use-ocr

Exit codes:
    0 — corpus scanned, no silent-failure SHAs detected
    1 — silent-failure SHAs detected (count printed to stderr)
    2 — invalid arguments / corpus directory not found

The script reuses ``oraculus_di_auditor.ingestion.engine.extract_text_from_pdf``
when ``--use-ocr`` is passed so the diagnostic exercises the same
pypdf+pytesseract path the audit pipeline uses. Without ``--use-ocr``
it runs the pypdf-only fast path so silent-failure candidates are the
documents that *would have needed* OCR fallback.

Exists in service of v2.9.3 Track A — the Run-12 evidence packet
revealed 8 of 38 unique SHAs (21%) were silently blind because no
OCR fallback fired during their audit. This script reproduces that
observation before touching detector logic so the root cause is
provable, not just inferred.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THRESHOLD_CHARS = 500  # match ingestion.engine._OCR_MIN_TEXT_LENGTH


def _extract_pdftotext_only(pdf_path: Path) -> int:
    """Pure pypdf extraction — no OCR fallback. Returns char count or -1."""
    try:
        from pypdf import PdfReader
    except ImportError:
        print(
            "ERROR: pypdf not installed. Install with: pip install pypdf",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        reader = PdfReader(str(pdf_path))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        return len("\n\n".join(t for t in text_parts if t).strip())
    except Exception as exc:
        print(f"  ! extraction error on {pdf_path.name}: {exc}", file=sys.stderr)
        return -1


def _extract_with_ocr(pdf_path: Path) -> int:
    """Full pipeline extraction including OCR fallback. Returns char count."""
    try:
        from oraculus_di_auditor.ingestion.engine import extract_text_from_pdf
    except ImportError as exc:
        print(f"ERROR: cannot import extract_text_from_pdf: {exc}", file=sys.stderr)
        sys.exit(2)
    try:
        return len(extract_text_from_pdf(pdf_path).strip())
    except Exception as exc:
        print(f"  ! extraction error on {pdf_path.name}: {exc}", file=sys.stderr)
        return -1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diagnose silent text-extraction failures in a PDF corpus."
    )
    ap.add_argument("corpus_dir", type=Path, help="Directory containing PDFs to scan")
    ap.add_argument(
        "--use-ocr",
        action="store_true",
        help="Use the full extract_text_from_pdf path (pypdf + OCR fallback). "
        "Without this flag, only pypdf is used — silent-failure candidates "
        "are documents that *would have needed* OCR.",
    )
    ap.add_argument(
        "--threshold",
        type=int,
        default=THRESHOLD_CHARS,
        help=f"Char-count threshold for silent failure (default: {THRESHOLD_CHARS})",
    )
    args = ap.parse_args()

    if not args.corpus_dir.exists() or not args.corpus_dir.is_dir():
        print(f"ERROR: not a directory: {args.corpus_dir}", file=sys.stderr)
        return 2

    pdfs = sorted(args.corpus_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs found in {args.corpus_dir}", file=sys.stderr)
        return 0

    extractor = _extract_with_ocr if args.use_ocr else _extract_pdftotext_only
    label = "pypdf+ocr" if args.use_ocr else "pypdf-only"

    print(f"# Text-extraction diagnostic ({label})")
    print(f"# Corpus: {args.corpus_dir}")
    print(f"# Threshold: {args.threshold} non-whitespace chars")
    print()
    print(f"{'chars':>7}  {'size_kb':>8}  filename")

    silent: list[str] = []
    for p in pdfs:
        n = extractor(p)
        size_kb = p.stat().st_size // 1024
        is_silent = 0 <= n < args.threshold
        flag = " [SILENT]" if is_silent else ""
        print(f"{n:>7}  {size_kb:>8}  {p.name}{flag}")
        if is_silent:
            silent.append(p.name)

    print()
    print(
        f"Silent failures: {len(silent)}/{len(pdfs)} "
        f"({100 * len(silent) / len(pdfs):.1f}%)"
    )
    if silent:
        print()
        print("Affected documents (likely image-only PDFs):")
        for name in silent:
            print(f"  - {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
