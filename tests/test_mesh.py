"""Tests for Phase 10 Agent Mesh components."""

from __future__ import annotations


class TestAgentTypes:
    """Tests for Agent Types."""

    def test_sentinel_agent_initialization(self):
        """Test SentinelAgent can be initialized."""
        from oraculus_di_auditor.mesh import SentinelAgent

        agent = SentinelAgent()
        assert agent is not None
        assert agent.agent_type == "sentinel"
        assert "monitor" in agent.capabilities

    def test_constraint_agent_initialization(self):
        """Test ConstraintAgent can be initialized."""
        from oraculus_di_auditor.mesh import ConstraintAgent

        agent = ConstraintAgent()
        assert agent is not None
        assert agent.agent_type == "constraint"
        assert "validate" in agent.capabilities

    def test_routing_agent_initialization(self):
        """Test RoutingAgent can be initialized."""
        from oraculus_di_auditor.mesh import RoutingAgent

        agent = RoutingAgent()
        assert agent is not None
        assert agent.agent_type == "routing"
        assert "route" in agent.capabilities

    def test_synthesis_agent_initialization(self):
        """Test SynthesisAgent can be initialized."""
        from oraculus_di_auditor.mesh import SynthesisAgent

        agent = SynthesisAgent()
        assert agent is not None
        assert agent.agent_type == "synthesis"
        assert "merge" in agent.capabilities

    def test_agent_execute_task(self):
        """Test agent task execution."""
        from oraculus_di_auditor.mesh import SentinelAgent

        agent = SentinelAgent()
        task = {"type": "monitor", "invariants": []}
        result = agent.execute_task(task)

        assert "status" in result
        assert result["status"] == "success"

    def test_agent_get_info(self):
        """Test getting agent info."""
        from oraculus_di_auditor.mesh import ConstraintAgent

        agent = ConstraintAgent()
        info = agent.get_info()

        assert "agent_id" in info
        assert "agent_name" in info
        assert "agent_type" in info
        assert "version" in info
        assert "capabilities" in info


class TestAgentRegistry:
    """Tests for AgentRegistry."""

    def test_registry_initialization(self):
        """Test AgentRegistry initialization."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        assert registry is not None
        assert registry.version == "1.0.0"

    def test_register_agent(self):
        """Test registering a new agent."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        result = registry.register_agent(
            agent_name="TestAgent",
            agent_type="specialist",
            capabilities=["test"],
            version="1.0.0",
        )

        assert result["success"] is True
        assert "agent_id" in result
        assert "timestamp" in result

    def test_get_agent(self):
        """Test retrieving an agent."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        result = registry.register_agent(
            agent_name="TestAgent",
            agent_type="specialist",
            capabilities=["test"],
            version="1.0.0",
        )

        agent_id = result["agent_id"]
        agent = registry.get_agent(agent_id)
        assert agent is not None
        assert agent["agent_id"] == agent_id

    def test_deregister_agent(self):
        """Test deregistering an agent."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        result = registry.register_agent(
            agent_name="TestAgent",
            agent_type="specialist",
            capabilities=["test"],
            version="1.0.0",
        )

        agent_id = result["agent_id"]
        success = registry.deregister_agent(agent_id)
        assert success is True
        assert registry.get_agent(agent_id) is None

    def test_get_agents_by_type(self):
        """Test retrieving agents by type."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        registry.register_agent(
            agent_name="Agent1",
            agent_type="sentinel",
            capabilities=[],
            version="1.0.0",
        )
        registry.register_agent(
            agent_name="Agent2",
            agent_type="sentinel",
            capabilities=[],
            version="1.0.0",
        )

        agents = registry.get_agents_by_type("sentinel")
        assert len(agents) >= 2

    def test_get_agents_by_capability(self):
        """Test retrieving agents by capability."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        registry.register_agent(
            agent_name="CapableAgent",
            agent_type="specialist",
            capabilities=["analyze", "transform"],
            version="1.0.0",
        )

        agents = registry.get_agents_by_capability("analyze")
        assert len(agents) > 0

    def test_update_agent_status(self):
        """Test updating agent status."""
        from oraculus_di_auditor.mesh import AgentRegistry

        registry = AgentRegistry()
        result = registry.register_agent(
            agent_name="TestAgent",
            agent_type="specialist",
            capabilities=[],
            version="1.0.0",
        )

        agent_id = result["agent_id"]
        success = registry.update_agent_status(agent_id, "inactive")
        assert success is True

        agent = registry.get_agent(agent_id)
        assert agent["status"] == "inactive"


class TestRoutingEngine:
    """Tests for RoutingEngine."""

    def test_routing_engine_initialization(self):
        """Test RoutingEngine initialization."""
        from oraculus_di_auditor.mesh import RoutingEngine

        engine = RoutingEngine()
        assert engine is not None
        assert engine.routing_policy == "capability_priority"

    def test_route_task_no_agents(self):
        """Test routing when no agents available."""
        from oraculus_di_auditor.mesh import RoutingEngine

        engine = RoutingEngine()
        task = {"task_id": "test", "capabilities": []}
        result = engine.route_task(task, [])

        assert result["success"] is False
        assert result["selected_agent"] is None

    def test_route_task_with_capability_match(self):
        """Test routing with capability matching."""
        from oraculus_di_auditor.mesh import RoutingEngine

        engine = RoutingEngine()
        task = {"task_id": "test", "capabilities": ["analyze"]}
        agents = [
            {
                "agent_id": "agent1",
                "status": "active",
                "capabilities": ["analyze", "transform"],
                "priority": 10,
                "current_task_count": 0,
                "max_concurrent_tasks": 10,
            }
        ]

        result = engine.route_task(task, agents)
        assert result["success"] is True
        assert result["selected_agent"] == "agent1"

    def test_set_routing_policy(self):
        """Test setting routing policy."""
        from oraculus_di_auditor.mesh import RoutingEngine

        engine = RoutingEngine()
        success = engine.set_routing_policy("load_balance")
        assert success is True
        assert engine.routing_policy == "load_balance"

    def test_schedule_tasks(self):
        """Test scheduling multiple tasks."""
        from oraculus_di_auditor.mesh import RoutingEngine

        engine = RoutingEngine()
        tasks = [
            {"task_id": "task1", "capabilities": []},
            {"task_id": "task2", "capabilities": []},
        ]
        agents = [
            {
                "agent_id": "agent1",
                "status": "active",
                "capabilities": [],
                "priority": 10,
                "current_task_count": 0,
                "max_concurrent_tasks": 10,
            }
        ]

        result = engine.schedule_tasks(tasks, agents)
        assert result["success"] is True
        assert "schedule" in result


class TestSynthesisEngine:
    """Tests for SynthesisEngine."""

    def test_synthesis_engine_initialization(self):
        """Test SynthesisEngine initialization."""
        from oraculus_di_auditor.mesh import SynthesisEngine

        engine = SynthesisEngine()
        assert engine is not None

    def test_synthesize_no_results(self):
        """Test synthesis with no results."""
        from oraculus_di_auditor.mesh import SynthesisEngine

        engine = SynthesisEngine()
        result = engine.synthesize_results([])

        assert result["success"] is False

    def test_synthesize_merge_strategy(self):
        """Test synthesis with merge strategy."""
        from oraculus_di_auditor.mesh import SynthesisEngine

        engine = SynthesisEngine()
        results = [
            {"agent_id": "agent1", "result": {"key1": "value1"}},
            {"agent_id": "agent2", "result": {"key2": "value2"}},
        ]

        result = engine.synthesize_results(results, "merge")
        assert result["success"] is True
        assert "synthesized_result" in result

    def test_synthesize_harmonize_strategy(self):
        """Test synthesis with harmonize strategy."""
        from oraculus_di_auditor.mesh import SynthesisEngine

        engine = SynthesisEngine()
        results = [
            {"agent_id": "agent1", "result": {"key": "value1"}},
            {"agent_id": "agent2", "result": {"key": "value2"}},
        ]

        result = engine.synthesize_results(results, "harmonize")
        assert result["success"] is True


class TestMeshCoordinator:
    """Tests for MeshCoordinator."""

    def test_mesh_coordinator_initialization(self):
        """Test MeshCoordinator initialization."""
        from oraculus_di_auditor.mesh import MeshCoordinator

        coordinator = MeshCoordinator()
        assert coordinator is not None
        assert coordinator.version == "1.0.0"

    def test_register_agent_through_coordinator(self):
        """Test registering agent through coordinator."""
        from oraculus_di_auditor.mesh import MeshCoordinator

        coordinator = MeshCoordinator()
        result = coordinator.register_agent(
            agent_name="CoordinatorAgent",
            agent_type="specialist",
            capabilities=["test"],
            version="1.0.0",
        )

        assert result["success"] is True
        assert "agent_id" in result

    def test_execute_mesh_job(self):
        """Test executing a mesh job."""
        from oraculus_di_auditor.mesh import MeshCoordinator

        coordinator = MeshCoordinator()
        result = coordinator.execute_mesh_job(
            job_type="analysis",
            documents=[{"document_text": "test", "metadata": {}}],
        )

        assert result["success"] is True
        assert "job_id" in result
        assert result["status"] == "completed"

    def test_get_mesh_graph(self):
        """Test getting mesh connectivity graph."""
        from oraculus_di_auditor.mesh import MeshCoordinator

        coordinator = MeshCoordinator()
        graph = coordinator.get_mesh_graph()

        assert "timestamp" in graph
        assert "node_count" in graph
        assert "link_count" in graph
        assert "nodes" in graph
        assert "links" in graph

    def test_get_mesh_state(self):
        """Test getting mesh state."""
        from oraculus_di_auditor.mesh import MeshCoordinator

        coordinator = MeshCoordinator()
        state = coordinator.get_mesh_state()

        assert "timestamp" in state
        assert "coordinator_version" in state
        assert "total_agents" in state
        assert "active_agents" in state
        assert "health" in state


__all__ = [
    "TestAgentTypes",
    "TestAgentRegistry",
    "TestRoutingEngine",
    "TestSynthesisEngine",
    "TestMeshCoordinator",
]
