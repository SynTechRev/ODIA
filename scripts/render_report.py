#!/usr/bin/env python3
"""
Oraculus DI Auditor - Report Renderer

Generates audit reports from manifests and configuration.
Produces Markdown output with optional HTML/PDF conversion via pandoc or wkhtmltopdf.

Usage:
    python scripts/render_report.py --config report_config.json
    python scripts/render_report.py --manifests-dir manifests --output report.md
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print(
        "Error: Jinja2 is required. Install with: pip install Jinja2",
        file=sys.stderr,
    )
    sys.exit(1)


class ReportRenderer:
    """Renders audit reports from manifests and templates."""

    def __init__(
        self, template_dir: str = "templates", manifests_dir: str = "manifests"
    ):
        self.template_dir = Path(template_dir)
        self.manifests_dir = Path(manifests_dir)

        # Set up Jinja2 environment
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))

        # Check for external tools
        self.pandoc_available = shutil.which("pandoc") is not None
        self.wkhtmltopdf_available = shutil.which("wkhtmltopdf") is not None

    def load_manifests(self) -> list[dict[str, Any]]:
        """Load all manifest files from the manifests directory."""
        manifests = []

        if not self.manifests_dir.exists():
            return manifests

        for manifest_file in self.manifests_dir.glob("*.json"):
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)
                    manifests.append(manifest)
            except Exception as e:
                print(
                    f"Warning: Failed to load manifest {manifest_file}: {e}",
                    file=sys.stderr,
                )

        return manifests

    def load_report_config(self, config_path: Path) -> dict[str, Any]:
        """Load report configuration from JSON or YAML file."""
        with open(config_path) as f:
            if config_path.suffix in [".yaml", ".yml"]:
                try:
                    import yaml

                    return yaml.safe_load(f)
                except ImportError:
                    print(
                        "Error: PyYAML required for YAML config. "
                        "Install with: pip install PyYAML",
                        file=sys.stderr,
                    )
                    sys.exit(1)
            else:
                return json.load(f)

    def analyze_manifests(self, manifests: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze manifests to generate statistics and findings."""
        total_documents = len(manifests)
        flagged_documents = sum(
            1 for m in manifests if m.get("flags") and len(m["flags"]) > 0
        )

        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        findings = []
        evidence_manifest = []

        severity_rank = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}

        for manifest in manifests:
            doc_id = manifest.get("document_id", "UNKNOWN")
            flags = manifest.get("flags", [])

            # Track max severity for this document
            max_severity = "none"
            if flags:
                for flag in flags:
                    severity = flag.get("severity", "low")
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1

                    # Update max severity using rank comparison
                    if severity_rank.get(severity, 0) > severity_rank.get(
                        max_severity, 0
                    ):
                        max_severity = severity

                    # Add to findings
                    findings.append(
                        {
                            "title": flag.get("message", "Untitled Finding"),
                            "severity": severity,
                            "category": flag.get("category", "uncategorized"),
                            "document_id": doc_id,
                            "description": flag.get("message", ""),
                            "evidence": f"See manifest: {doc_id}.json",
                            "recommendation": (
                                "Review document and consult legal counsel."
                            ),
                        }
                    )

            # Add to evidence manifest
            evidence_manifest.append(
                {
                    "document_id": doc_id,
                    "source": manifest.get("source", "unknown"),
                    "flag_count": len(flags),
                    "max_severity": max_severity,
                    "checksum": manifest.get("checksum_sha256", "N/A"),
                }
            )

        return {
            "total_documents": total_documents,
            "flagged_documents": flagged_documents,
            "critical_findings": severity_counts.get("critical", 0),
            "high_findings": severity_counts.get("high", 0),
            "medium_findings": severity_counts.get("medium", 0),
            "low_findings": severity_counts.get("low", 0),
            "findings": findings,
            "evidence_manifest": evidence_manifest,
        }

    def render_report(
        self, config: dict[str, Any], manifests: list[dict[str, Any]]
    ) -> str:
        """Render the report using Jinja2 template."""
        # Analyze manifests
        analysis = self.analyze_manifests(manifests)

        # Prepare template context
        context = {
            "report_title": config.get("title", "Audit Report"),
            "author": config.get("author", "Oraculus DI Auditor"),
            "report_id": config.get(
                "report_id", f"REPORT_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            ),
            "generation_date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "executive_summary": config.get(
                "executive_summary",
                (
                    "This audit report summarizes findings from "
                    "the document review process."
                ),
            ),
            "total_documents": analysis["total_documents"],
            "flagged_documents": analysis["flagged_documents"],
            "critical_findings": analysis["critical_findings"],
            "high_findings": analysis["high_findings"],
            "medium_findings": analysis["medium_findings"],
            "low_findings": analysis["low_findings"],
            "findings": analysis["findings"],
            "evidence_manifest": analysis["evidence_manifest"],
            "methodology": config.get(
                "methodology",
                {
                    "ingestion": "Manual document upload and triage",
                    "extraction": "OCR via pytesseract",
                    "analysis": "Four fault-line framework",
                    "review": "Manual review with automated flagging",
                    "limitations": (
                        "This audit is based on available documents and "
                        "may not represent a complete picture."
                    ),
                },
            ),
            "compliance": config.get(
                "compliance",
                {
                    "doj_certification": (
                        "Review DOJ certification requirements " "for all documents."
                    ),
                    "irb_compliance": (
                        "Verify IRB compliance under 28 C.F.R. Part 46."
                    ),
                    "infrastructure": (
                        "Assess infrastructure and procurement policies."
                    ),
                    "federal_grants": "Analyze federal grant incentive structures.",
                },
            ),
            "recommendations": config.get("recommendations", []),
            "chain_of_custody": config.get(
                "chain_of_custody",
                {
                    "initial_date": "Not specified",
                    "review_start": "Not specified",
                    "review_end": datetime.now(UTC).strftime("%Y-%m-%d"),
                    "custodians": ["Audit Team"],
                    "integrity_checks": len(manifests),
                },
            ),
            "manifests": [
                {"document_id": m.get("document_id", "UNKNOWN"), "content": m}
                for m in manifests
            ],
            "extraction_logs": [],
        }

        # Load and render template
        template = self.env.get_template("report_template.md")
        return template.render(**context)

    def convert_to_html(self, markdown_path: Path, html_path: Path) -> bool:
        """Convert Markdown to HTML using pandoc."""
        if not self.pandoc_available:
            print("Warning: pandoc not available, skipping HTML conversion")
            return False

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o",
                    str(html_path),
                    "--standalone",
                    "--toc",
                ],
                check=True,
                capture_output=True,
            )
            print(f"  Generated HTML: {html_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Warning: pandoc conversion failed: {e}", file=sys.stderr)
            return False

    def convert_to_pdf(self, markdown_path: Path, pdf_path: Path) -> bool:
        """Convert Markdown to PDF using pandoc or wkhtmltopdf."""
        if not self.pandoc_available:
            print("Warning: pandoc not available, skipping PDF conversion")
            return False

        try:
            subprocess.run(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o",
                    str(pdf_path),
                    "--pdf-engine=pdflatex",
                ],
                check=True,
                capture_output=True,
            )
            print(f"  Generated PDF: {pdf_path}")
            return True
        except subprocess.CalledProcessError:
            # Try wkhtmltopdf as fallback
            if self.wkhtmltopdf_available:
                try:
                    # First convert to HTML
                    html_path = pdf_path.with_suffix(".html")
                    if self.convert_to_html(markdown_path, html_path):
                        subprocess.run(
                            ["wkhtmltopdf", str(html_path), str(pdf_path)],
                            check=True,
                            capture_output=True,
                        )
                        html_path.unlink()  # Clean up temporary HTML
                        print(f"  Generated PDF: {pdf_path}")
                        return True
                except subprocess.CalledProcessError:
                    pass

            print(
                "Warning: PDF conversion failed "
                "(requires pandoc with pdflatex or wkhtmltopdf)"
            )
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Oraculus DI Auditor - Report Renderer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report from config file
  python scripts/render_report.py --config report_config.json

  # Generate report from manifests directory
  python scripts/render_report.py --manifests-dir manifests --output report.md

  # Generate with HTML and PDF output
  python scripts/render_report.py --config report_config.json --html --pdf
        """,
    )

    parser.add_argument(
        "--config", type=str, help="Path to report configuration (JSON or YAML)"
    )
    parser.add_argument(
        "--manifests-dir",
        type=str,
        default="manifests",
        help="Directory containing manifest files",
    )
    parser.add_argument(
        "--output", type=str, default="reports/audit_report.md", help="Output file path"
    )
    parser.add_argument("--html", action="store_true", help="Generate HTML output")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF output")
    parser.add_argument(
        "--template-dir", type=str, default="templates", help="Template directory"
    )

    args = parser.parse_args()

    # Initialize renderer
    renderer = ReportRenderer(
        template_dir=args.template_dir, manifests_dir=args.manifests_dir
    )

    print("Oraculus DI Auditor - Report Renderer")
    print(f"  Pandoc available: {renderer.pandoc_available}")
    print(f"  wkhtmltopdf available: {renderer.wkhtmltopdf_available}")

    # Load manifests
    print(f"\nLoading manifests from: {args.manifests_dir}")
    manifests = renderer.load_manifests()
    print(f"  Loaded {len(manifests)} manifest(s)")

    if len(manifests) == 0:
        print("Warning: No manifests found. Report will be empty.", file=sys.stderr)

    # Load configuration
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            sys.exit(1)
        print(f"Loading configuration from: {config_path}")
        config = renderer.load_report_config(config_path)
    else:
        # Use default configuration
        print("Using default configuration")
        config = {
            "title": "Oraculus DI Audit Report",
            "author": "Audit Team",
            "executive_summary": (
                "This report contains findings from " "the document audit process."
            ),
            "recommendations": [
                {
                    "title": "Review High-Severity Findings",
                    "priority": "HIGH",
                    "description": (
                        "All high and critical severity findings should "
                        "be reviewed immediately."
                    ),
                    "actions": [
                        "Consult legal counsel",
                        "Implement corrective actions",
                        "Document resolution",
                    ],
                }
            ],
        }

    # Render report
    print("\nRendering report...")
    report_content = renderer.render_report(config, manifests)

    # Save Markdown output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(report_content)

    print(f"[OK] Generated Markdown report: {output_path}")

    # Generate HTML if requested
    if args.html:
        html_path = output_path.with_suffix(".html")
        renderer.convert_to_html(output_path, html_path)

    # Generate PDF if requested
    if args.pdf:
        pdf_path = output_path.with_suffix(".pdf")
        renderer.convert_to_pdf(output_path, pdf_path)

    print("\n[OK] Report generation complete")


if __name__ == "__main__":
    main()
