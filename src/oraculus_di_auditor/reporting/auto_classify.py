"""Automatic finding classification and recommendation generation.

Classifies raw anomaly detections into actionable audit categories and
generates concrete remediation recommendations, turning detector output
into audit-ready findings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from oraculus_di_auditor.reporting.models import AuditReport, Finding

# ---------------------------------------------------------------------------
# Category registry
# ---------------------------------------------------------------------------

FINDING_CATEGORIES: dict[str, dict[str, Any]] = {
    "procurement_violation": {
        "display_name": "Procurement Violation",
        "detectors": ["procurement_timeline", "scope_expansion"],
        "recommendation_template": (
            "Review {document_id} for procurement compliance. "
            "Verify authorization chain with the clerk's office. "
            "If pre-authorization execution is confirmed, refer to "
            "city attorney for remediation options."
        ),
    },
    "document_integrity": {
        "display_name": "Document Integrity Failure",
        "detectors": ["signature_chain", "administrative_integrity"],
        "recommendation_template": (
            "Obtain executed copies of {document_id} or confirm void status. "
            "Review chain of custody for all unsigned instruments. "
            "Establish signature verification protocol for future contracts."
        ),
    },
    "governance_gap": {
        "display_name": "Governance & Oversight Gap",
        "detectors": ["governance_gap", "surveillance"],
        "recommendation_template": (
            "Develop and adopt use policies for identified capabilities. "
            "Conduct privacy impact assessment. "
            "Establish public oversight mechanism per CCOPS framework."
        ),
    },
    "fiscal_compliance": {
        "display_name": "Fiscal Compliance Issue",
        "detectors": ["fiscal"],
        "recommendation_template": (
            "Trace appropriation chain for identified amounts. "
            "Verify budget authorization against expenditure records. "
            "Cross-check against grant compliance requirements."
        ),
    },
    "constitutional_concern": {
        "display_name": "Constitutional / Legal Concern",
        "detectors": ["constitutional", "cross_reference"],
        "recommendation_template": (
            "Refer to legal counsel for constitutional analysis. "
            "Review delegation authority against intelligible principle standard. "
            "Assess Fourth Amendment implications of identified programs."
        ),
    },
    "temporal_pattern": {
        "display_name": "Temporal / Evolution Pattern",
        "detectors": ["procurement_timeline"],
        "recommendation_template": (
            "Review the full contract lineage for {vendor}. "
            "The {pattern_type} pattern spans {span_years} years "
            "with {growth_percentage}% growth. Consider competitive "
            "rebid or independent cost analysis."
        ),
    },
}

# Reverse lookup: detector name → category key
_DETECTOR_TO_CATEGORY: dict[str, str] = {
    detector: cat_key
    for cat_key, cat in FINDING_CATEGORIES.items()
    for detector in cat["detectors"]
}

_GENERIC_CATEGORY = "general_finding"
_GENERIC_RECOMMENDATION = (
    "Review the flagged document and consult with the relevant department. "
    "Escalate to legal counsel if the issue cannot be resolved internally."
)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def classify_finding(anomaly: dict[str, Any]) -> str:
    """Classify an anomaly into a finding category based on its detector.

    Args:
        anomaly: Raw anomaly dict with at least a ``"layer"`` key.

    Returns:
        Category key string, e.g. ``"procurement_violation"``.
        Falls back to ``"general_finding"`` for unrecognised detectors.
    """
    layer = anomaly.get("layer", "")
    return _DETECTOR_TO_CATEGORY.get(layer, _GENERIC_CATEGORY)


def generate_recommendation(
    anomaly: dict[str, Any],
    category: str,
) -> str:
    """Generate a specific recommendation for a finding.

    Args:
        anomaly: Raw anomaly dict; ``document_id`` used in template
            substitution if present.
        category: Category key returned by :func:`classify_finding`.

    Returns:
        Recommendation string with ``{document_id}`` resolved.
    """
    doc_id = (
        anomaly.get("_document_id")
        or anomaly.get("document_id")
        or anomaly.get("details", {}).get("document_id")
        or "the referenced document"
    )

    cat = FINDING_CATEGORIES.get(category)
    if cat is None:
        return _GENERIC_RECOMMENDATION

    template: str = cat["recommendation_template"]
    return template.format(document_id=doc_id)


def enrich_findings(findings: list[Finding]) -> list[Finding]:
    """Enrich Finding objects with classification and auto-generated recommendations.

    For each finding:
    - Adds ``category`` classification (as ``metadata["auto_category"]``
      and ``metadata["auto_category_display"]``).
    - Fills ``recommendation`` if it is currently ``None``.
    - Does NOT overwrite an existing ``recommendation``.
    - Returns new Finding objects; originals are not mutated.

    Args:
        findings: List of :class:`~oraculus_di_auditor.reporting.models.Finding`
            instances.

    Returns:
        New list of enriched Finding instances.
    """
    from oraculus_di_auditor.reporting.models import Finding

    enriched: list[Finding] = []
    for f in findings:
        # Build a minimal anomaly dict so helpers can operate on Finding fields
        anomaly: dict[str, Any] = {
            "layer": f.category,
            "document_id": f.document_id,
        }
        category = classify_finding(anomaly)
        cat_display = FINDING_CATEGORIES.get(category, {}).get(
            "display_name", "General Finding"
        )

        new_meta = {
            **f.metadata,
            "auto_category": category,
            "auto_category_display": cat_display,
        }

        new_rec = f.recommendation
        if new_rec is None:
            new_rec = generate_recommendation(anomaly, category)

        enriched.append(
            Finding(
                finding_id=f.finding_id,
                title=f.title,
                severity=f.severity,
                category=f.category,
                document_id=f.document_id,
                description=f.description,
                evidence=f.evidence,
                recommendation=new_rec,
                jurisdiction=f.jurisdiction,
                metadata=new_meta,
            )
        )
    return enriched


def generate_executive_summary(report: AuditReport) -> str:  # noqa: C901
    """Auto-generate a professional executive summary paragraph.

    Reads like a formal audit summary suitable for council or oversight
    bodies.

    Args:
        report: Populated :class:`~oraculus_di_auditor.reporting.models.AuditReport`.

    Returns:
        Multi-sentence executive summary string.
    """
    jid = report.jurisdiction or "the analyzed jurisdiction"
    doc_count = report.document_count
    total = report.severity_summary.total
    det_count = len(report.detector_summaries)
    critical = report.severity_summary.critical
    high = report.severity_summary.high

    # Date range from metadata or date_range field
    date_part = ""
    if report.date_range:
        date_part = f" spanning {report.date_range}"

    # Most prevalent category across findings
    cat_counts: dict[str, int] = {}
    for f in report.findings:
        cat = f.metadata.get("auto_category", classify_finding({"layer": f.category}))
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    doc_noun = "document" if doc_count == 1 else "documents"
    det_noun = "detection category" if det_count == 1 else "detection categories"

    if total == 0:
        return (
            f"This audit of {jid} analyzed {doc_count} {doc_noun}{date_part}. "
            "No anomalies were detected across all detection categories. "
            "The documents reviewed appear to be in compliance with applicable "
            "fiscal, constitutional, and governance standards."
        )

    parts: list[str] = [
        f"This audit of {jid} analyzed {doc_count} {doc_noun}{date_part}.",
        f"The analysis identified {total} "
        f"{'anomaly' if total == 1 else 'anomalies'} across "
        f"{det_count} {det_noun}.",
    ]

    if critical > 0:
        parts.append(
            f"{critical} {'finding is' if critical == 1 else 'findings are'} "
            f"classified as critical, requiring immediate attention."
        )
    if high > 0 and critical == 0:
        verb = "requires" if high == 1 else "require"
        parts.append(
            f"{high} high-severity {'finding' if high == 1 else 'findings'} "
            f"{verb} prompt review."
        )

    if cat_counts:
        top_cat_key = max(cat_counts, key=lambda k: cat_counts[k])
        top_cat_display = FINDING_CATEGORIES.get(top_cat_key, {}).get(
            "display_name", "General Finding"
        )
        parts.append(
            f"The most prevalent pattern is {top_cat_display} "
            f"({cat_counts[top_cat_key]} "
            f"{'finding' if cat_counts[top_cat_key] == 1 else 'findings'})."
        )

    # Multi-jurisdiction note from metadata
    jid_list = report.metadata.get("jurisdictions", [])
    patterns = report.metadata.get("cross_jurisdiction_patterns", [])
    if len(jid_list) > 1 and patterns:
        parts.append(
            f"Cross-jurisdiction analysis revealed {len(patterns)} vendor "
            f"playbook {'pattern' if len(patterns) == 1 else 'patterns'} "
            f"across {len(jid_list)} jurisdictions."
        )

    return " ".join(parts)
