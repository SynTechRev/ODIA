"""Causal Anomaly Detector - Phase 14.

Detects anomalies, breaks, and inconsistencies in causal governance chains.
Produces 7 required outputs per detection cycle.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .causal_graph import CausalGraph, CausalNode, NodeType

logger = logging.getLogger(__name__)


class AnomalyType:
    """Types of causal anomalies."""

    CAUSAL_BREAK = "causal_break"
    CONTRADICTION = "contradiction"
    NON_CONVERGENT = "non_convergent"
    UNDEFINED_STATE = "undefined_state"
    IMPOSSIBLE_NODE = "impossible_node"
    SYSTEMIC_INCONSISTENCY = "systemic_inconsistency"
    UNEXPLAINABLE_STATE = "unexplainable_state"


class CausalAnomalyDetector:
    """Detects causal anomalies and governance inconsistencies.

    Produces 7 required outputs per detection cycle:
    1. Anomaly summary
    2. Break locations
    3. Contradiction map
    4. Non-convergent trajectories
    5. Undefined states
    6. Systemic inconsistencies
    7. Recommended actions
    """

    def __init__(
        self,
        probability_threshold: float = 0.3,
        deviation_threshold: float = 3.0,
        convergence_threshold: float = 0.5,
    ):
        """Initialize anomaly detector.

        Args:
            probability_threshold: Min probability for valid nodes
            deviation_threshold: Max acceptable deviation slope
            convergence_threshold: Min convergence score
        """
        self.version = "1.0.0"
        self.probability_threshold = probability_threshold
        self.deviation_threshold = deviation_threshold
        self.convergence_threshold = convergence_threshold
        self.detection_count = 0

    def detect_all_anomalies(
        self, graph: CausalGraph, scalar_harmonics: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Run complete anomaly detection cycle.

        Produces all 7 required outputs.

        Args:
            graph: Causal graph to analyze
            scalar_harmonics: Optional scalar harmonic values

        Returns:
            Complete anomaly detection report
        """
        detection_start = datetime.now(UTC)
        self.detection_count += 1

        logger.info(f"Starting anomaly detection cycle {self.detection_count}")

        # 1. Detect causal breaks
        breaks = self._detect_causal_breaks(graph)

        # 2. Detect contradictions
        contradictions = self._detect_contradictions(graph)

        # 3. Detect non-convergent trajectories
        non_convergent = self._detect_non_convergent_trajectories(graph)

        # 4. Detect undefined states
        undefined_states = self._detect_undefined_states(graph)

        # 5. Detect impossible nodes
        impossible_nodes = self._detect_impossible_nodes(graph)

        # 6. Detect systemic inconsistencies
        systemic_issues = self._detect_systemic_inconsistencies(graph, scalar_harmonics)

        # 7. Detect unexplainable states
        unexplainable = self._detect_unexplainable_states(graph)

        # Generate summary (Output 1)
        total_anomalies = (
            len(breaks)
            + len(contradictions)
            + len(non_convergent)
            + len(undefined_states)
            + len(impossible_nodes)
            + len(systemic_issues)
            + len(unexplainable)
        )

        anomaly_summary = {
            "total_anomalies": total_anomalies,
            "breaks": len(breaks),
            "contradictions": len(contradictions),
            "non_convergent": len(non_convergent),
            "undefined_states": len(undefined_states),
            "impossible_nodes": len(impossible_nodes),
            "systemic_inconsistencies": len(systemic_issues),
            "unexplainable_states": len(unexplainable),
            "severity_breakdown": self._compute_severity_breakdown(
                breaks,
                contradictions,
                non_convergent,
                undefined_states,
                impossible_nodes,
                systemic_issues,
                unexplainable,
            ),
        }

        # Build break locations map (Output 2)
        break_locations = {
            "break_count": len(breaks),
            "locations": [
                {
                    "node_id": b["node_id"],
                    "type": b["type"],
                    "severity": b.get("severity", "medium"),
                }
                for b in breaks
            ],
        }

        # Build contradiction map (Output 3)
        contradiction_map = {
            "contradiction_count": len(contradictions),
            "contradictions": contradictions,
        }

        # Non-convergent trajectories (Output 4)
        non_convergent_trajectories = {
            "trajectory_count": len(non_convergent),
            "trajectories": non_convergent,
        }

        # Undefined states (Output 5)
        undefined_state_report = {
            "undefined_count": len(undefined_states),
            "states": undefined_states,
        }

        # Systemic inconsistencies (Output 6)
        systemic_report = {
            "inconsistency_count": len(systemic_issues),
            "inconsistencies": systemic_issues,
        }

        # Generate recommended actions (Output 7)
        recommended_actions = self._generate_recommendations(
            breaks,
            contradictions,
            non_convergent,
            undefined_states,
            impossible_nodes,
            systemic_issues,
            unexplainable,
        )

        detection_end = datetime.now(UTC)
        execution_time = (detection_end - detection_start).total_seconds()

        return {
            "version": self.version,
            "detection_cycle": self.detection_count,
            "timestamp": detection_start.isoformat(),
            "execution_time_seconds": execution_time,
            "graph_node_count": len(graph.nodes),
            # 7 Required Outputs
            "output_1_anomaly_summary": anomaly_summary,
            "output_2_break_locations": break_locations,
            "output_3_contradiction_map": contradiction_map,
            "output_4_non_convergent_trajectories": non_convergent_trajectories,
            "output_5_undefined_states": undefined_state_report,
            "output_6_systemic_inconsistencies": systemic_report,
            "output_7_recommended_actions": recommended_actions,
        }

    def _detect_causal_breaks(self, graph: CausalGraph) -> list[dict[str, Any]]:
        """Detect breaks in causal flow."""
        breaks = []

        for node_id, node in graph.nodes.items():
            # Low probability indicates weak causal link
            if node.qdcl_probability < self.probability_threshold:
                breaks.append(
                    {
                        "type": "probability_break",
                        "node_id": node_id,
                        "probability": node.qdcl_probability,
                        "threshold": self.probability_threshold,
                        "severity": "high" if node.qdcl_probability < 0.1 else "medium",
                    }
                )

            # High deviation indicates unstable causation
            if abs(node.deviation_slope) > self.deviation_threshold:
                breaks.append(
                    {
                        "type": "deviation_break",
                        "node_id": node_id,
                        "deviation_slope": node.deviation_slope,
                        "threshold": self.deviation_threshold,
                        "severity": (
                            "high" if abs(node.deviation_slope) > 5.0 else "medium"
                        ),
                    }
                )

        return breaks

    def _detect_contradictions(self, graph: CausalGraph) -> list[dict[str, Any]]:
        """Detect contradictory causal relationships."""
        contradictions = []

        for node_id, node in graph.nodes.items():
            # Check for contradictory state vectors
            if len(node.state_vectors) >= 2:
                for i, sv1 in enumerate(node.state_vectors):
                    for sv2 in node.state_vectors[i + 1 :]:
                        # If same dimension but opposing values with high confidence
                        if sv1.dimension == sv2.dimension:
                            value_diff = abs(sv1.value - sv2.value)
                            if (
                                value_diff > 1.0
                                and sv1.confidence > 0.7
                                and sv2.confidence > 0.7
                            ):
                                contradictions.append(
                                    {
                                        "type": "state_vector_contradiction",
                                        "node_id": node_id,
                                        "dimension": sv1.dimension,
                                        "value_1": sv1.value,
                                        "value_2": sv2.value,
                                        "severity": "high",
                                    }
                                )

            # Check for impossible probability values
            if not 0 <= node.qdcl_probability <= 1:
                contradictions.append(
                    {
                        "type": "invalid_probability",
                        "node_id": node_id,
                        "probability": node.qdcl_probability,
                        "severity": "critical",
                    }
                )

        return contradictions

    def _detect_non_convergent_trajectories(
        self, graph: CausalGraph
    ) -> list[dict[str, Any]]:
        """Detect trajectories that don't converge."""
        non_convergent = []

        # Check leaf nodes for convergence
        leaf_nodes = graph.get_leaf_nodes()

        for leaf in leaf_nodes:
            # Trace back to roots
            ancestors = graph.get_ancestors(leaf.node_id)

            if not ancestors:
                continue

            # Calculate convergence score based on ancestor alignment
            alignment_scores = []
            for ancestor in ancestors:
                # Compare state vectors if they exist
                if leaf.state_vectors and ancestor.state_vectors:
                    score = self._calculate_alignment(leaf, ancestor)
                    alignment_scores.append(score)

            if alignment_scores:
                avg_alignment = sum(alignment_scores) / len(alignment_scores)
                if avg_alignment < self.convergence_threshold:
                    non_convergent.append(
                        {
                            "type": "non_convergent_trajectory",
                            "leaf_node_id": leaf.node_id,
                            "ancestor_count": len(ancestors),
                            "convergence_score": avg_alignment,
                            "threshold": self.convergence_threshold,
                            "severity": "medium",
                        }
                    )

        return non_convergent

    def _calculate_alignment(self, node1: CausalNode, node2: CausalNode) -> float:
        """Calculate alignment between two nodes based on state vectors."""
        if not node1.state_vectors or not node2.state_vectors:
            return 0.5  # Neutral

        # Find common dimensions
        dims1 = {sv.dimension for sv in node1.state_vectors}
        dims2 = {sv.dimension for sv in node2.state_vectors}
        common_dims = dims1 & dims2

        if not common_dims:
            return 0.5  # Neutral

        # Calculate alignment for common dimensions
        alignments = []
        for dim in common_dims:
            sv1 = next(sv for sv in node1.state_vectors if sv.dimension == dim)
            sv2 = next(sv for sv in node2.state_vectors if sv.dimension == dim)

            # Normalize difference to [0, 1] assuming values in [-10, 10]
            value_diff = abs(sv1.value - sv2.value)
            alignment = max(0.0, 1.0 - value_diff / 20.0)
            alignments.append(alignment)

        return sum(alignments) / len(alignments)

    def _detect_undefined_states(self, graph: CausalGraph) -> list[dict[str, Any]]:
        """Detect nodes with undefined or missing states."""
        undefined = []

        for node_id, node in graph.nodes.items():
            # No state vectors
            if not node.state_vectors:
                undefined.append(
                    {
                        "type": "missing_state_vectors",
                        "node_id": node_id,
                        "severity": "medium",
                    }
                )

            # State vectors with zero confidence
            zero_confidence = [sv for sv in node.state_vectors if sv.confidence < 0.01]
            if zero_confidence:
                undefined.append(
                    {
                        "type": "zero_confidence_state",
                        "node_id": node_id,
                        "affected_dimensions": [sv.dimension for sv in zero_confidence],
                        "severity": "low",
                    }
                )

        return undefined

    def _detect_impossible_nodes(self, graph: CausalGraph) -> list[dict[str, Any]]:
        """Detect nodes with impossible configurations."""
        impossible = []

        for node_id, node in graph.nodes.items():
            # Retrocausal node with children but no parents
            if (
                node.node_type == NodeType.RETROCAUSAL
                and node.child_ids
                and not node.parent_ids
            ):
                impossible.append(
                    {
                        "type": "impossible_retrocausal",
                        "node_id": node_id,
                        "message": "Retrocausal node with children but no parents",
                        "severity": "high",
                    }
                )

            # Negative scalar harmonic (impossible in scalar geometry)
            if node.scalar_harmonic < 0:
                impossible.append(
                    {
                        "type": "negative_harmonic",
                        "node_id": node_id,
                        "scalar_harmonic": node.scalar_harmonic,
                        "severity": "critical",
                    }
                )

            # Extreme deviation slopes (likely computation error)
            if abs(node.deviation_slope) > 100:
                impossible.append(
                    {
                        "type": "extreme_deviation",
                        "node_id": node_id,
                        "deviation_slope": node.deviation_slope,
                        "severity": "high",
                    }
                )

        return impossible

    def _detect_systemic_inconsistencies(
        self, graph: CausalGraph, scalar_harmonics: dict[str, float] | None
    ) -> list[dict[str, Any]]:
        """Detect system-wide inconsistencies."""
        inconsistencies = []

        # Check for isolated subgraphs
        if len(graph.nodes) > 1:
            # Find connected components
            components = self._find_connected_components(graph)
            if len(components) > 1:
                inconsistencies.append(
                    {
                        "type": "disconnected_subgraphs",
                        "component_count": len(components),
                        "component_sizes": [len(c) for c in components],
                        "severity": "high",
                    }
                )

        # Check for harmonic inconsistencies
        if scalar_harmonics:
            for node_id, node in graph.nodes.items():
                expected_harmonic = scalar_harmonics.get(node_id)
                if expected_harmonic is not None:
                    harmonic_diff = abs(node.scalar_harmonic - expected_harmonic)
                    if harmonic_diff > 0.5:
                        inconsistencies.append(
                            {
                                "type": "harmonic_mismatch",
                                "node_id": node_id,
                                "expected": expected_harmonic,
                                "actual": node.scalar_harmonic,
                                "difference": harmonic_diff,
                                "severity": "medium",
                            }
                        )

        return inconsistencies

    def _find_connected_components(self, graph: CausalGraph) -> list[set[str]]:
        """Find connected components in graph (ignoring direction)."""
        visited = set()
        components = []

        def dfs(node_id: str, component: set[str]):
            if node_id in visited:
                return
            visited.add(node_id)
            component.add(node_id)

            node = graph.get_node(node_id)
            if node:
                for neighbor_id in node.parent_ids | node.child_ids:
                    dfs(neighbor_id, component)

        for node_id in graph.nodes:
            if node_id not in visited:
                component = set()
                dfs(node_id, component)
                components.append(component)

        return components

    def _detect_unexplainable_states(self, graph: CausalGraph) -> list[dict[str, Any]]:
        """Detect states that cannot be explained by causal chain."""
        unexplainable = []

        for node_id, node in graph.nodes.items():
            # Non-root node with no parents (except retrocausal)
            if (
                node.node_type != NodeType.RETROCAUSAL
                and not node.parent_ids
                and node.child_ids
            ):
                unexplainable.append(
                    {
                        "type": "unexplained_emergence",
                        "node_id": node_id,
                        "message": "Non-root node with causal influence but no parents",
                        "severity": "medium",
                    }
                )

        return unexplainable

    def _compute_severity_breakdown(self, *anomaly_lists) -> dict[str, int]:
        """Compute severity breakdown across all anomalies."""
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for anomaly_list in anomaly_lists:
            for anomaly in anomaly_list:
                severity = anomaly.get("severity", "medium")
                breakdown[severity] = breakdown.get(severity, 0) + 1

        return breakdown

    def _generate_recommendations(self, *anomaly_lists) -> list[dict[str, Any]]:
        """Generate recommended actions based on detected anomalies."""
        recommendations = []

        # Flatten all anomalies
        all_anomalies = []
        for anomaly_list in anomaly_lists:
            all_anomalies.extend(anomaly_list)

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_anomalies.sort(
            key=lambda x: severity_order.get(x.get("severity", "medium"), 2)
        )

        # Generate recommendations for top anomalies
        for i, anomaly in enumerate(all_anomalies[:10], 1):
            anomaly_type = anomaly.get("type", "unknown")
            severity = anomaly.get("severity", "medium")

            recommendation = {
                "priority": i,
                "severity": severity,
                "anomaly_type": anomaly_type,
                "node_id": anomaly.get("node_id", "unknown"),
                "action": self._get_recommended_action(anomaly_type),
            }
            recommendations.append(recommendation)

        return recommendations

    def _get_recommended_action(self, anomaly_type: str) -> str:
        """Get recommended action for anomaly type."""
        actions = {
            "probability_break": "Investigate causal link and strengthen probability chain",
            "deviation_break": "Analyze trajectory divergence and apply correction",
            "state_vector_contradiction": "Resolve contradictory states through reconciliation",
            "invalid_probability": "Correct probability calculation or data source",
            "non_convergent_trajectory": "Apply convergence forcing or re-evaluate trajectory",
            "missing_state_vectors": "Initialize state vectors from available data",
            "zero_confidence_state": "Re-evaluate confidence scoring or remove state",
            "impossible_retrocausal": "Restructure graph to resolve retrocausal paradox",
            "negative_harmonic": "Correct scalar harmonic calculation",
            "extreme_deviation": "Investigate computation error or anomalous data",
            "disconnected_subgraphs": "Establish causal links between subgraphs",
            "harmonic_mismatch": "Synchronize scalar harmonic values across system",
            "unexplained_emergence": "Identify missing causal parents or root cause",
        }
        return actions.get(anomaly_type, "Manual investigation required")
