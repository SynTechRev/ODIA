"""Superpositional Hypothesis Engine - QDCL Phase 13.

Maintains simultaneous hypotheses as quantum-like state vectors with
probability weights, coherence weights, dependency entanglements,
and predicted collapse outcomes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class HypothesisState(Enum):
    """States of a hypothesis."""

    SUPERPOSITION = "superposition"  # Multiple possible states
    COLLAPSED = "collapsed"  # Resolved to single state
    ENTANGLED = "entangled"  # Dependent on other hypotheses
    DECOHERENT = "decoherent"  # Lost coherence


@dataclass
class StateVector:
    """Quantum-like state vector for a hypothesis."""

    hypothesis_id: str
    state: str
    probability: float  # 0.0 to 1.0
    coherence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Validate state vector values."""
        if not 0.0 <= self.probability <= 1.0:
            raise ValueError(f"Probability must be 0.0-1.0, got {self.probability}")
        if not 0.0 <= self.coherence <= 1.0:
            raise ValueError(f"Coherence must be 0.0-1.0, got {self.coherence}")


@dataclass
class Entanglement:
    """Dependency entanglement between hypotheses."""

    source_id: str
    target_id: str
    strength: float  # 0.0 to 1.0
    entanglement_type: str  # "reinforcing", "contradictory", "conditional"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CollapseOutcome:
    """Predicted outcome if hypothesis collapses."""

    hypothesis_id: str
    outcome_state: str
    probability: float
    impact_score: float  # Expected impact magnitude
    implications: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class Hypothesis:
    """A quantum-like hypothesis with superpositional states."""

    def __init__(
        self,
        hypothesis_id: str | None = None,
        description: str = "",
        source_agent: str = "",
    ):
        """Initialize a hypothesis.

        Args:
            hypothesis_id: Unique identifier (auto-generated if None)
            description: Human-readable description
            source_agent: Agent that generated this hypothesis
        """
        self.hypothesis_id = hypothesis_id or str(uuid4())
        self.description = description
        self.source_agent = source_agent
        self.state = HypothesisState.SUPERPOSITION
        self.state_vectors: list[StateVector] = []
        self.entanglements: list[Entanglement] = []
        self.collapse_outcomes: list[CollapseOutcome] = []
        self.created_at = datetime.now(UTC)
        self.last_updated = datetime.now(UTC)
        self.metadata: dict[str, Any] = {}

    def add_state_vector(self, state: str, probability: float, coherence: float):
        """Add a state vector to this hypothesis.

        Args:
            state: State description
            probability: Probability of this state (0.0-1.0)
            coherence: Coherence weight (0.0-1.0)
        """
        vector = StateVector(
            hypothesis_id=self.hypothesis_id,
            state=state,
            probability=probability,
            coherence=coherence,
        )
        self.state_vectors.append(vector)
        self.last_updated = datetime.now(UTC)
        logger.debug(f"Added state vector to hypothesis {self.hypothesis_id}: {state}")

    def add_entanglement(self, target_id: str, strength: float, entanglement_type: str):
        """Add an entanglement with another hypothesis.

        Args:
            target_id: ID of the entangled hypothesis
            strength: Entanglement strength (0.0-1.0)
            entanglement_type: Type of entanglement
        """
        entanglement = Entanglement(
            source_id=self.hypothesis_id,
            target_id=target_id,
            strength=strength,
            entanglement_type=entanglement_type,
        )
        self.entanglements.append(entanglement)
        self.state = HypothesisState.ENTANGLED
        self.last_updated = datetime.now(UTC)
        logger.debug(
            f"Entangled hypothesis {self.hypothesis_id} with {target_id} "
            f"(strength={strength}, type={entanglement_type})"
        )

    def add_collapse_outcome(
        self,
        outcome_state: str,
        probability: float,
        impact_score: float,
        implications: list[str],
    ):
        """Add a predicted collapse outcome.

        Args:
            outcome_state: State after collapse
            probability: Probability of this outcome
            impact_score: Impact magnitude
            implications: List of implications
        """
        outcome = CollapseOutcome(
            hypothesis_id=self.hypothesis_id,
            outcome_state=outcome_state,
            probability=probability,
            impact_score=impact_score,
            implications=implications,
        )
        self.collapse_outcomes.append(outcome)
        self.last_updated = datetime.now(UTC)
        logger.debug(
            f"Added collapse outcome to hypothesis {self.hypothesis_id}: "
            f"{outcome_state}"
        )

    def collapse(self, final_state: str):
        """Collapse hypothesis to a single state.

        Args:
            final_state: The final collapsed state
        """
        self.state = HypothesisState.COLLAPSED
        self.metadata["collapsed_state"] = final_state
        self.metadata["collapsed_at"] = datetime.now(UTC).isoformat()
        self.last_updated = datetime.now(UTC)
        logger.info(
            f"Hypothesis {self.hypothesis_id} collapsed to state: {final_state}"
        )

    def get_dominant_state(self) -> StateVector | None:
        """Get the state vector with highest probability.

        Returns:
            StateVector with highest probability, or None if no vectors
        """
        if not self.state_vectors:
            return None
        return max(self.state_vectors, key=lambda v: v.probability)

    def get_total_probability(self) -> float:
        """Get sum of all state vector probabilities.

        Returns:
            Total probability across all states
        """
        return sum(v.probability for v in self.state_vectors)

    def get_average_coherence(self) -> float:
        """Get average coherence across all state vectors.

        Returns:
            Average coherence, or 0.0 if no vectors
        """
        if not self.state_vectors:
            return 0.0
        return sum(v.coherence for v in self.state_vectors) / len(self.state_vectors)

    def to_dict(self) -> dict[str, Any]:
        """Convert hypothesis to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "hypothesis_id": self.hypothesis_id,
            "description": self.description,
            "source_agent": self.source_agent,
            "state": self.state.value,
            "state_vectors": [
                {
                    "state": v.state,
                    "probability": v.probability,
                    "coherence": v.coherence,
                    "timestamp": v.timestamp.isoformat(),
                }
                for v in self.state_vectors
            ],
            "entanglements": [
                {
                    "target_id": e.target_id,
                    "strength": e.strength,
                    "type": e.entanglement_type,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.entanglements
            ],
            "collapse_outcomes": [
                {
                    "outcome_state": o.outcome_state,
                    "probability": o.probability,
                    "impact_score": o.impact_score,
                    "implications": o.implications,
                    "timestamp": o.timestamp.isoformat(),
                }
                for o in self.collapse_outcomes
            ],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }


class SuperpositionalHypothesisEngine:
    """Engine for managing quantum-like superpositional hypotheses.

    Maintains simultaneous hypotheses as state vectors with probability weights,
    coherence weights, dependency entanglements, and predicted collapse outcomes.
    """

    def __init__(self):
        """Initialize the Superpositional Hypothesis Engine."""
        self.version = "1.0.0"
        self.hypotheses: dict[str, Hypothesis] = {}
        self.created_at = datetime.now(UTC)
        logger.info("SuperpositionalHypothesisEngine initialized")

    def create_hypothesis(self, description: str, source_agent: str = "") -> Hypothesis:
        """Create a new hypothesis.

        Args:
            description: Hypothesis description
            source_agent: Agent that generated this hypothesis

        Returns:
            New Hypothesis instance
        """
        hypothesis = Hypothesis(description=description, source_agent=source_agent)
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        logger.info(f"Created hypothesis {hypothesis.hypothesis_id}: {description}")
        return hypothesis

    def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        """Get a hypothesis by ID.

        Args:
            hypothesis_id: Hypothesis identifier

        Returns:
            Hypothesis instance or None if not found
        """
        return self.hypotheses.get(hypothesis_id)

    def entangle_hypotheses(
        self, source_id: str, target_id: str, strength: float, entanglement_type: str
    ):
        """Create entanglement between two hypotheses.

        Args:
            source_id: Source hypothesis ID
            target_id: Target hypothesis ID
            strength: Entanglement strength (0.0-1.0)
            entanglement_type: Type of entanglement
        """
        source = self.get_hypothesis(source_id)
        target = self.get_hypothesis(target_id)

        if not source or not target:
            logger.warning(
                f"Cannot entangle: hypothesis not found (source={source_id}, "
                f"target={target_id})"
            )
            return

        source.add_entanglement(target_id, strength, entanglement_type)
        # Bidirectional entanglement
        target.add_entanglement(source_id, strength, entanglement_type)
        logger.info(
            f"Entangled hypotheses {source_id} <-> {target_id} "
            f"(strength={strength}, type={entanglement_type})"
        )

    def collapse_hypothesis(self, hypothesis_id: str, final_state: str):
        """Collapse a hypothesis to a single state.

        Args:
            hypothesis_id: Hypothesis to collapse
            final_state: Final collapsed state
        """
        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            logger.warning(f"Cannot collapse: hypothesis {hypothesis_id} not found")
            return

        hypothesis.collapse(final_state)

        # Propagate collapse to entangled hypotheses
        for entanglement in hypothesis.entanglements:
            entangled = self.get_hypothesis(entanglement.target_id)
            if entangled and entangled.state == HypothesisState.SUPERPOSITION:
                # Update entangled hypothesis state
                entangled.state = HypothesisState.DECOHERENT
                logger.debug(
                    f"Hypothesis {entanglement.target_id} decoherent due to "
                    f"collapse of {hypothesis_id}"
                )

    def get_high_probability_hypotheses(
        self, threshold: float = 0.7
    ) -> list[Hypothesis]:
        """Get hypotheses with high-probability states.

        Args:
            threshold: Minimum probability threshold

        Returns:
            List of hypotheses with dominant state above threshold
        """
        result = []
        for hypothesis in self.hypotheses.values():
            dominant = hypothesis.get_dominant_state()
            if dominant and dominant.probability >= threshold:
                result.append(hypothesis)
        return result

    def get_entangled_clusters(self) -> list[list[str]]:
        """Identify clusters of entangled hypotheses.

        Returns:
            List of clusters (each cluster is a list of hypothesis IDs)
        """
        clusters: list[set[str]] = []
        visited = set()

        for hyp_id in self.hypotheses:
            if hyp_id in visited:
                continue

            cluster = self._find_entangled_cluster(hyp_id)
            if len(cluster) > 1:  # Only include actual clusters
                clusters.append(cluster)
                visited.update(cluster)

        return [list(c) for c in clusters]

    def _find_entangled_cluster(self, start_id: str) -> set[str]:
        """Find all hypotheses entangled with the starting hypothesis.

        Args:
            start_id: Starting hypothesis ID

        Returns:
            Set of all entangled hypothesis IDs
        """
        cluster = {start_id}
        to_visit = [start_id]

        while to_visit:
            current_id = to_visit.pop()
            current = self.get_hypothesis(current_id)
            if not current:
                continue

            for entanglement in current.entanglements:
                if entanglement.target_id not in cluster:
                    cluster.add(entanglement.target_id)
                    to_visit.append(entanglement.target_id)

        return cluster

    def generate_hypothesis_matrix(self) -> dict[str, Any]:
        """Generate superpositional hypothesis matrix.

        Returns:
            Matrix containing all hypotheses and their states
        """
        return {
            "version": self.version,
            "timestamp": datetime.now(UTC).isoformat(),
            "total_hypotheses": len(self.hypotheses),
            "state_distribution": self._get_state_distribution(),
            "entanglement_count": sum(
                len(h.entanglements) for h in self.hypotheses.values()
            )
            // 2,  # Divide by 2 for bidirectional
            "hypotheses": [h.to_dict() for h in self.hypotheses.values()],
            "entangled_clusters": self.get_entangled_clusters(),
        }

    def _get_state_distribution(self) -> dict[str, int]:
        """Get distribution of hypothesis states.

        Returns:
            Dictionary mapping state to count
        """
        distribution: dict[str, int] = {}
        for hypothesis in self.hypotheses.values():
            state = hypothesis.state.value
            distribution[state] = distribution.get(state, 0) + 1
        return distribution

    def to_dict(self) -> dict[str, Any]:
        """Convert engine to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "total_hypotheses": len(self.hypotheses),
            "state_distribution": self._get_state_distribution(),
        }
