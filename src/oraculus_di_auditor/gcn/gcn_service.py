"""GCN Service - Global Constraint Network central authority.

Coordinates constraint validation, policy enforcement, and system governance.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from .constraint_validator import ConstraintValidator
from .policy_registry import PolicyRegistry

logger = logging.getLogger(__name__)


class GCNService:
    """Global Constraint Network Service.

    Central authority for defining and enforcing computation boundaries,
    structural constraints, policies, document rulesets, and pipeline
    safety invariants across all agents and operations.

    Functions as the "mathematical constitution" of the system.
    """

    def __init__(self):
        """Initialize GCN service."""
        self.policy_registry = PolicyRegistry()
        self.constraint_validator = ConstraintValidator()
        self.version = "1.0.0"
        self.enforcement_mode = "strict"  # strict, permissive, audit
        self.last_validation: str | None = None
        logger.info("GCN Service initialized")

    def get_state(self) -> dict[str, Any]:
        """Get current GCN system state.

        Returns:
            GCN state summary
        """
        logger.info("Getting GCN state")

        registry_state = self.policy_registry.get_registry_state()
        all_rules = self.policy_registry.get_all_rules()
        active_rules = self.policy_registry.get_all_rules(enabled_only=True)

        # Determine health status
        health_status = "healthy"
        if len(active_rules) == 0:
            health_status = "degraded"
        elif registry_state["rules_total"] == 0:
            health_status = "error"

        state = {
            "timestamp": datetime.now(UTC).isoformat(),
            "gcn_version": self.version,
            "rules_loaded": len(all_rules),
            "rules_active": len(active_rules),
            "rules_by_type": registry_state["rules_by_type"],
            "enforcement_mode": self.enforcement_mode,
            "last_validation": self.last_validation,
            "health_status": health_status,
        }

        logger.info(f"GCN state: {health_status}, {len(active_rules)} active rules")
        return state

    def validate_system(
        self,
        deep: bool = False,
        check_rules: bool = True,
        check_policies: bool = True,
    ) -> dict[str, Any]:
        """Validate GCN system state and integrity.

        Args:
            deep: Whether to perform deep validation
            check_rules: Whether to check rule integrity
            check_policies: Whether to check policy consistency

        Returns:
            Validation result
        """
        logger.info(f"Validating GCN system (deep={deep})")

        checks: dict[str, Any] = {}
        errors: list[str] = []
        warnings: list[str] = []

        # Check rule integrity
        if check_rules:
            rule_check = self._validate_rules()
            checks["rules"] = rule_check
            errors.extend(rule_check.get("errors", []))
            warnings.extend(rule_check.get("warnings", []))

        # Check policy consistency
        if check_policies:
            policy_check = self._validate_policies()
            checks["policies"] = policy_check
            errors.extend(policy_check.get("errors", []))
            warnings.extend(policy_check.get("warnings", []))

        # Deep validation - additional checks
        if deep:
            deep_checks = self._perform_deep_validation()
            checks["deep"] = deep_checks
            errors.extend(deep_checks.get("errors", []))
            warnings.extend(deep_checks.get("warnings", []))

        # Determine overall status
        overall_status = "success"
        if errors:
            overall_status = "error"
        elif warnings:
            overall_status = "warning"

        self.last_validation = datetime.now(UTC).isoformat()

        result = {
            "timestamp": self.last_validation,
            "overall_status": overall_status,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
        }

        logger.info(
            f"GCN validation: {overall_status}, {len(errors)} errors, "  # noqa: E501
            f"{len(warnings)} warnings"
        )
        return result

    def validate_entity(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: dict[str, Any],
        scope: str = "global",
        strict: bool = True,
    ) -> dict[str, Any]:
        """Validate an entity against GCN constraints.

        Args:
            entity_type: Type of entity (document, job, agent, task)
            entity_id: Entity identifier
            entity_data: Entity data to validate
            scope: Validation scope (global, agent, document, job)
            strict: Whether to fail on warnings

        Returns:
            Validation result with violations
        """
        logger.info(f"Validating {entity_type} entity: {entity_id}")

        # Get applicable rules for this entity type and scope
        rules = self.policy_registry.get_rules_by_scope(scope)

        # Filter rules by entity type relevance
        if entity_type == "document":
            rules = [
                r
                for r in rules
                if r.get("rule_type") in ["document", "structural", "policy"]
            ]
        elif entity_type == "job":
            rules = [
                r
                for r in rules
                if r.get("rule_type") in ["pipeline", "safety", "policy"]
            ]
        elif entity_type == "agent":
            rules = [r for r in rules if r.get("rule_type") in ["policy", "structural"]]

        # Validate against rules
        result = self.constraint_validator.validate_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_data=entity_data,
            rules=rules,
            scope=scope,
            strict=strict,
        )

        logger.info(
            f"Entity validation: valid={result['valid']}, "  # noqa: E501
            f"violations={len(result['violations'])}"
        )
        return result

    def _validate_rules(self) -> dict[str, Any]:
        """Validate rule integrity and configuration.

        Returns:
            Rule validation results
        """
        all_rules = self.policy_registry.get_all_rules()
        errors: list[str] = []
        warnings: list[str] = []

        # Check for duplicate rule IDs (should not happen with dict storage)
        rule_ids = [r.get("rule_id") for r in all_rules]
        if len(rule_ids) != len(set(rule_ids)):
            errors.append("Duplicate rule IDs detected")

        # Check that all rules have required fields
        required_fields = [
            "rule_id",
            "rule_name",
            "rule_type",
            "rule_version",
            "scope",
            "constraint_expression",
            "violation_action",
        ]
        for rule in all_rules:
            missing = [f for f in required_fields if f not in rule]
            if missing:
                errors.append(
                    f"Rule {rule.get('rule_id', 'unknown')} missing fields: {missing}"
                )  # noqa: E501

        # Check for rules with invalid types
        valid_types = ["structural", "policy", "document", "pipeline", "safety"]
        for rule in all_rules:
            if rule.get("rule_type") not in valid_types:
                warnings.append(
                    f"Rule {rule.get('rule_id')} has invalid type: "  # noqa: E501
                    f"{rule.get('rule_type')}"
                )

        return {
            "status": "error" if errors else ("warning" if warnings else "success"),
            "rules_checked": len(all_rules),
            "errors": errors,
            "warnings": warnings,
        }

    def _validate_policies(self) -> dict[str, Any]:
        """Validate policy consistency and conflicts.

        Returns:
            Policy validation results
        """
        all_rules = self.policy_registry.get_all_rules()
        errors: list[str] = []
        warnings: list[str] = []

        # Check for conflicting priorities
        priority_groups: dict[int, list[str]] = {}
        for rule in all_rules:
            priority = rule.get("priority", 0)
            rule_id = rule.get("rule_id", "unknown")
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(rule_id)

        # Warn if many rules have the same priority
        for priority, rule_ids in priority_groups.items():
            if len(rule_ids) > 5:
                warnings.append(
                    f"{len(rule_ids)} rules have priority {priority} - "  # noqa: E501
                    "consider adjusting"
                )

        # Check for rules with no configuration
        for rule in all_rules:
            if not rule.get("rule_config"):
                warnings.append(f"Rule {rule.get('rule_id')} has no configuration")

        return {
            "status": "error" if errors else ("warning" if warnings else "success"),
            "policies_checked": len(all_rules),
            "errors": errors,
            "warnings": warnings,
        }

    def _perform_deep_validation(self) -> dict[str, Any]:
        """Perform deep validation checks.

        Returns:
            Deep validation results
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check constraint validator is operational
        try:
            test_data = {"document_text": "test", "metadata": {}}
            self.constraint_validator.validate_entity(
                entity_type="document",
                entity_id="test",
                entity_data=test_data,
                rules=[],
                scope="global",
            )
        except Exception as e:
            errors.append(f"Constraint validator error: {e}")

        # Check policy registry is operational
        try:
            self.policy_registry.get_registry_state()
        except Exception as e:
            errors.append(f"Policy registry error: {e}")

        return {
            "status": "error" if errors else ("warning" if warnings else "success"),
            "errors": errors,
            "warnings": warnings,
        }

    def set_enforcement_mode(self, mode: str) -> bool:
        """Set GCN enforcement mode.

        Args:
            mode: Enforcement mode (strict, permissive, audit)

        Returns:
            True if set successfully
        """
        valid_modes = ["strict", "permissive", "audit"]
        if mode not in valid_modes:
            logger.error(f"Invalid enforcement mode: {mode}")
            return False

        self.enforcement_mode = mode
        logger.info(f"GCN enforcement mode set to: {mode}")
        return True


__all__ = ["GCNService"]
