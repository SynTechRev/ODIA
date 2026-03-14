"""Template rendering engine for ODIA audit reports.

Renders AuditReport models into formatted documents using Jinja2 templates.
Supports Markdown output (primary), HTML conversion via pandoc or basic
fallback, and writing rendered output directly to disk.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import jinja2

if TYPE_CHECKING:
    from oraculus_di_auditor.reporting.models import AuditReport


class ReportTemplateEngine:
    """Renders AuditReport models into formatted documents."""

    def __init__(self, template_dir: Path | str = "templates") -> None:
        """Load Jinja2 environment from template directory.

        Args:
            template_dir: Path to the directory containing Jinja2 templates.
                Defaults to ``"templates"`` (relative to the working directory).
        """
        self.template_dir = Path(template_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_markdown(
        self,
        report: AuditReport,
        template_name: str = "audit_report.md",
    ) -> str:
        """Render report to Markdown string.

        Args:
            report: Populated AuditReport instance.
            template_name: Template filename inside ``template_dir``.

        Returns:
            Rendered Markdown string.

        Raises:
            jinja2.TemplateNotFound: If *template_name* does not exist.
        """
        template = self.env.get_template(template_name)
        return template.render(**self._report_context(report))

    def render_to_file(
        self,
        report: AuditReport,
        output_path: Path | str,
        template_name: str = "audit_report.md",
    ) -> Path:
        """Render report and write to file.

        Args:
            report: Populated AuditReport instance.
            output_path: Destination file path. Parent directories are
                created automatically.
            template_name: Template filename inside ``template_dir``.

        Returns:
            Resolved Path of the written file.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        content = self.render_markdown(report, template_name=template_name)
        out.write_text(content, encoding="utf-8")
        return out.resolve()

    def render_html(
        self,
        report: AuditReport,
        template_name: str = "audit_report.md",
    ) -> str:
        """Render to Markdown then convert to HTML.

        Uses pandoc if available; falls back to a basic ``<pre>``-wrapped
        conversion so callers always receive a non-empty HTML string.

        Args:
            report: Populated AuditReport instance.
            template_name: Template filename inside ``template_dir``.

        Returns:
            HTML string.
        """
        md = self.render_markdown(report, template_name=template_name)
        return _md_to_html(md)

    def available_templates(self) -> list[str]:
        """List all template files in the template directory.

        Returns:
            Sorted list of template filenames (relative to template_dir).
        """
        if not self.template_dir.is_dir():
            return []
        return sorted(
            str(p.relative_to(self.template_dir))
            for p in self.template_dir.rglob("*")
            if p.is_file()
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _report_context(report: AuditReport) -> dict:
        """Convert an AuditReport to a flat Jinja2 template context."""
        findings_by_severity: dict[str, list] = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }
        for f in report.findings:
            bucket = findings_by_severity.get(f.severity.lower(), [])
            bucket.append(f)
            findings_by_severity[f.severity.lower()] = bucket

        return {
            "report": report,
            "findings_by_severity": findings_by_severity,
            "severity_order": ["critical", "high", "medium", "low"],
        }


# ---------------------------------------------------------------------------
# HTML conversion helper
# ---------------------------------------------------------------------------


def _md_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML via pandoc (or basic fallback).

    Tries to call ``pandoc`` as a subprocess. If pandoc is not installed,
    wraps the raw Markdown in a ``<pre>`` block so the caller still gets
    valid HTML.
    """
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
    except (
        FileNotFoundError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ):
        # Fallback: minimal HTML with raw markdown preserved.
        escaped = markdown_text.replace("&", "&amp;").replace("<", "&lt;")
        return f"<pre>{escaped}</pre>"
