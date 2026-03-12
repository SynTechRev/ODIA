"""Routing Engine for Phase 10 Agent Mesh.

Implements intent-based routing, task scheduling, and load balancing
across the agent mesh.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class RoutingEngine:
    """Intent-based routing engine for agent mesh.

    Routes tasks to appropriate agents based on capabilities,
    load, priority, and routing policies.
    """

    def __init__(self):
        """Initialize routing engine."""
        self.routing_policy = "capability_priority"  # capability_priority, load_balance, round_robin  # noqa: E501
        self.routing_history: list[dict[str, Any]] = []
        logger.info("RoutingEngine initialized")

    def route_task(
        self,
        task: dict[str, Any],
        available_agents: list[dict[str, Any]],
        routing_policy: str | None = None,
    ) -> dict[str, Any]:
        """Route a task to an appropriate agent.

        Args:
            task: Task definition with requirements
            available_agents: List of available agents
            routing_policy: Override routing policy (optional)

        Returns:
            Routing result with selected agent
        """
        policy = routing_policy or self.routing_policy
        logger.info(f"Routing task with policy: {policy}")

        if not available_agents:
            return {
                "success": False,
                "selected_agent": None,
                "message": "No available agents",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        # Apply routing policy
        if policy == "capability_priority":
            selected = self._route_by_capability_priority(task, available_agents)
        elif policy == "load_balance":
            selected = self._route_by_load_balance(task, available_agents)
        elif policy == "round_robin":
            selected = self._route_by_round_robin(task, available_agents)
        else:
            selected = self._route_by_capability_priority(task, available_agents)

        # Record routing decision
        routing_record = {
            "task_id": task.get("task_id", "unknown"),
            "selected_agent": selected.get("agent_id") if selected else None,
            "policy": policy,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.routing_history.append(routing_record)

        return {
            "success": selected is not None,
            "selected_agent": selected.get("agent_id") if selected else None,
            "agent_info": selected,
            "policy_used": policy,
            "timestamp": routing_record["timestamp"],
        }

    def _route_by_capability_priority(
        self,
        task: dict[str, Any],
        agents: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Route based on capability matching and agent priority."""
        required_capabilities = task.get("capabilities", [])

        # Filter agents by capabilities
        capable_agents = []
        for agent in agents:
            if agent["status"] != "active":
                continue
            agent_caps = agent.get("capabilities", [])
            if all(cap in agent_caps for cap in required_capabilities):
                capable_agents.append(agent)

        if not capable_agents:
            logger.warning("No capable agents found for task")
            return None

        # Sort by priority (higher first) and load (lower first)
        capable_agents.sort(
            key=lambda a: (
                -a.get("priority", 0),
                a.get("current_task_count", 0) / a.get("max_concurrent_tasks", 1),
            )
        )

        return capable_agents[0]

    def _route_by_load_balance(
        self,
        task: dict[str, Any],
        agents: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Route based on current load balancing."""
        active_agents = [a for a in agents if a["status"] == "active"]

        if not active_agents:
            return None

        # Calculate load percentage for each agent (without mutating input)
        agents_with_load = []
        for agent in active_agents:
            current = agent.get("current_task_count", 0)
            max_tasks = agent.get("max_concurrent_tasks", 1)
            load_percentage = (current / max_tasks * 100) if max_tasks > 0 else 100
            agent_copy = agent.copy()
            agent_copy["load_percentage"] = load_percentage
            agents_with_load.append(agent_copy)

        # Sort by load (lowest first)
        agents_with_load.sort(key=lambda a: a["load_percentage"])

        return agents_with_load[0]

    def _route_by_round_robin(
        self,
        task: dict[str, Any],
        agents: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Route using round-robin selection."""
        active_agents = [a for a in agents if a["status"] == "active"]

        if not active_agents:
            return None

        # Simple round-robin based on routing history length
        index = len(self.routing_history) % len(active_agents)
        return active_agents[index]

    def schedule_tasks(
        self,
        tasks: list[dict[str, Any]],
        agents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Schedule multiple tasks across agents.

        Args:
            tasks: List of tasks to schedule
            agents: List of available agents

        Returns:
            Schedule with task-agent assignments
        """
        logger.info(f"Scheduling {len(tasks)} tasks across {len(agents)} agents")

        schedule = []
        for task in tasks:
            routing_result = self.route_task(task, agents)
            if routing_result["success"]:
                schedule.append(
                    {
                        "task_id": task.get("task_id", "unknown"),
                        "agent_id": routing_result["selected_agent"],
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

        return {
            "success": True,
            "schedule": schedule,
            "tasks_scheduled": len(schedule),
            "tasks_failed": len(tasks) - len(schedule),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def get_routing_stats(self) -> dict[str, Any]:
        """Get routing statistics.

        Returns:
            Routing statistics and metrics
        """
        total_routes = len(self.routing_history)
        if total_routes == 0:
            return {
                "total_routes": 0,
                "routes_by_agent": {},
                "routes_by_policy": {},
            }

        # Count routes by agent
        routes_by_agent: dict[str, int] = {}
        for record in self.routing_history:
            agent_id = record.get("selected_agent", "unknown")
            routes_by_agent[agent_id] = routes_by_agent.get(agent_id, 0) + 1

        # Count routes by policy
        routes_by_policy: dict[str, int] = {}
        for record in self.routing_history:
            policy = record.get("policy", "unknown")
            routes_by_policy[policy] = routes_by_policy.get(policy, 0) + 1

        return {
            "total_routes": total_routes,
            "routes_by_agent": routes_by_agent,
            "routes_by_policy": routes_by_policy,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def set_routing_policy(self, policy: str) -> bool:
        """Set default routing policy.

        Args:
            policy: Routing policy (capability_priority, load_balance, round_robin)

        Returns:
            True if set successfully
        """
        valid_policies = ["capability_priority", "load_balance", "round_robin"]
        if policy not in valid_policies:
            logger.error(f"Invalid routing policy: {policy}")
            return False

        self.routing_policy = policy
        logger.info(f"Routing policy set to: {policy}")
        return True


__all__ = ["RoutingEngine"]
