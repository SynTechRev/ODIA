#!/usr/bin/env python
"""Example script demonstrating Phase 18 (RGK-18) Recursive Governance Kernel.

This script shows the complete workflow:
1. Evaluate a candidate action
2. Commit the decision with governor approval
3. Rollback if needed
"""

from oraculus_di_auditor.rgk18 import Phase18Service


def example_1_basic_evaluation():
    """Example 1: Basic evaluation with high scores (should APPROVE)."""
    print("\n" + "=" * 70)
    print("Example 1: Basic Evaluation - High Scores")
    print("=" * 70)

    service = Phase18Service()

    candidate_action = {
        "action_type": "update_document",
        "document_id": "doc-12345",
        "changes": {"section": "conclusion", "content": "Updated text"},
    }

    phase_inputs = {
        "phase12": {"coherence_score": 0.88},
        "phase13": {"probability": 0.92},
        "phase15": {"stability_score": 0.85},
        "phase17": {"global_ethics_score": 0.90},
        "phase11": {"risk_score": 0.08},  # Low risk = good
    }

    result = service.evaluate(candidate_action, phase_inputs, dry_run=True)

    print(f"Outcome: {result.outcome.outcome}")
    print(f"Score: {result.score.score:.3f}")
    print(f"Rationale: {result.outcome.rationale}")
    print(f"Ledger Entry ID: {result.ledger_entry_id}")
    print(f"Policy Violations: {len(result.policy_violations)}")
    print("\nProvenance:")
    print(f"  - Seed: {result.provenance['seed']}")
    print(f"  - Input Hash: {result.provenance['input_hash'][:16]}...")
    print(f"  - Service Version: {result.provenance['service_version']}")


def example_2_with_gcn_rules():
    """Example 2: Evaluation with GCN rules (policy violation)."""
    print("\n" + "=" * 70)
    print("Example 2: Evaluation with GCN Rules - Policy Violation")
    print("=" * 70)

    service = Phase18Service()

    candidate_action = {
        "action_type": "delete_document",
        "document_id": "doc-critical-001",
        "reason": "cleanup",
    }

    phase_inputs = {
        "phase12": {"coherence_score": 0.75},
        "phase13": {"probability": 0.80},
        "phase15": {"stability_score": 0.72},
        "phase17": {"global_ethics_score": 0.78},
        "phase11": {"risk_score": 0.20},
    }

    # Define governance rules
    gcn_rules = [
        {
            "policy_id": "no-delete-critical",
            "rule_type": "prohibition",
            "condition": {"prohibited_actions": ["delete_document"]},
            "severity": "high",
            "priority": 10,
        },
        {
            "policy_id": "require-approval",
            "rule_type": "requirement",
            "condition": {"required_fields": ["approval_token"]},
            "severity": "medium",
            "priority": 5,
        },
    ]

    result = service.evaluate(
        candidate_action, phase_inputs, gcn_rules=gcn_rules, dry_run=True
    )

    print(f"Outcome: {result.outcome.outcome}")
    print(f"Score: {result.score.score:.3f}")
    print(f"Rationale: {result.outcome.rationale}")
    print(f"\nPolicy Violations: {len(result.policy_violations)}")
    for violation in result.policy_violations:
        print(f"  - Policy: {violation.policy_id}")
        print(f"    Severity: {violation.severity}")
        print(f"    Reason: {violation.reason}")


def example_3_conditional_approval():
    """Example 3: Conditional approval with mitigations."""
    print("\n" + "=" * 70)
    print("Example 3: Conditional Approval - Medium Scores")
    print("=" * 70)

    service = Phase18Service()

    candidate_action = {
        "action_type": "apply_patch",
        "patch_id": "patch-789",
        "description": "Security fix",
    }

    phase_inputs = {
        "phase12": {"coherence_score": 0.65},
        "phase13": {"probability": 0.70},
        "phase15": {"stability_score": 0.62},
        "phase17": {"global_ethics_score": 0.68},
        "phase11": {"risk_score": 0.30},
    }

    gcn_rules = [
        {
            "policy_id": "require-testing",
            "rule_type": "requirement",
            "condition": {"required_fields": ["test_results"]},
            "severity": "medium",
        }
    ]

    result = service.evaluate(
        candidate_action, phase_inputs, gcn_rules=gcn_rules, dry_run=True
    )

    print(f"Outcome: {result.outcome.outcome}")
    print(f"Score: {result.score.score:.3f}")
    print(f"Rationale: {result.outcome.rationale}")
    print(f"\nMitigations Recommended: {len(result.outcome.mitigations)}")
    for mitigation in result.outcome.mitigations:
        print(f"  - {mitigation}")


def example_4_complete_workflow():
    """Example 4: Complete workflow - evaluate, commit, rollback."""
    print("\n" + "=" * 70)
    print("Example 4: Complete Workflow - Evaluate → Commit → Rollback")
    print("=" * 70)

    service = Phase18Service()

    candidate_action = {
        "action_type": "workflow_demo",
        "operation": "test_operation",
    }

    phase_inputs = {
        "phase12": {"coherence_score": 0.82},
        "phase13": {"probability": 0.85},
        "phase15": {"stability_score": 0.79},
        "phase17": {"global_ethics_score": 0.84},
        "phase11": {"risk_score": 0.12},
    }

    # Step 1: Evaluate
    print("\nStep 1: Evaluate")
    result = service.evaluate(candidate_action, phase_inputs, dry_run=False)
    print(f"  Outcome: {result.outcome.outcome}")
    print(f"  Score: {result.score.score:.3f}")
    print(f"  Entry ID: {result.ledger_entry_id}")

    if result.outcome.outcome in ["APPROVE", "CONDITIONAL_APPROVE"]:
        # Step 2: Commit
        print("\nStep 2: Commit with Governor Approval")
        commit_result = service.commit(
            result.ledger_entry_id, governor_approval="simulated-token-123"
        )
        print(f"  Success: {commit_result['success']}")
        print(f"  Message: {commit_result['message']}")

        # Step 3: Verify ledger
        print("\nStep 3: Verify Ledger Integrity")
        is_valid = service.verify_ledger()
        print(f"  Ledger Valid: {is_valid}")

        # Step 4: Rollback (dry run first)
        print("\nStep 4: Rollback (Dry Run)")
        rollback_dry = service.rollback(result.ledger_entry_id, dry_run=True)
        print(f"  Success: {rollback_dry['success']}")
        print(f"  Dry Run: {rollback_dry['dry_run']}")

        # Step 5: Actual rollback
        print("\nStep 5: Rollback (Actual)")
        rollback_result = service.rollback(
            result.ledger_entry_id,
            dry_run=False,
            governor_approval="simulated-token-123",
        )
        print(f"  Success: {rollback_result['success']}")
        print(f"  Message: {rollback_result['message']}")
    else:
        print(f"\nCannot commit - outcome is {result.outcome.outcome}")


def example_5_custom_weights():
    """Example 5: Custom consensus weights favoring ethics."""
    print("\n" + "=" * 70)
    print("Example 5: Custom Weights - Favor Ethical Score")
    print("=" * 70)

    custom_weights = {
        "scalar_harmonics": 0.15,
        "qdcl_probability": 0.15,
        "temporal_stability": 0.10,
        "ethical_score": 0.50,  # Heavy weight on ethics
        "self_healing_risk": 0.10,
    }

    service = Phase18Service(custom_weights=custom_weights)

    candidate_action = {
        "action_type": "ethical_decision_test",
        "context": "high ethical impact",
    }

    phase_inputs = {
        "phase12": {"coherence_score": 0.60},
        "phase13": {"probability": 0.65},
        "phase15": {"stability_score": 0.58},
        "phase17": {"global_ethics_score": 0.95},  # Very high ethical score
        "phase11": {"risk_score": 0.40},
    }

    result = service.evaluate(candidate_action, phase_inputs, dry_run=True)

    print(f"Outcome: {result.outcome.outcome}")
    print(f"Score: {result.score.score:.3f}")
    print(f"Rationale: {result.outcome.rationale}")
    print("\nScore Components:")
    for component, value in result.score.components.items():
        print(f"  - {component}: {value:.3f}")
    print("\nNote: High ethical score dominates due to custom weights")


def example_6_determinism_check():
    """Example 6: Demonstrate determinism - same input = same output."""
    print("\n" + "=" * 70)
    print("Example 6: Determinism Check - Multiple Runs")
    print("=" * 70)

    candidate_action = {"action_type": "determinism_test", "value": 42}

    phase_inputs = {
        "phase12": {"coherence_score": 0.75},
        "phase13": {"probability": 0.78},
        "phase15": {"stability_score": 0.72},
        "phase17": {"global_ethics_score": 0.76},
        "phase11": {"risk_score": 0.25},
    }

    results = []
    for _ in range(3):
        service = Phase18Service()  # New service each time
        result = service.evaluate(candidate_action, phase_inputs, dry_run=True)
        results.append(result)

    print(
        f"Run 1: Outcome={results[0].outcome.outcome}, "
        f"Score={results[0].score.score:.6f}"
    )
    print(
        f"Run 2: Outcome={results[1].outcome.outcome}, "
        f"Score={results[1].score.score:.6f}"
    )
    print(
        f"Run 3: Outcome={results[2].outcome.outcome}, "
        f"Score={results[2].score.score:.6f}"
    )

    # Check determinism
    all_same = all(
        r.outcome.outcome == results[0].outcome.outcome
        and r.score.score == results[0].score.score
        and r.provenance["seed"] == results[0].provenance["seed"]
        for r in results
    )

    print(f"\nAll results identical: {all_same}")
    print(f"Seed (all runs): {results[0].provenance['seed']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Phase 18 (RGK-18) - Recursive Governance Kernel Examples")
    print("=" * 70)

    example_1_basic_evaluation()
    example_2_with_gcn_rules()
    example_3_conditional_approval()
    example_4_complete_workflow()
    example_5_custom_weights()
    example_6_determinism_check()

    print("\n" + "=" * 70)
    print(" All Examples Completed Successfully!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
