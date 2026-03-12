#!/usr/bin/env python
"""Phase 8 Orchestrator Integration Example

This script demonstrates the complete Phase 8 Multi-Document Orchestrator
functionality with end-to-end testing and visualization of results.

Usage:
    python scripts/phase8_example.py
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from oraculus_di_auditor.interface.routes.orchestrator import (
    DocumentInput,
    OrchestratorRequest,
    OrchestratorService,
)


def print_banner(text: str) -> None:
    """Print a formatted banner."""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def example_1_basic_orchestration() -> None:
    """Example 1: Basic multi-document orchestration."""
    print_banner("Example 1: Basic Multi-Document Orchestration")

    service = OrchestratorService()

    # Create sample documents
    documents = [
        DocumentInput(
            document_text=(
                "There is appropriated $1,000,000 for fiscal year 2025. "
                "Additional funding of $500,000 is allocated."
            ),
            metadata={
                "title": "Budget Appropriations Act 2025",
                "jurisdiction": "federal",
                "document_type": "act",
            },
        ),
        DocumentInput(
            document_text=(
                "The Secretary may delegate any authority as deemed appropriate. "
                "No specific standards or intelligible principles are required."
            ),
            metadata={
                "title": "Administrative Delegation Act",
                "jurisdiction": "federal",
                "document_type": "act",
            },
        ),
    ]

    # Execute orchestration
    request = OrchestratorRequest(documents=documents, options={})
    result = service.execute_orchestration(request)

    # Display results
    print("✅ Orchestration completed successfully!")
    print(f"\nJob ID: {result.job_id}")
    print(f"Status: {result.status}")
    print(f"Documents Analyzed: {result.documents_analyzed}")
    print(f"Timestamp: {result.timestamp}\n")

    # Show per-document results
    print("Per-Document Results:")
    print("-" * 80)
    for idx, dr in enumerate(result.document_results, 1):
        print(f"\nDocument {idx}: {dr.metadata.get('title', 'Unknown')}")
        print(f"  Document ID: {dr.document_id}")
        print(f"  Severity Score: {dr.severity_score:.2f}")
        print(f"  Lattice Score: {dr.lattice_score:.2f}")
        print(f"  Total Findings: {sum(len(f) for f in dr.findings.values())}")
        for agent_type, findings in dr.findings.items():
            if findings:
                print(f"    - {agent_type}: {len(findings)} findings")

    # Show cross-document patterns
    if result.cross_document_patterns:
        print("\n" + "-" * 80)
        print(f"\nCross-Document Patterns ({len(result.cross_document_patterns)}):")
        for pattern in result.cross_document_patterns:
            print(f"\n  Pattern: {pattern.pattern_type}")
            print(f"  Description: {pattern.description}")
            print(f"  Confidence: {pattern.confidence:.2f}")
            print(f"  Documents: {len(pattern.document_ids)}")
            if pattern.evidence:
                print("  Evidence:")
                for evidence in pattern.evidence[:2]:
                    print(f"    - {evidence}")

    # Show correlated anomalies
    if result.correlated_anomalies:
        print("\n" + "-" * 80)
        print(f"\nCorrelated Anomalies ({len(result.correlated_anomalies)}):")
        for corr in result.correlated_anomalies:
            print(f"\n  Type: {corr['correlation_type']}")
            print(f"  Description: {corr['description']}")
            print(f"  Severity: {corr['severity']}")
            print(f"  Confidence: {corr['confidence']:.2f}")
            print(f"  Total Findings: {corr.get('total_findings', 0)}")


def example_2_large_batch() -> None:
    """Example 2: Large batch processing."""
    print_banner("Example 2: Large Batch Processing (10 Documents)")

    service = OrchestratorService()

    # Create 10 sample documents with varying content
    documents = []
    for i in range(10):
        if i % 3 == 0:
            text = f"Document {i}: There is appropriated ${i * 100000} for programs."
        elif i % 3 == 1:
            text = f"Document {i}: The agency may delegate authority as necessary."
        else:
            text = f"Document {i}: This is a standard legislative text."

        documents.append(
            DocumentInput(
                document_text=text,
                metadata={
                    "title": f"Document {i}",
                    "document_type": "act",
                    "index": i,
                },
            )
        )

    # Execute orchestration
    request = OrchestratorRequest(documents=documents, options={})
    start_time = datetime.now(UTC)
    result = service.execute_orchestration(request)
    end_time = datetime.now(UTC)

    # Calculate performance metrics
    duration = (end_time - start_time).total_seconds()
    docs_per_second = len(documents) / duration if duration > 0 else 0

    print("✅ Batch orchestration completed!")
    print("\nPerformance Metrics:")
    print(f"  Documents Processed: {result.documents_analyzed}")
    print(f"  Duration: {duration:.2f} seconds")
    print(f"  Throughput: {docs_per_second:.2f} docs/sec")
    print(f"  Total Findings: {result.metadata.get('total_findings', 0)}")
    print(f"  Patterns Detected: {len(result.cross_document_patterns)}")
    print(f"  Correlations Found: {len(result.correlated_anomalies)}")

    # Show summary statistics
    severities = [dr.severity_score for dr in result.document_results]
    avg_severity = sum(severities) / len(severities) if severities else 0

    print("\nAnalysis Summary:")
    print(f"  Average Severity: {avg_severity:.2f}")
    print(f"  Max Severity: {max(severities, default=0.0):.2f}")
    print(f"  Min Severity: {min(severities, default=0.0):.2f}")


def example_3_execution_log() -> None:
    """Example 3: Execution log analysis."""
    print_banner("Example 3: Execution Log Analysis")

    service = OrchestratorService()

    documents = [
        DocumentInput(
            document_text="Sample document for log analysis.",
            metadata={"title": "Test Document"},
        )
    ]

    request = OrchestratorRequest(documents=documents, options={})
    result = service.execute_orchestration(request)

    print(f"Execution Log Analysis for Job {result.job_id}\n")
    print(f"Total Log Events: {len(result.execution_log)}\n")

    # Group events by type
    event_counts = {}
    for log_entry in result.execution_log:
        event_type = log_entry["event"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1

    print("Event Type Distribution:")
    for event_type, count in sorted(event_counts.items()):
        print(f"  {event_type:35s}: {count:3d}")

    # Show timeline
    print("\nExecution Timeline:")
    print("-" * 80)
    for log_entry in result.execution_log:
        timestamp = log_entry["timestamp"]
        event = log_entry["event"]
        print(f"  {timestamp} | {event}")


def example_4_api_response() -> None:
    """Example 4: Complete API response structure."""
    print_banner("Example 4: Complete API Response Structure")

    service = OrchestratorService()

    documents = [
        DocumentInput(
            document_text="Sample document text.",
            metadata={"title": "API Test Document"},
        )
    ]

    request = OrchestratorRequest(documents=documents, options={})
    result = service.execute_orchestration(request)

    # Convert to dict for JSON serialization
    result_dict = result.model_dump()

    print("Complete API Response Structure:\n")
    print(json.dumps(result_dict, indent=2, default=str)[:2000] + "...")
    print(f"\nResponse Size: {len(json.dumps(result_dict))} bytes")


def main() -> None:
    """Run all examples."""
    print("\n" + "=" * 80)
    print("  PHASE 8 MULTI-DOCUMENT ORCHESTRATOR EXAMPLES")
    print("=" * 80)

    examples = [
        ("Basic Multi-Document Orchestration", example_1_basic_orchestration),
        ("Large Batch Processing", example_2_large_batch),
        ("Execution Log Analysis", example_3_execution_log),
        ("API Response Structure", example_4_api_response),
    ]

    for name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("  Examples completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
