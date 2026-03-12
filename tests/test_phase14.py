"""Tests for Phase 14: RPG-14 (Meta-Causal Inference & Recursive Predictive Governance).

Comprehensive test suite covering:
- Causal graph construction and validation
- Retrocausal inference
- Causal Responsibility Index (CRI)
- Anomaly detection
- Governance prognosis
- Phase 14 service integration
"""

import pytest

from oraculus_di_auditor.rpg14 import (
    CausalAnomalyDetector,
    CausalGraph,
    CausalNode,
    CausalResponsibilityIndex,
    GovernancePrognosisGenerator,
    NodeType,
    Phase14Service,
    RetrocausalInferenceEngine,
    StateVector,
    TrajectoryType,
)


class TestCausalGraph:
    """Tests for CausalGraph."""

    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = CausalGraph()
        assert graph.version == "1.0.0"
        assert len(graph.nodes) == 0

    def test_add_forward_node(self):
        """Test adding forward node."""
        graph = CausalGraph()
        node = graph.add_node(
            node_type=NodeType.FORWARD,
            deviation_slope=0.5,
            qdcl_probability=0.8,
            scalar_harmonic=1.2,
        )

        assert node.node_type == NodeType.FORWARD
        assert node.deviation_slope == 0.5
        assert node.qdcl_probability == 0.8
        assert node.scalar_harmonic == 1.2
        assert node.node_id in graph.nodes

    def test_add_retrocausal_node(self):
        """Test adding retrocausal node."""
        graph = CausalGraph()
        node = graph.add_node(node_type=NodeType.RETROCAUSAL)

        assert node.node_type == NodeType.RETROCAUSAL
        assert node.node_id in graph.nodes

    def test_add_predictive_node(self):
        """Test adding predictive node."""
        graph = CausalGraph()
        node = graph.add_node(node_type=NodeType.PREDICTIVE)

        assert node.node_type == NodeType.PREDICTIVE
        assert node.node_id in graph.nodes

    def test_add_edge_success(self):
        """Test adding valid edge."""
        graph = CausalGraph()
        node1 = graph.add_node()
        node2 = graph.add_node()

        success = graph.add_edge(node1.node_id, node2.node_id)

        assert success is True
        assert node2.node_id in node1.child_ids
        assert node1.node_id in node2.parent_ids

    def test_add_edge_cycle_detection(self):
        """Test cycle detection when adding edges."""
        graph = CausalGraph()
        node1 = graph.add_node()
        node2 = graph.add_node()
        node3 = graph.add_node()

        graph.add_edge(node1.node_id, node2.node_id)
        graph.add_edge(node2.node_id, node3.node_id)

        # Try to create cycle
        success = graph.add_edge(node3.node_id, node1.node_id)
        assert success is False

    def test_add_edge_with_retrocausal(self):
        """Test that retrocausal nodes allow cycles."""
        graph = CausalGraph()
        node1 = graph.add_node(node_type=NodeType.RETROCAUSAL)
        node2 = graph.add_node()

        # Retrocausal can participate in cycles
        graph.add_edge(node2.node_id, node1.node_id)
        graph.add_edge(node1.node_id, node2.node_id)

        # Should succeed because retrocausal node is involved
        assert node1.node_id in node2.child_ids

    def test_get_node(self):
        """Test getting node by ID."""
        graph = CausalGraph()
        node = graph.add_node()

        retrieved = graph.get_node(node.node_id)
        assert retrieved == node

        missing = graph.get_node("nonexistent")
        assert missing is None

    def test_get_ancestors(self):
        """Test getting ancestor nodes."""
        graph = CausalGraph()
        root = graph.add_node()
        middle = graph.add_node()
        leaf = graph.add_node()

        graph.add_edge(root.node_id, middle.node_id)
        graph.add_edge(middle.node_id, leaf.node_id)

        ancestors = graph.get_ancestors(leaf.node_id)
        ancestor_ids = {a.node_id for a in ancestors}

        assert root.node_id in ancestor_ids
        assert middle.node_id in ancestor_ids

    def test_get_descendants(self):
        """Test getting descendant nodes."""
        graph = CausalGraph()
        root = graph.add_node()
        middle = graph.add_node()
        leaf = graph.add_node()

        graph.add_edge(root.node_id, middle.node_id)
        graph.add_edge(middle.node_id, leaf.node_id)

        descendants = graph.get_descendants(root.node_id)
        descendant_ids = {d.node_id for d in descendants}

        assert middle.node_id in descendant_ids
        assert leaf.node_id in descendant_ids

    def test_get_causal_path(self):
        """Test finding causal path between nodes."""
        graph = CausalGraph()
        node1 = graph.add_node()
        node2 = graph.add_node()
        node3 = graph.add_node()

        graph.add_edge(node1.node_id, node2.node_id)
        graph.add_edge(node2.node_id, node3.node_id)

        path = graph.get_causal_path(node1.node_id, node3.node_id)

        assert path is not None
        assert len(path) == 3
        assert path[0].node_id == node1.node_id
        assert path[2].node_id == node3.node_id

    def test_validate_graph(self):
        """Test graph validation."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.8)
        node2 = graph.add_node(qdcl_probability=0.9)
        graph.add_edge(node1.node_id, node2.node_id)

        validation = graph.validate_graph()

        assert validation["is_valid"] is True
        assert validation["issue_count"] == 0

    def test_validate_graph_invalid_probability(self):
        """Test validation catches invalid probabilities."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=1.5)  # Invalid

        validation = graph.validate_graph()

        assert validation["is_valid"] is False
        assert validation["issue_count"] > 0

    def test_get_root_nodes(self):
        """Test getting root nodes."""
        graph = CausalGraph()
        root1 = graph.add_node()
        root2 = graph.add_node()
        child = graph.add_node()

        graph.add_edge(root1.node_id, child.node_id)

        roots = graph.get_root_nodes()
        root_ids = {r.node_id for r in roots}

        assert root1.node_id in root_ids
        assert root2.node_id in root_ids
        assert child.node_id not in root_ids

    def test_get_leaf_nodes(self):
        """Test getting leaf nodes."""
        graph = CausalGraph()
        root = graph.add_node()
        leaf1 = graph.add_node()
        leaf2 = graph.add_node()

        graph.add_edge(root.node_id, leaf1.node_id)
        graph.add_edge(root.node_id, leaf2.node_id)

        leaves = graph.get_leaf_nodes()
        leaf_ids = {l.node_id for l in leaves}

        assert leaf1.node_id in leaf_ids
        assert leaf2.node_id in leaf_ids
        assert root.node_id not in leaf_ids

    def test_to_dict(self):
        """Test graph serialization."""
        graph = CausalGraph()
        node = graph.add_node()

        data = graph.to_dict()

        assert data["version"] == "1.0.0"
        assert data["node_count"] == 1
        assert node.node_id in data["nodes"]


class TestStateVector:
    """Tests for StateVector."""

    def test_state_vector_creation(self):
        """Test state vector creation."""
        sv = StateVector(dimension="governance", value=0.7, confidence=0.9)

        assert sv.dimension == "governance"
        assert sv.value == 0.7
        assert sv.confidence == 0.9

    def test_state_vector_to_dict(self):
        """Test state vector serialization."""
        sv = StateVector(dimension="test", value=1.0, confidence=1.0)
        data = sv.to_dict()

        assert data["dimension"] == "test"
        assert data["value"] == 1.0
        assert data["confidence"] == 1.0


class TestCausalNode:
    """Tests for CausalNode."""

    def test_node_add_state_vector(self):
        """Test adding state vectors to node."""
        node = CausalNode()
        node.add_state_vector("dim1", 0.5, 0.8)
        node.add_state_vector("dim2", 0.7, 0.9)

        assert len(node.state_vectors) == 2
        assert node.state_vectors[0].dimension == "dim1"
        assert node.state_vectors[1].value == 0.7

    def test_node_add_parent(self):
        """Test adding parent to node."""
        node = CausalNode()
        node.add_parent("parent_id")

        assert "parent_id" in node.parent_ids

    def test_node_add_child(self):
        """Test adding child to node."""
        node = CausalNode()
        node.add_child("child_id")

        assert "child_id" in node.child_ids

    def test_node_get_weighted_state(self):
        """Test weighted state calculation."""
        node = CausalNode()
        node.add_state_vector("dim", 0.5, 0.5)
        node.add_state_vector("dim", 1.0, 1.0)

        weighted = node.get_weighted_state()

        # Expected: (0.5 * 0.5 + 1.0 * 1.0) / (0.5 + 1.0) = 1.25 / 1.5 = 0.833...
        assert 0.8 < weighted < 0.9

    def test_node_to_dict(self):
        """Test node serialization."""
        node = CausalNode(node_type=NodeType.FORWARD)
        data = node.to_dict()

        assert data["node_type"] == "forward"
        assert "node_id" in data
        assert "state_vectors" in data


class TestRetrocausalInference:
    """Tests for RetrocausalInferenceEngine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        engine = RetrocausalInferenceEngine(max_depth=10)

        assert engine.version == "1.0.0"
        assert engine.max_depth == 10

    def test_infer_root_causes(self):
        """Test root cause inference."""
        graph = CausalGraph()
        root = graph.add_node(qdcl_probability=0.9)
        middle = graph.add_node(qdcl_probability=0.8)
        leaf = graph.add_node(qdcl_probability=0.7)

        graph.add_edge(root.node_id, middle.node_id)
        graph.add_edge(middle.node_id, leaf.node_id)

        engine = RetrocausalInferenceEngine()
        result = engine.infer_root_causes(graph, leaf.node_id)

        assert result["success"] is True
        assert result["root_cause_count"] == 1
        assert result["root_causes"][0]["root_node_id"] == root.node_id

    def test_identify_causal_breaks(self):
        """Test causal break identification."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.1)  # Low probability
        node3 = graph.add_node(deviation_slope=5.0)  # High deviation

        engine = RetrocausalInferenceEngine()
        breaks = engine.identify_causal_breaks(graph, threshold=0.3)

        assert len(breaks) >= 2
        break_types = {b["type"] for b in breaks}
        assert "probability_drop" in break_types
        assert "deviation_discontinuity" in break_types

    def test_compute_causal_influence(self):
        """Test causal influence computation."""
        graph = CausalGraph()
        source = graph.add_node(qdcl_probability=0.9)
        target = graph.add_node(qdcl_probability=0.8)
        graph.add_edge(source.node_id, target.node_id)

        engine = RetrocausalInferenceEngine()
        result = engine.compute_causal_influence(graph, source.node_id, target.node_id)

        assert result["has_influence"] is True
        assert result["influence_strength"] > 0

    def test_analyze_causal_chain(self):
        """Test causal chain analysis."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.8)
        graph.add_edge(node1.node_id, node2.node_id)

        engine = RetrocausalInferenceEngine()
        result = engine.analyze_causal_chain(graph, [node1.node_id, node2.node_id])

        assert result["is_valid_chain"] is True
        assert result["chain_length"] == 2
        assert result["chain_strength"] > 0


class TestCausalResponsibilityIndex:
    """Tests for CausalResponsibilityIndex."""

    def test_cri_initialization(self):
        """Test CRI calculator initialization."""
        cri = CausalResponsibilityIndex()

        assert cri.version == "1.0.0"
        assert cri.harmonic_weight == 0.3
        assert cri.probability_weight == 0.3

    def test_cri_initialization_invalid_weights(self):
        """Test CRI initialization with invalid weights."""
        with pytest.raises(ValueError):
            CausalResponsibilityIndex(
                harmonic_weight=0.5,
                probability_weight=0.5,
                deviation_weight=0.5,
                connectivity_weight=0.5,
            )

    def test_compute_cri_basic(self):
        """Test basic CRI computation."""
        graph = CausalGraph()
        node = graph.add_node(
            qdcl_probability=0.8, scalar_harmonic=1.0, deviation_slope=0.5
        )

        cri_calc = CausalResponsibilityIndex()
        result = cri_calc.compute_cri(graph, node.node_id)

        assert result["success"] is True
        assert 0 <= result["cri"] <= 1
        assert "factors" in result

    def test_compute_cri_with_anomaly_penalty(self):
        """Test CRI computation with anomaly penalty."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=0.9)

        cri_calc = CausalResponsibilityIndex()
        result_no_penalty = cri_calc.compute_cri(
            graph, node.node_id, anomaly_penalty=0.0
        )
        result_with_penalty = cri_calc.compute_cri(
            graph, node.node_id, anomaly_penalty=0.5
        )

        assert result_with_penalty["cri"] < result_no_penalty["cri"]

    def test_compute_aggregate_cri(self):
        """Test aggregate CRI computation."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.5)

        cri_calc = CausalResponsibilityIndex()
        result = cri_calc.compute_aggregate_cri(graph, [node1.node_id, node2.node_id])

        assert result["success"] is True
        assert result["node_count"] == 2
        assert "avg_cri" in result

    def test_rank_by_responsibility(self):
        """Test ranking nodes by CRI."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.5)

        cri_calc = CausalResponsibilityIndex()
        rankings = cri_calc.rank_by_responsibility(graph)

        assert len(rankings) == 2
        # Higher probability should rank higher
        assert rankings[0]["cri"] >= rankings[1]["cri"]

    def test_explain_cri(self):
        """Test CRI explanation generation."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=0.8)

        cri_calc = CausalResponsibilityIndex()
        result = cri_calc.compute_cri(graph, node.node_id)
        explanation = cri_calc.explain_cri(result)

        assert isinstance(explanation, str)
        assert "CRI" in explanation
        assert "responsibility" in explanation.lower()


class TestCausalAnomalyDetector:
    """Tests for CausalAnomalyDetector."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = CausalAnomalyDetector()

        assert detector.version == "1.0.0"
        assert detector.probability_threshold == 0.3

    def test_detect_all_anomalies(self):
        """Test complete anomaly detection cycle."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.1)  # Low prob

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        # Check all 7 required outputs
        assert "output_1_anomaly_summary" in report
        assert "output_2_break_locations" in report
        assert "output_3_contradiction_map" in report
        assert "output_4_non_convergent_trajectories" in report
        assert "output_5_undefined_states" in report
        assert "output_6_systemic_inconsistencies" in report
        assert "output_7_recommended_actions" in report

    def test_detect_probability_breaks(self):
        """Test detection of probability breaks."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=0.05)  # Very low

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        summary = report["output_1_anomaly_summary"]
        assert summary["breaks"] > 0

    def test_detect_contradictions(self):
        """Test detection of contradictions."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=1.5)  # Invalid

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        contradictions = report["output_3_contradiction_map"]["contradictions"]
        assert len(contradictions) > 0

    def test_detect_undefined_states(self):
        """Test detection of undefined states."""
        graph = CausalGraph()
        node = graph.add_node()  # No state vectors

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        undefined = report["output_5_undefined_states"]["states"]
        assert len(undefined) > 0

    def test_anomaly_severity_breakdown(self):
        """Test anomaly severity breakdown."""
        graph = CausalGraph()
        graph.add_node(qdcl_probability=0.05)  # High severity
        graph.add_node(qdcl_probability=0.2)  # Medium severity

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        breakdown = report["output_1_anomaly_summary"]["severity_breakdown"]
        assert "high" in breakdown
        assert "medium" in breakdown

    def test_recommended_actions_generation(self):
        """Test recommended actions generation."""
        graph = CausalGraph()
        graph.add_node(qdcl_probability=0.05)

        detector = CausalAnomalyDetector()
        report = detector.detect_all_anomalies(graph)

        actions = report["output_7_recommended_actions"]
        assert len(actions) > 0
        assert "action" in actions[0]


class TestGovernancePrognosis:
    """Tests for GovernancePrognosisGenerator."""

    def test_generator_initialization(self):
        """Test generator initialization."""
        generator = GovernancePrognosisGenerator(time_depth=10, branching_factor=3)

        assert generator.version == "1.0.0"
        assert generator.time_depth == 10
        assert generator.branching_factor == 3

    def test_generate_prognosis(self):
        """Test complete prognosis generation."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.8)
        graph.add_edge(node1.node_id, node2.node_id)

        generator = GovernancePrognosisGenerator()
        prognosis = generator.generate_prognosis(graph)

        assert "best_case_trajectory" in prognosis
        assert "worst_case_trajectory" in prognosis
        assert "median_trajectory" in prognosis
        assert "governance_stability_index" in prognosis
        assert "risk_advisories" in prognosis

    def test_best_case_trajectory(self):
        """Test best-case trajectory generation."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9, scalar_harmonic=1.1)
        node2 = graph.add_node(qdcl_probability=0.8, scalar_harmonic=1.0)
        graph.add_edge(node1.node_id, node2.node_id)

        generator = GovernancePrognosisGenerator()
        prognosis = generator.generate_prognosis(graph)

        best_case = prognosis["best_case_trajectory"]
        assert best_case["trajectory_type"] == TrajectoryType.BEST_CASE
        assert best_case["outcome_score"] > 0

    def test_worst_case_trajectory(self):
        """Test worst-case trajectory generation."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=0.3)

        generator = GovernancePrognosisGenerator()
        prognosis = generator.generate_prognosis(graph)

        worst_case = prognosis["worst_case_trajectory"]
        assert worst_case["trajectory_type"] == TrajectoryType.WORST_CASE

    def test_stability_index(self):
        """Test stability index calculation."""
        graph = CausalGraph()
        node1 = graph.add_node(qdcl_probability=0.9)
        node2 = graph.add_node(qdcl_probability=0.8)
        graph.add_edge(node1.node_id, node2.node_id)

        generator = GovernancePrognosisGenerator()
        prognosis = generator.generate_prognosis(graph)

        stability = prognosis["governance_stability_index"]
        assert "stability_score" in stability
        assert "is_stable" in stability
        assert 0 <= stability["stability_score"] <= 1

    def test_risk_advisories(self):
        """Test risk advisory generation."""
        graph = CausalGraph()
        node = graph.add_node(qdcl_probability=0.2)  # Low probability

        generator = GovernancePrognosisGenerator()
        prognosis = generator.generate_prognosis(graph)

        advisories = prognosis["risk_advisories"]
        assert isinstance(advisories, list)


class TestPhase14Service:
    """Tests for Phase14Service."""

    def test_service_initialization(self):
        """Test service initialization."""
        service = Phase14Service()

        assert service.version == "1.0.0"
        assert service.phase == 14
        assert service.cycle_count == 0

    def test_service_components(self):
        """Test that service has all required components."""
        service = Phase14Service()

        assert service.causal_graph is not None
        assert service.retrocausal_engine is not None
        assert service.cri_calculator is not None
        assert service.anomaly_detector is not None
        assert service.prognosis_generator is not None

    def test_run_cycle_basic(self):
        """Test basic cycle execution."""
        service = Phase14Service()

        system_state = {
            "components": [
                {"id": "comp1", "deviation_slope": 0.5},
                {"id": "comp2", "deviation_slope": 0.3},
            ],
            "dependencies": [{"source": "comp1", "target": "comp2"}],
        }

        result = service.run_cycle(system_state)

        assert result["phase"] == 14
        assert result["cycle"] == 1
        assert "anomaly_report" in result
        assert "cri_rankings" in result
        assert "governance_prognosis" in result
        assert "governance_audit" in result
        assert "traceability_report" in result

    def test_run_cycle_with_harmonics(self):
        """Test cycle with Phase 12 harmonics."""
        service = Phase14Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        harmonics = {0: 1.2}

        result = service.run_cycle(system_state, phase12_harmonics=harmonics)

        assert result["phase"] == 14

    def test_run_cycle_with_probabilities(self):
        """Test cycle with Phase 13 probabilities."""
        service = Phase14Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        probabilities = {"comp1": 0.8}

        result = service.run_cycle(system_state, phase13_probabilities=probabilities)

        assert result["phase"] == 14

    def test_compute_cri(self):
        """Test CRI computation."""
        service = Phase14Service()
        service.causal_graph.add_node(qdcl_probability=0.8)

        result = service.compute_cri()

        assert "rankings" in result
        assert "aggregate" in result

    def test_detect_causal_breaks(self):
        """Test causal break detection."""
        service = Phase14Service()
        service.causal_graph.add_node(qdcl_probability=0.1)

        result = service.detect_causal_breaks()

        assert "output_1_anomaly_summary" in result

    def test_generate_prognosis(self):
        """Test prognosis generation."""
        service = Phase14Service()
        service.causal_graph.add_node(qdcl_probability=0.8)

        result = service.generate_prognosis()

        assert "best_case_trajectory" in result
        assert "worst_case_trajectory" in result
        assert "median_trajectory" in result

    def test_audit_governance(self):
        """Test governance auditing."""
        service = Phase14Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        cycle_result = service.run_cycle(system_state)

        audit = cycle_result["governance_audit"]

        assert "health_status" in audit
        assert "health_score" in audit
        assert "metrics" in audit
        assert "recommendations" in audit

    def test_integrate_with_phase13(self):
        """Test Phase 13 integration."""
        service = Phase14Service()

        phase13_output = {
            "version": "1.0.0",
            "output_4_trajectory_probability_cube": {
                "trajectories": [
                    {"trajectory_id": "traj1", "probability": 0.8},
                    {"trajectory_id": "traj2", "probability": 0.6},
                ]
            },
        }

        result = service.integrate_with_phase13(phase13_output)

        assert result["success"] is True
        assert result["extracted_probabilities"] == 2

    def test_produce_traceability_report(self):
        """Test traceability report generation."""
        service = Phase14Service()
        service.causal_graph.add_node(qdcl_probability=0.8)

        anomaly_report = service.detect_causal_breaks()
        cri_rankings = service.compute_cri()
        prognosis = service.generate_prognosis()

        report = service.produce_traceability_report(
            anomaly_report, cri_rankings, prognosis
        )

        assert report["version"] == "1.0.0"
        assert report["phase"] == 14
        assert "reasoning_chain" in report
        assert "reproducibility" in report
        assert report["reproducibility"]["deterministic"] is True

    def test_get_service_info(self):
        """Test getting service information."""
        service = Phase14Service()
        info = service.get_service_info()

        assert info["version"] == "1.0.0"
        assert info["phase"] == 14
        assert "components" in info

    def test_execution_history(self):
        """Test that execution history is maintained."""
        service = Phase14Service()

        system_state = {"components": [], "dependencies": []}
        service.run_cycle(system_state)
        service.run_cycle(system_state)

        assert len(service.execution_history) == 2

    def test_cycle_counter_increment(self):
        """Test that cycle counter increments."""
        service = Phase14Service()

        system_state = {"components": [], "dependencies": []}
        service.run_cycle(system_state)

        assert service.cycle_count == 1

        service.run_cycle(system_state)
        assert service.cycle_count == 2

    def test_deterministic_output(self):
        """Test that outputs are deterministic."""
        service1 = Phase14Service()
        service2 = Phase14Service()

        system_state = {
            "components": [{"id": "comp1", "deviation_slope": 0.5}],
            "dependencies": [],
        }

        result1 = service1.run_cycle(system_state)
        result2 = service2.run_cycle(system_state)

        # CRI should be deterministic
        cri1 = result1["cri_rankings"]["aggregate"]["avg_cri"]
        cri2 = result2["cri_rankings"]["aggregate"]["avg_cri"]

        assert cri1 == cri2
