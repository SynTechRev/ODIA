"""Parse statutory citations into structured form.

Handles the variant formats found in O.D.I.A. narrative templates,
finding sheets, and ingested document text:

Federal (USC):
    "34 U.S.C. § 10152"
    "34 U.S.C. § 10152(a)(1)(G)"
    "34 U.S.C. §§ 10152-10153"      # range
    "34 USC 10152"                   # informal
    "34 U.S.C. § 10152 (Supp. 2020)" # with edition

California Civil Code / CPRA (CCCitation):
    "Cal. Civ. Code § 1798.121"
    "Civil Code § 1798.121(a)"
    "§ 1798.121"                     # bare section (CPRA range)
    "CCP § 1281.97"
    "Cal. Code Civ. Proc. § 1281.97"
    "Lab. Code § 2699"
    "Gov. Code § 12953"

Does NOT handle CFR or case-law citations; those will have their
own parsers when those corpora land.

Returns None for unparseable strings — caller decides how to handle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class StatuteCitation:
    """A parsed federal statutory citation.

    Canonical form: f"{title} U.S.C. § {section}{subsection_path}"
    """

    title: int  # e.g., 34
    section: str  # e.g., "10152" (str to handle "10152a" etc.)
    subsection_path: str  # e.g., "(a)(1)(G)" or "" if root
    raw: str  # the original matched substring
    canonical: str  # normalized form for cache keys

    @property
    def section_root(self) -> str:
        """Section number without subsection path. Used for file lookup."""
        return self.section


# Comprehensive USC citation regex. Handles:
#   - 34 U.S.C. § 10152
#   - 34 USC 10152  (without periods or section symbol)
#   - 34 U.S.C. § 10152(a)(1)(G)
#   - 34 U.S.C. §§ 10152-10153  (range — captured but reported as first)
# Negative lookbehind for "C.F.R." prevents misparsing CFR citations
# (e.g. "2 C.F.R. § 200.303" must NOT match this regex).
_USC_PATTERN = re.compile(
    r"""
    (?<!C\.F\.R\.\s)                  # not preceded by "C.F.R. " (CFR guard)
    (?<!CFR\s)                        # not preceded by "CFR " (CFR guard)
    \b(?P<title>\d{1,2})              # title: 1-50ish
    \s*
    U\.?\s?S\.?\s?C\.?                # U.S.C. with variant punctuation
    \s*
    §{0,2}                            # zero, one, or two § symbols
    \s*
    (?P<section>\d+[a-z]*)            # section: digits + optional letter (e.g., 1395dd)
    (?P<subsection>(?:\([a-z0-9]+\))*) # zero or more subsection levels
    """,
    re.VERBOSE | re.IGNORECASE,
)


def parse_usc_citations(text: str) -> list[StatuteCitation]:
    """Extract every USC citation from a block of text."""
    out: list[StatuteCitation] = []
    for m in _USC_PATTERN.finditer(text):
        title = int(m.group("title"))
        if title < 1 or title > 54:
            continue  # USC titles are 1-54
        section = m.group("section")
        subsection = m.group("subsection") or ""
        raw = m.group(0).strip()
        canonical = f"{title} U.S.C. § {section}{subsection}"
        out.append(
            StatuteCitation(
                title=title,
                section=section,
                subsection_path=subsection,
                raw=raw,
                canonical=canonical,
            )
        )
    return out


def parse_single(text: str) -> StatuteCitation | None:
    """Parse a single citation string. Returns None if no match."""
    matches = parse_usc_citations(text)
    return matches[0] if matches else None


# ── California Code citation support ────────────────────────────────────────


@dataclass(frozen=True)
class CalCitation:
    """A parsed California statutory citation.

    Covers Cal. Civ. Code, CCP, Lab. Code, Gov. Code, and bare CPRA
    section references (§ 1798.xxx).

    Canonical form:  "{code_abbrev} § {section}{subsection_path}"
    Examples:
        "Cal. Civ. Code § 1798.121(a)(7)"
        "Cal. Code Civ. Proc. § 1281.97"
        "Cal. Lab. Code § 2699(f)"
        "Cal. Gov. Code § 12953"
    """

    code: str  # "Civ. Code" | "CCP" | "Lab. Code" | "Gov. Code"
    section: str  # e.g. "1798.121" or "1281.97"
    subsection_path: str
    raw: str
    canonical: str

    @property
    def section_root(self) -> str:
        return self.section.split(".")[0]

    @property
    def cpra_loader_key(self) -> str | None:
        """Return the CPRACorpusLoader._PROVISIONS key for this citation, if applicable."""
        if self.code == "Civ. Code" and self.section.startswith("1798."):
            return self.section
        if self.code == "CCP":
            return f"CCP_{self.section}"
        if self.code == "Lab. Code" and self.section == "2699":
            return "Lab_2699"
        if self.code == "Gov. Code" and self.section == "12953":
            return "GovCode_12953"
        return None


# California code abbreviation normaliser
_CAL_CODE_MAP: dict[str, str] = {
    "cal. civ. code": "Civ. Code",
    "civil code": "Civ. Code",
    "civ. code": "Civ. Code",
    "ccp": "CCP",
    "cal. code civ. proc.": "CCP",
    "code civ. proc.": "CCP",
    "c.c.p.": "CCP",
    "lab. code": "Lab. Code",
    "labor code": "Lab. Code",
    "cal. labor code": "Lab. Code",
    "gov. code": "Gov. Code",
    "government code": "Gov. Code",
    "cal. gov. code": "Gov. Code",
    "pen. code": "Pen. Code",
    "penal code": "Pen. Code",
}

# Matches: "Cal. Civ. Code § 1798.121(a)(7)", "CCP § 1281.97", "§ 1798.100" etc.
_CAL_PATTERN = re.compile(
    r"""
    (?:
        (?P<code_full>
            Cal\.?\s+(?:Civ(?:il)?\.?\s*Code|Code\s+Civ(?:il)?\.?\s*Proc\.?|Lab(?:or)?\.?\s*Code|Gov(?:ernment)?\.?\s*Code|Pen(?:al)?\.?\s*Code)
            |Civ(?:il)?\.?\s*Code
            |(?:Cal\.?\s*)?C\.?C\.?P\.?
            |Lab(?:or)?\.?\s*Code
            |Gov(?:ernment)?\.?\s*Code
            |Pen(?:al)?\.?\s*Code
        )\s*
    )?
    §{1,2}\s*
    (?P<section>\d{3,5}(?:\.\d+[a-z]?)?)   # e.g. 1798.121  or  2699
    (?P<subsection>(?:\([a-zA-Z0-9]+\))*)
    """,
    re.VERBOSE | re.IGNORECASE,
)

# CPRA section range for bare § citations: 1798.100–1798.199 and CCP 1281.xx
_CPRA_SECTION_RE = re.compile(r"^1798\.\d+[a-z]?$")
_CCP_ARB_RE = re.compile(r"^1281\.\d+$")
_CCP_UNCON_RE = re.compile(r"^1670\.5$")


def _normalise_code(raw: str | None, section: str) -> str | None:
    """Infer canonical code abbreviation."""
    if raw:
        k = re.sub(r"\s+", " ", raw.strip().lower())
        for variant, canonical in _CAL_CODE_MAP.items():
            if variant in k:
                return canonical
    # Bare § citation — try to infer from section range
    if _CPRA_SECTION_RE.match(section):
        return "Civ. Code"
    if _CCP_ARB_RE.match(section) or _CCP_UNCON_RE.match(section):
        return "CCP"
    return None


def parse_cal_citations(text: str) -> list[CalCitation]:
    """Extract every California statute citation from a block of text."""
    out: list[CalCitation] = []
    seen: set[str] = set()

    for m in _CAL_PATTERN.finditer(text):
        section = m.group("section")
        subsection = m.group("subsection") or ""
        raw_code = m.group("code_full")

        code = _normalise_code(raw_code, section)
        if code is None:
            continue  # can't determine which California code

        canonical = f"Cal. {code} § {section}{subsection}"
        if canonical in seen:
            continue
        seen.add(canonical)

        raw = m.group(0).strip()
        out.append(
            CalCitation(
                code=code,
                section=section,
                subsection_path=subsection,
                raw=raw,
                canonical=canonical,
            )
        )

    return out


def parse_cal_single(text: str) -> CalCitation | None:
    """Parse a single California citation string. Returns None if no match."""
    matches = parse_cal_citations(text)
    return matches[0] if matches else None
