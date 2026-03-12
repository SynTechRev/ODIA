"""Retrocausal Inference Algorithm - Phase 14.

Implements backward causal inference to trace causal chains in reverse,
identifying root causes and causal responsibility for observed states.
"""

from __future__ import annotations

import logging
from typing import Any

from .causal_graph import CausalGraph, CausalNode, NodeType

logger = logging.getLogger(__name__)


class RetrocausalInferenceEngine:
    """Engine for retrocausal (backward) inference.

    Traces causal chains backward from observed effects to identify
    root causes, causal pathways, and responsibility distributions.
    """

    def __init__(self, max_depth: int = 12):
        """Initialize retrocausal inference engine.

        Args:
            max_depth: Maximum depth for backward tracing
        """
        self.version = "1.0.0"
        self.max_depth = max_depth

    def infer_root_causes(
        self, graph: CausalGraph, target_node_id: str
    ) -> dict[str, Any]:
        """Infer root causes for a target node.

        Traces backward through causal chain to identify all contributing
        root causes and their relative causal strengths.

        Args:
            graph: Causal graph
            target_node_id: Node to analyze

        Returns:
            Root cause analysis with causal pathways
        """
        target_node = graph.get_node(target_node_id)
        if not target_node:
            return {
                "success": False,
                "error": "Target node not found",
                "target_node_id": target_node_id,
            }

        # Perform backward trace
        causal_paths = self._trace_backward(graph, target_node_id)

        # Identify root nodes (no parents)
        root_causes = []
        for path in causal_paths:
            if path and not path[0].parent_ids:
                # Calculate path strength
                strength = self._calculate_path_strength(path)
                root_causes.append(
                    {
                        "root_node_id": path[0].node_id,
                        "path_length": len(path),
                        "causal_strength": strength,
                        "path": [node.node_id for node in path],
                    }
                )

        # Normalize causal strengths
        total_strength = sum(rc["causal_strength"] for rc in root_causes)
        if total_strength > 0:
            for rc in root_causes:
                rc["normalized_strength"] = rc["causal_strength"] / total_strength
        else:
            for rc in root_causes:
                rc["normalized_strength"] = 0.0

        return {
            "success": True,
            "target_node_id": target_node_id,
            "root_cause_count": len(root_causes),
            "root_causes": sorted(
                root_causes, key=lambda x: x["normalized_strength"], reverse=True
            ),
            "total_paths": len(causal_paths),
        }

    def _trace_backward(
        self, graph: CausalGraph, start_id: str
    ) -> list[list[CausalNode]]:
        """Trace all paths backward from a node.

        Args:
            graph: Causal graph
            start_id: Starting node ID

        Returns:
            List of causal paths (each path is list of nodes)
        """
        all_paths = []

        def dfs(node_id: str, current_path: list[CausalNode], depth: int):
            if depth > self.max_depth:
                return

            node = graph.get_node(node_id)
            if not node:
                return

            current_path = [node] + current_path

            if not node.parent_ids:
                # Reached root
                all_paths.append(current_path[:])
                return

            for parent_id in node.parent_ids:
                dfs(parent_id, current_path[:], depth + 1)

        dfs(start_id, [], 0)
        return all_paths

    def _calculate_path_strength(self, path: list[CausalNode]) -> float:
        """Calculate strength of a causal path.

        Combines QDCL probabilities, scalar harmonics, and deviation slopes.

        Args:
            path: Path of causal nodes

        Returns:
            Path strength (0-1 scale)
        """
        if not path:
            return 0.0

        # Multiply probabilities along path
        prob_product = 1.0
        for node in path:
            prob_product *= node.qdcl_probability

        # Average scalar harmonics
        harmonic_avg = sum(node.scalar_harmonic for node in path) / len(path)

        # Penalize high deviation slopes
        deviation_penalty = 1.0
        for node in path:
            deviation_penalty *= 1.0 / (1.0 + abs(node.deviation_slope))

        # Combine factors
        strength = prob_product * harmonic_avg * deviation_penalty

        return min(max(strength, 0.0), 1.0)

    def identify_causal_breaks(
        self, graph: CausalGraph, threshold: float = 0.3
    ) -> list[dict[str, Any]]:
        """Identify breaks in causal chains.

        A causal break occurs when:
        - QDCL probability drops below threshold
        - Large deviation slope discontinuity
        - Missing expected causal links

        Args:
            graph: Causal graph
            threshold: Probability threshold for detecting breaks

        Returns:
            List of identified causal breaks
        """
        breaks = []

        for node_id, node in graph.nodes.items():
            # Check probability drop
            if node.qdcl_probability < threshold:
                breaks.append(
                    {
                        "type": "probability_drop",
                        "node_id": node_id,
                        "probability": node.qdcl_probability,
                        "threshold": threshold,
                        "severity": "high" if node.qdcl_probability < 0.1 else "medium",
                    }
                )

            # Check deviation discontinuity
            if abs(node.deviation_slope) > 2.0:
                breaks.append(
                    {
                        "type": "deviation_discontinuity",
                        "node_id": node_id,
                        "deviation_slope": node.deviation_slope,
                        "severity": (
                            "high" if abs(node.deviation_slope) > 5.0 else "medium"
                        ),
                    }
                )

            # Check for isolated nodes with parents but no children
            if (
                node.parent_ids
                and not node.child_ids
                and node.node_type == NodeType.FORWARD
            ):
                # Check if any parent has other children
                has_sibling_children = False
                for parent_id in node.parent_ids:
                    parent = graph.get_node(parent_id)
                    if parent and len(parent.child_ids) > 1:
                        has_sibling_children = True
                        break

                if not has_sibling_children:
                    breaks.append(
                        {
                            "type": "causal_termination",
                            "node_id": node_id,
                            "severity": "low",
                            "message": "Causal chain terminates unexpectedly",
                        }
                    )

        return breaks

    def compute_causal_influence(
        self, graph: CausalGraph, source_id: str, target_id: str
    ) -> dict[str, Any]:
        """Compute causal influence from source to target.

        Args:
            graph: Causal graph
            source_id: Source node ID
            target_id: Target node ID

        Returns:
            Causal influence analysis
        """
        # Find all paths from source to target
        path = graph.get_causal_path(source_id, target_id)

        if not path:
            return {
                "has_influence": False,
                "source_id": source_id,
                "target_id": target_id,
                "influence_strength": 0.0,
            }

        # Calculate influence strength
        strength = self._calculate_path_strength(path)

        return {
            "has_influence": True,
            "source_id": source_id,
            "target_id": target_id,
            "influence_strength": strength,
            "path_length": len(path),
            "path": [node.node_id for node in path],
        }

    def analyze_causal_chain(
        self, graph: CausalGraph, node_ids: list[str]
    ) -> dict[str, Any]:
        """Analyze a sequence of nodes as a causal chain.

        Args:
            graph: Causal graph
            node_ids: List of node IDs in sequence

        Returns:
            Chain analysis
        """
        if len(node_ids) < 2:
            return {
                "is_valid_chain": False,
                "error": "Need at least 2 nodes for chain analysis",
            }

        nodes = [graph.get_node(node_id) for node_id in node_ids]
        if None in nodes:
            return {
                "is_valid_chain": False,
                "error": "One or more nodes not found",
            }

        # Verify chain connectivity
        is_connected = True
        for i in range(len(nodes) - 1):
            if nodes[i + 1].node_id not in nodes[i].child_ids:
                is_connected = False
                break

        # Calculate chain metrics
        avg_probability = sum(n.qdcl_probability for n in nodes) / len(nodes)
        avg_harmonic = sum(n.scalar_harmonic for n in nodes) / len(nodes)
        max_deviation = max(abs(n.deviation_slope) for n in nodes)

        # Chain strength
        chain_strength = self._calculate_path_strength(nodes)

        return {
            "is_valid_chain": is_connected,
            "chain_length": len(nodes),
            "chain_strength": chain_strength,
            "avg_probability": avg_probability,
            "avg_harmonic": avg_harmonic,
            "max_deviation": max_deviation,
            "node_ids": node_ids,
        }
