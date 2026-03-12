"""Phase 14 Service - Recursive Predictive Governance Engine (RPG-14).

Main orchestrator for Phase 14: Meta-Causal Inference & Recursive Predictive
Governance Engine. Integrates all Phase 14 components and interfaces with
Phases 1-13.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .causal_anomaly_detector import CausalAnomalyDetector
from .causal_graph import CausalGraph, NodeType
from .causal_responsibility_index import CausalResponsibilityIndex
from .governance_prognosis import GovernancePrognosisGenerator
from .retrocausal_inference import RetrocausalInferenceEngine

logger = logging.getLogger(__name__)


class Phase14Service:
    """Phase 14 Service: Recursive Predictive Governance Engine (RPG-14).

    The governing intelligence layer that sits above Phases 1-13.

    Capabilities:
    - Traces causal chains backward (retrocausality)
    - Projects multi-branch future governance states
    - Validates causal responsibility (CRI)
    - Identifies governance anomalies
    - Evaluates systemic consistency
    - Produces predictive governance advisories
    """

    def __init__(
        self,
        time_depth: int = 12,
        branching_factor: int = 5,
        max_retrocausal_depth: int = 12,
    ):
        """Initialize Phase 14 service.

        Args:
            time_depth: Maximum time depth for predictions
            branching_factor: Maximum branching factor for trajectories
            max_retrocausal_depth: Maximum depth for retrocausal inference
        """
        self.version = "1.0.0"
        self.phase = 14
        self.time_depth = time_depth
        self.branching_factor = branching_factor

        # Initialize components
        self.causal_graph = CausalGraph()
        self.retrocausal_engine = RetrocausalInferenceEngine(
            max_depth=max_retrocausal_depth
        )
        self.cri_calculator = CausalResponsibilityIndex()
        self.anomaly_detector = CausalAnomalyDetector()
        self.prognosis_generator = GovernancePrognosisGenerator(
            time_depth=time_depth, branching_factor=branching_factor
        )

        self.created_at = datetime.now(UTC)
        self.cycle_count = 0
        self.execution_history: list[dict[str, Any]] = []

        logger.info("Phase 14 Service initialized - RPG-14 active")

    def run_cycle(
        self,
        system_state: dict[str, Any],
        phase12_harmonics: dict[int, float] | None = None,
        phase13_probabilities: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Execute a complete RPG-14 cycle.

        Args:
            system_state: Current system state from Phases 1-13
            phase12_harmonics: Scalar harmonic weights from Phase 12
            phase13_probabilities: QDCL probabilities from Phase 13

        Returns:
            Complete RPG-14 cycle output
        """
        cycle_start = datetime.now(UTC)
        self.cycle_count += 1

        logger.info(f"Starting RPG-14 cycle {self.cycle_count}")

        # Build causal graph from system state
        self._build_causal_graph_from_state(
            system_state, phase12_harmonics, phase13_probabilities
        )

        # Run all analysis components
        anomaly_report = self.detect_causal_breaks()
        cri_rankings = self.compute_cri(
            anomaly_penalties=self._extract_anomaly_penalties(anomaly_report)
        )
        prognosis = self.generate_prognosis()
        governance_audit = self.audit_governance(
            anomaly_report, cri_rankings, prognosis
        )
        traceability = self.produce_traceability_report(
            anomaly_report, cri_rankings, prognosis
        )

        cycle_end = datetime.now(UTC)
        execution_time = (cycle_end - cycle_start).total_seconds()

        result = {
            "version": self.version,
            "phase": self.phase,
            "cycle": self.cycle_count,
            "timestamp": cycle_start.isoformat(),
            "execution_time_seconds": execution_time,
            "causal_graph": {
                "node_count": len(self.causal_graph.nodes),
                "version": self.causal_graph.version,
            },
            "anomaly_report": anomaly_report,
            "cri_rankings": cri_rankings,
            "governance_prognosis": prognosis,
            "governance_audit": governance_audit,
            "traceability_report": traceability,
        }

        self.execution_history.append(result)
        logger.info(f"RPG-14 cycle {self.cycle_count} complete")

        return result

    def _build_causal_graph_from_state(
        self,
        system_state: dict[str, Any],
        phase12_harmonics: dict[int, float] | None,
        phase13_probabilities: dict[str, float] | None,
    ):
        """Build causal graph from system state.

        Args:
            system_state: System state dictionary
            phase12_harmonics: Scalar harmonics
            phase13_probabilities: QDCL probabilities
        """
        # Clear existing graph
        self.causal_graph = CausalGraph()

        # Extract components from system state
        components = system_state.get("components", [])
        if isinstance(components, dict):
            components = list(components.values())

        # Create nodes for each component
        node_map = {}
        for i, component in enumerate(components):
            if isinstance(component, dict):
                comp_id = component.get("id", f"comp_{i}")
                harmonic = phase12_harmonics.get(i, 1.0) if phase12_harmonics else 1.0
                probability = (
                    phase13_probabilities.get(comp_id, 1.0)
                    if phase13_probabilities
                    else 1.0
                )

                node = self.causal_graph.add_node(
                    node_type=NodeType.FORWARD,
                    deviation_slope=component.get("deviation_slope", 0.0),
                    qdcl_probability=probability,
                    scalar_harmonic=harmonic,
                    metadata={"component_id": comp_id, "component": component},
                )
                node_map[comp_id] = node.node_id

        # Create edges based on dependencies
        dependencies = system_state.get("dependencies", [])
        for dep in dependencies:
            if isinstance(dep, dict):
                source = dep.get("source")
                target = dep.get("target")
                if source in node_map and target in node_map:
                    self.causal_graph.add_edge(node_map[source], node_map[target])

    def compute_cri(
        self,
        node_ids: list[str] | None = None,
        anomaly_penalties: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compute Causal Responsibility Index for nodes.

        Args:
            node_ids: Optional list of node IDs (all nodes if None)
            anomaly_penalties: Optional anomaly penalties per node

        Returns:
            CRI rankings and analysis
        """
        if node_ids is None:
            node_ids = list(self.causal_graph.nodes.keys())

        rankings = self.cri_calculator.rank_by_responsibility(
            self.causal_graph, anomaly_penalties
        )

        # Get aggregate statistics
        aggregate = self.cri_calculator.compute_aggregate_cri(
            self.causal_graph, node_ids, anomaly_penalties
        )

        return {
            "rankings": rankings[:20],  # Top 20
            "aggregate": aggregate,
            "total_nodes": len(node_ids),
        }

    def detect_causal_breaks(
        self, scalar_harmonics: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Detect causal anomalies and breaks.

        Args:
            scalar_harmonics: Optional scalar harmonic values

        Returns:
            Anomaly detection report with 7 required outputs
        """
        return self.anomaly_detector.detect_all_anomalies(
            self.causal_graph, scalar_harmonics
        )

    def generate_prognosis(
        self, starting_nodes: list[str] | None = None
    ) -> dict[str, Any]:
        """Generate governance prognosis.

        Args:
            starting_nodes: Optional starting node IDs

        Returns:
            Governance prognosis with trajectories and stability
        """
        return self.prognosis_generator.generate_prognosis(
            self.causal_graph, starting_nodes
        )

    def audit_governance(
        self,
        anomaly_report: dict[str, Any],
        cri_rankings: dict[str, Any],
        prognosis: dict[str, Any],
    ) -> dict[str, Any]:
        """Audit overall governance state.

        Args:
            anomaly_report: Anomaly detection report
            cri_rankings: CRI rankings
            prognosis: Governance prognosis

        Returns:
            Governance audit report
        """
        # Extract key metrics
        total_anomalies = anomaly_report["output_1_anomaly_summary"]["total_anomalies"]
        avg_cri = cri_rankings["aggregate"].get("avg_cri", 0.0)
        stability_score = prognosis["governance_stability_index"]["stability_score"]

        # Determine governance health
        if total_anomalies == 0 and avg_cri >= 0.7 and stability_score >= 0.8:
            health_status = "excellent"
            health_score = 0.95
        elif total_anomalies <= 5 and avg_cri >= 0.5 and stability_score >= 0.6:
            health_status = "good"
            health_score = 0.75
        elif total_anomalies <= 15 and avg_cri >= 0.3 and stability_score >= 0.4:
            health_status = "fair"
            health_score = 0.55
        else:
            health_status = "poor"
            health_score = 0.30

        return {
            "health_status": health_status,
            "health_score": health_score,
            "metrics": {
                "total_anomalies": total_anomalies,
                "avg_causal_responsibility": avg_cri,
                "governance_stability": stability_score,
            },
            "critical_issues": self._identify_critical_issues(
                anomaly_report, cri_rankings, prognosis
            ),
            "recommendations": self._generate_governance_recommendations(
                health_status, anomaly_report, prognosis
            ),
        }

    def _identify_critical_issues(
        self,
        anomaly_report: dict[str, Any],
        cri_rankings: dict[str, Any],
        prognosis: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Identify critical governance issues."""
        issues = []

        # Critical anomalies
        severity = anomaly_report["output_1_anomaly_summary"]["severity_breakdown"]
        if severity.get("critical", 0) > 0:
            issues.append(
                {
                    "type": "critical_anomalies",
                    "count": severity["critical"],
                    "severity": "critical",
                    "message": f"{severity['critical']} critical anomalies detected",
                }
            )

        # Low CRI nodes
        low_responsibility = cri_rankings["aggregate"].get(
            "low_responsibility_count", 0
        )
        if low_responsibility > len(self.causal_graph.nodes) * 0.3:
            issues.append(
                {
                    "type": "widespread_low_responsibility",
                    "count": low_responsibility,
                    "severity": "high",
                    "message": "Over 30% of nodes have low causal responsibility",
                }
            )

        # Unstable governance
        if not prognosis["governance_stability_index"]["is_stable"]:
            issues.append(
                {
                    "type": "governance_instability",
                    "severity": "high",
                    "message": "Governance stability below threshold",
                    "stability_score": prognosis["governance_stability_index"][
                        "stability_score"
                    ],
                }
            )

        # High-risk advisories
        risk_advisories = prognosis.get("risk_advisories", [])
        critical_risks = [
            r for r in risk_advisories if r.get("risk_level") == "critical"
        ]
        if critical_risks:
            issues.append(
                {
                    "type": "critical_risk_advisories",
                    "count": len(critical_risks),
                    "severity": "critical",
                    "message": f"{len(critical_risks)} critical risk advisories issued",
                }
            )

        return issues

    def _generate_governance_recommendations(
        self,
        health_status: str,
        anomaly_report: dict[str, Any],
        prognosis: dict[str, Any],
    ) -> list[str]:
        """Generate governance recommendations."""
        recommendations = []

        if health_status == "poor":
            recommendations.append("URGENT: Immediate governance intervention required")
            recommendations.append("Address all critical anomalies within 24 hours")
            recommendations.append("Implement emergency stabilization measures")

        elif health_status == "fair":
            recommendations.append("Strengthen causal chains with low probabilities")
            recommendations.append("Address high-severity anomalies")
            recommendations.append("Review and optimize governance structure")

        # Add anomaly-specific recommendations
        recommended_actions = anomaly_report.get("output_7_recommended_actions", [])
        for action in recommended_actions[:5]:
            if action.get("severity") in ["critical", "high"]:
                recommendations.append(action.get("action", ""))

        # Add prognosis-based recommendations
        risk_advisories = prognosis.get("risk_advisories", [])
        for advisory in risk_advisories[:3]:
            if advisory.get("risk_level") in ["critical", "high"]:
                recommendations.append(advisory.get("recommendation", ""))

        return recommendations

    def integrate_with_phase13(self, phase13_output: dict[str, Any]) -> dict[str, Any]:
        """Integrate with Phase 13 (QDCL) outputs.

        Args:
            phase13_output: Output from Phase 13 QDCL cycle

        Returns:
            Integration result
        """
        # Extract QDCL probabilities
        trajectory_cube = phase13_output.get("output_4_trajectory_probability_cube", {})
        trajectories = trajectory_cube.get("trajectories", [])

        probabilities = {}
        for trajectory in trajectories:
            node_id = trajectory.get("trajectory_id", "")
            probability = trajectory.get("probability", 1.0)
            probabilities[node_id] = probability

        return {
            "success": True,
            "phase13_version": phase13_output.get("version", "unknown"),
            "extracted_probabilities": len(probabilities),
            "probabilities": probabilities,
        }

    def produce_traceability_report(
        self,
        anomaly_report: dict[str, Any],
        cri_rankings: dict[str, Any],
        prognosis: dict[str, Any],
    ) -> dict[str, Any]:
        """Produce complete traceability report.

        Args:
            anomaly_report: Anomaly detection report
            cri_rankings: CRI rankings
            prognosis: Governance prognosis

        Returns:
            Traceability report with full reasoning chain
        """
        # Validate graph
        validation = self.causal_graph.validate_graph()

        return {
            "version": self.version,
            "phase": self.phase,
            "cycle": self.cycle_count,
            "timestamp": datetime.now(UTC).isoformat(),
            "graph_validation": validation,
            "reasoning_chain": {
                "step_1_graph_construction": {
                    "node_count": len(self.causal_graph.nodes),
                    "root_nodes": len(self.causal_graph.get_root_nodes()),
                    "leaf_nodes": len(self.causal_graph.get_leaf_nodes()),
                },
                "step_2_anomaly_detection": {
                    "total_anomalies": anomaly_report["output_1_anomaly_summary"][
                        "total_anomalies"
                    ],
                    "detection_cycle": anomaly_report["detection_cycle"],
                },
                "step_3_cri_computation": {
                    "nodes_analyzed": cri_rankings["total_nodes"],
                    "avg_cri": cri_rankings["aggregate"].get("avg_cri", 0.0),
                },
                "step_4_prognosis_generation": {
                    "trajectories_generated": 3,
                    "stability_score": prognosis["governance_stability_index"][
                        "stability_score"
                    ],
                },
            },
            "reproducibility": {
                "deterministic": True,
                "seeded_prng": False,
                "version_locked": True,
                "parameters": {
                    "time_depth": self.time_depth,
                    "branching_factor": self.branching_factor,
                },
            },
        }

    def _extract_anomaly_penalties(
        self, anomaly_report: dict[str, Any]
    ) -> dict[str, float]:
        """Extract anomaly penalties for CRI calculation."""
        penalties = {}

        # Extract breaks
        breaks = anomaly_report["output_2_break_locations"]["locations"]
        for break_item in breaks:
            node_id = break_item["node_id"]
            severity = break_item.get("severity", "medium")

            penalty = {"critical": 0.8, "high": 0.5, "medium": 0.3, "low": 0.1}.get(
                severity, 0.3
            )

            penalties[node_id] = max(penalties.get(node_id, 0.0), penalty)

        # Extract contradictions
        contradictions = anomaly_report["output_3_contradiction_map"]["contradictions"]
        for contradiction in contradictions:
            node_id = contradiction["node_id"]
            severity = contradiction.get("severity", "medium")

            penalty = {"critical": 0.8, "high": 0.5, "medium": 0.3, "low": 0.1}.get(
                severity, 0.3
            )

            penalties[node_id] = max(penalties.get(node_id, 0.0), penalty)

        return penalties

    def get_service_info(self) -> dict[str, Any]:
        """Get service information."""
        return {
            "version": self.version,
            "phase": self.phase,
            "created_at": self.created_at.isoformat(),
            "cycle_count": self.cycle_count,
            "configuration": {
                "time_depth": self.time_depth,
                "branching_factor": self.branching_factor,
            },
            "components": {
                "causal_graph": self.causal_graph.version,
                "retrocausal_engine": self.retrocausal_engine.version,
                "cri_calculator": self.cri_calculator.version,
                "anomaly_detector": self.anomaly_detector.version,
                "prognosis_generator": self.prognosis_generator.version,
            },
        }
