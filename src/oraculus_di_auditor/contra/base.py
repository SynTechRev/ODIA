"""C.O.N.T.R.A. base types: Detector protocol, Finding, EvidenceSpan, Severity.

All L-11 through L-20 detectors implement the Detector protocol and
return List[Finding]. Findings are compatible with the existing O.D.I.A.
anomaly dict shape via to_anomaly_dict() for storage in the anomalies table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Protocol, runtime_checkable


class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class EvidenceSpan:
    """Character offsets and verbatim excerpt from the source document.

    Excerpt is hard-limited to 15 words for copyright compliance and
    evidentiary quotation policy (C.O.N.T.R.A. Framework Section 9.2).
    """

    start_offset: int
    end_offset: int
    verbatim_excerpt: str  # <= 15 words

    def __post_init__(self) -> None:
        words = self.verbatim_excerpt.split()
        if len(words) > 15:
            raise ValueError(
                f"verbatim_excerpt exceeds 15-word limit ({len(words)} words): "
                f"{self.verbatim_excerpt!r}"
            )


@dataclass
class Finding:
    """Single detector finding produced by an L-11 through L-20 detector.

    finding_id format: contra:{layer}:{sub_detector}:{document_hash_short}
    e.g. contra:L-11:B:a1b2c3d4
    """

    finding_id: str
    layer: str  # "L-11" through "L-20"
    sub_detector: str  # "A", "B", ...
    severity: Severity
    document_hash: str  # SHA-256 of source document
    evidence_span: EvidenceSpan
    doctrinal_anchor: str  # citation from contra.anchors controlled vocabulary
    scoring_input: dict  # {"axis": str, "delta": int}
    remedy_channels: List[str]
    notes: Optional[str] = None
    prompt_id: Optional[str] = None  # set when LLM-assisted
    prompt_version: Optional[str] = None  # set when LLM-assisted

    def to_anomaly_dict(self) -> dict:
        """Produce the standard O.D.I.A. anomaly dict for DB storage.

        Maps Finding fields to the platform's enforced anomaly shape:
        {id, issue, severity, layer, details}
        """
        return {
            "id": self.finding_id,
            "issue": (
                f"{self.layer}.{self.sub_detector}: "
                f"{self.evidence_span.verbatim_excerpt}"
            ),
            "severity": self.severity.value,
            "layer": f"contra:{self.layer.lower()}",
            "details": {
                "sub_detector": self.sub_detector,
                "document_hash": self.document_hash,
                "evidence_start": self.evidence_span.start_offset,
                "evidence_end": self.evidence_span.end_offset,
                "evidence_excerpt": self.evidence_span.verbatim_excerpt,
                "doctrinal_anchor": self.doctrinal_anchor,
                "scoring_axis": self.scoring_input.get("axis"),
                "scoring_delta": self.scoring_input.get("delta"),
                "remedy_channels": self.remedy_channels,
                "prompt_id": self.prompt_id,
                "prompt_version": self.prompt_version,
                "notes": self.notes,
            },
        }

    def to_db_dict(self) -> dict:
        """Produce a flat dict for direct insertion into contra_findings table."""
        return {
            "finding_id": self.finding_id,
            "layer": self.layer,
            "sub_detector": self.sub_detector,
            "severity": self.severity.value,
            "doctrinal_anchor": self.doctrinal_anchor,
            "evidence_start": self.evidence_span.start_offset,
            "evidence_end": self.evidence_span.end_offset,
            "evidence_excerpt": self.evidence_span.verbatim_excerpt,
            "scoring_axis": self.scoring_input.get("axis"),
            "scoring_delta": self.scoring_input.get("delta"),
            "remedy_channels": json.dumps(self.remedy_channels),
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "notes": self.notes,
        }


@runtime_checkable
class Detector(Protocol):
    """Protocol that every C.O.N.T.R.A. detector must implement.

    Detectors are stateless; all state needed for a scan is passed as
    doc_text and doc_meta. LLM clients are injected at construction.
    """

    layer: str  # e.g. "L-11"

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        """Scan doc_text and return all findings for this detector layer.

        doc_meta keys: entity_id, entity_name, doc_type, effective_date,
                       document_hash, source_url
        """
        ...
