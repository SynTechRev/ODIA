#!/usr/bin/env python3
"""
Validate Constitutional Linguistic Frameworks schema.

This script validates the CLF JSON against required schema constraints
for use in CI/CD and pre-commit hooks.
"""

import json
import sys
from pathlib import Path


def validate_clf_schema():  # noqa: C901
    """Validate CLF JSON schema."""
    repo_root = Path(__file__).parent.parent
    clf_file = (
        repo_root / "constitutional" / "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
    )

    if not clf_file.exists():
        print(f"[FAIL] CLF file not found: {clf_file}")
        return False

    try:
        with open(clf_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FAIL] Invalid JSON in CLF file: {e}")
        return False

    errors = []
    warnings = []

    # Check version
    if "version" not in data:
        errors.append("Missing 'version' field")

    # Check metadata
    if "metadata" not in data:
        errors.append("Missing 'metadata' section")
    elif data["metadata"].get("total_frameworks") != 10:
        errors.append(
            f"Expected 10 frameworks, got {data['metadata'].get('total_frameworks')}"
        )

    # Check frameworks
    if "frameworks" not in data:
        errors.append("Missing 'frameworks' section")
        return False

    frameworks = data["frameworks"]
    if len(frameworks) != 10:
        errors.append(f"Expected 10 frameworks, found {len(frameworks)}")

    # Required fields for each framework
    required_fields = [
        "framework_id",
        "name",
        "definition",
        "method",
        "historical_origin",
        "temporal_scope",
        "strengths",
        "weaknesses",
        "landmark_cases",
        "jim_weight",
        "ace_weight",
        "semantic_drift",
        "key_scholars",
    ]

    for framework_id, framework in frameworks.items():
        for field in required_fields:
            if field not in framework:
                errors.append(f"Framework '{framework_id}' missing field '{field}'")

        # Check weight ranges
        jim_weight = framework.get("jim_weight", 0)
        ace_weight = framework.get("ace_weight", 0)

        if not (0.05 <= jim_weight <= 0.40):
            warnings.append(
                f"Framework '{framework_id}' jim_weight {jim_weight} outside range [0.05, 0.40]"  # noqa: E501
            )

        if not (0.05 <= ace_weight <= 0.40):
            warnings.append(
                f"Framework '{framework_id}' ace_weight {ace_weight} outside range [0.05, 0.40]"  # noqa: E501
            )

    # Check weight totals
    jim_total = sum(f.get("jim_weight", 0) for f in frameworks.values())
    ace_total = sum(f.get("ace_weight", 0) for f in frameworks.values())

    if not (2.0 <= jim_total <= 2.5):
        warnings.append(f"JIM total weight {jim_total:.2f} outside range [2.0, 2.5]")

    if not (2.0 <= ace_total <= 2.5):
        warnings.append(f"ACE total weight {ace_total:.2f} outside range [2.0, 2.5]")

    # Report results
    if errors:
        print("[FAIL] CLF Schema Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        return False

    if warnings:
        print("[OK] CLF Schema Validation PASSED (with warnings):")
        for warning in warnings:
            print(f"  - {warning}")
    else:
        print("[OK] CLF Schema Validation PASSED")
        print("  - 10 frameworks validated")
        print(f"  - JIM total weight: {jim_total:.2f}")
        print(f"  - ACE total weight: {ace_total:.2f}")

    return True


if __name__ == "__main__":
    success = validate_clf_schema()
    sys.exit(0 if success else 1)
