"""Prevention Engine for Phase 11 Self-Healing.

Adds guards, fallback logic, and predictive checks to prevent failures.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class PreventionEngine:
    """Prevents system degradation through proactive measures.

    Capabilities:
    - Add guard clauses
    - Implement fallback logic
    - Install predictive checks
    - Setup monitoring triggers
    - Configure circuit breakers
    - Establish health thresholds
    """

    def __init__(self):
        """Initialize prevention engine."""
        self.guards: dict[str, dict[str, Any]] = {}
        self.fallbacks: dict[str, Callable] = {}
        self.thresholds: dict[str, float] = {}
        self.prevention_history: list[dict[str, Any]] = []
        self._initialize_default_guards()
        logger.info("PreventionEngine initialized")

    def _initialize_default_guards(self):
        """Initialize default guard configurations."""
        # Import validation guards
        self.add_guard(
            "import_validation",
            {
                "type": "import_check",
                "critical_modules": [
                    "sqlalchemy",
                    "fastapi",
                    "pydantic",
                    "numpy",
                    "sklearn",
                ],
                "action": "block",
            },
        )

        # Schema consistency guards
        self.add_guard(
            "schema_consistency",
            {
                "type": "schema_check",
                "check_on_startup": True,
                "check_on_migration": True,
                "action": "warn",
            },
        )

        # Performance guards
        self.add_guard(
            "query_timeout",
            {"type": "performance", "max_duration_seconds": 30, "action": "warn"},
        )

        # Memory guards
        self.add_guard(
            "memory_limit",
            {"type": "resource", "max_memory_mb": 1024, "action": "warn"},
        )

        # Agent task guards
        self.add_guard(
            "agent_task_limit",
            {"type": "agent", "max_concurrent_tasks": 50, "action": "block"},
        )

        logger.info(f"Initialized {len(self.guards)} default guards")

    def add_guard(self, guard_id: str, guard_config: dict[str, Any]):
        """Add or update a guard configuration.

        Args:
            guard_id: Unique identifier for the guard
            guard_config: Guard configuration dictionary
        """
        self.guards[guard_id] = {
            **guard_config,
            "added_at": datetime.now(UTC).isoformat(),
        }
        logger.info(f"Guard added: {guard_id}")

    def remove_guard(self, guard_id: str) -> bool:
        """Remove a guard configuration.

        Args:
            guard_id: Guard identifier to remove

        Returns:
            True if guard was removed, False if not found
        """
        if guard_id in self.guards:
            del self.guards[guard_id]
            logger.info(f"Guard removed: {guard_id}")
            return True
        return False

    def register_fallback(self, operation_id: str, fallback_fn: Callable):
        """Register a fallback function for an operation.

        Args:
            operation_id: Operation identifier
            fallback_fn: Fallback function to call on failure
        """
        self.fallbacks[operation_id] = fallback_fn
        logger.info(f"Fallback registered for: {operation_id}")

    def set_threshold(self, metric: str, threshold: float):
        """Set a threshold for a metric.

        Args:
            metric: Metric name
            threshold: Threshold value
        """
        self.thresholds[metric] = threshold
        logger.info(f"Threshold set: {metric} = {threshold}")

    def check_guard(self, guard_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Check if a guard condition is satisfied.

        Args:
            guard_id: Guard identifier
            context: Context data for evaluation

        Returns:
            Guard check result
        """
        if guard_id not in self.guards:
            return {"status": "unknown_guard", "passed": False}

        guard = self.guards[guard_id]
        guard_type = guard.get("type")

        result = {
            "guard_id": guard_id,
            "guard_type": guard_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "passed": True,
            "action": guard.get("action", "warn"),
        }

        # Evaluate guard based on type
        if guard_type == "import_check":
            result["passed"] = self._check_import_guard(guard, context)
        elif guard_type == "schema_check":
            result["passed"] = self._check_schema_guard(guard, context)
        elif guard_type == "performance":
            result["passed"] = self._check_performance_guard(guard, context)
        elif guard_type == "resource":
            result["passed"] = self._check_resource_guard(guard, context)
        elif guard_type == "agent":
            result["passed"] = self._check_agent_guard(guard, context)

        if not result["passed"]:
            logger.warning(f"Guard failed: {guard_id}")
            self._record_prevention("guard_failure", result)

        return result

    def check_all_guards(self, context: dict[str, Any]) -> dict[str, Any]:
        """Check all registered guards.

        Args:
            context: Context data for evaluation

        Returns:
            Comprehensive guard check results
        """
        logger.info(f"Checking {len(self.guards)} guards")

        results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_guards": len(self.guards),
            "guards_passed": 0,
            "guards_failed": 0,
            "details": [],
        }

        for guard_id in self.guards:
            check_result = self.check_guard(guard_id, context)
            results["details"].append(check_result)

            if check_result["passed"]:
                results["guards_passed"] += 1
            else:
                results["guards_failed"] += 1

        results["overall_status"] = (
            "healthy" if results["guards_failed"] == 0 else "degraded"
        )

        logger.info(
            f"Guards check complete: {results['guards_passed']}/"
            f"{results['total_guards']} passed"
        )
        return results

    def generate_prevention_plan(
        self, detection_report: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate prevention plan based on detection results.

        Args:
            detection_report: Report from DetectionEngine

        Returns:
            Prevention plan with recommended guards and fallbacks
        """
        logger.info("Generating prevention plan")

        plan = {
            "timestamp": datetime.now(UTC).isoformat(),
            "based_on_detection": detection_report.get("timestamp"),
            "recommended_guards": [],
            "recommended_fallbacks": [],
            "recommended_thresholds": [],
        }

        # Analyze detection report and recommend preventive measures
        for check_type, issues in detection_report.get("checks", {}).items():
            if check_type == "broken_imports" and len(issues) > 0:
                plan["recommended_guards"].append(
                    {
                        "guard_id": "runtime_import_validation",
                        "type": "import_check",
                        "reason": f"Found {len(issues)} broken imports",
                        "priority": "high",
                    }
                )

            if check_type == "performance_bottlenecks" and len(issues) > 0:
                plan["recommended_thresholds"].append(
                    {
                        "metric": "query_execution_time",
                        "threshold": 5.0,
                        "reason": f"Found {len(issues)} potential performance issues",
                        "priority": "medium",
                    }
                )

            if check_type == "schema_divergence" and len(issues) > 0:
                plan["recommended_guards"].append(
                    {
                        "guard_id": "schema_validation_on_startup",
                        "type": "schema_check",
                        "reason": f"Found {len(issues)} schema issues",
                        "priority": "high",
                    }
                )

        logger.info(
            f"Prevention plan generated: {len(plan['recommended_guards'])} guards, "
            f"{len(plan['recommended_fallbacks'])} fallbacks"
        )
        return plan

    def _check_import_guard(
        self, guard: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Check import validation guard.

        Args:
            guard: Guard configuration
            context: Evaluation context

        Returns:
            True if guard passes
        """
        critical_modules = guard.get("critical_modules", [])
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                logger.warning(f"Critical module not available: {module}")
                return False
        return True

    def _check_schema_guard(
        self, guard: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Check schema consistency guard.

        Args:
            guard: Guard configuration
            context: Evaluation context

        Returns:
            True if guard passes
        """
        # Check if database models are importable
        try:
            import oraculus_di_auditor.db.models  # noqa: F401

            return True
        except ImportError:
            return False

    def _check_performance_guard(
        self, guard: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Check performance guard.

        Args:
            guard: Guard configuration
            context: Evaluation context

        Returns:
            True if guard passes
        """
        max_duration = guard.get("max_duration_seconds")
        actual_duration = context.get("duration_seconds", 0)

        if max_duration and actual_duration > max_duration:
            return False
        return True

    def _check_resource_guard(
        self, guard: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Check resource usage guard.

        Args:
            guard: Guard configuration
            context: Evaluation context

        Returns:
            True if guard passes
        """
        max_memory_mb = guard.get("max_memory_mb")
        actual_memory_mb = context.get("memory_mb", 0)

        if max_memory_mb and actual_memory_mb > max_memory_mb:
            return False
        return True

    def _check_agent_guard(
        self, guard: dict[str, Any], context: dict[str, Any]
    ) -> bool:
        """Check agent-specific guard.

        Args:
            guard: Guard configuration
            context: Evaluation context

        Returns:
            True if guard passes
        """
        max_concurrent = guard.get("max_concurrent_tasks")
        actual_concurrent = context.get("concurrent_tasks", 0)

        if max_concurrent and actual_concurrent > max_concurrent:
            return False
        return True

    def _record_prevention(self, event_type: str, data: dict[str, Any]):
        """Record prevention event in history.

        Args:
            event_type: Type of prevention event
            data: Event data
        """
        self.prevention_history.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event_type": event_type,
                "data": data,
            }
        )
