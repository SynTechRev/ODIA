"""Policy Registry for Global Constraint Network.

Manages registration, storage, and retrieval of GCN rules and policies.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class PolicyRegistry:
    """Central registry for GCN rules and policies.

    Maintains a versioned collection of constraint rules with
    deterministic loading and retrieval.
    """

    def __init__(self):
        """Initialize policy registry with default rules."""
        self.rules: dict[str, dict[str, Any]] = {}
        self.version = "1.0.0"
        logger.info("PolicyRegistry initialized")
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default GCN constraint rules."""
        default_rules = [
            # Structural constraints
            {
                "rule_id": "gcn:structural:required-fields",
                "rule_name": "Required Fields Constraint",
                "rule_type": "structural",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 100,
                "scope": "global",
                "constraint_expression": "required_fields",
                "violation_action": "block",
                "severity": "error",
                "rule_config": {
                    "required_fields": ["document_text", "metadata"],
                },
            },
            # Document constraints
            {
                "rule_id": "gcn:document:min-length",
                "rule_name": "Minimum Document Length",
                "rule_type": "document",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 90,
                "scope": "document",
                "constraint_expression": "min_length",
                "violation_action": "block",
                "severity": "error",
                "rule_config": {
                    "min_length": 10,
                },
            },
            {
                "rule_id": "gcn:document:max-length",
                "rule_name": "Maximum Document Length",
                "rule_type": "document",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 90,
                "scope": "document",
                "constraint_expression": "max_length",
                "violation_action": "block",
                "severity": "error",
                "rule_config": {
                    "max_length": 10_000_000,
                },
            },
            {
                "rule_id": "gcn:document:require-metadata",
                "rule_name": "Required Document Metadata",
                "rule_type": "document",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 80,
                "scope": "document",
                "constraint_expression": "require_metadata",
                "violation_action": "warn",
                "severity": "warning",
                "rule_config": {
                    "required_metadata_keys": ["title"],
                },
            },
            # Pipeline safety constraints
            {
                "rule_id": "gcn:pipeline:max-agents",
                "rule_name": "Maximum Agent Count",
                "rule_type": "pipeline",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 95,
                "scope": "job",
                "constraint_expression": "max_agents",
                "violation_action": "block",
                "severity": "error",
                "rule_config": {
                    "max_agents": 100,
                },
            },
            {
                "rule_id": "gcn:pipeline:max-concurrent",
                "rule_name": "Maximum Concurrent Tasks",
                "rule_type": "pipeline",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 85,
                "scope": "job",
                "constraint_expression": "max_concurrent",
                "violation_action": "warn",
                "severity": "warning",
                "rule_config": {
                    "max_concurrent": 50,
                },
            },
            # Policy constraints
            {
                "rule_id": "gcn:policy:threat-score",
                "rule_name": "Maximum Threat Score",
                "rule_type": "policy",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 100,
                "scope": "global",
                "constraint_expression": "value_range",
                "violation_action": "block",
                "severity": "critical",
                "rule_config": {
                    "value_ranges": {
                        "threat_score": (0.0, 0.5),
                    },
                },
            },
            {
                "rule_id": "gcn:policy:agent-status",
                "rule_name": "Agent Status Validation",
                "rule_type": "policy",
                "rule_version": "1.0.0",
                "enabled": True,
                "priority": 90,
                "scope": "agent",
                "constraint_expression": "allowed_values",
                "violation_action": "warn",
                "severity": "warning",
                "rule_config": {
                    "allowed_values": {
                        "status": ["active", "inactive", "suspended"],
                    },
                },
            },
        ]

        for rule in default_rules:
            self.register_rule(rule)

        logger.info(f"Loaded {len(default_rules)} default GCN rules")

    def register_rule(self, rule: dict[str, Any]) -> bool:
        """Register a new GCN rule.

        Args:
            rule: Rule definition dictionary

        Returns:
            True if registered successfully, False otherwise
        """
        rule_id = rule.get("rule_id")
        if not rule_id:
            logger.error("Cannot register rule without rule_id")
            return False

        if rule_id in self.rules:
            logger.warning(f"Rule {rule_id} already exists, updating")

        self.rules[rule_id] = rule
        logger.debug(f"Registered rule: {rule_id}")
        return True

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        """Get a specific rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            Rule definition or None if not found
        """
        return self.rules.get(rule_id)

    def get_rules_by_type(self, rule_type: str) -> list[dict[str, Any]]:
        """Get all rules of a specific type.

        Args:
            rule_type: Type of rules to retrieve

        Returns:
            List of matching rules
        """
        return [r for r in self.rules.values() if r.get("rule_type") == rule_type]

    def get_rules_by_scope(self, scope: str) -> list[dict[str, Any]]:
        """Get all rules for a specific scope.

        Args:
            scope: Scope to filter by (global, agent, document, job)

        Returns:
            List of matching rules (includes global scope rules)
        """
        return [r for r in self.rules.values() if r.get("scope") in [scope, "global"]]

    def get_all_rules(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        """Get all registered rules.

        Args:
            enabled_only: Whether to return only enabled rules

        Returns:
            List of all rules
        """
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.get("enabled", True)]
        return rules

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule.

        Args:
            rule_id: Rule identifier

        Returns:
            True if successful, False otherwise
        """
        if rule_id in self.rules:
            self.rules[rule_id]["enabled"] = True
            logger.info(f"Enabled rule: {rule_id}")
            return True
        logger.warning(f"Rule not found: {rule_id}")
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule.

        Args:
            rule_id: Rule identifier

        Returns:
            True if successful, False otherwise
        """
        if rule_id in self.rules:
            self.rules[rule_id]["enabled"] = False
            logger.info(f"Disabled rule: {rule_id}")
            return True
        logger.warning(f"Rule not found: {rule_id}")
        return False

    def get_registry_state(self) -> dict[str, Any]:
        """Get current state of the policy registry.

        Returns:
            Registry state summary
        """
        all_rules = self.get_all_rules()
        active_rules = self.get_all_rules(enabled_only=True)

        rules_by_type: dict[str, int] = {}
        for rule in all_rules:
            rule_type = rule.get("rule_type", "unknown")
            rules_by_type[rule_type] = rules_by_type.get(rule_type, 0) + 1

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "registry_version": self.version,
            "rules_total": len(all_rules),
            "rules_active": len(active_rules),
            "rules_by_type": rules_by_type,
        }


__all__ = ["PolicyRegistry"]
