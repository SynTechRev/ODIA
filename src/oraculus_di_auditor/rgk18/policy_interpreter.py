# src/oraculus_di_auditor/rgk18/policy_interpreter.py
"""Policy interpreter for normalizing and validating GCN rules."""
from __future__ import annotations

from typing import Any, Literal

from .schemas import PolicyCheckResult


class Policy:
    """Canonical policy representation."""

    def __init__(
        self,
        policy_id: str,
        scope: str,
        rule_type: str,
        condition: dict[str, Any],
        severity: Literal["low", "medium", "high"] = "medium",
        priority: int = 0,
        mutable: bool = True,
    ):
        """Initialize a policy.

        Args:
            policy_id: Unique policy identifier
            scope: Policy scope (e.g., "global", "document", "phase")
            rule_type: Type of rule (e.g., "constraint", "requirement", "prohibition")
            condition: Condition dictionary for evaluation
            severity: Severity level if violated
            priority: Priority for conflict resolution (higher = more important)
            mutable: Whether the policy can be modified
        """
        self.policy_id = policy_id
        self.scope = scope
        self.rule_type = rule_type
        self.condition = condition
        self.severity = severity
        self.priority = priority
        self.mutable = mutable

    def check(self, candidate_action: dict[str, Any]) -> PolicyCheckResult:
        """Check if candidate action violates this policy.

        Args:
            candidate_action: Action to check

        Returns:
            PolicyCheckResult indicating violation status
        """
        # Simple rule evaluation logic
        violated = False
        reason = None

        # Check if action type is in prohibited list
        if self.rule_type == "prohibition":
            prohibited_actions = self.condition.get("prohibited_actions", [])
            action_type = candidate_action.get("action_type", "")
            if action_type in prohibited_actions:
                violated = True
                reason = f"Action type '{action_type}' is prohibited by policy"

        # Check required fields
        elif self.rule_type == "requirement":
            required_fields = self.condition.get("required_fields", [])
            for field in required_fields:
                if field not in candidate_action:
                    violated = True
                    reason = f"Required field '{field}' missing in action"
                    break

        # Check constraints
        elif self.rule_type == "constraint":
            constraint_field = self.condition.get("field")
            max_value = self.condition.get("max_value")
            min_value = self.condition.get("min_value")

            if constraint_field and constraint_field in candidate_action:
                field_value = candidate_action[constraint_field]
                if max_value is not None and field_value > max_value:
                    violated = True
                    reason = (
                        f"Field '{constraint_field}' exceeds maximum value {max_value}"
                    )
                elif min_value is not None and field_value < min_value:
                    violated = True
                    reason = (
                        f"Field '{constraint_field}' below minimum value {min_value}"
                    )

        return PolicyCheckResult(
            policy_id=self.policy_id,
            violated=violated,
            reason=reason,
            severity=self.severity,
        )


class PolicySet:
    """Collection of policies with priority ordering."""

    def __init__(self, policies: list[Policy] | None = None):
        """Initialize policy set.

        Args:
            policies: List of policies (optional)
        """
        self.policies = policies or []
        # Sort by priority (descending)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def add_policy(self, policy: Policy) -> None:
        """Add a policy and resort.

        Args:
            policy: Policy to add
        """
        self.policies.append(policy)
        self.policies.sort(key=lambda p: p.priority, reverse=True)

    def check_all(self, candidate_action: dict[str, Any]) -> list[PolicyCheckResult]:
        """Check all policies against candidate action.

        Args:
            candidate_action: Action to check

        Returns:
            List of policy check results
        """
        return [policy.check(candidate_action) for policy in self.policies]


class PolicyInterpreter:
    """Interprets and normalizes GCN rules into canonical Policy objects."""

    def __init__(self):
        """Initialize policy interpreter."""
        self.policy_sets: dict[str, PolicySet] = {}

    def load_gcn_rules(self, gcn_rules: list[dict[str, Any]]) -> PolicySet:
        """Load and normalize GCN rules into a PolicySet.

        Args:
            gcn_rules: List of GCN rule dictionaries

        Returns:
            Normalized PolicySet
        """
        policies = []
        for i, rule in enumerate(gcn_rules):
            policy = self._normalize_rule(rule, index=i)
            policies.append(policy)

        return PolicySet(policies)

    def _normalize_rule(self, rule: dict[str, Any], index: int) -> Policy:
        """Normalize a single rule into a Policy.

        Args:
            rule: Rule dictionary
            index: Rule index for ID generation

        Returns:
            Normalized Policy
        """
        policy_id = rule.get("policy_id", f"policy-{index}")
        scope = rule.get("scope", "global")
        rule_type = rule.get("rule_type", "constraint")
        condition = rule.get("condition", {})
        severity = rule.get("severity", "medium")
        priority = rule.get("priority", 0)
        mutable = rule.get("mutable", True)

        return Policy(
            policy_id=policy_id,
            scope=scope,
            rule_type=rule_type,
            condition=condition,
            severity=severity,
            priority=priority,
            mutable=mutable,
        )

    def check_policies(
        self, candidate_action: dict[str, Any], policy_set: PolicySet
    ) -> list[PolicyCheckResult]:
        """Check candidate action against a policy set.

        Args:
            candidate_action: Action to check
            policy_set: Set of policies to check against

        Returns:
            List of policy check results
        """
        return policy_set.check_all(candidate_action)
