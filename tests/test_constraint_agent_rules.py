from __future__ import annotations

from oraculus_di_auditor.gcn.policy_registry import PolicyRegistry
from oraculus_di_auditor.mesh.agent_types import ConstraintAgent


class TestConstraintAgentRuleValidation:
    def setup_method(self):
        self.agent = ConstraintAgent()
        self.registry = PolicyRegistry()

    def _run(self, entity: dict, rule_ids: list[str]):
        rules = [self.registry.get_rule(rid) for rid in rule_ids]
        task = {"type": "validate", "entity": entity, "rules": rules}
        return self.agent.execute_task(task)

    def test_required_fields_violation(self):
        result = self._run(
            entity={"document_text": "abc"}, rule_ids=["gcn:structural:required-fields"]
        )
        assert result["valid"] is False
        assert any(
            v["rule_id"] == "gcn:structural:required-fields"
            for v in result["violations"]
        )

    def test_required_fields_pass(self):
        entity = {"document_text": "abc", "metadata": {"title": "Doc"}}
        result = self._run(entity=entity, rule_ids=["gcn:structural:required-fields"])
        assert result["valid"] is True
        assert result["violations"] == []

    def test_min_length_violation(self):
        entity = {"document_text": "short", "metadata": {"title": "X"}}
        # default min_length is 10; length 5 should fail
        result = self._run(entity=entity, rule_ids=["gcn:document:min-length"])
        assert result["valid"] is False
        assert any(
            v["rule_id"] == "gcn:document:min-length" for v in result["violations"]
        )

    def test_min_length_pass(self):
        entity = {"document_text": "long enough text", "metadata": {"title": "X"}}
        result = self._run(entity=entity, rule_ids=["gcn:document:min-length"])
        assert result["valid"] is True

    def test_allowed_values_violation(self):
        entity = {"status": "bad_status"}
        result = self._run(entity=entity, rule_ids=["gcn:policy:agent-status"])
        assert result["valid"] is False
        assert any(
            v["rule_id"] == "gcn:policy:agent-status" for v in result["violations"]
        )

    def test_allowed_values_pass(self):
        entity = {"status": "active"}
        result = self._run(entity=entity, rule_ids=["gcn:policy:agent-status"])
        assert result["valid"] is True

    def test_value_range_violation(self):
        entity = {"threat_score": 0.9}
        result = self._run(entity=entity, rule_ids=["gcn:policy:threat-score"])
        assert result["valid"] is False
        assert any(
            v["rule_id"] == "gcn:policy:threat-score" for v in result["violations"]
        )

    def test_value_range_pass(self):
        entity = {"threat_score": 0.2}
        result = self._run(entity=entity, rule_ids=["gcn:policy:threat-score"])
        assert result["valid"] is True
