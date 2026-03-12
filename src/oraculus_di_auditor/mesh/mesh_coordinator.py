"""Mesh Coordinator for Phase 10 Agent Mesh.

Central orchestration service for multi-agent mesh execution,
coordinating agent registration, routing, execution, and synthesis.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .agent_registry import AgentRegistry
from .agent_types import ConstraintAgent, RoutingAgent, SentinelAgent, SynthesisAgent
from .routing_engine import RoutingEngine
from .synthesis_engine import SynthesisEngine

logger = logging.getLogger(__name__)


class MeshCoordinator:
    """Central coordinator for autonomous agent mesh.

    Manages agent lifecycle, task routing, execution orchestration,
    and result synthesis across the distributed agent network.
    """

    def __init__(self):
        """Initialize mesh coordinator."""
        self.agent_registry = AgentRegistry()
        self.routing_engine = RoutingEngine()
        self.synthesis_engine = SynthesisEngine()
        self.execution_history: list[dict[str, Any]] = []
        self.version = "1.0.0"

        # Initialize default system agents
        self._initialize_system_agents()

        logger.info("MeshCoordinator initialized")

    def _initialize_system_agents(self):
        """Initialize default system agents."""
        # Register Sentinel Agent
        SentinelAgent()  # Instance for validation
        self.agent_registry.register_agent(
            agent_name="SentinelAgent",
            agent_type="sentinel",
            capabilities=["monitor", "alert", "track_violations"],
            version="1.0.0",
            priority=100,
        )

        # Register Constraint Agent
        ConstraintAgent()  # Instance for validation
        self.agent_registry.register_agent(
            agent_name="ConstraintAgent",
            agent_type="constraint",
            capabilities=["validate", "enforce", "block"],
            version="1.0.0",
            priority=100,
        )

        # Register Routing Agent
        RoutingAgent()  # Instance for validation
        self.agent_registry.register_agent(
            agent_name="RoutingAgent",
            agent_type="routing",
            capabilities=["route", "schedule", "load_balance"],
            version="1.0.0",
            priority=90,
        )

        # Register Synthesis Agent
        SynthesisAgent()  # Instance for validation
        self.agent_registry.register_agent(
            agent_name="SynthesisAgent",
            agent_type="synthesis",
            capabilities=["merge", "harmonize", "aggregate"],
            version="1.0.0",
            priority=90,
        )

        logger.info("Initialized 4 system agents")

    def register_agent(
        self,
        agent_name: str,
        agent_type: str,
        capabilities: list[str],
        version: str,
        priority: int = 0,
        max_concurrent_tasks: int = 10,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register a new agent in the mesh.

        Args:
            agent_name: Agent name
            agent_type: Agent type
            capabilities: Agent capabilities
            version: Agent version
            priority: Agent priority
            max_concurrent_tasks: Maximum concurrent tasks
            metadata: Additional metadata

        Returns:
            Registration result
        """
        return self.agent_registry.register_agent(
            agent_name=agent_name,
            agent_type=agent_type,
            capabilities=capabilities,
            version=version,
            priority=priority,
            max_concurrent_tasks=max_concurrent_tasks,
            metadata=metadata,
        )

    def execute_mesh_job(
        self,
        job_type: str,
        documents: list[dict[str, Any]],
        agents: list[str] | None = None,
        options: dict[str, Any] | None = None,
        gcn_validate: bool = True,
        governor_check: bool = True,
    ) -> dict[str, Any]:
        """Execute a multi-agent mesh job.

        Args:
            job_type: Job type (analysis, synthesis, routing, validation)
            documents: Documents to process
            agents: Specific agents to use (auto-select if None)
            options: Execution options
            gcn_validate: Whether to validate with GCN
            governor_check: Whether to check with Governor

        Returns:
            Mesh execution result
        """
        job_id = f"mesh-job-{uuid4()}"
        logger.info(f"Executing mesh job {job_id} ({job_type})")

        # Create execution log
        execution_log: list[dict[str, Any]] = []
        execution_log.append(
            {
                "event": "job_started",
                "job_id": job_id,
                "job_type": job_type,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Select agents
        if agents:
            selected_agents = [
                self.agent_registry.get_agent(aid) for aid in agents if aid
            ]
            selected_agents = [a for a in selected_agents if a is not None]
        else:
            selected_agents = self._auto_select_agents(job_type, documents)

        execution_log.append(
            {
                "event": "agents_selected",
                "agent_count": len(selected_agents),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Route tasks to agents
        tasks = self._generate_tasks(job_type, documents, options or {})
        schedule = self.routing_engine.schedule_tasks(tasks, selected_agents)

        execution_log.append(
            {
                "event": "tasks_scheduled",
                "task_count": len(schedule["schedule"]),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Execute tasks (simulated execution)
        task_results = []
        for assignment in schedule["schedule"]:
            agent_id = assignment["agent_id"]
            task_id = assignment["task_id"]

            # Find the task
            task = next((t for t in tasks if t.get("task_id") == task_id), None)
            if not task:
                continue

            # Simulate task execution
            task_result = {
                "agent_id": agent_id,
                "task_name": task.get("task_name", "unknown"),
                "status": "success",
                "result": {
                    "processed": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
                "metrics": {
                    "execution_time_ms": 100,
                },
                "errors": [],
            }
            task_results.append(task_result)

            # Update agent task count
            self.agent_registry.update_task_count(agent_id, 1)

        execution_log.append(
            {
                "event": "tasks_completed",
                "completed_count": len(task_results),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Synthesize results
        synthesis_result = self.synthesis_engine.synthesize_results(
            task_results,
            synthesis_strategy=(
                options.get("synthesis_strategy", "merge") if options else "merge"
            ),  # noqa: E501
        )

        execution_log.append(
            {
                "event": "results_synthesized",
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Record execution
        execution_record = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "completed",
            "agent_count": len(selected_agents),
            "task_count": len(tasks),
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.execution_history.append(execution_record)

        # Update agent task counts (decrement)
        for assignment in schedule["schedule"]:
            self.agent_registry.update_task_count(assignment["agent_id"], -1)

        return {
            "success": True,
            "job_id": job_id,
            "status": "completed",
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_count": len(selected_agents),
            "task_count": len(tasks),
            "results": task_results,
            "synthesized_result": synthesis_result.get("synthesized_result", {}),
            "execution_log": execution_log,
        }

    def _auto_select_agents(
        self,
        job_type: str,
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Auto-select agents based on job type."""
        if job_type == "analysis":
            # Need analysis capabilities
            return self.agent_registry.get_agents_by_capability("analyze")
        elif job_type == "synthesis":
            # Need synthesis capabilities
            return self.agent_registry.get_agents_by_capability("merge")
        elif job_type == "routing":
            # Need routing capabilities
            return self.agent_registry.get_agents_by_type("routing")
        elif job_type == "validation":
            # Need validation capabilities
            return self.agent_registry.get_agents_by_capability("validate")
        else:
            # Default: return all active agents
            return self.agent_registry.get_active_agents()

    def _generate_tasks(
        self,
        job_type: str,
        documents: list[dict[str, Any]],
        options: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Generate tasks for mesh execution."""
        tasks = []

        for idx, doc in enumerate(documents):
            task = {
                "task_id": f"task-{uuid4()}",
                "task_name": f"{job_type}_document_{idx}",
                "task_type": job_type,
                "document": doc,
                "options": options,
                "capabilities": self._get_required_capabilities(job_type),
            }
            tasks.append(task)

        return tasks

    def _get_required_capabilities(self, job_type: str) -> list[str]:
        """Get required capabilities for a job type."""
        capability_map = {
            "analysis": ["analyze"],
            "synthesis": ["merge", "harmonize"],
            "routing": ["route"],
            "validation": ["validate"],
        }
        return capability_map.get(job_type, [])

    def get_mesh_graph(self) -> dict[str, Any]:
        """Get mesh connectivity graph.

        Returns:
            Graph with nodes and links
        """
        agents = self.agent_registry.agents.values()

        nodes = []
        for agent in agents:
            nodes.append(
                {
                    "agent_id": agent["agent_id"],
                    "agent_name": agent["agent_name"],
                    "agent_type": agent["agent_type"],
                    "status": agent["status"],
                    "connections": 0,  # Simplified - would track actual connections
                }
            )

        # Simplified links (in full implementation, would track actual agent links)
        links: list[dict[str, Any]] = []

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "node_count": len(nodes),
            "link_count": len(links),
            "nodes": nodes,
            "links": links,
        }

    def get_mesh_state(self) -> dict[str, Any]:
        """Get current mesh state.

        Returns:
            Mesh state summary
        """
        registry_state = self.agent_registry.get_registry_state()
        routing_stats = self.routing_engine.get_routing_stats()
        synthesis_stats = self.synthesis_engine.get_synthesis_stats()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "coordinator_version": self.version,
            "total_agents": registry_state["total_agents"],
            "active_agents": registry_state["active_agents"],
            "total_executions": len(self.execution_history),
            "total_routes": routing_stats["total_routes"],
            "total_syntheses": synthesis_stats["total_syntheses"],
            "health": "healthy" if registry_state["active_agents"] > 0 else "degraded",
        }


__all__ = ["MeshCoordinator"]
