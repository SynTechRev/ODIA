"""Adaptive Mesh Intelligence for Phase 11.

Extends Phase 10 mesh with adaptive, self-rebalancing, and fault-tolerant
capabilities.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# Performance score weights
SUCCESS_WEIGHT = 0.7
RESPONSE_WEIGHT = 0.3


class AdaptiveMeshIntelligence:
    """Adaptive intelligence layer for agent mesh.

    Capabilities:
    - Dynamic load balancing
    - Agent promotion/demotion based on performance
    - Self-rebalancing routing
    - Temporary micro-agent spawning
    - Fault-tolerant execution
    - Workload prediction and optimization
    """

    def __init__(self, mesh_coordinator=None):
        """Initialize adaptive mesh intelligence.

        Args:
            mesh_coordinator: Reference to MeshCoordinator (optional)
        """
        self.mesh_coordinator = mesh_coordinator
        self.performance_metrics: dict[str, dict[str, Any]] = {}
        self.load_history: list[dict[str, Any]] = []
        self.rebalancing_events: list[dict[str, Any]] = []
        self.micro_agents: list[dict[str, Any]] = []

        # Adaptive thresholds
        self.load_threshold_high = 0.8  # 80% capacity
        self.load_threshold_low = 0.3  # 30% capacity
        self.performance_threshold = 0.7  # 70% success rate
        self.rebalance_interval_seconds = 300  # 5 minutes

        logger.info("AdaptiveMeshIntelligence initialized")

    def analyze_mesh_load(self) -> dict[str, Any]:
        """Analyze current mesh load distribution.

        Returns:
            Load analysis report
        """
        logger.info("Analyzing mesh load distribution")

        if not self.mesh_coordinator:
            return {
                "status": "error",
                "message": "No mesh coordinator configured",
            }

        # Get all agents from registry
        agents = self.mesh_coordinator.agent_registry.get_all_agents()

        load_analysis = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_agents": len(agents),
            "agents_overloaded": 0,
            "agents_underutilized": 0,
            "agents_balanced": 0,
            "overall_load": 0.0,
            "recommendations": [],
        }

        total_load = 0.0
        for agent in agents:
            current_tasks = agent.get("current_task_count", 0)
            max_tasks = agent.get("max_concurrent_tasks", 10)

            if max_tasks > 0:
                agent_load = current_tasks / max_tasks
                total_load += agent_load

                if agent_load >= self.load_threshold_high:
                    load_analysis["agents_overloaded"] += 1
                    load_analysis["recommendations"].append(
                        {
                            "agent_id": agent.get("agent_id"),
                            "action": "scale_out",
                            "reason": f"Load at {agent_load:.0%}",
                        }
                    )
                elif agent_load <= self.load_threshold_low:
                    load_analysis["agents_underutilized"] += 1
                    load_analysis["recommendations"].append(
                        {
                            "agent_id": agent.get("agent_id"),
                            "action": "consider_scale_in",
                            "reason": f"Load at {agent_load:.0%}",
                        }
                    )
                else:
                    load_analysis["agents_balanced"] += 1

        if load_analysis["total_agents"] > 0:
            load_analysis["overall_load"] = total_load / load_analysis["total_agents"]

        # Record load history
        self.load_history.append(
            {
                "timestamp": load_analysis["timestamp"],
                "overall_load": load_analysis["overall_load"],
                "agents_overloaded": load_analysis["agents_overloaded"],
            }
        )

        logger.info(
            f"Load analysis complete: {load_analysis['overall_load']:.0%} overall, "
            f"{len(load_analysis['recommendations'])} recommendations"
        )

        return load_analysis

    def evaluate_agent_performance(self, agent_id: str) -> dict[str, Any]:
        """Evaluate performance of a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Performance evaluation
        """
        logger.info(f"Evaluating agent performance: {agent_id}")

        if agent_id not in self.performance_metrics:
            self.performance_metrics[agent_id] = {
                "tasks_completed": 0,
                "tasks_failed": 0,
                "avg_response_time": 0.0,
                "last_evaluation": datetime.now(UTC).isoformat(),
            }

        metrics = self.performance_metrics[agent_id]
        total_tasks = metrics["tasks_completed"] + metrics["tasks_failed"]

        evaluation = {
            "agent_id": agent_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "success_rate": (
                metrics["tasks_completed"] / total_tasks if total_tasks > 0 else 1.0
            ),
            "total_tasks": total_tasks,
            "avg_response_time": metrics["avg_response_time"],
            "performance_score": 0.0,
            "recommendation": "maintain",
        }

        # Calculate performance score (0.0 - 1.0)
        success_component = evaluation["success_rate"]
        # Response time component (assume 1000ms is baseline, lower is better)
        response_component = max(0.0, 1.0 - (metrics["avg_response_time"] / 1000.0))
        evaluation["performance_score"] = (
            success_component * SUCCESS_WEIGHT + response_component * RESPONSE_WEIGHT
        )

        # Make recommendation
        if evaluation["performance_score"] >= 0.85:
            evaluation["recommendation"] = "promote"
        elif evaluation["performance_score"] < self.performance_threshold:
            evaluation["recommendation"] = "demote"
        logger.info(
            "Agent %s performance: %.2f - %s",
            agent_id,
            evaluation["performance_score"],
            evaluation["recommendation"],
        )

        return evaluation

    def rebalance_mesh(self, force: bool = False) -> dict[str, Any]:
        """Rebalance agent mesh based on load and performance.

        Args:
            force: Force rebalancing even if thresholds not met

        Returns:
            Rebalancing report
        """
        logger.info(f"Rebalancing mesh (force={force})")

        load_analysis = self.analyze_mesh_load()

        # Handle error case
        if load_analysis.get("status") == "error":
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "action_taken": False,
                "reason": load_analysis.get("message", "Error analyzing load"),
            }

        rebalancing_actions = []

        # Check if rebalancing is needed
        needs_rebalancing = (
            force
            or load_analysis.get("agents_overloaded", 0) > 0
            or load_analysis.get("overall_load", 0.0) > self.load_threshold_high
        )

        if not needs_rebalancing:
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "action_taken": False,
                "reason": "Mesh is balanced",
                "load_analysis": load_analysis,
            }

        # Execute rebalancing recommendations
        recommendations = load_analysis.get("recommendations", [])
        for recommendation in recommendations:
            if recommendation.get("action") == "scale_out":
                # Spawn micro-agent to help overloaded agent
                micro_agent = self._spawn_micro_agent(
                    recommendation.get("agent_id", "unknown"), "load_balancing"
                )
                rebalancing_actions.append(
                    {
                        "action": "spawned_micro_agent",
                        "micro_agent_id": micro_agent["agent_id"],
                        "parent_agent": recommendation.get("agent_id", "unknown"),
                    }
                )

        rebalancing_report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action_taken": True,
            "actions_executed": len(rebalancing_actions),
            "actions": rebalancing_actions,
            "load_before": load_analysis.get("overall_load", 0.0),
        }

        # Record rebalancing event
        self.rebalancing_events.append(rebalancing_report)

        logger.info(f"Mesh rebalanced: {len(rebalancing_actions)} actions executed")

        return rebalancing_report

    def promote_agent(self, agent_id: str, reason: str) -> dict[str, Any]:
        """Promote an agent to higher priority.

        Args:
            agent_id: Agent to promote
            reason: Reason for promotion

        Returns:
            Promotion result
        """
        logger.info(f"Promoting agent {agent_id}: {reason}")

        if not self.mesh_coordinator:
            return {"status": "error", "message": "No mesh coordinator"}

        # Get current agent info
        agent_info = self.mesh_coordinator.agent_registry.get_agent(agent_id)
        if not agent_info:
            return {"status": "error", "message": "Agent not found"}

        current_priority = agent_info.get("priority", 0)
        new_priority = current_priority + 10  # Increase priority

        # Update agent priority (would need to add this method to registry)
        promotion = {
            "agent_id": agent_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "promote",
            "priority_before": current_priority,
            "priority_after": new_priority,
            "reason": reason,
            "status": "simulated",  # In production, would actually update
        }

        logger.info(
            f"Agent promoted: {agent_id} priority {current_priority} → {new_priority}"
        )

        return promotion

    def demote_agent(self, agent_id: str, reason: str) -> dict[str, Any]:
        """Demote an agent to lower priority.

        Args:
            agent_id: Agent to demote
            reason: Reason for demotion

        Returns:
            Demotion result
        """
        logger.info(f"Demoting agent {agent_id}: {reason}")

        if not self.mesh_coordinator:
            return {"status": "error", "message": "No mesh coordinator"}

        agent_info = self.mesh_coordinator.agent_registry.get_agent(agent_id)
        if not agent_info:
            return {"status": "error", "message": "Agent not found"}

        current_priority = agent_info.get("priority", 0)
        new_priority = max(0, current_priority - 10)  # Decrease priority

        demotion = {
            "agent_id": agent_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "demote",
            "priority_before": current_priority,
            "priority_after": new_priority,
            "reason": reason,
            "status": "simulated",
        }

        logger.info(
            f"Agent demoted: {agent_id} priority {current_priority} → {new_priority}"
        )

        return demotion

    def _spawn_micro_agent(self, parent_agent_id: str, purpose: str) -> dict[str, Any]:
        """Spawn a temporary micro-agent for specialized tasks.

        Args:
            parent_agent_id: Parent agent ID
            purpose: Purpose of micro-agent

        Returns:
            Micro-agent info
        """
        micro_agent_id = f"micro-{uuid4().hex[:8]}"

        micro_agent = {
            "agent_id": micro_agent_id,
            "agent_type": "micro",
            "parent_agent": parent_agent_id,
            "purpose": purpose,
            "spawned_at": datetime.now(UTC).isoformat(),
            "ttl_seconds": 3600,  # 1 hour TTL
            "status": "active",
        }

        self.micro_agents.append(micro_agent)

        logger.info(
            f"Spawned micro-agent {micro_agent_id} for {parent_agent_id} ({purpose})"
        )

        return micro_agent

    def cleanup_micro_agents(self) -> dict[str, Any]:
        """Cleanup expired micro-agents.

        Returns:
            Cleanup report
        """
        logger.info("Cleaning up expired micro-agents")

        current_time = datetime.now(UTC)
        cleaned = 0

        for micro_agent in list(self.micro_agents):
            spawned_at = datetime.fromisoformat(micro_agent["spawned_at"])
            age_seconds = (current_time - spawned_at).total_seconds()

            if age_seconds > micro_agent["ttl_seconds"]:
                self.micro_agents.remove(micro_agent)
                cleaned += 1
                logger.info(f"Cleaned up micro-agent {micro_agent['agent_id']}")

        return {
            "timestamp": current_time.isoformat(),
            "cleaned_count": cleaned,
            "active_micro_agents": len(self.micro_agents),
        }

    def get_adaptive_state(self) -> dict[str, Any]:
        """Get current state of adaptive mesh intelligence.

        Returns:
            Adaptive mesh state
        """
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "active_micro_agents": len(self.micro_agents),
            "rebalancing_events": len(self.rebalancing_events),
            "load_history_size": len(self.load_history),
            "agents_tracked": len(self.performance_metrics),
            "thresholds": {
                "load_high": self.load_threshold_high,
                "load_low": self.load_threshold_low,
                "performance": self.performance_threshold,
            },
            "recent_load_history": (
                self.load_history[-5:] if len(self.load_history) > 0 else []
            ),
        }
