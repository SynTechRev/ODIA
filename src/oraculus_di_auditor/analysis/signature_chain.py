"""Signature Chain Detector.

Detects unsigned, partially signed, or placeholder-signed compliance documents
in a contract chain. Flags cases where a contract instrument contains signature
gap indicators or unresolved placeholder tokens, which may indicate the document
was executed without valid assent from one or more required parties.
"""

from __future__ import annotations

import re
from typing import Any

from .text_utils import extract_text_content

# Patterns indicating a blank or missing signature block
SIGNATURE_GAP_PATTERNS = [
    r"\bsignature\s+block\s+blank\b",
    r"\bunsigned\b",
    r"\bnot\b.{0,20}\bexecuted\b",
    r"\bplaceholder\b",
    r"_{5,}",  # five or more underscores (blank signature line)
    r"\bDocuSign\b.{0,80}\bpending\b",  # DocuSign envelope not yet completed
    r"\bone\s+party\s+signed\b",
    r"\bagency\s+signature\s+missing\b",
    r"\bvendor\s+signature\s+only\b",
    r"\bcity\s+signature\s+blank\b",
]

# Literal placeholder tokens used by contract-assembly tools
PLACEHOLDER_PATTERN = re.compile(
    r"\\s1\\|\\d1\\|\[SIGNATURE\]",
    re.IGNORECASE,
)

# Contract instrument keywords
CONTRACT_INSTRUMENT_PATTERN = re.compile(
    r"\b(?:MSPA|MSA|PSA|SOW|MOU|agreement|contract|amendment|order\s+form)\b",
    re.IGNORECASE,
)

# Fiscal amount pattern (reused from fiscal layer)
_FISCAL_AMOUNT_PATTERN = re.compile(
    r"\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s*\d+(?:\.\d+)?\s*[MBT](?:illion)?",
    re.IGNORECASE,
)

# Compiled signature gap patterns (IGNORECASE applied individually)
_COMPILED_GAP_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in SIGNATURE_GAP_PATTERNS
]


def _detect_signature_gaps(text: str) -> list[str]:
    """Return each gap-pattern string that matched in *text*."""
    matched = []
    for pattern in _COMPILED_GAP_PATTERNS:
        if pattern.search(text):
            matched.append(pattern.pattern)
    return matched


def _nearest_instrument(text: str, gap_match: re.Match) -> str | None:  # type: ignore[type-arg]
    """Return the contract instrument keyword closest to *gap_match* in *text*."""
    gap_pos = gap_match.start()
    best_word: str | None = None
    best_dist = float("inf")
    for m in CONTRACT_INSTRUMENT_PATTERN.finditer(text):
        dist = abs(m.start() - gap_pos)
        if dist < best_dist:
            best_dist = dist
            best_word = m.group(0).upper()
    return best_word


def detect_signature_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify signature chain anomalies in a normalized document.

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

    has_instrument = bool(CONTRACT_INSTRUMENT_PATTERN.search(text_content))
    dollar_amounts = _FISCAL_AMOUNT_PATTERN.findall(text_content)

    # Check 1: Signature gap patterns near a contract instrument keyword
    if has_instrument:
        gap_matches: list[re.Match] = []  # type: ignore[type-arg]
        gap_types: list[str] = []
        for pattern in _COMPILED_GAP_PATTERNS:
            m = pattern.search(text_content)
            if m:
                gap_matches.append(m)
                gap_types.append(pattern.pattern)

        if gap_matches:
            # Use the first match to find the nearest instrument keyword
            instrument_type = _nearest_instrument(text_content, gap_matches[0]) or "UNKNOWN"
            severity = "critical" if dollar_amounts else "high"
            anomalies.append(
                {
                    "id": "signature:unsigned-instrument",
                    "issue": (
                        f"Signature gap detected in {instrument_type} instrument"
                    ),
                    "severity": severity,
                    "layer": "signature",
                    "details": {
                        "instrument_type": instrument_type,
                        "signature_gap_type": gap_types[0],
                        "gap_pattern_count": len(gap_matches),
                        "dollar_amount": dollar_amounts[0] if dollar_amounts else None,
                    },
                }
            )

    # Check 2: Placeholder tokens anywhere in the document
    placeholder_match = PLACEHOLDER_PATTERN.search(text_content)
    if placeholder_match:
        anomalies.append(
            {
                "id": "signature:placeholder-tokens",
                "issue": "Unresolved signature placeholder token found in document",
                "severity": "high",
                "layer": "signature",
                "details": {
                    "token": placeholder_match.group(0),
                    "position": placeholder_match.start(),
                },
            }
        )

    return anomalies
