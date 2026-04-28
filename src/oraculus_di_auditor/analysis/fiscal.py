"""Fiscal Trail Analyzer.

Detects potential gaps or inconsistencies in appropriation and fiscal lineage.

Initial heuristic is intentionally conservative and returns no findings unless
clear structural signals are present. This will evolve to incorporate
recursive scalar patterning for budgetary references and lineage mapping.
"""

from __future__ import annotations

import os
import re
from typing import Any

from .text_utils import extract_text_content


def _include_pipeline_checks() -> bool:
    """Return True iff pipeline-state checks should emit findings.

    v2.9.3 D.1 — `fiscal:missing-provenance-hash` is a pipeline-state
    check (it asks "did the audit pipeline record a provenance hash on
    this document object?", not "is something wrong with the document?")
    and fired on 100% of corpus documents in Run-11 + Run-12 (140 of
    537 cumulative findings = 26% pure noise floor). Default is now
    OFF; operators running diagnostics can opt in via:

        ODIA_INCLUDE_PIPELINE_CHECKS=1
    """
    flag = os.environ.get("ODIA_INCLUDE_PIPELINE_CHECKS", "")
    return flag.lower() in ("1", "true", "yes", "on")

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

# Fiscal amount pattern (e.g., $1,000,000 or $1M).
#
# Alternatives are ordered most-specific-first: the suffixed form
# (e.g. "$1M", "$1.5 Billion") must be tried before the comma-grouped
# form, otherwise the shorter alternative greedy-matches "$1" out of
# "$1M" and strips the suffix, silently mis-parsing "$1M" as 1.0.
# Callers then observe contract amounts that look three orders of
# magnitude too small — e.g. a $1,738,750 amendment against a "$1" (not
# $1M) baseline reads as a 173M% expansion.
FISCAL_AMOUNT_PATTERN = re.compile(
    r"\$\s*\d+(?:\.\d+)?\s*[MBT](?:illion)?|\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
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

    # Check 1: Provenance integrity (v2.9.3 D.1: gated behind
    # ODIA_INCLUDE_PIPELINE_CHECKS — fires on 100% of corpora because it
    # measures pipeline state, not document content).
    if _include_pipeline_checks():
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
