"""run_compliance_check.py — CCOPS compliance check for a jurisdiction.

Usage:
    python scripts/run_compliance_check.py \\
        --config-dir config/ \\
        --source data/sources/ \\
        --output reports/compliance/ \\
        --atlas-data data/reference/atlas_sample.json \\
        --has-ccops-ordinance

What it does:
    1. Load jurisdiction name from --config-dir (optional).
    2. Ingest and analyze all documents from --source directory.
    3. Load Atlas data if --atlas-data provided.
    4. Run ComplianceAssessmentEngine.assess() with all findings.
    5. Write ComplianceScorecard as <jurisdiction>_compliance.json and
       <jurisdiction>_compliance.md to --output directory.
    6. Print a mandate-by-mandate summary to stdout.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: make the src/ package importable when run as a script
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from oraculus_di_auditor.adapters.atlas_adapter import AtlasAdapter  # noqa: E402
from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter  # noqa: E402
from oraculus_di_auditor.adapters.compliance_engine import (  # noqa: E402
    ComplianceAssessmentEngine,
    ComplianceScorecard,
)
from oraculus_di_auditor.analysis import (  # noqa: E402
    detect_administrative_anomalies,
    detect_constitutional_anomalies,
    detect_fiscal_anomalies,
    detect_governance_gap_anomalies,
    detect_procurement_timeline_anomalies,
    detect_signature_anomalies,
    detect_surveillance_anomalies,
)

logger = logging.getLogger("run_compliance_check")

_SINGLE_DOC_DETECTORS = [
    ("fiscal", detect_fiscal_anomalies),
    ("constitutional", detect_constitutional_anomalies),
    ("surveillance", detect_surveillance_anomalies),
    ("signature_chain", detect_signature_anomalies),
    ("governance_gap", detect_governance_gap_anomalies),
    ("administrative_integrity", detect_administrative_anomalies),
]

_INGESTABLE = {".txt", ".json", ".xml", ".pdf"}

_STATUS_ICON = {
    "compliant": "[PASS]",
    "non_compliant": "[FAIL]",
    "partial": "[PART]",
    "unknown": "[----]",
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_compliance_check",
        description="Run a CCOPS compliance check on a jurisdiction's documents.",
    )
    p.add_argument(
        "--config-dir",
        default="config",
        metavar="DIR",
        help="Directory containing jurisdiction config (default: config/)",
    )
    p.add_argument(
        "--source",
        default="data/sources",
        metavar="DIR",
        help="Directory of documents to ingest (default: data/sources/)",
    )
    p.add_argument(
        "--output",
        default="reports/compliance",
        metavar="DIR",
        help="Directory for output files (default: reports/compliance/)",
    )
    p.add_argument(
        "--atlas-data",
        default=None,
        metavar="FILE",
        help="Path to Atlas of Surveillance JSON dataset (optional)",
    )
    p.add_argument(
        "--has-ccops-ordinance",
        action="store_true",
        default=False,
        help="Flag: jurisdiction has adopted a CCOPS ordinance",
    )
    p.add_argument(
        "--jurisdiction",
        default=None,
        metavar="NAME",
        help="Override jurisdiction name (uses config or source dirname if omitted)",
    )
    p.add_argument(
        "--state",
        default=None,
        metavar="ST",
        help="Two-letter state abbreviation for Atlas lookups",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    return p


# ---------------------------------------------------------------------------
# Document helpers
# ---------------------------------------------------------------------------


def _discover_files(source_dir: Path) -> list[Path]:
    """Return all ingestable files under *source_dir*."""
    files = []
    for ext in _INGESTABLE:
        files.extend(source_dir.rglob(f"*{ext}"))
    return sorted(files)


def _read_text(path: Path) -> str:
    """Read file text with UTF-8 fallback to CP1252."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")


def _ingest_file(path: Path) -> dict[str, Any] | None:
    """Return a minimal normalized document dict from *path*, or None on error."""
    try:
        if path.suffix == ".pdf":
            text = _extract_pdf_text(path)
        elif path.suffix == ".json":
            raw = json.loads(_read_text(path))
            text = raw.get("text", json.dumps(raw))
        else:
            text = _read_text(path)

        return {
            "document_id": path.stem,
            "title": path.stem,
            "text": text,
            "source_path": str(path),
            "ingested_at": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:
        logger.warning("Skipping %s: %s", path, exc)
        return None


def _extract_pdf_text(path: Path) -> str:
    """Extract text from a PDF using available libraries."""
    try:
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except ImportError:
        pass
    try:
        import pypdf

        reader = pypdf.PdfReader(str(path))
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except ImportError:
        pass
    return ""


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def _run_detectors(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run all single-document detectors and return flat finding list."""
    findings: list[dict[str, Any]] = []
    for layer, detector_fn in _SINGLE_DOC_DETECTORS:
        try:
            results = detector_fn(doc)
            for r in results:
                r.setdefault("layer", layer)
            findings.extend(results)
        except Exception as exc:
            logger.debug(
                "Detector %s failed on %s: %s", layer, doc.get("document_id"), exc
            )
    return findings


def _run_procurement_cross_doc(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run procurement-timeline cross-document detector."""
    try:
        results = detect_procurement_timeline_anomalies(docs)
        for r in results:
            r.setdefault("layer", "procurement_timeline")
        return results
    except Exception as exc:
        logger.debug("Procurement detector failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def _print_summary(scorecard: ComplianceScorecard) -> None:
    """Print mandate-by-mandate summary to stdout."""
    print(
        f"\n{'=' * 60}\n"
        f"CCOPS Compliance Check: {scorecard.jurisdiction}\n"
        f"{'=' * 60}"
    )
    print(f"Date         : {scorecard.assessment_date}")
    print(f"Has Ordinance: {'Yes' if scorecard.has_ccops_ordinance else 'No'}")
    print(f"Overall Risk : {scorecard.overall_risk.upper()}")
    print(
        f"Score        : {scorecard.compliant_count}/{scorecard.total_mandates} "
        f"({scorecard.compliance_percentage:.1f}%)\n"
    )
    print(f"{'Mandate':<8} {'Status':<10} {'Sev':<9} Title")
    print("-" * 60)
    for ms in scorecard.mandate_statuses:
        icon = _STATUS_ICON.get(ms.status, "[????]")
        print(f"{ms.mandate_id:<8} {icon:<10} {ms.severity:<9} {ms.mandate_title}")
    print()

    if scorecard.recommendations:
        print("Recommendations:")
        for rec in scorecard.recommendations:
            print(f"  * {rec}")
        print()

    if scorecard.technology_inventory:
        n = len(scorecard.technology_inventory)
        print(f"Technology inventory: {n} records loaded.")
        print()


# ---------------------------------------------------------------------------
# Core runner (importable for tests)
# ---------------------------------------------------------------------------


def run_compliance_check(
    source_dir: Path,
    output_dir: Path,
    jurisdiction: str,
    state: str | None = None,
    has_ccops_ordinance: bool = False,
    atlas_data_path: Path | None = None,
) -> ComplianceScorecard:
    """Programmatic entry point for compliance check.

    Args:
        source_dir: Directory containing documents to analyze.
        output_dir: Directory where output files are written.
        jurisdiction: Jurisdiction name for the assessment.
        state: Optional two-letter state code for Atlas lookups.
        has_ccops_ordinance: Whether a CCOPS ordinance is in place.
        atlas_data_path: Optional path to Atlas JSON dataset.

    Returns:
        The completed ``ComplianceScorecard``.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ingest documents
    all_findings: list[dict[str, Any]] = []
    all_docs: list[dict[str, Any]] = []
    ran_detectors: set[str] = set()

    if source_dir.exists():
        files = _discover_files(source_dir)
        logger.info("Ingesting %d files from %s", len(files), source_dir)
        for path in files:
            doc = _ingest_file(path)
            if doc:
                all_docs.append(doc)
                findings = _run_detectors(doc)
                all_findings.extend(findings)
                ran_detectors.update(
                    r.get("layer", "") for r in findings if "layer" in r
                )

        # Cross-document procurement check
        if all_docs:
            proc_findings = _run_procurement_cross_doc(all_docs)
            all_findings.extend(proc_findings)
            if proc_findings:
                ran_detectors.add("procurement_timeline")
    else:
        logger.warning("Source directory not found: %s", source_dir)

    # Mark all single-doc detectors as "ran" so they register as compliant if clean
    for layer, _ in _SINGLE_DOC_DETECTORS:
        if all_docs:
            ran_detectors.add(layer)
    if all_docs:
        ran_detectors.add("procurement_timeline")

    # Build Atlas adapter if path provided
    atlas: AtlasAdapter | None = None
    if atlas_data_path and atlas_data_path.exists():
        atlas = AtlasAdapter(local_dataset_path=atlas_data_path)
        logger.info("Atlas data loaded: %d records", atlas.record_count())

    # Run assessment
    ccops = CCOPSAdapter()
    engine = ComplianceAssessmentEngine(ccops=ccops, atlas=atlas)
    scorecard = engine.assess(
        jurisdiction=jurisdiction,
        analysis_results=all_findings,
        state=state,
        has_ccops_ordinance=has_ccops_ordinance,
        ran_detectors=ran_detectors if ran_detectors else None,
    )

    # Write outputs
    safe_name = jurisdiction.lower().replace(" ", "_")
    json_path = output_dir / f"{safe_name}_compliance.json"
    md_path = output_dir / f"{safe_name}_compliance.md"

    json_path.write_text(
        json.dumps(scorecard.model_dump(), indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(engine.generate_scorecard_markdown(scorecard), encoding="utf-8")
    logger.info("Reports written: %s, %s", json_path, md_path)

    return scorecard


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    source_dir = Path(args.source)
    output_dir = Path(args.output)

    # Determine jurisdiction name
    jurisdiction = args.jurisdiction
    if not jurisdiction:
        try:
            from oraculus_di_auditor.config import load_jurisdiction_config

            cfg = load_jurisdiction_config(args.config_dir)
            jurisdiction = cfg.name
        except Exception:
            jurisdiction = source_dir.name or "unknown"

    atlas_path = Path(args.atlas_data) if args.atlas_data else None

    scorecard = run_compliance_check(
        source_dir=source_dir,
        output_dir=output_dir,
        jurisdiction=jurisdiction,
        state=args.state,
        has_ccops_ordinance=args.has_ccops_ordinance,
        atlas_data_path=atlas_path,
    )

    _print_summary(scorecard)
    return 0 if scorecard.non_compliant_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
