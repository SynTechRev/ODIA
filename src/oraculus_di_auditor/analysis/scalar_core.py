"""Recursive Scalar Core (Pattern Lattice and Confidence Scoring).

Implements a stub for recursive scalar intelligence inspired scoring.

For now, this returns a high confidence (1.0) when no anomalies are present
and a simple diminishing score as anomalies grow, to keep the interface stable
while we evolve the underlying lattice and node-collapse modeling.
"""

from __future__ import annotations

from typing import Any

# Severity weights for anomaly scoring
SEVERITY_WEIGHTS = {
    "low": 0.02,
    "medium": 0.05,
    "high": 0.10,
}


def compute_recursive_scalar_score(
    doc: dict[str, Any],
    anomalies: list[dict[str, Any]],
) -> float:
    """Compute a confidence-like score using recursive scalar model.

    Args:
        doc: Normalized document
        anomalies: Current list of detected anomalies

    Returns:
        A score in [0.0, 1.0], with 1.0 meaning fully consistent.
    """
    if not anomalies:
        return 1.0

    # Weighted scoring based on severity
    total_penalty = 0.0
    for anomaly in anomalies:
        severity = anomaly.get("severity", "medium")
        weight = SEVERITY_WEIGHTS.get(severity, 0.05)
        total_penalty += weight

    # Apply pattern lattice coherence boost for documents with good provenance
    coherence_bonus = _compute_coherence_bonus(doc)
    adjusted_penalty = max(0.0, total_penalty - coherence_bonus)

    # Clamp score to [0, 1]
    score = max(0.0, min(1.0, 1.0 - adjusted_penalty))
    return score


def _compute_coherence_bonus(doc: dict[str, Any]) -> float:
    """Compute coherence bonus based on document structural integrity.

    Documents with strong provenance, references, and metadata get a small bonus
    to account for their structural coherence in the pattern lattice.

    Args:
        doc: Normalized document

    Returns:
        Bonus value (typically 0.0 to 0.02)
    """
    bonus = 0.0

    # Bonus for valid provenance
    prov = doc.get("provenance", {})
    if isinstance(prov, dict) and prov.get("hash"):
        bonus += 0.01

    # Bonus for having references (indicates lattice connectivity)
    refs = doc.get("references", [])
    if isinstance(refs, list) and len(refs) > 0:
        bonus += 0.005

    # Bonus for metadata completeness
    metadata = doc.get("metadata", {})
    if isinstance(metadata, dict) and len(metadata) > 0:
        bonus += 0.005

    return bonus
