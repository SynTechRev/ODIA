"""Format conversion utilities for ODIA audit reports.

Converts rendered Markdown reports to PDF, DOCX, and HTML for professional
distribution.  All converters degrade gracefully: if the required external
tool is unavailable the function returns None and logs a warning rather than
raising an exception.

Conversion priority:
  HTML  — pandoc → Python ``markdown`` library
  PDF   — pandoc → weasyprint → wkhtmltopdf
  DOCX  — pandoc only
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from oraculus_di_auditor.reporting.models import AuditReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Low-level converters
# ---------------------------------------------------------------------------


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML.

    Uses pandoc if available, falls back to the Python ``markdown`` library.

    Args:
        markdown_text: Markdown source string.

    Returns:
        HTML string.  Never raises — falls back to a ``<pre>``-wrapped
        representation if neither pandoc nor the markdown library is present.
    """
    # Try pandoc first.
    if shutil.which("pandoc"):
        try:
            result = subprocess.run(
                ["pandoc", "--from=markdown", "--to=html"],
                input=markdown_text,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
            return result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.warning("pandoc failed during HTML conversion: %s", exc)

    # Try Python markdown library.
    try:
        import markdown as md_lib  # type: ignore[import-untyped]

        return md_lib.markdown(markdown_text, extensions=["tables", "fenced_code"])
    except ImportError:
        logger.warning(
            "Neither pandoc nor the Python 'markdown' library is available. "
            "Returning pre-wrapped HTML fallback."
        )

    escaped = markdown_text.replace("&", "&amp;").replace("<", "&lt;")
    return f"<pre>{escaped}</pre>"


def markdown_to_pdf(
    markdown_text: str,
    output_path: Path | str,
    title: str = "ODIA Audit Report",
) -> Path | None:
    """Convert Markdown to PDF.

    Tries pandoc first, then weasyprint, then wkhtmltopdf.

    Args:
        markdown_text: Markdown source string.
        output_path: Destination ``.pdf`` file path.
        title: Document title embedded in the PDF metadata.

    Returns:
        Resolved Path of the written file on success, ``None`` if no PDF
        converter is available.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # 1. pandoc
    if shutil.which("pandoc"):
        try:
            subprocess.run(
                [
                    "pandoc",
                    "--from=markdown",
                    "--to=pdf",
                    f"--metadata=title:{title}",
                    f"--output={out}",
                ],
                input=markdown_text,
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
            logger.info("PDF written via pandoc: %s", out)
            return out.resolve()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.warning("pandoc PDF conversion failed: %s", exc)

    # 2. weasyprint
    try:
        import weasyprint  # type: ignore[import-untyped]

        html = markdown_to_html(markdown_text)
        weasyprint.HTML(string=html).write_pdf(str(out))
        logger.info("PDF written via weasyprint: %s", out)
        return out.resolve()
    except ImportError:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("weasyprint PDF conversion failed: %s", exc)

    # 3. wkhtmltopdf
    if shutil.which("wkhtmltopdf"):
        try:
            html = markdown_to_html(markdown_text)
            html_tmp = out.with_suffix(".tmp.html")
            html_tmp.write_text(html, encoding="utf-8")
            subprocess.run(
                ["wkhtmltopdf", str(html_tmp), str(out)],
                capture_output=True,
                timeout=60,
                check=True,
            )
            html_tmp.unlink(missing_ok=True)
            logger.info("PDF written via wkhtmltopdf: %s", out)
            return out.resolve()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            logger.warning("wkhtmltopdf failed: %s", exc)

    logger.warning(
        "No PDF converter available (pandoc, weasyprint, wkhtmltopdf). "
        "Install one to enable PDF export."
    )
    return None


def markdown_to_docx(
    markdown_text: str,
    output_path: Path | str,
) -> Path | None:
    """Convert Markdown to DOCX via pandoc.

    Args:
        markdown_text: Markdown source string.
        output_path: Destination ``.docx`` file path.

    Returns:
        Resolved Path of the written file on success, ``None`` if pandoc is
        not available.
    """
    if not shutil.which("pandoc"):
        logger.warning("pandoc not found. Install pandoc to enable DOCX export.")
        return None

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                "pandoc",
                "--from=markdown",
                "--to=docx",
                f"--output={out}",
            ],
            input=markdown_text,
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )
        logger.info("DOCX written via pandoc: %s", out)
        return out.resolve()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.warning("pandoc DOCX conversion failed: %s", exc)
        return None


def get_available_formats() -> list[str]:
    """Return list of available output formats based on installed tools.

    Always includes ``"markdown"`` and ``"json"``.  Conditionally includes
    ``"html"``, ``"pdf"``, and ``"docx"`` based on what is installed.

    Returns:
        Sorted list of format name strings.
    """
    formats = ["json", "markdown"]

    # HTML is available if pandoc or the markdown library is present.
    has_pandoc = bool(shutil.which("pandoc"))
    has_md_lib = _can_import("markdown")
    if has_pandoc or has_md_lib:
        formats.append("html")

    # PDF requires pandoc, weasyprint, or wkhtmltopdf.
    has_weasyprint = _can_import("weasyprint")
    has_wkhtmltopdf = bool(shutil.which("wkhtmltopdf"))
    if has_pandoc or has_weasyprint or has_wkhtmltopdf:
        formats.append("pdf")

    # DOCX requires pandoc.
    if has_pandoc:
        formats.append("docx")

    return sorted(formats)


# ---------------------------------------------------------------------------
# High-level export
# ---------------------------------------------------------------------------


def export_report(
    report: AuditReport,
    output_dir: Path | str,
    formats: list[str] | None = None,
    template_dir: Path | str = "templates",
    template_name: str = "audit_report.md",
) -> dict[str, Path]:
    """Export an AuditReport in multiple formats.

    Args:
        report: The AuditReport to export.
        output_dir: Directory to write files to (created if absent).
        formats: List of formats to generate.  Defaults to all available.
            Options: ``"json"``, ``"markdown"``, ``"html"``, ``"pdf"``,
            ``"docx"``.
        template_dir: Path to Jinja2 templates directory.
        template_name: Template filename to use for Markdown rendering.

    Returns:
        Dict mapping format name to the resolved output Path.
        e.g., ``{"json": Path("…/RPT-XYZ_report.json"), …}``
    """
    from oraculus_di_auditor.reporting.template_engine import ReportTemplateEngine

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    available = get_available_formats()
    requested = {f.lower() for f in (formats or available)}
    stem = f"{report.report_id}_report"
    written: dict[str, Path] = {}

    if "json" in requested:
        written["json"] = _export_json(report, out_dir, stem)

    md_formats = requested & {"markdown", "html", "pdf", "docx"}
    if md_formats:
        engine = ReportTemplateEngine(template_dir=template_dir)
        md = engine.render_markdown(report, template_name=template_name)
        title = report.title or "ODIA Audit Report"
        written.update(_export_md_formats(md, md_formats, out_dir, stem, title))

    for fmt in requested - {"json", "markdown", "html", "pdf", "docx"}:
        logger.warning("Format '%s' not available — skipping.", fmt)

    return written


def _export_md_formats(
    md: str,
    formats: set[str],
    out_dir: Path,
    stem: str,
    title: str,
) -> dict[str, Path]:
    """Render all Markdown-derived formats from a pre-rendered Markdown string."""
    written: dict[str, Path] = {}
    if "markdown" in formats:
        written["markdown"] = _export_markdown(md, out_dir, stem)
    if "html" in formats:
        written["html"] = _export_html(md, out_dir, stem)
    if "pdf" in formats:
        result = _export_pdf(md, out_dir, stem, title)
        if result:
            written["pdf"] = result
    if "docx" in formats:
        result = _export_docx(md, out_dir, stem)
        if result:
            written["docx"] = result
    return written


def _export_json(report: AuditReport, out_dir: Path, stem: str) -> Path:
    """Write report as JSON and return the path."""
    path = out_dir / f"{stem}.json"
    _write_json(report, path)
    print(f"[OK] JSON  → {path}")
    return path


def _export_markdown(md: str, out_dir: Path, stem: str) -> Path:
    """Write rendered Markdown to disk and return the path."""
    path = out_dir / f"{stem}.md"
    path.write_text(md, encoding="utf-8")
    print(f"[OK] Markdown → {path}")
    return path


def _export_html(md: str, out_dir: Path, stem: str) -> Path:
    """Convert Markdown to HTML, write to disk, and return the path."""
    path = out_dir / f"{stem}.html"
    html = markdown_to_html(md)
    path.write_text(html, encoding="utf-8")
    print(f"[OK] HTML  → {path}")
    return path


def _export_pdf(md: str, out_dir: Path, stem: str, title: str) -> Path | None:
    """Convert Markdown to PDF and return the path, or None if unavailable."""
    path = out_dir / f"{stem}.pdf"
    result = markdown_to_pdf(md, path, title=title)
    if result:
        print(f"[OK] PDF   → {result}")
        return result
    print("[SKIP] PDF — no converter available")
    return None


def _export_docx(md: str, out_dir: Path, stem: str) -> Path | None:
    """Convert Markdown to DOCX and return the path, or None if unavailable."""
    path = out_dir / f"{stem}.docx"
    result = markdown_to_docx(md, path)
    if result:
        print(f"[OK] DOCX  → {result}")
        return result
    print("[SKIP] DOCX — pandoc not available")
    return None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _can_import(module_name: str) -> bool:
    """Return True if *module_name* can be imported."""
    import importlib.util

    return importlib.util.find_spec(module_name) is not None


def _write_json(report: AuditReport, path: Path) -> None:
    """Serialise *report* to a pretty-printed JSON file."""
    data: dict[str, Any] = json.loads(report.model_dump_json())
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
