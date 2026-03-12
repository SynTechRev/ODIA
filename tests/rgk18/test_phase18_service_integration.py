# tests/rgk18/test_phase18_service_integration.py
"""Integration tests for Phase 18 service."""

from oraculus_di_auditor.rgk18.service import Phase18Service


def test_service_initialization():
    """Test Phase 18 service initialization."""
    service = Phase18Service()

    assert service.policy_interpreter is not None
    assert service.consensus_engine is not None
    assert service.kernel is not None
    assert service.ledger is not None
    assert service.rollback_manager is not None


def test_service_evaluate_basic():
    """Test basic service evaluation."""
    service = Phase18Service()

    candidate_action = {"action_type": "update", "target": "document.txt"}

    phase_inputs = {
        "phase12": {"coherence_score": 0.8},
        "phase13": {"probability": 0.85},
        "phase15": {"stability_score": 0.78},
        "phase17": {"global_ethics_score": 0.82},
        "phase11": {"risk_score": 0.15},
    }

    result = service.evaluate(candidate_action, phase_inputs)

    assert result.outcome is not None
    assert result.score is not None
    assert result.ledger_entry_id is not None
    assert result.provenance is not None
    assert 0.0 <= result.score.score <= 1.0


def test_service_evaluate_with_gcn_rules():
    """Test evaluation with GCN rules."""
    service = Phase18Service()

    candidate_action = {"action_type": "delete", "target": "file.txt"}

    phase_inputs = {
        "phase12": {"coherence_score": 0.9},
        "phase13": {"probability": 0.95},
        "phase15": {"stability_score": 0.88},
        "phase17": {"global_ethics_score": 0.92},
        "phase11": {"risk_score": 0.05},
    }

    gcn_rules = [
        {
            "policy_id": "no-delete",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete"]},
            "severity": "high",
        }
    ]

    result = service.evaluate(candidate_action, phase_inputs, gcn_rules=gcn_rules)

    assert result.outcome.outcome == "REJECT"
    assert len(result.policy_violations) > 0
    assert result.policy_violations[0].severity == "high"


def test_service_dry_run_default():
    """Test that dry_run is True by default."""
    service = Phase18Service()

    candidate_action = {"action_type": "test"}
    phase_inputs = {"phase12": {"coherence_score": 0.8}}

    result = service.evaluate(candidate_action, phase_inputs)

    # Check ledger entry metadata
    entry = service.ledger.get_entry(result.ledger_entry_id)
    assert entry.provenance["dry_run"] is True


def test_service_commit_requires_approval():
    """Test that commit requires governor approval."""
    service = Phase18Service()

    candidate_action = {"action_type": "update", "target": "test.txt"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.85},
        "phase13": {"probability": 0.88},
        "phase15": {"stability_score": 0.82},
        "phase17": {"global_ethics_score": 0.87},
        "phase11": {"risk_score": 0.1},
    }

    result = service.evaluate(candidate_action, phase_inputs)

    # Try to commit without approval
    commit_result = service.commit(result.ledger_entry_id, governor_approval=None)

    assert commit_result["success"] is False
    assert "governor approval required" in commit_result["error"].lower()


def test_service_commit_with_approval():
    """Test successful commit with governor approval."""
    service = Phase18Service()

    candidate_action = {"action_type": "update", "target": "test.txt"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.85},
        "phase13": {"probability": 0.88},
        "phase15": {"stability_score": 0.82},
        "phase17": {"global_ethics_score": 0.87},
        "phase11": {"risk_score": 0.1},
    }

    # Evaluate (should be APPROVE or CONDITIONAL_APPROVE with high scores)
    result = service.evaluate(candidate_action, phase_inputs)

    if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
        # Commit with approval
        commit_result = service.commit(
            result.ledger_entry_id, governor_approval="valid-token"
        )

        assert commit_result["success"] is True
        assert "committed successfully" in commit_result["message"].lower()


def test_service_commit_reject_not_allowed():
    """Test that REJECT decisions cannot be committed."""
    service = Phase18Service()

    candidate_action = {"action_type": "delete"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.2},
        "phase13": {"probability": 0.15},
        "phase15": {"stability_score": 0.18},
        "phase17": {"global_ethics_score": 0.22},
        "phase11": {"risk_score": 0.85},
    }

    gcn_rules = [
        {
            "policy_id": "no-delete",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete"]},
            "severity": "high",
        }
    ]

    result = service.evaluate(candidate_action, phase_inputs, gcn_rules=gcn_rules)

    assert result.outcome.outcome == "REJECT"

    # Try to commit
    commit_result = service.commit(result.ledger_entry_id, governor_approval="token")

    assert commit_result["success"] is False
    assert "cannot commit" in commit_result["error"].lower()


def test_service_rollback():
    """Test service rollback functionality."""
    service = Phase18Service()

    candidate_action = {"action_type": "update"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.85},
        "phase13": {"probability": 0.88},
        "phase15": {"stability_score": 0.82},
        "phase17": {"global_ethics_score": 0.87},
        "phase11": {"risk_score": 0.1},
    }

    # Evaluate and commit
    result = service.evaluate(candidate_action, phase_inputs)

    if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
        service.commit(result.ledger_entry_id, governor_approval="token")

        # Try rollback (dry run)
        rollback_result = service.rollback(result.ledger_entry_id, dry_run=True)

        assert rollback_result["success"] is True
        assert rollback_result["dry_run"] is True


def test_service_auto_apply():
    """Test auto_apply with governor approval."""
    service = Phase18Service()

    candidate_action = {"action_type": "safe_operation"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.9},
        "phase13": {"probability": 0.95},
        "phase15": {"stability_score": 0.88},
        "phase17": {"global_ethics_score": 0.92},
        "phase11": {"risk_score": 0.05},
    }

    # Evaluate with auto_apply and governor approval
    result = service.evaluate(
        candidate_action,
        phase_inputs,
        dry_run=False,
        auto_apply=True,
        governor_approval="valid-token",
    )

    if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
        # Should be marked as applied
        assert service.rollback_manager.is_applied(result.ledger_entry_id)


def test_service_get_ledger_entry():
    """Test retrieving ledger entry."""
    service = Phase18Service()

    candidate_action = {"action_type": "test"}
    phase_inputs = {"phase12": {"coherence_score": 0.75}}

    result = service.evaluate(candidate_action, phase_inputs)

    # Retrieve entry
    entry_dict = service.get_ledger_entry(result.ledger_entry_id)

    assert entry_dict is not None
    assert entry_dict["entry_id"] == result.ledger_entry_id
    assert "decision" in entry_dict
    assert "score" in entry_dict


def test_service_verify_ledger():
    """Test ledger verification."""
    service = Phase18Service()

    # Add multiple entries
    for i in range(5):
        candidate_action = {"action_type": f"test-{i}"}
        phase_inputs = {"phase12": {"coherence_score": 0.7 + i * 0.02}}
        service.evaluate(candidate_action, phase_inputs)

    # Verify ledger integrity
    assert service.verify_ledger() is True


def test_service_get_all_ledger_entries():
    """Test getting all ledger entries."""
    service = Phase18Service()

    # Add entries
    for i in range(3):
        candidate_action = {"action_type": f"action-{i}"}
        phase_inputs = {"phase12": {"coherence_score": 0.8}}
        service.evaluate(candidate_action, phase_inputs)

    all_entries = service.get_all_ledger_entries()

    assert len(all_entries) == 3
    assert all(isinstance(entry, dict) for entry in all_entries)


def test_service_determinism():
    """Test that service produces deterministic results."""
    # Create two independent service instances
    service1 = Phase18Service()
    service2 = Phase18Service()

    candidate_action = {"action_type": "test", "value": 42}
    phase_inputs = {
        "phase12": {"coherence_score": 0.75},
        "phase13": {"probability": 0.82},
        "phase15": {"stability_score": 0.68},
        "phase17": {"global_ethics_score": 0.79},
        "phase11": {"risk_score": 0.22},
    }

    result1 = service1.evaluate(candidate_action, phase_inputs)
    result2 = service2.evaluate(candidate_action, phase_inputs)

    # Outcomes should be identical
    assert result1.outcome.outcome == result2.outcome.outcome
    assert result1.outcome.rationale == result2.outcome.rationale
    assert result1.score.score == result2.score.score
    assert result1.score.components == result2.score.components
    assert result1.provenance["seed"] == result2.provenance["seed"]
    assert result1.provenance["input_hash"] == result2.provenance["input_hash"]


def test_service_custom_weights():
    """Test service with custom consensus weights."""
    custom_weights = {
        "scalar_harmonics": 0.5,
        "qdcl_probability": 0.3,
        "temporal_stability": 0.1,
        "ethical_score": 0.1,
        "self_healing_risk": 0.0,
    }

    service = Phase18Service(custom_weights=custom_weights)

    candidate_action = {"action_type": "test"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.9},  # High weight
        "phase13": {"probability": 0.5},  # Medium weight
        "phase15": {"stability_score": 0.5},  # Low weight
        "phase17": {"global_ethics_score": 0.5},  # Low weight
        "phase11": {"risk_score": 0.5},  # Zero weight
    }

    result = service.evaluate(candidate_action, phase_inputs)

    # Score should be heavily influenced by scalar_harmonics
    assert result.score.score > 0.7  # Should be closer to 0.9 than 0.5


def test_service_complete_workflow():
    """Test complete workflow: evaluate -> commit -> rollback."""
    service = Phase18Service()

    candidate_action = {"action_type": "workflow_test"}
    phase_inputs = {
        "phase12": {"coherence_score": 0.85},
        "phase13": {"probability": 0.88},
        "phase15": {"stability_score": 0.82},
        "phase17": {"global_ethics_score": 0.87},
        "phase11": {"risk_score": 0.1},
    }

    # Step 1: Evaluate
    result = service.evaluate(candidate_action, phase_inputs, dry_run=False)
    assert result.ledger_entry_id is not None

    # Step 2: Commit (if approvable)
    if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
        commit_result = service.commit(
            result.ledger_entry_id, governor_approval="token"
        )
        assert commit_result["success"] is True

        # Step 3: Rollback
        rollback_result = service.rollback(
            result.ledger_entry_id, dry_run=False, governor_approval="token"
        )
        assert rollback_result["success"] is True
        assert rollback_result["dry_run"] is False
