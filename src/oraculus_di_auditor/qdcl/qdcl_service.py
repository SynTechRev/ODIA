"""QDCL Service - Phase 13 Orchestrator.

Orchestrates all QDCL components and generates required outputs per cycle:
1. State-Space Summary
2. Multi-Hypothesis Matrix
3. Distributed Cognition Graph
4. Trajectory Probability Cube
5. Convergence Vector Set
6. Quantum-Kernel Recommendation
7. Traceable Justification Layer
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .adaptive_cognition import AdaptiveCompressionExpansion, CognitionMode
from .mesh_fusion import MeshFusion
from .convergence_vectors import ConvergenceVectorGenerator
from .trajectory_engine import FractalPredictiveTrajectoryEngine
from .grid_memory import GridMemoryOrganizer
from .multi_perspective import MultiPerspectiveEvaluator
from .decision_kernel import KernelDecisionLayer
from .multi_hypothesis import MultiHypothesisEngine

logger = logging.getLogger(__name__)

# Expected number of reasoning keys for complete agent output
EXPECTED_REASONING_KEYS = 5.0


class QDCLService:
    """QDCL Service - Phase 13 orchestrator.

    Quantum-Distributed Cognition Layer that overlays Phases 1-12 as a
    trans-scalar cognitive membrane enabling:
    - Nonlinear reasoning across scales
    - Cross-agent distributed inference
    - Quantum-like superposition of hypothesis states
    - Multi-perspective analysis fusion
    - Predictive trajectory mapping
    - Coherence-resonant decisioning
    - Meta-agent awareness & topological state memory
    """

    def __init__(self):
        """Initialize QDCL Service."""
        self.version = "1.0.0"
        self.phase = 13

        # Initialize all QDCL components
        self.hypothesis_engine = MultiHypothesisEngine()
        self.cognitive_fusion = MeshFusion()
        self.trajectory_engine = FractalPredictiveTrajectoryEngine()
        self.vector_generator = ConvergenceVectorGenerator()
        self.memory_organizer = GridMemoryOrganizer()
        self.multi_perspective = MultiPerspectiveEvaluator()
        self.adaptive_cognition = AdaptiveCompressionExpansion()
        self.decision_layer = KernelDecisionLayer()

        self.created_at = datetime.now(UTC)
        self.cycle_count = 0
        self.execution_history: list[dict[str, Any]] = []

        logger.info("QDCL Service initialized - Phase 13 active")

    def execute_qdcl_cycle(
        self,
        system_state: dict[str, Any],
        agent_outputs: list[dict[str, Any]] | None = None,
        scalar_harmonics: dict[int, float] | None = None,
    ) -> dict[str, Any]:
        """Execute a complete QDCL cycle.

        Args:
            system_state: Current system state from Phases 1-12
            agent_outputs: Outputs from various agents
            scalar_harmonics: Scalar harmonic weights from Phase 12

        Returns:
            Complete QDCL cycle output with all 7 required components
        """
        cycle_start = datetime.now(UTC)
        self.cycle_count += 1

        logger.info(f"Starting QDCL cycle {self.cycle_count}")

        # Determine cognition mode based on input complexity
        data_size = len(str(system_state))
        complexity = self._estimate_complexity(system_state)
        self.adaptive_cognition.auto_switch_mode(data_size, complexity)

        # Process based on mode
        if self.adaptive_cognition.current_mode == CognitionMode.COMPRESSION:
            processed_state = self.adaptive_cognition.compress_data(system_state)
        else:
            processed_state = self.adaptive_cognition.expand_input(system_state)

        # 1. Generate State-Space Summary
        state_space_summary = self._generate_state_space_summary(
            system_state, processed_state
        )

        # 2. Generate Multi-Hypothesis Matrix
        hypothesis_matrix = self._generate_hypothesis_matrix(
            system_state, agent_outputs or []
        )

        # 3. Generate Distributed Cognition Graph
        cognition_graph = self._generate_cognition_graph(agent_outputs or [])

        # 4. Generate Trajectory Probability Cube
        trajectory_cube = self._generate_trajectory_cube(
            system_state, scalar_harmonics or {}
        )

        # 5. Generate Convergence Vector Set
        vector_set = self._generate_convergence_vectors(
            hypothesis_matrix, cognition_graph, trajectory_cube
        )

        # 6. Generate Quantum-Kernel Recommendation
        kernel_recommendation = self._generate_kernel_recommendation(
            hypothesis_matrix,
            cognition_graph,
            state_space_summary,
            trajectory_cube,
            scalar_harmonics or {},
        )

        # 7. Generate Traceable Justification Layer
        justification_layer = self._generate_justification_layer(
            kernel_recommendation, vector_set
        )

        # Update grid memory
        self._update_grid_memory(
            hypothesis_matrix, cognition_graph, trajectory_cube
        )

        cycle_output = {
            "cycle_number": self.cycle_count,
            "timestamp": cycle_start.isoformat(),
            "cognition_mode": self.adaptive_cognition.current_mode.value,
            "outputs": {
                "state_space_summary": state_space_summary,
                "multi_hypothesis_matrix": hypothesis_matrix,
                "distributed_cognition_graph": cognition_graph,
                "trajectory_probability_cube": trajectory_cube,
                "convergence_vector_set": vector_set,
                "decision_kernel_recommendation": kernel_recommendation,
                "traceable_justification_layer": justification_layer,
            },
            "execution_time_ms": (datetime.now(UTC) - cycle_start).total_seconds()
            * 1000,
        }

        self.execution_history.append(cycle_output)

        logger.info(
            f"Completed QDCL cycle {self.cycle_count} in "
            f"{cycle_output['execution_time_ms']:.2f}ms"
        )

        return cycle_output

    def _estimate_complexity(self, data: dict[str, Any]) -> float:
        """Estimate complexity of data.

        Args:
            data: Data to estimate complexity for

        Returns:
            Complexity score (0.0-1.0)
        """
        # Simplified complexity estimation
        size = len(str(data))
        depth = self._calculate_depth(data)
        keys = len(data)

        # Normalize factors
        size_factor = min(size / 10000, 1.0)
        depth_factor = min(depth / 10, 1.0)
        keys_factor = min(keys / 100, 1.0)

        return (size_factor + depth_factor + keys_factor) / 3.0

    def _calculate_depth(self, data: dict[str, Any], current: int = 1) -> int:
        """Calculate nesting depth.

        Args:
            data: Data to calculate depth for
            current: Current depth

        Returns:
            Maximum depth
        """
        max_depth = current
        for value in data.values():
            if isinstance(value, dict):
                depth = self._calculate_depth(value, current + 1)
                max_depth = max(max_depth, depth)
        return max_depth

    def _generate_state_space_summary(
        self, system_state: dict[str, Any], processed_state: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate state-space summary.

        Args:
            system_state: Raw system state
            processed_state: Processed state from adaptive cognition

        Returns:
            State-space summary
        """
        return {
            "raw_state_size": len(str(system_state)),
            "processed_state_size": len(str(processed_state)),
            "processing_mode": processed_state.get("mode", "unknown"),
            "state_dimensions": len(system_state),
            "complexity_score": self._estimate_complexity(system_state),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _generate_hypothesis_matrix(
        self, system_state: dict[str, Any], agent_outputs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate superpositional hypothesis matrix.

        Args:
            system_state: System state
            agent_outputs: Agent outputs

        Returns:
            Hypothesis matrix
        """
        # Create hypotheses from system state and agent outputs
        for idx, output in enumerate(agent_outputs):
            hypothesis = self.hypothesis_engine.create_hypothesis(
                description=f"Agent hypothesis {idx}",
                source_agent=output.get("agent_type", "unknown"),
            )

            # Derive state vectors from agent output confidence and reasoning
            agent_confidence = output.get("confidence", 0.5)
            reasoning = output.get("reasoning", {})

            # Determine state probabilities based on agent output
            # High confidence -> higher probability of normal operation
            normal_prob = min(0.9, max(0.5, agent_confidence))
            anomaly_prob = min(0.4, max(0.1, 1.0 - agent_confidence))
            failure_prob = 0.05  # Explicit minimum failure probability
            # Normalize so that normal_prob + anomaly_prob + failure_prob == 1.0
            total = normal_prob + anomaly_prob
            if total > 0:
                normal_prob = normal_prob / total * (1.0 - failure_prob)
                anomaly_prob = anomaly_prob / total * (1.0 - failure_prob)
            else:
                # If both are zero, assign all probability to failure
                normal_prob = 0.0
                anomaly_prob = 0.0
            # failure_prob remains fixed at 0.05

            # Coherence based on reasoning completeness
            reasoning_completeness = len(reasoning) / EXPECTED_REASONING_KEYS
            base_coherence = min(1.0, reasoning_completeness + 0.5)

            hypothesis.add_state_vector(
                state="normal_operation",
                probability=normal_prob,
                coherence=base_coherence,
            )
            hypothesis.add_state_vector(
                state="anomaly_detected",
                probability=anomaly_prob,
                coherence=base_coherence * 0.8,
            )
            hypothesis.add_state_vector(
                state="failure_predicted",
                probability=failure_prob,
                coherence=base_coherence * 0.6,
            )

        return self.hypothesis_engine.generate_hypothesis_matrix()

    def _generate_cognition_graph(
        self, agent_outputs: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate distributed cognition graph.

        Args:
            agent_outputs: Agent outputs

        Returns:
            Cognition graph
        """
        # Add agent reasoning to cognitive fusion
        for output in agent_outputs:
            self.cognitive_fusion.add_agent_reasoning(
                agent_type=output.get("agent_type", "unknown"),
                agent_id=output.get("agent_id", "unknown"),
                reasoning=output.get("reasoning", {}),
                confidence=output.get("confidence", 0.5),
            )

        return self.cognitive_fusion.generate_distributed_cognition_graph()

    def _generate_trajectory_cube(
        self, system_state: dict[str, Any], scalar_harmonics: dict[int, float]
    ) -> dict[str, Any]:
        """Generate trajectory probability cube.

        Args:
            system_state: System state
            scalar_harmonics: Scalar harmonic weights

        Returns:
            Trajectory cube data
        """
        # Set baseline and harmonics
        self.trajectory_engine.set_baseline_state(system_state)
        self.trajectory_engine.set_scalar_harmonics(scalar_harmonics)

        # Generate trajectory cube
        cube = self.trajectory_engine.generate_trajectory_cube(
            initial_state=system_state, num_paths=10
        )

        # Analyze stability
        stability_analysis = self.trajectory_engine.analyze_trajectory_stability(cube)

        return {
            "cube": cube.to_dict(),
            "stability_analysis": stability_analysis,
        }

    def _generate_convergence_vectors(
        self,
        hypothesis_matrix: dict[str, Any],
        cognition_graph: dict[str, Any],
        trajectory_cube: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate convergence vector set.

        Args:
            hypothesis_matrix: Hypothesis matrix
            cognition_graph: Cognition graph
            trajectory_cube: Trajectory cube

        Returns:
            Convergence vector set
        """
        # Generate vectors from cognition data
        cognition_data = {
            "action_needs": [
                {"urgency": 0.7, "components": {"self_healing": 0.8}, "priority": 0.7}
            ],
            "risk_indicators": [
                {"severity": 0.6, "components": {"security": 0.7}, "priority": 0.6}
            ],
            "coherence_issues": [
                {"impact": 0.5, "components": {"integration": 0.6}, "priority": 0.5}
            ],
            "complexity_metrics": [
                {"level": 0.4, "components": {"orchestration": 0.5}, "priority": 0.4}
            ],
        }

        self.vector_generator.generate_vectors_from_cognition(cognition_data)
        return self.vector_generator.get_vector_set().to_dict()

    def _generate_kernel_recommendation(
        self,
        hypothesis_matrix: dict[str, Any],
        cognition_graph: dict[str, Any],
        state_space_summary: dict[str, Any],
        trajectory_cube: dict[str, Any],
        scalar_harmonics: dict[int, float],
    ) -> dict[str, Any]:
        """Generate quantum-kernel recommendation.

        Args:
            hypothesis_matrix: Hypothesis matrix
            cognition_graph: Cognition graph
            state_space_summary: State summary
            trajectory_cube: Trajectory cube
            scalar_harmonics: Scalar harmonics

        Returns:
            Kernel recommendation
        """
        # Evaluate multi-perspective state
        delta_map = self.multi_perspective.evaluate_all_perspectives(
            state_space_summary
        )

        # Generate decision kernel
        kernel = self.decision_layer.generate_decision_kernel(
            decision="Maintain current system state with monitoring",
            scalar_harmonics=scalar_harmonics,
            hypothesis_data=hypothesis_matrix,
            coherence_data=delta_map.to_dict(),
            consensus_data=cognition_graph.get("summary", {}),
            trajectory_data=trajectory_cube.get("stability_analysis", {}),
        )

        return {
            "kernel_id": kernel.kernel_id,
            "decision": kernel.decision,
            "confidence": kernel.confidence,
            "scores": {
                "scalar_harmonic": kernel.scalar_harmonic_score,
                "hypothesis_resonance": kernel.hypothesis_resonance,
                "coherence": kernel.coherence_score,
                "consensus": kernel.consensus_score,
                "trajectory_stability": kernel.trajectory_stability,
            },
            "justification": kernel.justification,
            "timestamp": kernel.timestamp.isoformat(),
        }

    def _generate_justification_layer(
        self, kernel_recommendation: dict[str, Any], vector_set: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate traceable justification layer.

        Args:
            kernel_recommendation: Kernel recommendation
            vector_set: Convergence vector set

        Returns:
            Justification layer
        """
        return {
            "decision": kernel_recommendation["decision"],
            "confidence": kernel_recommendation["confidence"],
            "justification_chain": kernel_recommendation["justification"],
            "supporting_evidence": {
                "convergence_vectors": {
                    "action_count": len(vector_set.get("action_vectors", [])),
                    "risk_count": len(vector_set.get("risk_vectors", [])),
                    "coherence_count": len(vector_set.get("coherence_vectors", [])),
                    "complexity_count": len(vector_set.get("complexity_vectors", [])),
                },
                "score_breakdown": kernel_recommendation["scores"],
            },
            "traceability": {
                "phase_13_cycle": self.cycle_count,
                "timestamp": datetime.now(UTC).isoformat(),
                "components_consulted": [
                    "hypothesis_engine",
                    "cognitive_fusion",
                    "trajectory_engine",
                    "vector_generator",
                    "multi_perspective",
                    "decision_layer",
                ],
            },
        }

    def _update_grid_memory(
        self,
        hypothesis_matrix: dict[str, Any],
        cognition_graph: dict[str, Any],
        trajectory_cube: dict[str, Any],
    ):
        """Update grid memory with cycle results.

        Args:
            hypothesis_matrix: Hypothesis matrix
            cognition_graph: Cognition graph
            trajectory_cube: Trajectory cube
        """
        # Store insights
        self.memory_organizer.store_insight(
            content={"cycle": self.cycle_count, "type": "hypothesis_generation"},
            magnitude=0.8,
        )

        # Store patterns
        self.memory_organizer.store_micro_pattern(
            content={"pattern": "cognition_fusion", "cycle": self.cycle_count},
            magnitude=0.7,
        )

        # Apply decay
        self.memory_organizer.apply_memory_decay()

    def get_status(self) -> dict[str, Any]:
        """Get current QDCL status.

        Returns:
            Status dictionary
        """
        return {
            "version": self.version,
            "phase": self.phase,
            "cycle_count": self.cycle_count,
            "current_mode": self.adaptive_cognition.current_mode.value,
            "component_status": {
                "hypothesis_engine": len(self.hypothesis_engine.hypotheses),
                "cognitive_fusion": len(self.cognitive_fusion.agent_reasoning),
                "memory_organizer": len(self.memory_organizer.grid.deformations),
                "decision_kernels": len(self.decision_layer.decision_kernels),
            },
            "created_at": self.created_at.isoformat(),
        }

    def get_execution_history(self) -> list[dict[str, Any]]:
        """Get execution history.

        Returns:
            List of cycle outputs
        """
        return self.execution_history

    def to_dict(self) -> dict[str, Any]:
        """Convert service to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "version": self.version,
            "phase": self.phase,
            "cycle_count": self.cycle_count,
            "status": self.get_status(),
            "components": {
                "hypothesis_engine": self.hypothesis_engine.to_dict(),
                "cognitive_fusion": self.cognitive_fusion.to_dict(),
                "trajectory_engine": self.trajectory_engine.to_dict(),
                "vector_generator": self.vector_generator.to_dict(),
                "memory_organizer": self.memory_organizer.to_dict(),
                "multi_perspective": self.multi_perspective.to_dict(),
                "adaptive_cognition": self.adaptive_cognition.to_dict(),
                "decision_layer": self.decision_layer.to_dict(),
            },
        }
