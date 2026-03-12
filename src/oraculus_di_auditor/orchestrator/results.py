"""Result formatting for Phase 5 orchestration.

This module provides structured output formats for Phase 5 orchestration:
- Task Execution Plan
- Agent Response
- Cross-Document Synthesis
- Pipeline Output (Phase 4 compatible)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class TaskExecutionPlan:
    """Structured task execution plan for orchestrated workflows."""

    def __init__(
        self,
        task_graph: list[dict[str, Any]],
        agents_involved: list[str],
        inputs: dict[str, Any],
        execution_mode: str,
        dependencies: list[dict[str, Any]],
        expected_outputs: list[str],
        risk_flags: list[str] | None = None,
        confidence: float = 1.0,
    ):
        """Initialize task execution plan.

        Args:
            task_graph: List of task definitions
            agents_involved: List of agent names
            inputs: Input parameters
            execution_mode: "sequential", "parallel", or "hybrid"
            dependencies: List of dependency relationships
            expected_outputs: Expected output types
            risk_flags: Optional risk flags
            confidence: Confidence in execution plan (0-1)
        """
        self.task_graph = task_graph
        self.agents_involved = agents_involved
        self.inputs = inputs
        self.execution_mode = execution_mode
        self.dependencies = dependencies
        self.expected_outputs = expected_outputs
        self.risk_flags = risk_flags or []
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary with task execution plan
        """
        return {
            "task_graph": self.task_graph,
            "agents_involved": self.agents_involved,
            "inputs": self.inputs,
            "execution_mode": self.execution_mode,
            "dependencies": self.dependencies,
            "expected_outputs": self.expected_outputs,
            "risk_flags": self.risk_flags,
            "confidence": self.confidence,
        }


class AgentResponse:
    """Structured response from a single agent execution."""

    def __init__(
        self,
        agent: str,
        action: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        provenance: dict[str, Any],
        confidence: float = 1.0,
    ):
        """Initialize agent response.

        Args:
            agent: Agent name
            action: Action performed
            inputs: Input parameters used
            outputs: Output data produced
            provenance: Provenance metadata
            confidence: Confidence in results (0-1)
        """
        self.agent = agent
        self.action = action
        self.inputs = inputs
        self.outputs = outputs
        self.provenance = provenance
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary with agent response
        """
        return {
            "agent": self.agent,
            "action": self.action,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "provenance": self.provenance,
            "confidence": self.confidence,
        }


class CrossDocumentSynthesis:
    """Structured synthesis across multiple documents."""

    def __init__(
        self,
        summary: str,
        themes: list[str],
        anomalies: list[dict[str, Any]],
        scalar_metrics: dict[str, float],
        cross_document_links: list[dict[str, Any]],
        risk_assessment: dict[str, Any],
        recommendations: list[str],
        confidence: float = 1.0,
    ):
        """Initialize cross-document synthesis.

        Args:
            summary: Narrative summary
            themes: Identified themes
            anomalies: Detected anomalies
            scalar_metrics: Scalar scores
            cross_document_links: Links between documents
            risk_assessment: Risk analysis
            recommendations: Recommended actions
            confidence: Confidence in synthesis (0-1)
        """
        self.summary = summary
        self.themes = themes
        self.anomalies = anomalies
        self.scalar_metrics = scalar_metrics
        self.cross_document_links = cross_document_links
        self.risk_assessment = risk_assessment
        self.recommendations = recommendations
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary with cross-document synthesis
        """
        return {
            "summary": self.summary,
            "themes": self.themes,
            "anomalies": self.anomalies,
            "scalar_metrics": self.scalar_metrics,
            "cross_document_links": self.cross_document_links,
            "risk_assessment": self.risk_assessment,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
        }


class PipelineOutput:
    """Pipeline output format compatible with Phase 4."""

    def __init__(
        self,
        metadata: dict[str, Any],
        findings: dict[str, list[dict[str, Any]]],
        scores: dict[str, float],
        flags: list[str],
        provenance: dict[str, Any],
        confidence: float = 1.0,
    ):
        """Initialize pipeline output.

        Args:
            metadata: Document metadata
            findings: Categorized findings
                (fiscal, constitutional, surveillance, anomalies)
            scores: Computed scores
            flags: High-priority flags
            provenance: Provenance tracking
            confidence: Overall confidence (0-1)
        """
        self.metadata = metadata
        self.findings = findings
        self.scores = scores
        self.flags = flags
        self.provenance = provenance
        self.confidence = confidence
        self.timestamp = datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary with pipeline output
        """
        return {
            "metadata": self.metadata,
            "findings": self.findings,
            "scores": self.scores,
            "flags": self.flags,
            "provenance": self.provenance,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


def format_task_execution_plan(
    task_graph: Any, inputs: dict[str, Any]
) -> dict[str, Any]:
    """Format task graph as execution plan.

    Args:
        task_graph: TaskGraph instance
        inputs: Input parameters

    Returns:
        Dictionary with formatted execution plan
    """
    graph_dict = task_graph.to_dict()

    agents_involved = list(
        set(task["agent_name"] for task in graph_dict["tasks"].values())
    )

    dependencies = [
        {
            "task_id": task_id,
            "depends_on": task["dependencies"],
        }
        for task_id, task in graph_dict["tasks"].items()
        if task["dependencies"]
    ]

    expected_outputs = ["analysis_results", "anomaly_report", "synthesis"]

    risk_flags = []
    if graph_dict["total_tasks"] > 10:
        risk_flags.append("Complex workflow with many tasks")

    plan = TaskExecutionPlan(
        task_graph=list(graph_dict["tasks"].values()),
        agents_involved=agents_involved,
        inputs=inputs,
        execution_mode=graph_dict["execution_mode"],
        dependencies=dependencies,
        expected_outputs=expected_outputs,
        risk_flags=risk_flags,
        confidence=0.95,
    )

    return plan.to_dict()


def format_pipeline_output(analysis_result: dict[str, Any]) -> dict[str, Any]:
    """Format analysis result as Phase 4 compatible pipeline output.

    Args:
        analysis_result: Result from run_full_analysis

    Returns:
        Dictionary with pipeline output
    """
    findings = analysis_result.get("findings", {})

    # Add anomalies as a separate category
    all_anomalies = []
    for category in ["fiscal", "constitutional", "surveillance"]:
        all_anomalies.extend(findings.get(category, []))

    findings_with_anomalies = {
        **findings,
        "anomalies": all_anomalies,
    }

    scores = {
        "severity": analysis_result.get("severity_score", 0.0),
        "lattice": analysis_result.get("lattice_score", 1.0),
        "coherence": analysis_result.get("coherence_bonus", 0.0),
    }

    provenance = {
        "source": "phase5_orchestrator",
        "timestamp": datetime.now(UTC).isoformat(),
        "pipeline_version": "phase5",
    }

    output = PipelineOutput(
        metadata=analysis_result.get("metadata", {}),
        findings=findings_with_anomalies,
        scores=scores,
        flags=analysis_result.get("flags", []),
        provenance=provenance,
        confidence=analysis_result.get("lattice_score", 1.0),
    )

    return output.to_dict()


__all__ = [
    "TaskExecutionPlan",
    "AgentResponse",
    "CrossDocumentSynthesis",
    "PipelineOutput",
    "format_task_execution_plan",
    "format_pipeline_output",
]
