"""Example script demonstrating Phase 14: RPG-14 (Meta-Causal Inference).

This script shows how to use Phase 14 to:
- Build causal governance graphs
- Perform retrocausal inference
- Compute Causal Responsibility Index (CRI)
- Detect governance anomalies
- Generate governance prognoses
- Audit overall governance health
"""

from oraculus_di_auditor.rpg14 import (
    CausalAnomalyDetector,
    CausalGraph,
    CausalResponsibilityIndex,
    GovernancePrognosisGenerator,
    NodeType,
    Phase14Service,
    RetrocausalInferenceEngine,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def example_causal_graph():
    """Example 1: Build and validate a causal graph."""
    print_section("Example 1: Building a Causal Graph")

    graph = CausalGraph()
    print(f"[OK] Initialized causal graph version {graph.version}")

    # Create a governance scenario: Policy → Implementation → Outcome
    policy_node = graph.add_node(
        node_type=NodeType.FORWARD,
        qdcl_probability=0.9,
        scalar_harmonic=1.2,
        deviation_slope=0.3,
        metadata={"name": "Policy Decision"},
    )
    policy_node.add_state_vector("governance_quality", 0.8, confidence=0.9)

    implementation_node = graph.add_node(
        node_type=NodeType.FORWARD,
        qdcl_probability=0.7,
        scalar_harmonic=1.0,
        deviation_slope=0.5,
        metadata={"name": "Implementation Phase"},
    )
    implementation_node.add_state_vector("governance_quality", 0.6, confidence=0.8)

    outcome_node = graph.add_node(
        node_type=NodeType.FORWARD,
        qdcl_probability=0.8,
        scalar_harmonic=1.1,
        deviation_slope=0.2,
        metadata={"name": "Governance Outcome"},
    )
    outcome_node.add_state_vector("governance_quality", 0.7, confidence=0.9)

    # Add causal edges
    graph.add_edge(policy_node.node_id, implementation_node.node_id)
    graph.add_edge(implementation_node.node_id, outcome_node.node_id)

    print(f"[OK] Created {len(graph.nodes)} causal nodes")
    print("  - Policy Decision → Implementation → Outcome")

    # Validate graph
    validation = graph.validate_graph()
    print(
        f"\n[OK] Graph validation: {'PASSED' if validation['is_valid'] else 'FAILED'}"
    )
    print(f"  - Issues: {validation['issue_count']}")
    print(f"  - Warnings: {validation['warning_count']}")

    return graph, policy_node, implementation_node, outcome_node


def example_retrocausal_inference(graph, outcome_node):
    """Example 2: Perform retrocausal inference."""
    print_section("Example 2: Retrocausal Inference")

    engine = RetrocausalInferenceEngine(max_depth=10)
    print(f"[OK] Initialized retrocausal engine version {engine.version}")

    # Trace root causes
    print("\nTracing root causes for outcome node...")
    result = engine.infer_root_causes(graph, outcome_node.node_id)

    if result["success"]:
        print(f"[OK] Found {result['root_cause_count']} root cause(s)")
        for i, root_cause in enumerate(result["root_causes"], 1):
            print(f"\n  Root Cause {i}:")
            print(f"    - Node ID: {root_cause['root_node_id'][:8]}...")
            print(f"    - Path length: {root_cause['path_length']}")
            print(f"    - Causal strength: {root_cause['normalized_strength']:.3f}")

    # Identify causal breaks
    print("\nIdentifying causal breaks...")
    breaks = engine.identify_causal_breaks(graph, threshold=0.3)
    print(f"[OK] Found {len(breaks)} causal break(s)")

    for i, break_item in enumerate(breaks[:3], 1):
        print(f"\n  Break {i}:")
        print(f"    - Type: {break_item['type']}")
        print(f"    - Severity: {break_item.get('severity', 'unknown')}")

    return engine


def example_causal_responsibility(graph):
    """Example 3: Compute Causal Responsibility Index."""
    print_section("Example 3: Causal Responsibility Index (CRI)")

    cri_calc = CausalResponsibilityIndex()
    print(f"[OK] Initialized CRI calculator version {cri_calc.version}")

    # Rank all nodes by responsibility
    print("\nRanking nodes by causal responsibility...")
    rankings = cri_calc.rank_by_responsibility(graph)

    print(f"[OK] Analyzed {len(rankings)} nodes")
    print("\nTop 3 Nodes by CRI:")

    for i, result in enumerate(rankings[:3], 1):
        print(f"\n  #{i} Node {result['node_id'][:8]}...")
        print(f"    - CRI Score: {result['cri']:.3f}")
        print(f"    - Harmonic Factor: {result['factors']['harmonic']:.3f}")
        print(f"    - Probability Factor: {result['factors']['probability']:.3f}")
        print(f"    - Deviation Factor: {result['factors']['deviation']:.3f}")
        print(f"    - Connectivity Factor: {result['factors']['connectivity']:.3f}")

    # Explain top node
    if rankings:
        print("\nDetailed Explanation for Top Node:")
        explanation = cri_calc.explain_cri(rankings[0])
        print(explanation)

    return cri_calc


def example_anomaly_detection(graph):
    """Example 4: Detect governance anomalies."""
    print_section("Example 4: Causal Anomaly Detection")

    detector = CausalAnomalyDetector()
    print(f"[OK] Initialized anomaly detector version {detector.version}")

    # Run full detection cycle
    print("\nRunning complete anomaly detection cycle...")
    report = detector.detect_all_anomalies(graph)

    print(f"[OK] Detection cycle {report['detection_cycle']} complete")
    print(f"  - Execution time: {report['execution_time_seconds']:.3f} seconds")

    # Display summary (Output 1 of 7)
    summary = report["output_1_anomaly_summary"]
    print("\nAnomaly Summary:")
    print(f"  - Total anomalies: {summary['total_anomalies']}")
    print(f"  - Breaks: {summary['breaks']}")
    print(f"  - Contradictions: {summary['contradictions']}")
    print(f"  - Non-convergent: {summary['non_convergent']}")
    print(f"  - Undefined states: {summary['undefined_states']}")
    print(f"  - Systemic inconsistencies: {summary['systemic_inconsistencies']}")

    # Severity breakdown
    severity = summary["severity_breakdown"]
    print("\nSeverity Breakdown:")
    print(f"  - Critical: {severity.get('critical', 0)}")
    print(f"  - High: {severity.get('high', 0)}")
    print(f"  - Medium: {severity.get('medium', 0)}")
    print(f"  - Low: {severity.get('low', 0)}")

    # Recommended actions (Output 7 of 7)
    actions = report["output_7_recommended_actions"]
    if actions:
        print("\nTop 3 Recommended Actions:")
        for i, action in enumerate(actions[:3], 1):
            print(f"\n  {i}. [{action['severity'].upper()}] {action['anomaly_type']}")
            print(f"     Action: {action['action']}")

    return detector, report


def example_governance_prognosis(graph):
    """Example 5: Generate governance prognosis."""
    print_section("Example 5: Governance Prognosis")

    generator = GovernancePrognosisGenerator(time_depth=12, branching_factor=5)
    print(f"[OK] Initialized prognosis generator version {generator.version}")

    # Generate complete prognosis
    print("\nGenerating governance prognosis...")
    prognosis = generator.generate_prognosis(graph)

    print("[OK] Prognosis generation complete")

    # Best-case trajectory
    best_case = prognosis["best_case_trajectory"]
    print("\nBest-Case Trajectory:")
    print(f"  - Nodes: {best_case['node_count']}")
    print(f"  - Outcome score: {best_case['outcome_score']:.3f}")
    print(f"  - Avg probability: {best_case['total_probability']:.3f}")

    # Worst-case trajectory
    worst_case = prognosis["worst_case_trajectory"]
    print("\nWorst-Case Trajectory:")
    print(f"  - Nodes: {worst_case['node_count']}")
    print(f"  - Outcome score: {worst_case['outcome_score']:.3f}")
    print(f"  - Avg probability: {worst_case['total_probability']:.3f}")

    # Median trajectory
    median = prognosis["median_trajectory"]
    print("\nMedian Trajectory:")
    print(f"  - Nodes: {median['node_count']}")
    print(f"  - Outcome score: {median['outcome_score']:.3f}")
    print(f"  - Avg probability: {median['total_probability']:.3f}")

    # Governance stability
    stability = prognosis["governance_stability_index"]
    print("\nGovernance Stability:")
    print(f"  - Stability score: {stability['stability_score']:.3f}")
    print(f"  - Status: {'STABLE' if stability['is_stable'] else 'UNSTABLE'}")
    print(f"  - Outcome spread: {stability['outcome_spread']:.3f}")

    # Risk advisories
    advisories = prognosis["risk_advisories"]
    if advisories:
        print(f"\nRisk Advisories ({len(advisories)} total):")
        for i, advisory in enumerate(advisories[:3], 1):
            print(f"\n  {i}. [{advisory['risk_level'].upper()}] {advisory['category']}")
            print(f"     {advisory['message']}")
            print(f"     → {advisory['recommendation']}")

    return generator, prognosis


def example_phase14_service():
    """Example 6: Use complete Phase 14 service."""
    print_section("Example 6: Complete Phase 14 Service (RPG-14)")

    service = Phase14Service(time_depth=12, branching_factor=5)
    print(f"[OK] Initialized Phase 14 Service version {service.version}")

    # Get service info
    info = service.get_service_info()
    print(f"  - Phase: {info['phase']}")
    print(f"  - Cycle count: {info['cycle_count']}")
    print("\nComponents:")
    for component, version in info["components"].items():
        print(f"  - {component}: v{version}")

    # Create system state
    system_state = {
        "components": [
            {
                "id": "policy_engine",
                "deviation_slope": 0.3,
            },
            {
                "id": "implementation_layer",
                "deviation_slope": 0.6,
            },
            {
                "id": "governance_outcome",
                "deviation_slope": 0.2,
            },
        ],
        "dependencies": [
            {"source": "policy_engine", "target": "implementation_layer"},
            {"source": "implementation_layer", "target": "governance_outcome"},
        ],
    }

    # Add Phase 12 harmonics
    phase12_harmonics = {0: 1.2, 1: 1.0, 2: 1.1}

    # Add Phase 13 probabilities
    phase13_probabilities = {
        "policy_engine": 0.9,
        "implementation_layer": 0.7,
        "governance_outcome": 0.8,
    }

    # Run complete cycle
    print("\nRunning complete RPG-14 cycle...")
    result = service.run_cycle(
        system_state,
        phase12_harmonics=phase12_harmonics,
        phase13_probabilities=phase13_probabilities,
    )

    print(f"[OK] Cycle {result['cycle']} complete")
    print(f"  - Execution time: {result['execution_time_seconds']:.3f} seconds")
    print(f"  - Graph nodes: {result['causal_graph']['node_count']}")

    # Governance audit
    audit = result["governance_audit"]
    print("\nGovernance Health:")
    print(f"  - Status: {audit['health_status'].upper()}")
    print(f"  - Health score: {audit['health_score']:.3f}")

    metrics = audit["metrics"]
    print("\nKey Metrics:")
    print(f"  - Total anomalies: {metrics['total_anomalies']}")
    print(f"  - Avg CRI: {metrics['avg_causal_responsibility']:.3f}")
    print(f"  - Stability: {metrics['governance_stability']:.3f}")

    # Critical issues
    critical = audit.get("critical_issues", [])
    if critical:
        print(f"\nCritical Issues ({len(critical)}):")
        for issue in critical[:3]:
            print(f"  - [{issue['severity'].upper()}] {issue['type']}")

    # Recommendations
    recommendations = audit.get("recommendations", [])
    if recommendations:
        print("\nTop Recommendations:")
        for i, rec in enumerate(recommendations[:5], 1):
            print(f"  {i}. {rec}")

    # Traceability
    traceability = result["traceability_report"]
    print("\nTraceability:")
    print(f"  - Deterministic: {traceability['reproducibility']['deterministic']}")
    print(f"  - Version locked: {traceability['reproducibility']['version_locked']}")

    return service, result


def final_summary():
    """Print final summary."""
    print_section("Phase 14 (RPG-14) Examples Complete")

    print("📊 Phase 14 Capabilities Demonstrated:")
    print("  [OK] Causal graph construction with validation")
    print("  [OK] Retrocausal inference and root cause analysis")
    print("  [OK] Causal Responsibility Index (CRI) computation")
    print("  [OK] Anomaly detection with 7 required outputs")
    print("  [OK] Governance prognosis (best/worst/median trajectories)")
    print("  [OK] Complete RPG-14 cycle with all integrations")

    print("\n🎯 Key Features:")
    print("  • Deterministic, reproducible outputs")
    print("  • Integration with Phase 12 (scalar harmonics)")
    print("  • Integration with Phase 13 (QDCL probabilities)")
    print("  • Full traceability and explainability")
    print("  • Governance stability assessment")
    print("  • Predictive risk advisories")

    print("\n🚀 Phase 14 Status: OPERATIONAL")
    print("📝 See PHASE14_OVERVIEW.md for complete documentation")


def main():
    """Run all Phase 14 examples."""
    print("🛰️  Phase 14: Meta-Causal Inference & Recursive Predictive Governance")
    print("=" * 80)

    # Run examples
    graph, policy, impl, outcome = example_causal_graph()
    example_retrocausal_inference(graph, outcome)
    example_causal_responsibility(graph)
    example_anomaly_detection(graph)
    example_governance_prognosis(graph)
    example_phase14_service()
    final_summary()


if __name__ == "__main__":
    main()
