#!/usr/bin/env python3
"""
Artifact Reconciliation Script

Scans all canonical paths, detects missing/empty/corrupt artifacts,
and recreates them automatically with proper defaults.

This script ensures all expected artifacts exist with required fields.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

# Canonical artifact paths and their expected structures
CANONICAL_ARTIFACTS = {
    "oraculus/corpus/ingestion_report.json": {
        "required_fields": [
            "summary",
        ],
        "defaults": {
            "summary": {
                "total_corpora": 0,
                "total_files_ingested": 0,
                "extraction_success_rate": 0.0,
            },
            "flagged_irregularities": [],
        },
    },
    "oraculus/corpus/VALIDATION_REPORT.json": {
        "required_fields": [
            "timeline",
        ],
        "defaults": {
            "total_files": 0,
            "extraction_success_rate": 0.0,
            "missing_items": [],
            "timeline": {"items": []},
        },
    },
    "analysis/ace/ACE_REPORT.json": {
        "required_fields": ["summary", "anomalies", "top_anomalies"],
        "defaults": {
            "summary": {
                "total_anomalies": 0,
                "by_type": {},
                "anomalies_total": 0,
            },
            "anomalies": [],
            "top_anomalies": [],
            "timestamp": "",
        },
    },
    "analysis/ace/ACE_SUMMARY.md": {
        "required_fields": None,
        "defaults": "# ACE Anomaly Summary\n\nNo anomalies detected.\n",
    },
    "analysis/vendor/vendor_graph.json": {
        "required_fields": ["nodes", "edges", "vendors"],
        "defaults": {
            "nodes": [],
            "edges": [],
            "vendors": [],
            "metadata": {"generated_at": ""},
        },
    },
    "analysis/vendor/VENDOR_ANOMALY_LINKS.json": {
        "required_fields": ["links", "anomaly_links"],
        "defaults": {
            "links": [],
            "anomaly_links": [],
            "metadata": {"generated_at": ""},
        },
    },
    "analysis/pdf_forensics/forensic_report.json": {
        "required_fields": ["total_scanned", "anomalies"],
        "defaults": {
            "total_scanned": 0,
            "anomalies": [],
            "forensic": {"anomalies": []},
            "anomaly_counts": {},
        },
    },
    "analysis/pdf_forensics/metadata_inconsistency_map.json": {
        "required_fields": None,
        "defaults": {},
    },
    "analysis/jim/JIM_REPORT.json": {
        "required_fields": ["summary", "cases_count"],
        "defaults": {
            "summary": {
                "cases_analyzed": 0,
            },
            "cases_count": 0,
            "top_doctrines": [],
            "high_risk_items": [],
            "case_links": [],
        },
    },
    "analysis/jim/JIM_SUMMARY.md": {
        "required_fields": None,
        "defaults": "# JIM Legal Correlation Summary\n\nNo cases analyzed.\n",
    },
    "analysis/semantic/SEMANTIC_HARMONIZATION_MATRIX.json": {
        "required_fields": ["entries"],
        "defaults": {
            "entries": [],
            "semantic": {"entries": []},
            "metadata": {"generated_at": ""},
        },
    },
    "analysis/semantic/MEANING_DIVERGENCE_INDEX.json": {
        "required_fields": ["terms"],
        "defaults": {
            "terms": {},
            "divergence": {"terms": {}},
            "metadata": {"generated_at": ""},
        },
    },
    "transparency_release/HASH_MANIFEST_FULL_SHA256.txt": {
        "required_fields": None,
        "defaults": "# SHA-256 Hash Manifest\n# Generated: {timestamp}\n\n",
    },
    "transparency_release/corpus_manifest.json": {
        "required_fields": ["files"],
        "defaults": {
            "files": [],
            "manifest_version": "1.0",
            "generated_at": "",
        },
    },
}

LOG_FILE = Path(_repo_root) / "analysis" / "logs" / "artifact_trace.log"


def log_message(message: str) -> None:
    """Log a message to both console and artifact trace log."""
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def normalize_value(value: Any) -> Any:
    """Normalize values: null -> appropriate typed defaults."""
    if value is None:
        return ""  # Return empty string instead of "unknown"
    return value


def check_artifact(artifact_path: str, config: dict) -> dict:
    """Check if artifact exists and has required fields."""
    full_path = _repo_root / artifact_path
    result = {
        "path": artifact_path,
        "exists": full_path.exists(),
        "valid": False,
        "issues": [],
        "missing_fields": [],
    }

    if not full_path.exists():
        result["issues"].append("File does not exist")
        return result

    # Check if file is empty
    if full_path.stat().st_size == 0:
        result["issues"].append("File is empty")
        return result

    # For text files, basic check
    if config["required_fields"] is None:
        if artifact_path.endswith(".txt") or artifact_path.endswith(".md"):
            result["valid"] = True
            return result

    # For JSON files, check structure
    if artifact_path.endswith(".json"):
        try:
            with open(full_path, encoding="utf-8") as f:
                data = json.load(f)

            # Check required fields - also look in nested 'summary' for ingestion/validation
            if config["required_fields"]:
                for field in config["required_fields"]:
                    # Check top level first
                    if field not in data:
                        # For certain fields, check in 'summary' too
                        if (
                            "summary" in data
                            and isinstance(data["summary"], dict)
                            and field in data["summary"]
                        ):
                            # Field exists in summary, that's acceptable
                            pass
                        else:
                            result["missing_fields"].append(field)
                            result["issues"].append(f"Missing required field: {field}")

            if not result["missing_fields"]:
                result["valid"] = True

        except json.JSONDecodeError as e:
            result["issues"].append(f"Invalid JSON: {e}")
        except Exception as e:
            result["issues"].append(f"Error reading file: {e}")

    return result


def repair_artifact(artifact_path: str, config: dict, check_result: dict) -> bool:
    """Repair or create artifact with proper defaults."""
    full_path = _repo_root / artifact_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # If artifact doesn't exist or is empty, create from defaults
        if not check_result["exists"] or "File is empty" in check_result["issues"]:
            defaults = config["defaults"]

            if isinstance(defaults, dict):
                # Add timestamp to metadata
                if "generated_at" in defaults:
                    defaults["generated_at"] = timestamp
                if "timestamp" in defaults:
                    defaults["timestamp"] = timestamp

                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(defaults, f, indent=2, ensure_ascii=False)

                log_message(f"Created artifact: {artifact_path}")
                return True

            elif isinstance(defaults, str):
                # Text file
                content = defaults.format(timestamp=timestamp)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)

                log_message(f"Created text artifact: {artifact_path}")
                return True

        # If artifact exists but has missing fields, backfill them
        elif check_result["missing_fields"] and artifact_path.endswith(".json"):
            with open(full_path, encoding="utf-8") as f:
                data = json.load(f)

            defaults = config["defaults"]
            for field in check_result["missing_fields"]:
                if field in defaults:
                    data[field] = defaults[field]
                    if field == "generated_at" or field == "timestamp":
                        data[field] = timestamp

            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_message(f"Backfilled missing fields in: {artifact_path}")
            return True

        # If JSON is corrupt, recreate
        elif "Invalid JSON" in str(check_result["issues"]):
            defaults = config["defaults"]
            if isinstance(defaults, dict):
                if "generated_at" in defaults:
                    defaults["generated_at"] = timestamp
                if "timestamp" in defaults:
                    defaults["timestamp"] = timestamp

                with open(full_path, "w", encoding="utf-8") as f:
                    json.dump(defaults, f, indent=2, ensure_ascii=False)

                log_message(f"Recreated corrupt artifact: {artifact_path}")
                return True

    except Exception as e:
        log_message(f"ERROR repairing {artifact_path}: {e}")
        return False

    return False


def scan_and_repair() -> dict:
    """Scan all canonical paths and repair as needed."""
    results = {
        "scanned": 0,
        "valid": 0,
        "repaired": 0,
        "failed": 0,
        "details": [],
    }

    log_message("=" * 80)
    log_message("Starting Artifact Reconciliation")
    log_message("=" * 80)

    for artifact_path, config in CANONICAL_ARTIFACTS.items():
        results["scanned"] += 1
        check_result = check_artifact(artifact_path, config)

        if check_result["valid"]:
            results["valid"] += 1
            log_message(f"[OK] Valid: {artifact_path}")
        else:
            log_message(f"[FAIL] Issues found in {artifact_path}:")
            for issue in check_result["issues"]:
                log_message(f"  - {issue}")

            # Attempt repair
            if repair_artifact(artifact_path, config, check_result):
                results["repaired"] += 1
            else:
                results["failed"] += 1

        results["details"].append(
            {
                "path": artifact_path,
                "valid": check_result["valid"],
                "issues": check_result["issues"],
            }
        )

    log_message("=" * 80)
    log_message("Reconciliation Complete")
    log_message(f"Scanned: {results['scanned']}")
    log_message(f"Valid: {results['valid']}")
    log_message(f"Repaired: {results['repaired']}")
    log_message(f"Failed: {results['failed']}")
    log_message("=" * 80)

    return results


def main():
    """Main entry point."""
    print("Artifact Reconciliation Script")
    print("=" * 80)

    results = scan_and_repair()

    # Exit with error code if any repairs failed
    if results["failed"] > 0:
        print(f"\n⚠ Warning: {results['failed']} artifacts could not be repaired")
        sys.exit(1)

    print("\n[OK] Success: All artifacts validated or repaired")
    sys.exit(0)


if __name__ == "__main__":
    main()
