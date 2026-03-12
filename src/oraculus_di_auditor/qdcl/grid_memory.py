"""Grid Memory Organizer - QDCL Phase 13.

Implements a topological memory model where insights, anomalies, transformations,
failures, and micro-patterns are stored as surface deformations in a holographic grid.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory stored in holographic model."""

    INSIGHT = "insight"
    ANOMALY = "anomaly"
    TRANSFORMATION = "transformation"
    FAILURE = "failure"
    MICRO_PATTERN = "micro_pattern"


@dataclass
class SurfaceDeformation:
    """A deformation on the grid memory surface."""

    deformation_id: str
    memory_type: MemoryType
    grid_position: tuple[float, float, float]  # 3D position in grid
    magnitude: float  # Deformation magnitude
    content: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    decay_rate: float = 0.01  # Rate of memory decay
    resonance_score: float = 1.0  # How well it resonates with current state


class HolographicGrid:
    """3D holographic grid for topological memory storage."""

    def __init__(self, grid_size: int = 100):
        """Initialize holographic grid.

        Args:
            grid_size: Size of grid in each dimension
        """
        self.grid_size = grid_size
        self.deformations: dict[str, SurfaceDeformation] = {}
        self.created_at = datetime.now(UTC)

    def add_deformation(self, deformation: SurfaceDeformation):
        """Add a surface deformation to the grid.

        Args:
            deformation: Surface deformation to add
        """
        self.deformations[deformation.deformation_id] = deformation
        logger.debug(
            f"Added {deformation.memory_type.value} deformation at "
            f"position {deformation.grid_position}"
        )

    def get_deformation(self, deformation_id: str) -> SurfaceDeformation | None:
        """Get a deformation by ID.

        Args:
            deformation_id: Deformation identifier

        Returns:
            Deformation or None if not found
        """
        return self.deformations.get(deformation_id)

    def get_deformations_by_type(
        self, memory_type: MemoryType
    ) -> list[SurfaceDeformation]:
        """Get all deformations of a specific type.

        Args:
            memory_type: Type of memory to retrieve

        Returns:
            List of deformations
        """
        return [d for d in self.deformations.values() if d.memory_type == memory_type]

    def get_nearby_deformations(
        self, position: tuple[float, float, float], radius: float
    ) -> list[SurfaceDeformation]:
        """Get deformations within a radius of a position.

        Args:
            position: Center position (x, y, z)
            radius: Search radius

        Returns:
            List of nearby deformations
        """
        nearby = []
        px, py, pz = position

        for deformation in self.deformations.values():
            dx, dy, dz = deformation.grid_position
            distance = ((dx - px) ** 2 + (dy - py) ** 2 + (dz - pz) ** 2) ** 0.5

            if distance <= radius:
                nearby.append(deformation)

        return nearby

    def apply_decay(self):
        """Apply decay to all deformations."""
        for deformation in self.deformations.values():
            deformation.magnitude *= 1.0 - deformation.decay_rate
            deformation.resonance_score *= 1.0 - deformation.decay_rate

        # Remove very weak deformations
        original_count = len(self.deformations)
        self.deformations = {
            d_id: d for d_id, d in self.deformations.items() if d.magnitude >= 0.01
        }
        removed_count = original_count - len(self.deformations)

        if removed_count:
            logger.debug(f"Removed {removed_count} decayed deformations")

    def to_dict(self) -> dict[str, Any]:
        """Convert grid to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "grid_size": self.grid_size,
            "total_deformations": len(self.deformations),
            "deformations": [
                {
                    "deformation_id": d.deformation_id,
                    "memory_type": d.memory_type.value,
                    "grid_position": list(d.grid_position),
                    "magnitude": d.magnitude,
                    "content": d.content,
                    "timestamp": d.timestamp.isoformat(),
                    "decay_rate": d.decay_rate,
                    "resonance_score": d.resonance_score,
                }
                for d in self.deformations.values()
            ],
            "created_at": self.created_at.isoformat(),
        }


class GridMemoryOrganizer:
    """Holographic memory organizer for QDCL.

    Implements a topological memory model where insights, anomalies,
    transformations, failures, and micro-patterns are stored as surface
    deformations in a holographic grid.
    """

    def __init__(self, grid_size: int = 100):
        """Initialize grid memory organizer.

        Args:
            grid_size: Size of holographic grid
        """
        self.version = "1.0.0"
        self.grid = HolographicGrid(grid_size=grid_size)
        self.memory_counter = 0
        self.created_at = datetime.now(UTC)
        logger.info(f"GridMemoryOrganizer initialized with grid size {grid_size}")

    def store_insight(
        self, content: dict[str, Any], magnitude: float = 1.0
    ) -> SurfaceDeformation:
        """Store an insight in grid memory.

        Args:
            content: Insight content
            magnitude: Magnitude of insight

        Returns:
            Surface deformation
        """
        position = self._calculate_position(content, MemoryType.INSIGHT)
        deformation = SurfaceDeformation(
            deformation_id=f"insight_{self.memory_counter}",
            memory_type=MemoryType.INSIGHT,
            grid_position=position,
            magnitude=magnitude,
            content=content,
        )
        self.grid.add_deformation(deformation)
        self.memory_counter += 1
        logger.info(f"Stored insight at position {position}")
        return deformation

    def store_anomaly(
        self, content: dict[str, Any], magnitude: float = 1.0
    ) -> SurfaceDeformation:
        """Store an anomaly in grid memory.

        Args:
            content: Anomaly content
            magnitude: Magnitude of anomaly

        Returns:
            Surface deformation
        """
        position = self._calculate_position(content, MemoryType.ANOMALY)
        deformation = SurfaceDeformation(
            deformation_id=f"anomaly_{self.memory_counter}",
            memory_type=MemoryType.ANOMALY,
            grid_position=position,
            magnitude=magnitude,
            content=content,
        )
        self.grid.add_deformation(deformation)
        self.memory_counter += 1
        logger.info(f"Stored anomaly at position {position}")
        return deformation

    def store_transformation(
        self, content: dict[str, Any], magnitude: float = 1.0
    ) -> SurfaceDeformation:
        """Store a transformation in grid memory.

        Args:
            content: Transformation content
            magnitude: Magnitude of transformation

        Returns:
            Surface deformation
        """
        position = self._calculate_position(content, MemoryType.TRANSFORMATION)
        deformation = SurfaceDeformation(
            deformation_id=f"transformation_{self.memory_counter}",
            memory_type=MemoryType.TRANSFORMATION,
            grid_position=position,
            magnitude=magnitude,
            content=content,
        )
        self.grid.add_deformation(deformation)
        self.memory_counter += 1
        logger.info(f"Stored transformation at position {position}")
        return deformation

    def store_failure(
        self, content: dict[str, Any], magnitude: float = 1.0
    ) -> SurfaceDeformation:
        """Store a failure in grid memory.

        Args:
            content: Failure content
            magnitude: Magnitude of failure

        Returns:
            Surface deformation
        """
        position = self._calculate_position(content, MemoryType.FAILURE)
        deformation = SurfaceDeformation(
            deformation_id=f"failure_{self.memory_counter}",
            memory_type=MemoryType.FAILURE,
            grid_position=position,
            magnitude=magnitude,
            content=content,
        )
        self.grid.add_deformation(deformation)
        self.memory_counter += 1
        logger.info(f"Stored failure at position {position}")
        return deformation

    def store_micro_pattern(
        self, content: dict[str, Any], magnitude: float = 1.0
    ) -> SurfaceDeformation:
        """Store a micro-pattern in grid memory.

        Args:
            content: Micro-pattern content
            magnitude: Magnitude of pattern

        Returns:
            Surface deformation
        """
        position = self._calculate_position(content, MemoryType.MICRO_PATTERN)
        deformation = SurfaceDeformation(
            deformation_id=f"pattern_{self.memory_counter}",
            memory_type=MemoryType.MICRO_PATTERN,
            grid_position=position,
            magnitude=magnitude,
            content=content,
        )
        self.grid.add_deformation(deformation)
        self.memory_counter += 1
        logger.info(f"Stored micro-pattern at position {position}")
        return deformation

    def _calculate_position(
        self, content: dict[str, Any], memory_type: MemoryType
    ) -> tuple[float, float, float]:
        """Calculate grid position for content using deterministic hashing.

        Args:
            content: Content to position
            memory_type: Type of memory

        Returns:
            3D position in grid
        """
        # Use deterministic hashing with hashlib
        content_str = str(sorted(content.items()))
        hash_obj = hashlib.sha256(content_str.encode())
        hash_bytes = hash_obj.digest()

        # Convert first 8 bytes to integers for coordinates
        x_bytes = int.from_bytes(hash_bytes[0:8], byteorder="big")
        y_bytes = int.from_bytes(hash_bytes[8:16], byteorder="big")

        # Hash memory type separately
        type_hash = hashlib.sha256(memory_type.value.encode()).digest()
        z_bytes = int.from_bytes(type_hash[0:8], byteorder="big")

        # Map to grid coordinates (0.0 to 1.0)
        x = (x_bytes % self.grid.grid_size) / self.grid.grid_size
        y = (y_bytes % self.grid.grid_size) / self.grid.grid_size
        z = (z_bytes % self.grid.grid_size) / self.grid.grid_size

        return (x, y, z)

    def recall_similar_memories(
        self,
        query_content: dict[str, Any],
        memory_type: MemoryType,
        radius: float = 0.1,
    ) -> list[SurfaceDeformation]:
        """Recall memories similar to query content.

        Args:
            query_content: Query content
            memory_type: Type of memory to recall
            radius: Search radius

        Returns:
            List of similar memories
        """
        query_position = self._calculate_position(query_content, memory_type)
        nearby = self.grid.get_nearby_deformations(query_position, radius)

        # Filter by type and sort by resonance
        filtered = [d for d in nearby if d.memory_type == memory_type]
        filtered.sort(key=lambda d: d.resonance_score, reverse=True)

        logger.info(
            f"Recalled {len(filtered)} {memory_type.value} memories "
            f"within radius {radius}"
        )
        return filtered

    def update_resonance(self, current_state: dict[str, Any]):
        """Update resonance scores based on current system state.

        Args:
            current_state: Current system state
        """
        # Simplified resonance update
        for deformation in self.grid.deformations.values():
            # Calculate similarity to current state
            similarity = self._calculate_similarity(deformation.content, current_state)
            deformation.resonance_score = similarity

        logger.debug("Updated resonance scores for all deformations")

    def _calculate_similarity(
        self, content1: dict[str, Any], content2: dict[str, Any]
    ) -> float:
        """Calculate similarity between two content dictionaries.

        Args:
            content1: First content
            content2: Second content

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simplified Jaccard similarity
        keys1 = set(content1.keys())
        keys2 = set(content2.keys())

        if not keys1 and not keys2:
            return 1.0
        if not keys1 or not keys2:
            return 0.0

        intersection = len(keys1 & keys2)
        union = len(keys1 | keys2)

        return intersection / union if union > 0 else 0.0

    def apply_memory_decay(self):
        """Apply decay to all memories."""
        self.grid.apply_decay()
        logger.info("Applied memory decay to holographic grid")

    def get_memory_summary(self) -> dict[str, Any]:
        """Get summary of grid memory state.

        Returns:
            Memory summary
        """
        type_counts = {}
        for memory_type in MemoryType:
            count = len(self.grid.get_deformations_by_type(memory_type))
            type_counts[memory_type.value] = count

        return {
            "total_memories": len(self.grid.deformations),
            "memory_type_distribution": type_counts,
            "grid_size": self.grid.grid_size,
            "average_magnitude": (
                sum(d.magnitude for d in self.grid.deformations.values())
                / len(self.grid.deformations)
                if self.grid.deformations
                else 0.0
            ),
            "average_resonance": (
                sum(d.resonance_score for d in self.grid.deformations.values())
                / len(self.grid.deformations)
                if self.grid.deformations
                else 0.0
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert organizer to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "grid": self.grid.to_dict(),
            "memory_summary": self.get_memory_summary(),
        }
