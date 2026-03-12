"""Cross-Reference Auditor for Legal Documents.

Detects cross-jurisdiction references and potential conflicts between
different legal corpora (federal vs state, USC vs CFR, etc.).

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import re
from typing import Any

# Pattern definitions for common legal citations
CITATION_PATTERNS = {
    "usc": r"\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+",  # e.g., "42 U.S.C. § 1983"
    "cfr": r"\b\d+\s+C\.?F\.?R\.?\s+§?\s*\d+",  # e.g., "21 CFR § 50.25"
    "cal_code": r"\bCal\.?\s+\w+\.?\s+Code\b",  # e.g., "Cal. Penal Code"
    "pub_law": r"\bPub\.?\s*L\.?\s+No\.?\s+\d+-\d+",  # e.g., "Pub. L. No. 111-148"
    "stat": r"\b\d+\s+Stat\.?\s+\d+",  # e.g., "124 Stat. 119"
}


def detect_cross_jurisdiction_refs(text: str) -> list[dict[str, Any]]:
    """Detect references across different legal jurisdictions.

    Args:
        text: Document text to analyze

    Returns:
        List of detected cross-jurisdiction references with details
    """
    references = []

    # Check for each citation type
    detected_types = {}
    for cite_type, pattern in CITATION_PATTERNS.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        detected = [match.group() for match in matches]
        if detected:
            detected_types[cite_type] = detected

    # Identify cross-jurisdiction patterns
    if "usc" in detected_types and "cal_code" in detected_types:
        references.append(
            {
                "type": "federal_state_cross_reference",
                "federal": detected_types["usc"],
                "state": detected_types["cal_code"],
                "severity": "info",
                "description": (
                    "Document contains both federal (USC) and "
                    "California state code references"
                ),
            }
        )

    if "cfr" in detected_types and "cal_code" in detected_types:
        references.append(
            {
                "type": "cfr_state_cross_reference",
                "federal": detected_types["cfr"],
                "state": detected_types["cal_code"],
                "severity": "info",
                "description": (
                    "Document contains both federal regulations (CFR) and "
                    "California state code references"
                ),
            }
        )

    return references


def cross_reference_audit(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Audit documents for cross-jurisdiction references and anomalies.

    Args:
        docs: List of document dictionaries with 'id', 'text',
            and optional 'jurisdiction'

    Returns:
        List of anomaly findings with document ID and issue details
    """
    anomalies = []

    for doc in docs:
        doc_id = doc.get("id", "unknown")
        text = doc.get("text", "")
        jurisdiction = doc.get("jurisdiction", "unknown")

        # Detect cross-jurisdiction references
        cross_refs = detect_cross_jurisdiction_refs(text)

        for ref in cross_refs:
            anomalies.append(
                {
                    "id": doc_id,
                    "jurisdiction": jurisdiction,
                    "issue": ref["type"],
                    "severity": ref["severity"],
                    "description": ref["description"],
                    "details": {
                        k: v
                        for k, v in ref.items()
                        if k not in ["type", "severity", "description"]
                    },
                }
            )

        # Additional checks for specific jurisdiction mismatches
        if jurisdiction == "federal":
            # Federal document shouldn't primarily reference state codes
            state_matches = re.findall(
                CITATION_PATTERNS["cal_code"], text, re.IGNORECASE
            )
            federal_matches = len(
                re.findall(CITATION_PATTERNS["usc"], text, re.IGNORECASE)
            ) + len(re.findall(CITATION_PATTERNS["cfr"], text, re.IGNORECASE))

            if state_matches and len(state_matches) > federal_matches:
                anomalies.append(
                    {
                        "id": doc_id,
                        "jurisdiction": jurisdiction,
                        "issue": "jurisdiction_mismatch",
                        "severity": "warning",
                        "description": (
                            f"Federal document contains more state references "
                            f"({len(state_matches)}) than federal references "
                            f"({federal_matches})"
                        ),
                    }
                )

        elif jurisdiction in ["california", "state"]:
            # State document with primarily federal references might be misclassified
            federal_matches = len(
                re.findall(CITATION_PATTERNS["usc"], text, re.IGNORECASE)
            ) + len(re.findall(CITATION_PATTERNS["cfr"], text, re.IGNORECASE))
            state_matches = re.findall(
                CITATION_PATTERNS["cal_code"], text, re.IGNORECASE
            )

            if federal_matches > len(state_matches) * 2:
                anomalies.append(
                    {
                        "id": doc_id,
                        "jurisdiction": jurisdiction,
                        "issue": "jurisdiction_mismatch",
                        "severity": "warning",
                        "description": (
                            f"State document contains significantly more "
                            f"federal references ({federal_matches}) than "
                            f"state references ({len(state_matches)})"
                        ),
                    }
                )

    return anomalies
