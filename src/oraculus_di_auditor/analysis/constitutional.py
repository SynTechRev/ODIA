"""Constitutional Conformity Analyzer.

Flags patterns suggestive of unconstitutional delegation or conflicts between
statutes and constitutional constraints. Initial version is a no-op placeholder
that returns no anomalies to preserve stability; logic will grow iteratively.
"""

from __future__ import annotations

import re
from typing import Any

from .text_utils import extract_text_content

# Delegation patterns indicating potentially problematic grants of authority
DELEGATION_PATTERNS = [
    r"\b(?:Secretary|Administrator|Director|Commissioner)\s+(?:may|shall)\s+(?:determine|prescribe|establish|define)",
    r"\b(?:as|in)\s+(?:the\s+)?(?:Secretary|Administrator|Director|Commissioner)\s+(?:deems?|determines?)",
    r"\bsuch\s+(?:rules?|regulations?|standards?)\s+as\s+(?:may\s+be\s+)?(?:necessary|appropriate|desirable)",
    r"\bin\s+(?:his|her|their)\s+discretion",
]

# Constitutional reference patterns
CONSTITUTIONAL_REFERENCE_PATTERN = re.compile(
    r"\b(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|"
    r"Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth|Sixteenth|Seventeenth|"
    r"Eighteenth|Nineteenth|Twentieth|Twenty-First|Twenty-Second|Twenty-Third|"
    r"Twenty-Fourth|Twenty-Fifth|Twenty-Sixth|Twenty-Seventh)\s+Amendment",
    re.IGNORECASE,
)


def detect_constitutional_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify constitutional anomalies in a normalized legislative document.

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

    # Check 1: Broad delegation without standards
    delegation_matches = []
    for pattern in DELEGATION_PATTERNS:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        delegation_matches.extend(matches)

    if delegation_matches:
        # Check if intelligible principle is present
        has_standards = _has_limiting_standards(text_content)

        if not has_standards:
            anomalies.append(
                {
                    "id": "constitutional:broad-delegation",
                    "issue": "Broad delegation of authority without clear standards",
                    "severity": "medium",
                    "layer": "constitutional",
                    "details": {
                        "delegation_count": len(delegation_matches),
                        "sample": delegation_matches[0] if delegation_matches else "",
                    },
                }
            )

    return anomalies


def _has_limiting_standards(text: str) -> bool:
    """Check if text contains limiting standards or intelligible principles."""
    # Keywords indicating limiting standards
    standard_keywords = [
        "standard",
        "criteria",
        "guideline",
        "requirement",
        "limitation",
        "restriction",
        "subject to",
        "consistent with",
        "in accordance with",
        "pursuant to",
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in standard_keywords)
