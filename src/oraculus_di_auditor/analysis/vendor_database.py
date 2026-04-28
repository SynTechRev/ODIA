"""ODIA vendor and statute reference database.

Encodes the surveillance vendor catalogue, product subtypes, and California /
federal statutory references that the ODIA audit methodology looks for.  Used
by the surveillance, governance_gap, and grant_compliance detectors so that
the rule set lives in one place instead of being duplicated across files.

Everything here is based on public information: vendor marketing copy, public
procurement records, published California Government Code citations, and the
ACLU CCOPS model bill.  No non-public intelligence is embedded.

Detection philosophy
--------------------
The ODIA methodology flags anomalies whenever a surveillance technology is
documented as *deployed or funded* without the corresponding *governance
artifact*.  For example:

  * Flock Safety ALPR referenced in a staff report, but no SB 524
    written-policy citation anywhere in the same corpus.
  * Axon body-worn camera contract authorized, but no CJIS Security Addendum
    referenced in the signed agreement.
  * JAG grant-funded equipment purchase, but no anti-supplanting certification
    on the receiving municipality.

Rather than try to model these as general-purpose heuristics, we encode the
specific vendor signatures, statutory triggers, and the pairs that
constitute a finding.  This mirrors how the human ODIA auditor reads a
corpus and produces an MAS (Master Audit Synthesis).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Vendor signatures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VendorSignature:
    """Canonical reference for a surveillance vendor and its products."""

    name: str
    category: str  # "alpr" | "bwc" | "policy_boilerplate" | "drone" | "other"
    patterns: tuple[str, ...]  # case-insensitive regex patterns
    subproducts: tuple[str, ...] = ()  # optional sub-product names to tag
    governance_required: tuple[str, ...] = ()  # keyword-sets required in same corpus


# The patterns are deliberately slightly permissive — ODIA source documents
# use a mix of marketing spellings, abbreviations, and informal references.
VENDOR_CATALOGUE: tuple[VendorSignature, ...] = (
    VendorSignature(
        name="Flock Safety",
        category="alpr",
        patterns=(
            r"\bflock\s+safety\b",
            r"\bflock\s+group\b",
            r"\bflock\s+(?:nova|aerodome|falcon|raven|sparrow|wing)\b",
            r"\bflock\s+cameras?\b",
            r"\bflock\s+alpr\b",
            r"\bflock\s+transparency\s+portal\b",
            r"\bflock\s+(?:llc|inc)\b",
            r"\bvehicle\s+fingerprint\b",  # Flock-specific ML product
        ),
        subproducts=("Flock Nova", "Flock Aerodome", "Vehicle Fingerprint"),
        governance_required=("sb_524", "cjis", "retention_policy", "council_approval"),
    ),
    VendorSignature(
        name="Axon Enterprise",
        category="bwc",
        patterns=(
            r"\baxon\b(?!\s+materia)",  # exclude "axon materia" false-positive
            r"\btaser\s+international\b",
            r"\bevidence\.com\b",
            r"\bdraft\s*one\b",  # Axon's AI report writer
            r"\bfleet\s*3\b",  # Axon dashcam product
            r"\bauto[-\s]?tagging\b",  # Axon AI auto-tagging
            r"\bofficer\s+safety\s+plan\b",
            r"\bosp\s?\d+\b",  # OSP7, OSP10 etc — Axon subscription plans
            r"\bbody[-\s]?worn\s+camer(?:a|as)\b",
            r"\bbwc\b(?!\s*fund)",
        ),
        subproducts=("Draft One", "Fleet 3", "Auto-Tagging", "Evidence.com", "OSP7"),
        governance_required=("sb_524", "cjis", "retention_policy", "draft_one_policy"),
    ),
    VendorSignature(
        name="Lexipol",
        category="policy_boilerplate",
        patterns=(
            r"\blexipol\b",
            r"\bcalifornia\s+state\s+master\b",  # Lexipol's boilerplate package
            r"\bpolicy\s+manual\b.*?\blexipol\b",  # within same text window
        ),
        governance_required=(),  # not itself a capability
    ),
    VendorSignature(
        name="Motorola Solutions",
        category="other",
        patterns=(
            r"\bmotorola\s+solutions\b",
            r"\bmotorola\s+apx\b",
            r"\bwatchguard\b",  # Motorola-owned BWC/dashcam
            r"\bcommandcentral\b",
        ),
        governance_required=("cjis",),
    ),
    VendorSignature(
        name="Spartan Camera",
        category="other",
        patterns=(r"\bspartan\s+camera\b",),
        governance_required=("retention_policy", "council_approval"),
    ),
    VendorSignature(
        name="ABH Fox Solutions",
        category="other",
        patterns=(r"\babh\s+fox\b", r"\babh\s+fox\s+solutions\b"),
        governance_required=("council_approval",),
    ),
    VendorSignature(
        name="SmartWater CSI",
        category="other",
        patterns=(r"\bsmartwater\s+csi\b", r"\bsmartwater\b"),
    ),
    VendorSignature(
        name="Nexanet",
        category="other",
        patterns=(r"\bnexanet\b",),
        governance_required=("cjis",),
    ),
    VendorSignature(
        name="Security Lines US",
        category="other",
        patterns=(r"\bsecurity\s+lines\s+us\b",),
    ),
    VendorSignature(
        name="BCS Consulting",
        category="other",
        patterns=(r"\bbcs\s+consulting\b",),
    ),
    VendorSignature(
        name="QPCS LLC",
        category="other",
        patterns=(r"\bqpcs\b(?:\s+llc)?",),
    ),
    # v2.9.3 E.2 — Verkada is a video-surveillance vendor MARS tracks
    # but Run-12 didn't surface (Visalia hasn't deployed it). Adding
    # it here so the detector fires correctly on jurisdictions that
    # have, and so its absence in Visalia is auditable rather than a
    # blind spot.
    VendorSignature(
        name="Verkada",
        category="other",  # video / cloud surveillance
        patterns=(r"\bverkada\b",),
        governance_required=("retention_policy", "council_approval"),
    ),
    # v2.9.3 E.2 — T-Mobile turns up in Tulare County procurement records
    # as the cellular backhaul provider for ALPR + BWC deployments. Not
    # itself a surveillance product, but its presence on a procurement
    # contract names the carrier responsible for video upload, which
    # matters for retention-policy and CJIS-data-routing review.
    VendorSignature(
        name="T-Mobile",
        category="other",  # telecom backhaul
        patterns=(r"\bt-?mobile\b",),
    ),
)


# ---------------------------------------------------------------------------
# Surveillance technology signatures (vendor-agnostic)
# ---------------------------------------------------------------------------

SURVEILLANCE_TECH: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "alpr",
        (
            r"\bautomated\s+license\s+plate\s+reader",
            r"\blicense\s+plate\s+reader",
            r"\balpr\b",
            r"\bplate\s+reader\s+system",
            r"\bvehicle\s+recognition\s+system",
        ),
    ),
    (
        "bwc",
        (
            r"\bbody[-\s]?worn\s+camer(?:a|as)",
            r"\bbwc\s+(?:program|system|contract|policy|deployment)",
            r"\bofficer\s+camera\s+system",
        ),
    ),
    (
        "drone_uas",
        (
            r"\bunmanned\s+aerial\s+system",
            r"\buas\s+program",
            r"\bdrone\s+program",
            r"\baerodome\b",
        ),
    ),
    (
        "facial_recognition",
        (
            r"\bfacial\s+recognition",
            r"\bface\s+recognition\s+system",
            r"\bbiometric\s+match(?:ing)?",
        ),
    ),
    (
        "ai_report_writing",
        (
            r"\bdraft\s*one\b",
            r"\bai[-\s]generated\s+reports?",
            r"\bautomated\s+report\s+writing",
        ),
    ),
    (
        "predictive_policing",
        (
            r"\bpredictive\s+policing",
            r"\bcrime\s+forecast(?:ing)?",
            r"\bhotspot\s+prediction",
        ),
    ),
    (
        "stingray_imsi",
        (
            r"\bstingray\b",
            r"\bcell\s+site\s+simulator",
            r"\bimsi\s+catcher",
        ),
    ),
    (
        "interview_room",
        (
            r"\binterview\s+room\s+camera",
            r"\bpatrol\s+vehicle\s+camera",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Statute and framework signatures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StatuteSignature:
    """A California or federal statute relevant to surveillance governance."""

    key: str
    citation: str
    short_name: str
    patterns: tuple[str, ...]
    effective_date: str | None = None
    triggers_when_missing: tuple[str, ...] = field(default_factory=tuple)


STATUTE_CATALOGUE: tuple[StatuteSignature, ...] = (
    StatuteSignature(
        key="sb_524",
        citation="California SB 524",
        short_name="SB 524 (AI Transparency)",
        patterns=(r"\bsb\s*524\b", r"\bsenate\s+bill\s+524\b"),
        effective_date="2026-01-01",
        triggers_when_missing=("ai_report_writing", "alpr"),
    ),
    StatuteSignature(
        key="ab_481",
        citation="California AB 481",
        short_name="AB 481 (Military Equipment Annual Report)",
        patterns=(
            r"\bab\s*481\b",
            r"\bassembly\s+bill\s+481\b",
            r"\bmilitary\s+equipment\s+use\s+policy",
            r"\bmilitary\s+equipment\s+annual\s+report",
        ),
        effective_date="2022-05-01",
        triggers_when_missing=("drone_uas",),
    ),
    StatuteSignature(
        key="sb_978",
        citation="California SB 978",
        short_name="SB 978 (Conspicuous Policy Posting)",
        patterns=(
            r"\bsb\s*978\b",
            r"\bsenate\s+bill\s+978\b",
            r"\bpost.*policies.*website",
            r"\bconspicuous(ly)?\s+post",
        ),
    ),
    StatuteSignature(
        key="alpr_privacy",
        citation="California Civil Code §§ 1798.90.5–1798.90.55",
        short_name="ALPR Privacy Act",
        patterns=(
            r"\bcivil\s+code\s+(?:§§?\s*)?1798\.90\.5\d?",
            r"\balpr\s+privacy\s+act",
            r"\busage\s+and\s+privacy\s+policy",
        ),
        triggers_when_missing=("alpr",),
    ),
    StatuteSignature(
        key="cjis",
        citation="FBI CJIS Security Policy",
        short_name="CJIS Security Policy",
        patterns=(
            r"\bcjis\b",
            r"\bcriminal\s+justice\s+information\s+services",
            r"\bcjis\s+security\s+(?:policy|addendum)",
        ),
        triggers_when_missing=("alpr", "bwc"),
    ),
    StatuteSignature(
        key="jag",
        citation="Edward Byrne Memorial Justice Assistance Grant",
        short_name="JAG (Edward Byrne)",
        patterns=(
            r"\bjag\s+(?:grant|program|allocation|fund)",
            r"\bedward\s+byrne\s+memorial",
            r"\bjustice\s+assistance\s+grant",
            r"\bbja\s+(?:grant|funding)",
            r"\bbureau\s+of\s+justice\s+assistance",
        ),
    ),
    StatuteSignature(
        key="cops",
        citation="COPS Hiring Grant",
        short_name="COPS (DOJ Hiring)",
        patterns=(
            r"\bcops\s+(?:hiring|grant|fund|allocation)",
            r"\bcommunity\s+oriented\s+policing\s+services",
        ),
    ),
    StatuteSignature(
        key="anti_supplanting",
        citation="JAG Anti-Supplanting Requirement",
        short_name="Anti-Supplanting Certification",
        patterns=(
            r"\banti[-\s]supplant(?:ing)?",
            r"\bsupplant(?:ing|ation)\b",
            r"\bnonsupplanting\b",
            r"\bmust\s+not\s+supplant",
        ),
    ),
    StatuteSignature(
        key="28_cfr_23",
        citation="28 CFR Part 23",
        short_name="28 CFR Part 23 (Criminal Intelligence)",
        patterns=(
            r"\b28\s+cfr\s+(?:part\s+)?23\b",
            r"\bcriminal\s+intelligence\s+systems",
        ),
    ),
    StatuteSignature(
        key="gov_code_sole_source",
        citation="California Gov Code § 10340 / § 10300–10334",
        short_name="Sole-Source Procurement Statute",
        patterns=(
            r"\bgov(?:ernment)?\s+code\s+(?:§§?\s*)?1034\d",
            r"\bgov(?:ernment)?\s+code\s+(?:§§?\s*)?10300",
            r"\bsole\s+source\s+justification",
        ),
    ),
)


# ---------------------------------------------------------------------------
# Procurement-irregularity patterns
# ---------------------------------------------------------------------------

CONSENT_CALENDAR_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bconsent\s+calendar\b",
        r"\bconsent\s+agenda\b",
    )
)

SOLE_SOURCE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bsole[\s-]source\b",
        r"\bsingle[\s-]source\b",
        r"\bno[\s-]bid\s+contract",
        r"\bproprietary\s+vendor",
        r"\bonly\s+(?:known\s+)?(?:source|provider|vendor)",
    )
)

AUTO_RENEWAL_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bautomatic(?:ally)?\s+renew",
        r"\bauto[-\s]renew(?:al)?",
        r"\brenew(?:s|ed)?\s+for\s+(?:an\s+)?additional",
        r"\brolling\s+(?:annual\s+)?renewal",
        r"\bevergreen\s+clause",
    )
)


# ---------------------------------------------------------------------------
# Pre-compiled matchers (memoised at import time)
# ---------------------------------------------------------------------------


def _compile_vendor_matchers() -> dict[str, list[re.Pattern[str]]]:
    return {
        v.name: [re.compile(p, re.IGNORECASE) for p in v.patterns]
        for v in VENDOR_CATALOGUE
    }


def _compile_tech_matchers() -> dict[str, list[re.Pattern[str]]]:
    return {
        tag: [re.compile(p, re.IGNORECASE) for p in patterns]
        for tag, patterns in SURVEILLANCE_TECH
    }


def _compile_statute_matchers() -> dict[str, list[re.Pattern[str]]]:
    return {
        s.key: [re.compile(p, re.IGNORECASE) for p in s.patterns]
        for s in STATUTE_CATALOGUE
    }


VENDOR_MATCHERS = _compile_vendor_matchers()
TECH_MATCHERS = _compile_tech_matchers()
STATUTE_MATCHERS = _compile_statute_matchers()

# Maps vendor name → vendor object for quick lookup
VENDOR_BY_NAME: dict[str, VendorSignature] = {v.name: v for v in VENDOR_CATALOGUE}
STATUTE_BY_KEY: dict[str, StatuteSignature] = {s.key: s for s in STATUTE_CATALOGUE}


# ---------------------------------------------------------------------------
# High-level detection functions
# ---------------------------------------------------------------------------


def detect_vendors(text: str) -> dict[str, list[str]]:
    """Return vendors mentioned in text, with the matching spans as evidence.

    Keys are vendor names (e.g. "Flock Safety"); values are up to 3 short
    text excerpts showing where the vendor was mentioned.
    """
    results: dict[str, list[str]] = {}
    for vendor_name, matchers in VENDOR_MATCHERS.items():
        snippets: list[str] = []
        for m in matchers:
            for match in m.finditer(text):
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                excerpt = text[start:end].replace("\n", " ").strip()
                if excerpt not in snippets:
                    snippets.append(excerpt)
                if len(snippets) >= 3:
                    break
            if len(snippets) >= 3:
                break
        if snippets:
            results[vendor_name] = snippets
    return results


def detect_technologies(text: str) -> dict[str, list[str]]:
    """Return surveillance technologies mentioned in text."""
    results: dict[str, list[str]] = {}
    for tag, matchers in TECH_MATCHERS.items():
        for m in matchers:
            matches = m.findall(text)
            if matches:
                results.setdefault(tag, []).extend(matches[:3])
    return results


def detect_statutes(text: str) -> set[str]:
    """Return the set of statute keys mentioned in text."""
    out: set[str] = set()
    for key, matchers in STATUTE_MATCHERS.items():
        if any(m.search(text) for m in matchers):
            out.add(key)
    return out


def detect_consent_calendar(text: str) -> bool:
    """True if the text references consent calendar / agenda placement."""
    return any(p.search(text) for p in CONSENT_CALENDAR_PATTERNS)


def detect_sole_source(text: str) -> bool:
    """True if the text references sole-source procurement."""
    return any(p.search(text) for p in SOLE_SOURCE_PATTERNS)


def detect_auto_renewal(text: str) -> bool:
    """True if the text references an auto-renewal clause."""
    return any(p.search(text) for p in AUTO_RENEWAL_PATTERNS)
