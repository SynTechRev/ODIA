"""Phase 8 Multi-Document Orchestrator Endpoint.

This module implements the /orchestrator/run endpoint for coordinating
multi-document analysis across specialized agents.

The orchestrator:
- Ingests multiple documents (TXT, JSON, extracted corpora)
- Distributes tasks across specialized agents
- Coordinates dependency graphs between tasks
- Merges & reconciles outputs from all agents
- Returns unified audit package with findings and correlations
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Import Pydantic models conditionally
try:
    from pydantic import BaseModel, Field

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore

    def Field(*args, **kwargs):  # type: ignore  # noqa: N802
        """Stub Field function for when Pydantic is not installed."""
        return None


# ============================================================================
# Request/Response Schemas (Pydantic v2)
# ============================================================================


class DocumentInput(BaseModel):  # type: ignore
    """Input document for orchestration."""

    document_text: str = Field(..., min_length=1, description="Document text content")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Document metadata (title, jurisdiction, etc.)",
    )


class OrchestratorRequest(BaseModel):  # type: ignore
    """Request model for /orchestrator/run endpoint."""

    documents: list[DocumentInput] = Field(
        ..., min_length=1, description="List of documents to analyze"
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional execution settings (parallel, timeout, etc.)",
    )


class AgentFinding(BaseModel):  # type: ignore
    """Finding from a specific agent."""

    agent: str = Field(..., description="Agent name")
    finding_type: str = Field(..., description="Type of finding")
    description: str = Field(..., description="Finding description")
    severity: float = Field(..., ge=0.0, le=1.0, description="Severity score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    location: dict[str, Any] = Field(
        default_factory=dict, description="Location in document"
    )


class CrossDocumentPattern(BaseModel):  # type: ignore
    """Cross-document pattern detected by meta-agent."""

    pattern_type: str = Field(..., description="Type of pattern")
    description: str = Field(..., description="Pattern description")
    document_ids: list[str] = Field(..., description="Documents involved")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: list[str] = Field(default_factory=list, description="Evidence snippets")


class DocumentResult(BaseModel):  # type: ignore
    """Analysis result for a single document."""

    document_id: str = Field(..., description="Document identifier")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    findings: dict[str, list[dict[str, Any]]] = Field(
        default_factory=dict, description="Findings by agent"
    )
    severity_score: float = Field(..., description="Overall severity score")
    lattice_score: float = Field(..., description="Lattice confidence score")


class OrchestratorResponse(BaseModel):  # type: ignore
    """Response model for /orchestrator/run endpoint."""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status")
    timestamp: str = Field(..., description="Job completion timestamp")
    documents_analyzed: int = Field(..., description="Number of documents analyzed")
    document_results: list[DocumentResult] = Field(
        default_factory=list, description="Per-document results"
    )
    cross_document_patterns: list[CrossDocumentPattern] = Field(
        default_factory=list, description="Cross-document patterns"
    )
    correlated_anomalies: list[dict[str, Any]] = Field(
        default_factory=list, description="Correlated anomalies"
    )
    execution_log: list[dict[str, Any]] = Field(
        default_factory=list, description="Pipeline execution log"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Job metadata")


# ============================================================================
# Orchestrator Service
# ============================================================================


class OrchestratorService:
    """Service for coordinating multi-document analysis.

    This service implements the Phase 8 orchestration logic:
    - Task graph construction
    - Agent coordination
    - Parallel execution
    - Result merging
    - Cross-document analysis
    """

    def __init__(self):
        """Initialize orchestrator service."""
        from ...orchestrator import Phase5Orchestrator

        self.orchestrator = Phase5Orchestrator()

    def execute_orchestration(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Execute multi-document orchestration.

        Args:
            request: Orchestrator request with documents and options

        Returns:
            OrchestratorResponse with unified audit package
        """
        job_id = str(uuid4())
        execution_log = []
        document_results = []

        logger.info(
            f"Starting orchestration job {job_id} with "
            f"{len(request.documents)} documents"
        )

        # Log job start
        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "job_started",
                "job_id": job_id,
                "document_count": len(request.documents),
            }
        )

        # Phase 1: Tier 1 - Ingestion
        # Process each document through ingestion
        ingested_documents = []
        for idx, doc_input in enumerate(request.documents):
            logger.debug(f"Processing document {idx + 1}/{len(request.documents)}")

            # Execute document analysis using Phase 5 orchestrator
            result = self.orchestrator.execute_request(
                {
                    "document_text": doc_input.document_text,
                    "metadata": doc_input.metadata,
                }
            )

            # Extract harmonized output from Phase 5 result
            harmonized = result.get("harmonized_output", {})
            metadata = harmonized.get("metadata", doc_input.metadata)
            findings = harmonized.get("findings", {})

            # Extract document ID
            doc_id = metadata.get("document_id", f"doc_{job_id}_{idx}")

            ingested_documents.append(
                {"id": doc_id, "result": harmonized, "full_phase5_result": result}
            )

            # Create document result
            document_result = DocumentResult(
                document_id=doc_id,
                metadata=metadata,
                findings=findings,
                severity_score=harmonized.get("severity_score", 0.0),
                lattice_score=harmonized.get("lattice_score", 1.0),
            )
            document_results.append(document_result)

            execution_log.append(
                {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "event": "document_analyzed",
                    "document_id": doc_id,
                    "document_index": idx,
                }
            )

        # Phase 2: Tier 3 - Meta-Agent Cross-Document Analysis
        cross_document_patterns = self._analyze_cross_document_patterns(
            ingested_documents, execution_log
        )
        correlated_anomalies = self._correlate_anomalies(
            ingested_documents, execution_log
        )

        # Log job completion
        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "job_completed",
                "job_id": job_id,
                "patterns_found": len(cross_document_patterns),
                "anomalies_correlated": len(correlated_anomalies),
            }
        )

        logger.info(
            f"Orchestration job {job_id} completed: "
            f"{len(document_results)} documents, "
            f"{len(cross_document_patterns)} patterns, "
            f"{len(correlated_anomalies)} correlations"
        )

        return OrchestratorResponse(
            job_id=job_id,
            status="completed",
            timestamp=datetime.now(UTC).isoformat(),
            documents_analyzed=len(request.documents),
            document_results=document_results,
            cross_document_patterns=cross_document_patterns,
            correlated_anomalies=correlated_anomalies,
            execution_log=execution_log,
            metadata={
                "total_findings": sum(
                    sum(len(f) for f in dr.findings.values()) for dr in document_results
                ),
            },
        )

    def _analyze_cross_document_patterns(
        self, documents: list[dict[str, Any]], execution_log: list[dict[str, Any]]
    ) -> list[CrossDocumentPattern]:
        """Analyze patterns across multiple documents.

        Args:
            documents: List of ingested documents with results
            execution_log: Execution log to append events

        Returns:
            List of cross-document patterns
        """
        patterns = []

        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "cross_document_analysis_started",
                "document_count": len(documents),
            }
        )

        if len(documents) < 2:
            # Need at least 2 documents for cross-document analysis
            return patterns

        # Pattern 1: Common anomaly types across documents
        anomaly_types = {}
        for doc in documents:
            result = doc["result"]
            findings = result.get("findings", {})
            for agent_type, agent_findings in findings.items():
                if agent_type not in anomaly_types:
                    anomaly_types[agent_type] = []
                anomaly_types[agent_type].append(
                    {"document_id": doc["id"], "count": len(agent_findings)}
                )

        # Create patterns for anomaly types present in multiple documents
        for anomaly_type, occurrences in anomaly_types.items():
            if len(occurrences) >= 2:
                patterns.append(
                    CrossDocumentPattern(
                        pattern_type=f"common_{anomaly_type}_anomalies",
                        description=(
                            f"{anomaly_type.title()} anomalies found across "
                            f"{len(occurrences)} documents"
                        ),
                        document_ids=[occ["document_id"] for occ in occurrences],
                        confidence=min(0.95, 0.5 + len(occurrences) * 0.15),
                        evidence=[
                            (
                                f"Document {occ['document_id']}: "
                                f"{occ['count']} {anomaly_type} findings"
                            )
                            for occ in occurrences[:3]
                        ],
                    )
                )

        # Pattern 2: Severity score trends
        high_severity_docs = [
            doc for doc in documents if doc["result"].get("severity_score", 0.0) > 0.5
        ]
        if len(high_severity_docs) >= 2:
            patterns.append(
                CrossDocumentPattern(
                    pattern_type="high_severity_cluster",
                    description=(
                        f"{len(high_severity_docs)} documents with "
                        f"elevated severity scores"
                    ),
                    document_ids=[doc["id"] for doc in high_severity_docs],
                    confidence=0.85,
                    evidence=[
                        (
                            f"Document {doc['id']}: "
                            f"severity={doc['result'].get('severity_score', 0.0):.2f}"
                        )
                        for doc in high_severity_docs[:3]
                    ],
                )
            )

        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "cross_document_analysis_completed",
                "patterns_found": len(patterns),
            }
        )

        return patterns

    def _correlate_anomalies(
        self, documents: list[dict[str, Any]], execution_log: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Correlate anomalies across documents.

        Args:
            documents: List of ingested documents with results
            execution_log: Execution log to append events

        Returns:
            List of correlated anomalies
        """
        correlations = []

        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "anomaly_correlation_started",
                "document_count": len(documents),
            }
        )

        if len(documents) < 2:
            return correlations

        # Collect all fiscal findings for correlation
        fiscal_findings_by_doc = {}
        for doc in documents:
            result = doc["result"]
            fiscal_findings = result.get("findings", {}).get("fiscal", [])
            if fiscal_findings:
                fiscal_findings_by_doc[doc["id"]] = fiscal_findings

        # If multiple documents have fiscal findings, create correlation
        if len(fiscal_findings_by_doc) >= 2:
            total_findings = sum(
                len(findings) for findings in fiscal_findings_by_doc.values()
            )
            correlations.append(
                {
                    "correlation_type": "fiscal_anomaly_cluster",
                    "description": (
                        f"Fiscal anomalies detected across "
                        f"{len(fiscal_findings_by_doc)} documents"
                    ),
                    "document_ids": list(fiscal_findings_by_doc.keys()),
                    "total_findings": total_findings,
                    "severity": "high" if total_findings > 5 else "medium",
                    "confidence": 0.9,
                }
            )

        # Collect constitutional findings
        constitutional_findings_by_doc = {}
        for doc in documents:
            result = doc["result"]
            constitutional_findings = result.get("findings", {}).get(
                "constitutional", []
            )
            if constitutional_findings:
                constitutional_findings_by_doc[doc["id"]] = constitutional_findings

        if len(constitutional_findings_by_doc) >= 2:
            correlations.append(
                {
                    "correlation_type": "constitutional_concern_pattern",
                    "description": (
                        f"Constitutional concerns identified across "
                        f"{len(constitutional_findings_by_doc)} documents"
                    ),
                    "document_ids": list(constitutional_findings_by_doc.keys()),
                    "total_findings": sum(
                        len(findings)
                        for findings in constitutional_findings_by_doc.values()
                    ),
                    "severity": "high",
                    "confidence": 0.85,
                }
            )

        execution_log.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "anomaly_correlation_completed",
                "correlations_found": len(correlations),
            }
        )

        return correlations


# ============================================================================
# Route Registration
# ============================================================================


def register_orchestrator_routes(app: Any) -> None:
    """Register orchestrator routes to FastAPI app.

    Args:
        app: FastAPI application instance
    """
    service = OrchestratorService()

    @app.post("/orchestrator/run")
    async def run_orchestrator(
        request: OrchestratorRequest,
    ) -> OrchestratorResponse:
        """Execute multi-document orchestration.

        This is the main Phase 8 endpoint for coordinating multi-document
        analysis across specialized agents.

        Args:
            request: OrchestratorRequest with documents and options

        Returns:
            OrchestratorResponse with unified audit package
        """
        logger.info(
            f"Orchestrator request received: {len(request.documents)} documents"
        )
        result = service.execute_orchestration(request)
        logger.info(f"Orchestrator job {result.job_id} completed successfully")
        return result


__all__ = [
    "OrchestratorRequest",
    "OrchestratorResponse",
    "DocumentInput",
    "DocumentResult",
    "AgentFinding",
    "CrossDocumentPattern",
    "OrchestratorService",
    "register_orchestrator_routes",
]
