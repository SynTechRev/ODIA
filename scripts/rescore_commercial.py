"""Re-run L-11–L-20 detectors on all ingested commercial documents.

Use after fixing detector patterns (e.g. L-13:A, L-17:C) to rebuild all
ContraFinding and CasiScore records from the current detector code without
altering CommercialDocument or CommercialEntity records.

Strategy
--------
1. Enumerate all source PDFs from every manifest JSON file found.
2. For each PDF: compute SHA-256(raw_bytes) and check whether it is in the DB.
3. On a match: delete its ContraFinding + CasiScore rows, re-run all L-11–L-20
   detectors, recompute CASI, and insert fresh rows.
4. Write a progress checkpoint to survive interruption (resume by default).

Usage:
    python scripts/rescore_commercial.py
    python scripts/rescore_commercial.py --dry-run
    python scripts/rescore_commercial.py --fresh   # ignore checkpoint, start over
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_CHECKPOINT = _REPO_ROOT / "cache" / "rescore_checkpoint.json"
_PAUSE = 0.1  # seconds between documents

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

_MANIFEST_GLOBS = [
    "contra_manifest*.json",
    "cache/*/harvest_manifest*.json",
]

_REGULATED_TYPES = {"privacy_notice"}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _collect_manifests(repo_root: Path) -> list[Path]:
    manifests: list[Path] = []
    for pattern in _MANIFEST_GLOBS:
        manifests.extend(repo_root.glob(pattern))
    return sorted(set(manifests))


def _all_file_paths(manifests: list[Path]) -> dict[str, dict]:
    """Build map of absolute_file_path -> manifest entry."""
    seen: dict[str, dict] = {}
    for mpath in manifests:
        try:
            entries = json.loads(mpath.read_text(encoding="utf-8"))
        except Exception as exc:
            log.warning("Could not read manifest %s: %s", mpath.name, exc)
            continue
        for entry in entries:
            fp = entry.get("file_path", "")
            if fp and fp not in seen:
                seen[fp] = entry
    return seen


def _run_detectors(doc_text: str, doc_hash: str) -> list:
    import importlib

    _CLASSES = [
        "L11ArbitrationArchitecture",
        "L12ChoiceOfLawForum",
        "L13UnilateralModification",
        "L14DataCollectionDepth",
        "L15DataRetention",
        "L16OnwardTransfer",
        "L17MlAiTraining",
        "L18RemedyForeclosure",
        "L19EnforcementAsymmetry",
        "L20DarkPattern",
    ]
    contra_module = importlib.import_module("oraculus_di_auditor.contra")
    doc_meta = {"document_hash": doc_hash}
    findings = []
    for cls_name in _CLASSES:
        cls = getattr(contra_module, cls_name, None)
        if cls is None:
            continue
        try:
            findings.extend(cls().scan(doc_text, doc_meta))
        except Exception as exc:
            log.warning("Detector %s raised: %s", cls_name, exc)
    return findings


def _compute_casi(findings: list) -> object:
    from oraculus_di_auditor.scoring.casi import compute_casi

    return compute_casi(findings)


def _extract_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        log.warning("PDF extraction failed %s: %s", pdf_path.name, exc)
        return ""


def rescore(db_path: str, dry_run: bool, fresh: bool) -> None:
    from oraculus_di_auditor.db.models import (
        CasiScore,
        CommercialDocument,
        ContraFinding,
    )
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    # Load checkpoint
    done: set[str] = set()
    if not fresh and _CHECKPOINT.exists():
        done = set(json.loads(_CHECKPOINT.read_text(encoding="utf-8")))
        log.info("Resuming — %d documents already processed", len(done))

    # Collect all known hashes in DB
    db_hashes: set[str] = {
        h for (h,) in session.query(CommercialDocument.document_hash).all()
    }
    log.info("DB contains %d document hashes", len(db_hashes))

    # Enumerate all manifest file paths
    manifests = _collect_manifests(_REPO_ROOT)
    log.info("Found %d manifest files", len(manifests))
    all_paths = _all_file_paths(manifests)
    log.info("Total unique file paths across manifests: %d", len(all_paths))

    stats = {"matched": 0, "rescored": 0, "missing": 0, "skipped": 0, "errors": 0}

    for fp_str, entry in sorted(all_paths.items()):
        fp = Path(fp_str)
        if not fp.exists():
            stats["missing"] += 1
            continue

        try:
            doc_hash = _sha256_file(fp)
        except Exception as exc:
            log.warning("Hash failed %s: %s", fp.name, exc)
            stats["errors"] += 1
            continue

        if doc_hash not in db_hashes:
            continue  # not ingested — skip silently

        stats["matched"] += 1

        if doc_hash in done:
            stats["skipped"] += 1
            continue

        # Re-extract text
        doc_text = _extract_text(fp)
        if not doc_text.strip():
            log.warning("Empty extraction for %s — skipping", fp.name)
            stats["errors"] += 1
            done.add(doc_hash)
            continue

        # Re-run detectors
        new_findings = _run_detectors(doc_text, doc_hash)
        casi = _compute_casi(new_findings)

        if dry_run:
            log.info(
                "DRY RUN %s | findings=%d  CASI=%d  band=%s",
                fp.name,
                len(new_findings),
                casi.aggregate,
                casi.band,
            )
            done.add(doc_hash)
            stats["rescored"] += 1
            continue

        # Delete old rows
        session.query(ContraFinding).filter(
            ContraFinding.document_hash == doc_hash
        ).delete()
        session.query(CasiScore).filter(CasiScore.document_hash == doc_hash).delete()

        # Insert new findings
        doc_type = entry.get("doc_type", "tos")
        for finding in new_findings:
            db_dict = finding.to_db_dict()
            db_dict["document_hash"] = doc_hash
            session.add(ContraFinding(**db_dict))

        agg = casi.aggregate
        fdr = round(len(new_findings) / agg, 3) if agg > 0 else 0.0
        rcd = (agg - 30) if doc_type in _REGULATED_TYPES and agg > 30 else None

        session.add(
            CasiScore(
                document_hash=doc_hash,
                remedy_foreclosure=casi.remedy_foreclosure,
                data_extraction_depth=casi.data_extraction_depth,
                modification_and_consent=casi.modification_and_consent,
                procedural_adhesion=casi.procedural_adhesion,
                enforcement_cost_asymmetry=casi.enforcement_cost_asymmetry,
                aggregate=agg,
                band=casi.band,
                framework_version="1.1",
                computed_at=datetime.now(UTC),
                finding_density_ratio=fdr,
                regulated_content_delta=rcd,
            )
        )

        session.commit()

        done.add(doc_hash)
        stats["rescored"] += 1

        if stats["rescored"] % 25 == 0:
            _CHECKPOINT.parent.mkdir(exist_ok=True)
            _CHECKPOINT.write_text(json.dumps(sorted(done)), encoding="utf-8")
            log.info(
                "Progress: %d rescored / %d matched",
                stats["rescored"],
                stats["matched"],
            )

        time.sleep(_PAUSE)

    # Final checkpoint save
    if not dry_run:
        _CHECKPOINT.parent.mkdir(exist_ok=True)
        _CHECKPOINT.write_text(json.dumps(sorted(done)), encoding="utf-8")

    session.close()

    print("\n-- Rescore Complete --")
    print(f"  Matched in DB    : {stats['matched']}")
    print(f"  Rescored         : {stats['rescored']}")
    print(f"  Skipped (done)   : {stats['skipped']}")
    print(f"  File missing     : {stats['missing']}")
    print(f"  Errors           : {stats['errors']}")
    if dry_run:
        print("  (dry run — no DB changes)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Re-run detectors on all ingested commercial documents"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fresh", action="store_true", help="Ignore checkpoint, start from scratch"
    )
    args = parser.parse_args()
    rescore(args.db_path, dry_run=args.dry_run, fresh=args.fresh)


if __name__ == "__main__":
    main()
