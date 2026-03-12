"""Temporal Stability Field (TSF) for Phase 15.

Computes temporal coherence as a weighted measure:
- 40% → harmonic stability (Phase 12)
- 30% → probabilistic continuity (Phase 13)
- 20% → causal consistency (Phase 14)
- 10% → anomaly divergence factor (new)

Produces:
- Stability score
- Destabilization hotspots
- Temporal drift warnings
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from .temporal_context_graph import TemporalContextGraph


class TemporalStabilityField:
    """Temporal Stability Field for Phase 15.

    Computes measures of temporal coherence across the temporal context graph.
    """

    # Weighting factors for stability computation
    HARMONIC_WEIGHT = 0.40  # Phase 12 contribution
    PROBABILISTIC_WEIGHT = 0.30  # Phase 13 contribution
    CAUSAL_WEIGHT = 0.20  # Phase 14 contribution
    ANOMALY_WEIGHT = 0.10  # Anomaly divergence contribution

    # Thresholds
    STABILITY_THRESHOLD = 0.6
    HOTSPOT_THRESHOLD = 0.4
    DRIFT_THRESHOLD = 0.3

    # Normalization constants
    MAX_ANOMALIES_PER_NODE = 10  # Maximum expected anomalies per node for normalization

    def __init__(self):
        """Initialize Temporal Stability Field."""
        self.version = "1.0.0"
        self.computation_history: list[dict[str, Any]] = []

    def compute_stability(
        self,
        tcg: TemporalContextGraph,
        anomalies: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Compute temporal stability for the entire graph.

        Args:
            tcg: Temporal Context Graph
            anomalies: Optional list of detected anomalies

        Returns:
            Stability analysis including score, hotspots, and warnings
        """
        if not tcg.nodes:
            return {
                "stability_score": 1.0,
                "is_stable": True,
                "destabilization_hotspots": [],
                "temporal_drift_warnings": [],
                "component_scores": {
                    "harmonic_stability": 1.0,
                    "probabilistic_continuity": 1.0,
                    "causal_consistency": 1.0,
                    "anomaly_divergence": 1.0,
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Compute individual components
        harmonic_stability = self._compute_harmonic_stability(tcg)
        probabilistic_continuity = self._compute_probabilistic_continuity(tcg)
        causal_consistency = self._compute_causal_consistency(tcg)
        anomaly_divergence = self._compute_anomaly_divergence(tcg, anomalies or [])

        # Weighted stability score
        stability_score = (
            self.HARMONIC_WEIGHT * harmonic_stability
            + self.PROBABILISTIC_WEIGHT * probabilistic_continuity
            + self.CAUSAL_WEIGHT * causal_consistency
            + self.ANOMALY_WEIGHT * anomaly_divergence
        )

        # Identify hotspots and drift
        hotspots = self._identify_destabilization_hotspots(
            tcg, harmonic_stability, probabilistic_continuity, causal_consistency
        )
        drift_warnings = self._identify_temporal_drift(tcg)

        result = {
            "stability_score": round(stability_score, 4),
            "is_stable": stability_score >= self.STABILITY_THRESHOLD,
            "destabilization_hotspots": hotspots,
            "temporal_drift_warnings": drift_warnings,
            "component_scores": {
                "harmonic_stability": round(harmonic_stability, 4),
                "probabilistic_continuity": round(probabilistic_continuity, 4),
                "causal_consistency": round(causal_consistency, 4),
                "anomaly_divergence": round(anomaly_divergence, 4),
            },
            "timestamp": datetime.now(UTC).isoformat(),
            "node_count": len(tcg.nodes),
        }

        self.computation_history.append(result)
        return result

    def _compute_harmonic_stability(self, tcg: TemporalContextGraph) -> float:
        """Compute harmonic stability from Phase 12 scalar harmonics.

        Args:
            tcg: Temporal Context Graph

        Returns:
            Harmonic stability score (0.0-1.0)
        """
        if not tcg.nodes:
            return 1.0

        # Compute variance in harmonic weights
        weights = [node.harmonic_weight for node in tcg.nodes.values()]
        if not weights:
            return 1.0

        mean_weight = sum(weights) / len(weights)
        variance = sum((w - mean_weight) ** 2 for w in weights) / len(weights)

        # Lower variance = higher stability
        # Normalize variance to 0-1 scale (assuming max variance ~1.0)
        stability = max(0.0, 1.0 - min(variance, 1.0))

        return stability

    def _compute_probabilistic_continuity(self, tcg: TemporalContextGraph) -> float:
        """Compute probabilistic continuity from Phase 13 QDCL probabilities.

        Args:
            tcg: Temporal Context Graph

        Returns:
            Probabilistic continuity score (0.0-1.0)
        """
        if not tcg.nodes:
            return 1.0

        # Check probability transitions between temporal neighbors
        continuity_scores = []

        for node in tcg.nodes.values():
            # Check past->present transitions
            for past_id in node.temporal_neighbors["past"]:
                if past_id in tcg.nodes:
                    past_node = tcg.nodes[past_id]
                    # Continuity = how similar probabilities are
                    diff = abs(node.qdcl_probability - past_node.qdcl_probability)
                    continuity = 1.0 - min(diff, 1.0)
                    continuity_scores.append(continuity)

            # Check present->future transitions
            for future_id in node.temporal_neighbors["future"]:
                if future_id in tcg.nodes:
                    future_node = tcg.nodes[future_id]
                    diff = abs(node.qdcl_probability - future_node.qdcl_probability)
                    continuity = 1.0 - min(diff, 1.0)
                    continuity_scores.append(continuity)

        if not continuity_scores:
            # No transitions to measure
            return 1.0

        return sum(continuity_scores) / len(continuity_scores)

    def _compute_causal_consistency(self, tcg: TemporalContextGraph) -> float:
        """Compute causal consistency from Phase 14 causal links.

        Args:
            tcg: Temporal Context Graph

        Returns:
            Causal consistency score (0.0-1.0)
        """
        if not tcg.nodes:
            return 1.0

        consistency_scores = []

        for node in tcg.nodes.values():
            # Check if causal parents are in temporal past
            if node.causal_parent_ids:
                for parent_id in node.causal_parent_ids:
                    if parent_id in tcg.nodes:
                        parent_node = tcg.nodes[parent_id]
                        # Consistent if parent is temporally before node
                        if parent_node.timestamp < node.timestamp:
                            consistency_scores.append(1.0)
                        else:
                            consistency_scores.append(0.0)

        if not consistency_scores:
            # No causal relationships to check
            return 1.0

        return sum(consistency_scores) / len(consistency_scores)

    def _compute_anomaly_divergence(
        self, tcg: TemporalContextGraph, anomalies: list[dict[str, Any]]
    ) -> float:
        """Compute anomaly divergence factor.

        Args:
            tcg: Temporal Context Graph
            anomalies: List of detected anomalies

        Returns:
            Anomaly divergence score (0.0-1.0, higher is better)
        """
        if not tcg.nodes:
            return 1.0

        if not anomalies:
            return 1.0

        # Count anomalies affecting each node
        node_anomaly_count = {}
        for anomaly in anomalies:
            node_id = anomaly.get("node_id")
            if node_id and node_id in tcg.nodes:
                node_anomaly_count[node_id] = node_anomaly_count.get(node_id, 0) + 1

        # Compute divergence based on anomaly density
        if not node_anomaly_count:
            return 1.0

        max_anomalies = max(node_anomaly_count.values())
        # Higher anomaly count = lower score
        # Normalize using class constant
        divergence_factor = max(
            0.0, 1.0 - (max_anomalies / self.MAX_ANOMALIES_PER_NODE)
        )

        return divergence_factor

    def _identify_destabilization_hotspots(
        self,
        tcg: TemporalContextGraph,
        harmonic_stability: float,
        probabilistic_continuity: float,
        causal_consistency: float,
    ) -> list[dict[str, Any]]:
        """Identify nodes that are destabilization hotspots.

        Args:
            tcg: Temporal Context Graph
            harmonic_stability: Overall harmonic stability
            probabilistic_continuity: Overall probabilistic continuity
            causal_consistency: Overall causal consistency

        Returns:
            List of hotspot descriptions
        """
        hotspots = []

        for node_id, node in tcg.nodes.items():
            # Identify nodes with extreme values
            issues = []

            # Check harmonic weight deviation
            if node.harmonic_weight < 0.5 or node.harmonic_weight > 2.0:
                issues.append("extreme_harmonic_weight")

            # Check probability extremes
            if node.qdcl_probability < 0.2:
                issues.append("low_probability")

            # Check high uncertainty
            if node.uncertainty_index > 0.7:
                issues.append("high_uncertainty")

            # Check isolation (few neighbors)
            total_neighbors = sum(
                len(neighbors) for neighbors in node.temporal_neighbors.values()
            )
            if total_neighbors == 0:
                issues.append("isolated_node")

            if issues:
                # Compute local stability for this node
                local_stability = (
                    0.4 * (1.0 - abs(node.harmonic_weight - 1.0))
                    + 0.3 * node.qdcl_probability
                    + 0.3 * (1.0 - node.uncertainty_index)
                )

                if local_stability < self.HOTSPOT_THRESHOLD:
                    hotspots.append(
                        {
                            "node_id": node_id,
                            "timestamp": node.timestamp.isoformat(),
                            "local_stability": round(local_stability, 4),
                            "issues": issues,
                            "severity": (
                                "critical"
                                if local_stability < 0.3
                                else "high" if local_stability < 0.5 else "medium"
                            ),
                        }
                    )

        return hotspots

    def _identify_temporal_drift(
        self, tcg: TemporalContextGraph
    ) -> list[dict[str, Any]]:
        """Identify temporal drift patterns.

        Args:
            tcg: Temporal Context Graph

        Returns:
            List of drift warnings
        """
        warnings = []

        # Check for timeline branches with significant divergence
        for branch_id, node_ids in tcg.timeline_branches.items():
            if len(node_ids) < 2:
                continue

            # Get nodes in this branch
            branch_nodes = [tcg.nodes[nid] for nid in node_ids if nid in tcg.nodes]
            if len(branch_nodes) < 2:
                continue

            # Check for drift in harmonics
            harmonics = [n.harmonic_weight for n in branch_nodes]
            harmonic_drift = max(harmonics) - min(harmonics)

            if harmonic_drift > 0.5:
                warnings.append(
                    {
                        "type": "harmonic_drift",
                        "branch_id": branch_id,
                        "drift_magnitude": round(harmonic_drift, 4),
                        "severity": "high" if harmonic_drift > 1.0 else "medium",
                        "message": (
                            f"Harmonic drift of {harmonic_drift:.2f} "
                            f"in branch {branch_id}"
                        ),
                    }
                )

            # Check for probability drift
            probabilities = [n.qdcl_probability for n in branch_nodes]
            probability_drift = max(probabilities) - min(probabilities)

            if probability_drift > 0.4:
                warnings.append(
                    {
                        "type": "probability_drift",
                        "branch_id": branch_id,
                        "drift_magnitude": round(probability_drift, 4),
                        "severity": "high" if probability_drift > 0.6 else "medium",
                        "message": (
                            f"Probability drift of {probability_drift:.2f} "
                            f"in branch {branch_id}"
                        ),
                    }
                )

        # Check for nodes with increasing uncertainty over time
        sorted_nodes = sorted(tcg.nodes.values(), key=lambda n: n.timestamp)
        if len(sorted_nodes) >= 3:
            # Check recent trend
            recent = sorted_nodes[-3:]
            uncertainties = [n.uncertainty_index for n in recent]

            if all(
                uncertainties[i] < uncertainties[i + 1]
                for i in range(len(uncertainties) - 1)
            ):
                warnings.append(
                    {
                        "type": "increasing_uncertainty",
                        "severity": "medium",
                        "message": (
                            "Uncertainty index increasing in recent temporal slices"
                        ),
                        "recent_values": uncertainties,
                    }
                )

        return warnings

    def compute_local_stability(self, tcg: TemporalContextGraph, node_id: str) -> float:
        """Compute local stability for a specific node.

        Args:
            tcg: Temporal Context Graph
            node_id: Node ID to analyze

        Returns:
            Local stability score (0.0-1.0)
        """
        if node_id not in tcg.nodes:
            return 0.0

        node = tcg.nodes[node_id]

        # Factor 1: Harmonic stability (deviation from 1.0)
        harmonic_score = 1.0 - min(abs(node.harmonic_weight - 1.0), 1.0)

        # Factor 2: Probability (higher is more stable)
        probability_score = node.qdcl_probability

        # Factor 3: Uncertainty (lower is more stable)
        uncertainty_score = 1.0 - node.uncertainty_index

        # Factor 4: Connectivity (more neighbors = more stable)
        total_neighbors = sum(
            len(neighbors) for neighbors in node.temporal_neighbors.values()
        )
        connectivity_score = min(total_neighbors / 5.0, 1.0)  # Normalize to 5 neighbors

        # Weighted local stability
        local_stability = (
            0.3 * harmonic_score
            + 0.3 * probability_score
            + 0.2 * uncertainty_score
            + 0.2 * connectivity_score
        )

        return local_stability

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "computation_count": len(self.computation_history),
            "weights": {
                "harmonic": self.HARMONIC_WEIGHT,
                "probabilistic": self.PROBABILISTIC_WEIGHT,
                "causal": self.CAUSAL_WEIGHT,
                "anomaly": self.ANOMALY_WEIGHT,
            },
            "thresholds": {
                "stability": self.STABILITY_THRESHOLD,
                "hotspot": self.HOTSPOT_THRESHOLD,
                "drift": self.DRIFT_THRESHOLD,
            },
        }
