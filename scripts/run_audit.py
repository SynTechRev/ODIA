"""run_audit.py — Single entry-point for running a full ODIA jurisdiction audit.

Usage:
    python scripts/run_audit.py --config-dir config/ --source data/sources/ --output reports/
    python scripts/run_audit.py --config-dir config/ --source data/ --output out/ --verbose
    python scripts/run_audit.py ... --formats json,markdown,html
    python scripts/run_audit.py ... --template audit_report.md --executive

What it does:
    1. Load jurisdiction config from --config-dir
    2. Ingest all PDF/XML/JSON/TXT documents from --source directory
    3. Normalize each document into the canonical schema
    4. Run every anomaly detector against each document
    5. Run the procurement-timeline detector across the full document set
    6. Write a JSON report and a Markdown report to --output directory
    7. Print a summary to stdout
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import traceback
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: make the src/ package importable when run as a script
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from oraculus_di_auditor.analysis import (  # noqa: E402
    detect_administrative_anomalies,
    detect_constitutional_anomalies,
    detect_cross_jurisdiction_refs,
    detect_fiscal_anomalies,
    detect_governance_gap_anomalies,
    detect_procurement_timeline_anomalies,
    detect_scope_expansion_anomalies,
    detect_signature_anomalies,
    detect_surveillance_anomalies,
)
from oraculus_di_auditor.analysis.text_utils import extract_text_content  # noqa: E402
from oraculus_di_auditor.config import (
    JurisdictionConfig,
    load_jurisdiction_config,
)

logger = logging.getLogger("run_audit")


def _detect_cross_ref_from_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Wrap detect_cross_jurisdiction_refs to accept a doc dict.

    Extracts text content from the doc, calls the detector, and normalizes
    the output to the standard {id, issue, severity, layer, details} shape.
    """
    text = extract_text_content(doc)
    raw_refs = detect_cross_jurisdiction_refs(text)
    return [
        {
            "id": f"cross_reference:{ref.get('type', 'unknown')}",
            "issue": ref.get("description", "Cross-jurisdiction reference detected"),
            "severity": "medium",
            "layer": "cross_reference",
            "details": {
                k: v for k, v in ref.items() if k not in ("description", "severity")
            },
        }
        for ref in raw_refs
    ]


# Ordered list of single-document detectors and the layer they report under
_SINGLE_DOC_DETECTORS = [
    ("fiscal", detect_fiscal_anomalies),
    ("constitutional", detect_constitutional_anomalies),
    ("surveillance", detect_surveillance_anomalies),
    ("scope", detect_scope_expansion_anomalies),
    ("signature", detect_signature_anomalies),
    ("governance", detect_governance_gap_anomalies),
    ("administrative", detect_administrative_anomalies),
    ("cross_reference", _detect_cross_ref_from_doc),
]

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_audit",
        description="Run a complete ODIA jurisdiction audit.",
    )
    p.add_argument(
        "--config-dir",
        default="config",
        metavar="DIR",
        help="Directory containing jurisdiction config files (default: config/)",
    )
    p.add_argument(
        "--source",
        required=True,
        metavar="DIR",
        help="Directory to ingest documents from (PDF, XML, JSON, TXT)",
    )
    p.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Directory to write audit reports to",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-document detector output",
    )
    p.add_argument(
        "--formats",
        default="json,markdown",
        metavar="LIST",
        help="Comma-separated output formats: json,markdown,html,pdf,docx (default: json,markdown)",
    )
    p.add_argument(
        "--template",
        default="audit_report.md",
        metavar="TMPL",
        help="Jinja2 template to use for Markdown output (default: audit_report.md)",
    )
    p.add_argument(
        "--executive",
        action="store_true",
        help="Also generate an executive summary report using audit_report_executive.md",
    )
    p.add_argument(
        "--temporal",
        action="store_true",
        default=True,
        help="Run temporal contract evolution analysis (default: on)",
    )
    p.add_argument(
        "--no-temporal",
        dest="temporal",
        action="store_false",
        help="Disable temporal contract evolution analysis",
    )
    return p


# ---------------------------------------------------------------------------
# Document ingestion
# ---------------------------------------------------------------------------


def _discover_files(source_dir: Path) -> list[Path]:
    """Return all ingestable files under source_dir, sorted by name."""
    exts = {".txt", ".json", ".xml", ".pdf"}
    files = sorted(
        f for f in source_dir.rglob("*") if f.is_file() and f.suffix.lower() in exts
    )
    return files


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1252", errors="replace")


def _ingest_file(path: Path, verbose: bool = False) -> dict[str, Any] | None:
    """Read a file and return a normalized document dict, or None on failure."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".txt":
            raw_text = _read_text_file(path)
        elif suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                # If the JSON is already a normalized doc, use it directly
                if "raw_text" in data or "sections" in data:
                    doc = data
                    doc.setdefault("document_id", path.stem)
                    doc.setdefault("title", path.stem)
                    return doc
                raw_text = json.dumps(data, ensure_ascii=False)
            else:
                raw_text = json.dumps(data, ensure_ascii=False)
        elif suffix == ".xml":
            raw_text = _read_text_file(path)
        elif suffix == ".pdf":
            raw_text = _extract_pdf_text(path, verbose)
            if raw_text is None:
                return None
        else:
            return None

        return {
            "document_id": path.stem,
            "title": path.stem.replace("_", " ").replace("-", " ").title(),
            "source_path": str(path),
            "raw_text": raw_text,
            "sections": [{"section_id": "main", "content": raw_text}],
        }

    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to ingest %s: %s", path.name, exc)
        if verbose:
            traceback.print_exc()
        return None


def _extract_pdf_text(path: Path, verbose: bool) -> str | None:
    """Extract text from a PDF using pdfplumber, pypdf, or PyPDF2 (in order)."""
    try:
        import pdfplumber  # type: ignore[import]

        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    except ImportError:
        pass

    for mod_name in ("pypdf", "PyPDF2"):
        try:
            mod = __import__(mod_name)
            reader = mod.PdfReader(str(path))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except ImportError:
            continue
        except Exception as exc:  # noqa: BLE001
            logger.warning("PDF extraction failed for %s: %s", path.name, exc)
            return None

    logger.warning(
        "Skipping %s — no PDF library available "
        "(install pdfplumber: pip install pdfplumber)",
        path.name,
    )
    return None


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def _run_detectors_on_doc(
    doc: dict[str, Any],
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Run all single-document detectors and return combined anomaly list."""
    all_findings: list[dict[str, Any]] = []
    for layer, detector in _SINGLE_DOC_DETECTORS:
        try:
            findings = detector(doc)
            all_findings.extend(findings)
            if verbose and findings:
                logger.info("  [%s] %d finding(s)", layer, len(findings))
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Detector %s failed on %s: %s", layer, doc.get("document_id"), exc
            )
    return all_findings


def _run_audit(
    docs: list[dict[str, Any]],
    jcfg: JurisdictionConfig,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """Run all detectors across all documents.

    Returns a flat list of result records, one per document, each containing
    the document metadata and its findings.
    """
    results: list[dict[str, Any]] = []

    for idx, doc in enumerate(docs, 1):
        doc_id = doc.get("document_id", f"doc-{idx}")
        if verbose:
            logger.info("[%d/%d] Analyzing: %s", idx, len(docs), doc_id)
        else:
            print(f"  [{idx}/{len(docs)}] {doc_id}", end="\r", flush=True)

        findings = _run_detectors_on_doc(doc, verbose=verbose)
        results.append(
            {
                "document_id": doc_id,
                "title": doc.get("title", doc_id),
                "source_path": doc.get("source_path", ""),
                "findings": findings,
                "finding_count": len(findings),
            }
        )

    # Clear the carriage-return progress line
    if not verbose:
        print()

    # Procurement timeline detector operates on the full document set
    try:
        procurement_findings = detect_procurement_timeline_anomalies(docs)
        if procurement_findings:
            # Attribute each procurement finding to its document
            proc_by_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for pf in procurement_findings:
                proc_by_doc[pf.get("details", {}).get("document_id", "unknown")].append(
                    pf
                )
            for result in results:
                extra = proc_by_doc.get(result["document_id"], [])
                result["findings"].extend(extra)
                result["finding_count"] = len(result["findings"])
            if verbose:
                logger.info(
                    "[procurement-timeline] %d finding(s)", len(procurement_findings)
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Procurement timeline detector failed: %s", exc)

    return results


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------


def _collect_all_findings(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten all findings from all document results."""
    flat = []
    for r in results:
        for f in r["findings"]:
            flat.append({**f, "_document_id": r["document_id"]})
    return flat


def _severity_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        sev = f.get("severity", "low")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _top_findings(findings: list[dict[str, Any]], n: int = 10) -> list[dict[str, Any]]:
    """Return the top N findings sorted by severity then by anomaly id."""
    return sorted(
        findings,
        key=lambda f: (
            _SEVERITY_ORDER.get(f.get("severity", "low"), 99),
            f.get("id", ""),
        ),
    )[:n]


def _date_range(results: list[dict[str, Any]]) -> tuple[str, str]:
    """Extract earliest and latest meeting_date fields found in documents."""
    dates: list[str] = []
    for r in results:
        for f in r["findings"]:
            d = f.get("details", {}).get("meeting_date") or f.get("details", {}).get(
                "authorization_date"
            )
            if d and isinstance(d, str) and len(d) == 10:
                dates.append(d)
    if dates:
        return min(dates), max(dates)
    return ("unknown", "unknown")


def _anomaly_summary_by_layer(
    findings: list[dict[str, Any]]
) -> dict[str, dict[str, int]]:
    """Return {layer: {severity: count}} mapping."""
    summary: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for f in findings:
        layer = f.get("layer", "unknown")
        sev = f.get("severity", "low")
        summary[layer][sev] += 1
    return {k: dict(v) for k, v in summary.items()}


def _build_report(
    jcfg: JurisdictionConfig,
    results: list[dict[str, Any]],
    run_ts: str,
) -> dict[str, Any]:
    all_findings = _collect_all_findings(results)
    date_min, date_max = _date_range(results)

    return {
        "audit_timestamp": run_ts,
        "jurisdiction": {
            "name": jcfg.name,
            "state": jcfg.state,
            "country": jcfg.country,
            "meeting_type": jcfg.meeting_type,
        },
        "date_range": {"earliest": date_min, "latest": date_max},
        "document_count": len(results),
        "total_findings": len(all_findings),
        "severity_summary": _severity_counts(all_findings),
        "findings_by_layer": _anomaly_summary_by_layer(all_findings),
        "top_findings": _top_findings(all_findings, 10),
        "documents": results,
    }


def _to_analysis_format(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adapt _run_audit() output to build_report_from_analysis() input format.

    Groups flat finding lists by detector layer so the unified reporting
    system can build structured AuditReport models.
    """
    adapted = []
    for r in results:
        findings_by_layer: dict[str, list[dict[str, Any]]] = {}
        for f in r.get("findings", []):
            layer = f.get("layer", "unknown")
            findings_by_layer.setdefault(layer, []).append(f)
        adapted.append(
            {
                "metadata": {
                    "document_id": r["document_id"],
                    "title": r.get("title", r["document_id"]),
                    "source": r.get("source_path", ""),
                },
                "findings": findings_by_layer,
            }
        )
    return adapted


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _write_reports(
    jcfg: JurisdictionConfig,
    results: list[dict[str, Any]],
    output_dir: Path,
    *,
    formats: list[str],
    template_name: str,
    executive: bool,
    template_dir: Path,
) -> dict[str, Path]:
    """Build an AuditReport and write all requested formats.

    Always writes ``audit_report.json`` and ``audit_report.md`` when those
    formats are requested (backward-compatible filenames). Additional formats
    (html, pdf, docx) are written as ``audit_report.{ext}``. The executive
    summary is written as ``audit_report_executive.md``.

    Returns a dict mapping format name to the written Path.
    """
    from oraculus_di_auditor.reporting import ReportTemplateEngine
    from oraculus_di_auditor.reporting.format_converters import (
        markdown_to_docx,
        markdown_to_html,
        markdown_to_pdf,
    )
    from oraculus_di_auditor.reporting.models import build_report_from_analysis

    analysis_format = _to_analysis_format(results)
    audit_report = build_report_from_analysis(
        analysis_format,
        jurisdiction=jcfg.name,
        title=f"Audit Report — {jcfg.name}",
        report_type="single_jurisdiction",
    )

    engine = ReportTemplateEngine(template_dir=template_dir)
    written: dict[str, Path] = {}
    md_content: str | None = None

    for fmt in formats:
        if fmt == "json":
            path = output_dir / "audit_report.json"
            path.write_text(
                json.dumps(json.loads(audit_report.model_dump_json()), indent=2),
                encoding="utf-8",
            )
            written["json"] = path
            print(f"  JSON : {path}")

        elif fmt == "markdown":
            if md_content is None:
                md_content = engine.render_markdown(
                    audit_report, template_name=template_name
                )
            path = output_dir / "audit_report.md"
            path.write_text(md_content, encoding="utf-8")
            written["markdown"] = path
            print(f"  MD   : {path}")

        elif fmt == "html":
            if md_content is None:
                md_content = engine.render_markdown(
                    audit_report, template_name=template_name
                )
            path = output_dir / "audit_report.html"
            path.write_text(markdown_to_html(md_content), encoding="utf-8")
            written["html"] = path
            print(f"  HTML : {path}")

        elif fmt == "pdf":
            if md_content is None:
                md_content = engine.render_markdown(
                    audit_report, template_name=template_name
                )
            path = output_dir / "audit_report.pdf"
            result = markdown_to_pdf(md_content, path, title=audit_report.title)
            if result:
                written["pdf"] = result
                print(f"  PDF  : {result}")
            else:
                print("  PDF  : [SKIP] no converter available")

        elif fmt == "docx":
            if md_content is None:
                md_content = engine.render_markdown(
                    audit_report, template_name=template_name
                )
            path = output_dir / "audit_report.docx"
            result = markdown_to_docx(md_content, path)
            if result:
                written["docx"] = result
                print(f"  DOCX : {result}")
            else:
                print("  DOCX : [SKIP] pandoc not available")

    if executive:
        exec_md = engine.render_markdown(
            audit_report, template_name="audit_report_executive.md"
        )
        path = output_dir / "audit_report_executive.md"
        path.write_text(exec_md, encoding="utf-8")
        written["executive"] = path
        print(f"  EXEC : {path}")

    return written


def _print_summary(report: dict[str, Any]) -> None:
    jur = report["jurisdiction"]
    sev = report["severity_summary"]
    total = report["total_findings"]

    print()
    print("=" * 60)
    print(f"ODIA Audit Complete — {jur['name']}")
    print("=" * 60)
    print(f"  Documents analyzed : {report['document_count']}")
    print(f"  Total findings     : {total}")
    if total:
        print(f"    Critical : {sev.get('critical', 0)}")
        print(f"    High     : {sev.get('high', 0)}")
        print(f"    Medium   : {sev.get('medium', 0)}")
        print(f"    Low      : {sev.get('low', 0)}")
    print()
    if report["top_findings"]:
        print("Top findings:")
        for i, f in enumerate(report["top_findings"][:5], 1):
            print(
                f"  {i}. [{f.get('severity','?').upper():8s}] "
                f"{f.get('id','?')} — {f.get('issue','')[:60]}"
            )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_audit(
    config_dir: str | Path,
    source_dir: str | Path,
    output_dir: str | Path,
    verbose: bool = False,
    *,
    formats: list[str] | None = None,
    template_name: str = "audit_report.md",
    executive: bool = False,
    template_dir: str | Path | None = None,
    temporal: bool = True,
) -> dict[str, Any]:
    """Programmatic entry point (also called by the CLI).

    Returns the full report dict so callers (and tests) can inspect results.

    Args:
        config_dir: Directory with jurisdiction config files.
        source_dir: Directory to ingest documents from.
        output_dir: Directory to write audit reports to.
        verbose: Print per-document detector output.
        formats: Output formats to generate. Default: ["json", "markdown"].
        template_name: Jinja2 template for Markdown output.
        executive: Also generate executive summary report.
        template_dir: Path to Jinja2 templates. Defaults to repo_root/templates.
    """
    config_dir = Path(config_dir)
    source_dir = Path(source_dir)
    output_dir = Path(output_dir)

    # 1. Validate directories
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir.resolve()}")
    if not source_dir.is_dir():
        raise NotADirectoryError(
            f"Source path is not a directory: {source_dir.resolve()}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Load jurisdiction config
    jcfg = load_jurisdiction_config(config_dir)
    if verbose:
        logger.info("Jurisdiction: %s (%s)", jcfg.name, jcfg.state)

    # 3. Discover files
    files = _discover_files(source_dir)
    if not files:
        raise ValueError(
            f"No ingestable documents found in {source_dir.resolve()}. "
            "Supported formats: PDF, XML, JSON, TXT"
        )
    print(f"Found {len(files)} file(s) in {source_dir}")

    # 4. Ingest
    docs: list[dict[str, Any]] = []
    for path in files:
        doc = _ingest_file(path, verbose=verbose)
        if doc is not None:
            docs.append(doc)
        else:
            logger.warning("Skipped: %s", path.name)

    if not docs:
        raise ValueError("No documents could be successfully ingested.")

    print(f"Ingested {len(docs)} document(s). Running analysis…")

    # 5. Run audit
    run_ts = datetime.now(UTC).isoformat()
    results = _run_audit(docs, jcfg, verbose=verbose)

    # 5b. Temporal analysis (best-effort)
    temporal_data: dict[str, Any] = {}
    if temporal:
        try:
            from oraculus_di_auditor.temporal.evolution_detector import (
                EvolutionPatternDetector,
            )
            from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder
            from oraculus_di_auditor.temporal.timeline_generator import (
                TimelineGenerator,
            )

            builder = LineageBuilder()
            builder.load_documents(docs)
            lineages = builder.build_lineages()
            patterns = EvolutionPatternDetector(lineages).detect_all_patterns()
            timeline = TimelineGenerator(lineages, patterns).generate_timeline_json()
            temporal_data = {
                "lineage_count": len(lineages),
                "pattern_count": len(patterns),
                "lineages": [ln.model_dump() for ln in lineages],
                "patterns": [p.model_dump() for p in patterns],
                "timeline": timeline,
            }
            print(
                f"Temporal: {len(lineages)} lineage(s), {len(patterns)} pattern(s) detected"
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Temporal analysis skipped: %s", exc)

    # 6. Build legacy report dict (used by _print_summary)
    report = _build_report(jcfg, results, run_ts)
    if temporal_data:
        report["temporal"] = temporal_data

    # 7. Write reports via unified reporting system
    _formats = formats if formats is not None else ["json", "markdown"]
    _template_dir = Path(template_dir) if template_dir else _REPO_ROOT / "templates"
    print("Reports written:")
    _write_reports(
        jcfg,
        results,
        output_dir,
        formats=_formats,
        template_name=template_name,
        executive=executive,
        template_dir=_template_dir,
    )

    # 8. Print summary
    _print_summary(report)

    return report


_EXAMPLE_JURISDICTION_NAME = "City of Example"


def _check_first_run(config_dir: Path) -> None:
    """Detect missing or unconfigured jurisdiction and offer wizard.

    - If jurisdiction.json does not exist: offer to run the setup wizard.
    - If jurisdiction.json exists but still has the example name: warn the user.

    This function is a no-op when valid configuration is already in place,
    so existing users experience no change.
    """
    jurisdiction_file = config_dir / "jurisdiction.json"

    if not jurisdiction_file.exists():
        print()
        print("No jurisdiction configured.")
        print(
            "Would you like to set up a new jurisdiction now? (y/n) ",
            end="",
            flush=True,
        )
        try:
            answer = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"

        if answer.startswith("y"):
            import subprocess

            wizard = _REPO_ROOT / "scripts" / "setup_jurisdiction.py"
            subprocess.run(
                [sys.executable, str(wizard), "--config-dir", str(config_dir)],
                check=False,
            )
            # Re-check after wizard; exit if still not configured
            if not jurisdiction_file.exists():
                print(
                    "\nJurisdiction not configured. Exiting.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            print()
            print(
                "To configure manually, copy config/jurisdiction.example.json to\n"
                "config/jurisdiction.json and edit the 'name' and 'state' fields.\n"
                "\nOr use the demo dataset without any configuration:\n"
                "    python scripts/run_audit.py"
                " --source data/demo/ --output reports/demo/"
            )
            sys.exit(0)

    else:
        # Config exists — warn if it's still the unmodified example
        try:
            import json as _json

            data = _json.loads(jurisdiction_file.read_text(encoding="utf-8"))
            if data.get("name") == _EXAMPLE_JURISDICTION_NAME:
                print(
                    f"NOTE: You are using the example configuration"
                    f" ('{_EXAMPLE_JURISDICTION_NAME}').\n"
                    "      Run 'python scripts/setup_jurisdiction.py' to configure"
                    " for your jurisdiction,\n"
                    "      or use '--source data/demo/' for the built-in demo.\n"
                )
        except Exception:  # noqa: BLE001
            pass  # If we can't read it, let load_jurisdiction_config handle the error


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    # First-run detection: offer wizard when config is missing or is the example
    _check_first_run(Path(args.config_dir))

    try:
        run_audit(
            config_dir=args.config_dir,
            source_dir=args.source,
            output_dir=args.output,
            verbose=args.verbose,
            formats=[f.strip() for f in args.formats.split(",") if f.strip()],
            template_name=args.template,
            executive=args.executive,
            temporal=args.temporal,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
