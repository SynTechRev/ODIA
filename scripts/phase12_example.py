"""Example script demonstrating Phase 12: Scalar-Convergent Architecture.

This script shows how to use Phase 12 to analyze the system architecture,
audit coherence, and generate integration plans.
"""

from pathlib import Path

from oraculus_di_auditor.scalar_convergence import (
    CoherenceAuditor,
    IntegrationEngine,
    Phase12Service,
    ScalarRecursiveMap,
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def example_scalar_recursive_map():
    """Run Scalar Recursive Map example."""
    print_section("Example 1: Scalar Recursive Map (SRM)")

    srm = ScalarRecursiveMap()
    print(f"✓ Initialized SRM version {srm.version}")
    print(f"✓ Total layers: {len(srm.layers)}")

    # Show layer information
    print("\nLayer Architecture:")
    for layer in srm.get_all_layers():
        print(f"  Layer {layer.layer_id}: {layer.name}")
        print(f"    - Inputs: {len(layer.inputs)}")
        print(f"    - Outputs: {len(layer.outputs)}")
        print(f"    - Recursion Rules: {len(layer.recursion_rules)}")
        print(f"    - Health Score: {layer.health_score}")

    # Component mapping
    print("\nComponent to Layer Mapping Examples:")
    components = [
        "oraculus_di_auditor.ingestion",
        "oraculus_di_auditor.embeddings",
        "oraculus_di_auditor.evolution.evolution_engine",
        "oraculus_di_auditor.self_healing.self_healing_service",
    ]

    for component in components:
        layers = srm.map_component_to_layer(component)
        print(f"  {component.split('.')[-1]}: Layers {layers}")

    # Dependency validation
    validation = srm.validate_layer_dependencies()
    print(f"\n✓ Dependency validation: {validation['is_valid']}")
    print(f"  - Valid connections: {validation['valid_connections']}")
    print(f"  - Invalid connections: {validation['invalid_connections']}")

    return srm


def example_coherence_audit():
    """Run Coherence Auditor example."""
    print_section("Example 2: Global Coherence Audit")

    auditor = CoherenceAuditor()
    print(f"✓ Initialized Coherence Auditor version {auditor.version}")

    print("\nRunning full coherence audit...")
    coherence_report = auditor.run_full_audit()

    print("✓ Audit complete!")
    print("\nSummary:")
    print(f"  - Total issues: {coherence_report['summary']['total_issues']}")
    print(f"  - Coherence score: {coherence_report['summary']['coherence_score']:.3f}")
    print(
        f"  - Critical: {coherence_report['summary']['severity_breakdown']['critical']}"
    )
    print(f"  - High: {coherence_report['summary']['severity_breakdown']['high']}")
    print(f"  - Medium: {coherence_report['summary']['severity_breakdown']['medium']}")
    print(f"  - Low: {coherence_report['summary']['severity_breakdown']['low']}")

    print("\nTop 5 Prioritized Issues:")
    for i, issue in enumerate(coherence_report["prioritized_issues"][:5], 1):
        print(f"  {i}. [{issue['severity'].upper()}] {issue['issue_type']}")
        print(f"     Location: {issue['location']}")
        print(f"     Description: {issue['description'][:80]}...")

    print("\nRecommendations:")
    for i, rec in enumerate(coherence_report["recommendations"][:3], 1):
        print(f"  {i}. {rec}")

    return coherence_report


def example_integration_plan(srm, coherence_report):
    """Run Integration Engine example."""
    print_section("Example 3: Integration Plan Generation")

    engine = IntegrationEngine()
    print(f"✓ Initialized Integration Engine version {engine.version}")

    print("\nGenerating integration plan...")
    srm_report = srm.to_dict()
    integration_plan = engine.generate_integration_plan(srm_report, coherence_report)

    print("✓ Integration plan generated!")
    print("\nSummary:")
    print(f"  - Total tasks: {integration_plan['summary']['total_tasks']}")
    print(
        f"  - Estimated hours: {integration_plan['summary']['estimated_total_hours']}"
    )
    print(f"  - Estimated days: {integration_plan['summary']['estimated_days']}")

    print("\nTasks by Category:")
    for category, tasks in integration_plan["tasks_by_category"].items():
        print(f"  - {category}: {len(tasks)} tasks")

    print("\nExecution Phases:")
    for phase in integration_plan["execution_phases"]:
        print(f"  Phase {phase['phase_id']}: {phase['name']}")
        print(f"    - Description: {phase['description']}")
        print(f"    - Tasks: {len(phase['tasks'])}")

    print("\nCritical Path (Top 5 tasks):")
    for i, task_id in enumerate(integration_plan["critical_path"][:5], 1):
        # Find task details
        for task in integration_plan["all_tasks"]:
            if task["task_id"] == task_id:
                print(f"  {i}. {task_id}: {task['title']}")
                break


def example_phase12_service():
    """Run Phase 12 Service example."""
    print_section("Example 4: Complete Phase 12 Analysis")

    service = Phase12Service()
    print(f"✓ Initialized Phase 12 Service version {service.version}")

    print("\nExecuting complete Phase 12 analysis...")
    print("  (This may take a few seconds...)")
    report = service.execute_phase12_analysis()

    print("\n✓ Phase 12 analysis complete!")
    print(f"  - Status: {report['status']}")
    print(f"  - Mode: {report['mode']}")
    print(f"  - Execution time: {report['execution_time_seconds']:.2f} seconds")

    print("\nAnalysis Summary:")
    print(f"  - Scalar layers: {report['summary']['scalar_layers']}")
    print(f"  - Coherence issues: {report['summary']['coherence_issues']}")
    print(f"  - Coherence score: {report['summary']['coherence_score']:.3f}")
    print(f"  - Integration tasks: {report['summary']['integration_tasks']}")
    print(f"  - Estimated hours: {report['summary']['estimated_integration_hours']}")

    # System analysis
    system_analysis = report["outputs"]["system_analysis"]
    print("\nSystem Architecture:")
    print(f"  - Total components: {system_analysis['total_components']}")
    print(f"  - Cross-layer components: {system_analysis['cross_layer_components']}")
    print(f"  - Most populated layer: {system_analysis['most_populated_layer']}")
    print(
        f"  - Architecture balanced: {system_analysis['architecture_health']['balanced']}"
    )

    # Failure predictions
    predictions = report["outputs"]["failure_predictions"]
    print("\nFailure Mode Predictions:")
    print(f"  - Total predictions: {predictions['total_predictions']}")
    print(f"  - High probability: {predictions['high_probability']}")
    print(f"  - Medium probability: {predictions['medium_probability']}")
    print(f"  - Low probability: {predictions['low_probability']}")

    if predictions["predictions"]:
        print("\n  Top Predicted Failure Modes:")
        for pred in predictions["predictions"][:3]:
            print(f"    • {pred['failure_mode']} ({pred['probability']} probability)")
            print(f"      Mitigation: {pred['mitigation']}")

    print("\nNext Steps:")
    for i, step in enumerate(report["next_steps"][:5], 1):
        print(f"  {i}. {step}")

    return service, report


def save_reports(service):
    """Save reports to files."""
    print_section("Example 5: Save Reports to Files")

    output_dir = Path("./phase12_reports")
    output_dir.mkdir(exist_ok=True)

    print(f"Saving Phase 12 reports to: {output_dir}")
    files = service.save_reports(str(output_dir))

    print("\n✓ Reports saved!")
    for report_name, file_path in files.items():
        file_size = Path(file_path).stat().st_size
        print(f"  - {report_name}: {file_path} ({file_size:,} bytes)")

    print("\nTo view reports:")
    print(f"  cat {output_dir}/PHASE12_ANALYSIS.json | jq '.summary'")
    print(f"  cat {output_dir}/PHASE12_COHERENCE_AUDIT.json | jq '.summary'")
    print(f"  cat {output_dir}/PHASE12_INTEGRATION_PLAN.json | jq '.summary'")

    return output_dir


def final_summary(report, output_dir):
    """Print final Phase 12 summary and guidance."""
    print_section("Phase 12 Analysis Complete")

    print("📊 Key Findings:")
    print(f"  ✓ System coherence score: {report['summary']['coherence_score']:.3f}/1.0")
    print("  ✓ Architecture health: Good")
    print(f"  ✓ Integration tasks identified: {report['summary']['integration_tasks']}")
    print(
        f"  ✓ Estimated integration effort: {report['summary']['estimated_integration_hours']} hours"
    )

    score = report["summary"]["coherence_score"]
    if score >= 0.9:
        print("\n🎉 Excellent coherence! System is in great shape.")
    elif score >= 0.7:
        print("\n✅ Good coherence! Address medium-priority issues to improve further.")
    else:
        print("\n⚠️  Coherence needs improvement. Prioritize high-severity issues.")

    print("\n🛰️  Phase 12 Status: COMPLETE (DRY-RUN Mode)")
    print("📝 Reports saved to:", output_dir)
    print("\n⏭️  Next: Review reports and prioritize integration tasks")
    print('🚀 Phase 13: Await "Initiate Phase 13 – Scalar Chrono-Synthesis" command')


def main():
    """Run Phase 12 analysis examples (orchestrator)."""
    print("🛰️  Phase 12: Scalar-Convergent Architecture Integration")
    print("=" * 80)

    srm = example_scalar_recursive_map()
    coherence_report = example_coherence_audit()
    example_integration_plan(srm, coherence_report)
    service, report = example_phase12_service()
    output_dir = save_reports(service)
    final_summary(report, output_dir)


if __name__ == "__main__":
    main()
