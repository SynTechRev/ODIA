"""Constraint Validator for Global Constraint Network.

Validates entities (documents, jobs, agents, tasks) against GCN rules.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class ConstraintValidator:
    """Validates entities against GCN constraint rules.

    Implements deterministic rule evaluation with priority-based ordering.
    """

    def __init__(self):
        """Initialize constraint validator."""
        self.validation_cache: dict[str, Any] = {}
        logger.info("ConstraintValidator initialized")

    def validate_entity(
        self,
        entity_type: str,
        entity_id: str,
        entity_data: dict[str, Any],
        rules: list[dict[str, Any]],
        scope: str = "global",
        strict: bool = True,
    ) -> dict[str, Any]:
        """Validate an entity against GCN rules.

        Args:
            entity_type: Type of entity (document, job, agent, task)
            entity_id: Entity identifier
            entity_data: Entity data to validate
            rules: List of GCN rules to evaluate
            scope: Validation scope (global, agent, document, job)
            strict: Whether to fail on warnings

        Returns:
            Validation result with violations list
        """
        logger.info(f"Validating {entity_type} {entity_id} against {len(rules)} rules")

        # Filter rules by scope and enabled status
        applicable_rules = [
            r
            for r in rules
            if r.get("enabled", True)
            and (r.get("scope") == scope or r.get("scope") == "global")
        ]

        # Sort by priority (higher priority first)
        applicable_rules.sort(key=lambda r: r.get("priority", 0), reverse=True)

        violations = []
        rules_evaluated = 0

        for rule in applicable_rules:
            rules_evaluated += 1
            violation = self._evaluate_rule(entity_type, entity_data, rule)
            if violation:
                violations.append(violation)

        # Determine if entity is blocked
        blocked = any(v["action"] == "block" for v in violations)

        # Count warnings and errors
        warnings = sum(1 for v in violations if v["severity"] == "warning")
        errors = sum(1 for v in violations if v["severity"] in ["error", "critical"])

        # Determine overall validity
        if strict:
            valid = len(violations) == 0
        else:
            valid = errors == 0 and not blocked

        result = {
            "valid": valid,
            "entity_id": entity_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "rules_evaluated": rules_evaluated,
            "violations": violations,
            "blocked": blocked,
            "warnings": warnings,
            "errors": errors,
        }

        logger.info(
            f"Validation complete: valid={valid}, violations={len(violations)}, "  # noqa: E501
            f"blocked={blocked}"
        )

        return result

    def _evaluate_rule(
        self,
        entity_type: str,
        entity_data: dict[str, Any],
        rule: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Evaluate a single rule against entity data.

        Args:
            entity_type: Type of entity
            entity_data: Entity data
            rule: GCN rule definition

        Returns:
            Violation dict if rule is violated, None otherwise
        """
        rule_id = rule.get("rule_id", "unknown")
        rule_type = rule.get("rule_type", "unknown")
        constraint_expr = rule.get("constraint_expression", "")

        logger.debug(f"Evaluating rule {rule_id} ({rule_type})")

        # Structural constraints
        if rule_type == "structural":
            return self._evaluate_structural_constraint(
                entity_data, rule, constraint_expr
            )

        # Policy constraints
        elif rule_type == "policy":
            return self._evaluate_policy_constraint(entity_data, rule, constraint_expr)

        # Document constraints
        elif rule_type == "document":
            return self._evaluate_document_constraint(
                entity_data, rule, constraint_expr
            )

        # Pipeline safety constraints
        elif rule_type == "pipeline" or rule_type == "safety":
            return self._evaluate_pipeline_constraint(
                entity_data, rule, constraint_expr
            )

        logger.warning(f"Unknown rule type: {rule_type}")
        return None

    def _evaluate_structural_constraint(
        self,
        entity_data: dict[str, Any],
        rule: dict[str, Any],
        constraint_expr: str,
    ) -> dict[str, Any] | None:
        """Evaluate structural constraints (required fields, types, formats)."""
        rule_config = rule.get("rule_config", {})

        # Check required fields
        if "required_fields" in constraint_expr:
            required = rule_config.get("required_fields", [])
            missing = [f for f in required if f not in entity_data]
            if missing:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "error"),
                    "action": rule["violation_action"],
                    "message": f"Missing required fields: {', '.join(missing)}",
                    "details": {"missing_fields": missing},
                }

        # Check field types
        if "field_types" in constraint_expr:
            type_checks = rule_config.get("field_types", {})
            for field, expected_type in type_checks.items():
                if field in entity_data:
                    actual_type = type(entity_data[field]).__name__
                    if actual_type != expected_type:
                        return {
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule.get("severity", "error"),
                            "action": rule["violation_action"],
                            "message": f"Field '{field}' has incorrect type: expected {expected_type}, got {actual_type}",  # noqa: E501
                            "details": {
                                "field": field,
                                "expected": expected_type,
                                "actual": actual_type,
                            },  # noqa: E501
                        }

        return None

    def _evaluate_policy_constraint(
        self,
        entity_data: dict[str, Any],
        rule: dict[str, Any],
        constraint_expr: str,
    ) -> dict[str, Any] | None:
        """Evaluate policy constraints (business rules, governance policies)."""
        rule_config = rule.get("rule_config", {})

        # Check value ranges
        if "value_range" in constraint_expr:
            ranges = rule_config.get("value_ranges", {})
            for field, (min_val, max_val) in ranges.items():
                if field in entity_data:
                    value = entity_data[field]
                    if isinstance(value, int | float):
                        if value < min_val or value > max_val:
                            return {
                                "rule_id": rule["rule_id"],
                                "rule_name": rule["rule_name"],
                                "severity": rule.get("severity", "warning"),
                                "action": rule["violation_action"],
                                "message": f"Field '{field}' value {value} outside allowed range [{min_val}, {max_val}]",  # noqa: E501
                                "details": {
                                    "field": field,
                                    "value": value,
                                    "min": min_val,
                                    "max": max_val,
                                },  # noqa: E501
                            }

        # Check allowed values
        if "allowed_values" in constraint_expr:
            allowed = rule_config.get("allowed_values", {})
            for field, allowed_list in allowed.items():
                if field in entity_data:
                    value = entity_data[field]
                    if value not in allowed_list:
                        return {
                            "rule_id": rule["rule_id"],
                            "rule_name": rule["rule_name"],
                            "severity": rule.get("severity", "warning"),
                            "action": rule["violation_action"],
                            "message": f"Field '{field}' value '{value}' not in allowed list",  # noqa: E501
                            "details": {
                                "field": field,
                                "value": value,
                                "allowed": allowed_list,
                            },
                        }

        return None

    def _evaluate_document_constraint(
        self,
        entity_data: dict[str, Any],
        rule: dict[str, Any],
        constraint_expr: str,
    ) -> dict[str, Any] | None:
        """Evaluate document-specific constraints (length, content, metadata)."""
        rule_config = rule.get("rule_config", {})

        # Check document text length
        if "min_length" in constraint_expr or "max_length" in constraint_expr:
            text = entity_data.get("document_text", "")
            text_len = len(text)

            min_len = rule_config.get("min_length", 0)
            max_len = rule_config.get("max_length", float("inf"))

            if text_len < min_len:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "error"),
                    "action": rule["violation_action"],
                    "message": f"Document too short: {text_len} chars "  # noqa: E501
                    f"(minimum {min_len})",
                    "details": {"length": text_len, "min_required": min_len},
                }
            elif text_len > max_len:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "error"),
                    "action": rule["violation_action"],
                    "message": f"Document too long: {text_len} chars "  # noqa: E501
                    f"(maximum {max_len})",
                    "details": {"length": text_len, "max_allowed": max_len},
                }

        # Check metadata requirements
        if "require_metadata" in constraint_expr:
            metadata = entity_data.get("metadata", {})
            required_keys = rule_config.get("required_metadata_keys", [])
            missing = [k for k in required_keys if k not in metadata]
            if missing:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "warning"),
                    "action": rule["violation_action"],
                    "message": f"Missing required metadata keys: {', '.join(missing)}",
                    "details": {"missing_keys": missing},
                }

        return None

    def _evaluate_pipeline_constraint(
        self,
        entity_data: dict[str, Any],
        rule: dict[str, Any],
        constraint_expr: str,
    ) -> dict[str, Any] | None:
        """Evaluate pipeline safety constraints.

        Checks agent limits, concurrency, and resources.
        """
        rule_config = rule.get("rule_config", {})

        # Check agent limits
        if "max_agents" in constraint_expr:
            agent_count = entity_data.get("agent_count", 0)
            max_agents = rule_config.get("max_agents", 100)
            if agent_count > max_agents:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "error"),
                    "action": rule["violation_action"],
                    "message": f"Too many agents: {agent_count} (maximum {max_agents})",
                    "details": {"agent_count": agent_count, "max_allowed": max_agents},
                }

        # Check concurrency limits
        if "max_concurrent" in constraint_expr:
            concurrent = entity_data.get("concurrent_tasks", 0)
            max_concurrent = rule_config.get("max_concurrent", 50)
            if concurrent > max_concurrent:
                return {
                    "rule_id": rule["rule_id"],
                    "rule_name": rule["rule_name"],
                    "severity": rule.get("severity", "warning"),
                    "action": rule["violation_action"],
                    "message": f"Too many concurrent tasks: {concurrent} (maximum {max_concurrent})",  # noqa: E501
                    "details": {
                        "concurrent_tasks": concurrent,
                        "max_allowed": max_concurrent,
                    },
                }

        return None


__all__ = ["ConstraintValidator"]
