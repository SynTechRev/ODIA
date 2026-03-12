#!/usr/bin/env python3
"""
Schema Validation Script

Validates all artifacts against their corresponding JSON schemas.
Performs light auto-fixing for missing keys but rejects type mismatches.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

# Mapping of artifacts to their schemas
ARTIFACT_SCHEMA_MAP = {
    "oraculus/corpus/ingestion_report.json": "schemas/ingestion_report_schema.json",
    "oraculus/corpus/VALIDATION_REPORT.json": "schemas/validation_report_schema.json",
    "analysis/ace/ACE_REPORT.json": "schemas/ace_report_schema.json",
    "analysis/vendor/vendor_graph.json": "schemas/vendor_graph_schema.json",
    "analysis/vendor/VENDOR_ANOMALY_LINKS.json": "schemas/vendor_anomaly_links_schema.json",
    "analysis/pdf_forensics/forensic_report.json": "schemas/forensic_report_schema.json",
    "analysis/pdf_forensics/metadata_inconsistency_map.json": "schemas/metadata_inconsistency_schema.json",
    "analysis/jim/JIM_REPORT.json": "schemas/jim_report_schema.json",
    "analysis/semantic/SEMANTIC_HARMONIZATION_MATRIX.json": "schemas/semantic_matrix_schema.json",
    "analysis/semantic/MEANING_DIVERGENCE_INDEX.json": "schemas/divergence_index_schema.json",
    "transparency_release/corpus_manifest.json": "schemas/corpus_manifest_schema.json",
}

LOG_FILE = Path(_repo_root) / "analysis" / "logs" / "schema_validation.log"


def log_message(message: str) -> None:
    """Log a message to both console and validation log."""
    import os

    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    # Skip file logging during pre-commit to avoid file modifications
    if os.environ.get("PRE_COMMIT") != "1":
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")


def create_minimal_schemas() -> None:
    """Create minimal schemas if they don't exist."""
    schemas_dir = _repo_root / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    minimal_schemas = {
        "ingestion_report_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["total_files", "extraction_success_rate"],
            "properties": {
                "total_files": {"type": "number"},
                "extraction_success_rate": {"type": "number"},
                "corpora_processed": {"type": "number"},
                "pdfs_scanned": {"type": "number"},
                "flagged_irregularities": {"type": "array"},
            },
        },
        "validation_report_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["total_files", "extraction_success_rate"],
            "properties": {
                "total_files": {"type": "number"},
                "extraction_success_rate": {"type": "number"},
                "missing_items": {"type": "array"},
                "timeline": {"type": "object"},
            },
        },
        "ace_report_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["summary", "anomalies"],
            "properties": {
                "summary": {
                    "type": "object",
                    "properties": {
                        "total_anomalies": {"type": "number"},
                        "by_type": {"type": "object"},
                    },
                },
                "anomalies": {"type": "array"},
                "top_anomalies": {"type": "array"},
            },
        },
        "vendor_graph_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["nodes"],
            "properties": {
                "nodes": {"type": "array"},
                "edges": {"type": "array"},
                "vendors": {"type": "array"},
            },
        },
        "vendor_anomaly_links_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "links": {"type": "array"},
                "anomaly_links": {"type": "array"},
            },
        },
        "forensic_report_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["total_scanned", "anomalies"],
            "properties": {
                "total_scanned": {"type": "number"},
                "anomalies": {"type": "array"},
            },
        },
        "metadata_inconsistency_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
        },
        "jim_report_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "summary": {"type": "object"},
                "cases_count": {"type": "number"},
            },
        },
        "semantic_matrix_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["entries"],
            "properties": {
                "entries": {"type": "array"},
            },
        },
        "divergence_index_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["terms"],
            "properties": {
                "terms": {"type": "object"},
            },
        },
        "corpus_manifest_schema.json": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["files"],
            "properties": {
                "files": {"type": "array"},
                "manifest_version": {"type": "string"},
            },
        },
    }

    for schema_name, schema_content in minimal_schemas.items():
        schema_path = schemas_dir / schema_name
        if not schema_path.exists():
            with open(schema_path, "w", encoding="utf-8") as f:
                json.dump(schema_content, f, indent=2)
            log_message(f"Created minimal schema: {schema_name}")


def load_schema(schema_path: str) -> dict[str, Any] | None:
    """Load a JSON schema file."""
    full_path = _repo_root / schema_path
    if not full_path.exists():
        return None

    try:
        with open(full_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_message(f"ERROR loading schema {schema_path}: {e}")
        return None


def load_artifact(artifact_path: str) -> dict[str, Any] | None:
    """Load an artifact JSON file."""
    full_path = _repo_root / artifact_path
    if not full_path.exists():
        return None

    try:
        with open(full_path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_message(f"ERROR loading artifact {artifact_path}: {e}")
        return None


def validate_artifact(
    artifact_path: str, schema_path: str, auto_fix: bool = True
) -> dict[str, Any]:
    """Validate an artifact against its schema."""
    result = {
        "artifact": artifact_path,
        "schema": schema_path,
        "valid": False,
        "errors": [],
        "fixed": False,
    }

    # Load artifact
    artifact = load_artifact(artifact_path)
    if artifact is None:
        result["errors"].append(f"Artifact not found or unreadable: {artifact_path}")
        return result

    # Load schema
    schema = load_schema(schema_path)
    if schema is None:
        result["errors"].append(f"Schema not found: {schema_path}")
        return result

    # Validate
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(artifact))

    if not errors:
        result["valid"] = True
        return result

    # Collect errors
    for error in errors:
        error_path = ".".join(str(p) for p in error.path)
        result["errors"].append(f"{error_path}: {error.message}")

    # Attempt auto-fix for missing keys (only if all errors are missing keys)
    if auto_fix:
        missing_key_errors = [
            e for e in errors if "is a required property" in e.message
        ]

        if missing_key_errors and len(missing_key_errors) == len(errors):
            # All errors are missing required keys - can auto-fix
            modified = False
            for error in missing_key_errors:
                # Extract property name from error message
                prop = error.message.split("'")[1] if "'" in error.message else None
                if prop and prop in schema.get("properties", {}):
                    # Add default value based on type
                    prop_schema = schema["properties"][prop]
                    prop_type = prop_schema.get("type", "string")

                    if prop_type == "array":
                        artifact[prop] = []
                    elif prop_type == "object":
                        artifact[prop] = {}
                    elif prop_type == "number":
                        artifact[prop] = 0
                    elif prop_type == "string":
                        artifact[prop] = ""  # Empty string instead of "unknown"
                    elif prop_type == "boolean":
                        artifact[prop] = False
                    else:
                        artifact[prop] = None

                    modified = True

            if modified:
                # Save fixed artifact
                full_path = _repo_root / artifact_path
                try:
                    with open(full_path, "w", encoding="utf-8") as f:
                        json.dump(artifact, f, indent=2, ensure_ascii=False)
                    result["fixed"] = True
                    result["valid"] = True
                    result["errors"] = []
                    log_message(f"Auto-fixed missing keys in: {artifact_path}")
                except Exception as e:
                    result["errors"].append(f"Failed to save fixed artifact: {e}")

    return result


def validate_all_artifacts(
    auto_fix: bool = True, fail_on_error: bool = True
) -> dict[str, Any]:
    """Validate all artifacts against their schemas."""
    results = {
        "validated": 0,
        "valid": 0,
        "fixed": 0,
        "failed": 0,
        "details": [],
    }

    log_message("=" * 80)
    log_message("Starting Schema Validation")
    log_message("=" * 80)

    for artifact_path, schema_path in ARTIFACT_SCHEMA_MAP.items():
        results["validated"] += 1
        result = validate_artifact(artifact_path, schema_path, auto_fix)
        results["details"].append(result)

        if result["valid"]:
            results["valid"] += 1
            if result["fixed"]:
                results["fixed"] += 1
                log_message(f"[OK] Fixed and validated: {artifact_path}")
            else:
                log_message(f"[OK] Valid: {artifact_path}")
        else:
            results["failed"] += 1
            log_message(f"[FAIL] Validation failed: {artifact_path}")
            for error in result["errors"]:
                log_message(f"  - {error}")

    log_message("=" * 80)
    log_message("Schema Validation Complete")
    log_message(f"Validated: {results['validated']}")
    log_message(f"Valid: {results['valid']}")
    log_message(f"Fixed: {results['fixed']}")
    log_message(f"Failed: {results['failed']}")
    log_message("=" * 80)

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate artifacts against JSON schemas"
    )
    parser.add_argument(
        "--no-auto-fix",
        action="store_true",
        help="Disable automatic fixing of missing keys",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Don't fail CI on validation errors (for initial setup)",
    )
    args = parser.parse_args()

    print("Schema Validation Script")
    print("=" * 80)

    # Create minimal schemas if needed
    create_minimal_schemas()

    # Validate all artifacts
    results = validate_all_artifacts(
        auto_fix=not args.no_auto_fix,
        fail_on_error=not args.no_fail,
    )

    # Exit with error code if validation failed and fail_on_error is True
    if results["failed"] > 0 and not args.no_fail:
        print(f"\n[FAIL] Validation failed for {results['failed']} artifacts")
        sys.exit(1)

    if results["fixed"] > 0:
        print(f"\n[OK] Success: {results['fixed']} artifacts auto-fixed")
    else:
        print("\n[OK] Success: All artifacts validated")

    sys.exit(0)


if __name__ == "__main__":
    main()
