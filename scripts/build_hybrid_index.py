#!/usr/bin/env python3
"""Build the full-corpus HybridRetriever index (BGE-M3 dense + BM25 sparse).

Resolves B-13: the Day 2 HybridRetriever was benchmarked on a 1,000-doc test
slice. This script builds the production index over all 81,309 documents in
oraculus_audit.db and saves it to data/vectors/hybrid_index/.

Expected wall-clock: ~7 hours on CPU-only hardware (Intel i7 / Ryzen 9 class).
Run as an overnight job:

  python -I scripts/build_hybrid_index.py

Or with explicit DB and output paths:

  python -I scripts/build_hybrid_index.py \\
      --db oraculus_audit.db \\
      --out data/vectors/hybrid_index \\
      --batch-size 64

After completion the gate and RAIA pipeline can be re-run with the full
HybridRetriever replacing the _TFIDFRetrieverShim:

  python -I scripts/raia_severity_critical_gate.py --model odia-v3

The raia_v0 agent reads data/vectors/hybrid_index/ if the --retriever flag
is set to "hybrid" (default still "tfidf" until index exists).
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DB_PATHS = [
    Path("oraculus_audit.db"),
    Path.home() / "AppData" / "Roaming" / "odia-desktop" / "oraculus_audit.db",
    Path.home() / "oraculus_audit.db",
]


def _find_db(override: Path | None) -> Path:
    if override and override.exists():
        return override
    for p in DB_PATHS:
        if p.exists():
            return p
    raise FileNotFoundError(
        "oraculus_audit.db not found. Checked:\n"
        + "\n".join(f"  {p}" for p in DB_PATHS)
    )


def _load_documents(db_path: Path, limit: int | None) -> list[dict]:
    """Pull document metadata + findings from SQLite for indexing."""
    log.info("Connecting to %s", db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        query = """
            SELECT
                d.document_id,
                d.title,
                d.jurisdiction
            FROM documents d
            ORDER BY d.document_id
        """
        if limit:
            query += f" LIMIT {limit}"

        rows = conn.execute(query).fetchall()
        log.info("Loaded %d document rows", len(rows))

        # Build doc_id -> findings list map
        log.info("Loading anomaly findings (may take a minute)...")
        finding_rows = conn.execute(
            "SELECT document_id, issue, severity, layer FROM anomaly_findings"
        ).fetchall()
        log.info("Loaded %d finding rows", len(finding_rows))

        findings_by_doc: dict[str, list[dict]] = {}
        for fr in finding_rows:
            doc_id = fr["document_id"]
            if doc_id not in findings_by_doc:
                findings_by_doc[doc_id] = []
            findings_by_doc[doc_id].append(
                {
                    "issue": fr["issue"] or "",
                    "severity": fr["severity"] or "",
                    "layer": fr["layer"] or "",
                }
            )

        docs = []
        for row in rows:
            doc_id = row["document_id"]
            docs.append(
                {
                    "document_id": doc_id,
                    "title": row["title"] or "",
                    "jurisdiction": row["jurisdiction"] or "",
                    "findings": findings_by_doc.get(doc_id, []),
                }
            )
        return docs
    finally:
        conn.close()


def _write_manifest(out_dir: Path, n_docs: int, elapsed_s: float) -> None:
    manifest = {
        "built": datetime.now(UTC).isoformat(),
        "n_docs": n_docs,
        "elapsed_seconds": round(elapsed_s, 1),
        "files": [
            "dense_matrix.npy",
            "bm25.pkl",
            "doc_ids.json",
            "doc_texts.json",
            "docs.jsonl",
        ],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    log.info("Manifest written: %s", out_dir / "manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build full-corpus HybridRetriever index (B-13)"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to oraculus_audit.db (auto-detected if omitted)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/vectors/hybrid_index"),
        help="Output directory for index files",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models"),
        help="Directory containing bge-m3/ subdirectory",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="BGE-M3 encoding batch size (default 64; reduce to 32 for <16GB RAM)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit docs for testing (omit for full 81K corpus)",
    )
    parser.add_argument(
        "--no-reranker",
        action="store_true",
        help="Skip loading bge-reranker-v2-m3 during index build (faster)",
    )
    args = parser.parse_args()

    try:
        db_path = _find_db(args.db)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    log.info("DB: %s", db_path)
    log.info("Output: %s", args.out)
    log.info("Model dir: %s", args.model_dir)

    bge_m3_path = args.model_dir / "bge-m3"
    if not bge_m3_path.exists():
        print(
            f"ERROR: BGE-M3 not found at {bge_m3_path}. "
            "Run scripts/download_day02_models.py first.",
            file=sys.stderr,
        )
        return 1

    t0 = time.monotonic()
    docs = _load_documents(db_path, args.limit)
    log.info(
        "Document load complete (%d docs, %.1fs)", len(docs), time.monotonic() - t0
    )

    from oraculus_di_auditor.retrieval.hybrid import HybridRetriever

    retriever = HybridRetriever(
        model_dir=args.model_dir,
        use_reranker=not args.no_reranker,
    )

    log.info(
        "Starting BGE-M3 encoding of %d documents (batch_size=%d)...",
        len(docs),
        args.batch_size,
    )
    log.info("Estimated wall-clock: ~7 hours for 81K docs on CPU")

    retriever.index(docs, batch_size=args.batch_size)

    log.info("Index built. Saving to %s", args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    retriever.save(args.out)

    elapsed = time.monotonic() - t0
    _write_manifest(args.out, len(docs), elapsed)

    log.info(
        "DONE: %d docs indexed in %.0f minutes (%.1fs)",
        len(docs),
        elapsed / 60,
        elapsed,
    )
    log.info("Index location: %s", args.out.resolve())
    log.info("Next: re-run severity_critical gate with --retriever hybrid")

    return 0


if __name__ == "__main__":
    sys.exit(main())
