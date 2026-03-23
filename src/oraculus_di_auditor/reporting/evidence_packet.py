"""Evidence packet generator for ODIA audit results.

Creates a ZIP archive containing all materials needed to brief a city council
member, journalist, or oversight body about the audit findings.

Contents:
    README.md              — explains the packet structure
    audit_report.md        — full findings in Markdown
    audit_report.html      — HTML version for browsers
    executive_summary.md   — 1-2 page briefing document
    document_manifest.json — analyzed documents with SHA-256 hashes
    findings/F-NNN_*.md    — one sheet per finding
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime
from typing import Any


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_evidence_packet(audit_results: dict[str, Any]) -> bytes:
    """Build a ZIP evidence packet from completed audit results.

    Args:
        audit_results: The ``results`` dict returned by a completed audit job
            (contains findings, severity_summary, document_manifest, etc.)

    Returns:
        Raw ZIP bytes suitable for streaming as an HTTP response.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        report_md = _build_audit_report_md(audit_results)

        zf.writestr("README.md", _build_readme(audit_results))
        zf.writestr("audit_report.md", report_md)
        zf.writestr("audit_report.html", _md_to_html(report_md))
        zf.writestr("executive_summary.md", _build_executive_summary(audit_results))
        zf.writestr(
            "document_manifest.json",
            json.dumps(audit_results.get("document_manifest", []), indent=2),
        )

        findings = audit_results.get("findings", [])
        # Sort critical first
        _sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(
            findings,
            key=lambda f: _sev_order.get(f.get("severity", "low"), 3),
        )

        for i, finding in enumerate(sorted_findings, 1):
            sev = finding.get("severity", "unknown")
            layer = finding.get("layer", "unknown").replace("/", "-")
            filename = f"findings/F-{i:03d}_{sev}_{layer}.md"
            zf.writestr(filename, _build_finding_sheet(i, finding))

    return buf.getvalue()


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------


def _build_readme(results: dict[str, Any]) -> str:
    doc_count = results.get("document_count", 0)
    finding_count = results.get("finding_count", 0)
    generated = results.get("generated_at", datetime.now(UTC).isoformat())

    return f"""# O.D.I.A. Evidence Packet

Generated: {generated}
Documents analyzed: {doc_count}
Total findings: {finding_count}

## What is in this packet?

| File | Description |
|------|-------------|
| `audit_report.md` | Full audit report with all findings (Markdown) |
| `audit_report.html` | Same report formatted for web browsers |
| `executive_summary.md` | Brief 1-2 page summary for decision makers |
| `document_manifest.json` | List of analyzed documents with SHA-256 checksums |
| `findings/F-NNN_*.md` | Individual finding sheet for each anomaly detected |

## How to use this packet

1. Start with `executive_summary.md` for a quick overview.
2. Review `audit_report.md` for the full list of findings with technical detail.
3. Use the `findings/` sheets to brief individual stakeholders on specific issues.
4. Verify document authenticity against hashes in `document_manifest.json`.

## About O.D.I.A.

Oraculus DI Auditor is an open-source civic accountability platform.
Source: https://github.com/SynTechRev/ODIA
License: MIT
"""


def _build_executive_summary(results: dict[str, Any]) -> str:
    doc_count = results.get("document_count", 0)
    finding_count = results.get("finding_count", 0)
    generated = results.get("generated_at", datetime.now(UTC).isoformat())
    sev = results.get("severity_summary", {})
    findings = results.get("findings", [])

    # Top 3 critical/high findings
    top_findings = [f for f in findings if f.get("severity") in ("critical", "high")][:3]

    lines = [
        "# Executive Summary — O.D.I.A. Audit",
        "",
        f"**Date**: {generated[:10]}  ",
        f"**Documents Reviewed**: {doc_count}  ",
        f"**Anomalies Detected**: {finding_count}  ",
        "",
        "## Key Statistics",
        "",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| Critical | {sev.get('critical', 0)} |",
        f"| High     | {sev.get('high', 0)} |",
        f"| Medium   | {sev.get('medium', 0)} |",
        f"| Low      | {sev.get('low', 0)} |",
        "",
    ]

    if top_findings:
        lines += ["## Most Significant Findings", ""]
        for i, f in enumerate(top_findings, 1):
            severity = f.get("severity", "unknown").upper()
            plain = f.get("plain_summary") or f.get("issue", "Unknown anomaly")
            action = f.get("plain_action") or "Review recommended."
            layer = f.get("layer", "unknown")
            doc_id = f.get("document_id", "unknown")

            lines += [
                f"### {i}. [{severity}] {layer} — {doc_id}",
                "",
                plain,
                "",
                f"**Recommended action**: {action}",
                "",
            ]

    lines += [
        "## Recommended Next Steps",
        "",
        "1. Review the individual finding sheets in the `findings/` directory.",
        "2. Prioritize critical and high-severity findings for immediate attention.",
        "3. Consult legal counsel on findings involving constitutional or jurisdictional issues.",
        "4. Request corrected records or additional documentation as recommended in each finding.",
        "5. Consider referring patterns of concern to the appropriate oversight body.",
        "",
        "---",
        "",
        "_This summary was generated automatically by O.D.I.A. (Oraculus DI Auditor)._",
        "_All findings should be reviewed by qualified professionals before taking action._",
    ]

    return "\n".join(lines)


def _build_audit_report_md(results: dict[str, Any]) -> str:
    doc_count = results.get("document_count", 0)
    finding_count = results.get("finding_count", 0)
    generated = results.get("generated_at", datetime.now(UTC).isoformat())
    sev = results.get("severity_summary", {})

    lines = [
        "# O.D.I.A. Audit Report",
        "",
        f"**Generated**: {generated}  ",
        f"**Documents analyzed**: {doc_count}  ",
        f"**Total findings**: {finding_count}  ",
        "",
        "## Severity Summary",
        "",
    ]

    for level in ("critical", "high", "medium", "low"):
        count = sev.get(level, 0)
        if count:
            lines.append(f"- **{level.upper()}**: {count}")

    lines += ["", "---", "", "## Findings", ""]

    findings = sorted(
        results.get("findings", []),
        key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
            f.get("severity", "low"), 3
        ),
    )

    for i, f in enumerate(findings, 1):
        severity = f.get("severity", "unknown").upper()
        layer = f.get("layer", "unknown")
        doc_id = f.get("document_id", "unknown")

        lines += [
            f"### Finding {i:03d} — [{severity}] {f.get('issue', 'Unknown issue')}",
            "",
            f"**Detector**: `{layer}`  ",
            f"**Document**: `{doc_id}`  ",
            f"**Severity**: {severity}  ",
            "",
        ]

        if "plain_summary" in f:
            lines += [
                f"**Summary**: {f['plain_summary']}  ",
                "",
                f"**Why it matters**: {f.get('plain_impact', '')}  ",
                "",
                f"**Recommended action**: {f.get('plain_action', '')}  ",
                "",
            ]
        else:
            issue = f.get("issue", "")
            if issue:
                lines += [f"_{issue}_", ""]

        details = f.get("details", {})
        if details:
            lines += ["**Technical details**:  ", ""]
            for k, v in details.items():
                lines.append(f"- `{k}`: {v}")
            lines.append("")

        lines += ["---", ""]

    return "\n".join(lines)


def _build_finding_sheet(index: int, finding: dict[str, Any]) -> str:
    severity = finding.get("severity", "unknown").upper()
    layer = finding.get("layer", "unknown")
    doc_id = finding.get("document_id", "unknown")
    issue = finding.get("issue", "Unknown issue")

    lines = [
        f"# Finding F-{index:03d}",
        "",
        f"**Severity**: {severity}  ",
        f"**Detector**: {layer}  ",
        f"**Document**: {doc_id}  ",
        f"**Finding ID**: `{finding.get('id', 'N/A')}`  ",
        "",
        "---",
        "",
        f"## Issue",
        "",
        issue,
        "",
    ]

    if "plain_summary" in finding:
        lines += [
            "## Plain-Language Explanation",
            "",
            f"**What was found**: {finding['plain_summary']}",
            "",
            f"**Why it matters**: {finding.get('plain_impact', '')}",
            "",
            f"**What to do**: {finding.get('plain_action', '')}",
            "",
        ]

    details = finding.get("details", {})
    if details:
        lines += ["## Technical Evidence", "", "```json"]
        lines.append(json.dumps(details, indent=2, default=str))
        lines += ["```", ""]

    lines += [
        "---",
        "",
        "_Generated by O.D.I.A. — for reference only; consult qualified counsel before acting._",
    ]

    return "\n".join(lines)


def _md_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML. Falls back to a <pre> block if markdown pkg absent."""
    try:
        import markdown as md_lib  # type: ignore[import]

        body = md_lib.markdown(markdown_text, extensions=["tables", "fenced_code"])
    except ImportError:
        escaped = (
            markdown_text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        body = f"<pre>{escaped}</pre>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>O.D.I.A. Audit Report</title>
  <style>
    body {{ font-family: Georgia, serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
    h1, h2, h3 {{ font-family: Arial, sans-serif; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 0.5rem; text-align: left; }}
    th {{ background: #f5f5f5; }}
    code, pre {{ background: #f8f8f8; padding: 0.2rem 0.4rem; border-radius: 3px; }}
    hr {{ border: none; border-top: 1px solid #ddd; margin: 1.5rem 0; }}
  </style>
</head>
<body>
{body}
</body>
</html>"""
