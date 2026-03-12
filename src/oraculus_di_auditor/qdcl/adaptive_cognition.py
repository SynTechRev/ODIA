"""Adaptive Compression/Expansion Cognition Mode - QDCL Phase 13.

Switches between compression mode (collapse data to vectors) and
expansion mode (explode inputs to full distributed exploration).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CognitionMode(Enum):
    """Cognition processing modes."""

    COMPRESSION = "compression"
    EXPANSION = "expansion"


class AdaptiveCompressionExpansion:
    """Adaptive compression/expansion cognition mode for QDCL.

    Switches between two modes:
    1. Compression mode: Collapse vast system data into small coherent vectors
    2. Expansion mode: Explode small inputs into full distributed exploration
    """

    def __init__(self):
        """Initialize adaptive compression/expansion engine."""
        self.version = "1.0.0"
        self.current_mode = CognitionMode.COMPRESSION
        self.mode_history: list[tuple[CognitionMode, datetime]] = []
        self.compression_ratio = 0.1  # Target ratio for compression
        self.expansion_factor = 10.0  # Target factor for expansion
        self.created_at = datetime.now(UTC)
        logger.info("AdaptiveCompressionExpansion initialized in compression mode")

    def set_mode(self, mode: CognitionMode):
        """Set the cognition mode.

        Args:
            mode: Cognition mode to set
        """
        if mode != self.current_mode:
            self.mode_history.append((self.current_mode, datetime.now(UTC)))
            self.current_mode = mode
            logger.info(f"Switched cognition mode to {mode.value}")

    def compress_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compress vast system data into small coherent vectors.

        Args:
            data: System data to compress

        Returns:
            Compressed vector representation
        """
        self.set_mode(CognitionMode.COMPRESSION)

        # Extract key features
        features = self._extract_key_features(data)

        # Calculate summary statistics
        compressed = {
            "mode": "compression",
            "timestamp": datetime.now(UTC).isoformat(),
            "original_size": self._estimate_size(data),
            "features": features,
            "statistics": self._calculate_statistics(data),
            "compression_ratio": self.compression_ratio,
        }

        logger.info(
            f"Compressed data from {compressed['original_size']} to "
            f"{len(features)} features"
        )
        return compressed

    def expand_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Explode small inputs into full distributed exploration.

        Args:
            input_data: Small input to expand

        Returns:
            Expanded exploration space
        """
        self.set_mode(CognitionMode.EXPANSION)

        # Generate exploration dimensions
        dimensions = self._generate_exploration_dimensions(input_data)

        # Create exploration paths
        paths = self._generate_exploration_paths(input_data, dimensions)

        # Generate hypotheses
        hypotheses = self._generate_hypotheses(input_data)

        expanded = {
            "mode": "expansion",
            "timestamp": datetime.now(UTC).isoformat(),
            "input_size": self._estimate_size(input_data),
            "dimensions": dimensions,
            "paths": paths,
            "hypotheses": hypotheses,
            "expansion_factor": len(paths),
        }

        logger.info(
            f"Expanded input into {len(dimensions)} dimensions "
            f"and {len(paths)} paths"
        )
        return expanded

    def _extract_key_features(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract key features from data.

        Args:
            data: Data to extract features from

        Returns:
            Key features
        """
        features = {}

        # Extract numeric features
        for key, value in data.items():
            if isinstance(value, int | float):
                features[key] = value
            elif isinstance(value, dict):
                # Recursively extract from nested dicts
                nested = self._extract_key_features(value)
                if nested:
                    features[key] = nested
            elif isinstance(value, list) and value:
                # Extract list statistics
                if all(isinstance(x, int | float) for x in value):
                    features[f"{key}_mean"] = sum(value) / len(value)
                    features[f"{key}_count"] = len(value)

        return features

    def _calculate_statistics(self, data: dict[str, Any]) -> dict[str, float]:
        """Calculate summary statistics for data.

        Args:
            data: Data to calculate statistics for

        Returns:
            Summary statistics
        """
        stats = {
            "total_keys": len(data),
            "nested_depth": self._calculate_depth(data),
            "numeric_count": sum(
                1 for v in data.values() if isinstance(v, int | float)
            ),
            "dict_count": sum(1 for v in data.values() if isinstance(v, dict)),
            "list_count": sum(1 for v in data.values() if isinstance(v, list)),
        }
        return stats

    def _calculate_depth(self, data: dict[str, Any], current_depth: int = 1) -> int:
        """Calculate nesting depth of data.

        Args:
            data: Data to calculate depth for
            current_depth: Current depth level

        Returns:
            Maximum nesting depth
        """
        max_depth = current_depth
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
        return max_depth

    def _estimate_size(self, data: dict[str, Any]) -> int:
        """Estimate size of data structure.

        Args:
            data: Data to estimate size for

        Returns:
            Estimated size (number of elements)
        """
        size = len(data)
        for value in data.values():
            if isinstance(value, dict):
                size += self._estimate_size(value)
            elif isinstance(value, list):
                size += len(value)
        return size

    def _generate_exploration_dimensions(self, input_data: dict[str, Any]) -> list[str]:
        """Generate exploration dimensions from input.

        Args:
            input_data: Input to generate dimensions from

        Returns:
            List of exploration dimensions
        """
        dimensions = []

        # Generate dimensions from keys
        for key in input_data.keys():
            dimensions.append(f"dimension_{key}")

        # Add standard exploration dimensions
        dimensions.extend(
            [
                "temporal_dimension",
                "causal_dimension",
                "semantic_dimension",
                "structural_dimension",
            ]
        )

        return dimensions

    def _generate_exploration_paths(
        self, input_data: dict[str, Any], dimensions: list[str]
    ) -> list[dict[str, Any]]:
        """Generate exploration paths through dimensions.

        Args:
            input_data: Input data
            dimensions: Exploration dimensions

        Returns:
            List of exploration paths
        """
        paths = []

        # Generate paths for each dimension
        for idx, dimension in enumerate(dimensions):
            path = {
                "path_id": f"path_{idx}",
                "dimension": dimension,
                "depth": 3,  # Default exploration depth
                "nodes": self._generate_path_nodes(dimension, 3),
            }
            paths.append(path)

        return paths

    def _generate_path_nodes(self, dimension: str, depth: int) -> list[str]:
        """Generate nodes for an exploration path.

        Args:
            dimension: Dimension name
            depth: Path depth

        Returns:
            List of node names
        """
        return [f"{dimension}_node_{i}" for i in range(depth)]

    def _generate_hypotheses(self, input_data: dict[str, Any]) -> list[str]:
        """Generate hypotheses from input data.

        Args:
            input_data: Input data

        Returns:
            List of hypotheses
        """
        hypotheses = []

        # Generate hypotheses for each key
        for key in input_data.keys():
            hypotheses.append(f"hypothesis_{key}_exploration")

        return hypotheses

    def auto_switch_mode(self, data_size: int, complexity: float):
        """Automatically switch mode based on data characteristics.

        Args:
            data_size: Size of input data
            complexity: Complexity measure (0.0-1.0)
        """
        # Switch to compression for large, complex data
        if data_size > 100 and complexity > 0.7:
            self.set_mode(CognitionMode.COMPRESSION)
        # Switch to expansion for small, simple data
        elif data_size < 10 and complexity < 0.3:
            self.set_mode(CognitionMode.EXPANSION)

        logger.debug(
            f"Auto-switched mode based on size={data_size}, "
            f"complexity={complexity:.2f}"
        )

    def get_mode_statistics(self) -> dict[str, Any]:
        """Get statistics about mode usage.

        Returns:
            Mode statistics
        """
        mode_counts = {}
        for mode, _ in self.mode_history:
            mode_counts[mode.value] = mode_counts.get(mode.value, 0) + 1

        return {
            "current_mode": self.current_mode.value,
            "mode_switches": len(self.mode_history),
            "mode_distribution": mode_counts,
            "compression_ratio": self.compression_ratio,
            "expansion_factor": self.expansion_factor,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert engine to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "current_mode": self.current_mode.value,
            "mode_statistics": self.get_mode_statistics(),
        }
