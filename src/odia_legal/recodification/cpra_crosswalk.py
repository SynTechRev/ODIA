"""CPRA recodification crosswalk — Gov. Code § 6250 → § 7920.000 family.

SB 1439 (Stats. 2021, ch. 614) reorganized the California Public Records Act
from Gov. Code §§ 6250–6276.50 to Gov. Code §§ 7920.000–7931.000, effective
January 1, 2022.  Documents pre-dating the recodification cite the old scheme;
post-2022 citations use the new scheme.  Both forms are valid in the field and
must be normalized for cross-document anomaly correlation.

Usage::

    from odia_legal.recodification.cpra_crosswalk import CPRACrosswalk

    xwalk = CPRACrosswalk()
    xwalk.normalize("§ 6254(f)")             # → "§ 7923.650"
    xwalk.to_new("6253(c)")                  # → "7922.535"
    xwalk.to_old("7922.535")                 # → "6253(c)"
    xwalk.is_legacy("Gov. Code § 6254")      # → True
    xwalk.translate_citation("Cal. Gov. Code § 6254(f)")
    # → "Cal. Gov. Code § 7923.650"

Reference: First Amendment Coalition CPRA Transition Guide (Jan. 2022);
California Legislative Counsel crosswalk table (SB 1439, §§ 1–285).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

RECODIFICATION_DATE = date(2022, 1, 1)


@dataclass(frozen=True)
class CrosswalkEntry:
    """Maps one old CPRA section to its new counterpart."""

    old: str
    new: str
    title: str
    article: str
    notes: str | None = None


class TranslationResult(NamedTuple):
    old_section: str
    new_section: str
    title: str
    article: str
    effective: date
    notes: str | None


# ---------------------------------------------------------------------------
# Full crosswalk table  (old_section → CrosswalkEntry)
# Sources: SB 1439 (Stats. 2021, ch. 614); Cal. Legislative Counsel digest;
#          First Amendment Coalition transition guide.
# ---------------------------------------------------------------------------

_ENTRIES: list[CrosswalkEntry] = [
    # ---- Article 1: General Provisions (§§ 7920.000 – 7920.565) ----
    CrosswalkEntry(
        "6250", "7920.000", "Legislative findings and intent", "General Provisions"
    ),
    CrosswalkEntry(
        "6250.5", "7920.005", "Construction of chapter", "General Provisions"
    ),
    CrosswalkEntry(
        "6251",
        "7920.100",
        "Application to state and local agencies",
        "General Provisions",
    ),
    CrosswalkEntry("6252", "7920.500", "Definitions — general", "General Provisions"),
    CrosswalkEntry("6252(a)", "7920.505", "Definition: agency", "General Provisions"),
    CrosswalkEntry(
        "6252(b)",
        "7920.510",
        "Definition: chief executive officer",
        "General Provisions",
    ),
    CrosswalkEntry("6252(c)", "7920.515", "Definition: contract", "General Provisions"),
    CrosswalkEntry(
        "6252(d)", "7920.525", "Definition: local agency", "General Provisions"
    ),
    CrosswalkEntry("6252(e)", "7920.530", "Definition: person", "General Provisions"),
    CrosswalkEntry(
        "6252(f)", "7920.535", "Definition: public agency", "General Provisions"
    ),
    CrosswalkEntry(
        "6252(g)", "7920.540", "Definition: public records", "General Provisions"
    ),
    CrosswalkEntry(
        "6252(h)", "7920.545", "Definition: state agency", "General Provisions"
    ),
    CrosswalkEntry("6252(i)", "7920.550", "Definition: writing", "General Provisions"),
    CrosswalkEntry(
        "6252.5", "7920.555", "Definitions — supplemental", "General Provisions"
    ),
    CrosswalkEntry(
        "6252.6", "7920.560", "Definition: member of the public", "General Provisions"
    ),
    CrosswalkEntry(
        "6252.7",
        "7920.565",
        "Definition: state summary criminal history information",
        "General Provisions",
    ),
    # ---- Article 2: Public Access (§§ 7921.000 – 7922.645) ----
    CrosswalkEntry(
        "6260", "7921.000", "Public records open to inspection", "Public Access"
    ),
    CrosswalkEntry(
        "6261", "7921.005", "Agency duty to make records available", "Public Access"
    ),
    CrosswalkEntry("6262", "7921.010", "Location of records", "Public Access"),
    CrosswalkEntry("6263", "7921.015", "Records of public interest", "Public Access"),
    CrosswalkEntry("6264", "7921.020", "Fees for copies", "Public Access"),
    CrosswalkEntry("6265", "7921.025", "Facilities for inspection", "Public Access"),
    CrosswalkEntry("6266", "7921.030", "Electronic access", "Public Access"),
    CrosswalkEntry("6267", "7921.100", "Retention of records", "Public Access"),
    CrosswalkEntry("6268", "7921.105", "Destruction of records", "Public Access"),
    CrosswalkEntry("6269", "7921.110", "Transfer of records", "Public Access"),
    CrosswalkEntry(
        "6270", "7921.115", "Records in custody of successor agency", "Public Access"
    ),
    CrosswalkEntry("6256", "7921.300", "Request requirements", "Public Access"),
    CrosswalkEntry("6257", "7922.100", "Agency response obligations", "Public Access"),
    CrosswalkEntry(
        "6253", "7922.500", "Right of access; time to respond", "Public Access"
    ),
    CrosswalkEntry("6253(a)", "7922.525", "Right of inspection", "Public Access"),
    CrosswalkEntry("6253(b)", "7922.530", "Right to copy; fees", "Public Access"),
    CrosswalkEntry(
        "6253(c)", "7922.535", "Ten-calendar-day response period", "Public Access"
    ),
    CrosswalkEntry(
        "6253(d)", "7922.540", "Unusual-circumstances extension", "Public Access"
    ),
    CrosswalkEntry(
        "6253(e)", "7922.545", "Rolling production of records", "Public Access"
    ),
    CrosswalkEntry("6253.1", "7922.600", "Assistance to requestors", "Public Access"),
    CrosswalkEntry("6253.2", "7922.605", "Pro bono legal assistance", "Public Access"),
    CrosswalkEntry(
        "6253.3",
        "7922.610",
        "No disclosure required for prior requests",
        "Public Access",
    ),
    CrosswalkEntry(
        "6253.4", "7922.615", "Agency regulations governing access", "Public Access"
    ),
    CrosswalkEntry(
        "6253.5",
        "7922.620",
        "Initiatives — records open to inspection",
        "Public Access",
    ),
    CrosswalkEntry(
        "6253.6", "7922.625", "Financial information of public agency", "Public Access"
    ),
    CrosswalkEntry("6253.9", "7922.630", "Electronic records", "Public Access"),
    CrosswalkEntry("6253.9(a)", "7922.635", "Electronic format right", "Public Access"),
    CrosswalkEntry(
        "6253.9(b)", "7922.640", "Programming cost limitation", "Public Access"
    ),
    CrosswalkEntry(
        "6253.9(c)", "7922.645", "Redaction of electronic records", "Public Access"
    ),
    # ---- Article 3: Exemptions — catch-all (§ 7922.000) ----
    CrosswalkEntry(
        "6255",
        "7922.000",
        "Public interest balancing test (catch-all exemption)",
        "Exemptions",
        notes="Key: agency may withhold if public interest in nondisclosure outweighs disclosure",  # noqa: E501
    ),
    CrosswalkEntry(
        "6255(a)", "7922.000", "Public interest balancing test — text", "Exemptions"
    ),
    CrosswalkEntry(
        "6255(b)", "7922.005", "Indigent requestor fee waiver", "Exemptions"
    ),
    # ---- Article 3: Enumerated Exemptions (§§ 7923.600 – 7923.915) ----
    CrosswalkEntry("6254", "7923.600", "Enumerated exemptions — general", "Exemptions"),
    CrosswalkEntry(
        "6254(a)",
        "7923.610",
        "Preliminary drafts, notes, inter-agency memoranda",
        "Exemptions",
    ),
    CrosswalkEntry(
        "6254(b)", "7923.620", "Records pertaining to pending litigation", "Exemptions"
    ),
    CrosswalkEntry(
        "6254(c)", "7923.625", "Personnel, medical, and similar files", "Exemptions"
    ),
    CrosswalkEntry("6254(d)", "7923.630", "Real estate appraisals", "Exemptions"),
    CrosswalkEntry(
        "6254(e)",
        "7923.640",
        "Third-party contract exemption for bid purposes",
        "Exemptions",
    ),
    CrosswalkEntry(
        "6254(f)",
        "7923.650",
        "Law enforcement investigative records",
        "Exemptions",
        notes="Most-litigated exemption; covers arrest records, crime reports, investigations",  # noqa: E501
    ),
    CrosswalkEntry(
        "6254(g)", "7923.655", "Test questions and scoring keys", "Exemptions"
    ),
    CrosswalkEntry("6254(h)", "7923.660", "Real estate negotiations", "Exemptions"),
    CrosswalkEntry(
        "6254(i)", "7923.665", "Communications to psychotherapist", "Exemptions"
    ),
    CrosswalkEntry("6254(j)", "7923.670", "Library circulation records", "Exemptions"),
    CrosswalkEntry(
        "6254(k)", "7923.700", "Attorney-client privilege communications", "Exemptions"
    ),
    CrosswalkEntry("6254(l)", "7923.705", "Controversial communications", "Exemptions"),
    CrosswalkEntry(
        "6254(m)",
        "7923.710",
        "Financial data of private companies submitted to agencies",
        "Exemptions",
    ),
    CrosswalkEntry(
        "6254(n)", "7923.715", "Geological and geophysical data", "Exemptions"
    ),
    CrosswalkEntry(
        "6254(o)", "7923.720", "Proprietary financial information", "Exemptions"
    ),
    CrosswalkEntry(
        "6254(p)", "7923.725", "Records of juvenile offenders", "Exemptions"
    ),
    CrosswalkEntry(
        "6254(q)", "7923.730", "Records regarding elder abuse", "Exemptions"
    ),
    CrosswalkEntry("6254(r)", "7923.735", "Records related to mediation", "Exemptions"),
    CrosswalkEntry(
        "6254.1",
        "7923.800",
        "Name and address of individuals receiving public assistance",
        "Exemptions",
    ),
    CrosswalkEntry("6254.2", "7923.805", "Records of utility customers", "Exemptions"),
    CrosswalkEntry("6254.4", "7923.810", "Tax collection information", "Exemptions"),
    CrosswalkEntry("6254.6", "7923.815", "Social security numbers", "Exemptions"),
    CrosswalkEntry(
        "6254.7",
        "7923.820",
        "Air quality and pollution records — generally public",
        "Exemptions",
        notes="Disclosure-affirmative: these records are expressly public",
    ),
    CrosswalkEntry(
        "6254.8",
        "7923.825",
        "Employment contracts — must be disclosed",
        "Exemptions",
        notes="Disclosure-affirmative: employment contracts are public",
    ),
    CrosswalkEntry("6254.9", "7923.830", "Computer software", "Exemptions"),
    CrosswalkEntry(
        "6254.10", "7929.600", "Intelligence agency sources and methods", "Exemptions"
    ),
    CrosswalkEntry("6254.11", "7923.835", "Consumer credit data", "Exemptions"),
    CrosswalkEntry("6254.12", "7923.840", "Private utility usage data", "Exemptions"),
    CrosswalkEntry(
        "6254.13", "7923.845", "Health information (HIPAA cross-ref)", "Exemptions"
    ),
    CrosswalkEntry("6254.14", "7923.850", "GPS fleet tracking data", "Exemptions"),
    CrosswalkEntry("6254.15", "7923.855", "Criminal history information", "Exemptions"),
    CrosswalkEntry(
        "6254.16", "7923.860", "Personal address of individuals", "Exemptions"
    ),
    CrosswalkEntry(
        "6254.17",
        "7923.865",
        "Records related to human trafficking victims",
        "Exemptions",
    ),
    CrosswalkEntry("6254.18", "7923.870", "Security plans", "Exemptions"),
    CrosswalkEntry(
        "6254.19",
        "7923.875",
        "Undocumented individual immigration status",
        "Exemptions",
    ),
    CrosswalkEntry("6254.20", "7923.880", "Biometric data", "Exemptions"),
    CrosswalkEntry(
        "6254.21", "7923.885", "Home address of public officials", "Exemptions"
    ),
    CrosswalkEntry(
        "6254.22", "7923.890", "Financial information of crime victims", "Exemptions"
    ),
    CrosswalkEntry(
        "6254.24",
        "7923.895",
        "Records obtained from federal agencies under secrecy agreement",
        "Exemptions",
    ),
    CrosswalkEntry(
        "6254.25", "7923.900", "Certain mental health records", "Exemptions"
    ),
    CrosswalkEntry(
        "6254.26", "7923.905", "Disaster preparedness records", "Exemptions"
    ),
    CrosswalkEntry("6254.27", "7923.910", "Public utility trade secrets", "Exemptions"),
    CrosswalkEntry(
        "6254.28", "7923.915", "Vulnerable utility customer data", "Exemptions"
    ),
    # ---- Employee salary disclosure (disclosure-affirmative) ----
    CrosswalkEntry(
        "6254.3",
        "7927.700",
        "Employee names and salaries — must be disclosed",
        "Disclosure-Affirmative",
        notes="Disclosure-affirmative: name/position/salary of every public employee is public",  # noqa: E501
    ),
    CrosswalkEntry(
        "6254.5",
        "7927.705",
        "Waiver of exemption by voluntary disclosure",
        "Disclosure-Affirmative",
    ),
    # ---- Article 4: Enforcement (§§ 7923.100 – 7923.120) ----
    CrosswalkEntry(
        "6258", "7923.100", "Injunctive or declaratory relief", "Enforcement"
    ),
    CrosswalkEntry("6259", "7923.115", "Judicial enforcement action", "Enforcement"),
    CrosswalkEntry("6259(a)", "7923.115", "Filing of action", "Enforcement"),
    CrosswalkEntry(
        "6259(b)", "7923.120", "Attorney fees to prevailing party", "Enforcement"
    ),
    CrosswalkEntry("6259(c)", "7923.125", "Court in camera review", "Enforcement"),
    CrosswalkEntry("6259(d)", "7923.130", "Contempt for noncompliance", "Enforcement"),
    # ---- Miscellaneous ----
    CrosswalkEntry(
        "6276", "7931.000", "Repeal of superseded provisions", "Miscellaneous"
    ),
    CrosswalkEntry(
        "6276.04", "7931.005", "Specific exemptions preserved", "Miscellaneous"
    ),
    CrosswalkEntry("6276.08", "7931.010", "Exemption index", "Miscellaneous"),
]

# ---------------------------------------------------------------------------
# Build O(1) lookup indexes
# ---------------------------------------------------------------------------

_OLD_TO_NEW: dict[str, CrosswalkEntry] = {e.old: e for e in _ENTRIES}

# For the reverse map, prefer the bare-section entry when multiple old sections
# share the same new number (e.g. "6255" and "6255(a)" → "7922.000").
_NEW_TO_OLD: dict[str, CrosswalkEntry] = {}
for _e in _ENTRIES:
    if _e.new not in _NEW_TO_OLD or "(" not in _e.old:
        _NEW_TO_OLD[_e.new] = _e

# Sections that start with these prefixes are CPRA old-scheme
_LEGACY_PREFIXES = ("625", "626", "627")
_CURRENT_PREFIXES = ("792", "793", "794", "795", "796", "797", "798", "799")

# ---------------------------------------------------------------------------
# Regex patterns for citation extraction
# ---------------------------------------------------------------------------

# Matches:  § 6254(f)  |  §6254  |  section 6254(f)  |  section 6254, subd. (f)
# Captures: (section_number)(optional_subdivision)
_LEGACY_CITATION_RE = re.compile(
    r"""
    (?:
        \b(?:Gov(?:ernment)?\.?\s*Code\s*)?    # optional code prefix
        (?:§{1,2}|section)\s*                  # § or "section"
    )?
    (?P<section>6\d{3}(?:\.\d+)?)              # 4-digit section starting with 6
    (?:
        (?:,\s*subd(?:ivision)?\.?\s*)?        # optional ", subd. "
        \((?P<subdiv>[a-z0-9]+)\)              # (subdivision letter/number)
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)

_CURRENT_CITATION_RE = re.compile(
    r"""
    (?:
        \b(?:Gov(?:ernment)?\.?\s*Code\s*)?
        (?:§{1,2}|section)\s*
    )?
    (?P<section>79\d{2}(?:\.\d+)?)             # 4-digit section starting with 79
    (?:
        (?:,\s*subd(?:ivision)?\.?\s*)?
        \((?P<subdiv>[a-z0-9]+)\)
    )?
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Prefix patterns for the surrounding code prefix in a full citation
_CODE_PREFIX_RE = re.compile(
    r"(Cal(?:ifornia)?\.?\s*)?Gov(?:ernment)?\.?\s*Code\s*(?:§{1,2}|section)?\s*",
    re.IGNORECASE,
)

_SECTION_SYMBOL_RE = re.compile(r"(?:§{1,2}|section)\s*", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


class CPRACrosswalk:
    """Bidirectional recodification engine for the California Public Records Act.

    Translates citations between the pre-2022 (§ 6250–6276) and the
    post-SB-1439 (§ 7920.000–7931.000) numbering schemes.
    """

    # Expose the raw table for downstream consumers (L-9 detector, RAG, etc.)
    entries: list[CrosswalkEntry] = _ENTRIES

    def is_legacy(self, text: str) -> bool:
        """Return True if *text* contains a pre-2022 CPRA section number."""
        return bool(_LEGACY_CITATION_RE.search(text))

    def is_current(self, text: str) -> bool:
        """Return True if *text* contains a post-2022 CPRA section number."""
        return bool(_CURRENT_CITATION_RE.search(text))

    def to_new(self, old_section: str) -> str | None:
        """Map a bare old section string (e.g. '6254(f)') to the new number.

        Returns None if the section is not in the crosswalk.
        """
        key = _normalize_key(old_section)
        entry = _OLD_TO_NEW.get(key)
        return entry.new if entry else None

    def to_old(self, new_section: str) -> str | None:
        """Map a bare new section string (e.g. '7923.650') to the old number."""
        key = _normalize_key(new_section)
        entry = _NEW_TO_OLD.get(key)
        return entry.old if entry else None

    def lookup_old(self, old_section: str) -> TranslationResult | None:
        """Full lookup by old section — returns TranslationResult or None."""
        key = _normalize_key(old_section)
        entry = _OLD_TO_NEW.get(key)
        if entry is None:
            return None
        return TranslationResult(
            old_section=entry.old,
            new_section=entry.new,
            title=entry.title,
            article=entry.article,
            effective=RECODIFICATION_DATE,
            notes=entry.notes,
        )

    def lookup_new(self, new_section: str) -> TranslationResult | None:
        """Full lookup by new section — returns TranslationResult or None."""
        key = _normalize_key(new_section)
        entry = _NEW_TO_OLD.get(key)
        if entry is None:
            return None
        return TranslationResult(
            old_section=entry.old,
            new_section=entry.new,
            title=entry.title,
            article=entry.article,
            effective=RECODIFICATION_DATE,
            notes=entry.notes,
        )

    def normalize(self, citation: str) -> str:
        """Normalize any CPRA section citation to the current (post-2022) form.

        Replaces every matched old-scheme section token in *citation* with its
        new counterpart.  Non-CPRA text is returned unchanged.

        Examples::

            normalize("§ 6254(f)")            → "§ 7923.650"
            normalize("Gov. Code § 6253(c)")  → "Gov. Code § 7922.535"
            normalize("§ 7922.535")           → "§ 7922.535"   (no-op)
        """
        return _substitute(citation, direction="to_new")

    def translate_citation(self, citation: str, target: str = "new") -> str:
        """Translate a full citation string in either direction.

        Args:
            citation: Any citation string, e.g. "Cal. Gov. Code § 6254(f)".
            target: "new" (default) or "old".

        Returns:
            The citation with all recognized sections translated.
        """
        direction = "to_new" if target == "new" else "to_old"
        return _substitute(citation, direction=direction)

    def find_all_in_text(self, text: str) -> list[TranslationResult]:
        """Extract and translate all CPRA citations found in *text*.

        Returns a deduplicated list of TranslationResults for every
        recognized old-scheme section found.
        """
        results: list[TranslationResult] = []
        seen: set[str] = set()
        for match in _LEGACY_CITATION_RE.finditer(text):
            section = match.group("section")
            subdiv = match.group("subdiv")
            key = f"{section}({subdiv})" if subdiv else section
            if key in seen:
                continue
            seen.add(key)
            result = self.lookup_old(key)
            if result:
                results.append(result)
        return results

    def statistics(self) -> dict[str, int]:
        """Return crosswalk coverage statistics."""
        articles: dict[str, int] = {}
        for e in _ENTRIES:
            articles[e.article] = articles.get(e.article, 0) + 1
        return {
            "total_mappings": len(_ENTRIES),
            "unique_old_sections": len(_OLD_TO_NEW),
            "unique_new_sections": len(_NEW_TO_OLD),
            **{
                f"article_{k.lower().replace(' ', '_')}": v for k, v in articles.items()
            },
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _normalize_key(section: str) -> str:
    """Strip whitespace and normalize section key for dict lookup.

    '6254 (f)' → '6254(f)',  ' 6254 ' → '6254'
    """
    return re.sub(r"\s+", "", section.strip())


def _substitute(text: str, direction: str) -> str:
    """Replace all matched CPRA section tokens in *text*.

    direction: "to_new" replaces old sections with new equivalents.
               "to_old" replaces new sections with old equivalents.
    """
    if direction == "to_new":
        pattern = _LEGACY_CITATION_RE
        lookup = _OLD_TO_NEW
        get_replacement = lambda e: e.new  # noqa: E731
    else:
        pattern = _CURRENT_CITATION_RE
        lookup = _NEW_TO_OLD
        get_replacement = lambda e: e.old  # noqa: E731

    def replacer(m: re.Match) -> str:
        section = m.group("section")
        subdiv = m.group("subdiv")
        key = f"{section}({subdiv})" if subdiv else section
        entry = lookup.get(_normalize_key(key))
        if entry is None:
            return m.group(0)  # no match — leave original
        new_sec = get_replacement(entry)
        # Reconstruct with same surrounding symbol and subdivision structure
        prefix = m.group(0)[: m.start("section") - m.start()]
        if subdiv and f"({subdiv})" in new_sec:
            return f"{prefix}{new_sec}"
        return f"{prefix}{new_sec}"

    return pattern.sub(replacer, text)
