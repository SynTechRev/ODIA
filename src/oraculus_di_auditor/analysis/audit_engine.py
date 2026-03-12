"""Audit Intelligence Engine for Oraculus-DI-Auditor.

Provides a unified entry point to run multiple anomaly detectors over a
normalized legislative document, returning structured, explainable findings.

This engine coordinates detectors across layers (fiscal, constitutional,
surveillance) and uses the recursive scalar core for pattern scoring.

All detectors must be pure functions accepting a normalized document dict and
returning a list of anomaly dicts with the following shape:

{
    "id": str,                    # stable identifier for the finding
    "issue": str,                 # concise description of the anomaly
    "severity": "low|medium|high",
    "layer": str,                 # detector layer (e.g., "fiscal")
    "details": dict,              # structured fields (explainable)
}

The engine aggregates and returns:
{
    "count": int,
    "score": float,               # overall confidence score (1.0 best)
    "anomalies": list[dict],
}
"""

from __future__ import annotations

from typing import Any

from .constitutional import detect_constitutional_anomalies
from .fiscal import detect_fiscal_anomalies
from .scalar_core import compute_recursive_scalar_score
from .surveillance import detect_surveillance_anomalies


def analyze_document(doc: dict[str, Any]) -> dict[str, Any]:
    """Run all anomaly detectors against a normalized document.

    Args:
        doc: Normalized document dict (canonical schema fields expected)

    Returns:
        Aggregate result with anomaly count, recursive scalar score, and items.
    """
    anomalies: list[dict[str, Any]] = []

    # Detectors should be side-effect-free and tolerant to missing fields.
    anomalies.extend(detect_fiscal_anomalies(doc))
    anomalies.extend(detect_constitutional_anomalies(doc))
    anomalies.extend(detect_surveillance_anomalies(doc))

    # Compute a confidence-like score (1.0 is best) using scalar core.
    score = compute_recursive_scalar_score(doc, anomalies)

    return {
        "count": len(anomalies),
        "score": score,
        "anomalies": anomalies,
    }
