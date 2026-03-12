from oraculus_di_auditor.mesh.agent_types import ConstraintAgent


def test_constraint_value_range_pass_and_fail():
    agent = ConstraintAgent()
    # Rule requires score between 0 and 100 inclusive
    rule = {
        "rule_id": "score-range-1",
        "rule_name": "Score Range",
        "constraint_expression": "value_range",
        "rule_config": {"value_ranges": {"score": (0, 100)}},
    }

    entity_pass = {"score": 50}
    entity_fail_low = {"score": -1}
    entity_fail_high = {"score": 150}

    assert agent._check_rule(entity_pass, rule) is True
    assert agent._check_rule(entity_fail_low, rule) is False
    assert agent._check_rule(entity_fail_high, rule) is False
