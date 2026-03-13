"""Detector-specific API routes for Oraculus-DI-Auditor.

Provides:
  POST /analyze/detailed  — per-detector breakdown for a single document
  GET  /detectors         — registry of all available detectors
  POST /analyze/batch     — multi-document analysis with cross-document patterns
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic request models — defined at module level so FastAPI can resolve
# the type annotations correctly (models inside functions cause resolution
# failures with `from __future__ import annotations`).
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel, Field

    _PYDANTIC_AVAILABLE = True
except ImportError:
    _PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args: Any, **kwargs: Any) -> Any:  # type: ignore  # noqa: N802
        """Stub for when Pydantic is not installed."""
        return None


class DetailedAnalyzeRequest(BaseModel):  # type: ignore
    """Request model for POST /analyze/detailed."""

    document_text: str = Field(
        ..., min_length=1, description="Document text to analyze"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Optional metadata"
    )


class BatchDocumentItem(BaseModel):  # type: ignore
    """Single document entry in a batch request."""

    document_text: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchAnalyzeRequest(BaseModel):  # type: ignore
    """Request model for POST /analyze/batch."""

    documents: list[BatchDocumentItem] = Field(
        ..., min_length=1, description="One or more documents to analyze"
    )


# ---------------------------------------------------------------------------
# Detector registry — static metadata about every available detector
# ---------------------------------------------------------------------------

DETECTOR_REGISTRY: dict[str, dict[str, Any]] = {
    "fiscal": {
        "name": "fiscal",
        "description": (
            "Detects fiscal anomalies: dollar amounts without corresponding "
            "appropriation authority, missing provenance hashes on funded items, "
            "and unbalanced budget references."
        ),
        "anomaly_types": [
            "fiscal:amount-without-appropriation",
            "fiscal:missing-provenance-hash",
            "fiscal:unbalanced-budget-reference",
        ],
    },
    "constitutional": {
        "name": "constitutional",
        "description": (
            "Detects constitutional anomalies: broad delegation of legislative "
            "power, vague or overbroad mandates, and missing due-process "
            "protections."
        ),
        "anomaly_types": [
            "constitutional:broad-delegation",
            "constitutional:vague-mandate",
            "constitutional:missing-due-process",
        ],
    },
    "surveillance": {
        "name": "surveillance",
        "description": (
            "Detects surveillance anomalies: procurement of monitoring or "
            "tracking technology without corresponding oversight provisions."
        ),
        "anomaly_types": [
            "surveillance:unanchored-monitoring-contract",
        ],
    },
    "procurement_timeline": {
        "name": "procurement_timeline",
        "description": (
            "Detects contracts executed before the required governing-body "
            "authorization date, indicating a structural integrity failure in "
            "the procurement process."
        ),
        "anomaly_types": [
            "procurement:executed-before-authorization",
        ],
    },
    "signature_chain": {
        "name": "signature_chain",
        "description": (
            "Detects unsigned, partially signed, or placeholder-signed compliance "
            "documents in a contract chain."
        ),
        "anomaly_types": [
            "signature:gap-detected",
            "signature:placeholder-token",
        ],
    },
    "scope_expansion": {
        "name": "scope_expansion",
        "description": (
            "Detects the amendment-as-procurement pattern: contract amendments "
            "or renewals that expand significantly beyond the original "
            "authorization scope, potentially circumventing competitive "
            "procurement requirements."
        ),
        "anomaly_types": [
            "scope:significant-expansion",
            "scope:amendment-without-baseline",
            "scope:sole-source-expansion",
        ],
    },
    "governance_gap": {
        "name": "governance_gap",
        "description": (
            "Detects surveillance or monitoring capabilities deployed without "
            "corresponding governance documentation — policies, oversight "
            "frameworks, access controls, or legal authority."
        ),
        "anomaly_types": [
            "governance:ungoverned-surveillance-tech",
            "governance:ungoverned-monitoring-capability",
        ],
    },
    "administrative_integrity": {
        "name": "administrative_integrity",
        "description": (
            "Detects administrative record-keeping failures: missing final "
            "actions, blank required fields, misfiled documents, and retroactive "
            "authorizations."
        ),
        "anomaly_types": [
            "admin:missing-required-field",
            "admin:missing-final-action",
            "admin:retroactive-authorization",
            "admin:misfiled-document",
        ],
    },
}

# All 8 detector keys in a stable order
_DETECTOR_KEYS = list(DETECTOR_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _preprocess_doc(
    document_text: str,
    metadata: dict[str, Any],
    agencies: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Normalize raw text + metadata into the standard document dict."""
    document_id = metadata.get("document_id", f"doc-{hash(document_text) % 10**8}")
    doc: dict[str, Any] = {
        "document_id": document_id,
        "title": metadata.get("title", "Untitled Document"),
        "document_type": metadata.get("document_type", "document"),
        "raw_text": document_text,
        "sections": [{"section_id": "main", "content": document_text}],
        "metadata": {**metadata, "document_id": document_id},
    }
    if agencies:
        doc["agencies"] = agencies
    if "hash" in metadata:
        doc["provenance"] = {
            "source": metadata.get("source", "pipeline"),
            "hash": metadata["hash"],
            "verified_on": datetime.now(UTC).isoformat(),
        }
    return doc


def _run_single_doc_detectors(doc: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Run all single-document detectors; return per-detector result lists."""
    from oraculus_di_auditor.analysis import (
        detect_administrative_anomalies,
        detect_constitutional_anomalies,
        detect_fiscal_anomalies,
        detect_governance_gap_anomalies,
        detect_scope_expansion_anomalies,
        detect_signature_anomalies,
        detect_surveillance_anomalies,
    )

    results: dict[str, list[dict[str, Any]]] = {}
    for name, fn in [
        ("fiscal", detect_fiscal_anomalies),
        ("constitutional", detect_constitutional_anomalies),
        ("surveillance", detect_surveillance_anomalies),
        ("signature_chain", detect_signature_anomalies),
        ("scope_expansion", detect_scope_expansion_anomalies),
        ("governance_gap", detect_governance_gap_anomalies),
        ("administrative_integrity", detect_administrative_anomalies),
    ]:
        try:
            results[name] = fn(doc)
        except Exception as exc:
            logger.warning(
                "Detector %s failed on doc %s: %s",
                name,
                doc.get("document_id"),
                exc,
            )
            results[name] = []
    return results


def _run_procurement_timeline(
    docs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run the multi-document procurement timeline detector; return findings."""
    try:
        from oraculus_di_auditor.analysis import detect_procurement_timeline_anomalies

        return detect_procurement_timeline_anomalies(docs)
    except Exception as exc:
        logger.warning("procurement_timeline detector failed: %s", exc)
        return []


def _compute_score(detector_results: dict[str, list[dict[str, Any]]]) -> float:
    """Weighted severity score (0.0–1.0) from all per-detector findings."""
    all_anomalies = [a for findings in detector_results.values() for a in findings]
    if not all_anomalies:
        return 0.0
    weights = {"critical": 0.9, "high": 0.6, "medium": 0.3, "low": 0.1}
    total = sum(weights.get(a.get("severity", "medium"), 0.3) for a in all_anomalies)
    return min(1.0, total / (len(all_anomalies) + 5))


def _build_summary(
    detector_results: dict[str, list[dict[str, Any]]],
    score: float,
) -> dict[str, Any]:
    """Build the standard summary block from per-detector results."""
    all_anomalies = [a for findings in detector_results.values() for a in findings]
    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for anomaly in all_anomalies:
        sev = anomaly.get("severity", "medium")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    return {
        "total_anomalies": len(all_anomalies),
        "by_severity": by_severity,
        "score": round(score, 4),
    }


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def register_detector_routes(app: Any, jurisdiction_config: Any = None) -> None:
    """Register /analyze/detailed, /detectors, and /analyze/batch on *app*."""
    if not _PYDANTIC_AVAILABLE:
        logger.warning("Pydantic not available; detector routes not registered.")
        return

    @app.post("/analyze/detailed")
    async def analyze_detailed(request: DetailedAnalyzeRequest) -> dict[str, Any]:
        """Analyze a document and return per-detector breakdowns.

        Returns anomaly lists for each of the 8 detectors plus a rolled-up
        summary with total anomaly count, by-severity counts, and a weighted
        severity score.
        """
        agencies = jurisdiction_config.agencies if jurisdiction_config else {}
        doc = _preprocess_doc(
            request.document_text, request.metadata, agencies=agencies
        )

        detector_results = _run_single_doc_detectors(doc)
        detector_results["procurement_timeline"] = _run_procurement_timeline([doc])

        score = _compute_score(detector_results)
        result: dict[str, Any] = {
            "document_id": doc["document_id"],
            "detectors": detector_results,
            "summary": _build_summary(detector_results, score),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        if jurisdiction_config is not None:
            result["jurisdiction"] = jurisdiction_config.name
        return result

    @app.get("/detectors")
    async def list_detectors() -> dict[str, Any]:
        """List all available anomaly detectors with descriptions and anomaly types."""
        return {
            "detectors": list(DETECTOR_REGISTRY.values()),
            "count": len(DETECTOR_REGISTRY),
        }

    @app.post("/analyze/batch")
    async def analyze_batch(request: BatchAnalyzeRequest) -> dict[str, Any]:
        """Analyze multiple documents and surface cross-document patterns.

        Per-document results mirror /analyze/detailed.  Cross-document patterns
        are procurement-timeline findings derived from the full document set
        (not just individual documents), which can surface authorization gaps
        that span documents.
        """
        agencies = jurisdiction_config.agencies if jurisdiction_config else {}
        normalized_docs = [
            _preprocess_doc(item.document_text, item.metadata, agencies=agencies)
            for item in request.documents
        ]

        # Per-document analysis
        doc_results: list[dict[str, Any]] = []
        total_by_severity: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        total_by_detector: dict[str, int] = {k: 0 for k in _DETECTOR_KEYS}
        grand_total = 0

        for doc in normalized_docs:
            det = _run_single_doc_detectors(doc)
            det["procurement_timeline"] = _run_procurement_timeline([doc])

            score = _compute_score(det)
            summary = _build_summary(det, score)

            doc_result: dict[str, Any] = {
                "document_id": doc["document_id"],
                "detectors": det,
                "summary": summary,
            }
            if jurisdiction_config is not None:
                doc_result["jurisdiction"] = jurisdiction_config.name
            doc_results.append(doc_result)

            # Accumulate batch totals
            for sev, cnt in summary["by_severity"].items():
                total_by_severity[sev] = total_by_severity.get(sev, 0) + cnt
            for det_name, findings in det.items():
                total_by_detector[det_name] = total_by_detector.get(det_name, 0) + len(
                    findings
                )
            grand_total += summary["total_anomalies"]

        # Cross-document patterns: run procurement_timeline over the full set
        cross_doc_patterns = _run_procurement_timeline(normalized_docs)

        return {
            "results": doc_results,
            "cross_document_patterns": cross_doc_patterns,
            "summary": {
                "document_count": len(normalized_docs),
                "total_anomalies": grand_total,
                "by_severity": total_by_severity,
                "by_detector": total_by_detector,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }
