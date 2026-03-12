"""Governance Gap Detector.

Detects surveillance or monitoring capabilities deployed without corresponding
governance documentation — policies, oversight frameworks, access controls, or
legal authority. Absence of governance documentation alongside capability
deployment is a structural anomaly regardless of the capability's legality.
"""

from __future__ import annotations

from typing import Any

from .text_utils import extract_text_content

# ---------------------------------------------------------------------------
# Capability keyword sets
# ---------------------------------------------------------------------------

# Surveillance technology — triggers critical severity when ungoverned
SURVEILLANCE_TECH_KEYWORDS = [
    "alpr",
    "license plate reader",
    "body camera",
    "bwc",
    "facial recognition",
    "drone",
    "uas",
    "real-time",
    "geofence",
    "cell site simulator",
    "stingray",
    "predictive policing",
]

# Data-handling capabilities — triggers high severity when ungoverned
DATA_CAPABILITY_KEYWORDS = [
    "data sharing",
    "data retention",
    "cloud storage",
    "third-party access",
    "federal access",
    "interagency",
]

# AI/automation capabilities — triggers high severity when ungoverned
AI_CAPABILITY_KEYWORDS = [
    "automated",
    "ai-generated",
    "machine learning",
    "draft one",
    "report writing",
]

# All capability keywords combined (for general capability detection)
ALL_CAPABILITY_KEYWORDS = (
    SURVEILLANCE_TECH_KEYWORDS + DATA_CAPABILITY_KEYWORDS + AI_CAPABILITY_KEYWORDS
)

# ---------------------------------------------------------------------------
# Governance keyword sets
# ---------------------------------------------------------------------------

GOVERNANCE_KEYWORDS = [
    # Policy
    "privacy policy",
    "use policy",
    "retention policy",
    "access control",
    "audit log",
    "oversight",
    "governance framework",
    # Legal authority
    "warrant",
    "court order",
    "probable cause",
    "privacy impact assessment",
    "civil liberties",
    "cjis",
    # Public process
    "public hearing",
    "council approval",
    "community input",
    "transparency report",
]

# Retention-specific governance keywords (for data-retention gap check)
RETENTION_GOVERNANCE_KEYWORDS = [
    "retention policy",
    "data retention policy",
    "retention schedule",
    "purge",
    "deletion policy",
]

# Data sharing/retention capability keywords (for data-retention gap check)
DATA_SHARING_RETENTION_KEYWORDS = [
    "data sharing",
    "data retention",
    "third-party access",
    "federal access",
    "interagency",
]


def detect_governance_gap_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify governance gap anomalies in a normalized document.

    Args:
        doc: Normalized document dict

    Returns:
        List of anomaly records; empty if none found.
    """
    anomalies: list[dict[str, Any]] = []

    if not isinstance(doc, dict):
        return anomalies

    text_content = extract_text_content(doc)
    if not text_content:
        return anomalies

    text_lower = text_content.lower()

    # Identify which capability and governance keywords are present
    surveillance_found = [kw for kw in SURVEILLANCE_TECH_KEYWORDS if kw in text_lower]
    data_found = [kw for kw in DATA_CAPABILITY_KEYWORDS if kw in text_lower]
    ai_found = [kw for kw in AI_CAPABILITY_KEYWORDS if kw in text_lower]
    capabilities_found = surveillance_found + data_found + ai_found

    governance_found = [kw for kw in GOVERNANCE_KEYWORDS if kw in text_lower]
    governance_missing = [kw for kw in GOVERNANCE_KEYWORDS if kw not in text_lower]

    # Check 1: Capabilities present without governance documentation
    if capabilities_found and not governance_found:
        # Severity is critical for surveillance tech, high for data/AI only
        severity = "critical" if surveillance_found else "high"
        anomalies.append(
            {
                "id": "governance:capability-without-policy",
                "issue": (
                    "Surveillance or monitoring capability deployed without "
                    "governance documentation"
                ),
                "severity": severity,
                "layer": "governance",
                "details": {
                    "capabilities_found": capabilities_found,
                    "governance_keywords_missing": governance_missing,
                    "capability_count": len(capabilities_found),
                    "governance_count": 0,
                },
            }
        )

    # Check 2: Data sharing or retention present without retention policy
    data_sharing_present = any(
        kw in text_lower for kw in DATA_SHARING_RETENTION_KEYWORDS
    )
    retention_policy_present = any(
        kw in text_lower for kw in RETENTION_GOVERNANCE_KEYWORDS
    )

    if data_sharing_present and not retention_policy_present:
        data_keywords_found = [
            kw for kw in DATA_SHARING_RETENTION_KEYWORDS if kw in text_lower
        ]
        anomalies.append(
            {
                "id": "governance:data-retention-gap",
                "issue": (
                    "Data sharing or retention capability found without "
                    "retention policy reference"
                ),
                "severity": "high",
                "layer": "governance",
                "details": {
                    "data_keywords_found": data_keywords_found,
                    "retention_keywords_checked": RETENTION_GOVERNANCE_KEYWORDS,
                },
            }
        )

    return anomalies
