# tests/rgk18/test_kernel_decision_flow.py
"""Tests for kernel decision flow."""

from oraculus_di_auditor.rgk18.kernel import GovernanceKernel


def test_kernel_high_severity_violation_immediate_reject():
    """Test that high severity violations trigger immediate reject."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "delete", "target": "critical_file.txt"}

    phase_inputs = {
        "phase12": {"coherence_score": 0.9},
        "phase13": {"probability": 0.95},
        "phase15": {"stability_score": 0.88},
        "phase17": {"global_ethics_score": 0.92},
        "phase11": {"risk_score": 0.1},
    }

    # Create policy set with high severity violation
    gcn_rules = [
        {
            "policy_id": "no-delete",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete"]},
            "severity": "high",
        }
    ]
    policy_set = kernel.policy_interpreter.load_gcn_rules(gcn_rules)

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs, policy_set
    )

    assert outcome.outcome == "REJECT"
    assert "high severity" in outcome.rationale.lower()
    assert score.score == 0.0
    assert any(v.violated and v.severity == "high" for v in violations)


def test_kernel_high_score_approve():
    """Test that high composite score leads to APPROVE."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "update", "target": "document.txt"}

    # High scores from all phases
    phase_inputs = {
        "phase12": {"coherence_score": 0.9},
        "phase13": {"probability": 0.95},
        "phase15": {"stability_score": 0.88},
        "phase17": {"global_ethics_score": 0.92},
        "phase11": {"risk_score": 0.05},  # Low risk = high score
    }

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs
    )

    assert outcome.outcome == "APPROVE"
    assert score.score >= 0.75  # Above APPROVE_THRESHOLD
    assert "meets approval threshold" in outcome.rationale.lower()


def test_kernel_conditional_approve():
    """Test conditional approval with medium severity violations."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "update", "target": "file.txt"}

    # High scores but medium violation
    phase_inputs = {
        "phase12": {"coherence_score": 0.85},
        "phase13": {"probability": 0.88},
        "phase15": {"stability_score": 0.82},
        "phase17": {"global_ethics_score": 0.87},
        "phase11": {"risk_score": 0.1},
    }

    gcn_rules = [
        {
            "policy_id": "require-approval",
            "rule_type": "requirement",
            "condition": {"required_fields": ["approval_token"]},
            "severity": "medium",
        }
    ]
    policy_set = kernel.policy_interpreter.load_gcn_rules(gcn_rules)

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs, policy_set
    )

    assert outcome.outcome == "CONDITIONAL_APPROVE"
    assert len(outcome.mitigations) > 0


def test_kernel_review_needed():
    """Test that borderline scores trigger manual review."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "complex_operation", "params": {}}

    # Medium scores that fall in review range
    phase_inputs = {
        "phase12": {"coherence_score": 0.45},
        "phase13": {"probability": 0.50},
        "phase15": {"stability_score": 0.42},
        "phase17": {"global_ethics_score": 0.48},
        "phase11": {"risk_score": 0.45},
    }

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs
    )

    assert outcome.outcome == "REVIEW"
    assert "manual review" in outcome.rationale.lower()
    assert 0.35 <= score.score < 0.55  # In review range


def test_kernel_reject_low_score():
    """Test that low scores trigger rejection."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "risky_operation", "level": "high"}

    # Low scores from all phases
    phase_inputs = {
        "phase12": {"coherence_score": 0.2},
        "phase13": {"probability": 0.15},
        "phase15": {"stability_score": 0.25},
        "phase17": {"global_ethics_score": 0.18},
        "phase11": {"risk_score": 0.85},  # High risk = low score
    }

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs
    )

    assert outcome.outcome == "REJECT"
    assert score.score < 0.35  # Below REVIEW_THRESHOLD
    assert "below minimum threshold" in outcome.rationale.lower()


def test_kernel_determinism():
    """Test that kernel produces identical results for identical inputs."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "test", "value": 42}

    phase_inputs = {
        "phase12": {"coherence_score": 0.75},
        "phase13": {"probability": 0.82},
        "phase15": {"stability_score": 0.68},
        "phase17": {"global_ethics_score": 0.79},
        "phase11": {"risk_score": 0.22},
    }

    # Run evaluation multiple times
    results = [kernel.evaluate(candidate_action, phase_inputs) for _ in range(3)]

    # All results should be identical
    for i in range(1, len(results)):
        outcome, score, violations, provenance = results[i]
        outcome0, score0, violations0, provenance0 = results[0]

        assert outcome.outcome == outcome0.outcome
        assert outcome.rationale == outcome0.rationale
        assert score.score == score0.score
        assert score.components == score0.components
        assert len(violations) == len(violations0)
        # Provenance seed and input_hash should be identical
        assert provenance["seed"] == provenance0["seed"]
        assert provenance["input_hash"] == provenance0["input_hash"]


def test_kernel_missing_phase_inputs():
    """Test kernel behavior with missing phase inputs (conservative fallback)."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "test"}

    # Incomplete phase inputs
    phase_inputs = {
        "phase12": {"coherence_score": 0.8},
        # phase13, phase15, phase17, phase11 missing
    }

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs
    )

    # Should handle gracefully with neutral defaults
    assert outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE", "REVIEW", "REJECT"]
    assert 0.0 <= score.score <= 1.0
    # Missing evidence should be handled with 0.5 (neutral) defaults


def test_kernel_provenance_metadata():
    """Test that provenance metadata is complete."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "test"}
    phase_inputs = {"phase12": {"coherence_score": 0.7}}

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs
    )

    # Check provenance fields
    assert "seed" in provenance
    assert "input_hash" in provenance
    assert "timestamp" in provenance
    assert "service_version" in provenance
    assert isinstance(provenance["seed"], int)
    assert len(provenance["input_hash"]) == 64  # SHA256 hex


def test_kernel_mitigation_generation():
    """Test that mitigations are generated for violations."""
    kernel = GovernanceKernel()

    candidate_action = {"action_type": "update"}

    phase_inputs = {
        "phase12": {"coherence_score": 0.65},
        "phase13": {"probability": 0.68},
        "phase15": {"stability_score": 0.62},
        "phase17": {"global_ethics_score": 0.70},
        "phase11": {"risk_score": 0.3},
    }

    gcn_rules = [
        {
            "policy_id": "require-fields",
            "rule_type": "requirement",
            "condition": {"required_fields": ["approval", "user_id"]},
            "severity": "medium",
        }
    ]
    policy_set = kernel.policy_interpreter.load_gcn_rules(gcn_rules)

    outcome, score, violations, provenance = kernel.evaluate(
        candidate_action, phase_inputs, policy_set
    )

    # Should have mitigations for violations
    if outcome.outcome == "CONDITIONAL_APPROVE":
        assert len(outcome.mitigations) > 0
        assert any(
            "approval" in m.lower() or "user_id" in m.lower()
            for m in outcome.mitigations
        )
