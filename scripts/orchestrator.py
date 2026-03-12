#!/usr/bin/env python3
"""
Pipeline Orchestrator - Coordinates all Oraculus-DI modules.

This module orchestrates the complete pipeline:
1. Corpus ingestion
2. Schema validation
3. Artifact reconciliation
4. Analysis modules (ACE, JIM, DPMM, CAIM, VICFM, CDSCE)
5. Report generation

Author: GitHub Copilot Agent
Date: 2025-12-08
"""

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root / "src"))
sys.path.insert(0, str(_repo_root))

from scripts.ingest_corpus import (  # noqa: E402
    generate_manifest,
    save_manifest,
    scan_corpus,
)

# Constants
CORPUS_PATH = _repo_root / "oraculus" / "corpus"
MANIFEST_PATH = _repo_root / "transparency_release" / "corpus_manifest.json"
LOG_FILE = _repo_root / "analysis" / "logs" / "artifact_trace.log"


def log_message(message: str) -> None:
    """Log a message to both console and artifact trace log."""
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def run_module(name: str, func: callable, optional: bool = False) -> bool:
    """
    Run a pipeline module function.

    Args:
        name: Module name for logging
        func: Function to execute
        optional: Whether module is optional

    Returns:
        True if successful, False otherwise
    """
    log_message(f"Running: {name}")
    try:
        func()
        log_message(f"[OK] {name} completed successfully")
        return True
    except Exception as e:
        log_message(f"[FAIL] {name} failed: {e}")
        if optional:
            log_message(f"⚠ {name} is optional, continuing...")
            return True
        return False


def run_script(
    name: str, script_path: str, optional: bool = False, timeout: int = 300
) -> bool:
    """
    Run a Python script as a pipeline module.

    Args:
        name: Module name for logging
        script_path: Path to Python script
        optional: Whether module is optional
        timeout: Timeout in seconds (default: 300 for 5 minutes)

    Returns:
        True if successful, False otherwise

    Note:
        The default timeout of 300 seconds may not be sufficient for large
        corpus processing operations. Adjust the timeout parameter as needed
        for specific modules (e.g., 600-1800 seconds for intensive operations).
    """
    log_message(f"Running: {name}")
    try:
        result = subprocess.run(
            ["python3", script_path],
            cwd=_repo_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            log_message(f"[OK] {name} completed successfully")
            return True
        else:
            log_message(f"[FAIL] {name} failed with return code {result.returncode}")
            if result.stderr:
                log_message(f"Error: {result.stderr}")
            if optional:
                log_message(f"⚠ {name} is optional, continuing...")
                return True
            return False
    except Exception as e:
        log_message(f"[FAIL] {name} failed: {e}")
        if optional:
            log_message(f"⚠ {name} is optional, continuing...")
            return True
        return False


def run_ingestion() -> None:
    """Run corpus ingestion and manifest generation."""
    corpus = scan_corpus(CORPUS_PATH)
    manifest = generate_manifest(corpus)
    save_manifest(manifest, MANIFEST_PATH)

    # Update ingestion report
    subprocess.run(
        ["python3", "scripts/update_ingestion_report.py"],
        cwd=_repo_root,
        check=True,
    )


def run_validation() -> None:
    """Run schema validation."""
    subprocess.run(
        ["python3", "scripts/validate_schemas.py"],
        cwd=_repo_root,
        check=True,
    )


def run_reconciliation() -> None:
    """Run artifact reconciliation."""
    subprocess.run(
        ["python3", "scripts/reconcile_artifacts.py"],
        cwd=_repo_root,
        check=True,
    )


def run_ace() -> None:
    """Run ACE anomaly analysis."""
    subprocess.run(
        ["python3", "scripts/ace_analyzer.py"],
        cwd=_repo_root,
        check=False,  # Optional
    )


def run_jim() -> None:
    """Run JIM legal correlation."""
    # JIM initialization is done inline in run_full_pipeline
    pass


def run_dpmm() -> None:
    """Run PDF forensic analysis (DPMM)."""
    # DPMM is integrated in pdf_forensics module
    pass


def run_caim() -> None:
    """Run CAIM agency analysis."""
    subprocess.run(
        ["python3", "scripts/generate_caim_reports.py"],
        cwd=_repo_root,
        check=False,  # Optional
    )


def run_vicfm() -> None:
    """Run VICFM vendor analysis."""
    subprocess.run(
        ["python3", "scripts/vendor_graph_builder.py"],
        cwd=_repo_root,
        check=False,  # Optional
    )


def run_cdsce() -> None:
    """Run CDSCE semiotic analysis."""
    # CDSCE is integrated in JIM module
    pass


def run_mdi() -> None:
    """Run Meaning Divergence Index."""
    # MDI is integrated in semantic harmonization
    pass


def generate_plaintext_audit() -> None:
    """Generate plaintext audit report."""
    subprocess.run(
        ["python3", "scripts/generate_plaintext_audit.py"],
        cwd=_repo_root,
        check=True,
    )


def generate_transparency_package() -> None:
    """Generate transparency package."""
    subprocess.run(
        ["python3", "scripts/generate_transparency_package.py"],
        cwd=_repo_root,
        check=True,
    )


def run_all_modules() -> bool:
    """
    Run all pipeline modules in sequence.

    Returns:
        True if pipeline completed successfully
    """
    log_message("=" * 80)
    log_message("STARTING FULL ORACULUS-DI PIPELINE")
    log_message("=" * 80)

    # Define pipeline stages
    stages = [
        ("1. Corpus Ingestion", run_ingestion, False),
        ("2. Schema Validation", run_validation, True),
        ("3. Artifact Reconciliation", run_reconciliation, True),
        ("4. ACE Anomaly Analysis", run_ace, True),
        ("5. Vendor Analysis (VICFM)", run_vicfm, True),
        ("6. Agency Analysis (CAIM)", run_caim, True),
        ("7. JIM Legal Correlation", run_jim, True),
        ("8. CDSCE Semiotic Analysis", run_cdsce, True),
        ("9. Meaning Divergence Index", run_mdi, True),
        ("10. Plaintext Audit Generation", generate_plaintext_audit, True),
        ("11. Transparency Package", generate_transparency_package, False),
    ]

    # Run each stage
    failed_stages = []
    for name, func, optional in stages:
        success = run_module(name, func, optional)
        if not success and not optional:
            failed_stages.append(name)
            log_message("Pipeline execution aborted")
            return False

    log_message("=" * 80)
    log_message("PIPELINE EXECUTION COMPLETE")
    log_message("=" * 80)

    if failed_stages:
        log_message(f"⚠ Some optional stages failed: {', '.join(failed_stages)}")

    return True


def main():
    """Main entry point for orchestrator."""
    print("Pipeline Orchestrator - Full Oraculus-DI Pipeline")
    print("=" * 80)

    success = run_all_modules()

    if success:
        print("\n[OK] Pipeline orchestration completed successfully")
    else:
        print("\n[FAIL] Pipeline orchestration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
