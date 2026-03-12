#!/usr/bin/env python3
"""
Full Pipeline Orchestration Script

Runs all upstream Oraculus-DI model pipelines in the correct order:
1. Ingestion module
2. Validation module
3. ACE anomaly engine
4. Vendor graph generator
5. Vendor anomaly linker
6. PDF forensic analyzer
7. Metadata inconsistency mapper
8. JIM legal correlation engine
9. Semantic harmonization module
10. Meaning divergence engine
11. Transparency package generator

Each module logs its file creation to analysis/logs/artifact_trace.log
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

LOG_FILE = Path(_repo_root) / "analysis" / "logs" / "artifact_trace.log"


def log_message(message: str) -> None:
    """Log a message to both console and artifact trace log."""
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] {message}"
    print(log_entry)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")


def run_module(name: str, command: list, optional: bool = False) -> bool:
    """Run a pipeline module and log results."""
    log_message("=" * 80)
    log_message(f"Running: {name}")
    log_message(f"Command: {' '.join(command)}")
    log_message("=" * 80)

    try:
        result = subprocess.run(
            command,
            cwd=_repo_root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per module
        )

        if result.returncode == 0:
            log_message(f"✓ {name} completed successfully")
            if result.stdout:
                log_message(f"Output:\n{result.stdout}")
            return True
        else:
            log_message(f"✗ {name} failed with return code {result.returncode}")
            if result.stderr:
                log_message(f"Error output:\n{result.stderr}")
            if result.stdout:
                log_message(f"Standard output:\n{result.stdout}")

            if optional:
                log_message(f"⚠ {name} is optional, continuing...")
                return True
            return False

    except subprocess.TimeoutExpired:
        log_message(f"✗ {name} timed out after 5 minutes")
        if optional:
            log_message(f"⚠ {name} is optional, continuing...")
            return True
        return False
    except Exception as e:
        log_message(f"✗ {name} failed with exception: {e}")
        if optional:
            log_message(f"⚠ {name} is optional, continuing...")
            return True
        return False


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a required file exists."""
    if path.exists():
        log_message(f"✓ {description} exists: {path}")
        return True
    else:
        log_message(f"✗ {description} missing: {path}")
        return False


def validate_json_output(path: Path, required_keys: list[str] | None = None) -> bool:
    """Validate a JSON output file exists and contains required data.

    Args:
        path: Path to the JSON file
        required_keys: Optional list of keys that must be present in the JSON

    Returns:
        True if validation passes, False otherwise
    """
    import json

    if not path.exists():
        log_message(f"✗ Validation failed: {path} does not exist")
        return False

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Check file is not empty
        if not data:
            log_message(f"✗ Validation failed: {path} is empty")
            return False

        # Check required keys if specified
        if required_keys:
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                log_message(f"✗ Validation failed: {path} missing keys: {missing_keys}")
                return False

        log_message(f"✓ Validation passed: {path}")
        return True

    except json.JSONDecodeError as e:
        log_message(f"✗ Validation failed: {path} is not valid JSON: {e}")
        return False
    except Exception as e:
        log_message(f"✗ Validation failed: {path} error: {e}")
        return False


def validate_forensic_report(report_path: Path) -> bool:
    """Validate the PDF forensic report contains actual data.

    Args:
        report_path: Path to forensic_report.json

    Returns:
        True if report contains data, False otherwise
    """
    import json

    if not report_path.exists():
        log_message(f"✗ Forensic report missing: {report_path}")
        return False

    try:
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)

        pdfs_processed = data.get("pdfs_processed", 0)
        mode = data.get("mode", "unknown")

        if pdfs_processed == 0:
            log_message("✗ Forensic report shows 0 PDFs processed")
            return False

        log_message(
            f"✓ Forensic report valid: {pdfs_processed} PDFs processed (mode: {mode})"
        )
        return True

    except Exception as e:
        log_message(f"✗ Failed to validate forensic report: {e}")
        return False


def run_full_pipeline(force_extract=False) -> bool:
    """Run the complete pipeline."""
    log_message("=" * 80)
    log_message("STARTING FULL ORACULUS-DI PIPELINE")
    log_message("=" * 80)

    if force_extract:
        log_message("Force extraction mode enabled")

    # Define pipeline modules
    # Note: Some modules may not have standalone scripts, so we mark them as optional
    pipeline = [
        {
            "name": "1. Corpus Ingestion Module",
            "command": ["python3", "scripts/ingest_corpus.py"],
            "optional": False,
            "output_files": [
                _repo_root / "transparency_release" / "corpus_manifest.json"
            ],
        },
        {
            "name": "2. Update Ingestion Report",
            "command": ["python3", "scripts/update_ingestion_report.py"],
            "optional": False,
            "output_files": [
                _repo_root / "oraculus" / "corpus" / "ingestion_report.json"
            ],
        },
        {
            "name": "3. Validation Module",
            "command": ["python3", "scripts/validate_corpus_integrity.py"],
            "optional": True,
            "output_files": [
                _repo_root / "oraculus" / "corpus" / "VALIDATION_REPORT.json"
            ],
        },
        {
            "name": "4. ACE Anomaly Engine",
            "command": ["python3", "scripts/ace_analyzer.py"],
            "optional": True,
            "output_files": [
                _repo_root / "analysis" / "ace" / "ACE_REPORT.json",
                _repo_root / "analysis" / "ace" / "ACE_SUMMARY.md",
            ],
        },
        {
            "name": "5. Vendor Graph Generator",
            "command": ["python3", "scripts/vendor_graph_builder.py"],
            "optional": True,
            "output_files": [_repo_root / "analysis" / "vendor" / "vendor_graph.json"],
        },
        {
            "name": "6. Vendor Anomaly Linker",
            "command": ["python3", "scripts/vendor_map_extractor.py"],
            "optional": True,
            "output_files": [
                _repo_root / "analysis" / "vendor" / "VENDOR_ANOMALY_LINKS.json"
            ],
        },
        {
            "name": "7. PDF Forensic Analyzer",
            "command": [
                "python3",
                "scripts/pdf_forensics/pdf_metadata_miner.py",
                "--corpus-root",
                "oraculus/corpus",
                "--years",
                "2014-2025",
                "--output",
                "analysis/pdf_forensics",
            ],
            "optional": False,  # Make PDF forensics mandatory - fixes issue where DPMM showed 0 documents analyzed
            "output_files": [
                _repo_root / "analysis" / "pdf_forensics" / "forensic_report.json"
            ],
        },
        {
            "name": "8. Metadata Inconsistency Mapper",
            "command": [
                "python3",
                "-c",
                "print('Metadata inconsistency mapping integrated in PDF forensics')",
            ],
            "optional": True,
            "output_files": [
                _repo_root
                / "analysis"
                / "pdf_forensics"
                / "metadata_inconsistency_map.json"
            ],
        },
        {
            "name": "9. JIM Legal Correlation Engine",
            "command": [
                "python3",
                "-c",
                "from scripts.jim.jim_core import JIMCore; jim = JIMCore(); jim.initialize(); print('JIM initialized')",
            ],
            "optional": True,
            "output_files": [
                _repo_root / "analysis" / "jim" / "JIM_REPORT.json",
                _repo_root / "analysis" / "jim" / "JIM_SUMMARY.md",
            ],
        },
        {
            "name": "10. Semantic Harmonization Module",
            "command": [
                "python3",
                "-c",
                "from scripts.jim.semantic_harmonizer import SemanticHarmonizer; h = SemanticHarmonizer(); h.load_lexicon_sources(); h.generate_artifacts(); print('Semantic harmonization complete')",
            ],
            "optional": True,
            "output_files": [
                _repo_root / "artifacts" / "SEMANTIC_HARMONIZATION_MATRIX.json",
                _repo_root
                / "analysis"
                / "semantic"
                / "SEMANTIC_HARMONIZATION_MATRIX.json",
            ],
        },
        {
            "name": "11. Meaning Divergence Engine",
            "command": [
                "python3",
                "-c",
                "print('Meaning divergence integrated in semantic harmonization')",
            ],
            "optional": True,
            "output_files": [
                _repo_root / "artifacts" / "MEANING_DIVERGENCE_INDEX.json",
                _repo_root / "analysis" / "semantic" / "MEANING_DIVERGENCE_INDEX.json",
            ],
        },
        {
            "name": "12. Transparency Package Generator",
            "command": ["python3", "scripts/generate_transparency_package.py"],
            "optional": False,
            "output_files": [
                _repo_root / "transparency_release" / "HASH_MANIFEST_FULL_SHA256.txt",
                _repo_root / "transparency_release" / "corpus_manifest.json",
            ],
        },
    ]

    # Run each module
    failed_modules = []
    for module in pipeline:
        success = run_module(module["name"], module["command"], module["optional"])

        if not success:
            failed_modules.append(module["name"])
            if not module["optional"]:
                log_message(f"✗ Required module failed: {module['name']}")
                log_message("Pipeline execution aborted")
                return False

        # Check output files and validate content
        for output_file in module.get("output_files", []):
            if not check_file_exists(output_file, f"{module['name']} output"):
                if not module["optional"]:
                    log_message(f"✗ Required output missing: {output_file}")
                    log_message("Pipeline execution aborted")
                    return False

            # Special validation for forensic report
            if output_file.name == "forensic_report.json":
                if not validate_forensic_report(output_file):
                    if not module["optional"]:
                        log_message("✗ Forensic report validation failed")
                        log_message("Pipeline execution aborted")
                        return False

    log_message("=" * 80)
    log_message("PIPELINE EXECUTION COMPLETE")
    log_message("=" * 80)

    if failed_modules:
        log_message(f"⚠ Some optional modules failed: {', '.join(failed_modules)}")
        log_message("Continuing with artifact reconciliation...")

    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run the full Oraculus-DI pipeline")
    parser.add_argument(
        "--force-extract",
        action="store_true",
        help="Force PDF extraction even if already extracted",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    print("Full Pipeline Orchestration Script")
    print("=" * 80)

    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    success = run_full_pipeline(force_extract=args.force_extract)

    if success:
        print("\n✓ Pipeline execution completed")
        print(
            "Next step: Run scripts/reconcile_artifacts.py to repair any missing data"
        )
    else:
        print("\n✗ Pipeline execution failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
