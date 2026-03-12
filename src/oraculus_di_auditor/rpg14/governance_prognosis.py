"""Governance Prognosis Generator - Phase 14.

Generates predictive governance trajectories using causal graph analysis,
scalar harmonic weighting, and QDCL probability flows.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from .causal_graph import CausalGraph, CausalNode

logger = logging.getLogger(__name__)


class TrajectoryType:
    """Types of governance trajectories."""

    BEST_CASE = "best_case"
    WORST_CASE = "worst_case"
    MEDIAN = "median"
    PREDICTED = "predicted"


class GovernancePrognosisGenerator:
    """Generates governance trajectory prognoses.

    Produces:
    - Best-case governance trajectory
    - Worst-case governance trajectory
    - Scalar-harmonic weighted median trajectory
    - Risk advisories
    - Governance stability index
    """

    def __init__(
        self,
        time_depth: int = 12,
        branching_factor: int = 5,
        stability_threshold: float = 0.7,
    ):
        """Initialize prognosis generator.

        Args:
            time_depth: Maximum time depth for projections
            branching_factor: Maximum branches per node
            stability_threshold: Minimum stability score
        """
        self.version = "1.0.0"
        self.time_depth = time_depth
        self.branching_factor = branching_factor
        self.stability_threshold = stability_threshold

    def generate_prognosis(
        self, graph: CausalGraph, starting_nodes: list[str] | None = None
    ) -> dict[str, Any]:
        """Generate complete governance prognosis.

        Args:
            graph: Causal graph
            starting_nodes: Optional list of starting node IDs

        Returns:
            Complete prognosis with all trajectories and metrics
        """
        logger.info("Generating governance prognosis")

        # Use leaf nodes if no starting nodes specified
        if starting_nodes is None:
            starting_nodes = [node.node_id for node in graph.get_leaf_nodes()]

        if not starting_nodes:
            # Use all nodes if no leaves
            starting_nodes = list(graph.nodes.keys())

        # Generate trajectories
        best_case = self._generate_best_case_trajectory(graph, starting_nodes)
        worst_case = self._generate_worst_case_trajectory(graph, starting_nodes)
        median_trajectory = self._generate_median_trajectory(graph, starting_nodes)

        # Calculate governance stability
        stability_index = self._calculate_stability_index(
            graph, best_case, worst_case, median_trajectory
        )

        # Generate risk advisories
        risk_advisories = self._generate_risk_advisories(
            graph, worst_case, stability_index
        )

        return {
            "version": self.version,
            "starting_node_count": len(starting_nodes),
            "starting_nodes": starting_nodes,
            "best_case_trajectory": best_case,
            "worst_case_trajectory": worst_case,
            "median_trajectory": median_trajectory,
            "governance_stability_index": stability_index,
            "risk_advisories": risk_advisories,
        }

    def _generate_best_case_trajectory(
        self, graph: CausalGraph, starting_nodes: list[str]
    ) -> dict[str, Any]:
        """Generate best-case governance trajectory.

        Optimistic projection assuming high probabilities and low deviations.

        Args:
            graph: Causal graph
            starting_nodes: Starting node IDs

        Returns:
            Best-case trajectory
        """
        # Select paths with highest probabilities and best harmonics
        trajectory_nodes = []
        total_probability = 1.0

        for node_id in starting_nodes:
            node = graph.get_node(node_id)
            if not node:
                continue

            # Trace forward through highest probability paths
            path = self._trace_optimal_path(graph, node_id, optimize_for="best")
            trajectory_nodes.extend(path)
            total_probability *= self._calculate_path_probability(path)

        # Calculate trajectory metrics
        avg_harmonic = (
            sum(n.scalar_harmonic for n in trajectory_nodes) / len(trajectory_nodes)
            if trajectory_nodes
            else 1.0
        )
        avg_deviation = (
            sum(abs(n.deviation_slope) for n in trajectory_nodes)
            / len(trajectory_nodes)
            if trajectory_nodes
            else 0.0
        )

        return {
            "trajectory_type": TrajectoryType.BEST_CASE,
            "node_count": len(trajectory_nodes),
            "node_ids": [n.node_id for n in trajectory_nodes],
            "total_probability": total_probability,
            "avg_harmonic": avg_harmonic,
            "avg_deviation": avg_deviation,
            "outcome_score": self._calculate_outcome_score(
                total_probability, avg_harmonic, avg_deviation
            ),
        }

    def _generate_worst_case_trajectory(
        self, graph: CausalGraph, starting_nodes: list[str]
    ) -> dict[str, Any]:
        """Generate worst-case governance trajectory.

        Pessimistic projection assuming low probabilities and high deviations.

        Args:
            graph: Causal graph
            starting_nodes: Starting node IDs

        Returns:
            Worst-case trajectory
        """
        trajectory_nodes = []
        total_probability = 1.0

        for node_id in starting_nodes:
            node = graph.get_node(node_id)
            if not node:
                continue

            # Trace through lowest probability paths
            path = self._trace_optimal_path(graph, node_id, optimize_for="worst")
            trajectory_nodes.extend(path)
            total_probability *= self._calculate_path_probability(path)

        avg_harmonic = (
            sum(n.scalar_harmonic for n in trajectory_nodes) / len(trajectory_nodes)
            if trajectory_nodes
            else 1.0
        )
        avg_deviation = (
            sum(abs(n.deviation_slope) for n in trajectory_nodes)
            / len(trajectory_nodes)
            if trajectory_nodes
            else 0.0
        )

        return {
            "trajectory_type": TrajectoryType.WORST_CASE,
            "node_count": len(trajectory_nodes),
            "node_ids": [n.node_id for n in trajectory_nodes],
            "total_probability": total_probability,
            "avg_harmonic": avg_harmonic,
            "avg_deviation": avg_deviation,
            "outcome_score": self._calculate_outcome_score(
                total_probability, avg_harmonic, avg_deviation
            ),
        }

    def _generate_median_trajectory(
        self, graph: CausalGraph, starting_nodes: list[str]
    ) -> dict[str, Any]:
        """Generate scalar-harmonic weighted median trajectory.

        Balanced projection using scalar harmonic weighting.

        Args:
            graph: Causal graph
            starting_nodes: Starting node IDs

        Returns:
            Median trajectory
        """
        trajectory_nodes = []
        total_probability = 1.0

        for node_id in starting_nodes:
            node = graph.get_node(node_id)
            if not node:
                continue

            # Trace through harmonic-weighted paths
            path = self._trace_optimal_path(graph, node_id, optimize_for="median")
            trajectory_nodes.extend(path)
            total_probability *= self._calculate_path_probability(path)

        avg_harmonic = (
            sum(n.scalar_harmonic for n in trajectory_nodes) / len(trajectory_nodes)
            if trajectory_nodes
            else 1.0
        )
        avg_deviation = (
            sum(abs(n.deviation_slope) for n in trajectory_nodes)
            / len(trajectory_nodes)
            if trajectory_nodes
            else 0.0
        )

        return {
            "trajectory_type": TrajectoryType.MEDIAN,
            "node_count": len(trajectory_nodes),
            "node_ids": [n.node_id for n in trajectory_nodes],
            "total_probability": total_probability,
            "avg_harmonic": avg_harmonic,
            "avg_deviation": avg_deviation,
            "outcome_score": self._calculate_outcome_score(
                total_probability, avg_harmonic, avg_deviation
            ),
        }

    def _trace_optimal_path(
        self, graph: CausalGraph, start_id: str, optimize_for: str = "best"
    ) -> list[CausalNode]:
        """Trace optimal path from a starting node.

        Args:
            graph: Causal graph
            start_id: Starting node ID
            optimize_for: "best", "worst", or "median"

        Returns:
            List of nodes in optimal path
        """
        path = []
        current_id = start_id
        visited = set()
        depth = 0

        while current_id and depth < self.time_depth:
            if current_id in visited:
                break

            node = graph.get_node(current_id)
            if not node:
                break

            path.append(node)
            visited.add(current_id)

            # Get children and select next node
            if not node.child_ids:
                break

            children = [graph.get_node(cid) for cid in node.child_ids]
            children = [c for c in children if c is not None]

            if not children:
                break

            # Select next node based on optimization strategy
            if optimize_for == "best":
                # Highest probability * harmonic / deviation
                next_node = max(
                    children,
                    key=lambda n: n.qdcl_probability
                    * n.scalar_harmonic
                    / (1.0 + abs(n.deviation_slope)),
                )
            elif optimize_for == "worst":
                # Lowest probability * harmonic / deviation
                next_node = min(
                    children,
                    key=lambda n: n.qdcl_probability
                    * n.scalar_harmonic
                    / (1.0 + abs(n.deviation_slope)),
                )
            else:  # median
                # Closest to harmonic = 1.0
                next_node = min(children, key=lambda n: abs(n.scalar_harmonic - 1.0))

            current_id = next_node.node_id
            depth += 1

        return path

    def _calculate_path_probability(self, path: list[CausalNode]) -> float:
        """Calculate cumulative probability of path."""
        if not path:
            return 0.0

        prob = 1.0
        for node in path:
            prob *= node.qdcl_probability

        return prob

    def _calculate_outcome_score(
        self, probability: float, harmonic: float, deviation: float
    ) -> float:
        """Calculate outcome score for trajectory.

        Args:
            probability: Cumulative probability
            harmonic: Average harmonic
            deviation: Average deviation

        Returns:
            Outcome score (0-1)
        """
        # Normalize harmonic: 1.0 is optimal
        harmonic_score = 1.0 / (1.0 + abs(harmonic - 1.0))

        # Normalize deviation: lower is better
        deviation_score = math.exp(-abs(deviation))

        # Combine factors
        score = probability * 0.4 + harmonic_score * 0.3 + deviation_score * 0.3

        return min(max(score, 0.0), 1.0)

    def _calculate_stability_index(
        self,
        graph: CausalGraph,
        best_case: dict[str, Any],
        worst_case: dict[str, Any],
        median: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate governance stability index.

        Args:
            graph: Causal graph
            best_case: Best case trajectory
            worst_case: Worst case trajectory
            median: Median trajectory

        Returns:
            Stability index report
        """
        # Calculate spread between best and worst
        outcome_spread = abs(best_case["outcome_score"] - worst_case["outcome_score"])

        # Lower spread = higher stability
        stability_score = 1.0 - outcome_spread

        # Check for structural stability indicators
        root_nodes = graph.get_root_nodes()
        leaf_nodes = graph.get_leaf_nodes()

        # More roots/leaves = less stable (more entry/exit points)
        structural_stability = 1.0 / (1.0 + 0.1 * (len(root_nodes) + len(leaf_nodes)))

        # Average probability across all nodes
        avg_global_probability = (
            sum(n.qdcl_probability for n in graph.nodes.values()) / len(graph.nodes)
            if graph.nodes
            else 0.0
        )

        # Combined stability
        combined_stability = (
            stability_score * 0.5
            + structural_stability * 0.3
            + avg_global_probability * 0.2
        )

        is_stable = combined_stability >= self.stability_threshold

        return {
            "stability_score": combined_stability,
            "is_stable": is_stable,
            "outcome_spread": outcome_spread,
            "structural_stability": structural_stability,
            "avg_probability": avg_global_probability,
            "root_node_count": len(root_nodes),
            "leaf_node_count": len(leaf_nodes),
            "threshold": self.stability_threshold,
        }

    def _generate_risk_advisories(
        self,
        graph: CausalGraph,
        worst_case: dict[str, Any],
        stability_index: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate risk advisories based on prognosis.

        Args:
            graph: Causal graph
            worst_case: Worst case trajectory
            stability_index: Stability index

        Returns:
            List of risk advisories
        """
        advisories = []

        # Unstable governance
        if not stability_index["is_stable"]:
            advisories.append(
                {
                    "risk_level": "high",
                    "category": "governance_instability",
                    "message": f"Governance stability below threshold ({stability_index['stability_score']:.3f} < {self.stability_threshold})",
                    "recommendation": "Strengthen causal links and reduce outcome variance",
                }
            )

        # Low worst-case outcome
        if worst_case["outcome_score"] < 0.3:
            advisories.append(
                {
                    "risk_level": "critical",
                    "category": "catastrophic_trajectory",
                    "message": f"Worst-case outcome score critically low: {worst_case['outcome_score']:.3f}",
                    "recommendation": "Implement preventive measures to avoid worst-case scenarios",
                }
            )

        # High outcome spread
        if stability_index["outcome_spread"] > 0.5:
            advisories.append(
                {
                    "risk_level": "medium",
                    "category": "high_uncertainty",
                    "message": f"Large spread between best/worst outcomes: {stability_index['outcome_spread']:.3f}",
                    "recommendation": "Reduce uncertainty through additional constraints",
                }
            )

        # Low global probability
        if stability_index["avg_probability"] < 0.5:
            advisories.append(
                {
                    "risk_level": "high",
                    "category": "weak_causal_chains",
                    "message": f"Average causal probability low: {stability_index['avg_probability']:.3f}",
                    "recommendation": "Strengthen causal relationships across the graph",
                }
            )

        # Too many entry/exit points
        if stability_index["root_node_count"] > 10:
            advisories.append(
                {
                    "risk_level": "medium",
                    "category": "fragmented_causality",
                    "message": f"High number of root nodes: {stability_index['root_node_count']}",
                    "recommendation": "Consolidate causal origins to reduce fragmentation",
                }
            )

        return advisories
