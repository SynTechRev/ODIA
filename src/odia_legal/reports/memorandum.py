"""Litigation-grade memorandum generator for O.D.I.A.

Converts a set of legal findings (standard anomaly dict shape) into a
formally structured memorandum suitable for filing with oversight bodies,
inclusion in CPRA litigation packets, or submission to elected officials.

Output sections:
  I.   Overview — finding counts by severity
  II.  Table of Authorities — cases and statutes cited, with page-ref stubs
  III. Analysis — findings grouped by severity (high → medium → low)
  IV.  Conclusion — recommended actions

Usage::

    from odia_legal.reports.memorandum import generate_memorandum

    memo = generate_memorandum(
        doc_meta={"title": "ALPR Policy 2024", "agency": "Anytown PD", "date": "2024-03-15"},
        findings=findings_list,
        to_field="City Council Oversight Committee",
    )
    print(memo)        # plain-text
    # or
    print(memo.to_markdown())
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from datetime import date
from typing import Any

from odia_legal.citations.formatter import format_citation
from odia_legal.citations.parser import (
    Citation,
    parse_cal_case,
    parse_cal_code,
    parse_cfr,
    parse_usc,
)

_LINE_WIDTH = 72
_INDENT = "    "
_SECTION_RULE = "─" * _LINE_WIDTH


# ---------------------------------------------------------------------------
# Citation extraction from findings
# ---------------------------------------------------------------------------

# Keys in findings["details"] that may contain citation strings
_CITATION_KEYS = ("statute", "framework", "case", "citation", "regulation")

# Regex to pull bare statute references like "Gov. Code § 7922.000" or
# "2 C.F.R. § 200.303" out of free-text strings in details values
_INLINE_CITE_RE = re.compile(
    r"""
    (?:
        \d{1,2}\s*U\.?\s?S\.?\s?C\.?\s*§\s*\d+[\w.()\-]*   # USC
      | \d{1,2}\s*C\.?\s?F\.?\s?R\.?\s*§\s*[\d.]+          # CFR section
      | \d{1,2}\s*C\.?\s?F\.?\s?R\.?\s*[Pp]art\s*\d+       # CFR part
      | (?:Gov|Pen|Civ|Veh|Ed|Lab|Fam|Corp|Prob|Fin)\.?\s+Code\s*§\s*[\d.]+  # Cal codes
      | Code\s+Civ\.?\s+Proc\.?\s*§\s*[\d.]+               # CCP
      | Welf\.?\s*(?:&|and)\s*Inst\.?\s*Code\s*§\s*[\d.]+  # Welf & Inst
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _extract_citations_from_findings(findings: list[dict[str, Any]]) -> list[Citation]:
    """Pull every recognizable citation out of finding detail fields."""
    seen_canonicals: set[str] = set()
    results: list[Citation] = []

    def _add(cites: list[Citation]) -> None:
        for c in cites:
            if c.canonical not in seen_canonicals:
                seen_canonicals.add(c.canonical)
                results.append(c)

    for finding in findings:
        details = finding.get("details", {})
        # Collect text from known citation-bearing keys
        texts: list[str] = []
        for key in _CITATION_KEYS:
            val = details.get(key)
            if isinstance(val, str):
                texts.append(val)
        # Also scan issue string for inline citations
        texts.append(finding.get("issue", ""))

        for text in texts:
            _add(parse_usc(text))
            _add(parse_cfr(text))
            _add(parse_cal_code(text))
            _add(parse_cal_case(text))

    return results


# ---------------------------------------------------------------------------
# Table of Authorities builder
# ---------------------------------------------------------------------------


def _build_toa(citations: list[Citation]) -> str:
    """Build the Table of Authorities section."""
    cases = [c for c in citations if c.citation_type == "cal_case"]
    statutes = [c for c in citations if c.citation_type in ("usc", "cal_code")]
    regulations = [c for c in citations if c.citation_type == "cfr"]

    lines: list[str] = []

    def _toa_entry(label: str) -> str:
        return f"{_INDENT}{label}"

    if cases:
        lines.append("Cases:")
        for c in cases:
            lines.append(_toa_entry(format_citation(c, "cal_style")))
        lines.append("")

    if statutes:
        lines.append("Statutes:")
        for c in statutes:
            lines.append(_toa_entry(format_citation(c, "cal_style")))
        lines.append("")

    if regulations:
        lines.append("Regulations:")
        for c in regulations:
            lines.append(_toa_entry(format_citation(c, "cal_style")))
        lines.append("")

    if not lines:
        return f"{_INDENT}(No citations identified in findings)"

    return "\n".join(lines).rstrip()


# ---------------------------------------------------------------------------
# Finding renderer
# ---------------------------------------------------------------------------

_SEVERITY_ORDER = ("high", "medium", "low")
_SEVERITY_LABELS = {
    "high": "A. High-Severity Findings",
    "medium": "B. Medium-Severity Findings",
    "low": "C. Low-Severity Findings",
}


def _fmt_finding(finding: dict[str, Any], index: int) -> str:
    """Render a single finding block."""
    sev = finding.get("severity", "?").upper()
    issue = finding.get("issue", "(no issue text)")
    fid = finding.get("id", "")
    details = finding.get("details", {})

    lines: list[str] = [
        f"  {index}. [{sev}] {issue}",
        f"     ID: {fid}",
    ]

    # Emit key detail fields
    for key in ("statute", "framework", "case", "citation", "regulation", "detail"):
        val = details.get(key)
        if val:
            label = key.replace("_", " ").title()
            wrapped = textwrap.fill(
                str(val),
                width=_LINE_WIDTH - 12,
                initial_indent="",
                subsequent_indent="            ",
            )
            lines.append(f"     {label}: {wrapped}")

    return "\n".join(lines)


def _build_analysis(findings: list[dict[str, Any]]) -> str:
    """Build Section III — Analysis."""
    grouped: dict[str, list[dict[str, Any]]] = {s: [] for s in _SEVERITY_ORDER}
    for f in findings:
        sev = f.get("severity", "low")
        if sev in grouped:
            grouped[sev].append(f)

    parts: list[str] = []
    for sev in _SEVERITY_ORDER:
        items = grouped[sev]
        if not items:
            continue
        label = _SEVERITY_LABELS[sev]
        section_lines = [label, ""]
        for i, finding in enumerate(items, 1):
            section_lines.append(_fmt_finding(finding, i))
            section_lines.append("")
        parts.append("\n".join(section_lines).rstrip())

    return "\n\n".join(parts) if parts else f"{_INDENT}No findings to report."


# ---------------------------------------------------------------------------
# Memorandum dataclass
# ---------------------------------------------------------------------------


@dataclass
class Memorandum:
    """A rendered legal memorandum."""

    to_field: str
    from_field: str
    re_field: str
    memo_date: str
    overview: str
    toa: str
    analysis: str
    conclusion: str

    def to_text(self) -> str:
        """Render as plain-text memorandum."""
        return "\n".join(
            [
                "MEMORANDUM",
                "",
                _SECTION_RULE,
                f"TO:   {self.to_field}",
                f"FROM: {self.from_field}",
                f"RE:   {self.re_field}",
                f"DATE: {self.memo_date}",
                _SECTION_RULE,
                "",
                "I. OVERVIEW",
                "",
                self.overview,
                "",
                _SECTION_RULE,
                "",
                "II. TABLE OF AUTHORITIES",
                "",
                self.toa,
                "",
                _SECTION_RULE,
                "",
                "III. ANALYSIS",
                "",
                self.analysis,
                "",
                _SECTION_RULE,
                "",
                "IV. CONCLUSION",
                "",
                self.conclusion,
                "",
                _SECTION_RULE,
            ]
        )

    def to_markdown(self) -> str:
        """Render as Markdown memorandum."""
        return "\n".join(
            [
                "# MEMORANDUM",
                "",
                f"**TO:** {self.to_field}  ",
                f"**FROM:** {self.from_field}  ",
                f"**RE:** {self.re_field}  ",
                f"**DATE:** {self.memo_date}  ",
                "",
                "---",
                "",
                "## I. Overview",
                "",
                self.overview,
                "",
                "## II. Table of Authorities",
                "",
                self.toa,
                "",
                "## III. Analysis",
                "",
                self.analysis,
                "",
                "## IV. Conclusion",
                "",
                self.conclusion,
            ]
        )

    def __str__(self) -> str:
        return self.to_text()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_FROM = "ODIA Legal Analysis Engine (Oraculus Decimus Intellect Analyst)"


def generate_memorandum(
    doc_meta: dict[str, Any],
    findings: list[dict[str, Any]],
    *,
    to_field: str = "Oversight Body / Responsible Agency",
    from_field: str = _DEFAULT_FROM,
    memo_date: str | None = None,
    recommended_actions: list[str] | None = None,
) -> Memorandum:
    """Generate a litigation-grade memorandum from ODIA legal findings.

    Args:
        doc_meta:   Document metadata. Recognized keys: 'title', 'agency',
                    'date', 'source', 'document_id'.
        findings:   List of standard ODIA finding dicts (id/issue/severity/
                    layer/details).
        to_field:   Memo recipient line.
        from_field: Memo author/sender line.
        memo_date:  ISO date string; defaults to today.
        recommended_actions: Optional bullet list of actions for Conclusion.

    Returns:
        Memorandum dataclass with .to_text() and .to_markdown() methods.
    """
    if memo_date is None:
        memo_date = date.today().isoformat()

    title = doc_meta.get("title") or doc_meta.get("document_id") or "Untitled Document"
    agency = doc_meta.get("agency", "")
    doc_date = doc_meta.get("date", "")

    re_field = f"Legal Audit Findings: {title}"
    if agency:
        re_field += f" — {agency}"

    # Counts
    total = len(findings)
    counts = {
        s: sum(1 for f in findings if f.get("severity") == s) for s in _SEVERITY_ORDER
    }

    # Overview
    if total == 0:
        overview_text = "No legal findings were identified in the analyzed document."
    else:
        doc_ref = f'"{title}"'
        if doc_date:
            doc_ref += f" (dated {doc_date})"
        overview_text = textwrap.fill(
            f"ODIA legal analysis of {doc_ref} identified {total} finding(s) "
            f"across {len({f.get('layer') for f in findings})} detector layer(s): "
            f"{counts['high']} high-severity, {counts['medium']} medium-severity, "
            f"and {counts['low']} low-severity.",
            width=_LINE_WIDTH,
        )

    # Table of authorities
    citations = _extract_citations_from_findings(findings)
    toa = _build_toa(citations)

    # Analysis
    analysis = _build_analysis(findings)

    # Conclusion
    if recommended_actions:
        action_lines = "\n".join(f"  • {a}" for a in recommended_actions)
        conclusion = (
            f"Based on the foregoing analysis, the following actions are recommended:\n\n"
            f"{action_lines}"
        )
    elif counts["high"] > 0:
        conclusion = textwrap.fill(
            f"The {counts['high']} high-severity finding(s) identified above require "
            "immediate agency response. Failure to address these matters may expose the "
            "agency to litigation under the California Public Records Act, "
            "42 U.S.C. § 1983, or applicable federal grant conditions. "
            "Agency counsel should be notified and corrective action documented "
            "within 30 days.",
            width=_LINE_WIDTH,
        )
    else:
        conclusion = textwrap.fill(
            "The identified findings represent areas where agency practice "
            "may benefit from policy review or legal clarification. No immediate "
            "litigation risk has been assessed at this time. Periodic re-audit "
            "is recommended as law and agency practices evolve.",
            width=_LINE_WIDTH,
        )

    return Memorandum(
        to_field=to_field,
        from_field=from_field,
        re_field=re_field,
        memo_date=memo_date,
        overview=overview_text,
        toa=toa,
        analysis=analysis,
        conclusion=conclusion,
    )
