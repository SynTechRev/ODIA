#!/usr/bin/env python3
"""Phase 5 Orchestration Example Script.

This script demonstrates the Phase 5 autonomous orchestration capabilities
including single document analysis, cross-document synthesis, and plan generation.
"""

from oraculus_di_auditor.orchestrator import Phase5Orchestrator


def example_single_document():
    """Example: Single document analysis using Phase 5 orchestration."""
    print("=" * 80)
    print("EXAMPLE 1: Single Document Analysis")
    print("=" * 80)

    orchestrator = Phase5Orchestrator()

    request = {
        "document_text": (
            "Section 1. Budget Authorization\n"
            "\n"
            "There is hereby appropriated from the General Fund the sum of $5,000,000\n"
            "for the fiscal year ending December 31, 2025, for the purpose of funding\n"
            "the Department of Public Infrastructure.\n"
            "\n"
            "Section 2. Delegation of Authority\n"
            "\n"
            "The Secretary may promulgate such rules and regulations as "
            "deemed necessary\n"
            "to carry out the purposes of this Act.\n"
            "\n"
            "Section 3. Data Collection\n"
            "\n"
            "The Department is authorized to enter into contracts with "
            "private entities\n"
            "for the collection and analysis of citizen data "
            "related to infrastructure usage."
        ),
        "metadata": {
            "title": "Infrastructure Funding Act 2025",
            "jurisdiction": "federal",
            "document_type": "act",
            "year": 2025,
        },
    }

    # Execute orchestrated analysis
    result = orchestrator.execute_request(request)

    # Display results
    print(f"\nRequest Type: {result['request_type']}")
    print(f"Execution Mode: {result['provenance']['execution_mode']}")
    print(f"Overall Confidence: {result['confidence']:.2f}")

    print("\n--- Execution Plan ---")
    plan = result["execution_plan"]
    print(f"Agents Involved: {', '.join(plan['agents_involved'])}")
    print(f"Total Tasks: {len(plan['task_graph'])}")
    print(f"Execution Mode: {plan['execution_mode']}")

    print("\n--- Agent Results ---")
    for agent_result in result["agent_results"]:
        print(f"  {agent_result['agent']}: {agent_result['action']}")
        if "outputs" in agent_result:
            outputs = agent_result["outputs"]
            if "summary" in outputs:
                print(f"    Summary: {outputs['summary'][:80]}...")

    print("\n--- Harmonized Output ---")
    output = result["harmonized_output"]
    print("Findings:")

    for category, findings in output.get("findings", {}).items():
        if findings:
            print(f"  {category.title()}: {len(findings)} anomalies")
            for finding in findings[:2]:  # Show first 2
                print(
                    f"    - {finding.get('id', 'N/A')}: {finding.get('issue', 'N/A')}"
                )

    print("\nScores:")
    scores = output.get("scores", {})
    for score_name, score_value in scores.items():
        print(f"  {score_name}: {score_value:.2f}")

    if output.get("flags"):
        print("\nFlags:")
        for flag in output["flags"]:
            print(f"  - {flag}")


def example_cross_document():
    """Example: Cross-document analysis with theme extraction."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 2: Cross-Document Analysis")
    print("=" * 80)

    orchestrator = Phase5Orchestrator()

    request = {
        "documents": [
            {
                "text": (
                    "Budget Act 2024\n"
                    "\n"
                    "There is appropriated $2,000,000 for surveillance "
                    "equipment purchases.\n"
                    "The Secretary shall delegate authority to contractors for "
                    "data collection."
                ),
                "metadata": {"title": "Budget Act 2024", "year": 2024},
            },
            {
                "text": (
                    "Budget Act 2025\n"
                    "\n"
                    "There is appropriated $5,000,000 for expanded surveillance "
                    "programs.\n"
                    "Private contractors are authorized to handle citizen data "
                    "without oversight."
                ),
                "metadata": {"title": "Budget Act 2025", "year": 2025},
            },
            {
                "text": (
                    "Privacy Protection Act 2025\n"
                    "\n"
                    "All surveillance activities must comply with Fourth "
                    "Amendment protections.\n"
                    "Contractors must maintain strict data privacy safeguards."
                ),
                "metadata": {"title": "Privacy Protection Act 2025", "year": 2025},
            },
        ]
    }

    # Execute cross-document analysis
    result = orchestrator.execute_request(request)

    print(f"\nRequest Type: {result['request_type']}")
    print(f"Execution Mode: {result['provenance']['execution_mode']}")
    print(f"Overall Confidence: {result['confidence']:.2f}")

    print("\n--- Execution Plan ---")
    plan = result["execution_plan"]
    print(f"Agents Involved: {', '.join(plan['agents_involved'])}")
    print(f"Total Tasks: {len(plan['task_graph'])}")

    print("\n--- Cross-Document Synthesis ---")
    synthesis = result["harmonized_output"]

    print("\nSummary:")
    print(f"  {synthesis.get('summary', 'N/A')}")

    print("\nThemes:")
    for theme in synthesis.get("themes", []):
        print(f"  - {theme}")

    print("\nCross-Document Links:")
    for link in synthesis.get("cross_document_links", []):
        print(f"  Documents {link['doc1_index']} <-> {link['doc2_index']}")
        print(f"    Shared themes: {', '.join(link['shared_themes'])}")

    print("\nRisk Assessment:")
    risk = synthesis.get("risk_assessment", {})
    print(f"  Overall Risk: {risk.get('overall_risk', 0):.2f}")
    print(f"  High Priority Count: {risk.get('high_priority_count', 0)}")

    print("\nRecommendations:")
    for rec in synthesis.get("recommendations", []):
        print(f"  - {rec}")


def example_plan_only():
    """Example: Generate execution plan without executing tasks."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 3: Plan-Only Mode")
    print("=" * 80)

    orchestrator = Phase5Orchestrator()

    request = {
        "document_text": "Sample legislation for planning purposes.",
        "metadata": {"title": "Test Act"},
    }

    # Generate plan only (don't execute)
    result = orchestrator.execute_request(request, mode="plan_only")

    print(f"\nMode: {result['mode']}")
    print(f"Request Type: {result['request_type']}")

    plan = result["execution_plan"]
    print("\n--- Execution Plan ---")
    print(f"Execution Mode: {plan['execution_mode']}")
    print(f"Agents Involved: {', '.join(plan['agents_involved'])}")
    print(f"Expected Outputs: {', '.join(plan['expected_outputs'])}")
    print(f"Confidence: {plan['confidence']:.2f}")

    print("\n--- Task Graph ---")
    for task in plan["task_graph"]:
        deps = task.get("dependencies", [])
        deps_str = f" (depends on: {', '.join(deps)})" if deps else ""
        print(f"  {task['task_id']}: {task['agent_name']}.{task['action']}{deps_str}")

    print("\n--- Dependencies ---")
    for dep in plan["dependencies"]:
        print(f"  {dep['task_id']} depends on: {', '.join(dep['depends_on'])}")


def example_agent_info():
    """Example: Get information about available agents."""
    print("\n\n")
    print("=" * 80)
    print("EXAMPLE 4: Agent Information")
    print("=" * 80)

    orchestrator = Phase5Orchestrator()
    info = orchestrator.get_agent_info()

    print("\n--- Available Agents ---")
    for agent in info["agents"]:
        print(f"\n{agent}:")
        capabilities = info["capabilities"].get(agent, [])
        for capability in capabilities:
            print(f"  - {capability}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "PHASE 5 ORCHESTRATION EXAMPLES" + " " * 28 + "║")
    print("║" + " " * 78 + "║")
    print(
        "║  Demonstrates autonomous multi-agent coordination, task scheduling,"
        + " " * 9
        + "║"
    )
    print(
        "║  and deterministic execution for complex document analysis workflows."
        + " " * 4
        + "║"
    )
    print("╚" + "=" * 78 + "╝")

    try:
        example_single_document()
        example_cross_document()
        example_plan_only()
        example_agent_info()

        print("\n\n")
        print("=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
