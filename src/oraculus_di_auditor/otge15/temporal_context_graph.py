"""Temporal Context Graph (TCG) for Phase 15.

Stores temporal slices with:
- Past, present, and projected future states
- Phase 12 scalar harmonics at each slice
- QDCL quantum probabilities for transitions
- Causal links from Phase 14
- Bidirectional traversal (past → future, future → past)
- Cross-timeline linking (parallel possibility branches)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class TemporalNode:
    """Node in the temporal context graph.

    Represents a state at a specific temporal slice with associated
    quantum, harmonic, and causal properties.
    """

    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    state_vector: dict[str, Any] = field(default_factory=dict)
    harmonic_weight: float = 1.0  # Phase 12 scalar harmonic
    qdcl_probability: float = 1.0  # Phase 13 quantum probability
    causal_parent_ids: list[str] = field(default_factory=list)  # Phase 14 causal links
    temporal_neighbors: dict[str, list[str]] = field(
        default_factory=lambda: {"past": [], "future": [], "parallel": []}
    )
    uncertainty_index: float = 0.0  # Measure of temporal uncertainty
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of temporal node
        """
        return {
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "state_vector": self.state_vector,
            "harmonic_weight": self.harmonic_weight,
            "qdcl_probability": self.qdcl_probability,
            "causal_parent_ids": self.causal_parent_ids,
            "temporal_neighbors": self.temporal_neighbors,
            "uncertainty_index": self.uncertainty_index,
            "metadata": self.metadata,
        }


class TemporalContextGraph:
    """Temporal Context Graph for Phase 15.

    Stores and manages temporal slices with cross-timeline linking,
    bidirectional traversal, and integration with Phases 12-14.
    """

    # Constants
    TEMPORAL_SLICE_MATCH_THRESHOLD = 1.0  # seconds for temporal slice matching

    def __init__(self):
        """Initialize Temporal Context Graph."""
        self.version = "1.0.0"
        self.nodes: dict[str, TemporalNode] = {}
        self.timeline_branches: dict[str, list[str]] = {}  # branch_id -> node_ids
        self.created_at = datetime.now(UTC)

    def add_temporal_slice(
        self,
        state_vector: dict[str, Any],
        harmonic_weight: float = 1.0,
        qdcl_probability: float = 1.0,
        causal_parent_ids: list[str] | None = None,
        uncertainty_index: float = 0.0,
        metadata: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> TemporalNode:
        """Add a temporal slice to the graph.

        Args:
            state_vector: System state at this temporal slice
            harmonic_weight: Phase 12 scalar harmonic weight
            qdcl_probability: Phase 13 quantum probability
            causal_parent_ids: Phase 14 causal parent node IDs
            uncertainty_index: Temporal uncertainty measure
            metadata: Additional metadata
            timestamp: Timestamp for this slice (defaults to now)

        Returns:
            Created temporal node
        """
        node = TemporalNode(
            timestamp=timestamp or datetime.now(UTC),
            state_vector=state_vector,
            harmonic_weight=harmonic_weight,
            qdcl_probability=qdcl_probability,
            causal_parent_ids=causal_parent_ids or [],
            uncertainty_index=uncertainty_index,
            metadata=metadata or {},
        )

        self.nodes[node.node_id] = node
        return node

    def link_temporal_neighbors(
        self,
        node_id: str,
        past_ids: list[str] | None = None,
        future_ids: list[str] | None = None,
        parallel_ids: list[str] | None = None,
    ) -> bool:
        """Link temporal neighbors to a node.

        Args:
            node_id: Node to link
            past_ids: Past neighbor node IDs
            future_ids: Future neighbor node IDs
            parallel_ids: Parallel timeline node IDs

        Returns:
            True if successful
        """
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]

        if past_ids:
            node.temporal_neighbors["past"].extend(past_ids)
        if future_ids:
            node.temporal_neighbors["future"].extend(future_ids)
        if parallel_ids:
            node.temporal_neighbors["parallel"].extend(parallel_ids)

        return True

    def traverse_backward(
        self, start_node_id: str, max_depth: int = 10
    ) -> list[TemporalNode]:
        """Traverse graph backward in time.

        Args:
            start_node_id: Starting node ID
            max_depth: Maximum traversal depth

        Returns:
            List of temporal nodes in backward traversal order
        """
        if start_node_id not in self.nodes:
            return []

        visited = set()
        path = []

        def _traverse(node_id: str, depth: int):
            if depth >= max_depth or node_id in visited or node_id not in self.nodes:
                return

            visited.add(node_id)
            node = self.nodes[node_id]
            path.append(node)

            # Traverse to past neighbors
            for past_id in node.temporal_neighbors["past"]:
                _traverse(past_id, depth + 1)

        _traverse(start_node_id, 0)
        return path

    def traverse_forward(
        self, start_node_id: str, max_depth: int = 10
    ) -> list[TemporalNode]:
        """Traverse graph forward in time.

        Args:
            start_node_id: Starting node ID
            max_depth: Maximum traversal depth

        Returns:
            List of temporal nodes in forward traversal order
        """
        if start_node_id not in self.nodes:
            return []

        visited = set()
        path = []

        def _traverse(node_id: str, depth: int):
            if depth >= max_depth or node_id in visited or node_id not in self.nodes:
                return

            visited.add(node_id)
            node = self.nodes[node_id]
            path.append(node)

            # Traverse to future neighbors
            for future_id in node.temporal_neighbors["future"]:
                _traverse(future_id, depth + 1)

        _traverse(start_node_id, 0)
        return path

    def get_parallel_timelines(self, node_id: str) -> list[TemporalNode]:
        """Get parallel timeline nodes.

        Args:
            node_id: Node ID to get parallel timelines for

        Returns:
            List of parallel timeline nodes
        """
        if node_id not in self.nodes:
            return []

        node = self.nodes[node_id]
        return [
            self.nodes[pid]
            for pid in node.temporal_neighbors["parallel"]
            if pid in self.nodes
        ]

    def create_timeline_branch(
        self, branch_point_id: str, branch_name: str | None = None
    ) -> str:
        """Create a new timeline branch from a branch point.

        Args:
            branch_point_id: Node ID to branch from
            branch_name: Optional branch name

        Returns:
            Branch ID
        """
        if branch_point_id not in self.nodes:
            raise ValueError(f"Node {branch_point_id} not found")

        branch_id = branch_name or f"branch_{str(uuid.uuid4())[:8]}"
        self.timeline_branches[branch_id] = [branch_point_id]
        return branch_id

    def add_node_to_branch(self, branch_id: str, node_id: str) -> bool:
        """Add a node to a timeline branch.

        Args:
            branch_id: Branch ID
            node_id: Node ID to add

        Returns:
            True if successful
        """
        if branch_id not in self.timeline_branches:
            return False
        if node_id not in self.nodes:
            return False

        self.timeline_branches[branch_id].append(node_id)
        return True

    def get_temporal_slice(self, timestamp: datetime) -> list[TemporalNode]:
        """Get all nodes at a specific temporal slice.

        Args:
            timestamp: Timestamp to query

        Returns:
            List of nodes at that timestamp
        """
        # Find nodes within 1 second of target timestamp
        return [
            node
            for node in self.nodes.values()
            if abs((node.timestamp - timestamp).total_seconds())
            < self.TEMPORAL_SLICE_MATCH_THRESHOLD
        ]

    def compute_temporal_distance(self, node_id1: str, node_id2: str) -> float:
        """Compute temporal distance between two nodes.

        Args:
            node_id1: First node ID
            node_id2: Second node ID

        Returns:
            Temporal distance (in seconds)
        """
        if node_id1 not in self.nodes or node_id2 not in self.nodes:
            return float("inf")

        node1 = self.nodes[node_id1]
        node2 = self.nodes[node_id2]

        return abs((node1.timestamp - node2.timestamp).total_seconds())

    def get_root_nodes(self) -> list[TemporalNode]:
        """Get root nodes (nodes with no past neighbors).

        Returns:
            List of root temporal nodes
        """
        return [
            node for node in self.nodes.values() if not node.temporal_neighbors["past"]
        ]

    def get_leaf_nodes(self) -> list[TemporalNode]:
        """Get leaf nodes (nodes with no future neighbors).

        Returns:
            List of leaf temporal nodes
        """
        return [
            node
            for node in self.nodes.values()
            if not node.temporal_neighbors["future"]
        ]

    def validate_temporal_consistency(self) -> dict[str, Any]:
        """Validate temporal consistency of the graph.

        Returns:
            Validation report
        """
        issues: list[dict[str, Any]] = []
        issues.extend(self._check_temporal_causality())
        issues.extend(self._find_orphaned_nodes())

        return {
            "valid": len(issues) == 0,
            "total_nodes": len(self.nodes),
            "total_branches": len(self.timeline_branches),
            "issues": issues,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _check_temporal_causality(self) -> list[dict[str, Any]]:
        """Check ordering of past and future neighbors.

        Returns:
            List of temporal violation issues.
        """
        violations: list[dict[str, Any]] = []
        for node_id, node in self.nodes.items():
            for past_id in node.temporal_neighbors["past"]:
                if past_id in self.nodes:
                    past_node = self.nodes[past_id]
                    if past_node.timestamp >= node.timestamp:
                        violations.append(
                            {
                                "type": "temporal_violation",
                                "node_id": node_id,
                                "past_node_id": past_id,
                                "message": "Past neighbor has later or equal timestamp",
                            }
                        )
            for future_id in node.temporal_neighbors["future"]:
                if future_id in self.nodes:
                    future_node = self.nodes[future_id]
                    if future_node.timestamp <= node.timestamp:
                        violations.append(
                            {
                                "type": "temporal_violation",
                                "node_id": node_id,
                                "future_node_id": future_id,
                                "message": (
                                    "Future neighbor has earlier or equal timestamp"
                                ),
                            }
                        )
        return violations

    def _find_orphaned_nodes(self) -> list[dict[str, Any]]:
        """Identify nodes with no temporal connections.

        Returns:
            List of orphaned node issues.
        """
        connected_nodes = set()
        for node in self.nodes.values():
            connected_nodes.update(node.temporal_neighbors["past"])
            connected_nodes.update(node.temporal_neighbors["future"])
            connected_nodes.update(node.temporal_neighbors["parallel"])
            if (
                node.temporal_neighbors["past"]
                or node.temporal_neighbors["future"]
                or node.temporal_neighbors["parallel"]
            ):
                connected_nodes.add(node.node_id)
        orphaned = set(self.nodes.keys()) - connected_nodes
        return [
            {
                "type": "orphaned_node",
                "node_id": orphan_id,
                "message": "Node is not connected to any temporal neighbors",
            }
            for orphan_id in orphaned
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of temporal context graph
        """
        return {
            "version": self.version,
            "node_count": len(self.nodes),
            "branch_count": len(self.timeline_branches),
            "created_at": self.created_at.isoformat(),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "timeline_branches": self.timeline_branches,
            "root_node_count": len(self.get_root_nodes()),
            "leaf_node_count": len(self.get_leaf_nodes()),
        }
