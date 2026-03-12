"""Fiscal Trail Analyzer.

Detects potential gaps or inconsistencies in appropriation and fiscal lineage.

Initial heuristic is intentionally conservative and returns no findings unless
clear structural signals are present. This will evolve to incorporate
recursive scalar patterning for budgetary references and lineage mapping.
"""

from __future__ import annotations

import re
from typing import Any

from .text_utils import extract_text_content

# Fiscal keywords indicating appropriation or budget references
APPROPRIATION_KEYWORDS = [
    "appropriation",
    "appropriated",
    "budget",
    "expenditure",
    "funding",
    "allocation",
    "fiscal year",
]

# Fiscal amount pattern (e.g., $1,000,000 or $1M)
FISCAL_AMOUNT_PATTERN = re.compile(
    r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s*\d+(?:\.\d+)?\s*[MBT](?:illion)?",
    re.IGNORECASE,
)


def detect_fiscal_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify fiscal anomalies in a normalized legislative document.

    Args:
        doc: Normalized document dict

    Returns:
        List of anomaly records; empty if none found.
    """
    anomalies: list[dict[str, Any]] = []

    if not isinstance(doc, dict):
        return anomalies

    # Check 1: Provenance integrity
    prov = doc.get("provenance", {})
    if not isinstance(prov, dict) or not prov.get("hash"):
        anomalies.append(
            {
                "id": "fiscal:missing-provenance-hash",
                "issue": "Provenance hash missing; integrity trail incomplete",
                "severity": "low",
                "layer": "fiscal",
                "details": {"provenance_present": bool(prov)},
            }
        )

    # Check 2: Appropriation trail - detect fiscal amounts without
    # appropriation reference
    text_content = extract_text_content(doc)
    if text_content:
        fiscal_amounts = FISCAL_AMOUNT_PATTERN.findall(text_content)
        has_appropriation_ref = any(
            keyword in text_content.lower() for keyword in APPROPRIATION_KEYWORDS
        )

        if fiscal_amounts and not has_appropriation_ref:
            anomalies.append(
                {
                    "id": "fiscal:amount-without-appropriation",
                    "issue": "Fiscal amounts present without appropriation reference",
                    "severity": "medium",
                    "layer": "fiscal",
                    "details": {
                        "amount_count": len(fiscal_amounts),
                        "sample_amounts": fiscal_amounts[:3],  # First 3 for brevity
                    },
                }
            )

    return anomalies
