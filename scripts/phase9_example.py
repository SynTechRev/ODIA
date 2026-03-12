#!/usr/bin/env python3
"""Phase 9 Governor Example Script.

Demonstrates usage of the Pipeline Governor & Compliance Engine.
"""

from __future__ import annotations


def _banner(title: str) -> None:
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()


def _example_system_state(service) -> None:
    print("Example 1: System State Check")
    print("-" * 80)
    state = service.get_system_state()
    print(f"Timestamp: {state['timestamp']}")
    print(f"Overall Health: {state['overall_health']}")
    print(f"Governor Version: {state['governor_version']}")
    print(f"Policy Version: {state['policy_version']}")
    print(f"Security Posture: {state['security_posture']}")
    print("Validation Summary:")
    for key, value in state["validation_summary"].items():
        print(f"  {key}: {value}")
    print()


def _example_validation(service, deep: bool) -> None:
    label = "Deep" if deep else "Quick"
    print(f"Example {2 if not deep else 3}: Pipeline Validation ({label})")
    print("-" * 80)
    result = service.validate_pipeline(deep=deep)
    print(f"Overall Status: {result['overall_status']}")
    print(f"Checks Performed: {len(result['checks'])}")
    for check_name, check_result in result["checks"].items():
        status = check_result.get("status", "N/A")
        print(f"  {check_name}: {status}")
        if deep and status == "error":
            for error in check_result.get("errors", []):
                print(f"    ERROR: {error}")
    print()


def _example_clean_enforcement(service) -> None:
    print("Example 4: Clean Document - Policy Enforcement")
    print("-" * 80)
    clean_document = (
        "This is a clean legal document with appropriate content. "
        "It contains sufficient text for analysis and has no malicious patterns. "
        "The document discusses legislative procedures and statutory interpretation."
    )
    clean_metadata = {
        "document_id": "doc_2025_001",
        "title": "Legislative Analysis Document",
        "jurisdiction": "federal",
        "hash": "a" * 64,
    }
    result = service.enforce_policies(clean_document, clean_metadata)
    print(f"Enforcement Status: {result['enforcement_status']}")
    print(f"Checks Performed: {', '.join(result['checks_performed'])}")
    print(f"Violations: {len(result['violations'])}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"Threat Score: {result['security_profile']['threat_score']}")
    print()


def _example_malicious_enforcement(service) -> None:
    print("Example 5: Malicious Document - Policy Enforcement")
    print("-" * 80)
    malicious_document = (
        "<script>alert('XSS Attack')</script> This document contains malicious content."
    )
    malicious_metadata = {"title": "Suspicious Document"}
    result = service.enforce_policies(malicious_document, malicious_metadata)
    print(f"Enforcement Status: {result['enforcement_status']}")
    print(f"Checks Performed: {', '.join(result['checks_performed'])}")
    print(f"Violations: {len(result['violations'])}")
    print(f"Threat Score: {result['security_profile']['threat_score']}")
    if result["violations"]:
        print("Violations Detected:")
        for violation in result["violations"]:
            v_type = violation.get("type", "unknown")
            v_sev = violation.get("severity", "unknown")
            v_desc = violation.get("description", "N/A")
            print(f"  - {v_type} | {v_sev}: {v_desc}")
    print()


def _example_gatekeeper(gatekeeper) -> None:
    print("Example 6: Security Gatekeeper - Threat Detection")
    print("-" * 80)
    test_documents = [
        ("Clean text", "This is normal document text."),
        ("XSS Attack", "<script>alert('xss')</script>"),
        ("SQL Injection", "SELECT * FROM users WHERE id=1"),
        ("Path Traversal", "../../etc/passwd"),
    ]
    for name, text in test_documents:
        result = gatekeeper.sanitize_input(text, {})
        print(f"{name}:")
        print(f"  Status: {result['status']}")
        print(f"  Threat Score: {result['threat_score']}")
        print(f"  Threats: {len(result['threats_detected'])}")
        for threat in result.get("threats_detected", []):
            print(f"    - {threat['type']} (severity: {threat['severity']})")
    print()


def _example_policy_engine(policy_engine) -> None:
    print("Example 7: Policy Engine - Document Policies")
    print("-" * 80)
    short_doc = "Short"
    result = policy_engine.evaluate_document_policies(short_doc, {})
    print("Too Short Document:")
    print(f"  Status: {result['status']}")
    print(f"  Violations: {len(result['violations'])}")
    valid_doc = "This is a valid document with sufficient content."
    result = policy_engine.evaluate_document_policies(valid_doc, {"title": "Test"})
    print("Valid Document:")
    print(f"  Status: {result['status']}")
    print(f"  Violations: {len(result['violations'])}")
    print()


def _example_orchestrator_job(service) -> None:
    print("Example 8: Orchestrator Job Validation")
    print("-" * 80)
    result = service.validate_orchestrator_job(5)
    print("Valid Job (5 documents):")
    print(f"  Status: {result['validation_status']}")
    print(f"  Violations: {len(result['violations'])}")
    result = service.validate_orchestrator_job(150)
    print("Too Many Documents (150):")
    print(f"  Status: {result['validation_status']}")
    print(f"  Violations: {len(result['violations'])}")
    for violation in result.get("violations", []):
        print(f"    - {violation['policy']}: {violation['description']}")
    print()


def _example_security_profile(gatekeeper) -> None:
    print("Example 9: Security Profile Generation")
    print("-" * 80)
    profile = gatekeeper.generate_security_profile(
        "Clean document for security profiling.",
        {"document_id": "doc_profile_001", "title": "Test"},
        "text/plain",
    )
    print(f"Timestamp: {profile['timestamp']}")
    print(f"Overall Status: {profile['overall_status']}")
    print(f"Threat Score: {profile['threat_score']}")
    print("Checks:")
    for check_name, check_result in profile["checks"].items():
        print(f"  {check_name}: {check_result.get('status', 'N/A')}")
    print()


def _example_compliance_report(policy_engine) -> None:
    print("Example 10: Compliance Report")
    print("-" * 80)
    evaluations = [
        {"status": "compliant", "violations": [], "warnings": []},
        {
            "status": "non_compliant",
            "violations": [{"severity": "error"}],
            "warnings": [],
        },
        {
            "status": "compliant",
            "violations": [],
            "warnings": [{"severity": "warning"}],
        },
    ]
    report = policy_engine.generate_compliance_report(evaluations)
    print(f"Policy Version: {report['policy_version']}")
    print(f"Overall Compliance: {report['overall_compliance']}")
    print(f"Total Evaluations: {report['total_evaluations']}")
    print(f"Compliant: {report['compliant_count']}")
    print(f"Non-Compliant: {report['non_compliant_count']}")
    print(f"Total Violations: {report['total_violations']}")
    print(f"Total Warnings: {report['total_warnings']}")
    for rec in report.get("recommendations", []):
        print(f"  - {rec}")
    print()


def _summary() -> None:
    _banner("Phase 9 Governor Examples Complete")
    print("The Pipeline Governor provides:")
    print("  [OK] System health monitoring")
    print("  [OK] Pipeline validation (quick & deep)")
    print("  [OK] Policy enforcement")
    print("  [OK] Threat detection & scoring")
    print("  [OK] Security profiling")
    print("  [OK] Compliance reporting")
    print("For more details, see:")
    print("  - PHASE9_GOVERNOR_IMPLEMENTATION.md")
    print("  - PHASE9_POLICY_REFERENCE.md")
    print("  - PHASE9_SECURITY_PROFILE.md")
    print()


def main() -> None:
    """Run all Phase 9 governor examples (refactored for lower complexity)."""
    from oraculus_di_auditor.governor import (
        GovernorService,
        PolicyEngine,
        SecurityGatekeeper,
    )

    _banner("Phase 9: Pipeline Governor & Compliance Engine - Example Usage")
    service = GovernorService()
    policy_engine = PolicyEngine()
    gatekeeper = SecurityGatekeeper()

    _example_system_state(service)
    _example_validation(service, deep=False)
    _example_validation(service, deep=True)
    _example_clean_enforcement(service)
    _example_malicious_enforcement(service)
    _example_gatekeeper(gatekeeper)
    _example_policy_engine(policy_engine)
    _example_orchestrator_job(service)
    _example_security_profile(gatekeeper)
    _example_compliance_report(policy_engine)
    _summary()


if __name__ == "__main__":
    main()
