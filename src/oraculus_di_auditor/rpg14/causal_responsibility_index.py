"""Causal Responsibility Index (CRI) - Phase 14.

Computes a quantifiable responsibility metric (0-1 scale) for causal nodes,
entities, components, or events using harmonic weighting, QDCL probability
integration, deviation adjustments, and anomaly penalties.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from .causal_graph import CausalGraph, CausalNode

logger = logging.getLogger(__name__)


class CausalResponsibilityIndex:
    """Computes Causal Responsibility Index (CRI) for nodes.

    CRI is a deterministic metric (0-1 scale) that quantifies causal
    responsibility based on:
    - Harmonic weighted factors from Phase 12
    - QDCL probability integration from Phase 13
    - Deviation-slope adjustments
    - Anomaly-penalty multipliers
    - Path-length normalization
    """

    def __init__(
        self,
        harmonic_weight: float = 0.3,
        probability_weight: float = 0.3,
        deviation_weight: float = 0.2,
        connectivity_weight: float = 0.2,
    ):
        """Initialize CRI calculator.

        Args:
            harmonic_weight: Weight for scalar harmonic factor
            probability_weight: Weight for QDCL probability factor
            deviation_weight: Weight for deviation slope factor
            connectivity_weight: Weight for connectivity factor
        """
        self.version = "1.0.0"

        # Validate weights sum to 1.0
        total_weight = (
            harmonic_weight
            + probability_weight
            + deviation_weight
            + connectivity_weight
        )
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")

        self.harmonic_weight = harmonic_weight
        self.probability_weight = probability_weight
        self.deviation_weight = deviation_weight
        self.connectivity_weight = connectivity_weight

    def compute_cri(
        self, graph: CausalGraph, node_id: str, anomaly_penalty: float = 0.0
    ) -> dict[str, Any]:
        """Compute Causal Responsibility Index for a node.

        Args:
            graph: Causal graph
            node_id: Node to compute CRI for
            anomaly_penalty: Penalty factor for anomalies (0-1)

        Returns:
            CRI computation result with breakdown
        """
        node = graph.get_node(node_id)
        if not node:
            return {
                "success": False,
                "error": "Node not found",
                "node_id": node_id,
                "cri": 0.0,
            }

        # Compute individual factors
        harmonic_factor = self._compute_harmonic_factor(node)
        probability_factor = self._compute_probability_factor(node)
        deviation_factor = self._compute_deviation_factor(node)
        connectivity_factor = self._compute_connectivity_factor(graph, node)

        # Weighted sum
        raw_cri = (
            self.harmonic_weight * harmonic_factor
            + self.probability_weight * probability_factor
            + self.deviation_weight * deviation_factor
            + self.connectivity_weight * connectivity_factor
        )

        # Apply anomaly penalty
        final_cri = raw_cri * (1.0 - anomaly_penalty)

        # Ensure in [0, 1] range
        final_cri = min(max(final_cri, 0.0), 1.0)

        return {
            "success": True,
            "node_id": node_id,
            "cri": final_cri,
            "raw_cri": raw_cri,
            "factors": {
                "harmonic": harmonic_factor,
                "probability": probability_factor,
                "deviation": deviation_factor,
                "connectivity": connectivity_factor,
            },
            "weights": {
                "harmonic": self.harmonic_weight,
                "probability": self.probability_weight,
                "deviation": self.deviation_weight,
                "connectivity": self.connectivity_weight,
            },
            "anomaly_penalty": anomaly_penalty,
            "metadata": {
                "scalar_harmonic": node.scalar_harmonic,
                "qdcl_probability": node.qdcl_probability,
                "deviation_slope": node.deviation_slope,
                "parent_count": len(node.parent_ids),
                "child_count": len(node.child_ids),
            },
        }

    def _compute_harmonic_factor(self, node: CausalNode) -> float:
        """Compute harmonic factor based on scalar harmonic weight.

        Scalar harmonic values are typically in [0, 2] range.
        We normalize to [0, 1] with 1.0 being optimal.

        Args:
            node: Causal node

        Returns:
            Harmonic factor (0-1)
        """
        # Normalize scalar harmonic: 1.0 is optimal, deviations reduce factor
        deviation_from_optimal = abs(node.scalar_harmonic - 1.0)
        factor = 1.0 / (1.0 + deviation_from_optimal)
        return factor

    def _compute_probability_factor(self, node: CausalNode) -> float:
        """Compute probability factor from QDCL probability.

        Args:
            node: Causal node

        Returns:
            Probability factor (0-1)
        """
        # QDCL probability is already in [0, 1]
        return node.qdcl_probability

    def _compute_deviation_factor(self, node: CausalNode) -> float:
        """Compute deviation factor from deviation slope.

        Lower absolute deviation is better. We penalize high deviations.

        Args:
            node: Causal node

        Returns:
            Deviation factor (0-1)
        """
        # Deviation slope can be any real number
        # We use exponential decay: factor = exp(-|slope|)
        # For slope=0: factor=1.0
        # For slope=1: factor≈0.37
        # For slope=3: factor≈0.05
        factor = math.exp(-abs(node.deviation_slope))
        return factor

    def _compute_connectivity_factor(
        self, graph: CausalGraph, node: CausalNode
    ) -> float:
        """Compute connectivity factor based on graph position.

        Nodes with more connections and central positions have higher
        causal responsibility.

        Args:
            graph: Causal graph
            node: Causal node

        Returns:
            Connectivity factor (0-1)
        """
        parent_count = len(node.parent_ids)
        child_count = len(node.child_ids)
        total_connections = parent_count + child_count

        if total_connections == 0:
            # Isolated node
            return 0.0

        # Normalize by total graph size
        max_possible_connections = len(graph.nodes) - 1
        if max_possible_connections == 0:
            return 1.0

        connectivity_ratio = total_connections / max_possible_connections

        # Apply square root to reduce impact of super-connected nodes
        factor = math.sqrt(connectivity_ratio)
        return min(factor, 1.0)

    def compute_aggregate_cri(
        self,
        graph: CausalGraph,
        node_ids: list[str],
        anomaly_penalties: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compute aggregate CRI for multiple nodes.

        Args:
            graph: Causal graph
            node_ids: List of node IDs
            anomaly_penalties: Optional dict of anomaly penalties per node

        Returns:
            Aggregate CRI analysis
        """
        if anomaly_penalties is None:
            anomaly_penalties = {}

        results = []
        for node_id in node_ids:
            penalty = anomaly_penalties.get(node_id, 0.0)
            cri_result = self.compute_cri(graph, node_id, penalty)
            if cri_result["success"]:
                results.append(cri_result)

        if not results:
            return {
                "success": False,
                "error": "No valid CRI computations",
                "node_count": 0,
            }

        # Compute statistics
        cri_values = [r["cri"] for r in results]
        avg_cri = sum(cri_values) / len(cri_values)
        min_cri = min(cri_values)
        max_cri = max(cri_values)

        # Identify high/low responsibility nodes
        high_responsibility = [r for r in results if r["cri"] >= 0.7]
        low_responsibility = [r for r in results if r["cri"] < 0.3]

        return {
            "success": True,
            "node_count": len(results),
            "avg_cri": avg_cri,
            "min_cri": min_cri,
            "max_cri": max_cri,
            "high_responsibility_count": len(high_responsibility),
            "low_responsibility_count": len(low_responsibility),
            "high_responsibility_nodes": [r["node_id"] for r in high_responsibility],
            "low_responsibility_nodes": [r["node_id"] for r in low_responsibility],
            "all_results": results,
        }

    def rank_by_responsibility(
        self, graph: CausalGraph, anomaly_penalties: dict[str, float] | None = None
    ) -> list[dict[str, Any]]:
        """Rank all nodes by CRI.

        Args:
            graph: Causal graph
            anomaly_penalties: Optional dict of anomaly penalties per node

        Returns:
            Sorted list of CRI results (highest first)
        """
        if anomaly_penalties is None:
            anomaly_penalties = {}

        results = []
        for node_id in graph.nodes:
            penalty = anomaly_penalties.get(node_id, 0.0)
            cri_result = self.compute_cri(graph, node_id, penalty)
            if cri_result["success"]:
                results.append(cri_result)

        # Sort by CRI descending
        results.sort(key=lambda x: x["cri"], reverse=True)
        return results

    def explain_cri(self, cri_result: dict[str, Any]) -> str:
        """Generate human-readable explanation of CRI.

        Args:
            cri_result: Result from compute_cri()

        Returns:
            Explanation string
        """
        if not cri_result.get("success"):
            return f"CRI computation failed: {cri_result.get('error', 'Unknown error')}"

        cri = cri_result["cri"]
        node_id = cri_result["node_id"]
        factors = cri_result["factors"]

        explanation = f"Node {node_id[:8]}... has CRI of {cri:.3f}\n"

        if cri >= 0.7:
            explanation += "This indicates HIGH causal responsibility.\n"
        elif cri >= 0.4:
            explanation += "This indicates MODERATE causal responsibility.\n"
        else:
            explanation += "This indicates LOW causal responsibility.\n"

        explanation += "\nFactor breakdown:\n"
        explanation += f"  - Harmonic: {factors['harmonic']:.3f} (weight: {self.harmonic_weight})\n"
        explanation += f"  - Probability: {factors['probability']:.3f} (weight: {self.probability_weight})\n"
        explanation += f"  - Deviation: {factors['deviation']:.3f} (weight: {self.deviation_weight})\n"
        explanation += f"  - Connectivity: {factors['connectivity']:.3f} (weight: {self.connectivity_weight})\n"

        if cri_result["anomaly_penalty"] > 0:
            explanation += (
                f"\nAnomaly penalty applied: {cri_result['anomaly_penalty']:.3f}"
            )

        return explanation
