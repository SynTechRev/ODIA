"""Render a ``RAIAResult`` to Markdown / DOCX for WF-010 distribution.

C5.2 lands a pure-Python markdown renderer (no Jinja2 dependency for
the default path) so callers can get a human-readable report without a
templates/ file. C5.3 swaps the primary path to a Jinja2 template at
``templates/raia_synthesis_report.md`` and wires the webhook
``/synthesize`` endpoint to produce and return the rendered output.

The DOCX path is deliberately not implemented here yet — the v2.5.x
DOCX export pipeline already lives in ``reporting/format_converters``;
C5.3 reuses that via the template_engine rather than re-implementing.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oraculus_di_auditor.raia.schemas import RAIAResult


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


__all__ = ["render_markdown", "write_markdown"]
