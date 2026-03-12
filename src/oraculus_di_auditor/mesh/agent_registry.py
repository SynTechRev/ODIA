"""Agent Registry for Phase 10 Agent Mesh.

Manages registration, storage, and lifecycle of agent nodes in the mesh.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for managing agent nodes in the mesh.

    Handles agent registration, deregistration, status updates,
    and agent discovery.
    """

    def __init__(self):
        """Initialize agent registry."""
        self.agents: dict[str, dict[str, Any]] = {}
        self.version = "1.0.0"
        logger.info("AgentRegistry initialized")

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
            agent_name: Human-readable agent name
            agent_type: Agent type
            capabilities: List of agent capabilities
            version: Agent version
            priority: Agent priority
            max_concurrent_tasks: Maximum concurrent tasks
            metadata: Additional agent metadata

        Returns:
            Registration result with agent_id
        """
        agent_id = f"{agent_type}-{uuid4()}"

        agent_node = {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "status": "active",
            "capabilities": capabilities,
            "version": version,
            "priority": priority,
            "max_concurrent_tasks": max_concurrent_tasks,
            "current_task_count": 0,
            "registered_at": datetime.now(UTC).isoformat(),
            "last_heartbeat": datetime.now(UTC).isoformat(),
            "metadata": metadata or {},
        }

        self.agents[agent_id] = agent_node
        logger.info(f"Registered agent: {agent_id} ({agent_name})")

        return {
            "success": True,
            "agent_id": agent_id,
            "message": f"Agent {agent_name} registered successfully",
            "timestamp": agent_node["registered_at"],
        }

    def deregister_agent(self, agent_id: str) -> bool:
        """Deregister an agent from the mesh.

        Args:
            agent_id: Agent identifier

        Returns:
            True if deregistered, False otherwise
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Deregistered agent: {agent_id}")
            return True
        logger.warning(f"Agent not found for deregistration: {agent_id}")
        return False

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent information.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent information or None
        """
        return self.agents.get(agent_id)

    def get_agents_by_type(self, agent_type: str) -> list[dict[str, Any]]:
        """Get all agents of a specific type.

        Args:
            agent_type: Agent type to filter by

        Returns:
            List of matching agents
        """
        return [a for a in self.agents.values() if a["agent_type"] == agent_type]

    def get_agents_by_capability(self, capability: str) -> list[dict[str, Any]]:
        """Get all agents with a specific capability.

        Args:
            capability: Capability to filter by

        Returns:
            List of matching agents
        """
        return [
            a for a in self.agents.values() if capability in a.get("capabilities", [])
        ]

    def get_active_agents(self) -> list[dict[str, Any]]:
        """Get all active agents.

        Returns:
            List of active agents
        """
        return [a for a in self.agents.values() if a["status"] == "active"]

    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """Update agent status.

        Args:
            agent_id: Agent identifier
            status: New status (active, inactive, suspended, error)

        Returns:
            True if updated, False otherwise
        """
        if agent_id in self.agents:
            self.agents[agent_id]["status"] = status
            self.agents[agent_id]["last_heartbeat"] = datetime.now(UTC).isoformat()
            logger.info(f"Updated agent {agent_id} status to: {status}")
            return True
        logger.warning(f"Agent not found for status update: {agent_id}")
        return False

    def update_task_count(self, agent_id: str, delta: int) -> bool:
        """Update agent's current task count.

        Args:
            agent_id: Agent identifier
            delta: Change in task count (+1 for new task, -1 for completed)

        Returns:
            True if updated, False otherwise
        """
        if agent_id in self.agents:
            current = self.agents[agent_id]["current_task_count"]
            self.agents[agent_id]["current_task_count"] = max(0, current + delta)
            self.agents[agent_id]["last_heartbeat"] = datetime.now(UTC).isoformat()
            return True
        return False

    def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat timestamp.

        Args:
            agent_id: Agent identifier

        Returns:
            True if updated, False otherwise
        """
        if agent_id in self.agents:
            self.agents[agent_id]["last_heartbeat"] = datetime.now(UTC).isoformat()
            return True
        return False

    def get_registry_state(self) -> dict[str, Any]:
        """Get current state of the agent registry.

        Returns:
            Registry state summary
        """
        active_agents = self.get_active_agents()
        agents_by_type: dict[str, int] = {}

        for agent in self.agents.values():
            agent_type = agent["agent_type"]
            agents_by_type[agent_type] = agents_by_type.get(agent_type, 0) + 1

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "registry_version": self.version,
            "total_agents": len(self.agents),
            "active_agents": len(active_agents),
            "agents_by_type": agents_by_type,
        }


__all__ = ["AgentRegistry"]
