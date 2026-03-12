# tests/rgk18/test_rollback_manager.py
"""Tests for rollback manager."""

from oraculus_di_auditor.rgk18.ledger import Ledger
from oraculus_di_auditor.rgk18.rollback_manager import RollbackManager


def test_rollback_manager_initialization():
    """Test rollback manager initialization."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    assert len(manager.applied_decisions) == 0
    assert len(manager.rollback_attempts) == 0


def test_mark_applied():
    """Test marking a decision as applied."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    reverse_patch = {"operation": "restore", "data": {"key": "value"}}
    manager.mark_applied("decision-1", reverse_patch)

    assert manager.is_applied("decision-1") is True
    assert manager.applied_decisions["decision-1"]["reverse_patch"] == reverse_patch
    assert manager.applied_decisions["decision-1"]["applied"] is True


def test_is_applied():
    """Test checking if a decision is applied."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    assert manager.is_applied("decision-1") is False

    manager.mark_applied("decision-1")
    assert manager.is_applied("decision-1") is True


def test_rollback_dry_run():
    """Test rollback in dry run mode."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    reverse_patch = {"operation": "undo"}
    manager.mark_applied("decision-1", reverse_patch)

    result = manager.rollback("decision-1", dry_run=True)

    assert result["success"] is True
    assert result["dry_run"] is True
    assert "validated" in result["message"].lower()
    # Decision should still be applied after dry run
    assert manager.is_applied("decision-1") is True


def test_rollback_not_applied():
    """Test rolling back a decision that wasn't applied."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    result = manager.rollback("non-existent-decision", dry_run=True)

    assert result["success"] is False
    assert "not applied" in result["error"].lower()


def test_rollback_no_reverse_patch():
    """Test rolling back without a reverse patch."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch=None)

    result = manager.rollback("decision-1", dry_run=True)

    assert result["success"] is False
    assert "no reverse patch" in result["error"].lower()


def test_rollback_requires_governor_approval():
    """Test that actual rollback requires governor approval."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch={"operation": "undo"})

    # Try rollback without approval (dry_run=False)
    result = manager.rollback("decision-1", dry_run=False, governor_approval=None)

    assert result["success"] is False
    assert "governor approval required" in result["error"].lower()


def test_rollback_with_approval():
    """Test successful rollback with governor approval."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch={"operation": "undo"})

    # Rollback with approval
    result = manager.rollback(
        "decision-1", dry_run=False, governor_approval="valid-token"
    )

    assert result["success"] is True
    assert result["dry_run"] is False
    assert "applied successfully" in result["message"].lower()
    # Decision should no longer be marked as applied
    assert manager.applied_decisions["decision-1"]["applied"] is False
    assert manager.applied_decisions["decision-1"]["rolled_back"] is True


def test_rollback_attempts_tracking():
    """Test that rollback attempts are tracked."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch={"operation": "undo"})

    # First rollback
    result1 = manager.rollback("decision-1", dry_run=False, governor_approval="token")
    assert result1["success"] is True
    assert result1["attempts"] == 1

    # After rollback, the decision is no longer applied
    # In a real scenario, you would create a new decision for a second rollback
    # This test verifies that the attempt counter persists
    assert manager.rollback_attempts["decision-1"] == 1


def test_rollback_max_attempts():
    """Test that rollback respects max attempts limit."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch={"operation": "undo"})

    # Manually set attempts to max
    from oraculus_di_auditor.rgk18.constants import MAX_ROLLBACK_ATTEMPTS

    manager.rollback_attempts["decision-1"] = MAX_ROLLBACK_ATTEMPTS

    result = manager.rollback("decision-1", dry_run=True)

    assert result["success"] is False
    assert "maximum rollback attempts" in result["error"].lower()


def test_get_applied_decisions():
    """Test getting list of applied decisions."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    manager.mark_applied("decision-1", reverse_patch={"op": "undo1"})
    manager.mark_applied("decision-2", reverse_patch={"op": "undo2"})
    manager.mark_applied("decision-3", reverse_patch={"op": "undo3"})

    # Rollback decision-2 using proper API
    manager.rollback("decision-2", dry_run=False, governor_approval="token")

    applied = manager.get_applied_decisions()

    assert len(applied) == 2
    assert "decision-1" in applied
    assert "decision-3" in applied
    assert "decision-2" not in applied


def test_get_rollback_status():
    """Test getting rollback status for a decision."""
    ledger = Ledger()
    manager = RollbackManager(ledger)

    # Non-existent decision
    status1 = manager.get_rollback_status("non-existent")
    assert status1["exists"] is False

    # Applied decision
    manager.mark_applied("decision-1", reverse_patch={"data": "test"})
    status2 = manager.get_rollback_status("decision-1")
    assert status2["exists"] is True
    assert status2["applied"] is True
    assert status2["rolled_back"] is False
    assert status2["attempts"] == 0
    assert status2["has_reverse_patch"] is True

    # Decision without reverse patch
    manager.mark_applied("decision-2", reverse_patch=None)
    status3 = manager.get_rollback_status("decision-2")
    assert status3["has_reverse_patch"] is False


def test_rollback_integration_with_ledger():
    """Test rollback manager integration with ledger."""
    from oraculus_di_auditor.rgk18.schemas import (
        DecisionOutcome,
        DecisionScore,
    )

    ledger = Ledger()
    manager = RollbackManager(ledger)

    # Add entry to ledger
    entry_data = {
        "entry_id": "test-decision",
        "input_hash": "x" * 64,
        "decision": DecisionOutcome(
            outcome="APPROVE", rationale="Test", mitigations=[]
        ),
        "score": DecisionScore(score=0.85, components={}),
        "policies_checked": [],
        "provenance": {},
    }
    ledger.append(entry_data)

    # Mark as applied
    manager.mark_applied("test-decision", reverse_patch={"undo": "data"})

    # Verify ledger entry exists and decision is applied
    entry = ledger.get_entry("test-decision")
    assert entry is not None
    assert manager.is_applied("test-decision") is True

    # Rollback
    result = manager.rollback("test-decision", dry_run=False, governor_approval="token")

    assert result["success"] is True
    assert manager.applied_decisions["test-decision"]["rolled_back"] is True
