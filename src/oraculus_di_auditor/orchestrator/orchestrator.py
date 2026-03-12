"""Phase 5 Orchestrator - Main coordination kernel.

This module implements the core Phase 5 orchestration logic for coordinating
multi-agent workflows, scheduling tasks, and merging results.

The orchestrator:
- Classifies incoming requests
- Generates task execution plans
- Assigns tasks to agents
- Simulates deterministic agent execution
- Merges outputs into harmonized results

All operations are deterministic, stateless, and maintain full provenance.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .agents import (
    AnalysisAgent,
    AnomalyAgent,
    DatabaseAgent,
    IngestionAgent,
    InterfaceAgent,
    SynthesisAgent,
)
from .results import (
    CrossDocumentSynthesis,
    format_pipeline_output,
    format_task_execution_plan,
)
from .task_graph import TaskGraph


class Phase5Orchestrator:
    """Phase 5 Orchestration Kernel.

    Coordinates multi-agent workflows with deterministic execution,
    full provenance tracking, and structured output formatting.

    This is the main entry point for Phase 5 operations.
    """

    def __init__(self):
        """Initialize Phase 5 Orchestrator with all agents."""
        self.agents = {
            "IngestionAgent": IngestionAgent(),
            "AnalysisAgent": AnalysisAgent(),
            "AnomalyAgent": AnomalyAgent(),
            "SynthesisAgent": SynthesisAgent(),
            "DatabaseAgent": DatabaseAgent(),
            "InterfaceAgent": InterfaceAgent(),
        }

    def execute_request(
        self, request: dict[str, Any], mode: str = "auto"
    ) -> dict[str, Any]:
        """Execute a user request through the orchestration system.

        This is the main entry point for Phase 5 operations.

        Args:
            request: User request containing:
                - document_text (str, optional): Document text to analyze
                - documents (list, optional): Multiple documents for cross-analysis
                - metadata (dict, optional): Document metadata
                - operation (str, optional): Specific operation to perform
            mode: Execution mode ("auto", "plan_only", "execute")

        Returns:
            Structured Phase 5 response with task plan, execution results,
            and harmonized outputs

        Example:
            >>> orchestrator = Phase5Orchestrator()
            >>> result = orchestrator.execute_request({
            ...     "document_text": "Sample legislation text...",
            ...     "metadata": {"title": "Test Act"}
            ... })
        """
        # Step 1: Classify request
        request_type = self._classify_request(request)

        # Step 2: Generate task plan
        task_graph = self._generate_task_plan(request_type, request)

        # Format execution plan
        execution_plan = format_task_execution_plan(task_graph, request)

        # If plan_only mode, return just the plan
        if mode == "plan_only":
            return {
                "request_type": request_type,
                "execution_plan": execution_plan,
                "mode": "plan_only",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Step 3: Execute task graph
        results = self._execute_task_graph(task_graph)

        # Step 4: Merge outputs
        harmonized_output = self._merge_outputs(results, request_type)

        # Return complete Phase 5 response
        return {
            "request_type": request_type,
            "execution_plan": execution_plan,
            "agent_results": results,
            "harmonized_output": harmonized_output,
            "provenance": {
                "orchestrator": "Phase5Orchestrator",
                "timestamp": datetime.now(UTC).isoformat(),
                "execution_mode": task_graph.get_execution_mode(),
            },
            "confidence": harmonized_output.get("confidence", 1.0),
        }

    def _classify_request(self, request: dict[str, Any]) -> str:
        """Classify the type of request.

        Args:
            request: User request

        Returns:
            Request type classification
        """
        # Check for explicit operation
        if "operation" in request:
            return request["operation"]

        # Check for multiple documents (cross-document analysis)
        if "documents" in request and len(request.get("documents", [])) > 1:
            return "cross_document_analysis"

        # Check for single document analysis
        if "document_text" in request:
            return "single_document_analysis"

        # Check for database query
        if "query" in request:
            return "database_query"

        # Default to analysis
        return "single_document_analysis"

    def _generate_task_plan(
        self, request_type: str, request: dict[str, Any]
    ) -> TaskGraph:
        """Generate task execution plan based on request type.

        Args:
            request_type: Classified request type
            request: Original request

        Returns:
            TaskGraph with scheduled tasks
        """
        graph = TaskGraph()

        if request_type == "single_document_analysis":
            # Standard single document pipeline
            graph.add_task(
                "ingest_01",
                "IngestionAgent",
                "ingest_document",
                {
                    "document_text": request.get("document_text", ""),
                    "metadata": request.get("metadata", {}),
                },
            )

            graph.add_task(
                "analyze_01",
                "AnalysisAgent",
                "run_analysis",
                {
                    "document_text": request.get("document_text", ""),
                    "metadata": request.get("metadata", {}),
                },
                dependencies=["ingest_01"],
            )

            graph.add_task(
                "anomaly_01",
                "AnomalyAgent",
                "detect_anomalies",
                {"findings": "from_analyze_01"},
                dependencies=["analyze_01"],
            )

            graph.add_task(
                "synthesis_01",
                "SynthesisAgent",
                "synthesize",
                {"analyses": "from_single_analysis", "mode": "single"},
                dependencies=["analyze_01", "anomaly_01"],
            )

        elif request_type == "cross_document_analysis":
            # Multi-document pipeline
            documents = request.get("documents", [])

            # Ingest all documents in parallel
            for i, doc in enumerate(documents):
                graph.add_task(
                    f"ingest_{i:02d}",
                    "IngestionAgent",
                    "ingest_document",
                    {
                        "document_text": doc.get("text", ""),
                        "metadata": doc.get("metadata", {}),
                    },
                )

            # Analyze all documents in parallel
            for i, doc in enumerate(documents):
                graph.add_task(
                    f"analyze_{i:02d}",
                    "AnalysisAgent",
                    "run_analysis",
                    {
                        "document_text": doc.get("text", ""),
                        "metadata": doc.get("metadata", {}),
                    },
                    dependencies=[f"ingest_{i:02d}"],
                )

            # Synthesize across all documents
            analyze_deps = [f"analyze_{i:02d}" for i in range(len(documents))]
            graph.add_task(
                "synthesis_cross",
                "SynthesisAgent",
                "synthesize",
                {"analyses": "from_all_analyses", "mode": "cross_document"},
                dependencies=analyze_deps,
            )

        elif request_type == "database_query":
            # Database operations
            graph.add_task(
                "db_query_01",
                "DatabaseAgent",
                "query",
                {"query": request.get("query", "")},
            )

            graph.add_task(
                "interface_01",
                "InterfaceAgent",
                "prepare_response",
                {"format": "json", "data": "from_db_query_01"},
                dependencies=["db_query_01"],
            )

        # Compute execution order
        graph.compute_execution_order()

        return graph

    def _execute_task_graph(self, graph: TaskGraph) -> list[dict[str, Any]]:
        """Execute task graph with proper dependency handling.

        Args:
            graph: Task graph to execute

        Returns:
            List of agent execution results
        """
        results = []
        result_cache: dict[str, dict[str, Any]] = {}

        # Execute in topological order
        for level in graph.execution_order:
            for task_id in level:
                task = graph.get_task(task_id)

                # Resolve inputs from previous task results
                resolved_inputs = self._resolve_task_inputs(task.inputs, result_cache)

                # Get agent and execute
                agent = self.agents[task.agent_name]
                graph.update_task_status(task_id, "running")

                try:
                    result = agent.execute(resolved_inputs)
                    graph.update_task_status(task_id, "completed", result=result)
                    result_cache[task_id] = result
                    results.append(result)
                except Exception as e:
                    error_msg = f"Task {task_id} failed: {str(e)}"
                    graph.update_task_status(task_id, "failed", error=error_msg)
                    results.append(
                        {
                            "agent": task.agent_name,
                            "action": task.action,
                            "error": error_msg,
                            "confidence": 0.0,
                        }
                    )

        return results

    def _resolve_task_inputs(
        self, inputs: dict[str, Any], result_cache: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Resolve task inputs by looking up previous results.

        Args:
            inputs: Task input specification
            result_cache: Cache of previous task results

        Returns:
            Resolved input dictionary
        """
        resolved: dict[str, Any] = {}

        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("from_"):
                resolved[key] = self._resolve_reference(value, result_cache)
            else:
                resolved[key] = value

        return resolved

    def _resolve_reference(
        self, reference: str, result_cache: dict[str, dict[str, Any]]
    ) -> Any:
        """Resolve a single reference token like 'from_analyze_01'."""
        if reference == "from_all_analyses":
            return self._collect_all_analyses(result_cache)

        if reference == "from_single_analysis":
            single = self._first_analysis_outputs(result_cache)
            return [single] if single is not None else []

        if reference.startswith("from_analyze_"):
            task_ref = reference.replace("from_", "")
            return self._findings_from_task(task_ref, result_cache)

        task_ref = reference.replace("from_", "")
        return self._outputs_from_task(task_ref, result_cache)

    def _collect_all_analyses(
        self, result_cache: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        analyses: list[dict[str, Any]] = []
        for _task_id in sorted(result_cache.keys()):
            result = result_cache[_task_id]
            if result.get("agent") == "AnalysisAgent":
                analyses.append(result.get("outputs", {}))
        return analyses

    def _first_analysis_outputs(
        self, result_cache: dict[str, dict[str, Any]]
    ) -> dict[str, Any] | None:
        for _task_id in sorted(result_cache.keys()):
            result = result_cache[_task_id]
            if result.get("agent") == "AnalysisAgent":
                return result.get("outputs", {})
        return None

    def _findings_from_task(
        self, task_ref: str, result_cache: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        if task_ref in result_cache:
            result = result_cache[task_ref]
            return result.get("outputs", {}).get("findings", {})
        return {}

    def _outputs_from_task(
        self, task_ref: str, result_cache: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        if task_ref in result_cache:
            return result_cache[task_ref].get("outputs", {})
        return {}

    def _merge_outputs(
        self, results: list[dict[str, Any]], request_type: str
    ) -> dict[str, Any]:
        """Merge agent outputs into harmonized Phase 5 response.

        Args:
            results: List of agent execution results
            request_type: Type of request being processed

        Returns:
            Harmonized output dictionary
        """
        # Find key results
        analysis_results = [r for r in results if r.get("agent") == "AnalysisAgent"]
        synthesis_results = [r for r in results if r.get("agent") == "SynthesisAgent"]
        anomaly_results = [r for r in results if r.get("agent") == "AnomalyAgent"]

        if request_type == "single_document_analysis" and analysis_results:
            # Format as Phase 4 compatible pipeline output
            analysis = analysis_results[0].get("outputs", {})

            # Reconstruct full analysis result
            full_result = {
                "metadata": {},
                "findings": analysis.get("findings", {}),
                "severity_score": analysis.get("scores", {}).get("severity", 0.0),
                "lattice_score": analysis.get("scores", {}).get("lattice", 1.0),
                "coherence_bonus": analysis.get("scores", {}).get("coherence", 0.0),
                "flags": analysis.get("flags", []),
                "summary": analysis.get("summary", ""),
            }

            return format_pipeline_output(full_result)

        elif request_type == "cross_document_analysis" and synthesis_results:
            # Format as cross-document synthesis
            synthesis = synthesis_results[0].get("outputs", {})

            # Collect all anomalies
            all_anomalies = []
            for anomaly_result in anomaly_results:
                all_anomalies.extend(
                    anomaly_result.get("outputs", {}).get("anomalies", [])
                )

            # Compute aggregate metrics
            avg_risk = (
                sum(
                    a.get("outputs", {}).get("risk_score", 0.0) for a in anomaly_results
                )
                / len(anomaly_results)
                if anomaly_results
                else 0.0
            )

            cross_doc_synthesis = CrossDocumentSynthesis(
                summary=synthesis.get("summary", ""),
                themes=synthesis.get("themes", []),
                anomalies=all_anomalies,
                scalar_metrics={
                    "average_risk": avg_risk,
                    "document_count": len(analysis_results),
                },
                cross_document_links=synthesis.get("cross_links", []),
                risk_assessment={
                    "overall_risk": avg_risk,
                    "high_priority_count": sum(
                        len(a.get("outputs", {}).get("high_priority", []))
                        for a in anomaly_results
                    ),
                },
                recommendations=synthesis.get("recommendations", []),
                confidence=0.85,
            )

            return cross_doc_synthesis.to_dict()

        else:
            # Generic output format
            return {
                "status": "completed",
                "result_count": len(results),
                "results": results,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    def get_agent_info(self) -> dict[str, Any]:
        """Get information about available agents.

        Returns:
            Dictionary with agent names and capabilities
        """
        return {
            "agents": list(self.agents.keys()),
            "capabilities": {
                "IngestionAgent": ["ingest_document", "normalize", "chunk"],
                "AnalysisAgent": [
                    "fiscal_analysis",
                    "constitutional_analysis",
                    "surveillance_analysis",
                ],
                "AnomalyAgent": [
                    "detect_anomalies",
                    "assess_risk",
                    "flag_high_priority",
                ],
                "SynthesisAgent": [
                    "single_doc_synthesis",
                    "cross_doc_synthesis",
                    "theme_extraction",
                ],
                "DatabaseAgent": ["store", "query", "update", "delete"],
                "InterfaceAgent": ["format_json", "format_csv", "generate_report"],
            },
        }


__all__ = ["Phase5Orchestrator"]
