"""Scope Expansion Detector.

Detects the "amendment-as-procurement" pattern: contract amendments or renewals
that expand significantly beyond the original authorization scope, potentially
circumventing competitive procurement requirements.

Three findings:
  scope:significant-expansion  — amendment with a dollar amount >50% above another
  scope:amendment-without-baseline — amendment with no original authorization reference
  scope:sole-source-expansion  — sole-source justification combined with an amendment
"""

from __future__ import annotations

import re
from typing import Any

from .fiscal import FISCAL_AMOUNT_PATTERN
from .text_utils import extract_text_content

# Amendment / renewal instrument keywords
AMENDMENT_KEYWORDS = [
    "amendment",
    "renewal",
    "extension",
    "modification",
    "change order",
    "supplemental",
    "addendum",
]

# Original authorization / baseline reference keywords
BASELINE_KEYWORDS = [
    "original contract",
    "base contract",
    "initial authorization",
    "approved amount",
    "not to exceed",
]

# Sole-source procurement pattern
_SOLE_SOURCE_PATTERN = re.compile(
    r"\bsole[\s-]source\b|\bsingle\s+source\b",
    re.IGNORECASE,
)

# Multiplier map for M/B/T suffixes (handles "Million", "Billion", "Trillion")
_SUFFIX_MULTIPLIERS: dict[str, float] = {
    "m": 1_000_000.0,
    "b": 1_000_000_000.0,
    "t": 1_000_000_000_000.0,
}

# Expansion threshold (50 %)
_EXPANSION_THRESHOLD = 0.50


def _parse_dollar_amount(raw: str) -> float | None:
    """Convert a matched dollar string to a float, handling M/B/T suffixes.

    Examples:
        "$1,000,000"  → 1_000_000.0
        "$1.5M"       → 1_500_000.0
        "$2 Billion"  → 2_000_000_000.0
    """
    s = raw.replace("$", "").replace(",", "").strip()
    # Strip the "illion" tail so "Million" → "M", "Billion" → "B", etc.
    if s.lower().endswith("illion"):
        s = s[: -len("illion")]
    if s and s[-1].lower() in _SUFFIX_MULTIPLIERS:
        mult = _SUFFIX_MULTIPLIERS[s[-1].lower()]
        try:
            return float(s[:-1].strip()) * mult
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def detect_scope_expansion_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify scope expansion anomalies in a normalized document.

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

    has_amendment = any(kw in text_lower for kw in AMENDMENT_KEYWORDS)
    if not has_amendment:
        return anomalies

    has_baseline = any(kw in text_lower for kw in BASELINE_KEYWORDS)

    # Parse all dollar amounts in the document
    raw_amounts = FISCAL_AMOUNT_PATTERN.findall(text_content)
    parsed: list[tuple[str, float]] = []
    for raw in raw_amounts:
        value = _parse_dollar_amount(raw)
        if value is not None and value > 0:
            parsed.append((raw, value))

    # Check 1: Significant expansion — any amount >50% above another
    if len(parsed) >= 2:
        values = [v for _, v in parsed]
        min_val = min(values)
        max_val = max(values)
        if max_val > min_val * (1 + _EXPANSION_THRESHOLD):
            expansion_pct = round((max_val - min_val) / min_val * 100, 1)
            original_raw = next(r for r, v in parsed if v == min_val)
            expanded_raw = next(r for r, v in parsed if v == max_val)
            anomalies.append(
                {
                    "id": "scope:significant-expansion",
                    "issue": (
                        f"Contract amount expanded by {expansion_pct}% — "
                        "possible amendment-as-procurement"
                    ),
                    "severity": "high",
                    "layer": "scope",
                    "details": {
                        "original_amount": original_raw,
                        "expanded_amount": expanded_raw,
                        "expansion_percentage": expansion_pct,
                    },
                }
            )

    # Check 2: Amendment present but no original authorization reference
    if not has_baseline:
        anomalies.append(
            {
                "id": "scope:amendment-without-baseline",
                "issue": "Amendment instrument found with no original authorization reference",
                "severity": "medium",
                "layer": "scope",
                "details": {
                    "baseline_keywords_checked": BASELINE_KEYWORDS,
                },
            }
        )

    # Check 3: Sole-source justification combined with amendment
    if _SOLE_SOURCE_PATTERN.search(text_content):
        anomalies.append(
            {
                "id": "scope:sole-source-expansion",
                "issue": "Sole-source justification combined with amendment instrument",
                "severity": "high",
                "layer": "scope",
                "details": {
                    "sole_source_match": _SOLE_SOURCE_PATTERN.search(
                        text_content
                    ).group(0),
                },
            }
        )

    return anomalies
