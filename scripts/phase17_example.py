#!/usr/bin/env python3
"""Example script demonstrating Phase 17: Recursive Ethical Cognition (REC-17)."""

from oraculus_di_auditor.rec17.rec17_service import Phase17Service
from oraculus_di_auditor.rec17.schemas import Phase17Result


def create_mock_phase16_result():
    """Create a mock Phase 16 result for demonstration."""
    return {
        "recursive_integrity_score": 0.85,
        "meta_harmonic_field": {
            "0": 1.0,
            "1": 0.9,
            "2": 0.95,
        },
        "emergent_pattern_index": {
            "pattern1": 0.8,
            "pattern2": 0.7,
        },
        "prediction_drift_corrections": [
            {
                "id": "correction_1",
                "description": "Align dependency versions",
                "confidence": 0.85,
                "estimated_effort_hours": 2.0,
                "risk_level": "low",
                "reversible": True,
            },
            {
                "id": "correction_2",
                "description": "Update configuration parameter",
                "confidence": 0.92,
                "estimated_effort_hours": 0.5,
                "risk_level": "low",
                "reversible": True,
            },
        ],
        "self_reflection_report": {
            "status": "nominal",
            "observations": ["System operating within normal parameters"],
        },
        "meta_state_vector": {
            "complexity": 0.65,
            "stability": 0.88,
        },
        "provenance": {
            "input_hash": "a1b2c3d4e5f6",
            "service_version": "emcs16-0.1.0",
            "deterministic_seed": 12345,
        },
    }


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def main():
    """Run Phase 17 example."""
    print_section("Phase 17: Recursive Ethical Cognition (REC-17) - Example")

    # Create service
    service = Phase17Service()
    print("✓ Phase17Service initialized")

    # Create mock Phase 16 result
    phase16_result = create_mock_phase16_result()
    print("✓ Mock Phase 16 result created")

    # Run ethical analysis
    print_section("Running Ethical Analysis")
    result = service.run_ethical_analysis(
        phase16_result=phase16_result,
        dry_run=True,  # Default: suggestions only, no actions
        auto_apply=False,  # Default: requires manual approval
    )
    print("✓ Ethical analysis complete")

    # Validate against schema
    validated_result = Phase17Result(**result)
    print("✓ Result validated against Phase17Result schema")

    # Display results
    print_section("Ethical Lattice")
    print(f"Primary Ethic: {validated_result.ethical_lattice.primary_ethic}")
    print(f"Lattice ID: {validated_result.ethical_lattice.lattice_id[:16]}...")
    print("\nEthical Vector:")
    for axis, score in validated_result.ethical_lattice.ethical_vector.items():
        print(f"  {axis:25s}: {score:.3f}")

    print_section("Ethical Projection")
    print(f"Risk Level: {validated_result.ethical_projection.risk}")
    print(f"Reversible: {validated_result.ethical_projection.reversible}")
    print(f"Delta Ethics: {validated_result.ethical_projection.delta_ethics:+.3f}")
    print("\nProjected Scores (3 steps):")
    for i, score in enumerate(validated_result.ethical_projection.projected_scores, 1):
        print(f"  Step {i}: {score:.3f}")

    print_section("Legal & Constitutional Mapping")
    print(f"Compliance Score: {validated_result.legal_map.compliance_score:.3f}")
    if validated_result.legal_map.constitutional_flags:
        print("\nConstitutional Flags:")
        for flag in validated_result.legal_map.constitutional_flags:
            print(f"  - {flag}")
    else:
        print("\nNo constitutional flags")

    if validated_result.legal_map.human_rights_flags:
        print("\nHuman Rights Flags:")
        for flag in validated_result.legal_map.human_rights_flags:
            print(f"  - {flag}")
    else:
        print("\nNo human rights flags")

    print_section("Governance Invariants")
    print(
        f"Alignment Score: {validated_result.governance_invariants.alignment_score:.3f}"
    )
    if validated_result.governance_invariants.invariant_violations:
        print("\nInvariant Violations:")
        for violation in validated_result.governance_invariants.invariant_violations:
            print(f"  - {violation}")
    else:
        print("\nNo invariant violations ✓")

    print_section("Global Assessment")
    print(f"Global Ethics Score: {validated_result.global_ethics_score:.3f}")

    print_section("Action Suggestions")
    if validated_result.action_suggestions:
        for i, suggestion in enumerate(validated_result.action_suggestions, 1):
            print(f"{i}. {suggestion}")
    else:
        print("No specific actions recommended")

    print_section("Provenance")
    print(f"Service Version: {validated_result.provenance['service_version']}")
    print(f"Input Hash: {validated_result.provenance['input_hash']}")
    print(f"Dry Run: {validated_result.provenance['dry_run']}")
    print(f"Auto Apply: {validated_result.provenance['auto_apply']}")
    print(f"Timestamp: {validated_result.timestamp}")

    print_section("Determinism Test")
    # Run again with same input
    result2 = service.run_ethical_analysis(phase16_result)
    if (
        result["ethical_lattice"]["lattice_id"]
        == result2["ethical_lattice"]["lattice_id"]
    ):
        print("✓ PASS: Determinism verified (same input → same lattice)")
    else:
        print("✗ FAIL: Non-deterministic behavior detected")

    print_section("Example Complete")
    print("Phase 17 successfully demonstrated recursive ethical cognition.")
    print("All components operational and deterministic.")


if __name__ == "__main__":
    main()
