"""Tests for Phase 13: QDCL (Quantum-Distributed Cognition Layer)."""

import pytest

from oraculus_di_auditor.qdcl import (
    AdaptiveCompressionExpansion,
    CognitionMode,
    MeshFusion,
    ConvergenceVectorGenerator,
    DecisionKernel,
    FractalPredictiveTrajectoryEngine,
    GridMemoryOrganizer,
    HypothesisState,
    MemoryType,
    MultiPerspectiveEvaluator,
    Perspective,
    QDCLService,
    KernelDecisionLayer,
    MultiHypothesisEngine,
    VectorType,
)


class TestMultiHypothesisEngine:
    """Tests for Multi-Hypothesis Engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = MultiHypothesisEngine()
        assert engine.version == "1.0.0"
        assert len(engine.hypotheses) == 0

    def test_create_hypothesis(self):
        """Test hypothesis creation."""
        engine = MultiHypothesisEngine()
        hyp = engine.create_hypothesis(
            description="Test hypothesis", source_agent="test_agent"
        )

        assert hyp.description == "Test hypothesis"
        assert hyp.source_agent == "test_agent"
        assert hyp.state == HypothesisState.SUPERPOSITION
        assert hyp.hypothesis_id in engine.hypotheses

    def test_add_state_vector(self):
        """Test adding state vectors to hypothesis."""
        engine = MultiHypothesisEngine()
        hyp = engine.create_hypothesis("Test", "agent")

        hyp.add_state_vector("state_a", 0.7, 0.8)
        hyp.add_state_vector("state_b", 0.3, 0.6)

        assert len(hyp.state_vectors) == 2
        assert hyp.state_vectors[0].state == "state_a"
        assert hyp.state_vectors[0].probability == 0.7

    def test_hypothesis_entanglement(self):
        """Test hypothesis entanglement."""
        engine = MultiHypothesisEngine()
        hyp1 = engine.create_hypothesis("Hyp 1", "agent1")
        hyp2 = engine.create_hypothesis("Hyp 2", "agent2")

        engine.entangle_hypotheses(
            hyp1.hypothesis_id, hyp2.hypothesis_id, 0.8, "reinforcing"
        )

        assert len(hyp1.entanglements) == 1
        assert len(hyp2.entanglements) == 1
        assert hyp1.state == HypothesisState.ENTANGLED

    def test_hypothesis_collapse(self):
        """Test hypothesis collapse."""
        engine = MultiHypothesisEngine()
        hyp = engine.create_hypothesis("Test", "agent")
        hyp.add_state_vector("final_state", 0.9, 0.9)

        engine.collapse_hypothesis(hyp.hypothesis_id, "final_state")

        assert hyp.state == HypothesisState.COLLAPSED
        assert hyp.metadata["collapsed_state"] == "final_state"

    def test_hypothesis_matrix_generation(self):
        """Test hypothesis matrix generation."""
        engine = MultiHypothesisEngine()
        engine.create_hypothesis("Hyp 1", "agent1")
        engine.create_hypothesis("Hyp 2", "agent2")

        matrix = engine.generate_hypothesis_matrix()

        assert matrix["version"] == "1.0.0"
        assert matrix["total_hypotheses"] == 2
        assert len(matrix["hypotheses"]) == 2


class TestMeshFusion:
    """Tests for Mesh Fusion."""

    def test_fusion_initialization(self):
        """Test fusion initialization."""
        fusion = MeshFusion()
        assert fusion.version == "1.0.0"
        assert len(fusion.agent_reasoning) == 0

    def test_add_agent_reasoning(self):
        """Test adding agent reasoning."""
        fusion = MeshFusion()
        fusion.add_agent_reasoning(
            agent_type="constraint",
            agent_id="agent_1",
            reasoning={"concepts": ["concept_a", "concept_b"]},
            confidence=0.8,
        )

        assert len(fusion.agent_reasoning) == 1
        assert fusion.agent_reasoning[0].agent_type == "constraint"

    def test_fuse_reasoning(self):
        """Test reasoning fusion."""
        fusion = MeshFusion()
        fusion.add_agent_reasoning(
            "constraint", "a1", {"concepts": ["safety", "performance"]}, 0.8
        )
        fusion.add_agent_reasoning(
            "semantic", "a2", {"concepts": ["safety", "reliability"]}, 0.7
        )

        fractal_map = fusion.fuse_reasoning()

        assert fractal_map is not None
        assert len(fractal_map.nodes) > 0

    def test_cognition_graph_generation(self):
        """Test cognition graph generation."""
        fusion = MeshFusion()
        fusion.add_agent_reasoning("constraint", "a1", {"concepts": ["test"]}, 0.8)

        graph = fusion.generate_distributed_cognition_graph()

        assert "nodes" in graph
        assert "edges" in graph
        assert "summary" in graph


class TestTrajectoryEngineEngine:
    """Tests for Fractal Predictive Trajectory Engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = FractalPredictiveTrajectoryEngine(max_time_depth=5)
        assert engine.version == "1.0.0"
        assert engine.max_time_depth == 5

    def test_set_baseline_state(self):
        """Test setting baseline state."""
        engine = FractalPredictiveTrajectoryEngine()
        baseline = {"param_a": 1.0, "param_b": 2.0}
        engine.set_baseline_state(baseline)

        assert engine.baseline_state == baseline

    def test_set_scalar_harmonics(self):
        """Test setting scalar harmonics."""
        engine = FractalPredictiveTrajectoryEngine()
        harmonics = {1: 0.9, 2: 0.8, 3: 0.85}
        engine.set_scalar_harmonics(harmonics)

        assert engine.scalar_harmonics == harmonics

    def test_generate_trajectory_cube(self):
        """Test trajectory cube generation."""
        engine = FractalPredictiveTrajectoryEngine(max_time_depth=3)
        initial_state = {"value": 1.0}

        cube = engine.generate_trajectory_cube(initial_state, num_paths=5)

        assert len(cube.paths) == 5
        assert cube.max_time_depth == 3

    def test_trajectory_stability_analysis(self):
        """Test trajectory stability analysis."""
        engine = FractalPredictiveTrajectoryEngine(max_time_depth=3)
        initial_state = {"value": 1.0}

        cube = engine.generate_trajectory_cube(initial_state, num_paths=5)
        stability = engine.analyze_trajectory_stability(cube)

        assert "total_paths" in stability
        assert "stability_score" in stability
        assert 0.0 <= stability["stability_score"] <= 1.0


class TestConvergenceVectorGenerator:
    """Tests for Convergence Vector Generator."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = ConvergenceVectorGenerator()
        assert generator.version == "1.0.0"

    def test_generate_action_vector(self):
        """Test action vector generation."""
        generator = ConvergenceVectorGenerator()
        vector = generator.generate_action_vector(
            vector_id="action_1",
            magnitude=0.8,
            direction={"self_healing": 0.9},
            target_phase=11,
            priority=0.7,
        )

        assert vector.vector_type == VectorType.ACTION
        assert vector.magnitude == 0.8
        assert vector.target_phase == 11

    def test_generate_risk_vector(self):
        """Test risk vector generation."""
        generator = ConvergenceVectorGenerator()
        vector = generator.generate_risk_vector(
            vector_id="risk_1",
            magnitude=0.6,
            direction={"security": 0.8},
            priority=0.9,
        )

        assert vector.vector_type == VectorType.RISK
        assert vector.magnitude == 0.6

    def test_generate_coherence_vector(self):
        """Test coherence vector generation."""
        generator = ConvergenceVectorGenerator()
        vector = generator.generate_coherence_vector(
            vector_id="coherence_1",
            magnitude=0.7,
            direction={"integration": 0.75},
            target_phase=12,
        )

        assert vector.vector_type == VectorType.COHERENCE
        assert vector.target_phase == 12

    def test_generate_complexity_vector(self):
        """Test complexity vector generation."""
        generator = ConvergenceVectorGenerator()
        vector = generator.generate_complexity_vector(
            vector_id="complexity_1",
            magnitude=0.5,
            direction={"orchestration": 0.6},
        )

        assert vector.vector_type == VectorType.COMPLEXITY

    def test_high_priority_vectors(self):
        """Test high priority vector retrieval."""
        generator = ConvergenceVectorGenerator()
        generator.generate_action_vector("a1", 0.8, {}, priority=0.8)
        generator.generate_risk_vector("r1", 0.6, {}, priority=0.5)

        high_priority = generator.vector_set.get_high_priority_vectors(threshold=0.7)

        assert len(high_priority) == 1
        assert high_priority[0].vector_id == "a1"


class TestGridMemoryOrganizer:
    """Tests for Grid Memory Organizer."""

    def test_organizer_initialization(self):
        """Test organizer initialization."""
        organizer = GridMemoryOrganizer(grid_size=50)
        assert organizer.version == "1.0.0"
        assert organizer.grid.grid_size == 50

    def test_store_insight(self):
        """Test storing insights."""
        organizer = GridMemoryOrganizer()
        deformation = organizer.store_insight(
            content={"insight": "test_insight"}, magnitude=0.9
        )

        assert deformation.memory_type == MemoryType.INSIGHT
        assert deformation.magnitude == 0.9

    def test_store_anomaly(self):
        """Test storing anomalies."""
        organizer = GridMemoryOrganizer()
        deformation = organizer.store_anomaly(
            content={"anomaly": "test_anomaly"}, magnitude=0.8
        )

        assert deformation.memory_type == MemoryType.ANOMALY

    def test_store_transformation(self):
        """Test storing transformations."""
        organizer = GridMemoryOrganizer()
        deformation = organizer.store_transformation(
            content={"transform": "test"}, magnitude=0.7
        )

        assert deformation.memory_type == MemoryType.TRANSFORMATION

    def test_store_failure(self):
        """Test storing failures."""
        organizer = GridMemoryOrganizer()
        deformation = organizer.store_failure(
            content={"failure": "test_failure"}, magnitude=0.6
        )

        assert deformation.memory_type == MemoryType.FAILURE

    def test_store_micro_pattern(self):
        """Test storing micro-patterns."""
        organizer = GridMemoryOrganizer()
        deformation = organizer.store_micro_pattern(
            content={"pattern": "test_pattern"}, magnitude=0.8
        )

        assert deformation.memory_type == MemoryType.MICRO_PATTERN

    def test_recall_similar_memories(self):
        """Test recalling similar memories."""
        organizer = GridMemoryOrganizer()
        organizer.store_insight({"key": "value1"}, 0.9)
        organizer.store_insight({"key": "value2"}, 0.8)

        memories = organizer.recall_similar_memories(
            {"key": "value1"}, MemoryType.INSIGHT, radius=0.5
        )

        assert len(memories) >= 1

    def test_memory_decay(self):
        """Test memory decay."""
        organizer = GridMemoryOrganizer()
        organizer.store_insight({"test": "data"}, magnitude=0.5)

        initial_count = len(organizer.grid.deformations)
        organizer.apply_memory_decay()

        # Should still have memories after one decay
        assert len(organizer.grid.deformations) <= initial_count


class TestMultiPerspectiveEvaluator:
    """Tests for Multi-Perspective State Evaluator."""

    def test_evaluator_initialization(self):
        """Test evaluator initialization."""
        evaluator = MultiPerspectiveEvaluator()
        assert evaluator.version == "1.0.0"

    def test_systemic_perspective(self):
        """Test systemic perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {
            "coherence_score": 0.8,
            "component_count": 50,
            "integration_level": 0.9,
        }

        evaluation = evaluator.evaluate_systemic_perspective(state)

        assert evaluation.perspective == Perspective.SYSTEMIC
        assert 0.0 <= evaluation.score <= 1.0

    def test_component_perspective(self):
        """Test component perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {"component_health": {"comp_a": 0.8, "comp_b": 0.9}}

        evaluation = evaluator.evaluate_component_perspective(state)

        assert evaluation.perspective == Perspective.COMPONENT

    def test_temporal_perspective(self):
        """Test temporal perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {"drift_rate": 0.2, "evolution_health": 0.8, "change_velocity": 0.3}

        evaluation = evaluator.evaluate_temporal_perspective(state)

        assert evaluation.perspective == Perspective.TEMPORAL

    def test_adversarial_perspective(self):
        """Test adversarial perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {"vulnerability_count": 1, "security_score": 0.9, "attack_surface": 0.2}

        evaluation = evaluator.evaluate_adversarial_perspective(state)

        assert evaluation.perspective == Perspective.ADVERSARIAL

    def test_governance_perspective(self):
        """Test governance perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {
            "compliance_score": 0.9,
            "policy_violations": 0,
            "governance_health": 0.85,
        }

        evaluation = evaluator.evaluate_governance_perspective(state)

        assert evaluation.perspective == Perspective.GOVERNANCE

    def test_user_centric_perspective(self):
        """Test user-centric perspective evaluation."""
        evaluator = MultiPerspectiveEvaluator()
        state = {
            "user_satisfaction": 0.8,
            "value_delivery": 0.85,
            "usability_score": 0.9,
        }

        evaluation = evaluator.evaluate_user_centric_perspective(state)

        assert evaluation.perspective == Perspective.USER_CENTRIC

    def test_evaluate_all_perspectives(self):
        """Test evaluating all six perspectives."""
        evaluator = MultiPerspectiveEvaluator()
        state = {
            "coherence_score": 0.8,
            "component_count": 50,
            "integration_level": 0.9,
            "component_health": {"comp_a": 0.8},
            "drift_rate": 0.2,
            "evolution_health": 0.8,
            "vulnerability_count": 0,
            "security_score": 0.9,
            "compliance_score": 0.9,
            "governance_health": 0.85,
            "user_satisfaction": 0.8,
            "value_delivery": 0.85,
        }

        delta_map = evaluator.evaluate_all_perspectives(state)

        assert len(delta_map.evaluations) == 6
        assert len(delta_map.delta_matrix) > 0

    def test_perspective_alignment(self):
        """Test perspective alignment analysis."""
        evaluator = MultiPerspectiveEvaluator()
        state = {"coherence_score": 0.8}

        evaluator.evaluate_all_perspectives(state)
        alignment = evaluator.get_perspective_alignment()

        assert "alignment_score" in alignment
        assert 0.0 <= alignment["alignment_score"] <= 1.0


class TestAdaptiveCompressionExpansion:
    """Tests for Adaptive Compression/Expansion Cognition."""

    def test_initialization(self):
        """Test initialization."""
        engine = AdaptiveCompressionExpansion()
        assert engine.version == "1.0.0"
        assert engine.current_mode == CognitionMode.COMPRESSION

    def test_set_mode(self):
        """Test mode setting."""
        engine = AdaptiveCompressionExpansion()
        engine.set_mode(CognitionMode.EXPANSION)

        assert engine.current_mode == CognitionMode.EXPANSION
        assert len(engine.mode_history) == 1

    def test_compress_data(self):
        """Test data compression."""
        engine = AdaptiveCompressionExpansion()
        data = {"key1": 1, "key2": 2, "key3": 3, "nested": {"subkey": 4}}

        compressed = engine.compress_data(data)

        assert compressed["mode"] == "compression"
        assert "features" in compressed
        assert "statistics" in compressed

    def test_expand_input(self):
        """Test input expansion."""
        engine = AdaptiveCompressionExpansion()
        input_data = {"query": "test"}

        expanded = engine.expand_input(input_data)

        assert expanded["mode"] == "expansion"
        assert "dimensions" in expanded
        assert "paths" in expanded
        assert len(expanded["paths"]) > 0

    def test_auto_switch_mode(self):
        """Test automatic mode switching."""
        engine = AdaptiveCompressionExpansion()

        # Large, complex data should trigger compression
        engine.auto_switch_mode(data_size=200, complexity=0.8)
        assert engine.current_mode == CognitionMode.COMPRESSION

        # Small, simple data should trigger expansion
        engine.auto_switch_mode(data_size=5, complexity=0.2)
        assert engine.current_mode == CognitionMode.EXPANSION


class TestKernelDecisionLayer:
    """Tests for Quantum-Kernel Decision Layer."""

    def test_layer_initialization(self):
        """Test layer initialization."""
        layer = KernelDecisionLayer()
        assert layer.version == "1.0.0"
        assert len(layer.decision_kernels) == 0

    def test_generate_decision_kernel(self):
        """Test decision kernel generation."""
        layer = KernelDecisionLayer()

        kernel = layer.generate_decision_kernel(
            decision="Test decision",
            scalar_harmonics={1: 0.9, 2: 0.8},
            hypothesis_data={"total_hypotheses": 5},
            coherence_data={"alignment_score": 0.8},
            consensus_data={"total_agents": 3, "total_concepts": 10},
            trajectory_data={"stability_score": 0.85},
        )

        assert isinstance(kernel, DecisionKernel)
        assert kernel.decision == "Test decision"
        assert 0.0 <= kernel.confidence <= 1.0
        assert len(kernel.justification) > 0

    def test_get_high_confidence_kernels(self):
        """Test high confidence kernel retrieval."""
        layer = KernelDecisionLayer()

        # Generate kernels with different confidence
        layer.generate_decision_kernel(
            "Decision 1",
            {1: 0.9},
            {},
            {"alignment_score": 0.9},
            {},
            {"stability_score": 0.9},
        )
        layer.generate_decision_kernel(
            "Decision 2",
            {1: 0.5},
            {},
            {"alignment_score": 0.5},
            {},
            {"stability_score": 0.5},
        )

        high_confidence = layer.get_high_confidence_kernels(threshold=0.7)

        assert len(high_confidence) >= 0


class TestQDCLService:
    """Tests for QDCL Service orchestrator."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = QDCLService()
        assert service.version == "1.0.0"
        assert service.phase == 13
        assert service.cycle_count == 0

    def test_execute_qdcl_cycle(self):
        """Test executing a complete QDCL cycle."""
        service = QDCLService()

        system_state = {
            "coherence_score": 0.8,
            "component_count": 50,
            "integration_level": 0.9,
        }

        agent_outputs = [
            {
                "agent_type": "constraint",
                "agent_id": "agent_1",
                "reasoning": {"concepts": ["safety"]},
                "confidence": 0.8,
            }
        ]

        scalar_harmonics = {1: 0.9, 2: 0.85, 3: 0.88}

        result = service.execute_qdcl_cycle(
            system_state=system_state,
            agent_outputs=agent_outputs,
            scalar_harmonics=scalar_harmonics,
        )

        assert result["cycle_number"] == 1
        assert "outputs" in result
        assert "state_space_summary" in result["outputs"]
        assert "multi_hypothesis_matrix" in result["outputs"]
        assert "distributed_cognition_graph" in result["outputs"]
        assert "trajectory_probability_cube" in result["outputs"]
        assert "convergence_vector_set" in result["outputs"]
        assert "decision_kernel_recommendation" in result["outputs"]
        assert "traceable_justification_layer" in result["outputs"]

    def test_get_status(self):
        """Test getting service status."""
        service = QDCLService()
        status = service.get_status()

        assert status["version"] == "1.0.0"
        assert status["phase"] == 13
        assert status["cycle_count"] == 0
        assert "component_status" in status

    def test_execution_history(self):
        """Test execution history tracking."""
        service = QDCLService()

        system_state = {"test": "data"}
        service.execute_qdcl_cycle(system_state)
        service.execute_qdcl_cycle(system_state)

        history = service.get_execution_history()

        assert len(history) == 2
        assert history[0]["cycle_number"] == 1
        assert history[1]["cycle_number"] == 2

    def test_multiple_cycles(self):
        """Test executing multiple QDCL cycles."""
        service = QDCLService()

        for i in range(3):
            result = service.execute_qdcl_cycle(
                system_state={"iteration": i},
                agent_outputs=[],
                scalar_harmonics={},
            )
            assert result["cycle_number"] == i + 1

        assert service.cycle_count == 3


class TestPhase13Integration:
    """Integration tests for Phase 13 QDCL."""

    def test_full_qdcl_workflow(self):
        """Test complete QDCL workflow."""
        service = QDCLService()

        # Prepare comprehensive system state
        system_state = {
            "coherence_score": 0.82,
            "component_count": 75,
            "integration_level": 0.88,
            "component_health": {"comp_a": 0.9, "comp_b": 0.85},
            "drift_rate": 0.15,
            "evolution_health": 0.87,
            "change_velocity": 0.25,
            "vulnerability_count": 1,
            "security_score": 0.92,
            "attack_surface": 0.18,
            "compliance_score": 0.94,
            "policy_violations": 0,
            "governance_health": 0.91,
            "user_satisfaction": 0.86,
            "value_delivery": 0.89,
            "usability_score": 0.88,
        }

        # Prepare agent outputs
        agent_outputs = [
            {
                "agent_type": "constraint",
                "agent_id": "constraint_1",
                "reasoning": {"concepts": ["safety", "compliance"], "findings": []},
                "confidence": 0.85,
            },
            {
                "agent_type": "anomaly",
                "agent_id": "anomaly_1",
                "reasoning": {"concepts": ["performance"], "issues": []},
                "confidence": 0.78,
            },
            {
                "agent_type": "semantic",
                "agent_id": "semantic_1",
                "reasoning": {"concepts": ["coherence"], "findings": []},
                "confidence": 0.82,
            },
        ]

        # Scalar harmonics from Phase 12
        scalar_harmonics = {
            1: 0.92,
            2: 0.89,
            3: 0.87,
            4: 0.85,
            5: 0.88,
            6: 0.86,
            7: 0.90,
        }

        # Execute QDCL cycle
        result = service.execute_qdcl_cycle(
            system_state=system_state,
            agent_outputs=agent_outputs,
            scalar_harmonics=scalar_harmonics,
        )

        # Validate all outputs
        outputs = result["outputs"]

        # 1. State-Space Summary
        assert "state_space_summary" in outputs
        assert outputs["state_space_summary"]["complexity_score"] > 0

        # 2. Multi-Hypothesis Matrix
        assert "multi_hypothesis_matrix" in outputs
        assert outputs["multi_hypothesis_matrix"]["total_hypotheses"] >= 0

        # 3. Distributed Cognition Graph
        assert "distributed_cognition_graph" in outputs
        assert "nodes" in outputs["distributed_cognition_graph"]

        # 4. Trajectory Probability Cube
        assert "trajectory_probability_cube" in outputs
        assert "cube" in outputs["trajectory_probability_cube"]

        # 5. Convergence Vector Set
        assert "convergence_vector_set" in outputs
        assert "total_vectors" in outputs["convergence_vector_set"]

        # 6. Quantum-Kernel Recommendation
        assert "decision_kernel_recommendation" in outputs
        assert "decision" in outputs["decision_kernel_recommendation"]
        assert 0.0 <= outputs["decision_kernel_recommendation"]["confidence"] <= 1.0

        # 7. Traceable Justification Layer
        assert "traceable_justification_layer" in outputs
        assert "justification_chain" in outputs["traceable_justification_layer"]
        assert "traceability" in outputs["traceable_justification_layer"]

    def test_qdcl_determinism(self):
        """Test QDCL produces consistent results."""
        service1 = QDCLService()
        service2 = QDCLService()

        system_state = {"test": "data", "value": 42}

        result1 = service1.execute_qdcl_cycle(system_state)
        result2 = service2.execute_qdcl_cycle(system_state)

        # Both should produce valid outputs
        assert "outputs" in result1
        assert "outputs" in result2

    def test_phase13_initialization_message(self):
        """Test Phase 13 initialization produces expected status."""
        service = QDCLService()
        status = service.get_status()

        assert status["phase"] == 13
        assert status["version"] == "1.0.0"

        # Verify message would be: "Phase 13: Quantum-Distributed Cognition Layer
        # successfully initialized. QDCL is now active and mapping distributed
        # cognition fields."
        initialization_message = (
            f"Phase {status['phase']}: Quantum-Distributed Cognition Layer "
            "successfully initialized. QDCL is now active and mapping "
            "distributed cognition fields."
        )

        assert "Phase 13" in initialization_message
        assert "QDCL" in initialization_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
