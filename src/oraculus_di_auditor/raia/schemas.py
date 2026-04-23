"""R.A.I.A. (Recursion Analysis Investigative Audit) data schemas.

Pure dataclasses — no I/O, no DB, no side effects. These are the shapes
that ``RAIAService.synthesize()`` returns and that ``synthesis_report``
consumes when rendering the cross-jurisdictional DOCX for WF-010.

Kept deliberately dataclass-only (not Pydantic) so the raia/ package
does not drag pydantic v2 into the import graph for the common case,
and so ``to_dict()`` is trivial for JSON serialisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class AnomalyRow:
    """Flattened view of a single persisted ``Anomaly`` row.

    Mirrors the shape of ``db.models.Anomaly`` minus the SQLAlchemy
    bookkeeping. ``details`` is the decoded ``details_json`` dict.
    """

    anomaly_id: str
    issue: str
    severity: str
    layer: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "issue": self.issue,
            "severity": self.severity,
            "layer": self.layer,
            "details": self.details,
        }


@dataclass
class JurisdictionSummary:
    """Per-jurisdiction aggregate of persisted analysis runs.

    Built by ``RAIAService`` from a DB query that joins ``Document``,
    ``Analysis``, and ``Anomaly``. A jurisdiction with zero documents
    yields a summary with ``document_count=0`` rather than being
    silently dropped — the caller needs to distinguish "we looked and
    found nothing" from "we didn't look".
    """

    jurisdiction_id: str
    document_count: int = 0
    analysis_count: int = 0
    total_anomalies: int = 0
    scalar_score_avg: float = 0.0
    severity_counts: dict[str, int] = field(default_factory=dict)
    layer_counts: dict[str, int] = field(default_factory=dict)
    top_anomalies: list[AnomalyRow] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "jurisdiction_id": self.jurisdiction_id,
            "document_count": self.document_count,
            "analysis_count": self.analysis_count,
            "total_anomalies": self.total_anomalies,
            "scalar_score_avg": round(self.scalar_score_avg, 4),
            "severity_counts": dict(self.severity_counts),
            "layer_counts": dict(self.layer_counts),
            "top_anomalies": [a.to_dict() for a in self.top_anomalies],
        }


@dataclass
class CrossJurisdictionPattern:
    """A pattern that repeats across two or more jurisdictions.

    ``pattern_type`` is one of:
      - ``shared_anomaly_id`` — identical detector-emitted ``id`` string
        appearing in 2+ jurisdictions (strongest signal: same violation,
        same vendor, same mechanism).
      - ``shared_layer_spike`` — the same detector ``layer`` is hot in
        2+ jurisdictions, even if the underlying anomaly IDs differ.
      - ``vendor_convergence`` — vendor-name keywords (Flock, Axon, etc.)
        are present in anomaly issue text across 2+ jurisdictions.

    ``confidence`` is fraction-of-jurisdictions with the pattern, so
    callers can sort patterns by how widespread they are without
    re-deriving from ``jurisdictions_affected``.
    """

    pattern_id: str
    pattern_type: str
    jurisdictions_affected: list[str]
    confidence: float
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "jurisdictions_affected": list(self.jurisdictions_affected),
            "confidence": round(self.confidence, 4),
            "description": self.description,
            "evidence": self.evidence,
        }


@dataclass
class RAIAResult:
    """Top-level synthesis output returned by ``RAIAService.synthesize()``.

    ``missing_jurisdictions`` lists the jurisdiction IDs that the caller
    asked for but that had zero persisted rows; the synthesis still
    succeeds in that case but this field makes the gap visible to n8n
    WF-010 (so it can warn the operator before shipping a partial
    report).
    """

    synthesis_id: str
    generated_at: str
    jurisdictions: list[JurisdictionSummary]
    patterns: list[CrossJurisdictionPattern]
    include_tier3: bool = False
    tier3_notes: dict[str, Any] | None = None
    missing_jurisdictions: list[str] = field(default_factory=list)

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "synthesis_id": self.synthesis_id,
            "generated_at": self.generated_at,
            "jurisdictions": [j.to_dict() for j in self.jurisdictions],
            "patterns": [p.to_dict() for p in self.patterns],
            "include_tier3": self.include_tier3,
            "tier3_notes": self.tier3_notes,
            "missing_jurisdictions": list(self.missing_jurisdictions),
        }


__all__ = [
    "AnomalyRow",
    "JurisdictionSummary",
    "CrossJurisdictionPattern",
    "RAIAResult",
]
