"""Tests for Phase 11 Adaptive Mesh Intelligence and Advanced Agents."""

from oraculus_di_auditor.mesh.adaptive_intelligence import AdaptiveMeshIntelligence
from oraculus_di_auditor.mesh.advanced_agents import (
    CooperativeNegotiationAgent,
    MultiLayerAnomalyAgent,
    SemanticAnalysisAgent,
)


class TestAdaptiveMeshIntelligence:
    """Tests for AdaptiveMeshIntelligence."""

    def test_adaptive_intelligence_initialization(self):
        """Test adaptive intelligence initializes correctly."""
        intelligence = AdaptiveMeshIntelligence()
        assert intelligence is not None
        assert len(intelligence.performance_metrics) == 0
        assert len(intelligence.load_history) == 0
        assert len(intelligence.rebalancing_events) == 0
        assert len(intelligence.micro_agents) == 0

    def test_analyze_mesh_load_without_coordinator(self):
        """Test load analysis without mesh coordinator."""
        intelligence = AdaptiveMeshIntelligence()
        analysis = intelligence.analyze_mesh_load()

        assert "status" in analysis
        assert analysis["status"] == "error"

    def test_evaluate_agent_performance(self):
        """Test agent performance evaluation."""
        intelligence = AdaptiveMeshIntelligence()
        evaluation = intelligence.evaluate_agent_performance("test-agent-1")

        assert "agent_id" in evaluation
        assert evaluation["agent_id"] == "test-agent-1"
        assert "timestamp" in evaluation
        assert "success_rate" in evaluation
        assert "performance_score" in evaluation
        assert "recommendation" in evaluation
        assert 0.0 <= evaluation["success_rate"] <= 1.0
        assert 0.0 <= evaluation["performance_score"] <= 1.0

    def test_rebalance_mesh_not_needed(self):
        """Test mesh rebalancing when not needed."""
        intelligence = AdaptiveMeshIntelligence()
        report = intelligence.rebalance_mesh(force=False)

        # Without coordinator, should handle gracefully
        assert "timestamp" in report

    def test_rebalance_mesh_forced(self):
        """Test forced mesh rebalancing."""
        intelligence = AdaptiveMeshIntelligence()
        report = intelligence.rebalance_mesh(force=True)

        assert "timestamp" in report
        assert "action_taken" in report

    def test_promote_agent(self):
        """Test agent promotion."""
        intelligence = AdaptiveMeshIntelligence()
        result = intelligence.promote_agent("test-agent", "High performance")

        # Without coordinator, should return error
        assert "status" in result
        assert result["status"] == "error"

    def test_demote_agent(self):
        """Test agent demotion."""
        intelligence = AdaptiveMeshIntelligence()
        result = intelligence.demote_agent("test-agent", "Poor performance")

        # Without coordinator, should return error
        assert "status" in result
        assert result["status"] == "error"

    def test_cleanup_micro_agents(self):
        """Test micro-agent cleanup."""
        intelligence = AdaptiveMeshIntelligence()

        # Spawn some micro-agents
        for i in range(3):
            intelligence._spawn_micro_agent(f"parent-{i}", "testing")

        assert len(intelligence.micro_agents) == 3

        # Cleanup (won't remove any yet as they're fresh)
        result = intelligence.cleanup_micro_agents()
        assert "timestamp" in result
        assert "cleaned_count" in result
        assert "active_micro_agents" in result

    def test_get_adaptive_state(self):
        """Test getting adaptive state."""
        intelligence = AdaptiveMeshIntelligence()
        state = intelligence.get_adaptive_state()

        assert "timestamp" in state
        assert "active_micro_agents" in state
        assert "rebalancing_events" in state
        assert "load_history_size" in state
        assert "agents_tracked" in state
        assert "thresholds" in state
        assert "recent_load_history" in state


class TestSemanticAnalysisAgent:
    """Tests for SemanticAnalysisAgent."""

    def test_semantic_agent_initialization(self):
        """Test semantic analysis agent initializes correctly."""
        agent = SemanticAnalysisAgent()
        assert agent is not None
        assert agent.agent_type == "semantic_analysis"
        assert len(agent.capabilities) > 0
        assert "semantic_extraction" in agent.capabilities

    def test_analyze_semantic_structure(self):
        """Test semantic structure analysis."""
        agent = SemanticAnalysisAgent()
        document = {
            "document_text": "The Secretary shall implement regulations.",
            "metadata": {"title": "Test Regulation"},
        }

        analysis = agent.analyze_semantic_structure(document)

        assert "agent_id" in analysis
        assert "timestamp" in analysis
        assert "document_id" in analysis
        assert "semantic_features" in analysis
        assert "conceptual_graph" in analysis
        assert "contextual_anomalies" in analysis
        assert "confidence" in analysis
        assert 0.0 <= analysis["confidence"] <= 1.0

    def test_infer_implicit_requirements(self):
        """Test implicit requirement inference."""
        agent = SemanticAnalysisAgent()
        document = {
            "document_text": (
                "The agency shall report annually. The director may waive"
                " this requirement."
            ),
            "metadata": {"title": "Test Policy"},
        }

        inferences = agent.infer_implicit_requirements(document)

        assert "agent_id" in inferences
        assert "timestamp" in inferences
        assert "inferred_requirements" in inferences
        assert "confidence_score" in inferences
        assert isinstance(inferences["inferred_requirements"], list)
        # Should detect "shall" and "may"
        assert len(inferences["inferred_requirements"]) >= 2


class TestMultiLayerAnomalyAgent:
    """Tests for MultiLayerAnomalyAgent."""

    def test_multilayer_agent_initialization(self):
        """Test multi-layer anomaly agent initializes correctly."""
        agent = MultiLayerAnomalyAgent()
        assert agent is not None
        assert agent.agent_type == "multilayer_anomaly"
        assert len(agent.capabilities) > 0
        assert "structural_analysis" in agent.capabilities

    def test_detect_multilayer_anomalies(self):
        """Test multi-layer anomaly detection."""
        agent = MultiLayerAnomalyAgent()
        documents = [
            {
                "document_text": "Short text",
                "metadata": {"title": "Doc 1"},
            },
            {
                "document_text": (
                    "This is a longer document with more content " "to analyze."
                ),
                "metadata": {"title": "Doc 2"},
            },
        ]

        result = agent.detect_multilayer_anomalies(documents)

        assert "agent_id" in result
        assert "timestamp" in result
        assert "documents_analyzed" in result
        assert result["documents_analyzed"] == 2
        assert "layers" in result
        assert "structural" in result["layers"]
        assert "semantic" in result["layers"]
        assert "temporal" in result["layers"]
        assert "cross_document" in result["layers"]
        assert "total_anomalies" in result

        # Should detect at least the structural anomaly for short text
        assert result["total_anomalies"] >= 1


class TestCooperativeNegotiationAgent:
    """Tests for CooperativeNegotiationAgent."""

    def test_cooperative_agent_initialization(self):
        """Test cooperative negotiation agent initializes correctly."""
        agent = CooperativeNegotiationAgent()
        assert agent is not None
        assert agent.agent_type == "cooperative_negotiation"
        assert len(agent.capabilities) > 0
        assert "negotiate" in agent.capabilities
        assert len(agent.shared_state) == 0

    def test_negotiate_solution(self):
        """Test solution negotiation."""
        agent = CooperativeNegotiationAgent()
        problem = {
            "problem_id": "test-problem-1",
            "description": "Test problem",
        }
        peer_agents = ["agent-1", "agent-2", "agent-3"]

        result = agent.negotiate_solution(problem, peer_agents)

        assert "agent_id" in result
        assert "timestamp" in result
        assert "problem_id" in result
        assert "peer_agents" in result
        assert "rounds" in result
        assert "consensus_reached" in result
        assert "solution" in result
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_share_state_with_peers(self):
        """Test state sharing with peers."""
        agent = CooperativeNegotiationAgent()
        state_data = {"metric1": 100, "metric2": "value"}
        peer_agents = ["agent-1", "agent-2"]

        result = agent.share_state_with_peers(state_data, peer_agents)

        assert "agent_id" in result
        assert "timestamp" in result
        assert "shared_with" in result
        assert result["shared_with"] == peer_agents
        assert "state_keys" in result
        assert "status" in result
        assert result["status"] == "shared"

        # State should be updated
        assert "metric1" in agent.shared_state
        assert agent.shared_state["metric1"] == 100

    def test_build_consensus(self):
        """Test consensus building."""
        agent = CooperativeNegotiationAgent()
        proposals = [
            {"proposal_id": 1, "action": "option_a", "support": 0.8},
            {"proposal_id": 2, "action": "option_b", "support": 0.6},
            {"proposal_id": 3, "action": "option_c", "support": 0.9},
        ]

        result = agent.build_consensus(proposals)

        assert "agent_id" in result
        assert "timestamp" in result
        assert "proposals_considered" in result
        assert result["proposals_considered"] == 3
        assert "consensus_method" in result
        assert "consensus_proposal" in result
        assert "agreement_level" in result
        assert 0.0 <= result["agreement_level"] <= 1.0

    def test_escalate_to_higher_order(self):
        """Test issue escalation."""
        agent = CooperativeNegotiationAgent()
        issue = {
            "issue_id": "complex-issue-1",
            "description": "Complex problem requiring higher-order analysis",
        }

        result = agent.escalate_to_higher_order(issue, "Requires specialized expertise")

        assert "agent_id" in result
        assert "timestamp" in result
        assert "issue_id" in result
        assert "escalation_reason" in result
        assert "escalation_level" in result
        assert "status" in result
        assert result["status"] == "escalated"

    def test_operate_with_partial_info(self):
        """Test operation with partial information."""
        agent = CooperativeNegotiationAgent()

        # Test with minimal data
        minimal_data = {"field1": "value1"}
        result = agent.operate_with_partial_info(minimal_data)

        assert "agent_id" in result
        assert "timestamp" in result
        assert "data_completeness" in result
        assert "uncertainty_level" in result
        assert "can_proceed" in result
        assert "recommendations" in result
        assert 0.0 <= result["data_completeness"] <= 1.0
        assert 0.0 <= result["uncertainty_level"] <= 1.0

        # Test with complete data
        complete_data = {f"field{i}": f"value{i}" for i in range(10)}
        result_complete = agent.operate_with_partial_info(complete_data)
        assert result_complete["data_completeness"] >= 0.8
        assert result_complete["can_proceed"] is True
