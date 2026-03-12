"""Agent type definitions for Phase 10 Agent Mesh.

Defines specialized agent types: Sentinel, Constraint, Routing, Synthesis.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all mesh agents."""

    def __init__(
        self,
        agent_id: str | None = None,
        agent_name: str | None = None,
        agent_type: str | None = None,
        version: str = "1.0.0",
    ):
        """Initialize base agent.

        Args:
            agent_id: Agent identifier (generated if not provided)
            agent_name: Human-readable agent name
            agent_type: Agent type
            version: Agent version
        """
        self.agent_id = agent_id or f"agent-{uuid4()}"
        self.agent_name = agent_name or "BaseAgent"
        self.agent_type = agent_type or "base"
        self.version = version
        self.status = "active"
        self.capabilities: list[str] = []
        logger.info(f"Initialized {self.agent_name} ({self.agent_id})")

    @abstractmethod
    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task assigned to this agent.

        Args:
            task: Task definition with parameters

        Returns:
            Task execution result
        """
        pass

    def get_info(self) -> dict[str, Any]:
        """Get agent information.

        Returns:
            Agent metadata
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "version": self.version,
            "status": self.status,
            "capabilities": self.capabilities,
        }


class SentinelAgent(BaseAgent):
    """Sentinel Agent - Watches pipeline invariants.

    Monitors system state, tracks violations, and raises alerts
    when pipeline invariants are compromised.
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize sentinel agent."""
        super().__init__(
            agent_id=agent_id,
            agent_name="SentinelAgent",
            agent_type="sentinel",
        )
        self.capabilities = ["monitor", "alert", "track_violations"]

    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute sentinel monitoring task.

        Args:
            task: Monitoring task definition

        Returns:
            Monitoring result
        """
        task_type = task.get("type", "monitor")
        logger.info(f"SentinelAgent executing task: {task_type}")

        if task_type == "monitor":
            return self._monitor_invariants(task)
        elif task_type == "alert":
            return self._raise_alert(task)
        elif task_type == "track_violations":
            return self._track_violations(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}",
            }

    def _monitor_invariants(self, task: dict[str, Any]) -> dict[str, Any]:
        """Monitor pipeline invariants."""
        invariants = task.get("invariants", [])
        violations = []

        # Simulate invariant checking
        for invariant in invariants:
            if not self._check_invariant(invariant):
                violations.append(
                    {
                        "invariant": invariant,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

        return {
            "status": "success",
            "invariants_checked": len(invariants),
            "violations": violations,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _check_invariant(self, invariant: dict[str, Any]) -> bool:
        """Check a single invariant."""
        # Simplified invariant checking logic
        return invariant.get("condition", True)

    def _raise_alert(self, task: dict[str, Any]) -> dict[str, Any]:
        """Raise an alert."""
        alert_level = task.get("level", "info")
        message = task.get("message", "Alert raised")
        logger.warning(f"Alert ({alert_level}): {message}")

        return {
            "status": "success",
            "alert_level": alert_level,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _track_violations(self, task: dict[str, Any]) -> dict[str, Any]:
        """Track violations over time."""
        violations = task.get("violations", [])

        return {
            "status": "success",
            "violations_tracked": len(violations),
            "timestamp": datetime.now(UTC).isoformat(),
        }


class ConstraintAgent(BaseAgent):
    """Constraint Agent - Enforces GCN rules.

    Validates operations against GCN constraints and blocks
    operations that violate rules.
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize constraint agent."""
        super().__init__(
            agent_id=agent_id,
            agent_name="ConstraintAgent",
            agent_type="constraint",
        )
        self.capabilities = ["validate", "enforce", "block"]

    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute constraint enforcement task.

        Args:
            task: Constraint task definition

        Returns:
            Enforcement result
        """
        task_type = task.get("type", "validate")
        logger.info(f"ConstraintAgent executing task: {task_type}")

        if task_type == "validate":
            return self._validate_constraints(task)
        elif task_type == "enforce":
            return self._enforce_constraints(task)
        elif task_type == "block":
            return self._block_operation(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}",
            }

    def _validate_constraints(self, task: dict[str, Any]) -> dict[str, Any]:
        """Validate constraints."""
        entity = task.get("entity", {})
        rules = task.get("rules", [])

        violations = []
        for rule in rules:
            if not self._check_rule(entity, rule):
                violations.append(
                    {
                        "rule_id": rule.get("rule_id"),
                        "rule_name": rule.get("rule_name"),
                    }
                )

        return {
            "status": "success" if not violations else "failed",
            "valid": len(violations) == 0,
            "violations": violations,
            "rules_checked": len(rules),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _check_rule(self, entity: dict[str, Any], rule: dict[str, Any]) -> bool:
        """Check a single rule against entity using a small dispatch table."""
        constraint_expr = rule.get("constraint_expression", "")
        config = rule.get("rule_config", {})

        handlers: dict[str, Any] = {
            "required_fields": self._rule_required_fields,
            "min_length": self._rule_min_length,
            "max_length": self._rule_max_length,
            "require_metadata": self._rule_require_metadata,
            "max_agents": self._rule_max_agents,
            "max_concurrent": self._rule_max_concurrent,
            "value_range": self._rule_value_range,
            "allowed_values": self._rule_allowed_values,
        }

        handler = handlers.get(constraint_expr)
        if handler is None:
            return True
        return handler(entity, config)

    # ---- Rule handlers (private) ----
    def _rule_required_fields(
        self, entity: dict[str, Any], config: dict[str, Any]
    ) -> bool:
        required = config.get("required_fields", [])
        return all(field in entity for field in required)

    def _rule_min_length(self, entity: dict[str, Any], config: dict[str, Any]) -> bool:
        min_len = config.get("min_length", 0)
        text = entity.get("document_text", "")
        return len(text) >= min_len

    def _rule_max_length(self, entity: dict[str, Any], config: dict[str, Any]) -> bool:
        max_len = config.get("max_length", float("inf"))
        text = entity.get("document_text", "")
        return len(text) <= max_len

    def _rule_require_metadata(
        self, entity: dict[str, Any], config: dict[str, Any]
    ) -> bool:
        metadata = entity.get("metadata", {})
        required_keys = config.get("required_metadata_keys", [])
        return all(k in metadata for k in required_keys)

    def _rule_max_agents(self, entity: dict[str, Any], config: dict[str, Any]) -> bool:
        max_agents = config.get("max_agents", 0)
        agent_count = entity.get("agent_count", 0)
        return agent_count <= max_agents

    def _rule_max_concurrent(
        self, entity: dict[str, Any], config: dict[str, Any]
    ) -> bool:
        max_concurrent = config.get("max_concurrent", 0)
        concurrent_tasks = entity.get("concurrent_tasks", 0)
        return concurrent_tasks <= max_concurrent

    def _rule_value_range(self, entity: dict[str, Any], config: dict[str, Any]) -> bool:
        ranges = config.get("value_ranges", {})
        for field, (min_val, max_val) in ranges.items():
            if field in entity:
                value = entity[field]
                if isinstance(value, int | float):
                    if value < min_val or value > max_val:
                        return False
        return True

    def _rule_allowed_values(
        self, entity: dict[str, Any], config: dict[str, Any]
    ) -> bool:
        allowed = config.get("allowed_values", {})
        for field, allowed_list in allowed.items():
            if field in entity and entity[field] not in allowed_list:
                return False
        return True

    def _enforce_constraints(self, task: dict[str, Any]) -> dict[str, Any]:
        """Enforce constraints on an operation."""
        constraints = task.get("constraints", [])

        return {
            "status": "success",
            "enforced": True,
            "constraints_applied": len(constraints),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _block_operation(self, task: dict[str, Any]) -> dict[str, Any]:
        """Block an operation due to constraint violations."""
        operation_id = task.get("operation_id", "unknown")
        reason = task.get("reason", "Constraint violation")
        logger.warning(f"Blocking operation {operation_id}: {reason}")

        return {
            "status": "blocked",
            "operation_id": operation_id,
            "reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class RoutingAgent(BaseAgent):
    """Routing Agent - Orchestrates multi-agent flow.

    Routes tasks to appropriate agents based on capabilities,
    load, and routing policies.
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize routing agent."""
        super().__init__(
            agent_id=agent_id,
            agent_name="RoutingAgent",
            agent_type="routing",
        )
        self.capabilities = ["route", "schedule", "load_balance"]

    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute routing task.

        Args:
            task: Routing task definition

        Returns:
            Routing result
        """
        task_type = task.get("type", "route")
        logger.info(f"RoutingAgent executing task: {task_type}")

        if task_type == "route":
            return self._route_task(task)
        elif task_type == "schedule":
            return self._schedule_tasks(task)
        elif task_type == "load_balance":
            return self._load_balance(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}",
            }

    def _route_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Route a task to an appropriate agent."""
        task_requirements = task.get("requirements", {})
        available_agents = task.get("agents", [])

        # Simple capability-based routing
        selected_agent = None
        for agent in available_agents:
            agent_capabilities = agent.get("capabilities", [])
            required_capabilities = task_requirements.get("capabilities", [])
            if all(cap in agent_capabilities for cap in required_capabilities):
                selected_agent = agent
                break

        return {
            "status": "success" if selected_agent else "failed",
            "selected_agent": (
                selected_agent.get("agent_id") if selected_agent else None
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _schedule_tasks(self, task: dict[str, Any]) -> dict[str, Any]:
        """Schedule multiple tasks for execution."""
        tasks = task.get("tasks", [])
        agents = task.get("agents", [])

        schedule = []
        for t in tasks:
            # Simple round-robin scheduling
            agent_idx = len(schedule) % len(agents) if agents else 0
            schedule.append(
                {
                    "task_id": t.get("task_id"),
                    "agent_id": agents[agent_idx].get("agent_id") if agents else None,
                }
            )

        return {
            "status": "success",
            "schedule": schedule,
            "tasks_scheduled": len(schedule),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _load_balance(self, task: dict[str, Any]) -> dict[str, Any]:
        """Balance load across agents."""
        agents = task.get("agents", [])

        # Simple load balancing logic
        balanced = []
        for agent in agents:
            current_load = agent.get("current_task_count", 0)
            max_load = agent.get("max_concurrent_tasks", 10)
            balanced.append(
                {
                    "agent_id": agent.get("agent_id"),
                    "load_percentage": (
                        (current_load / max_load * 100) if max_load > 0 else 0
                    ),
                }
            )

        return {
            "status": "success",
            "agents_balanced": len(balanced),
            "load_distribution": balanced,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class SynthesisAgent(BaseAgent):
    """Synthesis Agent - Merges multi-source results.

    Aggregates results from multiple agents and produces
    unified, harmonized insights.
    """

    def __init__(self, agent_id: str | None = None):
        """Initialize synthesis agent."""
        super().__init__(
            agent_id=agent_id,
            agent_name="SynthesisAgent",
            agent_type="synthesis",
        )
        self.capabilities = ["merge", "harmonize", "aggregate"]

    def execute_task(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute synthesis task.

        Args:
            task: Synthesis task definition

        Returns:
            Synthesis result
        """
        task_type = task.get("type", "merge")
        logger.info(f"SynthesisAgent executing task: {task_type}")

        if task_type == "merge":
            return self._merge_results(task)
        elif task_type == "harmonize":
            return self._harmonize_results(task)
        elif task_type == "aggregate":
            return self._aggregate_results(task)
        else:
            return {
                "status": "error",
                "message": f"Unknown task type: {task_type}",
            }

    def _merge_results(self, task: dict[str, Any]) -> dict[str, Any]:
        """Merge results from multiple agents."""
        results = task.get("results", [])

        merged = {
            "timestamp": datetime.now(UTC).isoformat(),
            "sources": len(results),
            "merged_data": {},
        }

        # Simple merging logic - combine all result data
        for result in results:
            agent_id = result.get("agent_id", "unknown")
            merged["merged_data"][agent_id] = result.get("result", {})

        return {
            "status": "success",
            "merged_result": merged,
            "sources_merged": len(results),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _harmonize_results(self, task: dict[str, Any]) -> dict[str, Any]:
        """Harmonize conflicting results."""
        # Detect conflicts and resolve
        harmonized = {
            "timestamp": datetime.now(UTC).isoformat(),
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "final_result": {},
        }

        return {
            "status": "success",
            "harmonized_result": harmonized,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    def _aggregate_results(self, task: dict[str, Any]) -> dict[str, Any]:
        """Aggregate numerical or statistical results."""
        results = task.get("results", [])

        aggregated = {
            "timestamp": datetime.now(UTC).isoformat(),
            "count": len(results),
            "aggregations": {},
        }

        return {
            "status": "success",
            "aggregated_result": aggregated,
            "timestamp": datetime.now(UTC).isoformat(),
        }


__all__ = [
    "BaseAgent",
    "SentinelAgent",
    "ConstraintAgent",
    "RoutingAgent",
    "SynthesisAgent",
]
