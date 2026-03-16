"""Unified data models for ODIA audit reports.

Defines canonical Pydantic models used by all report generators — single-
jurisdiction, multi-jurisdiction, and triage — so downstream consumers
always see a consistent structure regardless of which pipeline produced it.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

# Severity ordering for sorting findings (critical first).
_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Finding(BaseModel):
    """A single audit finding."""

    finding_id: str  # e.g., "F-001"
    title: str
    severity: str  # "critical", "high", "medium", "low"
    category: str  # detector name that produced it
    document_id: str | None = None
    description: str
    evidence: str | None = None
    recommendation: str | None = None
    jurisdiction: str | None = None
    metadata: dict[str, Any] = {}


class DocumentSummary(BaseModel):
    """Summary of a document analyzed in the audit."""

    document_id: str
    title: str | None = None
    source: str | None = None
    anomaly_count: int = 0
    max_severity: str = "none"
    checksum: str | None = None


class SeveritySummary(BaseModel):
    """Anomaly counts by severity."""

    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0

    @property
    def total(self) -> int:
        return self.critical + self.high + self.medium + self.low


class DetectorSummary(BaseModel):
    """Anomaly counts by detector."""

    detector_name: str
    anomaly_count: int = 0
    severities: SeveritySummary = SeveritySummary()


class AuditReport(BaseModel):
    """Complete audit report — the canonical output of any ODIA analysis."""

    report_id: str
    report_type: str  # "single_jurisdiction", "multi_jurisdiction", "triage"
    generated_at: str  # ISO timestamp
    jurisdiction: str | None = None
    title: str = "ODIA Audit Report"
    executive_summary: str = ""
    methodology: str = ""
    date_range: str | None = None
    document_count: int = 0
    documents: list[DocumentSummary] = []
    severity_summary: SeveritySummary = SeveritySummary()
    detector_summaries: list[DetectorSummary] = []
    findings: list[Finding] = []
    recommendations: list[str] = []
    chain_of_custody: dict[str, Any] = {}
    provenance: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    # Temporal analysis (populated when --temporal / temporal analysis ran)
    contract_lineages: list[dict[str, Any]] = []
    evolution_patterns: list[dict[str, Any]] = []
    timeline_data: dict[str, Any] = {}


def build_report_from_analysis(
    analysis_results: list[dict[str, Any]],
    jurisdiction: str | None = None,
    title: str = "ODIA Audit Report",
    report_type: str = "single_jurisdiction",
    enrich: bool = True,
) -> AuditReport:
    """Convert raw analysis pipeline output into an AuditReport.

    Bridges the gap between run_full_analysis() output and the reporting
    system.  Each element of analysis_results is a dict as returned by
    run_full_analysis() — i.e., it contains a "findings" key with sub-keys
    "fiscal", "constitutional", "surveillance", plus a "metadata" key.

    Args:
        analysis_results: List of dicts from run_full_analysis().
        jurisdiction: Optional jurisdiction name to embed in the report.
        title: Human-readable report title.
        report_type: One of "single_jurisdiction", "multi_jurisdiction",
            "triage".
        enrich: If True (default), automatically classify findings and
            generate recommendations using auto_classify, and replace the
            executive_summary with an auto-generated professional paragraph.

    Returns:
        Populated AuditReport instance.
    """
    generated_at = datetime.now(UTC).isoformat()

    # Stable report_id derived from timestamp + jurisdiction.
    _id_source = f"{generated_at}:{jurisdiction or ''}"
    report_id = "RPT-" + hashlib.sha256(_id_source.encode()).hexdigest()[:12].upper()

    # Collect all raw anomalies and track per-document info.
    raw_anomalies: list[tuple[dict[str, Any], str | None]] = []  # (anomaly, doc_id)
    detector_counts: dict[str, dict[str, int]] = {}
    documents: list[DocumentSummary] = []

    for result in analysis_results:
        meta = result.get("metadata", {})
        doc_id = str(meta.get("document_id", "unknown"))
        findings_map: dict[str, list[dict[str, Any]]] = result.get("findings", {})

        doc_anomaly_count = 0
        doc_max_sev = "none"
        for detector_name, anomalies in findings_map.items():
            for anomaly in anomalies:
                raw_anomalies.append((anomaly, doc_id))
                doc_anomaly_count += 1
                sev = anomaly.get("severity", "low")
                if _SEVERITY_ORDER.get(sev, 99) < _SEVERITY_ORDER.get(doc_max_sev, 99):
                    doc_max_sev = sev
                # Accumulate detector counts.
                if detector_name not in detector_counts:
                    detector_counts[detector_name] = {
                        "critical": 0,
                        "high": 0,
                        "medium": 0,
                        "low": 0,
                    }
                detector_counts[detector_name][sev] = (
                    detector_counts[detector_name].get(sev, 0) + 1
                )

        documents.append(
            DocumentSummary(
                document_id=doc_id,
                title=meta.get("title"),
                source=meta.get("source"),
                anomaly_count=doc_anomaly_count,
                max_severity=doc_max_sev,
                checksum=meta.get("checksum"),
            )
        )

    # Sort anomalies: critical → high → medium → low.
    raw_anomalies.sort(
        key=lambda t: _SEVERITY_ORDER.get(t[0].get("severity", "low"), 99)
    )

    # Build Finding objects with sequential IDs.
    findings: list[Finding] = []
    sev_counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for idx, (anomaly, doc_id) in enumerate(raw_anomalies, start=1):
        sev = anomaly.get("severity", "low")
        sev_counts[sev] = sev_counts.get(sev, 0) + 1
        findings.append(
            Finding(
                finding_id=f"F-{idx:03d}",
                title=anomaly.get("issue", anomaly.get("id", "Unknown finding")),
                severity=sev,
                category=anomaly.get("layer", "unknown"),
                document_id=doc_id,
                description=anomaly.get("issue", ""),
                evidence=str(anomaly.get("details", "")) or None,
                jurisdiction=jurisdiction,
                metadata={"anomaly_id": anomaly.get("id", "")},
            )
        )

    severity_summary = SeveritySummary(**sev_counts)

    detector_summaries = [
        DetectorSummary(
            detector_name=name,
            anomaly_count=sum(counts.values()),
            severities=SeveritySummary(**counts),
        )
        for name, counts in detector_counts.items()
    ]

    # Build executive summary.
    total = severity_summary.total
    jid_label = f" for {jurisdiction}" if jurisdiction else ""
    if total == 0:
        exec_summary = (
            f"Analysis{jid_label} of {len(documents)} document(s) found no anomalies."
        )
    else:
        parts = []
        for sev in ("critical", "high", "medium", "low"):
            count = getattr(severity_summary, sev)
            if count:
                parts.append(f"{count} {sev}")
        exec_summary = (
            f"Analysis{jid_label} of {len(documents)} document(s) identified "
            f"{total} anomaly/anomalies ({', '.join(parts)}) across "
            f"{len(detector_summaries)} detector(s)."
        )

    report = AuditReport(
        report_id=report_id,
        report_type=report_type,
        generated_at=generated_at,
        jurisdiction=jurisdiction,
        title=title,
        executive_summary=exec_summary,
        document_count=len(documents),
        documents=documents,
        severity_summary=severity_summary,
        detector_summaries=detector_summaries,
        findings=findings,
    )

    if enrich:
        try:
            from oraculus_di_auditor.reporting.auto_classify import (
                enrich_findings,
                generate_executive_summary,
            )

            report = report.model_copy(
                update={
                    "findings": enrich_findings(report.findings),
                    "executive_summary": generate_executive_summary(report),
                }
            )
        except Exception:  # noqa: BLE001
            pass  # enrichment is best-effort; never break report generation

    return report
