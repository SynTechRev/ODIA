"""bulk_ingest.py — Bulk ingest a multi-jurisdiction corpus into oraculus_audit.db.

Usage:
    python scripts/bulk_ingest.py --corpus "C:\\path\\to\\corpus"
    python scripts/bulk_ingest.py --corpus "C:\\path\\to\\corpus" --dry-run
    python scripts/bulk_ingest.py --corpus "C:\\path\\to\\corpus" --jurisdiction exeter

Folder names are auto-mapped to jurisdiction slugs. Pass --jurisdiction to
override for a single-folder run.

Supported file types: PDF, DOCX, DOC, TXT, JSON, XML, HTML/HTM
Skipped automatically: WAV, MP3, JPG, ZIP, PPTX, MHT and other binaries.

After ingestion, run:
    python scripts/build_rag_index.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from oraculus_di_auditor.analysis import analyze_document  # noqa: E402
from oraculus_di_auditor.db.models import Analysis, Anomaly, Document  # noqa: E402
from oraculus_di_auditor.db.session import get_db, init_db  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("bulk_ingest")

# ---------------------------------------------------------------------------
# Text extraction cache — avoids re-reading PDFs/DOCXs on re-runs
# ---------------------------------------------------------------------------

_CACHE_DIR = _REPO_ROOT / ".text_cache"
_CACHE_DIR.mkdir(exist_ok=True)


def _cache_key(path: Path) -> str:
    """Stable key: sha256 of (absolute path + file mtime + file size)."""
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_mtime}|{stat.st_size}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(path: Path) -> str | None:
    cache_file = _CACHE_DIR / (_cache_key(path) + ".txt")
    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8", errors="replace")
    return None


def _cache_set(path: Path, text: str) -> None:
    cache_file = _CACHE_DIR / (_cache_key(path) + ".txt")
    cache_file.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Jurisdiction slug map — folder prefix → canonical slug
# ---------------------------------------------------------------------------

_FOLDER_TO_JURISDICTION: dict[str, str] = {
    "dinu": "dinuba",
    "exet": "exeter",
    "farm": "farmersville",
    "lynd": "lindsay",
    "odia_multi": "multi-jurisdiction",
    "multi": "multi-jurisdiction",
    "port": "porterville",
    "tcso": "tcso",
    "tula": "tulare",
    "vpd": "visalia-pd",
    "wood": "woodlake",
    "visa": "visalia",
    "dinu-odia": "dinuba",
    "exet_odia": "exeter",
    "farm-odia": "farmersville",
    "lynd- odia": "lindsay",
    "lynd-odia": "lindsay",
    "odia_multi_juris": "multi-jurisdiction",
    "port-odia": "porterville",
    "tcso_odia": "tcso",
    "tula-odia": "tulare",
    "vpd_odia": "visalia-pd",
    "wood-odia": "woodlake",
}

_SUPPORTED_EXTS = {".pdf", ".docx", ".doc", ".txt", ".json", ".xml", ".html", ".htm"}

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------


def _extract_pdf(path: Path) -> str | None:
    for lib in ("pdfplumber", "pypdf", "PyPDF2"):
        try:
            if lib == "pdfplumber":
                import pdfplumber  # type: ignore[import]

                with pdfplumber.open(path) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages)
            else:
                mod = __import__(lib)
                reader = mod.PdfReader(str(path))
                return "\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            continue
        except Exception:
            return None
    return None


def _extract_docx(path: Path) -> str | None:
    try:
        from docx import Document as DocxDoc  # type: ignore[import]

        doc = DocxDoc(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return None


def _extract_doc(path: Path) -> str | None:
    # Best-effort: try python-docx first (sometimes works on .doc),
    # then fall back to reading as binary and stripping non-ASCII.
    text = _extract_docx(path)
    if text:
        return text
    try:
        raw = path.read_bytes()
        ascii_text = raw.decode("ascii", errors="ignore")
        return re.sub(r"[^\x20-\x7E\n\t]", " ", ascii_text)
    except Exception:
        return None


def _extract_html(path: Path) -> str:
    try:
        from bs4 import BeautifulSoup

        html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)
    except ImportError:
        html = path.read_text(encoding="utf-8", errors="replace")
        return re.sub(r"<[^>]+>", " ", html)


def _extract_text(path: Path) -> str | None:
    # Check cache first — avoids re-reading PDFs/DOCXs on every re-run
    cached = _cache_get(path)
    if cached is not None:
        return cached or None  # empty string cached means extraction failed

    ext = path.suffix.lower()
    text: str | None = None
    try:
        if ext == ".pdf":
            text = _extract_pdf(path)
        elif ext == ".docx":
            text = _extract_docx(path)
        elif ext == ".doc":
            text = _extract_doc(path)
        elif ext in (".html", ".htm"):
            text = _extract_html(path)
        elif ext == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and ("raw_text" in data or "sections" in data):
                text = data.get("raw_text") or ""
            else:
                text = json.dumps(data, ensure_ascii=False)
        else:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="cp1252", errors="replace")
    except Exception as exc:
        logger.debug("Extraction failed for %s: %s", path.name, exc)

    # Cache result (empty string = extraction failed, so we skip next time too)
    _cache_set(path, text or "")
    return text


# ---------------------------------------------------------------------------
# Jurisdiction detection
# ---------------------------------------------------------------------------


def _jurisdiction_from_folder(folder: Path) -> str:
    name = folder.name.lower().strip()
    if name in _FOLDER_TO_JURISDICTION:
        return _FOLDER_TO_JURISDICTION[name]
    # Try prefix match
    for prefix, slug in _FOLDER_TO_JURISDICTION.items():
        if name.startswith(prefix):
            return slug
    return name  # use folder name as-is if no match


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


def _doc_id(path: Path) -> str:
    h = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    return f"{path.stem[:40]}_{h}"


def _persist(
    session: Any,
    doc_dict: dict[str, Any],
    findings: list[dict[str, Any]],
    jurisdiction: str,
    path: Path,
) -> bool:
    doc_id = doc_dict.get("document_id") or _doc_id(path)

    existing_doc = (
        session.query(Document).filter(Document.document_id == doc_id).first()
    )
    existing_analysis = (
        session.query(Analysis).filter(Analysis.document_id == doc_id).first()
        if existing_doc
        else None
    )

    # Fully processed already — skip
    if existing_doc and existing_analysis:
        return False

    if not existing_doc:
        doc_row = Document(
            document_id=doc_id,
            title=path.stem.replace("_", " ").replace("-", " ").title()[:200],
            document_type=path.suffix.lstrip(".").lower(),
            jurisdiction=jurisdiction,
            updated_at=datetime.now(UTC),
        )
        session.add(doc_row)
        session.flush()

    analysis_row = Analysis(
        document_id=doc_id,
        anomaly_count=len(findings),
        scalar_score=round(1.0 - min(len(findings) * 0.02, 0.5), 4),
        engine_version="3.6.0",
    )
    session.add(analysis_row)
    session.flush()

    for f in findings:
        session.add(
            Anomaly(
                analysis_id=analysis_row.id,
                anomaly_id=f.get("id", "unknown"),
                issue=f.get("issue", "")[:500],
                severity=f.get("severity", "low"),
                layer=f.get("layer", "unknown"),
                details_json=json.dumps(f.get("details", {})),
            )
        )

    session.commit()
    return True


# ---------------------------------------------------------------------------
# Core ingestion loop
# ---------------------------------------------------------------------------


def _ingest_folder(  # noqa: C901
    folder: Path,
    jurisdiction: str,
    dry_run: bool,
    verbose: bool,
) -> dict[str, int]:
    stats = {
        "processed": 0,
        "skipped_ext": 0,
        "skipped_empty": 0,
        "skipped_dup": 0,
        "errors": 0,
        "findings": 0,
    }

    files = sorted(
        f
        for f in folder.rglob("*")
        if f.is_file() and f.suffix.lower() in _SUPPORTED_EXTS
    )

    if not files:
        logger.warning("No supported files found in %s", folder)
        return stats

    logger.info("  %s → '%s': %d files", folder.name, jurisdiction, len(files))

    def _run_one(path: Path, session: Any | None) -> None:
        print(
            f"    [{files.index(path) + 1}/{len(files)}] {path.name[:60]}",
            end="\r",
            flush=True,
        )
        raw_text = _extract_text(path)
        if not raw_text or not raw_text.strip():
            stats["skipped_empty"] += 1
            return
        doc_dict: dict[str, Any] = {
            "document_id": _doc_id(path),
            "title": path.stem,
            "raw_text": raw_text,
            "jurisdiction": jurisdiction,
            "sections": [{"section_id": "main", "content": raw_text}],
        }
        result = analyze_document(doc_dict)
        if dry_run:
            stats["processed"] += 1
            stats["findings"] += result.get("count", 0)
            if verbose:
                logger.info(
                    "DRY-RUN %s → %d findings", path.name, result.get("count", 0)
                )
            return
        try:
            findings = result.get("anomalies", [])
            if _persist(session, doc_dict, findings, jurisdiction, path):
                stats["processed"] += 1
                stats["findings"] += len(findings)
            else:
                stats["skipped_dup"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["errors"] += 1
            logger.warning("Error on %s: %s", path.name, exc)
            if verbose:
                traceback.print_exc()

    if dry_run:
        for path in files:
            _run_one(path, None)
    else:
        with get_db() as session:
            for path in files:
                _run_one(path, session)

    print()  # clear \r line
    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bulk_ingest",
        description="Bulk ingest a multi-jurisdiction corpus into oraculus_audit.db",
    )
    p.add_argument(
        "--corpus",
        required=True,
        metavar="DIR",
        help="Root folder containing jurisdiction subfolders",
    )
    p.add_argument(
        "--jurisdiction",
        default=None,
        metavar="SLUG",
        help="Override jurisdiction for all folders (default: auto-detect from folder name)",  # noqa: E501
    )
    p.add_argument(
        "--folder",
        default=None,
        metavar="NAME",
        help="Process only this subfolder (default: all subfolders)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run detectors but do not write to DB — shows finding counts only",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file detail",
    )
    return p


def main() -> None:
    args = _build_parser().parse_args()
    corpus_root = Path(args.corpus)

    if not corpus_root.exists():
        sys.exit(f"ERROR: corpus path not found: {corpus_root}")

    if not args.dry_run:
        init_db()
        logger.info("Database initialised.")

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logger.info("bulk_ingest %s — corpus: %s", mode, corpus_root)

    # Collect target folders
    if args.folder:
        targets = [corpus_root / args.folder]
    else:
        targets = sorted(d for d in corpus_root.iterdir() if d.is_dir())

    totals = {
        "processed": 0,
        "skipped_ext": 0,
        "skipped_empty": 0,
        "skipped_dup": 0,
        "errors": 0,
        "findings": 0,
    }

    for folder in targets:
        jurisdiction = args.jurisdiction or _jurisdiction_from_folder(folder)
        stats = _ingest_folder(folder, jurisdiction, args.dry_run, args.verbose)
        for k in totals:
            totals[k] += stats[k]
        logger.info(
            "  Done %-20s processed=%d  findings=%d  dups=%d  errors=%d",
            f"'{jurisdiction}'",
            stats["processed"],
            stats["findings"],
            stats["skipped_dup"],
            stats["errors"],
        )

    print()
    logger.info("=" * 60)
    logger.info(
        "TOTAL  processed=%d  findings=%d  dups=%d  errors=%d",
        totals["processed"],
        totals["findings"],
        totals["skipped_dup"],
        totals["errors"],
    )

    if not args.dry_run and totals["processed"] > 0:
        logger.info("")
        logger.info("Next step — rebuild RAG index:")
        logger.info("  python scripts/build_rag_index.py")


if __name__ == "__main__":
    main()
