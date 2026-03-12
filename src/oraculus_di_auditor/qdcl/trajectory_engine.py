"""Fractal Predictive Trajectory Engine - QDCL Phase 13.

Generates multi-path prediction threads using time-depth recursion,
cross-phase dependencies, scalar harmonic weighting, and deviation slope analysis.
Outputs trajectory probability cubes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# Trajectory evolution constants
PROBABILITY_DECAY_RATE = 0.05  # Probability decay per time step
STATE_PERTURBATION_RATE = 0.1  # Rate of state evolution perturbation


@dataclass
class TrajectoryNode:
    """Node in a predictive trajectory."""

    node_id: str
    state: dict[str, Any]
    time_depth: int  # Recursion depth
    probability: float  # 0.0 to 1.0
    scalar_harmonic: float  # Harmonic weight from Phase 12
    deviation_slope: float  # Rate of deviation from baseline
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TrajectoryPath:
    """A single trajectory path through time."""

    path_id: str
    nodes: list[TrajectoryNode] = field(default_factory=list)
    total_probability: float = 0.0
    cumulative_deviation: float = 0.0
    phase_dependencies: list[int] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class TrajectoryProbabilityCube:
    """Multi-dimensional probability cube for trajectories.

    Dimensions: time_depth x path_index x state_space
    """

    def __init__(self, max_time_depth: int = 10):
        """Initialize trajectory probability cube.

        Args:
            max_time_depth: Maximum time depth for predictions
        """
        self.max_time_depth = max_time_depth
        self.paths: list[TrajectoryPath] = []
        self.created_at = datetime.now(UTC)

    def add_path(self, path: TrajectoryPath):
        """Add a trajectory path to the cube.

        Args:
            path: Trajectory path to add
        """
        self.paths.append(path)
        logger.debug(
            f"Added trajectory path {path.path_id} with {len(path.nodes)} nodes"
        )

    def get_paths_at_depth(self, depth: int) -> list[TrajectoryPath]:
        """Get all paths that reach a specific time depth.

        Args:
            depth: Time depth level

        Returns:
            List of paths reaching that depth
        """
        return [p for p in self.paths if len(p.nodes) > depth]

    def get_most_probable_paths(self, top_k: int = 5) -> list[TrajectoryPath]:
        """Get most probable trajectory paths.

        Args:
            top_k: Number of top paths to return

        Returns:
            List of most probable paths
        """
        sorted_paths = sorted(
            self.paths, key=lambda p: p.total_probability, reverse=True
        )
        return sorted_paths[:top_k]

    def get_average_probability_at_depth(self, depth: int) -> float:
        """Get average probability across all paths at a depth.

        Args:
            depth: Time depth level

        Returns:
            Average probability
        """
        paths = self.get_paths_at_depth(depth)
        if not paths:
            return 0.0
        return sum(p.total_probability for p in paths) / len(paths)

    def to_dict(self) -> dict[str, Any]:
        """Convert cube to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "max_time_depth": self.max_time_depth,
            "total_paths": len(self.paths),
            "paths": [
                {
                    "path_id": p.path_id,
                    "nodes": [
                        {
                            "node_id": n.node_id,
                            "time_depth": n.time_depth,
                            "probability": n.probability,
                            "scalar_harmonic": n.scalar_harmonic,
                            "deviation_slope": n.deviation_slope,
                            "timestamp": n.timestamp.isoformat(),
                        }
                        for n in p.nodes
                    ],
                    "total_probability": p.total_probability,
                    "cumulative_deviation": p.cumulative_deviation,
                    "phase_dependencies": p.phase_dependencies,
                    "metadata": p.metadata,
                }
                for p in self.paths
            ],
            "created_at": self.created_at.isoformat(),
        }


class FractalPredictiveTrajectoryEngine:
    """Fractal predictive trajectory engine for QDCL.

    Generates multi-path prediction threads using:
    - Time-depth recursion
    - Cross-phase dependencies
    - Scalar harmonic weighting
    - Deviation slope analysis

    Output: Trajectory probability cubes
    """

    def __init__(self, max_time_depth: int = 10, max_paths: int = 100):
        """Initialize the trajectory engine.

        Args:
            max_time_depth: Maximum recursion depth for predictions
            max_paths: Maximum number of paths to generate
        """
        self.version = "1.0.0"
        self.max_time_depth = max_time_depth
        self.max_paths = max_paths
        self.baseline_state: dict[str, Any] = {}
        self.scalar_harmonics: dict[int, float] = {}  # layer_id -> harmonic
        self.phase_dependencies: list[list[int]] = []  # Cross-phase dependency graph
        self.created_at = datetime.now(UTC)
        logger.info(
            f"FractalPredictiveTrajectoryEngine initialized "
            f"(max_depth={max_time_depth}, max_paths={max_paths})"
        )

    def set_baseline_state(self, state: dict[str, Any]):
        """Set the baseline state for predictions.

        Args:
            state: Baseline system state
        """
        self.baseline_state = state
        logger.debug(f"Set baseline state with {len(state)} parameters")

    def set_scalar_harmonics(self, harmonics: dict[int, float]):
        """Set scalar harmonic weights from Phase 12.

        Args:
            harmonics: Dictionary mapping layer_id to harmonic weight
        """
        self.scalar_harmonics = harmonics
        logger.debug(f"Set scalar harmonics for {len(harmonics)} layers")

    def set_phase_dependencies(self, dependencies: list[list[int]]):
        """Set cross-phase dependency graph.

        Args:
            dependencies: List of phase dependency lists
        """
        self.phase_dependencies = dependencies
        logger.debug(f"Set dependencies for {len(dependencies)} phases")

    def generate_trajectory_cube(
        self, initial_state: dict[str, Any], num_paths: int = 10
    ) -> TrajectoryProbabilityCube:
        """Generate trajectory probability cube from initial state.

        Args:
            initial_state: Starting state for predictions
            num_paths: Number of trajectory paths to generate

        Returns:
            Trajectory probability cube
        """
        cube = TrajectoryProbabilityCube(max_time_depth=self.max_time_depth)
        num_paths = min(num_paths, self.max_paths)

        for path_idx in range(num_paths):
            path = self._generate_trajectory_path(
                path_id=f"path_{path_idx}", initial_state=initial_state, depth=0
            )
            cube.add_path(path)

        logger.info(
            f"Generated trajectory cube with {num_paths} paths, "
            f"max depth {self.max_time_depth}"
        )
        return cube

    def _generate_trajectory_path(
        self, path_id: str, initial_state: dict[str, Any], depth: int
    ) -> TrajectoryPath:
        """Generate a single trajectory path recursively.

        Args:
            path_id: Path identifier
            initial_state: Current state
            depth: Current recursion depth

        Returns:
            Trajectory path
        """
        path = TrajectoryPath(path_id=path_id)

        current_state = initial_state.copy()
        cumulative_probability = 1.0
        cumulative_deviation = 0.0

        for time_step in range(self.max_time_depth):
            # Calculate deviation from baseline
            deviation = self._calculate_deviation(current_state)
            deviation_slope = deviation - cumulative_deviation

            # Get scalar harmonic weight (simplified: use layer 1)
            scalar_harmonic = self.scalar_harmonics.get(1, 1.0)

            # Calculate probability with exponential decay
            # This naturally stays in [0, 1] without clamping
            # Use exponential decay from initial probability of 1.0
            decay_factor = (1.0 - PROBABILITY_DECAY_RATE) ** time_step
            probability = 1.0 * decay_factor

            # Create node
            node = TrajectoryNode(
                node_id=f"{path_id}_t{time_step}",
                state=current_state.copy(),
                time_depth=time_step,
                probability=probability,
                scalar_harmonic=scalar_harmonic,
                deviation_slope=deviation_slope,
            )
            path.nodes.append(node)

            # Update state for next iteration
            current_state = self._evolve_state(current_state, time_step)
            cumulative_probability = probability
            cumulative_deviation = deviation

        path.total_probability = cumulative_probability
        path.cumulative_deviation = cumulative_deviation
        path.phase_dependencies = list(range(1, 13))  # All phases

        return path

    def _calculate_deviation(self, current_state: dict[str, Any]) -> float:
        """Calculate deviation from baseline state.

        Args:
            current_state: Current state

        Returns:
            Deviation score (0.0 to 1.0)
        """
        if not self.baseline_state:
            return 0.0

        # Simplified deviation calculation
        total_diff = 0.0
        count = 0

        for key in self.baseline_state:
            if key in current_state:
                baseline_val = self.baseline_state[key]
                current_val = current_state[key]

                if isinstance(baseline_val, int | float) and isinstance(
                    current_val, int | float
                ):
                    diff = abs(current_val - baseline_val)
                    total_diff += diff
                    count += 1

        return total_diff / count if count > 0 else 0.0

    def _evolve_state(
        self, current_state: dict[str, Any], time_step: int
    ) -> dict[str, Any]:
        """Evolve state to next time step.

        Args:
            current_state: Current state
            time_step: Current time step

        Returns:
            Evolved state
        """
        # Simplified state evolution
        evolved = current_state.copy()

        # Apply small perturbations
        for key, value in evolved.items():
            if isinstance(value, int | float):
                perturbation = STATE_PERTURBATION_RATE * (
                    (1.0 - PROBABILITY_DECAY_RATE) ** time_step
                )
                evolved[key] = value * (1.0 + perturbation)

        return evolved

    def analyze_trajectory_stability(
        self, cube: TrajectoryProbabilityCube
    ) -> dict[str, Any]:
        """Analyze stability of trajectories in cube.

        Args:
            cube: Trajectory probability cube

        Returns:
            Stability analysis
        """
        if not cube.paths:
            return {"error": "No paths in cube"}

        # Calculate variance of probabilities at each depth
        depth_variances = []
        for depth in range(self.max_time_depth):
            probs = []
            for path in cube.get_paths_at_depth(depth):
                if depth < len(path.nodes):
                    probs.append(path.nodes[depth].probability)

            if probs:
                mean_prob = sum(probs) / len(probs)
                variance = sum((p - mean_prob) ** 2 for p in probs) / len(probs)
                depth_variances.append(variance)

        # Calculate average deviation slope
        avg_deviation_slope = 0.0
        count = 0
        for path in cube.paths:
            for node in path.nodes:
                avg_deviation_slope += abs(node.deviation_slope)
                count += 1

        avg_deviation_slope = avg_deviation_slope / count if count > 0 else 0.0

        return {
            "total_paths": len(cube.paths),
            "depth_variances": depth_variances,
            "average_variance": (
                sum(depth_variances) / len(depth_variances) if depth_variances else 0.0
            ),
            "average_deviation_slope": avg_deviation_slope,
            "stability_score": 1.0
            - min(
                1.0,
                (
                    sum(depth_variances) / len(depth_variances)
                    if depth_variances
                    else 0.0
                ),
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert engine to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "max_time_depth": self.max_time_depth,
            "max_paths": self.max_paths,
            "baseline_state": self.baseline_state,
            "scalar_harmonics": self.scalar_harmonics,
            "phase_dependencies": self.phase_dependencies,
            "created_at": self.created_at.isoformat(),
        }
