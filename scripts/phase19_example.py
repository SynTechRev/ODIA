#!/usr/bin/env python
"""Example script demonstrating Phase 19 (AEI-19) Applied Emergent Intelligence.

This script shows the complete workflow:
1. Prepare inputs from Phases 12-18
2. Run Applied Emergent Intelligence analysis
3. Review insights, alignment, and scenario projections
4. Demonstrate determinism
"""

import hashlib

from oraculus_di_auditor.aei19 import Phase19Service


def create_example_phase_inputs():
    """Create example Phase 12-18 inputs for demonstration."""
    # Generate a deterministic lattice_id for demonstration
    lattice_base = hashlib.sha256(b"example_lattice").hexdigest()

    return {
        "phase12": {
            "coherence_score": 0.88,
            "scalar_map": {
                "layer_0": 1.0,
                "layer_1": 0.92,
                "layer_2": 0.85,
            },
            "integration_status": "stable",
        },
        "phase13": {
            "probability": 0.90,
            "temporal_vector": [0.92, 0.88, 0.85],
            "quantization_level": 3,
        },
        "phase14": {
            "prediction_score": 0.84,
            "recursive_depth": 4,
            "scalar_predictions": [0.86, 0.84, 0.82],
        },
        "phase15": {
            "stability_score": 0.82,
            "temporal_field": {
                "stability": 0.78,
                "consistency": 0.80,
            },
            "governance_signals": {"temporal_safe": True},
        },
        "phase16": {
            "recursive_integrity_score": 0.89,
            "meta_harmonic_field": {
                "0": 1.0,
                "1": 0.92,
                "2": 0.87,
            },
            "self_reflection_report": {"status": "optimal"},
        },
        "phase17": {
            "global_ethics_score": 0.92,
            "ethical_lattice": {
                "lattice_id": lattice_base,
                "primary_ethic": "beneficence",
                "ethical_vector": {
                    "rights_impact": 0.90,
                    "harm_probability": 0.10,
                    "autonomy_effect": 0.88,
                    "system_stability": 0.92,
                    "governance_compliance": 0.90,
                },
            },
            "ethical_projection": {
                "projected_scores": [0.92, 0.93, 0.94],
                "delta_ethics": 0.02,
                "risk": "none",
                "reversible": True,
            },
            "legal_map": {
                "constitutional_flags": [],
                "human_rights_flags": [],
                "compliance_score": 0.95,
            },
            "governance_invariants": {
                "invariant_violations": [],
                "alignment_score": 0.91,
            },
        },
        "phase18": {
            "score": 0.88,
            "outcome": {
                "outcome": "APPROVE",
                "rationale": "All governance checks passed",
                "mitigations": [],
            },
            "policy_violations": [],
            "ledger_entry_id": "entry-12345",
        },
    }


def example_1_basic_analysis():
    """Example 1: Basic Applied Intelligence Analysis."""
    print("\n" + "=" * 80)
    print("Example 1: Basic Applied Intelligence Analysis (AEI-19)")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    result = service.run_applied_intelligence(phase_inputs)

    print("\n📊 UNIFIED INTELLIGENCE FIELD (UIF-19)")
    print("-" * 80)
    uif = result.uif_19_state
    print(f"UIF ID: {uif.uif_id[:16]}...")
    print(f"Dimensions: {uif.dimension}")
    print(f"System Coherence: {uif.field_vector['dim_140']:.3f}")
    print(f"Cross-Phase Alignment: {uif.field_vector['dim_141']:.3f}")
    print(f"Ethical Warp: {uif.ethical_warp:.3f}")
    print(f"Governance Weight: {uif.governance_weight:.3f}")
    print(f"Harmonization Pressure: {uif.harmonization_pressure:.3f}")

    print("\n💡 KEY INSIGHTS (ISE-19)")
    print("-" * 80)
    for i, insight in enumerate(result.insight_packets[:5], 1):
        print(
            f"{i}. [{insight.insight_type.upper()}] "
            f"(confidence: {insight.confidence:.2f})"
        )
        print(f"   {insight.content[:120]}...")

    print("\n✅ ALIGNMENT REPORT (EGA-19)")
    print("-" * 80)
    alignment = result.alignment_report
    print(f"REC-17 Compliant: {alignment.rec17_compliant}")
    print(f"RGK-18 Compliant: {alignment.rgk18_compliant}")
    print(f"Ethical Score: {alignment.ethical_score:.3f}")
    print(f"Governance Score: {alignment.governance_score:.3f}")
    print(f"Violations: {len(alignment.violations)}")
    if alignment.recommendations:
        print("\nTop Recommendations:")
        for rec in alignment.recommendations[:3]:
            print(f"  • {rec[:100]}...")

    print("\n🔮 SCENARIO PROJECTION (DSS-19)")
    print("-" * 80)
    scenario = result.scenario_map
    print(f"Scenario ID: {scenario.scenario_id[:16]}...")
    print(f"Trajectory Type: {scenario.trajectory_type.upper()}")
    print(f"Reversibility: {scenario.reversibility}")
    print(f"Steps Simulated: {len(scenario.steps)}")
    crit = scenario.critical_points if scenario.critical_points else "None"
    print(f"Critical Points: {crit}")

    print("\n  Step-by-Step Projection:")
    for step in scenario.steps:
        print(
            f"  Step {step.step_number}: "
            f"Ethical Δ={step.ethical_delta:+.3f}, "
            f"Governance Δ={step.governance_delta:+.3f}, "
            f"Risk={step.risk_level}"
        )

    print("\n📦 APPLIED INTELLIGENCE PACKET (AIP-19)")
    print("-" * 80)
    aei = result.aei19_result
    print(f"Result ID: {aei.result_id[:16]}...")
    print(f"Determinism Signature: {aei.determinism_signature[:16]}...")
    print(f"Counterfactuals Generated: {len(aei.counterfactuals)}")

    print("\n🔄 PROVENANCE")
    print("-" * 80)
    prov = result.provenance
    print(f"Service Version: {prov['service_version']}")
    print(f"Input Hash: {prov['input_hash'][:16]}...")
    print(f"Dry Run: {prov['dry_run']}")
    print(f"Determinism Guaranteed: {prov['determinism_guaranteed']}")
    print(f"Phases Integrated: {', '.join(prov['phases_integrated'])}")


def example_2_detailed_explanation():
    """Example 2: View detailed narrative explanation."""
    print("\n" + "=" * 80)
    print("Example 2: Detailed Narrative Explanation")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    result = service.run_applied_intelligence(phase_inputs)

    print("\n" + result.aei19_result.explanation)


def example_3_structured_packet():
    """Example 3: View structured intelligence packet."""
    print("\n" + "=" * 80)
    print("Example 3: Structured Intelligence Packet")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    result = service.run_applied_intelligence(phase_inputs)

    import json

    packet = result.aei19_result.structured_packet

    print("\n📊 UIF Summary:")
    print(json.dumps(packet["uif_summary"], indent=2))

    print("\n💡 Insights Summary:")
    print(json.dumps(packet["insights"], indent=2))

    print("\n✅ Compliance Summary:")
    print(json.dumps(packet["compliance"], indent=2))

    print("\n🔮 Scenario Summary:")
    print(json.dumps(packet["scenario"], indent=2))


def example_4_counterfactuals():
    """Example 4: Explore counterfactual scenarios."""
    print("\n" + "=" * 80)
    print("Example 4: Counterfactual Scenarios")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    result = service.run_applied_intelligence(phase_inputs)

    counterfactuals = result.aei19_result.counterfactuals

    print(f"\n🔄 Generated {len(counterfactuals)} counterfactual scenarios:")
    for i, cf in enumerate(counterfactuals, 1):
        print(f"\n{i}. {cf}")


def example_5_reversibility_protocol():
    """Example 5: View reversibility protocol."""
    print("\n" + "=" * 80)
    print("Example 5: Reversibility Protocol")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    result = service.run_applied_intelligence(phase_inputs)

    print("\n" + result.aei19_result.reversibility_protocol)


def example_6_low_compliance_scenario():
    """Example 6: Handle low compliance scores."""
    print("\n" + "=" * 80)
    print("Example 6: Low Compliance Scenario")
    print("=" * 80)

    service = Phase19Service()
    phase_inputs = create_example_phase_inputs()

    # Simulate low scores and violations
    phase_inputs["phase17"]["global_ethics_score"] = 0.45
    phase_inputs["phase18"]["score"] = 0.42
    phase_inputs["phase17"]["governance_invariants"]["invariant_violations"] = [
        "transparency",
        "proportionality",
    ]

    result = service.run_applied_intelligence(phase_inputs)

    print("\n⚠️ COMPLIANCE ISSUES DETECTED")
    print("-" * 80)
    alignment = result.alignment_report
    print(f"REC-17 Compliant: {alignment.rec17_compliant}")
    print(f"RGK-18 Compliant: {alignment.rgk18_compliant}")
    print(f"Ethical Score: {alignment.ethical_score:.3f}")
    print(f"Governance Score: {alignment.governance_score:.3f}")

    print(f"\n❌ Violations Detected ({len(alignment.violations)}):")
    for violation in alignment.violations:
        print(f"  • {violation}")

    print(f"\n💡 Recommendations ({len(alignment.recommendations)}):")
    for rec in alignment.recommendations[:5]:
        print(f"  • {rec}")


def example_7_determinism_verification():
    """Example 7: Verify deterministic behavior."""
    print("\n" + "=" * 80)
    print("Example 7: Determinism Verification")
    print("=" * 80)

    phase_inputs = create_example_phase_inputs()

    print("\nRunning Phase 19 three times with identical inputs...")

    results = []
    for i in range(3):
        service = Phase19Service()
        result = service.run_applied_intelligence(phase_inputs)
        results.append(result)
        print(f"  Run {i+1}: UIF ID = {result.uif_19_state.uif_id[:16]}...")

    # Verify determinism
    all_same_uif = all(
        r.uif_19_state.uif_id == results[0].uif_19_state.uif_id for r in results
    )
    all_same_alignment = all(
        r.alignment_report.alignment_id == results[0].alignment_report.alignment_id
        for r in results
    )
    all_same_scenario = all(
        r.scenario_map.scenario_id == results[0].scenario_map.scenario_id
        for r in results
    )
    all_same_signature = all(
        r.aei19_result.determinism_signature
        == results[0].aei19_result.determinism_signature
        for r in results
    )

    print("\n✓ Determinism Verification:")
    print(f"  UIF IDs identical: {all_same_uif}")
    print(f"  Alignment IDs identical: {all_same_alignment}")
    print(f"  Scenario IDs identical: {all_same_scenario}")
    print(f"  Determinism signatures identical: {all_same_signature}")

    if all_same_uif and all_same_alignment and all_same_scenario and all_same_signature:
        print("\n✅ DETERMINISM VERIFIED: All outputs are identical")
    else:
        print("\n❌ DETERMINISM FAILED: Outputs differ")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print(" Phase 19 (AEI-19) - Applied Emergent Intelligence Examples")
    print(" Version: aei19-1.0.0")
    print("=" * 80)

    example_1_basic_analysis()
    example_2_detailed_explanation()
    example_3_structured_packet()
    example_4_counterfactuals()
    example_5_reversibility_protocol()
    example_6_low_compliance_scenario()
    example_7_determinism_verification()

    print("\n" + "=" * 80)
    print(" All Examples Completed Successfully!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
