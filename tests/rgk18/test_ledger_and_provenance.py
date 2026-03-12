# tests/rgk18/test_ledger_and_provenance.py
"""Tests for ledger and provenance tracking."""

from oraculus_di_auditor.rgk18.ledger import Ledger
from oraculus_di_auditor.rgk18.schemas import (
    DecisionOutcome,
    DecisionScore,
    PolicyCheckResult,
)


def test_ledger_initialization():
    """Test ledger initialization."""
    ledger = Ledger()

    assert len(ledger.entries) == 0
    assert ledger.last_signature is not None
    assert len(ledger.last_signature) == 64  # SHA256 hex


def test_ledger_append_entry():
    """Test appending an entry to the ledger."""
    ledger = Ledger()

    entry_data = {
        "entry_id": "test-entry-1",
        "input_hash": "abc123" * 10 + "abcd",  # 64 chars
        "decision": DecisionOutcome(
            outcome="APPROVE",
            rationale="Test approval",
            mitigations=[],
        ),
        "score": DecisionScore(
            score=0.85,
            components={"test": 0.85},
        ),
        "policies_checked": [],
        "provenance": {"seed": 12345, "timestamp": "2024-01-01T00:00:00Z"},
    }

    entry = ledger.append(entry_data)

    assert entry.entry_id == "test-entry-1"
    assert entry.signature is not None
    assert len(entry.signature) == 64  # SHA256 hex
    assert len(ledger.entries) == 1


def test_ledger_chain_signature():
    """Test that signatures chain correctly."""
    ledger = Ledger()

    # Append first entry
    entry1_data = {
        "entry_id": "entry-1",
        "input_hash": "a" * 64,
        "decision": DecisionOutcome(
            outcome="APPROVE", rationale="Test", mitigations=[]
        ),
        "score": DecisionScore(score=0.8, components={}),
        "policies_checked": [],
        "provenance": {},
    }
    entry1 = ledger.append(entry1_data)
    sig1 = entry1.signature

    # Append second entry
    entry2_data = {
        "entry_id": "entry-2",
        "input_hash": "b" * 64,
        "decision": DecisionOutcome(outcome="REJECT", rationale="Test", mitigations=[]),
        "score": DecisionScore(score=0.2, components={}),
        "policies_checked": [],
        "provenance": {},
    }
    entry2 = ledger.append(entry2_data)
    sig2 = entry2.signature

    # Signatures should be different and entry2 should depend on entry1
    assert sig1 != sig2
    assert ledger.last_signature == sig2


def test_ledger_get_entry():
    """Test retrieving an entry by ID."""
    ledger = Ledger()

    entry_data = {
        "entry_id": "test-entry-retrieve",
        "input_hash": "x" * 64,
        "decision": DecisionOutcome(outcome="REVIEW", rationale="Test", mitigations=[]),
        "score": DecisionScore(score=0.5, components={}),
        "policies_checked": [],
        "provenance": {},
    }
    ledger.append(entry_data)

    # Retrieve entry
    retrieved = ledger.get_entry("test-entry-retrieve")
    assert retrieved is not None
    assert retrieved.entry_id == "test-entry-retrieve"

    # Try non-existent entry
    not_found = ledger.get_entry("non-existent")
    assert not_found is None


def test_ledger_get_chain_proof():
    """Test getting chain proof for an entry."""
    ledger = Ledger()

    # Add three entries
    for i in range(3):
        entry_data = {
            "entry_id": f"entry-{i}",
            "input_hash": str(i) * 64,
            "decision": DecisionOutcome(
                outcome="APPROVE", rationale="Test", mitigations=[]
            ),
            "score": DecisionScore(score=0.7, components={}),
            "policies_checked": [],
            "provenance": {},
        }
        ledger.append(entry_data)

    # Get proof for second entry
    proof = ledger.get_chain_proof("entry-1")

    assert len(proof) == 2  # Should include entries 0 and 1
    assert proof[0].entry_id == "entry-0"
    assert proof[1].entry_id == "entry-1"


def test_ledger_verify_chain():
    """Test verifying the integrity of the ledger chain."""
    ledger = Ledger()

    # Add multiple entries
    for i in range(5):
        entry_data = {
            "entry_id": f"entry-{i}",
            "input_hash": f"{i}" * 64,
            "decision": DecisionOutcome(
                outcome="APPROVE", rationale="Test", mitigations=[]
            ),
            "score": DecisionScore(score=0.75, components={}),
            "policies_checked": [],
            "provenance": {"index": i},
        }
        ledger.append(entry_data)

    # Chain should be valid
    assert ledger.verify_chain() is True


def test_ledger_deterministic_signatures():
    """Test that signatures are deterministic for same data."""
    # Create two ledgers with identical entries
    ledger1 = Ledger()
    ledger2 = Ledger()

    entry_data = {
        "entry_id": "deterministic-test",
        "input_hash": "d" * 64,
        "decision": DecisionOutcome(
            outcome="APPROVE", rationale="Test", mitigations=[]
        ),
        "score": DecisionScore(score=0.88, components={"test": 0.88}),
        "policies_checked": [
            PolicyCheckResult(
                policy_id="test-policy",
                violated=False,
                reason=None,
                severity="low",
            )
        ],
        "provenance": {"seed": 999, "version": "test"},
    }

    entry1 = ledger1.append(entry_data)
    entry2 = ledger2.append(entry_data)

    # Signatures should be identical
    assert entry1.signature == entry2.signature


def test_ledger_get_all_entries():
    """Test getting all ledger entries."""
    ledger = Ledger()

    # Add entries
    for i in range(3):
        entry_data = {
            "entry_id": f"entry-{i}",
            "input_hash": f"{i}" * 64,
            "decision": DecisionOutcome(
                outcome="APPROVE", rationale="Test", mitigations=[]
            ),
            "score": DecisionScore(score=0.8, components={}),
            "policies_checked": [],
            "provenance": {},
        }
        ledger.append(entry_data)

    all_entries = ledger.get_all_entries()

    assert len(all_entries) == 3
    assert all_entries[0].entry_id == "entry-0"
    assert all_entries[1].entry_id == "entry-1"
    assert all_entries[2].entry_id == "entry-2"


def test_ledger_with_policy_violations():
    """Test ledger entry with policy violations."""
    ledger = Ledger()

    violations = [
        PolicyCheckResult(
            policy_id="policy-1",
            violated=True,
            reason="Missing required field",
            severity="medium",
        ),
        PolicyCheckResult(
            policy_id="policy-2",
            violated=False,
            reason=None,
            severity="low",
        ),
    ]

    entry_data = {
        "entry_id": "entry-with-violations",
        "input_hash": "v" * 64,
        "decision": DecisionOutcome(
            outcome="CONDITIONAL_APPROVE",
            rationale="Violations present but score acceptable",
            mitigations=["Fix missing field"],
        ),
        "score": DecisionScore(score=0.65, components={}),
        "policies_checked": violations,
        "provenance": {"test": True},
    }

    entry = ledger.append(entry_data)

    assert len(entry.policies_checked) == 2
    assert entry.policies_checked[0].violated is True
    assert entry.policies_checked[1].violated is False


def test_ledger_provenance_persistence():
    """Test that provenance metadata persists in ledger."""
    ledger = Ledger()

    provenance = {
        "seed": 42,
        "input_hash": "test-hash",
        "timestamp": "2024-01-01T12:00:00Z",
        "service_version": "rgk18-0.1.0",
        "custom_field": "custom_value",
    }

    entry_data = {
        "entry_id": "provenance-test",
        "input_hash": "p" * 64,
        "decision": DecisionOutcome(
            outcome="APPROVE", rationale="Test", mitigations=[]
        ),
        "score": DecisionScore(score=0.9, components={}),
        "policies_checked": [],
        "provenance": provenance,
    }

    ledger.append(entry_data)

    # Retrieve and verify provenance
    retrieved = ledger.get_entry("provenance-test")
    assert retrieved is not None
    assert retrieved.provenance["seed"] == 42
    assert retrieved.provenance["custom_field"] == "custom_value"
