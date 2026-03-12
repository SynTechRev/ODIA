"""Tests for Phase 15: OTGE-15 (Omni-Contextual Temporal Governance Engine).

Comprehensive test suite covering:
- Temporal Context Graph (TCG)
- Temporal Stability Field (TSF)
- Temporal Governance Policy Synthesizer (TGPS)
- Temporal Integrity Auditor (TIA-15)
- Phase15Service integration
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from oraculus_di_auditor.otge15 import (
    Phase15Service,
    TemporalContextGraph,
    TemporalGovernanceSynthesizer,
    TemporalIntegrityAuditor,
    TemporalNode,
    TemporalStabilityField,
)


class TestTemporalNode:
    """Tests for TemporalNode."""

    def test_temporal_node_initialization(self):
        """Test temporal node initialization with defaults."""
        node = TemporalNode()

        assert node.node_id is not None
        assert isinstance(node.timestamp, datetime)
        assert node.state_vector == {}
        assert node.harmonic_weight == 1.0
        assert node.qdcl_probability == 1.0
        assert node.causal_parent_ids == []
        assert "past" in node.temporal_neighbors
        assert "future" in node.temporal_neighbors
        assert "parallel" in node.temporal_neighbors
        assert node.uncertainty_index == 0.0

    def test_temporal_node_with_values(self):
        """Test temporal node with custom values."""
        timestamp = datetime.now(UTC)
        state = {"key": "value"}
        node = TemporalNode(
            timestamp=timestamp,
            state_vector=state,
            harmonic_weight=1.5,
            qdcl_probability=0.8,
            causal_parent_ids=["parent1"],
            uncertainty_index=0.3,
        )

        assert node.timestamp == timestamp
        assert node.state_vector == state
        assert node.harmonic_weight == 1.5
        assert node.qdcl_probability == 0.8
        assert node.causal_parent_ids == ["parent1"]
        assert node.uncertainty_index == 0.3

    def test_temporal_node_to_dict(self):
        """Test temporal node serialization."""
        node = TemporalNode(
            state_vector={"test": "data"},
            harmonic_weight=1.2,
        )

        node_dict = node.to_dict()

        assert "node_id" in node_dict
        assert "timestamp" in node_dict
        assert node_dict["state_vector"] == {"test": "data"}
        assert node_dict["harmonic_weight"] == 1.2


class TestTemporalContextGraph:
    """Tests for Temporal Context Graph."""

    def test_tcg_initialization(self):
        """Test TCG initialization."""
        tcg = TemporalContextGraph()

        assert tcg.version == "1.0.0"
        assert len(tcg.nodes) == 0
        assert len(tcg.timeline_branches) == 0

    def test_add_temporal_slice(self):
        """Test adding temporal slice."""
        tcg = TemporalContextGraph()
        state = {"component": "test"}

        node = tcg.add_temporal_slice(
            state_vector=state,
            harmonic_weight=1.3,
            qdcl_probability=0.9,
        )

        assert node.node_id in tcg.nodes
        assert tcg.nodes[node.node_id] == node
        assert node.state_vector == state
        assert node.harmonic_weight == 1.3
        assert node.qdcl_probability == 0.9

    def test_link_temporal_neighbors(self):
        """Test linking temporal neighbors."""
        tcg = TemporalContextGraph()
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})
        node3 = tcg.add_temporal_slice(state_vector={"id": 3})

        # Link node2 to past (node1) and future (node3)
        success = tcg.link_temporal_neighbors(
            node2.node_id,
            past_ids=[node1.node_id],
            future_ids=[node3.node_id],
        )

        assert success is True
        assert node1.node_id in node2.temporal_neighbors["past"]
        assert node3.node_id in node2.temporal_neighbors["future"]

    def test_traverse_backward(self):
        """Test backward traversal."""
        tcg = TemporalContextGraph()

        # Create temporal chain: 1 -> 2 -> 3
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})
        node3 = tcg.add_temporal_slice(state_vector={"id": 3})

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])
        tcg.link_temporal_neighbors(node3.node_id, past_ids=[node2.node_id])

        # Traverse backward from node3
        path = tcg.traverse_backward(node3.node_id)

        assert len(path) == 3
        assert path[0] == node3
        assert path[1] == node2
        assert path[2] == node1

    def test_traverse_forward(self):
        """Test forward traversal."""
        tcg = TemporalContextGraph()

        # Create temporal chain: 1 -> 2 -> 3
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})
        node3 = tcg.add_temporal_slice(state_vector={"id": 3})

        tcg.link_temporal_neighbors(node1.node_id, future_ids=[node2.node_id])
        tcg.link_temporal_neighbors(node2.node_id, future_ids=[node3.node_id])

        # Traverse forward from node1
        path = tcg.traverse_forward(node1.node_id)

        assert len(path) == 3
        assert path[0] == node1
        assert path[1] == node2
        assert path[2] == node3

    def test_get_parallel_timelines(self):
        """Test getting parallel timelines."""
        tcg = TemporalContextGraph()

        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})
        node3 = tcg.add_temporal_slice(state_vector={"id": 3})

        # Link parallel timelines
        tcg.link_temporal_neighbors(
            node1.node_id, parallel_ids=[node2.node_id, node3.node_id]
        )

        parallel = tcg.get_parallel_timelines(node1.node_id)

        assert len(parallel) == 2
        assert node2 in parallel
        assert node3 in parallel

    def test_create_timeline_branch(self):
        """Test creating timeline branch."""
        tcg = TemporalContextGraph()
        node = tcg.add_temporal_slice(state_vector={"id": 1})

        branch_id = tcg.create_timeline_branch(node.node_id, "test_branch")

        assert branch_id == "test_branch"
        assert branch_id in tcg.timeline_branches
        assert node.node_id in tcg.timeline_branches[branch_id]

    def test_add_node_to_branch(self):
        """Test adding node to branch."""
        tcg = TemporalContextGraph()
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})

        branch_id = tcg.create_timeline_branch(node1.node_id)
        success = tcg.add_node_to_branch(branch_id, node2.node_id)

        assert success is True
        assert node2.node_id in tcg.timeline_branches[branch_id]

    def test_compute_temporal_distance(self):
        """Test computing temporal distance."""
        tcg = TemporalContextGraph()
        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 + timedelta(seconds=10)

        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, timestamp=timestamp1)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, timestamp=timestamp2)

        distance = tcg.compute_temporal_distance(node1.node_id, node2.node_id)

        assert abs(distance - 10.0) < 0.1

    def test_get_root_nodes(self):
        """Test getting root nodes."""
        tcg = TemporalContextGraph()
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])

        roots = tcg.get_root_nodes()

        assert len(roots) == 1
        assert roots[0] == node1

    def test_get_leaf_nodes(self):
        """Test getting leaf nodes."""
        tcg = TemporalContextGraph()
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})

        tcg.link_temporal_neighbors(node1.node_id, future_ids=[node2.node_id])

        leaves = tcg.get_leaf_nodes()

        assert len(leaves) == 1
        assert leaves[0] == node2

    def test_validate_temporal_consistency(self):
        """Test temporal consistency validation."""
        tcg = TemporalContextGraph()
        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 + timedelta(seconds=10)

        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, timestamp=timestamp1)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, timestamp=timestamp2)

        # Valid link: node1 (past) -> node2 (future)
        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])

        validation = tcg.validate_temporal_consistency()

        assert validation["valid"] is True
        assert len(validation["issues"]) == 0

    def test_temporal_violation_detection(self):
        """Test detection of temporal violations."""
        tcg = TemporalContextGraph()
        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 + timedelta(seconds=10)  # Later!

        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, timestamp=timestamp1)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, timestamp=timestamp2)

        # Invalid: node2 (later timestamp) marked as past of node1 (earlier timestamp)
        # This is a violation because past neighbors should have earlier timestamps
        tcg.link_temporal_neighbors(node1.node_id, past_ids=[node2.node_id])
        tcg.link_temporal_neighbors(node2.node_id, future_ids=[node1.node_id])

        validation = tcg.validate_temporal_consistency()

        assert validation["valid"] is False
        assert len(validation["issues"]) > 0

    def test_tcg_to_dict(self):
        """Test TCG serialization."""
        tcg = TemporalContextGraph()
        node = tcg.add_temporal_slice(state_vector={"test": "data"})

        tcg_dict = tcg.to_dict()

        assert tcg_dict["version"] == "1.0.0"
        assert tcg_dict["node_count"] == 1
        assert node.node_id in tcg_dict["nodes"]


class TestTemporalStabilityField:
    """Tests for Temporal Stability Field."""

    def test_tsf_initialization(self):
        """Test TSF initialization."""
        tsf = TemporalStabilityField()

        assert tsf.version == "1.0.0"
        assert len(tsf.computation_history) == 0
        assert tsf.HARMONIC_WEIGHT == 0.40
        assert tsf.PROBABILISTIC_WEIGHT == 0.30
        assert tsf.CAUSAL_WEIGHT == 0.20
        assert tsf.ANOMALY_WEIGHT == 0.10

    def test_compute_stability_empty_graph(self):
        """Test stability computation on empty graph."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        stability = tsf.compute_stability(tcg)

        assert stability["stability_score"] == 1.0
        assert stability["is_stable"] is True
        assert len(stability["destabilization_hotspots"]) == 0

    def test_compute_stability_with_nodes(self):
        """Test stability computation with nodes."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        # Add nodes with varying properties
        tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.0, qdcl_probability=0.9
        )
        tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=1.1, qdcl_probability=0.85
        )

        stability = tsf.compute_stability(tcg)

        assert "stability_score" in stability
        assert 0.0 <= stability["stability_score"] <= 1.0
        assert "component_scores" in stability

    def test_harmonic_stability(self):
        """Test harmonic stability computation."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        # Nodes with similar harmonics -> high stability
        for i in range(5):
            tcg.add_temporal_slice(
                state_vector={"id": i}, harmonic_weight=1.0 + i * 0.05
            )

        stability = tsf.compute_stability(tcg)

        # Low variance = high harmonic stability
        assert stability["component_scores"]["harmonic_stability"] > 0.7

    def test_probabilistic_continuity(self):
        """Test probabilistic continuity computation."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        # Create chain with smooth probability transitions
        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, qdcl_probability=0.9)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, qdcl_probability=0.85)
        node3 = tcg.add_temporal_slice(state_vector={"id": 3}, qdcl_probability=0.8)

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])
        tcg.link_temporal_neighbors(node3.node_id, past_ids=[node2.node_id])

        stability = tsf.compute_stability(tcg)

        # Smooth transitions = high continuity
        assert stability["component_scores"]["probabilistic_continuity"] > 0.7

    def test_causal_consistency(self):
        """Test causal consistency computation."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 + timedelta(seconds=10)

        # Causally consistent: parent before child
        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, timestamp=timestamp1, causal_parent_ids=[]
        )
        tcg.add_temporal_slice(
            state_vector={"id": 2},
            timestamp=timestamp2,
            causal_parent_ids=[node1.node_id],
        )

        stability = tsf.compute_stability(tcg)

        # Consistent causality = high score
        assert stability["component_scores"]["causal_consistency"] == 1.0

    def test_identify_hotspots(self):
        """Test hotspot identification."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        # Normal nodes
        tcg.add_temporal_slice(state_vector={"id": 1}, harmonic_weight=1.0)

        # Hotspot: extreme harmonic weight and high uncertainty
        tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=3.0, uncertainty_index=0.9
        )

        stability = tsf.compute_stability(tcg)

        assert len(stability["destabilization_hotspots"]) > 0

    def test_temporal_drift_warnings(self):
        """Test temporal drift warning generation."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        # Create branch with significant drift
        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, harmonic_weight=1.0)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, harmonic_weight=2.0)

        branch_id = tcg.create_timeline_branch(node1.node_id)
        tcg.add_node_to_branch(branch_id, node2.node_id)

        stability = tsf.compute_stability(tcg)

        assert "temporal_drift_warnings" in stability

    def test_compute_local_stability(self):
        """Test local stability computation."""
        tsf = TemporalStabilityField()
        tcg = TemporalContextGraph()

        node = tcg.add_temporal_slice(
            state_vector={"id": 1},
            harmonic_weight=1.0,
            qdcl_probability=0.9,
            uncertainty_index=0.1,
        )

        local_stability = tsf.compute_local_stability(tcg, node.node_id)

        assert 0.0 <= local_stability <= 1.0

    def test_tsf_to_dict(self):
        """Test TSF serialization."""
        tsf = TemporalStabilityField()

        tsf_dict = tsf.to_dict()

        assert tsf_dict["version"] == "1.0.0"
        assert "weights" in tsf_dict
        assert "thresholds" in tsf_dict


class TestTemporalGovernanceSynthesizer:
    """Tests for Temporal Governance Policy Synthesizer."""

    def test_tgps_initialization(self):
        """Test TGPS initialization."""
        tgps = TemporalGovernanceSynthesizer()

        assert tgps.version == "1.0.0"
        assert len(tgps.synthesis_history) == 0

    def test_synthesize_governance_policy(self):
        """Test governance policy synthesis."""
        tgps = TemporalGovernanceSynthesizer()
        tcg = TemporalContextGraph()

        # Add some temporal slices
        tcg.add_temporal_slice(state_vector={"id": 1})
        tcg.add_temporal_slice(state_vector={"id": 2})

        stability_report = {
            "stability_score": 0.8,
            "destabilization_hotspots": [],
            "temporal_drift_warnings": [],
        }

        policy = tgps.synthesize_governance_policy(tcg, stability_report)

        assert "version" in policy
        assert "timestamp" in policy
        assert "analysis" in policy
        assert "recommendations" in policy
        assert policy["deterministic"] is True

    def test_cascading_failure_analysis(self):
        """Test cascading failure analysis."""
        tgps = TemporalGovernanceSynthesizer()
        tcg = TemporalContextGraph()

        # Create chain that could cascade
        node1 = tcg.add_temporal_slice(state_vector={"id": 1})
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})
        node3 = tcg.add_temporal_slice(state_vector={"id": 3})

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])
        tcg.link_temporal_neighbors(node3.node_id, past_ids=[node2.node_id])

        # Simulate anomalies
        anomalies = [{"node_id": node1.node_id, "severity": "high"}]

        stability_report = {"stability_score": 0.7}

        policy = tgps.synthesize_governance_policy(tcg, stability_report, anomalies)

        cascade_analysis = policy["analysis"]["cascading_failure_risks"]
        assert "total_cascade_risks" in cascade_analysis

    def test_retrocausal_corrections(self):
        """Test retrocausal correction identification."""
        tgps = TemporalGovernanceSynthesizer()
        tcg = TemporalContextGraph()

        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.5, qdcl_probability=0.9
        )
        node2 = tcg.add_temporal_slice(state_vector={"id": 2})

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])

        anomalies = [{"node_id": node2.node_id}]

        stability_report = {"stability_score": 0.7}

        policy = tgps.synthesize_governance_policy(tcg, stability_report, anomalies)

        corrections = policy["analysis"]["retrocausal_corrections"]
        assert "total_corrections" in corrections

    def test_multi_timeline_consensus(self):
        """Test multi-timeline consensus planning."""
        tgps = TemporalGovernanceSynthesizer()
        tcg = TemporalContextGraph()

        # Create multiple branches with sufficient nodes
        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.0, qdcl_probability=0.9
        )
        node2 = tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=1.2, qdcl_probability=0.7
        )
        node3 = tcg.add_temporal_slice(
            state_vector={"id": 3}, harmonic_weight=1.1, qdcl_probability=0.85
        )
        node4 = tcg.add_temporal_slice(
            state_vector={"id": 4}, harmonic_weight=1.3, qdcl_probability=0.75
        )

        # Create branches with multiple nodes each
        branch1 = tcg.create_timeline_branch(node1.node_id, "branch1")
        tcg.add_node_to_branch(branch1, node3.node_id)

        branch2 = tcg.create_timeline_branch(node2.node_id, "branch2")
        tcg.add_node_to_branch(branch2, node4.node_id)

        stability_report = {"stability_score": 0.8}

        policy = tgps.synthesize_governance_policy(tcg, stability_report)

        consensus = policy["analysis"]["multi_timeline_consensus"]
        assert "branches_analyzed" in consensus
        assert consensus["branches_analyzed"] == 2

    def test_recommendation_generation(self):
        """Test recommendation generation."""
        tgps = TemporalGovernanceSynthesizer()
        tcg = TemporalContextGraph()

        tcg.add_temporal_slice(state_vector={"id": 1})

        stability_report = {
            "stability_score": 0.5,  # Low stability
            "destabilization_hotspots": [{"node_id": "test"}],
            "temporal_drift_warnings": [],
        }

        policy = tgps.synthesize_governance_policy(tcg, stability_report)

        recommendations = policy["recommendations"]
        assert isinstance(recommendations, list)

    def test_tgps_to_dict(self):
        """Test TGPS serialization."""
        tgps = TemporalGovernanceSynthesizer()

        tgps_dict = tgps.to_dict()

        assert tgps_dict["version"] == "1.0.0"
        assert "synthesis_count" in tgps_dict


class TestTemporalIntegrityAuditor:
    """Tests for Temporal Integrity Auditor."""

    def test_tia_initialization(self):
        """Test TIA initialization."""
        tia = TemporalIntegrityAuditor()

        assert tia.version == "1.0.0"
        assert len(tia.audit_history) == 0

    def test_perform_temporal_audit(self):
        """Test performing temporal audit."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        tcg.add_temporal_slice(state_vector={"id": 1})

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        # Check all 7 mandatory outputs
        assert "output_1_timeline_consistency_report" in audit
        assert "output_2_temporal_contradiction_detection" in audit
        assert "output_3_drift_vectors" in audit
        assert "output_4_retrocausal_impact_matrix" in audit
        assert "output_5_forward_cascade_criticality" in audit
        assert "output_6_cross_branch_divergence_analysis" in audit
        assert "output_7_recommended_stabilizers" in audit
        assert "overall_integrity_score" in audit

    def test_timeline_consistency_report(self):
        """Test timeline consistency report generation."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 + timedelta(seconds=10)

        node1 = tcg.add_temporal_slice(state_vector={"id": 1}, timestamp=timestamp1)
        node2 = tcg.add_temporal_slice(state_vector={"id": 2}, timestamp=timestamp2)

        tcg.link_temporal_neighbors(node2.node_id, past_ids=[node1.node_id])

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        consistency = audit["output_1_timeline_consistency_report"]
        assert "is_consistent" in consistency
        assert "consistency_score" in consistency

    def test_temporal_contradiction_detection(self):
        """Test temporal contradiction detection."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        timestamp1 = datetime.now(UTC)
        timestamp2 = timestamp1 - timedelta(seconds=10)  # Earlier

        # Contradiction: effect before cause
        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, timestamp=timestamp1, causal_parent_ids=[]
        )
        _ = tcg.add_temporal_slice(
            state_vector={"id": 2},
            timestamp=timestamp2,
            causal_parent_ids=[node1.node_id],
        )

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        contradictions = audit["output_2_temporal_contradiction_detection"]
        assert contradictions["total_contradictions"] > 0

    def test_drift_vectors_computation(self):
        """Test drift vector computation."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        # Create branch with drift
        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.0, qdcl_probability=0.9
        )
        node2 = tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=1.5, qdcl_probability=0.7
        )

        branch_id = tcg.create_timeline_branch(node1.node_id)
        tcg.add_node_to_branch(branch_id, node2.node_id)

        stability_report = {
            "stability_score": 0.8,
            "temporal_drift_warnings": [],
        }
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        drift_vectors = audit["output_3_drift_vectors"]
        assert "total_drift_vectors" in drift_vectors

    def test_retrocausal_impact_matrix(self):
        """Test retrocausal impact matrix building."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.0, qdcl_probability=0.9
        )
        node2 = tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=1.1, qdcl_probability=0.85
        )

        tcg.link_temporal_neighbors(node1.node_id, future_ids=[node2.node_id])

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        impact_matrix = audit["output_4_retrocausal_impact_matrix"]
        assert "total_nodes" in impact_matrix
        assert "impact_matrix" in impact_matrix

    def test_forward_cascade_criticality(self):
        """Test forward-cascade criticality assessment."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        tcg.add_temporal_slice(state_vector={"id": 1})

        stability_report = {"stability_score": 0.8}
        governance_policy = {
            "analysis": {
                "cascading_failure_risks": {
                    "risks": [
                        {
                            "target_node_id": "node1",
                            "cascade_probability": 0.8,
                            "affected_ancestor_count": 3,
                            "severity": "high",
                        }
                    ]
                }
            }
        }

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        criticality = audit["output_5_forward_cascade_criticality"]
        assert "total_cascade_points" in criticality

    def test_cross_branch_divergence(self):
        """Test cross-branch divergence analysis."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        # Create two divergent branches
        node1 = tcg.add_temporal_slice(
            state_vector={"id": 1}, harmonic_weight=1.0, qdcl_probability=0.9
        )
        node2 = tcg.add_temporal_slice(
            state_vector={"id": 2}, harmonic_weight=2.0, qdcl_probability=0.5
        )

        tcg.create_timeline_branch(node1.node_id, "branch1")
        tcg.create_timeline_branch(node2.node_id, "branch2")

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        divergence = audit["output_6_cross_branch_divergence_analysis"]
        assert "total_branch_comparisons" in divergence

    def test_recommended_stabilizers(self):
        """Test stabilizer recommendations."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        tcg.add_temporal_slice(state_vector={"id": 1})

        stability_report = {
            "stability_score": 0.5,  # Low stability
            "destabilization_hotspots": [{"node_id": "test"}],
            "temporal_drift_warnings": [{"type": "drift"}],
        }
        governance_policy = {
            "analysis": {
                "cascading_failure_risks": {"high_severity_count": 2, "risks": []}
            }
        }

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        stabilizers = audit["output_7_recommended_stabilizers"]
        assert "total_stabilizers" in stabilizers
        assert len(stabilizers["stabilizers"]) > 0

    def test_overall_integrity_score(self):
        """Test overall integrity score computation."""
        tia = TemporalIntegrityAuditor()
        tcg = TemporalContextGraph()

        tcg.add_temporal_slice(state_vector={"id": 1})

        stability_report = {"stability_score": 0.8}
        governance_policy = {"analysis": {"cascading_failure_risks": {"risks": []}}}

        audit = tia.perform_temporal_audit(tcg, stability_report, governance_policy)

        integrity_score = audit["overall_integrity_score"]
        assert 0.0 <= integrity_score <= 1.0

    def test_tia_to_dict(self):
        """Test TIA serialization."""
        tia = TemporalIntegrityAuditor()

        tia_dict = tia.to_dict()

        assert tia_dict["version"] == "1.0.0"
        assert "audit_count" in tia_dict


class TestPhase15Service:
    """Tests for Phase 15 Service."""

    def test_service_initialization(self):
        """Test Phase 15 service initialization."""
        service = Phase15Service()

        assert service.version == "1.0.0"
        assert service.phase == 15
        assert service.cycle_count == 0
        assert isinstance(service.tcg, TemporalContextGraph)
        assert isinstance(service.tsf, TemporalStabilityField)
        assert isinstance(service.tgps, TemporalGovernanceSynthesizer)
        assert isinstance(service.tia, TemporalIntegrityAuditor)

    def test_run_cycle_basic(self):
        """Test running basic cycle."""
        service = Phase15Service()

        system_state = {
            "components": [{"id": "comp1", "status": "active"}],
            "dependencies": [],
        }

        result = service.run_cycle(system_state)

        assert result["version"] == "1.0.0"
        assert result["phase"] == 15
        assert result["cycle"] == 1
        assert "temporal_graph" in result
        assert "temporal_stability" in result
        assert "temporal_governance" in result
        assert "temporal_audit" in result

    def test_run_cycle_with_phase12_harmonics(self):
        """Test cycle with Phase 12 harmonics."""
        service = Phase15Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        harmonics = {1: 1.0, 2: 1.1, 3: 0.9}

        result = service.run_cycle(system_state, phase12_harmonics=harmonics)

        assert result["harmonic_inputs"]["available"] is True
        assert result["harmonic_inputs"]["layer_count"] == 3

    def test_run_cycle_with_phase13_probabilities(self):
        """Test cycle with Phase 13 probabilities."""
        service = Phase15Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        probabilities = {"comp1": 0.9, "comp2": 0.85}

        result = service.run_cycle(system_state, phase13_probabilities=probabilities)

        assert result["qdcl_inputs"]["available"] is True
        assert result["qdcl_inputs"]["probability_count"] == 2

    def test_run_cycle_with_phase14_outputs(self):
        """Test cycle with Phase 14 outputs."""
        service = Phase15Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}
        phase14_outputs = {
            "cycle": 1,
            "anomaly_report": {
                "output_1_anomaly_summary": {"total_anomalies": 2},
                "output_2_break_locations": {"locations": []},
                "output_3_contradiction_map": {"contradictions": []},
            },
            "cri_rankings": {"rankings": []},
            "governance_audit": {"health_status": "good"},
        }

        result = service.run_cycle(system_state, phase14_outputs=phase14_outputs)

        assert result["phase14_outputs"]["available"] is True
        assert result["phase14_outputs"]["anomaly_count"] == 2

    def test_add_temporal_slice(self):
        """Test adding temporal slice through service."""
        service = Phase15Service()

        node_id = service.add_temporal_slice(
            state_vector={"test": "data"}, harmonic_weight=1.2, qdcl_probability=0.9
        )

        assert node_id in service.tcg.nodes
        assert len(service.tcg.nodes) == 1

    def test_create_timeline_branch(self):
        """Test creating timeline branch through service."""
        service = Phase15Service()

        node_id = service.add_temporal_slice(state_vector={"id": 1})
        branch_id = service.create_timeline_branch(node_id, "test_branch")

        assert branch_id == "test_branch"
        assert branch_id in service.tcg.timeline_branches

    def test_compute_stability(self):
        """Test computing stability through service."""
        service = Phase15Service()

        service.add_temporal_slice(state_vector={"id": 1})

        stability = service.compute_stability()

        assert "stability_score" in stability
        assert "is_stable" in stability

    def test_get_service_info(self):
        """Test getting service information."""
        service = Phase15Service()

        info = service.get_service_info()

        assert info["version"] == "1.0.0"
        assert info["phase"] == 15
        assert "components" in info

    def test_execution_history(self):
        """Test execution history tracking."""
        service = Phase15Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}

        service.run_cycle(system_state)
        service.run_cycle(system_state)

        history = service.get_execution_history()

        assert len(history) == 2
        assert history[0]["cycle"] == 1
        assert history[1]["cycle"] == 2

    def test_cycle_counter_increment(self):
        """Test cycle counter increments properly."""
        service = Phase15Service()

        system_state = {"components": [], "dependencies": []}

        result1 = service.run_cycle(system_state)
        result2 = service.run_cycle(system_state)
        result3 = service.run_cycle(system_state)

        assert result1["cycle"] == 1
        assert result2["cycle"] == 2
        assert result3["cycle"] == 3
        assert service.cycle_count == 3

    def test_deterministic_output(self):
        """Test deterministic output."""
        service = Phase15Service()

        system_state = {"components": [{"id": "comp1"}], "dependencies": []}

        result = service.run_cycle(system_state)

        # Check key deterministic properties
        assert "timestamp" in result
        assert "execution_time_seconds" in result
        assert result["temporal_governance"]["deterministic"] is True

    def test_service_to_dict(self):
        """Test service serialization."""
        service = Phase15Service()

        service_dict = service.to_dict()

        assert service_dict["version"] == "1.0.0"
        assert service_dict["phase"] == 15
        assert "temporal_graph" in service_dict
        assert "components" in service_dict
