# tests/rgk18/test_policy_interpreter.py
"""Tests for policy interpreter."""

from oraculus_di_auditor.rgk18.policy_interpreter import (
    Policy,
    PolicyInterpreter,
    PolicySet,
)


def test_policy_check_prohibition():
    """Test policy check for prohibited actions."""
    policy = Policy(
        policy_id="no-delete",
        scope="global",
        rule_type="prohibition",
        condition={"prohibited_actions": ["delete", "remove"]},
        severity="high",
    )

    # Violating action
    result = policy.check({"action_type": "delete", "target": "file.txt"})
    assert result.violated is True
    assert result.severity == "high"
    assert "prohibited" in result.reason.lower()

    # Non-violating action
    result = policy.check({"action_type": "update", "target": "file.txt"})
    assert result.violated is False


def test_policy_check_requirement():
    """Test policy check for required fields."""
    policy = Policy(
        policy_id="require-approval",
        scope="global",
        rule_type="requirement",
        condition={"required_fields": ["approval_token", "user_id"]},
        severity="medium",
    )

    # Missing required field
    result = policy.check({"action_type": "apply_patch", "user_id": "user123"})
    assert result.violated is True
    assert "approval_token" in result.reason

    # All required fields present
    result = policy.check(
        {
            "action_type": "apply_patch",
            "user_id": "user123",
            "approval_token": "token456",
        }
    )
    assert result.violated is False


def test_policy_check_constraint():
    """Test policy check for constraints."""
    policy = Policy(
        policy_id="max-size",
        scope="document",
        rule_type="constraint",
        condition={"field": "size_bytes", "max_value": 1000000},
        severity="low",
    )

    # Exceeds constraint
    result = policy.check(
        {"action_type": "upload", "size_bytes": 2000000, "filename": "large.pdf"}
    )
    assert result.violated is True
    assert "exceeds" in result.reason.lower()

    # Within constraint
    result = policy.check(
        {"action_type": "upload", "size_bytes": 500000, "filename": "small.pdf"}
    )
    assert result.violated is False


def test_policy_set_ordering():
    """Test that policies are ordered by priority."""
    policy1 = Policy(
        policy_id="low-priority",
        scope="global",
        rule_type="constraint",
        condition={},
        priority=1,
    )
    policy2 = Policy(
        policy_id="high-priority",
        scope="global",
        rule_type="constraint",
        condition={},
        priority=10,
    )
    policy3 = Policy(
        policy_id="medium-priority",
        scope="global",
        rule_type="constraint",
        condition={},
        priority=5,
    )

    policy_set = PolicySet([policy1, policy2, policy3])

    # Should be ordered by priority descending
    assert policy_set.policies[0].policy_id == "high-priority"
    assert policy_set.policies[1].policy_id == "medium-priority"
    assert policy_set.policies[2].policy_id == "low-priority"


def test_policy_interpreter_load_gcn_rules():
    """Test loading and normalizing GCN rules."""
    interpreter = PolicyInterpreter()

    gcn_rules = [
        {
            "policy_id": "rule-1",
            "scope": "global",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete"]},
            "severity": "high",
            "priority": 10,
        },
        {
            "scope": "document",
            "rule_type": "requirement",
            "condition": {"required_fields": ["author"]},
            "severity": "medium",
            "priority": 5,
        },
    ]

    policy_set = interpreter.load_gcn_rules(gcn_rules)

    assert len(policy_set.policies) == 2
    assert policy_set.policies[0].policy_id == "rule-1"
    # Second policy should get auto-generated ID
    assert policy_set.policies[1].policy_id.startswith("policy-")


def test_policy_interpreter_check_policies():
    """Test checking candidate action against policy set."""
    interpreter = PolicyInterpreter()

    gcn_rules = [
        {
            "policy_id": "no-delete",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete"]},
            "severity": "high",
        },
        {
            "policy_id": "require-approval",
            "rule_type": "requirement",
            "condition": {"required_fields": ["approval"]},
            "severity": "medium",
        },
    ]

    policy_set = interpreter.load_gcn_rules(gcn_rules)
    candidate_action = {"action_type": "delete", "target": "file.txt"}

    results = interpreter.check_policies(candidate_action, policy_set)

    assert len(results) == 2
    # First should be violation (prohibition)
    assert results[0].violated is True
    assert results[0].severity == "high"
    # Second should be violation (missing approval)
    assert results[1].violated is True
    assert results[1].severity == "medium"


def test_deterministic_policy_checks():
    """Test that policy checks are deterministic."""
    policy = Policy(
        policy_id="test",
        scope="global",
        rule_type="prohibition",
        condition={"prohibited_actions": ["delete"]},
        severity="high",
    )

    action = {"action_type": "delete", "target": "test.txt"}

    # Run check multiple times
    results = [policy.check(action) for _ in range(3)]

    # All results should be identical
    for result in results[1:]:
        assert result.violated == results[0].violated
        assert result.reason == results[0].reason
        assert result.severity == results[0].severity
