"""Tests for Phase 10 Constraint Validator and Policy Registry."""

from __future__ import annotations


class TestConstraintValidator:
    """Tests for ConstraintValidator."""

    def test_validator_initialization(self):
        """Test ConstraintValidator can be initialized."""
        from oraculus_di_auditor.gcn import ConstraintValidator

        validator = ConstraintValidator()
        assert validator is not None
        assert validator.validation_cache == {}

    def test_validate_entity_with_no_rules(self):
        """Test validation with empty rules list."""
        from oraculus_di_auditor.gcn import ConstraintValidator

        validator = ConstraintValidator()
        result = validator.validate_entity(
            entity_type="document",
            entity_id="test",
            entity_data={"document_text": "test"},
            rules=[],
        )

        assert result["valid"] is True
        assert result["rules_evaluated"] == 0
        assert len(result["violations"]) == 0

    def test_validate_structural_constraint_required_fields(self):
        """Test structural constraint for required fields."""
        from oraculus_di_auditor.gcn import ConstraintValidator

        validator = ConstraintValidator()
        rule = {
            "rule_id": "test-rule",
            "rule_name": "Test Required Fields",
            "rule_type": "structural",
            "enabled": True,
            "scope": "global",
            "priority": 10,
            "constraint_expression": "required_fields",
            "violation_action": "block",
            "severity": "error",
            "rule_config": {"required_fields": ["field1", "field2"]},
        }

        # Entity missing required fields
        result = validator.validate_entity(
            entity_type="document",
            entity_id="test",
            entity_data={},
            rules=[rule],
        )

        assert not result["valid"]
        assert len(result["violations"]) == 1

    def test_validate_document_length_constraints(self):
        """Test document length constraints."""
        from oraculus_di_auditor.gcn import ConstraintValidator

        validator = ConstraintValidator()
        rule = {
            "rule_id": "doc-length",
            "rule_name": "Document Length",
            "rule_type": "document",
            "enabled": True,
            "scope": "document",
            "priority": 10,
            "constraint_expression": "min_length",
            "violation_action": "block",
            "severity": "error",
            "rule_config": {"min_length": 100},
        }

        result = validator.validate_entity(
            entity_type="document",
            entity_id="short-doc",
            entity_data={"document_text": "Short"},
            rules=[rule],
            scope="document",  # Set scope explicitly to match rule
        )

        assert not result["valid"]
        assert result["blocked"] is True

    def test_rule_priority_ordering(self):
        """Test that rules are evaluated by priority."""
        from oraculus_di_auditor.gcn import ConstraintValidator

        validator = ConstraintValidator()
        rules = [
            {
                "rule_id": "low-priority",
                "rule_name": "Low Priority",
                "rule_type": "structural",
                "enabled": True,
                "scope": "global",
                "priority": 1,
                "constraint_expression": "required_fields",
                "violation_action": "warn",
                "severity": "warning",
                "rule_config": {},
            },
            {
                "rule_id": "high-priority",
                "rule_name": "High Priority",
                "rule_type": "structural",
                "enabled": True,
                "scope": "global",
                "priority": 100,
                "constraint_expression": "required_fields",
                "violation_action": "block",
                "severity": "error",
                "rule_config": {},
            },
        ]

        result = validator.validate_entity(
            entity_type="document",
            entity_id="test",
            entity_data={"document_text": "test"},
            rules=rules,
        )

        # Both rules should be evaluated
        assert result["rules_evaluated"] == 2


class TestPolicyRegistry:
    """Tests for PolicyRegistry."""

    def test_registry_initialization(self):
        """Test PolicyRegistry initialization with default rules."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        assert registry is not None
        assert registry.version == "1.0.0"
        # Should have loaded default rules
        assert len(registry.get_all_rules()) > 0

    def test_register_new_rule(self):
        """Test registering a new rule."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        initial_count = len(registry.get_all_rules())

        rule = {
            "rule_id": "custom-rule",
            "rule_name": "Custom Test Rule",
            "rule_type": "policy",
            "rule_version": "1.0.0",
            "enabled": True,
            "priority": 50,
            "scope": "global",
            "constraint_expression": "test",
            "violation_action": "warn",
            "severity": "warning",
        }

        result = registry.register_rule(rule)
        assert result is True
        assert len(registry.get_all_rules()) == initial_count + 1

    def test_get_rule_by_id(self):
        """Test retrieving a specific rule."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        rule = registry.get_rule("gcn:document:min-length")
        assert rule is not None
        assert rule["rule_id"] == "gcn:document:min-length"

    def test_get_rules_by_type(self):
        """Test retrieving rules by type."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        document_rules = registry.get_rules_by_type("document")
        assert len(document_rules) > 0
        assert all(r["rule_type"] == "document" for r in document_rules)

    def test_get_rules_by_scope(self):
        """Test retrieving rules by scope."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        global_rules = registry.get_rules_by_scope("global")
        # Should include rules with both global and specified scope
        assert len(global_rules) > 0

    def test_enable_disable_rule(self):
        """Test enabling and disabling rules."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        rule_id = "gcn:document:min-length"

        # Disable rule
        result = registry.disable_rule(rule_id)
        assert result is True
        rule = registry.get_rule(rule_id)
        assert rule["enabled"] is False

        # Enable rule
        result = registry.enable_rule(rule_id)
        assert result is True
        rule = registry.get_rule(rule_id)
        assert rule["enabled"] is True

    def test_get_registry_state(self):
        """Test getting registry state."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        state = registry.get_registry_state()

        assert "timestamp" in state
        assert "registry_version" in state
        assert "rules_total" in state
        assert "rules_active" in state
        assert "rules_by_type" in state
        assert isinstance(state["rules_by_type"], dict)

    def test_register_duplicate_rule(self):
        """Test registering a rule with duplicate ID updates it."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()
        rule_id = "duplicate-test"

        rule1 = {
            "rule_id": rule_id,
            "rule_name": "First Version",
            "rule_type": "policy",
            "rule_version": "1.0.0",
            "enabled": True,
            "priority": 10,
            "scope": "global",
            "constraint_expression": "test",
            "violation_action": "warn",
        }

        rule2 = {
            "rule_id": rule_id,
            "rule_name": "Second Version",
            "rule_type": "policy",
            "rule_version": "2.0.0",
            "enabled": True,
            "priority": 20,
            "scope": "global",
            "constraint_expression": "test",
            "violation_action": "block",
        }

        registry.register_rule(rule1)
        registry.register_rule(rule2)

        # Should have the updated version
        rule = registry.get_rule(rule_id)
        assert rule["rule_name"] == "Second Version"
        assert rule["rule_version"] == "2.0.0"

    def test_filter_enabled_rules(self):
        """Test filtering for only enabled rules."""
        from oraculus_di_auditor.gcn import PolicyRegistry

        registry = PolicyRegistry()

        # Disable a rule
        registry.disable_rule("gcn:document:min-length")

        all_rules = registry.get_all_rules(enabled_only=False)
        enabled_rules = registry.get_all_rules(enabled_only=True)

        assert len(enabled_rules) < len(all_rules)


__all__ = ["TestConstraintValidator", "TestPolicyRegistry"]
