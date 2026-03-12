"""Causal Graph - Phase 14 Core Data Structure.

Implements a directed acyclic graph (DAG) with support for retrocausal nodes
used for inference. Each node contains state vectors, deviation slopes,
QDCL probability weights, and scalar harmonic weights.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class NodeType(Enum):
    """Type of causal node."""

    FORWARD = "forward"  # Normal causal node
    RETROCAUSAL = "retrocausal"  # Used for backward inference
    PREDICTIVE = "predictive"  # Future state prediction


@dataclass
class StateVector:
    """State vector for a causal node."""

    dimension: str
    value: float
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension,
            "value": self.value,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CausalNode:
    """Node in the causal graph.

    Attributes:
        node_id: Unique identifier
        node_type: Type of node (forward, retrocausal, predictive)
        state_vectors: State vectors for this node
        deviation_slope: Rate of deviation from expected trajectory
        qdcl_probability: Probability weight from QDCL (Phase 13)
        scalar_harmonic: Harmonic weight from Phase 12
        parent_ids: IDs of causal parent nodes
        child_ids: IDs of predictive child nodes
        metadata: Additional metadata
    """

    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType = NodeType.FORWARD
    state_vectors: list[StateVector] = field(default_factory=list)
    deviation_slope: float = 0.0
    qdcl_probability: float = 1.0
    scalar_harmonic: float = 1.0
    parent_ids: set[str] = field(default_factory=set)
    child_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_state_vector(self, dimension: str, value: float, confidence: float = 1.0):
        """Add a state vector to this node."""
        self.state_vectors.append(StateVector(dimension, value, confidence))

    def add_parent(self, parent_id: str):
        """Add a parent node."""
        self.parent_ids.add(parent_id)

    def add_child(self, child_id: str):
        """Add a child node."""
        self.child_ids.add(child_id)

    def get_weighted_state(self) -> float:
        """Calculate weighted average of state vectors."""
        if not self.state_vectors:
            return 0.0

        total_weight = sum(sv.confidence for sv in self.state_vectors)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(sv.value * sv.confidence for sv in self.state_vectors)
        return weighted_sum / total_weight

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "state_vectors": [sv.to_dict() for sv in self.state_vectors],
            "deviation_slope": self.deviation_slope,
            "qdcl_probability": self.qdcl_probability,
            "scalar_harmonic": self.scalar_harmonic,
            "parent_ids": list(self.parent_ids),
            "child_ids": list(self.child_ids),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


class CausalGraph:
    """Directed acyclic graph for causal inference.

    Supports forward causal chains and retrocausal inference nodes.
    Detects cycles and validates graph consistency.
    """

    def __init__(self):
        """Initialize causal graph."""
        self.nodes: dict[str, CausalNode] = {}
        self.created_at = datetime.now(UTC)
        self.version = "1.0.0"

    def add_node(
        self,
        node_type: NodeType = NodeType.FORWARD,
        deviation_slope: float = 0.0,
        qdcl_probability: float = 1.0,
        scalar_harmonic: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> CausalNode:
        """Add a new node to the graph.

        Args:
            node_type: Type of node
            deviation_slope: Deviation slope value
            qdcl_probability: QDCL probability weight
            scalar_harmonic: Scalar harmonic weight
            metadata: Optional metadata

        Returns:
            Created node
        """
        node = CausalNode(
            node_type=node_type,
            deviation_slope=deviation_slope,
            qdcl_probability=qdcl_probability,
            scalar_harmonic=scalar_harmonic,
            metadata=metadata or {},
        )
        self.nodes[node.node_id] = node
        return node

    def add_edge(self, parent_id: str, child_id: str) -> bool:
        """Add a causal edge from parent to child.

        Args:
            parent_id: Parent node ID
            child_id: Child node ID

        Returns:
            True if edge added successfully, False if would create cycle
        """
        if parent_id not in self.nodes or child_id not in self.nodes:
            raise ValueError("Both nodes must exist in graph")

        # Check for cycles (only for forward nodes)
        parent_node = self.nodes[parent_id]
        child_node = self.nodes[child_id]

        if (
            parent_node.node_type != NodeType.RETROCAUSAL
            and child_node.node_type != NodeType.RETROCAUSAL
        ):
            if self._would_create_cycle(parent_id, child_id):
                return False

        # Add edge
        parent_node.add_child(child_id)
        child_node.add_parent(parent_id)
        return True

    def _would_create_cycle(self, start_id: str, end_id: str) -> bool:
        """Check if adding edge would create a cycle.

        Args:
            start_id: Starting node ID
            end_id: Ending node ID

        Returns:
            True if cycle would be created
        """
        # DFS from end_id to see if we can reach start_id
        visited = set()
        stack = [end_id]

        while stack:
            current_id = stack.pop()
            if current_id == start_id:
                return True

            if current_id in visited:
                continue

            visited.add(current_id)
            node = self.nodes[current_id]

            # Only follow forward/predictive edges
            if node.node_type != NodeType.RETROCAUSAL:
                for child_id in node.child_ids:
                    if child_id not in visited:
                        stack.append(child_id)

        return False

    def get_node(self, node_id: str) -> CausalNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_ancestors(self, node_id: str, max_depth: int = -1) -> list[CausalNode]:
        """Get all ancestor nodes (parents, grandparents, etc).

        Args:
            node_id: Node ID to start from
            max_depth: Maximum depth to traverse (-1 for unlimited)

        Returns:
            List of ancestor nodes
        """
        ancestors = []
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited:
                continue

            if max_depth >= 0 and depth > max_depth:
                continue

            visited.add(current_id)
            node = self.nodes.get(current_id)

            if node and current_id != node_id:
                ancestors.append(node)

            if node:
                for parent_id in node.parent_ids:
                    if parent_id not in visited:
                        queue.append((parent_id, depth + 1))

        return ancestors

    def get_descendants(self, node_id: str, max_depth: int = -1) -> list[CausalNode]:
        """Get all descendant nodes (children, grandchildren, etc).

        Args:
            node_id: Node ID to start from
            max_depth: Maximum depth to traverse (-1 for unlimited)

        Returns:
            List of descendant nodes
        """
        descendants = []
        visited = set()
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited:
                continue

            if max_depth >= 0 and depth > max_depth:
                continue

            visited.add(current_id)
            node = self.nodes.get(current_id)

            if node and current_id != node_id:
                descendants.append(node)

            if node:
                for child_id in node.child_ids:
                    if child_id not in visited:
                        queue.append((child_id, depth + 1))

        return descendants

    def get_causal_path(self, start_id: str, end_id: str) -> list[CausalNode] | None:
        """Find a causal path between two nodes.

        Args:
            start_id: Starting node ID
            end_id: Ending node ID

        Returns:
            List of nodes in path, or None if no path exists
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        # BFS to find path
        queue = [(start_id, [start_id])]
        visited = set()

        while queue:
            current_id, path = queue.pop(0)
            if current_id == end_id:
                return [self.nodes[node_id] for node_id in path]

            if current_id in visited:
                continue

            visited.add(current_id)
            node = self.nodes[current_id]

            for child_id in node.child_ids:
                if child_id not in visited:
                    queue.append((child_id, path + [child_id]))

        return None

    def validate_graph(self) -> dict[str, Any]:
        """Validate graph structure and consistency.

        Returns:
            Validation report with issues found
        """
        issues = []
        warnings = []

        # Check for orphan nodes
        for node_id, node in self.nodes.items():
            if not node.parent_ids and not node.child_ids:
                warnings.append(
                    {
                        "type": "orphan_node",
                        "node_id": node_id,
                        "message": "Node has no connections",
                    }
                )

        # Check for invalid probabilities
        for node_id, node in self.nodes.items():
            if not 0 <= node.qdcl_probability <= 1:
                issues.append(
                    {
                        "type": "invalid_probability",
                        "node_id": node_id,
                        "value": node.qdcl_probability,
                        "message": "QDCL probability must be between 0 and 1",
                    }
                )

        # Check for cycles in forward nodes
        for node_id in self.nodes:
            if self._has_cycle_from(node_id):
                issues.append(
                    {
                        "type": "cycle_detected",
                        "node_id": node_id,
                        "message": "Cycle detected in forward causal chain",
                    }
                )

        return {
            "is_valid": len(issues) == 0,
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "issues": issues,
            "warnings": warnings,
        }

    def _has_cycle_from(self, start_id: str) -> bool:
        """Check if there's a cycle starting from a node."""
        node = self.nodes[start_id]
        if node.node_type == NodeType.RETROCAUSAL:
            return False

        visited = set()
        stack = [(start_id, set())]

        while stack:
            current_id, path = stack.pop()
            if current_id in path:
                return True

            if current_id in visited:
                continue

            visited.add(current_id)
            node = self.nodes[current_id]

            if node.node_type != NodeType.RETROCAUSAL:
                new_path = path | {current_id}
                for child_id in node.child_ids:
                    stack.append((child_id, new_path))

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary."""
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "node_count": len(self.nodes),
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
        }

    def get_root_nodes(self) -> list[CausalNode]:
        """Get all root nodes (nodes with no parents)."""
        return [node for node in self.nodes.values() if not node.parent_ids]

    def get_leaf_nodes(self) -> list[CausalNode]:
        """Get all leaf nodes (nodes with no children)."""
        return [node for node in self.nodes.values() if not node.child_ids]
