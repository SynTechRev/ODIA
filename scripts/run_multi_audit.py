"""run_multi_audit.py — CLI entry point for multi-jurisdiction analysis.

Usage:
    python scripts/run_multi_audit.py \\
        --config-dir config/multi_jurisdiction/ \\
        --source-dir data/multi_jurisdiction/ \\
        --output reports/multi_jurisdiction/ \\
        --verbose

    # Analyze specific jurisdictions only:
    python scripts/run_multi_audit.py \\
        --config-dir config/multi_jurisdiction/ \\
        --source-dir data/multi_jurisdiction/ \\
        --output reports/multi_jurisdiction/ \\
        --jurisdictions example_city_a,example_city_b

What it does:
    1. Load all jurisdiction configs from --config-dir using
       JurisdictionRegistry.from_directory()
    2. For each jurisdiction, discover and ingest documents from
       --source-dir/{jurisdiction_id}/
    3. Run MultiJurisdictionRunner.analyze_all()
    4. Run CrossJurisdictionPatternDetector.detect_all_patterns()
    5. Generate JSON and Markdown reports with ComparativeReportGenerator
    6. Write reports to --output directory
    7. Print a summary to stdout
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
# Bootstrap: make src/ importable when run as a script
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from oraculus_di_auditor.multi_jurisdiction.pattern_detector import (  # noqa: E402
    CrossJurisdictionPatternDetector,
)
from oraculus_di_auditor.multi_jurisdiction.registry import (  # noqa: E402
    JurisdictionRegistry,
)
from oraculus_di_auditor.multi_jurisdiction.report_generator import (  # noqa: E402
    ComparativeReportGenerator,
)
from oraculus_di_auditor.multi_jurisdiction.runner import (  # noqa: E402
    MultiJurisdictionRunner,
)

logger = logging.getLogger("run_multi_audit")

_INGESTABLE_EXTS = {".txt", ".json", ".xml", ".pdf"}


# ---------------------------------------------------------------------------
# Document ingestion helpers
# ---------------------------------------------------------------------------


def _discover_files(source_dir: Path) -> list[Path]:
    """Return all ingestable files under source_dir, sorted by name."""
    return sorted(
        f
        for f in source_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in _INGESTABLE_EXTS
    )


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")


def _extract_pdf_text(path: Path) -> str | None:
    for mod_name in ("pdfplumber", "pypdf", "PyPDF2"):
        try:
            if mod_name == "pdfplumber":
                import pdfplumber  # type: ignore[import]

                with pdfplumber.open(path) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            mod = __import__(mod_name)
            reader = mod.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            continue
        except Exception as exc:  # noqa: BLE001
            logger.warning("PDF extraction failed for %s: %s", path.name, exc)
            return None
    logger.warning("Skipping %s — no PDF library available", path.name)
    return None


def _ingest_file(path: Path) -> dict[str, Any] | None:
    """Read a file and return a {document_text, metadata} dict for the runner."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".txt":
            text = _read_text(path)
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            # If JSON is already a normalized doc, extract raw_text
            if isinstance(data, dict) and "raw_text" in data:
                text = data["raw_text"]
            else:
                text = json.dumps(data, ensure_ascii=False)
        elif suffix == ".xml":
            text = _read_text(path)
        elif suffix == ".pdf":
            text = _extract_pdf_text(path)
            if text is None:
                return None
        else:
            return None

        return {
            "document_text": text,
            "metadata": {
                "document_id": path.stem,
                "title": path.stem.replace("_", " ").replace("-", " ").title(),
                "source_path": str(path),
            },
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to ingest %s: %s", path.name, exc)
        return None


def _load_documents_for_jurisdiction(
    source_dir: Path,
    jurisdiction_id: str,
    verbose: bool,
) -> list[dict[str, Any]]:
    """Discover and ingest all documents for one jurisdiction."""
    jdir = source_dir / jurisdiction_id
    if not jdir.exists():
        if verbose:
            print(
                f"  [WARN] Source directory not found for {jurisdiction_id!r}: "
                f"{jdir} — skipping."
            )
        return []

    files = _discover_files(jdir)
    if verbose:
        print(f"  {jurisdiction_id}: found {len(files)} file(s) in {jdir}")

    docs: list[dict[str, Any]] = []
    for f in files:
        doc = _ingest_file(f)
        if doc is not None:
            docs.append(doc)
            if verbose:
                print(f"    [OK] {f.name}")
        elif verbose:
            print(f"    [FAIL] {f.name}")
    return docs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_multi_audit",
        description="Run a multi-jurisdiction comparative audit.",
    )
    p.add_argument(
        "--config-dir",
        required=True,
        metavar="DIR",
        help="Directory with per-jurisdiction config subdirectories",
    )
    p.add_argument(
        "--source-dir",
        required=True,
        metavar="DIR",
        help="Directory with per-jurisdiction document subdirectories",
    )
    p.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Output directory for reports",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress details",
    )
    p.add_argument(
        "--jurisdictions",
        default="",
        metavar="IDS",
        help="Comma-separated jurisdiction IDs to analyze (default: all in config-dir)",
    )
    p.add_argument(
        "--formats",
        default="json,markdown",
        metavar="LIST",
        help="Comma-separated output formats: json,markdown,html,pdf,docx"
        " (default: json,markdown)",
    )
    p.add_argument(
        "--executive",
        action="store_true",
        help="Also generate an executive summary using audit_report_executive.md",
    )
    return p


def _print_summary(
    runner_results: dict[str, dict[str, Any]],
    patterns: dict[str, Any],
    output_dir: Path,
) -> None:
    total_docs = sum(v.get("document_count", 0) for v in runner_results.values())
    total_anomalies = sum(
        v.get("anomaly_summary", {}).get("total", 0) for v in runner_results.values()
    )
    pcount = patterns.get("patterns_detected", 0)

    print("\n" + "=" * 60)
    print("Multi-Jurisdiction Audit Complete")
    print("=" * 60)
    print(f"  Jurisdictions analyzed : {len(runner_results)}")
    print(f"  Total documents        : {total_docs}")
    print(f"  Total anomalies        : {total_anomalies}")
    print(f"  Cross-jurisdiction     : {pcount} pattern(s) detected")
    print(f"  Output directory       : {output_dir.resolve()}")
    print("=" * 60)

    for jid, jdata in runner_results.items():
        asummary = jdata.get("anomaly_summary", {})
        by_sev = asummary.get("by_severity", {})
        parts = ", ".join(
            f"{sev}={by_sev.get(sev, 0)}"
            for sev in ("critical", "high", "medium", "low")
            if by_sev.get(sev, 0) > 0
        )
        print(
            f"  {jid:30s}  docs={jdata.get('document_count', 0):3d}"
            f"  anomalies={asummary.get('total', 0):3d}"
            + (f"  [{parts}]" if parts else "")
        )
    print()


def run(args: argparse.Namespace) -> int:  # noqa: C901
    """Execute the multi-jurisdiction audit pipeline. Returns exit code."""
    config_dir = Path(args.config_dir)
    source_dir = Path(args.source_dir)
    output_dir = Path(args.output)
    verbose = args.verbose
    formats_raw = getattr(args, "formats", "json,markdown")
    formats = [f.strip() for f in formats_raw.split(",") if f.strip()]
    executive = getattr(args, "executive", False)

    # --- 1. Load registry ---
    if verbose:
        print(f"Loading jurisdiction configs from: {config_dir}")
    try:
        registry = JurisdictionRegistry.from_directory(config_dir)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if registry.count() == 0:
        print("[ERROR] No jurisdiction configs found in config-dir.", file=sys.stderr)
        return 1

    # Apply --jurisdictions filter
    jids_all = registry.list_jurisdictions()
    if args.jurisdictions:
        wanted = {j.strip() for j in args.jurisdictions.split(",") if j.strip()}
        unknown = wanted - set(jids_all)
        if unknown:
            print(
                "[WARN] Unknown jurisdiction IDs (ignored): "
                + ", ".join(sorted(unknown)),
                file=sys.stderr,
            )
        jids_to_run = [j for j in jids_all if j in wanted]
        if not jids_to_run:
            print("[ERROR] No valid jurisdiction IDs after filtering.", file=sys.stderr)
            return 1
        # Build a filtered registry
        filtered = JurisdictionRegistry()
        for jid in jids_to_run:
            filtered.register(jid, registry.get(jid))
        registry = filtered
    else:
        jids_to_run = jids_all

    if verbose:
        print(f"Jurisdictions to analyze: {', '.join(jids_to_run)}")

    # --- 2. Ingest documents per jurisdiction ---
    if verbose and not source_dir.exists():
        print(
            f"[WARN] Source directory does not exist: {source_dir} "
            "— all jurisdictions will have 0 documents."
        )

    documents_by_jurisdiction: dict[str, list[dict[str, Any]]] = {}
    for jid in jids_to_run:
        documents_by_jurisdiction[jid] = _load_documents_for_jurisdiction(
            source_dir, jid, verbose
        )

    # --- 3. Run analysis ---
    if verbose:
        print("\nRunning analysis...")
    runner = MultiJurisdictionRunner(registry)
    runner.analyze_all(documents_by_jurisdiction)
    runner_results = runner.get_all_results()

    # --- 4. Pattern detection ---
    if verbose:
        print("Detecting cross-jurisdiction patterns...")
    detector = CrossJurisdictionPatternDetector(runner_results)
    patterns = detector.detect_all_patterns()

    # --- 5. Generate reports ---
    if verbose:
        print("Generating reports...")
    gen = ComparativeReportGenerator(runner_results, patterns)
    json_report = gen.generate_json_report()

    # --- 6. Write output ---
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    json_path = output_dir / f"multi_audit_{ts}.json"
    md_path = output_dir / f"multi_audit_{ts}.md"

    # Always write JSON (backward-compat: preserves report_type, jurisdictions,
    # risk_ranking)
    json_path.write_text(
        json.dumps(json_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if verbose:
        print(f"  JSON report: {json_path}")

    # Build AuditReport wrapper so the template engine can render markdown
    _repo_root = Path(__file__).resolve().parent.parent
    _template_dir = _repo_root / "templates"
    try:
        from oraculus_di_auditor.reporting import AuditReport, ReportTemplateEngine
        from oraculus_di_auditor.reporting.format_converters import (
            markdown_to_docx,
            markdown_to_html,
            markdown_to_pdf,
        )

        # Wrap ComparativeReportGenerator JSON into an AuditReport for templating
        audit_report = AuditReport(
            report_id=json_report.get("report_id", f"MULTI-{ts}"),
            report_type=json_report.get("report_type", "multi_jurisdiction"),
            generated_at=json_report.get("generated_at", datetime.now(UTC).isoformat()),
            title="Multi-Jurisdiction Comparative Audit Report",
            executive_summary=(
                f"Analysis of {len(runner_results)} jurisdiction(s) complete. "
                f"See comparison matrix and cross-jurisdiction patterns below."
            ),
            metadata={
                "jurisdictions": list(runner_results.keys()),
                "jurisdiction_count": len(runner_results),
                "cross_jurisdiction_patterns": json_report.get(
                    "cross_jurisdiction_patterns", []
                ),
                "risk_ranking": json_report.get("risk_ranking", []),
            },
        )
        engine = ReportTemplateEngine(template_dir=_template_dir)
        md_content: str | None = None

        for fmt in formats:
            if fmt == "markdown":
                if md_content is None:
                    md_content = engine.render_markdown(
                        audit_report, template_name="multi_jurisdiction_report.md"
                    )
                md_path.write_text(md_content, encoding="utf-8")
                if verbose:
                    print(f"  Markdown report: {md_path}")
            elif fmt == "html":
                if md_content is None:
                    md_content = engine.render_markdown(
                        audit_report, template_name="multi_jurisdiction_report.md"
                    )
                html_path = output_dir / f"multi_audit_{ts}.html"
                html_path.write_text(markdown_to_html(md_content), encoding="utf-8")
                if verbose:
                    print(f"  HTML report: {html_path}")
            elif fmt == "pdf":
                if md_content is None:
                    md_content = engine.render_markdown(
                        audit_report, template_name="multi_jurisdiction_report.md"
                    )
                pdf_path = output_dir / f"multi_audit_{ts}.pdf"
                result = markdown_to_pdf(
                    md_content, pdf_path, title="Multi-Jurisdiction Audit Report"
                )
                if result and verbose:
                    print(f"  PDF report: {result}")
            elif fmt == "docx":
                if md_content is None:
                    md_content = engine.render_markdown(
                        audit_report, template_name="multi_jurisdiction_report.md"
                    )
                docx_path = output_dir / f"multi_audit_{ts}.docx"
                result = markdown_to_docx(md_content, docx_path)
                if result and verbose:
                    print(f"  DOCX report: {result}")

        if executive:
            exec_md = engine.render_markdown(
                audit_report, template_name="audit_report_executive.md"
            )
            exec_path = output_dir / f"multi_audit_{ts}_executive.md"
            exec_path.write_text(exec_md, encoding="utf-8")
            if verbose:
                print(f"  Executive summary: {exec_path}")

    except Exception as exc:  # noqa: BLE001
        # Fallback: use legacy markdown generator if reporting system unavailable
        logger.warning("Template rendering failed (%s); using legacy markdown.", exc)
        if "markdown" in formats:
            md_report = gen.generate_markdown_report()
            md_path.write_text(md_report, encoding="utf-8")
            if verbose:
                print(f"  Markdown report (legacy): {md_path}")

    # --- 7. Print summary ---
    _print_summary(runner_results, patterns, output_dir)
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s — %(message)s",
    )
    args = _build_parser().parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
