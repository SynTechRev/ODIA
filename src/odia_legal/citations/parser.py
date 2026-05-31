"""Multi-code legal citation parser for O.D.I.A.

Parses citation strings into structured Citation objects for:

  Federal:
    USC    — 34 U.S.C. § 10152(a)(1)(G)
    CFR    — 2 C.F.R. § 200.303 | 28 C.F.R. Part 23

  California codes:
    Gov. Code  — § 6254(f) | § 7923.650      (CPRA both old + new)
    Pen. Code  — § 832.7
    Civ. Code  — § 1798.90.55                (ALPR)
    CCP        — Code Civ. Proc. § 1085
    Welf. Code — Welf. & Inst. Code § 827
    Veh. Code  — § 2413
    Ed. Code, Health & Safety, Labor, etc.

  California case law:
    CBS, Inc. v. Block (1986) 42 Cal.3d 646
    ACLU v. Superior Court (2011) 202 Cal.App.4th 55

Usage::

    from odia_legal.citations.parser import parse_citations, Citation

    cites = parse_citations(
        "Under § 6254(f) and 2 C.F.R. § 200.303, see Carpenter v. "
        "United States, 585 U.S. 296 (2018)."
    )
    for c in cites:
        print(c.canonical, c.citation_type)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Unified Citation dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Citation:
    """A parsed legal citation of any supported type.

    Fields unused by a given citation type are None.
    """

    citation_type: str
    """One of: 'usc' | 'cfr' | 'cal_code' | 'cal_case'"""

    corpus_id: str
    """Identifies the corpus that resolves this citation.
    USC: 'us_code'  |  CFR: 'cfr'  |  Cal. code: code abbreviation
    e.g. 'cal_gov_code', 'cal_pen_code', 'cal_civ_code'
    Cal. case: 'cal_case_law'
    """

    raw: str
    """The original matched substring."""

    canonical: str
    """Normalized citation in the preferred display form."""

    # Federal statutory / regulatory
    usc_title: int | None = None
    cfr_title: int | None = None
    cfr_part: str | None = None

    # California code
    cal_code: str | None = None
    """Abbreviation, e.g. 'Gov.', 'Pen.', 'Civ.', 'CCP', 'Veh.'"""

    # Shared statutory section fields
    section: str | None = None
    subdivision: str | None = None

    # California case law
    parties: str | None = None
    year: int | None = None
    volume: int | None = None
    reporter: str | None = None
    page: int | None = None


# ---------------------------------------------------------------------------
# California code abbreviation → corpus_id mapping
# ---------------------------------------------------------------------------

_CAL_CODE_MAP: dict[str, str] = {
    "gov": "cal_gov_code",
    "pen": "cal_pen_code",
    "civ": "cal_civ_code",
    "ccp": "cal_ccp",
    "welf": "cal_welf_inst_code",
    "veh": "cal_veh_code",
    "ed": "cal_ed_code",
    "h&s": "cal_health_safety_code",
    "lab": "cal_labor_code",
    "fam": "cal_fam_code",
    "corp": "cal_corp_code",
    "prob": "cal_prob_code",
    "uic": "cal_unemp_ins_code",
    "rev&tax": "cal_rev_tax_code",
    "sts&high": "cal_sts_high_code",
    "pub util": "cal_pub_util_code",
    "bus&prof": "cal_bus_prof_code",
    "fin": "cal_fin_code",
}

_CAL_CODE_CANONICAL: dict[str, str] = {
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
    "sts&high": "Sts. & High. Code",
    "pub util": "Pub. Util. Code",
    "bus&prof": "Bus. & Prof. Code",
    "fin": "Fin. Code",
}

# California reporter abbreviations (ordered longest-first for greedy match)
_CAL_REPORTERS = [
    "Cal.App.5th",
    "Cal.App.4th",
    "Cal.App.3d",
    "Cal.App.2d",
    "Cal.Rptr.3d",
    "Cal.Rptr.2d",
    "Cal.Rptr.",
    "Cal.5th",
    "Cal.4th",
    "Cal.3d",
    "Cal.2d",
    "Cal.",
]

_CAL_REPORTER_PATTERN = "|".join(
    re.escape(r) for r in _CAL_REPORTERS
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# ------ Federal USC ------
_USC_RE = re.compile(
    r"""
    (?<!C\.F\.R\.\s)(?<!CFR\s)         # not part of a CFR citation
    \b(?P<usc_title>\d{1,2})\s*
    U\.?\s?S\.?\s?C\.?
    \s*§{0,2}\s*
    (?P<section>\d+[a-z]*)
    (?P<subdivision>(?:\([a-z0-9]+\))*)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ------ Federal CFR ------
_CFR_RE = re.compile(
    r"""
    \b(?P<cfr_title>\d{1,2})\s*
    C\.?\s?F\.?\s?R\.?
    \s*
    (?:
        §{1,2}\s*(?P<section>\d+(?:\.\d+)*)
        (?P<subdivision>(?:\([a-z0-9]+\))*)
    |
        [Pp]art\s+(?P<part>\d+(?:\.\d+)*)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ------ California codes ------
# Handles: Gov. Code § 6254(f), Government Code section 7923.650,
#          Cal. Gov. Code §§ 6250-6256, Pen. Code § 832.7,
#          Civ. Code § 1798.90.55, Code Civ. Proc. § 1085,
#          Welf. & Inst. Code § 827, Veh. Code § 2413, etc.
_CAL_CODE_PREFIX = r"""
    (?:Cal(?:ifornia)?\.?\s+)?          # optional "Cal." or "California"
    (?P<code>
        Gov(?:ernment)?\.?\s*Code
      | (?:California\s+)?Penal\s+Code | Pen\.?\s+Code
      | Civil\s+Code | Civ\.?\s+Code
      | Code\s+Civ\.?\s+Proc\.?
      | Welf(?:are)?\.?\s+(?:&|and)\s+Inst(?:itutions)?\.?\s+Code
      | Veh(?:icle)?\.?\s+Code
      | Ed(?:ucation)?\.?\s+Code
      | Health\s+(?:&|and)\s+Saf(?:ety)?\.?\s+Code
      | Lab(?:or)?\.?\s+Code
      | Fam(?:ily)?\.?\s+Code
      | Corp(?:orations)?\.?\s+Code
      | Prob(?:ate)?\.?\s+Code
      | Unemp(?:loyment)?\.?\s+Ins(?:urance)?\.?\s+Code
      | Rev(?:enue)?\.?\s+(?:&|and)\s+Tax(?:ation)?\.?\s+Code
      | Bus(?:iness)?\.?\s+(?:&|and)\s+Prof(?:essions)?\.?\s+Code
      | Fin(?:ancial)?\.?\s+Code
    )
    \s+
    (?:§{1,2}|section)\s*
    (?P<section>\d+(?:\.\d+)*)
    (?P<subdivision>
        (?:,\s*subd(?:ivision)?\.?\s*)?
        (?:\([a-z0-9]+\))+
    )?
"""

_CAL_CODE_RE = re.compile(_CAL_CODE_PREFIX, re.VERBOSE | re.IGNORECASE)

# ------ California case law ------
# "CBS, Inc. v. Block (1986) 42 Cal.3d 646"
# "ACLU v. Superior Court (2011) 202 Cal.App.4th 55"
_CAL_CASE_RE = re.compile(
    rf"""
    (?P<parties>
        [A-Z][A-Za-z0-9,\.\s]{{3,60}}?  # plaintiff
        \s+v\.?\s+
        [A-Z][A-Za-z0-9,\.\s]{{3,60}}?  # defendant
    )
    \s*\((?P<year>\d{{4}})\)\s*          # (YEAR)
    (?P<volume>\d{{1,4}})\s*
    (?P<reporter>{_CAL_REPORTER_PATTERN})\s*
    (?P<page>\d{{1,4}})
    """,
    re.VERBOSE,
)


# ---------------------------------------------------------------------------
# Helper: normalize California code key
# ---------------------------------------------------------------------------


# Ordered (most-specific first) pairs of (substring_required, key)
_CODE_KEY_TABLE: list[tuple[tuple[str, ...], str]] = [
    (("proc",), "ccp"),  # "Code Civ. Proc." — "proc" is the discriminator
    (("rev", "tax"), "rev&tax"),
    (("bus", "prof"), "bus&prof"),
    (("health",), "h&s"),
    (("saf",), "h&s"),
    (("welf",), "welf"),
    (("unemp",), "uic"),
    (("gov",), "gov"),
    (("pen",), "pen"),
    (("civ",), "civ"),
    (("veh",), "veh"),
    (("lab",), "lab"),
    (("fam",), "fam"),
    (("corp",), "corp"),
    (("prob",), "prob"),
    (("fin",), "fin"),
    (("ed",), "ed"),
]


def _code_key(code_text: str) -> str:
    """Map raw matched code text to a short canonical key."""
    t = code_text.lower().strip()
    for substrings, key in _CODE_KEY_TABLE:
        if all(s in t for s in substrings):
            return key
    return "gov"


def _normalize_subdivision(raw: str) -> str:
    """Normalize subdivision text: remove 'subd.' and extra spaces."""
    return re.sub(r",?\s*subd(?:ivision)?\.?\s*", "", raw).strip()


# ---------------------------------------------------------------------------
# Public parse functions
# ---------------------------------------------------------------------------


def parse_usc(text: str) -> list[Citation]:
    """Extract all USC citations from *text*."""
    results: list[Citation] = []
    for m in _USC_RE.finditer(text):
        usc_title = int(m.group("usc_title"))
        if not (1 <= usc_title <= 54):
            continue
        section = m.group("section")
        subdiv = m.group("subdivision") or ""
        canonical = f"{usc_title} U.S.C. § {section}{subdiv}"
        results.append(
            Citation(
                citation_type="usc",
                corpus_id="us_code",
                raw=m.group(0).strip(),
                canonical=canonical,
                usc_title=usc_title,
                section=section,
                subdivision=subdiv or None,
            )
        )
    return results


def parse_cfr(text: str) -> list[Citation]:
    """Extract all CFR citations from *text*."""
    results: list[Citation] = []
    for m in _CFR_RE.finditer(text):
        cfr_title = int(m.group("cfr_title"))
        section = m.group("section")
        part = m.group("part")
        subdiv = m.group("subdivision") or "" if section else ""
        if section:
            canonical = f"{cfr_title} C.F.R. § {section}{subdiv}"
        else:
            canonical = f"{cfr_title} C.F.R. Part {part}"
        results.append(
            Citation(
                citation_type="cfr",
                corpus_id="cfr",
                raw=m.group(0).strip(),
                canonical=canonical,
                cfr_title=cfr_title,
                cfr_part=part,
                section=section,
                subdivision=subdiv or None,
            )
        )
    return results


def parse_cal_code(text: str) -> list[Citation]:
    """Extract all California code citations from *text*."""
    results: list[Citation] = []
    for m in _CAL_CODE_RE.finditer(text):
        code_raw = m.group("code")
        section = m.group("section")
        subdiv_raw = m.group("subdivision") or ""
        subdiv = _normalize_subdivision(subdiv_raw)

        key = _code_key(code_raw)
        canonical_code = _CAL_CODE_CANONICAL.get(key, "Gov. Code")
        corpus_id = _CAL_CODE_MAP.get(key, "cal_gov_code")
        canonical = f"{canonical_code} § {section}{subdiv}"

        results.append(
            Citation(
                citation_type="cal_code",
                corpus_id=corpus_id,
                raw=m.group(0).strip(),
                canonical=canonical,
                cal_code=key,
                section=section,
                subdivision=subdiv or None,
            )
        )
    return results


def parse_cal_case(text: str) -> list[Citation]:
    """Extract California appellate case citations from *text*."""
    results: list[Citation] = []
    for m in _CAL_CASE_RE.finditer(text):
        parties = re.sub(r"\s+", " ", m.group("parties")).strip().rstrip(",")
        year = int(m.group("year"))
        volume = int(m.group("volume"))
        reporter = m.group("reporter").strip()
        page = int(m.group("page"))
        canonical = f"{parties} ({year}) {volume} {reporter} {page}"
        results.append(
            Citation(
                citation_type="cal_case",
                corpus_id="cal_case_law",
                raw=m.group(0).strip(),
                canonical=canonical,
                parties=parties,
                year=year,
                volume=volume,
                reporter=reporter,
                page=page,
            )
        )
    return results


def parse_citations(text: str) -> list[Citation]:
    """Extract all recognized citation types from *text*.

    Order: USC first (most precise pattern), then CFR, then Cal. codes,
    then Cal. cases.  Overlapping spans are not deduplicated — callers
    should use Citation.raw to detect spans if needed.
    """
    return (
        parse_usc(text)
        + parse_cfr(text)
        + parse_cal_code(text)
        + parse_cal_case(text)
    )
