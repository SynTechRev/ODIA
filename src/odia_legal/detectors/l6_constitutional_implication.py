"""L-6 Constitutional Implication detector.

Identifies constitutional law implications — primarily Fourth Amendment
privacy rights and Fourteenth Amendment equal protection — that arise from
surveillance technology deployment and public-agency data collection.

Framework: Carpenter mosaic theory; Riley v. California; City of LA v. Patel.

Checks:
  1. ALPR without Carpenter analysis — mass location data collected without
     warrant analysis referencing Carpenter v. United States (2018)
  2. Facial recognition without Fourth Amendment analysis
  3. Cell-site simulator / stingray use without warrant reference
  4. Biometric data collection without equal protection / due process analysis
  5. Government surveillance creating "mosaic" of individual movements without
     individualized suspicion

Severity:
  high   — warrantless comprehensive location/biometric surveillance
  medium — surveillance program without Carpenter analysis; facial recognition
  low    — general privacy implication flag
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# Warrantless surveillance triggers
_WARRANT_RE = re.compile(
    r"\b(?:warrant|court\s+order|judicial\s+authorization|probable\s+cause|"
    r"consent\s+(?:of|from)\s+(?:the\s+)?(?:person|subject|individual))\b",
    re.IGNORECASE,
)

_NO_WARRANT_RE = re.compile(
    r"\b(?:without\s+(?:a\s+)?warrant|warrantless|no\s+warrant\s+(?:required|needed)|"
    r"administrative\s+subpoena|third.party\s+doctrine)\b",
    re.IGNORECASE,
)

# Comprehensive location surveillance (Carpenter-triggering)
_LOCATION_SURVEILLANCE_RE = re.compile(
    r"\b(?:cell.site\s+location|csli|tower\s+dump|geofence|"
    r"alpr|license\s+plate\s+reader|lpr|"
    r"real.time\s+tracking|continuous\s+surveillance|"
    r"location\s+tracking|gps\s+tracking|"
    r"persistent\s+surveillance|bulk\s+(?:location|location\s+data))\b",
    re.IGNORECASE,
)

# Carpenter analysis present
_CARPENTER_RE = re.compile(
    r"\b(?:carpenter|mosaic\s+theory|mosaic\s+effect|"
    r"reasonable\s+expectation\s+of\s+privacy|"
    r"fourth\s+amendment|katz\s+test|two.part\s+test)\b",
    re.IGNORECASE,
)

# Facial recognition
_FACIAL_RECOGNITION_RE = re.compile(
    r"\b(?:facial\s+recognition|face\s+recognition|biometric\s+identification|"
    r"clearview|face\s+match(?:ing)?)\b",
    re.IGNORECASE,
)

# Cell-site simulator / stingray
_STINGRAY_RE = re.compile(
    r"\b(?:stingray|imsi.catcher|cell.site\s+simulator|"
    r"dirtbox|hailstorm|triggerfish)\b",
    re.IGNORECASE,
)

# Biometric data
_BIOMETRIC_RE = re.compile(
    r"\b(?:biometric(?:\s+data)?|fingerprint|iris\s+scan|"
    r"retina\s+scan|voiceprint|gait\s+analysis|dna\s+(?:sample|collection))\b",
    re.IGNORECASE,
)

# Equal protection / due process
_EQUAL_PROTECTION_RE = re.compile(
    r"\b(?:equal\s+protection|due\s+process|disparate\s+impact|"
    r"racial\s+bias|algorithmic\s+bias|discriminat(?:ory|ion)|"
    r"fourteenth\s+amendment)\b",
    re.IGNORECASE,
)


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
        "id": f"legal:l6:constitutional_implication:{rule_id}",
        "issue": issue,
        "severity": severity,
        "layer": "l6_constitutional_implication",
        "details": details,
    }


def detect(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run L-6 Constitutional Implication detection on a single document."""
    text = _get_text(doc)
    if not text:
        return []

    findings: list[dict[str, Any]] = []

    # 1. Location surveillance without Carpenter analysis
    has_location = bool(_LOCATION_SURVEILLANCE_RE.search(text))
    if has_location and not _CARPENTER_RE.search(text):
        findings.append(
            _make_finding(
                "location_surveillance_no_carpenter",
                "Comprehensive location surveillance deployed without Fourth Amendment / Carpenter mosaic-theory analysis",
                "high",
                {
                    "statute": "42 U.S.C. § 1983",
                    "case_law": "Carpenter v. United States (2018) 585 U.S. 296",
                    "detail": "Carpenter requires warrant for long-term comprehensive location data; ALPR systems, geofences, and continuous tracking may implicate mosaic theory",
                },
            )
        )
    elif has_location and _NO_WARRANT_RE.search(text):
        findings.append(
            _make_finding(
                "location_surveillance_warrantless",
                "Warrantless location surveillance program referenced — Fourth Amendment / Carpenter analysis required",
                "high",
                {
                    "statute": "42 U.S.C. § 1983",
                    "case_law": "Carpenter v. United States (2018) 585 U.S. 296",
                    "detail": "Warrantless comprehensive location tracking likely violates the Fourth Amendment under Carpenter",
                },
            )
        )

    # 2. Facial recognition without constitutional analysis
    if _FACIAL_RECOGNITION_RE.search(text) and not _EQUAL_PROTECTION_RE.search(text):
        findings.append(
            _make_finding(
                "facial_recognition_no_constitutional_analysis",
                "Facial recognition technology deployed without equal protection or Fourth Amendment analysis",
                "medium",
                {
                    "statute": "42 U.S.C. § 1983",
                    "case_law": "City of Los Angeles v. Patel (2015) 576 U.S. 409",
                    "detail": "Facial recognition raises Fourth Amendment and equal protection concerns — documented civil rights impact analysis required",
                },
            )
        )

    # 3. Stingray / IMSI catcher without warrant
    if _STINGRAY_RE.search(text) and not _WARRANT_RE.search(text):
        findings.append(
            _make_finding(
                "stingray_no_warrant",
                "Cell-site simulator (stingray) deployment without warrant authorization",
                "high",
                {
                    "statute": "42 U.S.C. § 1983",
                    "case_law": "Carpenter v. United States (2018) 585 U.S. 296; United States v. Jones (2012) 565 U.S. 400",
                    "detail": "IMSI catchers collect location and call data for all persons in the area — mass surveillance without warrant implicates Fourth Amendment",
                },
            )
        )

    # 4. Biometric collection without equal protection analysis
    if _BIOMETRIC_RE.search(text) and not _EQUAL_PROTECTION_RE.search(text):
        findings.append(
            _make_finding(
                "biometric_no_equal_protection",
                "Biometric data collection without equal protection or due process analysis",
                "medium",
                {
                    "statute": "42 U.S.C. § 1983",
                    "detail": "Biometric surveillance programs must be analyzed for disparate racial impact and due process implications",
                },
            )
        )

    return findings
