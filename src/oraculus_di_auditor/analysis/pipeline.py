"""Unified Analysis Pipeline for Oraculus-DI-Auditor.

This module provides the central entry point for running a complete analysis
on a document, coordinating all detectors, scalar scoring, and result formatting.

Phase 4 integration layer that connects:
- Text preprocessing
- All anomaly detectors (fiscal, constitutional, surveillance)
- Recursive scalar core
- Structured result generation

All functions are pure, side-effect-free, and fully testable.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .constitutional import detect_constitutional_anomalies
from .fiscal import detect_fiscal_anomalies
from .scalar_core import compute_recursive_scalar_score
from .surveillance import detect_surveillance_anomalies


def run_full_analysis(document_text: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Execute complete anomaly detection analysis on document text.

    This is the main entry point for Phase 4 unified analysis pipeline.
    Coordinates all detectors and returns structured, explainable results.

    Args:
        document_text: Raw text content of the document to analyze
        metadata: Document metadata dict containing fields like:
            - document_id (str, optional): unique identifier
            - title (str, optional): document title
            - document_type (str, optional): e.g., "act", "regulation"
            - jurisdiction (str, optional): e.g., "federal", "state"
            - Any additional metadata fields

    Returns:
        Structured analysis result containing:
        {
            "metadata": {...},  # Original metadata plus document_id if generated
            "findings": {
                "fiscal": [...],
                "constitutional": [...],
                "surveillance": [...]
            },
            "severity_score": float,  # Weighted severity 0.0-1.0
            "lattice_score": float,  # Scalar confidence 0.0-1.0 (1.0=best)
            "coherence_bonus": float,  # Pattern coherence adjustment
            "flags": [...],  # High-priority anomaly flags
            "summary": str,  # Human-readable summary
            "timestamp": str  # ISO 8601 UTC timestamp
        }

    Example:
        >>> result = run_full_analysis(
        ...     document_text="There is appropriated $1,000,000...",
        ...     metadata={"title": "Budget Act 2025"}
        ... )
        >>> print(result["severity_score"])
        0.0
    """
    # Preprocess: normalize metadata and create document structure
    normalized_doc = _preprocess_document(document_text, metadata)

    # Run all detectors
    fiscal_findings = detect_fiscal_anomalies(normalized_doc)
    constitutional_findings = detect_constitutional_anomalies(normalized_doc)
    surveillance_findings = detect_surveillance_anomalies(normalized_doc)

    # Combine all findings
    all_anomalies = fiscal_findings + constitutional_findings + surveillance_findings

    # Compute recursive scalar score (confidence-like, 1.0 = best)
    lattice_score = compute_recursive_scalar_score(normalized_doc, all_anomalies)

    # Compute additional metrics
    severity_score = _compute_severity_score(all_anomalies)
    coherence_bonus = _compute_coherence_bonus(normalized_doc)
    flags = _extract_high_priority_flags(all_anomalies)
    summary = _generate_summary(all_anomalies, severity_score, lattice_score)

    # Return structured response
    return {
        "metadata": normalized_doc.get("metadata", metadata),
        "findings": {
            "fiscal": fiscal_findings,
            "constitutional": constitutional_findings,
            "surveillance": surveillance_findings,
        },
        "severity_score": severity_score,
        "lattice_score": lattice_score,
        "coherence_bonus": coherence_bonus,
        "flags": flags,
        "summary": summary,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _preprocess_document(
    document_text: str, metadata: dict[str, Any]
) -> dict[str, Any]:
    """Convert raw text and metadata into normalized document structure.

    Args:
        document_text: Raw document text
        metadata: Metadata dictionary

    Returns:
        Normalized document dict compatible with detector interfaces
    """
    # Generate document ID if not provided
    document_id = metadata.get("document_id", f"doc-{hash(document_text) % 10**8}")

    # Build normalized document structure
    normalized_doc = {
        "document_id": document_id,
        "title": metadata.get("title", "Untitled Document"),
        "document_type": metadata.get("document_type", "document"),
        "raw_text": document_text,
        "sections": [
            {
                "section_id": "main",
                "content": document_text,
            }
        ],
        "metadata": {**metadata, "document_id": document_id},
    }

    # Add provenance if hash is provided in metadata
    if "hash" in metadata:
        normalized_doc["provenance"] = {
            "source": metadata.get("source", "pipeline"),
            "hash": metadata["hash"],
            "verified_on": datetime.now(UTC).isoformat(),
        }

    return normalized_doc


def _compute_severity_score(anomalies: list[dict[str, Any]]) -> float:
    """Compute aggregate severity score from anomalies.

    Args:
        anomalies: List of anomaly dicts with "severity" field

    Returns:
        Weighted severity score from 0.0 (no issues) to 1.0 (critical)
    """
    if not anomalies:
        return 0.0

    severity_weights = {
        "low": 0.1,
        "medium": 0.3,
        "high": 0.6,
    }

    total_weight = sum(
        severity_weights.get(a.get("severity", "medium"), 0.3) for a in anomalies
    )

    # Normalize to 0-1 range, with diminishing returns for many anomalies
    return min(1.0, total_weight / (len(anomalies) + 5))


def _compute_coherence_bonus(doc: dict[str, Any]) -> float:
    """Compute pattern coherence bonus for documents with strong provenance.

    Args:
        doc: Normalized document

    Returns:
        Coherence bonus value (0.0 to 0.2)
    """
    bonus = 0.0

    # Check provenance quality
    prov = doc.get("provenance", {})
    if prov.get("hash"):
        bonus += 0.05
    if prov.get("verified_on"):
        bonus += 0.05
    if prov.get("source"):
        bonus += 0.05

    # Check metadata completeness
    if doc.get("document_type") and doc.get("title"):
        bonus += 0.05

    return min(0.2, bonus)


def _extract_high_priority_flags(anomalies: list[dict[str, Any]]) -> list[str]:
    """Extract high-priority flags from anomalies.

    Args:
        anomalies: List of anomaly dicts

    Returns:
        List of flag strings for high-severity issues
    """
    flags = []

    for anomaly in anomalies:
        if anomaly.get("severity") == "high":
            flag_id = anomaly.get("id", "unknown")
            issue = anomaly.get("issue", "High-severity anomaly detected")
            flags.append(f"{flag_id}: {issue}")

    return flags


def _generate_summary(
    anomalies: list[dict[str, Any]], severity_score: float, lattice_score: float
) -> str:
    """Generate human-readable summary of analysis results.

    Args:
        anomalies: List of detected anomalies
        severity_score: Computed severity score
        lattice_score: Recursive scalar confidence score

    Returns:
        Human-readable summary string
    """
    anomaly_count = len(anomalies)

    if anomaly_count == 0:
        return (
            f"Analysis complete. No anomalies detected. "
            f"Confidence score: {lattice_score:.2f}"
        )

    # Categorize by severity
    by_severity = {"low": 0, "medium": 0, "high": 0}
    for a in anomalies:
        severity = a.get("severity", "medium")
        by_severity[severity] = by_severity.get(severity, 0) + 1

    severity_parts = []
    if by_severity["high"] > 0:
        severity_parts.append(f"{by_severity['high']} high")
    if by_severity["medium"] > 0:
        severity_parts.append(f"{by_severity['medium']} medium")
    if by_severity["low"] > 0:
        severity_parts.append(f"{by_severity['low']} low")

    severity_str = ", ".join(severity_parts)
    anomaly_word = "y" if anomaly_count == 1 else "ies"

    return (
        f"Analysis detected {anomaly_count} anomal{anomaly_word} "
        f"({severity_str} severity). "
        f"Overall severity: {severity_score:.2f}, "
        f"confidence: {lattice_score:.2f}"
    )


__all__ = ["run_full_analysis"]
