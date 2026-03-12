"""Anomaly detection and analysis module.

Author: Marcus A. Sanchez
Date: 2025-11-12
Updated: 2025-11-13 (GitHub Copilot Agent - Phase 6)
"""

import re
from typing import Any


def detect_long_sentence(text: str, threshold: int = 1000) -> list[dict[str, Any]]:
    """Detect sentences that exceed length threshold.

    Args:
        text: Text to analyze
        threshold: Maximum sentence length in characters

    Returns:
        List of anomaly dictionaries
    """
    verdicts = []
    sentences = text.split(".")  # Simple sentence splitting
    for i, s in enumerate(sentences):
        if len(s) > threshold:
            verdicts.append(
                {
                    "type": "long_sentence",
                    "severity": "medium",
                    "location": i,
                    "length": len(s),
                    "evidence": f"Sentence length: {len(s)} chars",
                    "snippet": s[:200] + "..." if len(s) > 200 else s,
                }
            )
    return verdicts


def detect_missing_citation(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect citation patterns in text that are not in citations array.

    Looks for common legal citation patterns like:
    - U.S.C. (United States Code)
    - CFR (Code of Federal Regulations)
    - v. (versus, for case names)
    - Cal. Code (California codes)

    Args:
        doc: Document dictionary with 'text' and 'citations' fields

    Returns:
        List of anomaly dictionaries
    """
    found = []
    text = doc.get("text", "")
    citations = doc.get("citations", [])

    # Common citation patterns (made more flexible)
    citation_patterns = [
        (r"\d+\s+U\.S\.C\.\s*§?\s*\d*", "U.S.C."),
        (r"\d+\s+C\.F\.R\.\s*§?\s*\d*", "CFR"),
        (r"\d+\s+Cal\.\s+\w+\.?\s+Code\s*§?\s*\d*", "Cal. Code"),
        (r"\w+\s+v\.\s+\w+", "case citation"),
    ]

    for pattern, token in citation_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Strip trailing spaces
            match = match.strip()
            if not match:
                continue

            # Check if this specific citation reference is in the citations array
            # We check if the match appears in any citation string
            if not any(match in str(c) for c in citations):
                # Determine type: use cross_reference_mismatch for U.S.C./CFR patterns
                # to maintain backwards compatibility with existing tests
                anomaly_type = (
                    "cross_reference_mismatch"
                    if token in ["U.S.C.", "CFR"]
                    else "missing_citation"
                )

                found.append(
                    {
                        "type": anomaly_type,
                        "severity": "high",
                        "token": token,
                        "evidence": (
                            f"Citation {match} found in text but not in citations array"
                        ),
                        "citation": match,
                    }
                )

    return found


def find_anomalies(record: dict[str, Any]) -> dict[str, Any]:
    """Find anomalies in a document record.

    Detectors:
    - Long sentences (> 1000 chars)
    - Missing citations (patterns in text not in citations array)
    - Cross-reference mismatches
    - Contradictory dates

    Args:
        record: Document record to analyze

    Returns:
        Dictionary with anomaly findings
    """
    anomalies = []
    text = record.get("text", "")
    date_field = record.get("date", "") or record.get("version_date", "")

    # Run modular detectors
    if text:
        anomalies.extend(detect_long_sentence(text))

    anomalies.extend(detect_missing_citation(record))

    # Detector: Contradictory dates
    if text and date_field:
        # Look for year patterns in text
        year_patterns = re.findall(r"\b(19\d{2}|20\d{2})\b", text)
        if date_field and year_patterns:
            date_year = re.search(r"\b(19\d{2}|20\d{2})\b", date_field)
            if date_year:
                main_year = date_year.group(1)
                for year in year_patterns:
                    if abs(int(year) - int(main_year)) > 50:
                        anomalies.append(
                            {
                                "type": "contradictory_dates",
                                "severity": "medium",
                                "evidence": (
                                    f"Text mentions year {year} but "
                                    f"date field is {date_field}"
                                ),
                            }
                        )
                        break

    return {"id": record.get("id"), "anomalies": anomalies, "count": len(anomalies)}
