"""Base types for odia_legal Phase 2 L-detectors (L-1 through L-10).

All legal-layer detectors consume a DocContext and produce LegalFinding objects.
LegalFindings are compatible with the ODIA anomaly dict shape via to_anomaly_dict().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from oraculus_di_auditor.legal.legal_resolver import LegalResolver


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DocContext:
    """Input context passed to every L-detector.

    Carries all metadata a detector needs without requiring a live DB session.
    Fields map directly to the Document ORM model columns.
    """

    document_id: str
    document_hash: str
    document_type: str        # "agenda" | "meeting_minutes" | "contract" | "policy" | ...
    jurisdiction: str         # e.g. "fresnocounty" | "visalia" | "tcso"
    authority: str | None     # e.g. "Fresno County Board of Supervisors"
    version_date: date | None
    text: str                 # full document text (UTF-8)
    # Optional: the ODIA anomaly dict that triggered this legal enrichment pass
    source_finding: dict | None = field(default=None, compare=False)


@dataclass
class LegalFinding:
    """A legal-layer finding produced by an L-detector.

    Carries both the plain-language conclusion and the statutory citations
    that support it. Resolving those citations via LegalResolver gives the
    full statutory text for litigation-grade reporting.
    """

    finding_id: str
    sub_detector: str                    # "l1-statutory-applicability" etc.
    severity: Severity
    document_hash: str
    document_id: str
    statutes_applied: list[str]          # canonical citation strings
    legal_conclusion: str                # plain-language determination
    confidence: float                    # 0.0 (weak signal) – 1.0 (definitive)
    layer: str = "legal"
    source_finding_id: str | None = None # if enriching an existing anomaly finding
    notes: str | None = None

    def to_anomaly_dict(self) -> dict:
        """Serialize to ODIA anomaly dict shape for storage in the anomalies table."""
        return {
            "id": self.finding_id,
            "issue": self.legal_conclusion,
            "severity": self.severity.value,
            "layer": self.layer,
            "details": {
                "sub_detector": self.sub_detector,
                "statutes_applied": self.statutes_applied,
                "confidence": self.confidence,
                "source_finding_id": self.source_finding_id,
                "notes": self.notes,
            },
        }


@runtime_checkable
class LegalDetector(Protocol):
    """Protocol every L-detector must satisfy."""

    detector_id: str

    def detect(
        self,
        ctx: DocContext,
        resolver: "LegalResolver",
    ) -> list[LegalFinding]:
        """Run the detector. Never raises; returns empty list on any error."""
        ...
