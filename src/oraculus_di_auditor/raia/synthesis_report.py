"""Render a ``RAIAResult`` to Markdown / DOCX for WF-010 distribution.

Two rendering paths:

  1. ``render_markdown_template(result, template_dir)`` — uses Jinja2
     with ``templates/raia_synthesis_report.md``. Primary path for the
     webhook ``/synthesize`` endpoint.
  2. ``render_markdown(result)`` — pure-Python fallback that does not
     require Jinja2 or a templates/ directory. Used when the template
     cannot be loaded (missing dir, missing file) so synthesis never
     becomes unavailable due to a packaging issue.

The DOCX path is deliberately not implemented here — the v2.5.x DOCX
export pipeline lives in ``reporting/format_converters``; follow-on
work will pipe the rendered markdown through ``convert_to_docx()``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oraculus_di_auditor.raia.schemas import RAIAResult

logger = logging.getLogger(__name__)

# Default template directory lookup — walks up from this file to the
# repo root and appends /templates. Works for both editable installs
# and wheel-installed copies as long as the repo layout is preserved.
_DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"
_DEFAULT_TEMPLATE_NAME = "raia_synthesis_report.md"


def render_markdown_template(
    result: RAIAResult,
    template_dir: Path | str | None = None,
    template_name: str = _DEFAULT_TEMPLATE_NAME,
) -> str:
    """Render via Jinja2 + ``templates/raia_synthesis_report.md``.

    Falls through to ``render_markdown`` (the pure-Python path) on
    any template-resolution failure so callers always get content
    back. Logs a warning so operators can investigate. Missing
    Jinja2 is *not* treated as an error — synthesis still works
    without the templating dependency.
    """
    try:
        import jinja2
    except ImportError:
        logger.warning(
            "RAIA render: Jinja2 not installed — using pure-Python renderer."
        )
        return render_markdown(result)

    tpl_dir = Path(template_dir) if template_dir else _DEFAULT_TEMPLATE_DIR
    tpl_path = tpl_dir / template_name
    if not tpl_path.is_file():
        logger.warning(
            "RAIA render: template %s not found — using pure-Python renderer.",
            tpl_path,
        )
        return render_markdown(result)

    try:
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(tpl_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,
        )
        template = env.get_template(template_name)
        # Template references `result.*` — pass the RAIAResult itself
        # so attribute access works in Jinja.
        return template.render(result=result)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "RAIA render: Jinja2 render failed (%s) — using pure-Python renderer.",
            exc,
        )
        return render_markdown(result)


def render_markdown(result: RAIAResult) -> str:
    """Render a ``RAIAResult`` to a self-contained Markdown string.

    Sections:
      1. Header with synthesis ID + timestamp + jurisdiction list.
      2. Per-jurisdiction summary tables.
      3. Cross-jurisdiction patterns, strongest first.
      4. Tier 3 notes (if include_tier3=True).
      5. Missing-jurisdictions appendix.

    No external dependencies — the string-building path is deliberate
    so this can execute in minimal environments (e.g. a webhook
    responder on a slim container).
    """
    lines: list[str] = []
    lines.append("# R.A.I.A. Cross-Jurisdiction Synthesis Report")
    lines.append("")
    lines.append(f"**Synthesis ID:** `{result.synthesis_id}`  ")
    lines.append(f"**Generated:** {result.generated_at}  ")
    lines.append(
        f"**Jurisdictions analysed:** "
        f"{', '.join(s.jurisdiction_id for s in result.jurisdictions) or 'none'}  "
    )
    if result.missing_jurisdictions:
        lines.append(
            f"**Missing (no persisted data):** "
            f"{', '.join(result.missing_jurisdictions)}  "
        )
    lines.append(
        f"**Tier 3 recursive synthesis:** "
        f"{'included' if result.include_tier3 else 'not included'}"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## Per-Jurisdiction Summary")
    lines.append("")
    if not result.jurisdictions:
        lines.append("*No jurisdictions loaded.*")
    else:
        lines.append(
            "| Jurisdiction | Documents | Analyses | Anomalies | "
            "Avg Score | Top Layer |"
        )
        lines.append(
            "|--------------|-----------|----------|-----------|"
            "-----------|-----------|"
        )
        for s in result.jurisdictions:
            top_layer = ""
            if s.layer_counts:
                top_layer = max(s.layer_counts.items(), key=lambda kv: kv[1])[0]
            lines.append(
                f"| {s.jurisdiction_id} | {s.document_count} | "
                f"{s.analysis_count} | {s.total_anomalies} | "
                f"{s.scalar_score_avg:.3f} | {top_layer or '—'} |"
            )
        lines.append("")

    lines.append("## Cross-Jurisdiction Patterns")
    lines.append("")
    if not result.patterns:
        lines.append(
            "*No cross-jurisdiction patterns detected. At least two "
            "jurisdictions with persisted data are required.*"
        )
    else:
        for p in result.patterns:
            lines.append(f"### {p.pattern_id}")
            lines.append("")
            lines.append(f"- **Type:** `{p.pattern_type}`")
            lines.append(
                f"- **Confidence:** {p.confidence:.2f} "
                f"({len(p.jurisdictions_affected)} of "
                f"{len(result.jurisdictions)} jurisdictions)"
            )
            lines.append(f"- **Jurisdictions:** {', '.join(p.jurisdictions_affected)}")
            lines.append(f"- **Description:** {p.description}")
            lines.append("")
    lines.append("")

    if result.include_tier3 and result.tier3_notes:
        lines.append("## Tier 3 Notes")
        lines.append("")
        for key, value in result.tier3_notes.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

    return "\n".join(lines) + "\n"


def write_markdown(result: RAIAResult, path: Path | str) -> Path:
    """Serialise ``render_markdown(result)`` to disk, UTF-8 encoded."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_markdown(result), encoding="utf-8")
    return out


__all__ = ["render_markdown", "render_markdown_template", "write_markdown"]
