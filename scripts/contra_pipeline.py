"""CONTRA corpus expansion pipeline — end-to-end orchestrator.

Chains:
  1. Gap analysis    → show which chain members have no coverage
  2. New PDF finder  → hash-based dedup of a target folder
  3. Batch ingest    → ingest only genuinely new files
  4. CIFU recompute  → update all chain scores after ingest
  5. Summary report  → corpus stats before and after

Usage:
    # Full pipeline on the Uber Technologies Inc folder:
    python scripts/contra_pipeline.py --folder "D:/CONTRA Contract Corpus/Uber Technologies Inc"

    # Full corpus scan (all entities, auto-entity inference):
    python scripts/contra_pipeline.py --folder "D:/CONTRA Contract Corpus" --auto-entity

    # Gap analysis only (no ingest):
    python scripts/contra_pipeline.py --gap-only

    # Ingest only (skip gap and CIFU recompute):
    python scripts/contra_pipeline.py --folder "..." --ingest-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
_DATA = _REPO_ROOT / "data"
_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"


def _run(cmd: list[str], label: str) -> tuple[int, str]:
    print(f"\n{'─'*60}")
    print(f"[PIPELINE] {label}")
    print(f"{'─'*60}")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode, result.stdout


def _corpus_stats(db_path: str) -> dict:
    """Snapshot entity/doc/finding counts from DB."""
    from sqlalchemy import create_engine, text

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    with engine.connect() as conn:
        docs = conn.execute(text("SELECT COUNT(*) FROM commercial_documents")).scalar()
        entities = conn.execute(
            text("SELECT COUNT(*) FROM commercial_entities")
        ).scalar()
        findings = conn.execute(text("SELECT COUNT(*) FROM contra_findings")).scalar()
    return {"docs": docs, "entities": entities, "findings": findings}


def run_pipeline(
    folder: str | None,
    db_path: str,
    auto_entity: bool,
    entity_name: str | None,
    gap_only: bool,
    ingest_only: bool,
    chain: str | None,
    dry_run: bool,
) -> None:
    ts = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'═'*60}")
    print(f"C.O.N.T.R.A. Corpus Expansion Pipeline — {ts}")
    print(f"{'═'*60}")

    # ── Step 0: snapshot before state ──────────────────────────
    stats_before = _corpus_stats(db_path)
    print(
        f"\nCorpus before: {stats_before['docs']} docs | "
        f"{stats_before['entities']} entities | "
        f"{stats_before['findings']} findings"
    )

    # ── Step 1: Gap analysis ────────────────────────────────────
    if not ingest_only:
        gap_out = _DATA / f"gap_report_{datetime.now(UTC).strftime('%Y-%m-%d')}.json"
        gap_args = [
            sys.executable,
            str(_SCRIPTS / "contra_corpus_gap.py"),
            "--db-path",
            db_path,
            "--json-out",
            str(gap_out),
        ]
        if chain:
            gap_args += ["--chain", chain]
        rc, _ = _run(gap_args, "Step 1: Chain Coverage Gap Analysis")
        if rc != 0:
            print("WARNING: gap analysis returned non-zero exit code, continuing...")

    if gap_only:
        print("\n[PIPELINE] --gap-only: stopping after gap analysis.")
        return

    # ── Step 2: New PDF finder ──────────────────────────────────
    if folder:
        manifest_ts = datetime.now(UTC).strftime("%Y-%m-%d")
        manifest_path = _DATA / "manifests" / f"auto_new_{manifest_ts}.json"
        dup_path = _DATA / f"dup_report_{manifest_ts}.json"

        finder_args = [
            sys.executable,
            str(_SCRIPTS / "contra_new_pdf_finder.py"),
            "--folder",
            folder,
            "--db-path",
            db_path,
            "--manifest",
            str(manifest_path),
            "--dup-report",
            str(dup_path),
        ]
        if auto_entity:
            finder_args.append("--auto-entity")
        if entity_name:
            finder_args += ["--entity", entity_name]

        rc, finder_out = _run(finder_args, "Step 2: New PDF Finder (hash dedup)")
        if rc != 0:
            print("ERROR: PDF finder failed. Stopping.")
            return

        # Check if any new files were found
        if manifest_path.exists():
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
            n_new = len(manifest)
        else:
            n_new = 0

        print(f"\n[PIPELINE] New files found: {n_new}")

        # ── Step 3: Batch ingest ─────────────────────────────────
        if n_new > 0:
            if dry_run:
                print("[PIPELINE] --dry-run: skipping ingest.")
            else:
                ingest_args = [
                    sys.executable,
                    str(_SCRIPTS / "contra_batch_ingest.py"),
                    "--manifest",
                    str(manifest_path),
                    "--db-path",
                    db_path,
                ]
                rc, _ = _run(ingest_args, f"Step 3: Batch Ingest ({n_new} new files)")
                if rc != 0:
                    print(
                        "WARNING: ingest returned non-zero exit code, continuing to CIFU recompute..."
                    )
        else:
            print("[PIPELINE] No new files — skipping ingest.")

    # ── Step 4: CIFU recompute ──────────────────────────────────
    if not ingest_only or not folder:
        cifu_args = [
            sys.executable,
            str(_SCRIPTS / "compute_cifu.py"),
            "--db-path",
            db_path,
        ]
        if chain:
            cifu_args += ["--chain", chain]
        _run(cifu_args, "Step 4: CIFU Recompute (all chains)")

    # ── Step 5: Summary ─────────────────────────────────────────
    stats_after = _corpus_stats(db_path)
    delta_docs = stats_after["docs"] - stats_before["docs"]
    delta_entities = stats_after["entities"] - stats_before["entities"]
    delta_findings = stats_after["findings"] - stats_before["findings"]

    print(f"\n{'═'*60}")
    print(f"Pipeline Complete — {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'═'*60}")
    print(
        f"  Docs:     {stats_before['docs']:>5} → {stats_after['docs']:>5}  (Δ {delta_docs:+d})"
    )
    print(
        f"  Entities: {stats_before['entities']:>5} → {stats_after['entities']:>5}  (Δ {delta_entities:+d})"
    )
    print(
        f"  Findings: {stats_before['findings']:>5} → {stats_after['findings']:>5}  (Δ {delta_findings:+d})"
    )
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CONTRA end-to-end corpus expansion pipeline"
    )
    parser.add_argument("--folder", default=None, help="Folder to scan for new PDFs")
    parser.add_argument(
        "--entity",
        default=None,
        help="Entity name override (for single-entity folders)",
    )
    parser.add_argument(
        "--auto-entity",
        action="store_true",
        help="Infer entity from subfolder structure",
    )
    parser.add_argument(
        "--db-path", default=_DEFAULT_DB, help="Path to contra_corpus.db"
    )
    parser.add_argument(
        "--chain", default=None, help="Limit gap analysis and CIFU to a specific chain"
    )
    parser.add_argument(
        "--gap-only", action="store_true", help="Run gap analysis only, no ingest"
    )
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Skip gap analysis and CIFU, just ingest",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Find new PDFs but do not ingest them"
    )
    args = parser.parse_args()

    sys.path.insert(0, str(_REPO_ROOT / "src"))

    run_pipeline(
        folder=args.folder,
        db_path=args.db_path,
        auto_entity=args.auto_entity,
        entity_name=args.entity,
        gap_only=args.gap_only,
        ingest_only=args.ingest_only,
        chain=args.chain,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
