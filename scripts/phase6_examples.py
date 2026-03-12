#!/usr/bin/env python3
"""Phase 6 Frontend Orchestration Examples.

This script demonstrates the Phase 6 frontend orchestration system,
showing how to generate front-end architecture and build instructions
for the Oraculus-DI-Auditor UI.

Examples:
1. Generate a task plan for front-end development
2. Generate complete build instructions
3. Perform gap analysis
4. Generate full Phase 6 bundle with all outputs

Run this script:
    python scripts/phase6_examples.py
"""

import json

from oraculus_di_auditor.frontend import Phase6Orchestrator


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_json(data: dict, indent: int = 2) -> None:
    """Print JSON data with formatting."""
    print(json.dumps(data, indent=indent))


def example_1_task_plan():
    """Example 1: Generate a front-end task plan."""
    print_section("Example 1: Front-End Task Plan Generation")

    orchestrator = Phase6Orchestrator()

    request = {
        "type": "task_plan",
        "framework": "nextjs",
    }

    result = orchestrator.execute_request(request)

    print("Request:")
    print_json(request)
    print("\nResult Summary:")
    print(f"  - Components to build: {len(result['components'])}")
    print(f"  - APIs needed: {len(result['apis_needed'])}")
    print(f"  - Data models: {len(result['data_models'])}")
    print(f"  - State management: {result['state_management']['library']}")
    print(f"  - Readiness score: {result['readiness_score']:.2f}")
    print(f"  - Risk flags: {len(result['risk_flags'])}")

    print("\nComponent Categories:")
    categories = {}
    for component in result["components"]:
        cat = component["category"]
        categories[cat] = categories.get(cat, 0) + 1

    for category, count in categories.items():
        print(f"  - {category}: {count} components")

    print("\nExecution Order (first 5 steps):")
    for step in result["execution_order"][:5]:
        print(f"  {step}")

    if result["risk_flags"]:
        print("\nRisk Flags:")
        for flag in result["risk_flags"]:
            print(f"  ⚠️  {flag}")


def example_2_build_instructions():
    """Example 2: Generate build instructions."""
    print_section("Example 2: Front-End Build Instructions")

    orchestrator = Phase6Orchestrator()

    request = {
        "type": "build_instructions",
        "framework": "nextjs",
    }

    result = orchestrator.execute_request(request)

    print("Request:")
    print_json(request)
    print("\nBuild Instructions Summary:")
    print(f"  - Framework: {result['framework']}")
    print(f"  - Scaffold commands: {len(result['scaffold_commands'])}")
    print(f"  - Setup steps: {len(result['setup_steps'])}")
    print(f"  - Integration steps: {len(result['integration_steps'])}")
    print(f"  - Success criteria: {len(result['success_criteria'])}")

    print("\nScaffold Commands:")
    for cmd in result["scaffold_commands"]:
        print(f"  $ {cmd}")

    print("\nDirectory Structure:")
    structure = result["directory_structure"]["structure"]
    print(f"  Root: {result['directory_structure']['root']}")
    for key in list(structure.keys())[:3]:
        print(f"  - {key}")

    print("\nSetup Steps (first 2):")
    for step in result["setup_steps"][:2]:
        print(f"  Step {step['step']}: {step['action']}")
        if step.get("commands"):
            print(f"    Commands: {len(step['commands'])} command(s)")

    print("\nSuccess Criteria (first 5):")
    for criteria in result["success_criteria"][:5]:
        print(f"  {criteria}")


def example_3_gap_report():
    """Example 3: Generate gap identification report."""
    print_section("Example 3: Gap Identification Report")

    orchestrator = Phase6Orchestrator()

    request = {
        "type": "gap_report",
    }

    result = orchestrator.execute_request(request)

    print("Request:")
    print_json(request)
    print("\nGap Report Summary:")
    print(f"  - Overall Priority: {result['priority'].upper()}")
    print(f"  - Missing endpoints: {len(result['missing_endpoints'])}")
    print(f"  - Missing UI components: {len(result['missing_ui_components'])}")
    print(f"  - Backend incompatibilities: {len(result['backend_incompatibilities'])}")
    print(f"  - Security issues: {len(result['security_issues'])}")
    print(f"  - Suggested fixes: {len(result['suggested_fixes'])}")

    if result["missing_endpoints"]:
        print("\nMissing Endpoints (first 3):")
        for endpoint in result["missing_endpoints"][:3]:
            print(f"  - {endpoint['path']} ({endpoint['priority']})")
            print(f"    {endpoint['description']}")

    if result["security_issues"]:
        print("\nSecurity Issues (first 3):")
        for issue in result["security_issues"][:3]:
            print(f"  - {issue['type']} (Severity: {issue['severity']})")
            print(f"    {issue['description']}")

    if result["suggested_fixes"]:
        print("\nSuggested Fixes (first 3):")
        for fix in result["suggested_fixes"][:3]:
            print(f"  - {fix['gap']}")
            print(f"    Fix: {fix['fix']}")
            print(f"    Priority: {fix['priority']}")


def example_4_full_bundle():
    """Example 4: Generate complete Phase 6 output bundle."""
    print_section("Example 4: Complete Phase 6 Output Bundle")

    orchestrator = Phase6Orchestrator()

    request = {
        "type": "full_bundle",
        "framework": "nextjs",
    }

    result = orchestrator.execute_request(request)

    print("Request:")
    print_json(request)
    print("\nFull Bundle Summary:")
    print(f"  - Framework: {result['architecture']['framework']}")
    print(f"  - Pattern: {result['architecture']['pattern']}")
    print(f"  - Language: {result['architecture']['language']}")
    print(f"  - Styling: {result['architecture']['styling']}")
    print(f"  - State Management: {result['architecture']['state_management']}")
    print(f"  - Overall Confidence: {result['confidence']:.2f}")

    print("\nArchitecture Principles:")
    for principle in result["architecture"]["principles"][:5]:
        print(f"  - {principle}")

    print("\nComponent Categories:")
    for category, specs in result["components"].items():
        if isinstance(specs, dict):
            print(f"  - {category}: {len(specs)} detailed specs")

    print("\nAPI Client Structure:")
    api_client = result["api_client"]
    print(f"  - Files: {len(api_client['structure']['files'])}")
    print(f"  - Types: {len(api_client['types'])}")
    print(f"  - Methods: {len(api_client['methods'])}")

    print("\nState Model Stores:")
    for store_name, store_spec in result["state_model"]["stores"].items():
        print(f"  - {store_name}")
        print(f"    Actions: {len(store_spec['actions'])}")

    print("\nTesting Strategy:")
    testing = result["testing"]
    print(f"  - Unit tests: {testing['unit_tests']['tool']}")
    print(f"  - Integration tests: {testing['integration_tests']['tool']}")
    print(f"  - Target coverage: {testing['unit_tests']['target']}")

    print("\nDeployment Platforms:")
    for platform, config in result["deployment"]["platforms"].items():
        rec = "[OK]" if config.get("recommended") else " "
        print(f"  [{rec}] {platform}")

    print("\nIncluded Sub-Reports:")
    print(f"  - Task Plan: [OK] ({len(result['task_plan']['components'])} components)")
    print(
        f"  - Build Instructions: [OK] ("
        f"{len(result['build_instructions']['setup_steps'])} steps)"
    )
    print(f"  - Gap Report: [OK] (Priority: {result['gap_report']['priority']})")

    print("\nRecommended Next Phase:")
    print(f"  {result['recommended_next_phase']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  PHASE 6 FRONTEND ORCHESTRATION EXAMPLES")
    print("  Oraculus-DI-Auditor - Front-End System & User Interaction Layer")
    print("=" * 80)

    try:
        example_1_task_plan()
        example_2_build_instructions()
        example_3_gap_report()
        example_4_full_bundle()

        print("\n" + "=" * 80)
        print("  Examples completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
