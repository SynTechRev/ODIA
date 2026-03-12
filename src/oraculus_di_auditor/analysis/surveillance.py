"""Surveillance Outsourcing Detector.

Surfaces potential outsourcing of surveillance functions to private vendors
and associated privacy risks. This initial version is a safe placeholder that
returns no anomalies until rule heuristics are implemented.
"""

from __future__ import annotations

from typing import Any

from .text_utils import extract_text_content

# Surveillance-related keywords
SURVEILLANCE_KEYWORDS = [
    "surveillance",
    "monitoring",
    "tracking",
    "biometric",
    "facial recognition",
    "data collection",
    "wiretap",
    "intercept",
    "metadata",
    "geolocation",
    "cell site",
    "stingray",
]

# Private contractor indicators
CONTRACTOR_KEYWORDS = [
    "contractor",
    "vendor",
    "third party",
    "private entity",
    "service provider",
]

# Privacy safeguard indicators
SAFEGUARD_KEYWORDS = [
    "warrant",
    "probable cause",
    "court order",
    "judicial authorization",
    "minimization",
    "oversight",
    "privacy protection",
    "data retention limit",
]


def detect_surveillance_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify surveillance outsourcing anomalies.

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

    # Check 1: Surveillance + contractor without safeguards
    has_surveillance = any(keyword in text_lower for keyword in SURVEILLANCE_KEYWORDS)
    has_contractor = any(keyword in text_lower for keyword in CONTRACTOR_KEYWORDS)
    has_safeguards = any(keyword in text_lower for keyword in SAFEGUARD_KEYWORDS)

    if has_surveillance and has_contractor and not has_safeguards:
        # Find specific surveillance keywords present
        surveillance_found = [kw for kw in SURVEILLANCE_KEYWORDS if kw in text_lower]
        contractor_found = [kw for kw in CONTRACTOR_KEYWORDS if kw in text_lower]

        anomalies.append(
            {
                "id": "surveillance:outsourced-without-safeguards",
                "issue": "Surveillance outsourcing detected without privacy safeguards",
                "severity": "high",
                "layer": "surveillance",
                "details": {
                    "surveillance_keywords": surveillance_found[:3],
                    "contractor_keywords": contractor_found[:2],
                },
            }
        )
    elif has_surveillance and has_contractor and has_safeguards:
        # Surveillance with safeguards - informational only
        anomalies.append(
            {
                "id": "surveillance:outsourced-with-safeguards",
                "issue": "Surveillance outsourcing detected with some safeguards",
                "severity": "low",
                "layer": "surveillance",
                "details": {"requires_review": True},
            }
        )

    return anomalies
