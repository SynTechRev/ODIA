"""L-8 Case-Law Currency Detector.

Checks whether case law cited in public-agency documents remains good law.
Two operational modes:

  LOCAL (default): Static treatment table of cases with known adverse
    signals in the CPRA / surveillance / due-process domains. No network
    calls. Runs on every document without configuration.

  LIVE (opt-in): Set COURTLISTENER_API_KEY environment variable to enable
    on-demand treatment lookups via the CourtListener citation API. Local
    table results are always included; live lookups supplement them.
    This is the only outbound network call in ODIA and is explicitly
    opt-in to preserve local-first architecture.

Checks:
  1. Pre-Carpenter third-party doctrine — Smith v. Maryland, United States
     v. Miller, or Knotts cited in a surveillance context without
     acknowledging Carpenter's limitation. Severity: medium.

  2. Knotts location-tracking doctrine — cited for public-roads tracking
     without noting Jones (2012) or Carpenter (2018). Severity: medium.

  3. Pre-recodification CPRA case currency — CPRA cases cited by
     pre-2022 framework without a recodification note. Severity: low.
     (Complements L-9 which handles statutory citation numbers.)

  4. CourtListener live treatment (opt-in) — negative/overruled signals
     returned by CourtListener for detected citations. Severity: medium.
"""

from __future__ import annotations

import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Citation patterns
# ---------------------------------------------------------------------------

_SMITH_MARYLAND_RE = re.compile(r"\bsmith\s+v\.?\s+maryland\b", re.IGNORECASE)
_MILLER_US_RE = re.compile(r"\bunited\s+states\s+v\.?\s+miller\b", re.IGNORECASE)
_KNOTTS_RE = re.compile(r"\bknotts\s+v\.?\s+united\s+states\b", re.IGNORECASE)

# Surveillance context — triggers pre-Carpenter third-party checks
_SURVEILLANCE_RE = re.compile(
    r"\b(?:alpr|license\s+plate\s+reader|lpr|csli|cell.site|geofence|"
    r"stingray|gps\s+(?:tracking|data)|location\s+(?:data|tracking)|"
    r"persistent\s+(?:surveillance|tracking)|third.party\s+doctrine|"
    r"third\s+party\s+doctrine)\b",
    re.IGNORECASE,
)

# Carpenter present — if cited, pre-Carpenter checks pass
_CARPENTER_RE = re.compile(r"\bcarpenter\b", re.IGNORECASE)

# Pre-recodification CPRA case short-names (no trailing \b — pattern ends with a literal
# dot which is non-word, making \b unmatchable before a space)
_OLD_CPRA_CASES_RE = re.compile(
    r"\b(?:CBS\s+Inc\.|Times\s+Mirror\s+Co\.|City\s+of\s+San\s+Jose\s+v\.\s+Superior|"
    r"Braun\s+v\.\s+City|Register\s+Div\.|Connell\s+v\.\s+Superior)",
    re.IGNORECASE,
)

# Recodification acknowledged
_RECODIFICATION_NOTE_RE = re.compile(
    r"\b(?:recodif|renumber|7920|7921|7922|january\s+1\s*,?\s*2023|"
    r"cpra\s+2021|ab\s+473)\b",
    re.IGNORECASE,
)

# CourtListener citation extraction — "Name v. Name (YYYY)"
_CITATION_RE = re.compile(
    r"\b([A-Z][A-Za-z\s&,.'-]{2,40}?)\s+v\.?\s+([A-Z][A-Za-z\s&,.'-]{2,40}?)"
    r"(?:\s*[\(,]\s*\d{4}\s*[\),])?",
    re.MULTILINE,
)

# ---------------------------------------------------------------------------
# Static treatment table
# ---------------------------------------------------------------------------

_TREATMENT_TABLE: dict[str, dict[str, str]] = {
    "smith_v_maryland": {
        "citation": "Smith v. Maryland (1979) 442 U.S. 735",
        "treatment": "limited",
        "limitation": (
            "Third-party doctrine for pen registers significantly narrowed by "
            "Carpenter v. United States (2018) 585 U.S. 296 for comprehensive "
            "digital location data and CSLI. Smith v. Maryland cannot be cited "
            "as controlling authority for ALPR, CSLI, or persistent tracking "
            "without acknowledging Carpenter's limitation."
        ),
        "current_authority": "Carpenter v. United States (2018) 585 U.S. 296",
        "severity": "medium",
    },
    "us_v_miller": {
        "citation": "United States v. Miller (1976) 425 U.S. 435",
        "treatment": "limited",
        "limitation": (
            "Third-party doctrine for financial records narrowed by Carpenter (2018) "
            "as applied to comprehensive digital records revealing personal patterns. "
            "Miller should not be cited without Carpenter analysis for modern "
            "data types."
        ),
        "current_authority": "Carpenter v. United States (2018) 585 U.S. 296",
        "severity": "medium",
    },
    "knotts_v_us": {
        "citation": "Knotts v. United States (1983) 460 U.S. 276",
        "treatment": "limited",
        "limitation": (
            "Public-roads tracking doctrine for single-trip beeper surveillance "
            "limited by United States v. Jones (2012) 565 U.S. 400 (28-day GPS) "
            "and Carpenter (2018) (7-day CSLI). Long-term or aggregate location "
            "tracking requires individualized suspicion analysis."
        ),
        "current_authority": (
            "United States v. Jones (2012) 565 U.S. 400; "
            "Carpenter v. United States (2018) 585 U.S. 296"
        ),
        "severity": "medium",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _make_finding(
    rule_id: str, issue: str, severity: str, details: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": f"legal:l8:case_law_currency:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l8_case_law_currency",
        "details": details,
    }


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def _check_pre_carpenter_third_party(text: str) -> list[dict[str, Any]]:
    """Flag Smith/Miller/Knotts citations in surveillance context without Carpenter."""
    findings: list[dict[str, Any]] = []

    if not _SURVEILLANCE_RE.search(text):
        return findings
    if _CARPENTER_RE.search(text):
        return findings  # Carpenter acknowledged — no finding

    if _SMITH_MARYLAND_RE.search(text):
        e = _TREATMENT_TABLE["smith_v_maryland"]
        findings.append(
            _make_finding(
                "smith_v_maryland_third_party_stale",
                "Smith v. Maryland cited in surveillance context without Carpenter "
                "acknowledgment — third-party doctrine limited by Carpenter (2018)",
                e["severity"],
                {
                    "cited_case": e["citation"],
                    "treatment": e["treatment"],
                    "limitation": e["limitation"],
                    "current_authority": e["current_authority"],
                },
            )
        )

    if _MILLER_US_RE.search(text):
        e = _TREATMENT_TABLE["us_v_miller"]
        findings.append(
            _make_finding(
                "us_v_miller_third_party_stale",
                "United States v. Miller cited in surveillance context "
                "without Carpenter acknowledgment — third-party doctrine "
                "limited by Carpenter (2018)",
                e["severity"],
                {
                    "cited_case": e["citation"],
                    "treatment": e["treatment"],
                    "limitation": e["limitation"],
                    "current_authority": e["current_authority"],
                },
            )
        )

    if _KNOTTS_RE.search(text):
        e = _TREATMENT_TABLE["knotts_v_us"]
        findings.append(
            _make_finding(
                "knotts_location_tracking_stale",
                "Knotts v. United States cited for location tracking without noting "
                "Jones (2012) and Carpenter (2018) limitations",
                e["severity"],
                {
                    "cited_case": e["citation"],
                    "treatment": e["treatment"],
                    "limitation": e["limitation"],
                    "current_authority": e["current_authority"],
                },
            )
        )

    return findings


def _check_cpra_case_currency(text: str) -> list[dict[str, Any]]:
    """Flag pre-recodification CPRA case citations without a recodification note."""
    if not _OLD_CPRA_CASES_RE.search(text):
        return []
    if _RECODIFICATION_NOTE_RE.search(text):
        return []

    return [
        _make_finding(
            "pre_recodification_cpra_case_currency",
            "Pre-2022 CPRA case law cited without recodification note — verify "
            "holding current under recodified CPRA (Gov. Code §§ 7920.000 et seq.)",
            "low",
            {
                "detail": (
                    "The California Public Records Act was recodified effective "
                    "January 1, 2023 (AB 473, 2021). Pre-recodification holdings "
                    "remain substantively valid but should be cross-referenced to "
                    "recodified sections: § 6250 → § 7920.000; § 6255 → § 7922.000."
                ),
                "current_statute": "Gov. Code §§ 7920.000 et seq. (eff. Jan. 1, 2023)",
            },
        )
    ]


def _live_treatment_check(text: str) -> list[dict[str, Any]]:
    """Query CourtListener for negative treatment signals on detected citations.

    Only runs when COURTLISTENER_API_KEY is set. Supplemental to static checks.
    Maximum 5 API calls per document to limit latency.
    """
    api_key = os.environ.get("COURTLISTENER_API_KEY", "").strip()
    if not api_key:
        return []

    findings: list[dict[str, Any]] = []
    try:
        import json as _json
        import urllib.parse
        import urllib.request

        raw_citations = _CITATION_RE.findall(text)
        unique = list(
            {
                f"{p.strip()} v. {d.strip()}"
                for p, d in raw_citations
                if 3 < len(p.strip()) < 50 and 3 < len(d.strip()) < 50
            }
        )[:5]

        for cite in unique:
            url = (
                "https://www.courtlistener.com/api/rest/v3/citation-lookup/"
                f"?citation={urllib.parse.quote(cite)}"
            )
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Token {api_key}",
                    "User-Agent": "ODIA-LegalDetector/3.8",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = _json.loads(resp.read().decode("utf-8"))
                negative = [
                    t
                    for t in data.get("treatment_signals", [])
                    if t.get("type") in ("negative", "overruled", "distinguished")
                ]
                if negative:
                    slug = re.sub(r"[^a-z0-9]", "_", cite[:30].lower())
                    findings.append(
                        _make_finding(
                            f"courtlistener_negative_{slug}",
                            f"CourtListener reports negative treatment for '{cite}'",
                            "medium",
                            {
                                "cited_case": cite,
                                "treatment_signals": negative[:3],
                                "source": "CourtListener API (live lookup)",
                                "detail": (
                                    "Verify this case remains good law before "
                                    "relying on it in a legal argument."
                                ),
                            },
                        )
                    )
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass

    return findings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-8 Case-Law Currency detection on a single document.

    Local static table checks always run. CourtListener live lookups
    run only when COURTLISTENER_API_KEY is set in the environment.
    """
    text = _get_text(doc)
    if not text:
        return []

    return (
        _check_pre_carpenter_third_party(text)
        + _check_cpra_case_currency(text)
        + _live_treatment_check(text)
    )
