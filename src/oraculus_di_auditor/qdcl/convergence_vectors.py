"""Convergence Vector Generator - QDCL Phase 13.

Transforms distributed cognition into action, risk, coherence, and complexity vectors
that guide self-healing, scalar integration, and adaptive agent behavior.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VectorType(Enum):
    """Types of convergence vectors."""

    ACTION = "action"
    RISK = "risk"
    COHERENCE = "coherence"
    COMPLEXITY = "complexity"


@dataclass
class ConvergenceVector:
    """A convergence vector for guiding system behavior."""

    vector_id: str
    vector_type: VectorType
    magnitude: float  # 0.0 to 1.0
    direction: dict[str, float]  # Component -> weight mapping
    target_phase: int | None  # Target phase (1-12) or None for all
    priority: float  # 0.0 to 1.0
    timestamp: datetime
    metadata: dict[str, Any]

    def __post_init__(self):
        """Validate vector values."""
        if not 0.0 <= self.magnitude <= 1.0:
            raise ValueError(f"Magnitude must be 0.0-1.0, got {self.magnitude}")
        if not 0.0 <= self.priority <= 1.0:
            raise ValueError(f"Priority must be 0.0-1.0, got {self.priority}")


class ConvergenceVectorSet:
    """Set of convergence vectors organized by type."""

    def __init__(self):
        """Initialize convergence vector set."""
        self.action_vectors: list[ConvergenceVector] = []
        self.risk_vectors: list[ConvergenceVector] = []
        self.coherence_vectors: list[ConvergenceVector] = []
        self.complexity_vectors: list[ConvergenceVector] = []
        self.created_at = datetime.now(UTC)

    def add_vector(self, vector: ConvergenceVector):
        """Add a convergence vector to the set.

        Args:
            vector: Convergence vector to add
        """
        if vector.vector_type == VectorType.ACTION:
            self.action_vectors.append(vector)
        elif vector.vector_type == VectorType.RISK:
            self.risk_vectors.append(vector)
        elif vector.vector_type == VectorType.COHERENCE:
            self.coherence_vectors.append(vector)
        elif vector.vector_type == VectorType.COMPLEXITY:
            self.complexity_vectors.append(vector)

        logger.debug(
            f"Added {vector.vector_type.value} vector {vector.vector_id} "
            f"(magnitude={vector.magnitude:.2f}, priority={vector.priority:.2f})"
        )

    def get_vectors_by_type(self, vector_type: VectorType) -> list[ConvergenceVector]:
        """Get all vectors of a specific type.

        Args:
            vector_type: Type of vectors to retrieve

        Returns:
            List of vectors
        """
        if vector_type == VectorType.ACTION:
            return self.action_vectors
        elif vector_type == VectorType.RISK:
            return self.risk_vectors
        elif vector_type == VectorType.COHERENCE:
            return self.coherence_vectors
        elif vector_type == VectorType.COMPLEXITY:
            return self.complexity_vectors
        return []

    def get_high_priority_vectors(
        self, threshold: float = 0.7
    ) -> list[ConvergenceVector]:
        """Get all high-priority vectors across all types.

        Args:
            threshold: Minimum priority threshold

        Returns:
            List of high-priority vectors
        """
        all_vectors = (
            self.action_vectors
            + self.risk_vectors
            + self.coherence_vectors
            + self.complexity_vectors
        )
        return [v for v in all_vectors if v.priority >= threshold]

    def to_dict(self) -> dict[str, Any]:
        """Convert vector set to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "action_vectors": [self._vector_to_dict(v) for v in self.action_vectors],
            "risk_vectors": [self._vector_to_dict(v) for v in self.risk_vectors],
            "coherence_vectors": [
                self._vector_to_dict(v) for v in self.coherence_vectors
            ],
            "complexity_vectors": [
                self._vector_to_dict(v) for v in self.complexity_vectors
            ],
            "total_vectors": len(self.action_vectors)
            + len(self.risk_vectors)
            + len(self.coherence_vectors)
            + len(self.complexity_vectors),
            "created_at": self.created_at.isoformat(),
        }

    def _vector_to_dict(self, vector: ConvergenceVector) -> dict[str, Any]:
        """Convert a vector to dictionary.

        Args:
            vector: Vector to convert

        Returns:
            Dictionary representation
        """
        return {
            "vector_id": vector.vector_id,
            "vector_type": vector.vector_type.value,
            "magnitude": vector.magnitude,
            "direction": vector.direction,
            "target_phase": vector.target_phase,
            "priority": vector.priority,
            "timestamp": vector.timestamp.isoformat(),
            "metadata": vector.metadata,
        }


class ConvergenceVectorGenerator:
    """Generator for convergence vectors from distributed cognition.

    Transforms distributed cognition into:
    - Action vectors (guide self-healing)
    - Risk vectors (guide prevention)
    - Coherence vectors (guide scalar integration)
    - Complexity vectors (guide adaptive behavior)
    """

    def __init__(self):
        """Initialize convergence vector generator."""
        self.version = "1.0.0"
        self.vector_set = ConvergenceVectorSet()
        self.created_at = datetime.now(UTC)
        logger.info("ConvergenceVectorGenerator initialized")

    def generate_action_vector(
        self,
        vector_id: str,
        magnitude: float,
        direction: dict[str, float],
        target_phase: int | None = None,
        priority: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ConvergenceVector:
        """Generate an action vector for self-healing.

        Args:
            vector_id: Unique vector identifier
            magnitude: Vector magnitude (0.0-1.0)
            direction: Component weights
            target_phase: Target phase (1-12) or None
            priority: Priority level (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Action convergence vector
        """
        vector = ConvergenceVector(
            vector_id=vector_id,
            vector_type=VectorType.ACTION,
            magnitude=magnitude,
            direction=direction,
            target_phase=target_phase,
            priority=priority,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self.vector_set.add_vector(vector)
        logger.info(f"Generated action vector {vector_id} for phase {target_phase}")
        return vector

    def generate_risk_vector(
        self,
        vector_id: str,
        magnitude: float,
        direction: dict[str, float],
        target_phase: int | None = None,
        priority: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ConvergenceVector:
        """Generate a risk vector for prevention.

        Args:
            vector_id: Unique vector identifier
            magnitude: Vector magnitude (0.0-1.0)
            direction: Component weights
            target_phase: Target phase (1-12) or None
            priority: Priority level (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Risk convergence vector
        """
        vector = ConvergenceVector(
            vector_id=vector_id,
            vector_type=VectorType.RISK,
            magnitude=magnitude,
            direction=direction,
            target_phase=target_phase,
            priority=priority,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self.vector_set.add_vector(vector)
        logger.info(f"Generated risk vector {vector_id} for phase {target_phase}")
        return vector

    def generate_coherence_vector(
        self,
        vector_id: str,
        magnitude: float,
        direction: dict[str, float],
        target_phase: int | None = None,
        priority: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ConvergenceVector:
        """Generate a coherence vector for scalar integration.

        Args:
            vector_id: Unique vector identifier
            magnitude: Vector magnitude (0.0-1.0)
            direction: Component weights
            target_phase: Target phase (1-12) or None
            priority: Priority level (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Coherence convergence vector
        """
        vector = ConvergenceVector(
            vector_id=vector_id,
            vector_type=VectorType.COHERENCE,
            magnitude=magnitude,
            direction=direction,
            target_phase=target_phase,
            priority=priority,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self.vector_set.add_vector(vector)
        logger.info(f"Generated coherence vector {vector_id} for phase {target_phase}")
        return vector

    def generate_complexity_vector(
        self,
        vector_id: str,
        magnitude: float,
        direction: dict[str, float],
        target_phase: int | None = None,
        priority: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> ConvergenceVector:
        """Generate a complexity vector for adaptive behavior.

        Args:
            vector_id: Unique vector identifier
            magnitude: Vector magnitude (0.0-1.0)
            direction: Component weights
            target_phase: Target phase (1-12) or None
            priority: Priority level (0.0-1.0)
            metadata: Additional metadata

        Returns:
            Complexity convergence vector
        """
        vector = ConvergenceVector(
            vector_id=vector_id,
            vector_type=VectorType.COMPLEXITY,
            magnitude=magnitude,
            direction=direction,
            target_phase=target_phase,
            priority=priority,
            timestamp=datetime.now(UTC),
            metadata=metadata or {},
        )
        self.vector_set.add_vector(vector)
        logger.info(f"Generated complexity vector {vector_id} for phase {target_phase}")
        return vector

    def generate_vectors_from_cognition(
        self, cognition_data: dict[str, Any]
    ) -> ConvergenceVectorSet:
        """Generate convergence vectors from distributed cognition data.

        Args:
            cognition_data: Distributed cognition data

        Returns:
            Set of convergence vectors
        """
        # Extract action needs
        if "action_needs" in cognition_data:
            for idx, action in enumerate(cognition_data["action_needs"]):
                self.generate_action_vector(
                    vector_id=f"action_{idx}",
                    magnitude=action.get("urgency", 0.5),
                    direction=action.get("components", {}),
                    target_phase=action.get("target_phase"),
                    priority=action.get("priority", 0.5),
                    metadata={"source": "cognition_action_needs"},
                )

        # Extract risk indicators
        if "risk_indicators" in cognition_data:
            for idx, risk in enumerate(cognition_data["risk_indicators"]):
                self.generate_risk_vector(
                    vector_id=f"risk_{idx}",
                    magnitude=risk.get("severity", 0.5),
                    direction=risk.get("components", {}),
                    target_phase=risk.get("target_phase"),
                    priority=risk.get("priority", 0.5),
                    metadata={"source": "cognition_risk_indicators"},
                )

        # Extract coherence issues
        if "coherence_issues" in cognition_data:
            for idx, issue in enumerate(cognition_data["coherence_issues"]):
                self.generate_coherence_vector(
                    vector_id=f"coherence_{idx}",
                    magnitude=issue.get("impact", 0.5),
                    direction=issue.get("components", {}),
                    target_phase=issue.get("target_phase"),
                    priority=issue.get("priority", 0.5),
                    metadata={"source": "cognition_coherence_issues"},
                )

        # Extract complexity metrics
        if "complexity_metrics" in cognition_data:
            for idx, metric in enumerate(cognition_data["complexity_metrics"]):
                self.generate_complexity_vector(
                    vector_id=f"complexity_{idx}",
                    magnitude=metric.get("level", 0.5),
                    direction=metric.get("components", {}),
                    target_phase=metric.get("target_phase"),
                    priority=metric.get("priority", 0.5),
                    metadata={"source": "cognition_complexity_metrics"},
                )

        logger.info(
            f"Generated vectors from cognition: "
            f"{len(self.vector_set.action_vectors)} action, "
            f"{len(self.vector_set.risk_vectors)} risk, "
            f"{len(self.vector_set.coherence_vectors)} coherence, "
            f"{len(self.vector_set.complexity_vectors)} complexity"
        )
        return self.vector_set

    def get_vector_set(self) -> ConvergenceVectorSet:
        """Get the current convergence vector set.

        Returns:
            Current vector set
        """
        return self.vector_set

    def to_dict(self) -> dict[str, Any]:
        """Convert generator to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "vector_set": self.vector_set.to_dict(),
        }
