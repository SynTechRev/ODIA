"""Cross-Agent Cognitive Mesh Fusion - QDCL Phase 13.

Merges reasoning from multiple agents and transforms them into
consensus-driven semantic fractal maps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentReasoning:
    """Reasoning output from a single agent."""

    agent_type: str  # constraint, anomaly, semantic, negotiation, mesh, scalar
    agent_id: str
    reasoning: dict[str, Any]
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SemanticFractalNode:
    """Node in a semantic fractal map."""

    concept: str
    level: int  # Fractal depth level
    parent_concept: str | None
    child_concepts: list[str] = field(default_factory=list)
    agent_votes: dict[str, float] = field(default_factory=dict)  # agent_type -> weight
    consensus_strength: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticFractalMap:
    """Consensus-driven semantic fractal map from multi-agent reasoning."""

    def __init__(self):
        """Initialize semantic fractal map."""
        self.root_concepts: list[str] = []
        self.nodes: dict[str, SemanticFractalNode] = {}
        self.max_depth = 0
        self.created_at = datetime.now(UTC)

    def add_node(
        self,
        concept: str,
        level: int,
        parent_concept: str | None = None,
        agent_votes: dict[str, float] | None = None,
    ):
        """Add a node to the fractal map.

        Args:
            concept: Concept identifier
            level: Fractal depth level
            parent_concept: Parent concept (None for root)
            agent_votes: Vote weights from different agents
        """
        if concept in self.nodes:
            # Update existing node
            node = self.nodes[concept]
            if agent_votes:
                node.agent_votes.update(agent_votes)
                if len(agent_votes) > 0:
                    node.consensus_strength = sum(agent_votes.values()) / len(
                        agent_votes
                    )
        else:
            # Create new node
            node = SemanticFractalNode(
                concept=concept,
                level=level,
                parent_concept=parent_concept,
                agent_votes=agent_votes or {},
            )
            if agent_votes and len(agent_votes) > 0:
                node.consensus_strength = sum(agent_votes.values()) / len(agent_votes)
            self.nodes[concept] = node

            if parent_concept is None:
                self.root_concepts.append(concept)
            elif parent_concept in self.nodes:
                self.nodes[parent_concept].child_concepts.append(concept)

            self.max_depth = max(self.max_depth, level)

        logger.debug(
            f"Added/updated fractal node: {concept} (level={level}, "
            f"consensus={node.consensus_strength:.2f})"
        )

    def get_node(self, concept: str) -> SemanticFractalNode | None:
        """Get a node by concept.

        Args:
            concept: Concept identifier

        Returns:
            Node or None if not found
        """
        return self.nodes.get(concept)

    def get_high_consensus_concepts(self, threshold: float = 0.7) -> list[str]:
        """Get concepts with high consensus strength.

        Args:
            threshold: Minimum consensus threshold

        Returns:
            List of concept identifiers
        """
        return [
            concept
            for concept, node in self.nodes.items()
            if node.consensus_strength >= threshold
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert map to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "root_concepts": self.root_concepts,
            "total_nodes": len(self.nodes),
            "max_depth": self.max_depth,
            "nodes": [
                {
                    "concept": node.concept,
                    "level": node.level,
                    "parent_concept": node.parent_concept,
                    "child_concepts": node.child_concepts,
                    "agent_votes": node.agent_votes,
                    "consensus_strength": node.consensus_strength,
                    "metadata": node.metadata,
                }
                for node in self.nodes.values()
            ],
            "created_at": self.created_at.isoformat(),
        }


class CognitiveMeshFusion:
    """Cross-agent cognitive mesh fusion engine.

    Merges reasoning from multiple agents (constraint, anomaly, semantic,
    negotiation, mesh intelligence, scalar-convergence) and transforms them
    into consensus-driven semantic fractal maps.
    """

    def __init__(self):
        """Initialize cognitive mesh fusion engine."""
        self.version = "1.0.0"
        self.agent_reasoning: list[AgentReasoning] = []
        self.fractal_map: SemanticFractalMap | None = None
        self.created_at = datetime.now(UTC)
        logger.info("CognitiveMeshFusion initialized")

    def add_agent_reasoning(
        self,
        agent_type: str,
        agent_id: str,
        reasoning: dict[str, Any],
        confidence: float,
    ):
        """Add reasoning output from an agent.

        Args:
            agent_type: Type of agent (constraint, anomaly, semantic, etc.)
            agent_id: Unique agent identifier
            reasoning: Reasoning output dictionary
            confidence: Confidence level (0.0-1.0)
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {confidence}")

        agent_reasoning = AgentReasoning(
            agent_type=agent_type,
            agent_id=agent_id,
            reasoning=reasoning,
            confidence=confidence,
        )
        self.agent_reasoning.append(agent_reasoning)
        logger.debug(
            f"Added reasoning from {agent_type} agent {agent_id} "
            f"(confidence={confidence:.2f})"
        )

    def fuse_reasoning(self) -> SemanticFractalMap:
        """Fuse all agent reasoning into a semantic fractal map.

        Returns:
            Semantic fractal map representing consensus
        """
        self.fractal_map = SemanticFractalMap()

        # Extract concepts from each agent's reasoning
        concept_votes: dict[str, dict[str, float]] = {}  # concept -> agent_type -> vote

        for agent_reasoning in self.agent_reasoning:
            concepts = self._extract_concepts(agent_reasoning.reasoning)
            weight = agent_reasoning.confidence

            for concept in concepts:
                if concept not in concept_votes:
                    concept_votes[concept] = {}
                concept_votes[concept][agent_reasoning.agent_type] = weight

        # Build fractal hierarchy based on consensus strength
        sorted_concepts = sorted(
            concept_votes.items(),
            key=lambda x: (sum(x[1].values()) / len(x[1])) if len(x[1]) > 0 else 0.0,
            reverse=True,
        )

        # Add root concepts (highest consensus)
        root_threshold = 0.8
        for concept, votes in sorted_concepts[:5]:  # Top 5 as roots
            avg_consensus = (
                (sum(votes.values()) / len(votes)) if len(votes) > 0 else 0.0
            )
            if avg_consensus >= root_threshold:
                self.fractal_map.add_node(
                    concept=concept, level=0, parent_concept=None, agent_votes=votes
                )

        # Add child concepts (lower levels)
        for concept, votes in sorted_concepts[5:]:
            # Find best parent based on semantic similarity (simplified here)
            parent = self._find_best_parent(concept)
            level = 1 if parent else 0
            self.fractal_map.add_node(
                concept=concept, level=level, parent_concept=parent, agent_votes=votes
            )

        logger.info(
            f"Fused reasoning from {len(self.agent_reasoning)} agents into "
            f"semantic fractal map with {len(self.fractal_map.nodes)} concepts"
        )
        return self.fractal_map

    def _extract_concepts(self, reasoning: dict[str, Any]) -> list[str]:
        """Extract concepts from agent reasoning.

        Args:
            reasoning: Agent reasoning dictionary

        Returns:
            List of extracted concepts
        """
        concepts = []

        # Extract from common keys
        if "concepts" in reasoning:
            concepts.extend(reasoning["concepts"])
        if "issues" in reasoning:
            concepts.extend([str(issue) for issue in reasoning["issues"]])
        if "findings" in reasoning:
            concepts.extend([str(finding) for finding in reasoning["findings"]])
        if "constraints" in reasoning:
            concepts.extend([str(c) for c in reasoning["constraints"]])

        return concepts

    def _find_best_parent(self, concept: str) -> str | None:
        """Find best parent concept for a concept.

        Args:
            concept: Concept to find parent for

        Returns:
            Parent concept or None
        """
        if not self.fractal_map or not self.fractal_map.root_concepts:
            return None

        # Simplified: use first root concept
        # In production, use semantic similarity
        return self.fractal_map.root_concepts[0]

    def get_consensus_summary(self) -> dict[str, Any]:
        """Get summary of consensus across agents.

        Returns:
            Consensus summary
        """
        if not self.fractal_map:
            return {"error": "No fractal map generated yet"}

        agent_distribution = {}
        for reasoning in self.agent_reasoning:
            agent_type = reasoning.agent_type
            agent_distribution[agent_type] = agent_distribution.get(agent_type, 0) + 1

        return {
            "total_agents": len(self.agent_reasoning),
            "agent_distribution": agent_distribution,
            "total_concepts": len(self.fractal_map.nodes),
            "root_concepts": self.fractal_map.root_concepts,
            "max_depth": self.fractal_map.max_depth,
            "high_consensus_concepts": self.fractal_map.get_high_consensus_concepts(),
        }

    def generate_distributed_cognition_graph(self) -> dict[str, Any]:
        """Generate distributed cognition graph from fusion.

        Returns:
            Cognition graph with nodes, edges, and consensus metrics
        """
        if not self.fractal_map:
            self.fuse_reasoning()

        nodes = []
        edges = []

        for concept, node in self.fractal_map.nodes.items():
            nodes.append(
                {
                    "id": concept,
                    "label": concept,
                    "level": node.level,
                    "consensus_strength": node.consensus_strength,
                    "agent_votes": node.agent_votes,
                }
            )

            if node.parent_concept:
                edges.append(
                    {
                        "source": node.parent_concept,
                        "target": concept,
                        "weight": node.consensus_strength,
                    }
                )

        return {
            "version": self.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "nodes": nodes,
            "edges": edges,
            "summary": self.get_consensus_summary(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert fusion engine to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "agent_reasoning_count": len(self.agent_reasoning),
            "fractal_map": self.fractal_map.to_dict() if self.fractal_map else None,
            "consensus_summary": self.get_consensus_summary(),
        }
