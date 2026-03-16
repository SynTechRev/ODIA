#!/usr/bin/env python3
"""CLI for temporal contract evolution analysis.

Usage:
    python scripts/run_temporal_analysis.py \\
        --config-dir config/ \\
        --source data/sources/ \\
        --output reports/temporal/ \\
        --format json,markdown
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from repo root without installing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.temporal.evolution_detector import (
    EvolutionPatternDetector,
)  # noqa: E402
from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder  # noqa: E402
from oraculus_di_auditor.temporal.timeline_generator import (
    TimelineGenerator,
)  # noqa: E402


def _load_documents(source_dir: Path) -> list[dict]:
    """Load JSON documents from a directory. Returns empty list if dir is missing."""
    if not source_dir.exists():
        return []
    docs = []
    for path in sorted(source_dir.glob("*.json")):
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                docs.extend(data)
            elif isinstance(data, dict):
                docs.append(data)
        except Exception as e:
            print(f"  [WARN] Could not load {path.name}: {e}")
    return docs


def _print_summary(lineages, patterns, total_spend: float) -> None:
    print()
    print("=" * 60)
    print("  TEMPORAL ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"  Contract lineages: {len(lineages)}")
    print(f"  Evolution patterns: {len(patterns)}")
    print(f"  Total spend tracked: ${total_spend:,.0f}")
    print()

    if lineages:
        print("  Lineages by risk (highest first):")
        for ln in sorted(lineages, key=lambda x: x.risk_score, reverse=True):
            bar = "#" * int(ln.risk_score * 20)
            print(
                f"    {ln.vendor:<24} risk={ln.risk_score:.2f} [{bar:<20}]"
                f"  ${ln.current_amount:>12,.0f}"
                f"  +{ln.growth_percentage:.0f}%"
                f"  {ln.amendment_count} amd(s)"
            )
        print()

    if patterns:
        print("  Detected patterns:")
        for p in sorted(patterns, key=lambda x: x.severity):
            icon = {"critical": "[!!]", "high": "[! ]", "medium": "[ ?]"}.get(
                p.severity, "[ ]"
            )
            print(f"    {icon} {p.pattern_type.upper()}: {p.description[:70]}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run temporal contract evolution analysis on ODIA documents"
    )
    parser.add_argument(
        "--config-dir",
        default="config/",
        help="Path to jurisdiction config directory (default: config/)",
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to directory containing source JSON documents",
    )
    parser.add_argument(
        "--output",
        default="reports/temporal/",
        help="Directory for output files (default: reports/temporal/)",
    )
    parser.add_argument(
        "--format",
        default="json,markdown",
        help="Comma-separated output formats: json, markdown (default: json,markdown)",
    )
    args = parser.parse_args()

    source_dir = Path(args.source)
    output_dir = Path(args.output)
    formats = {f.strip().lower() for f in args.format.split(",")}

    print(f"[OK] Loading documents from: {source_dir}")
    documents = _load_documents(source_dir)
    print(f"     {len(documents)} document(s) loaded")

    if not documents:
        print("[WARN] No documents found. Nothing to analyze.")
        # Still write empty outputs so callers can depend on files existing
        output_dir.mkdir(parents=True, exist_ok=True)
        if "json" in formats:
            (output_dir / "timeline.json").write_text("{}", encoding="utf-8")
        if "markdown" in formats:
            (output_dir / "timeline.md").write_text(
                "## Contract Evolution Timeline\n\n_No documents found._\n",
                encoding="utf-8",
            )
        return 0

    # Build lineages
    print("[OK] Building contract lineages...")
    builder = LineageBuilder()
    builder.load_documents(documents)
    lineages = builder.build_lineages()
    print(f"     {len(lineages)} lineage(s) reconstructed")

    # Detect patterns
    print("[OK] Detecting evolution patterns...")
    detector = EvolutionPatternDetector(lineages)
    patterns = detector.detect_all_patterns()
    print(f"     {len(patterns)} pattern(s) detected")

    # Generate outputs
    gen = TimelineGenerator(lineages, patterns)
    total_spend = sum(ln.current_amount for ln in lineages)

    output_dir.mkdir(parents=True, exist_ok=True)

    if "json" in formats:
        timeline_json = gen.generate_timeline_json()
        timeline_path = output_dir / "timeline.json"
        with timeline_path.open("w", encoding="utf-8") as f:
            json.dump(timeline_json, f, indent=2, default=str)
        print(f"[OK] Timeline JSON written: {timeline_path}")

        chart_path = output_dir / "growth_chart.json"
        with chart_path.open("w", encoding="utf-8") as f:
            json.dump(gen.generate_growth_chart_data(), f, indent=2, default=str)
        print(f"[OK] Growth chart data written: {chart_path}")

    if "markdown" in formats:
        md_path = output_dir / "timeline.md"
        md_path.write_text(gen.generate_timeline_markdown(), encoding="utf-8")
        print(f"[OK] Timeline Markdown written: {md_path}")

    _print_summary(lineages, patterns, total_spend)
    return 0


if __name__ == "__main__":
    sys.exit(main())
