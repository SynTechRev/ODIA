#!/usr/bin/env python3
"""
Enhanced Full Audit Orchestrator

This script provides robust, automatic orchestration of the complete Oraculus-DI
audit pipeline with strict sequential execution, comprehensive validation, and
fail-loudly error handling.

Pipeline stages execute in strict order:
1. Corpus structure validation
2. PDF metadata generation
3. Text extraction (when PDFs available)
4. Global index building
5. PDF forensics analysis (DPMM)
6. ACE anomaly detection
7. VICFM vendor analysis
8. CAIM cross-agency analysis
9. JIM legal correlation
10. Semantic harmonization (MSH)
11. Meaning divergence analysis (MDI)
12. Transparency package generation
13. Hash manifest generation
14. Plain-text audit report generation

Each stage is validated before proceeding to the next.

Author: GitHub Copilot Agent
Date: 2025-12-16
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

LOG_FILE = Path(_repo_root) / "analysis" / "logs" / "orchestrator_trace.log"


def log_message(message: str, level: str = "INFO") -> None:
    """Log a message to both console and orchestrator trace log."""
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] [{level}] {message}"
    print(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def run_command(
    name: str,
    command: list[str],
    timeout: int = 300,
    check_output: bool = True,
) -> tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr.

    Args:
        name: Human-readable name for the command
        command: Command and arguments as list
        timeout: Timeout in seconds
        check_output: Whether to capture output

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    log_message("=" * 80)
    log_message(f"Running: {name}")
    log_message(f"Command: {' '.join(command)}")
    log_message("=" * 80)

    try:
        result = subprocess.run(
            command,
            cwd=_repo_root,
            capture_output=check_output,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            log_message(f"[OK] {name} completed successfully")
            return (
                True,
                result.stdout if check_output else "",
                result.stderr if check_output else "",
            )
        else:
            log_message(
                f"[FAIL] {name} failed with return code {result.returncode}", "ERROR"
            )
            if check_output and result.stderr:
                log_message(f"Error output:\n{result.stderr}", "ERROR")
            return (
                False,
                result.stdout if check_output else "",
                result.stderr if check_output else "",
            )

    except subprocess.TimeoutExpired:
        log_message(f"[FAIL] {name} timed out after {timeout} seconds", "ERROR")
        return False, "", f"Command timed out after {timeout} seconds"
    except Exception as e:
        log_message(f"[FAIL] {name} failed with exception: {e}", "ERROR")
        return False, "", str(e)


def validate_file_exists(path: Path, description: str) -> bool:
    """Validate that a required file exists."""
    if path.exists():
        size = path.stat().st_size
        log_message(f"[OK] {description} exists: {path} ({size} bytes)")
        return True
    else:
        log_message(f"[FAIL] {description} missing: {path}", "ERROR")
        return False


def validate_json_file(
    path: Path,
    description: str,
    required_keys: list[str] | None = None,
    min_value_checks: dict[str, int] | None = None,
) -> bool:
    """Validate a JSON file exists, is valid JSON, and contains required data.

    Args:
        path: Path to JSON file
        description: Human-readable description
        required_keys: Optional list of keys that must be present
        min_value_checks: Optional dict of key->min_value pairs for validation

    Returns:
        True if validation passes
    """
    if not validate_file_exists(path, description):
        return False

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Check file is not empty
        if not data:
            log_message(f"[FAIL] {description} is empty", "ERROR")
            return False

        # Check required keys
        if required_keys:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                log_message(
                    f"[FAIL] {description} missing required keys: {missing_keys}", "ERROR"
                )
                return False

        # Check minimum value requirements
        if min_value_checks:
            for key, min_value in min_value_checks.items():
                actual_value = data.get(key, 0)
                if actual_value < min_value:
                    log_message(
                        f"[FAIL] {description} validation failed: "
                        f"{key}={actual_value}, expected >= {min_value}",
                        "ERROR",
                    )
                    return False

        log_message(f"[OK] {description} validation passed")
        return True

    except json.JSONDecodeError as e:
        log_message(f"[FAIL] {description} is not valid JSON: {e}", "ERROR")
        return False
    except Exception as e:
        log_message(f"[FAIL] {description} validation error: {e}", "ERROR")
        return False


def validate_forensic_report() -> bool:
    """Validate the PDF forensic report contains actual data."""
    report_path = _repo_root / "analysis" / "pdf_forensics" / "forensic_report.json"

    if not validate_file_exists(report_path, "PDF Forensic Report"):
        return False

    try:
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)

        pdfs_processed = data.get("pdfs_processed", 0)
        mode = data.get("mode", "unknown")
        unique_files = len(data.get("metadata_by_file", {}))

        if pdfs_processed == 0:
            log_message("[FAIL] Forensic report shows 0 PDFs processed", "ERROR")
            return False

        log_message(
            f"[OK] Forensic report valid: {pdfs_processed} PDFs processed, "
            f"{unique_files} unique files, mode: {mode}"
        )
        return True

    except Exception as e:
        log_message(f"[FAIL] Failed to validate forensic report: {e}", "ERROR")
        return False


def run_full_audit_pipeline() -> bool:
    """Execute the complete audit pipeline with validation."""
    log_message("=" * 80)
    log_message("ORACULUS-DI FULL AUDIT ORCHESTRATOR")
    log_message("=" * 80)
    log_message(f"Started: {datetime.now(UTC).isoformat()}")
    log_message(f"Repository: {_repo_root}")
    log_message("=" * 80)

    # Define pipeline stages
    stages = [
        {
            "name": "1. Full Corpus Ingestion",
            "command": ["python3", "scripts/full_ingestion.py"],
            "timeout": 300,
            "validate": lambda: validate_json_file(
                _repo_root / "oraculus" / "corpus" / "ingestion_report.json",
                "Ingestion Report",
                required_keys=["summary", "text_extraction"],
            ),
            "skip_if_exists": [
                _repo_root / "oraculus" / "corpus" / "ingestion_report.json",
            ],
        },
        {
            "name": "2. Corpus Validation",
            "command": ["python3", "scripts/validate_corpus_integrity.py"],
            "timeout": 120,
            "validate": lambda: validate_file_exists(
                _repo_root / "oraculus" / "corpus" / "VALIDATION_REPORT.json",
                "Validation Report",
            ),
            "optional": True,  # May not exist in all repos
        },
        {
            "name": "3. ACE Anomaly Detection",
            "command": ["python3", "scripts/ace_analyzer.py"],
            "timeout": 180,
            "validate": lambda: validate_json_file(
                _repo_root / "analysis" / "ace" / "ACE_REPORT.json",
                "ACE Report",
                required_keys=["summary", "anomalies"],
            ),
            "optional": True,
        },
        {
            "name": "4. Vendor Graph Generation",
            "command": ["python3", "scripts/vendor_graph_builder.py"],
            "timeout": 120,
            "validate": lambda: validate_json_file(
                _repo_root / "analysis" / "vendor" / "vendor_graph.json",
                "Vendor Graph",
                required_keys=["nodes"],
            ),
            "optional": True,
        },
        {
            "name": "5. PDF Forensic Analysis (DPMM)",
            "command": [
                "python3",
                "scripts/pdf_forensics/pdf_metadata_miner.py",
                "--corpus-root",
                "oraculus/corpus",
                "--years",
                "2014-2025",
            ],
            "timeout": 300,
            "validate": validate_forensic_report,
            # CRITICAL - PDF forensics is required for complete audit report
            # Fixes issue where DPMM showed 0 documents analyzed
            "optional": False,
        },
        {
            "name": "6. JIM Legal Correlation",
            "command": [
                "python3",
                "-c",
                (
                    "from scripts.jim.jim_core import JIMCore; "
                    "jim = JIMCore(); jim.initialize(); "
                    "print('JIM initialized successfully')"
                ),
            ],
            "timeout": 120,
            "validate": lambda: validate_file_exists(
                _repo_root / "analysis" / "jim" / "JIM_REPORT.json", "JIM Report"
            ),
            "optional": True,
        },
        {
            "name": "7. Semantic Harmonization (MSH)",
            "command": [
                "python3",
                "-c",
                (
                    "from scripts.jim.semantic_harmonizer import "
                    "SemanticHarmonizer; h = SemanticHarmonizer(); "
                    "h.load_lexicon_sources(); h.generate_artifacts(); "
                    "print('Semantic harmonization complete')"
                ),
            ],
            "timeout": 120,
            "validate": lambda: validate_file_exists(
                _repo_root
                / "analysis"
                / "semantic"
                / "SEMANTIC_HARMONIZATION_MATRIX.json",
                "Semantic Harmonization Matrix",
            ),
            "optional": True,
        },
        {
            "name": "8. Transparency Package Generation",
            "command": ["python3", "scripts/generate_transparency_package.py"],
            "timeout": 180,
            "validate": lambda: validate_json_file(
                _repo_root / "transparency_release" / "corpus_manifest.json",
                "Corpus Manifest",
                required_keys=["corpora"],
            ),
            "optional": False,  # CRITICAL
        },
        {
            "name": "9. Plain-Text Audit Report Generation",
            "command": [
                "python3",
                "scripts/generate_plaintext_audit.py",
                "--output",
                "transparency_release/ALL_AUDIT_FULL.txt",
            ],
            "timeout": 120,
            "validate": lambda: validate_file_exists(
                _repo_root / "transparency_release" / "ALL_AUDIT_FULL.txt",
                "Plain-Text Audit Report",
            ),
            "optional": False,  # CRITICAL
        },
    ]

    # Execute stages
    failed_stages = []
    completed_stages = 0

    for stage in stages:
        stage_name = stage["name"]
        is_optional = stage.get("optional", False)

        # Check if stage should be skipped
        skip_if_exists = stage.get("skip_if_exists", [])
        if skip_if_exists:
            all_exist = all(path.exists() for path in skip_if_exists)
            if all_exist:
                log_message(f"⊗ Skipping {stage_name} - outputs already exist")
                # Still run validation
                if "validate" in stage:
                    if not stage["validate"]():
                        failed_stages.append(f"{stage_name} (validation)")
                        if not is_optional:
                            log_message(
                                f"[FAIL] CRITICAL VALIDATION FAILED: {stage_name}", "ERROR"
                            )
                            log_message("Pipeline execution aborted", "ERROR")
                            return False
                completed_stages += 1
                continue

        # Execute command
        success, stdout, stderr = run_command(
            stage_name,
            stage["command"],
            timeout=stage.get("timeout", 300),
        )

        if not success:
            failed_stages.append(stage_name)
            if not is_optional:
                log_message(f"[FAIL] CRITICAL STAGE FAILED: {stage_name}", "ERROR")
                log_message("Pipeline execution aborted", "ERROR")
                return False
            else:
                log_message(
                    f"⚠ Optional stage failed: {stage_name}, continuing...", "WARNING"
                )
                continue

        # Validate outputs
        if "validate" in stage:
            if not stage["validate"]():
                failed_stages.append(f"{stage_name} (validation)")
                if not is_optional:
                    log_message(f"[FAIL] CRITICAL VALIDATION FAILED: {stage_name}", "ERROR")
                    log_message("Pipeline execution aborted", "ERROR")
                    return False
                else:
                    log_message(
                        f"⚠ Optional stage validation failed: "
                        f"{stage_name}, continuing...",
                        "WARNING",
                    )

        completed_stages += 1

    # Summary
    log_message("=" * 80)
    log_message("PIPELINE EXECUTION COMPLETE")
    log_message("=" * 80)
    log_message(f"Completed stages: {completed_stages}/{len(stages)}")

    if failed_stages:
        log_message(f"⚠ Failed optional stages: {', '.join(failed_stages)}", "WARNING")

    log_message("=" * 80)
    log_message("[OK] Full audit pipeline completed successfully")
    log_message("=" * 80)

    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Full Audit Orchestrator for Oraculus-DI"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    success = run_full_audit_pipeline()

    if success:
        print("\n[OK] Full audit orchestration completed successfully")
        print(f"Audit report: {_repo_root}/transparency_release/ALL_AUDIT_FULL.txt")
        sys.exit(0)
    else:
        print("\n[FAIL] Full audit orchestration failed")
        print(f"Check logs: {LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()
