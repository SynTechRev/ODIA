"""Legal citation formatter for O.D.I.A.

Renders Citation objects (from odia_legal.citations.parser) in four styles:

  cal_style  — California Style Manual (4th ed.), used by California courts
  bluebook   — The Bluebook: A Uniform System of Citation (21st ed.)
  plain      — Plain-language description for community/non-lawyer audiences
  markdown   — Markdown-formatted with italic case names and § symbols

Usage::

    from odia_legal.citations.formatter import format_citation, format_all
    from odia_legal.citations.parser import parse_citations

    cites = parse_citations("Gov. Code § 7922.000; Carpenter v. United States (2018) 585 U.S. 296")
    for c in cites:
        print(format_citation(c, style="cal_style"))
        print(format_citation(c, style="bluebook"))
        print(format_citation(c, style="plain"))
        print(format_citation(c, style="markdown"))
"""

from __future__ import annotations

from typing import Literal

from odia_legal.citations.parser import Citation

Style = Literal["cal_style", "bluebook", "plain", "markdown"]

# ---------------------------------------------------------------------------
# Bluebook abbreviations for California codes (T1 state statutes table)
# ---------------------------------------------------------------------------

_BLUEBOOK_CAL_CODE: dict[str, str] = {
    "gov": "Cal. Gov't Code",
    "pen": "Cal. Penal Code",
    "civ": "Cal. Civ. Code",
    "ccp": "Cal. Civ. Proc. Code",
    "welf": "Cal. Welf. & Inst. Code",
    "veh": "Cal. Veh. Code",
    "ed": "Cal. Educ. Code",
    "h&s": "Cal. Health & Safety Code",
    "lab": "Cal. Lab. Code",
    "fam": "Cal. Fam. Code",
    "corp": "Cal. Corp. Code",
    "prob": "Cal. Prob. Code",
    "uic": "Cal. Unemp. Ins. Code",
    "rev&tax": "Cal. Rev. & Tax. Code",
    "bus&prof": "Cal. Bus. & Prof. Code",
    "fin": "Cal. Fin. Code",
}

# CA Style Manual canonical code name (abbreviated, no "Cal." prefix)
_CASM_CAL_CODE: dict[str, str] = {
    "gov": "Gov. Code",
    "pen": "Pen. Code",
    "civ": "Civ. Code",
    "ccp": "Code Civ. Proc.",
    "welf": "Welf. & Inst. Code",
    "veh": "Veh. Code",
    "ed": "Ed. Code",
    "h&s": "Health & Saf. Code",
    "lab": "Lab. Code",
    "fam": "Fam. Code",
    "corp": "Corp. Code",
    "prob": "Prob. Code",
    "uic": "Unemp. Ins. Code",
    "rev&tax": "Rev. & Tax. Code",
    "bus&prof": "Bus. & Prof. Code",
    "fin": "Fin. Code",
}

# Human-readable full names for plain-language style
_PLAIN_CAL_CODE: dict[str, str] = {
    "gov": "California Government Code",
    "pen": "California Penal Code",
    "civ": "California Civil Code",
    "ccp": "California Code of Civil Procedure",
    "welf": "California Welfare and Institutions Code",
    "veh": "California Vehicle Code",
    "ed": "California Education Code",
    "h&s": "California Health and Safety Code",
    "lab": "California Labor Code",
    "fam": "California Family Code",
    "corp": "California Corporations Code",
    "prob": "California Probate Code",
    "uic": "California Unemployment Insurance Code",
    "rev&tax": "California Revenue and Taxation Code",
    "bus&prof": "California Business and Professions Code",
    "fin": "California Financial Code",
}

# California reporters: short → Bluebook abbreviation
_BLUEBOOK_REPORTER: dict[str, str] = {
    "Cal.5th": "Cal. 5th",
    "Cal.4th": "Cal. 4th",
    "Cal.3d": "Cal. 3d",
    "Cal.2d": "Cal. 2d",
    "Cal.": "Cal.",
    "Cal.App.5th": "Cal. App. 5th",
    "Cal.App.4th": "Cal. App. 4th",
    "Cal.App.3d": "Cal. App. 3d",
    "Cal.App.2d": "Cal. App. 2d",
    "Cal.Rptr.3d": "Cal. Rptr. 3d",
    "Cal.Rptr.2d": "Cal. Rptr. 2d",
    "Cal.Rptr.": "Cal. Rptr.",
}

# Plain-language reporter descriptions
_PLAIN_REPORTER_COURT: dict[str, str] = {
    "Cal.5th": "California Supreme Court",
    "Cal.4th": "California Supreme Court",
    "Cal.3d": "California Supreme Court",
    "Cal.2d": "California Supreme Court",
    "Cal.": "California Supreme Court",
    "Cal.App.5th": "California Court of Appeal",
    "Cal.App.4th": "California Court of Appeal",
    "Cal.App.3d": "California Court of Appeal",
    "Cal.App.2d": "California Court of Appeal",
    "Cal.Rptr.3d": "California Court of Appeal",
    "Cal.Rptr.2d": "California Court of Appeal",
    "Cal.Rptr.": "California Court of Appeal",
    "U.S.": "U.S. Supreme Court",
    "F.3d": "Federal Circuit Court of Appeals",
    "F.4th": "Federal Circuit Court of Appeals",
}


def _subdiv_casm(subdiv: str | None) -> str:
    """Convert '(f)(1)' → ', subd. (f)(1)' per CA Style Manual § 2:55."""
    if not subdiv:
        return ""
    # Only the outermost subdivision gets the "subd." label
    return f", subd. {subdiv}"


# ---------------------------------------------------------------------------
# Per-type formatters
# ---------------------------------------------------------------------------


def _fmt_usc(c: Citation, style: Style) -> str:
    subdiv = c.subdivision or ""
    if style == "cal_style":
        return f"{c.usc_title} U.S.C. § {c.section}{subdiv}"
    if style == "bluebook":
        return f"{c.usc_title} U.S.C. § {c.section}{subdiv}"
    if style == "plain":
        return f"Section {c.section}{subdiv} of Title {c.usc_title} of the United States Code"
    # markdown
    return f"{c.usc_title} U.S.C. § {c.section}{subdiv}"


def _fmt_cfr(c: Citation, style: Style) -> str:
    if c.section:
        subdiv = c.subdivision or ""
        if style == "plain":
            return (
                f"Section {c.section}{subdiv} of Title {c.cfr_title} "
                f"of the Code of Federal Regulations"
            )
        return f"{c.cfr_title} C.F.R. § {c.section}{subdiv}"
    # Part-level citation
    part = c.cfr_part or ""
    if style == "plain":
        return f"Part {part} of Title {c.cfr_title} of the Code of Federal Regulations"
    return f"{c.cfr_title} C.F.R. Part {part}"


def _fmt_cal_code(c: Citation, style: Style) -> str:
    key = c.cal_code or "gov"
    section = c.section or ""
    subdiv = c.subdivision or ""

    if style == "cal_style":
        code_name = _CASM_CAL_CODE.get(key, "Gov. Code")
        subdiv_str = _subdiv_casm(c.subdivision)
        return f"{code_name}, § {section}{subdiv_str}"
    if style == "bluebook":
        code_name = _BLUEBOOK_CAL_CODE.get(key, "Cal. Gov't Code")
        return f"{code_name} § {section}{subdiv}"
    if style == "plain":
        code_name = _PLAIN_CAL_CODE.get(key, "California Government Code")
        return f"{code_name} section {section}{subdiv}"
    # markdown — same as canonical, no comma
    code_name = _CASM_CAL_CODE.get(key, "Gov. Code")
    return f"{code_name} § {section}{subdiv}"


def _fmt_cal_case(c: Citation, style: Style) -> str:
    parties = c.parties or ""
    year = c.year or 0
    volume = c.volume or 0
    reporter = c.reporter or ""
    page = c.page or 0

    if style == "cal_style":
        # CA Style Manual: Party v. Party (year) volume Reporter page
        return f"{parties} ({year}) {volume} {reporter} {page}"

    if style == "bluebook":
        # Bluebook: Party v. Party, volume Reporter page (year)
        bb_reporter = _BLUEBOOK_REPORTER.get(reporter, reporter)
        return f"{parties}, {volume} {bb_reporter} {page} ({year})"

    if style == "plain":
        court = _PLAIN_REPORTER_COURT.get(reporter, "California appellate court")
        return f"{parties} ({court}, {year})"

    # markdown — italic parties
    return f"*{parties}* ({year}) {volume} {reporter} {page}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def format_citation(citation: Citation, style: Style = "cal_style") -> str:
    """Format a single Citation in the requested style.

    Args:
        citation: A parsed Citation object from odia_legal.citations.parser.
        style:    One of 'cal_style', 'bluebook', 'plain', 'markdown'.

    Returns:
        Formatted citation string.

    Raises:
        ValueError: If citation_type is unrecognized.
    """
    if citation.citation_type == "usc":
        return _fmt_usc(citation, style)
    if citation.citation_type == "cfr":
        return _fmt_cfr(citation, style)
    if citation.citation_type == "cal_code":
        return _fmt_cal_code(citation, style)
    if citation.citation_type == "cal_case":
        return _fmt_cal_case(citation, style)
    raise ValueError(f"Unknown citation_type: {citation.citation_type!r}")


def format_all(
    citations: list[Citation],
    style: Style = "cal_style",
    separator: str = "; ",
) -> str:
    """Format a list of Citations and join with *separator*."""
    return separator.join(format_citation(c, style) for c in citations)
