#!/usr/bin/env python3
"""S.A.B.E.R. Phase 1 migration script.

Migrates all four corpora (cpra, cal_codes, us_code, cfr) in parallel into the
S.A.B.E.R. content store (ELECT-5: all four in parallel).

Each corpus migration:
  1. Instantiates the CorpusLoader for that corpus
  2. Calls loader.initialize()
  3. Iterates over all known citations
  4. Stores each provision in the ContentStore (Pillar 1)
  5. Logs each operation to the AuditLog (Pillar 3)
  6. Writes a LoaderManifest (Pillar 2)
  7. Signs everything with the Architect key (Pillar 4, optional)

Usage:
    python scripts/saber_migrate_phase1.py
    python scripts/saber_migrate_phase1.py --dry-run
    python scripts/saber_migrate_phase1.py --store-path /custom/store/path
    python scripts/saber_migrate_phase1.py --no-sign
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.legal.saber import (
    AuditLog,
    ContentStore,
    LoaderManifest,
    SigningKey,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("saber.migrate")

_DEFAULT_STORE = Path(__file__).parent.parent / "data" / "saber" / "store"
_DEFAULT_LOG = Path(__file__).parent.parent / "data" / "saber" / "audit" / "saber.log"
_DEFAULT_MANIFESTS = Path(__file__).parent.parent / "data" / "saber" / "manifests"

# ELECT-5: cpra, cal_codes, us_code, cfr in parallel
_CORPORA = ["cpra", "cal_codes", "us_code", "cfr"]


def _load_cpra_provisions() -> dict[str, str]:
    """Return {citation: text} for all embedded CPRA provisions."""
    from oraculus_di_auditor.legal.cpra_corpus import _PROVISIONS

    return {citation: prov["text"] for citation, prov in _PROVISIONS.items()}


def _load_corpus_provisions(corpus_id: str) -> dict[str, str]:
    """Load provisions for a corpus. Returns empty dict if corpus is unavailable."""
    if corpus_id == "cpra":
        return _load_cpra_provisions()
    # cal_codes, us_code, cfr: attempt CorpusLoader.initialize() + list all
    try:
        module_name = f"oraculus_di_auditor.legal.{corpus_id}_corpus"
        import importlib

        mod = importlib.import_module(module_name)
        loader_cls = getattr(
            mod, f"{corpus_id.title().replace('_', '')}CorpusLoader", None
        )
        if loader_cls is None:
            logger.warning("No CorpusLoader found in %s; skipping corpus", module_name)
            return {}
        loader = loader_cls()
        loader.initialize()
        # Attempt list_citations if available
        if hasattr(loader, "list_all_citations"):
            citations = loader.list_all_citations()
            provisions = {}
            for cit in citations:
                result = loader.resolve_citation(cit)
                if result is not None:
                    provisions[cit] = result.text
            return provisions
        logger.info(
            "Corpus %s has no list_all_citations(); migrating 0 provisions", corpus_id
        )
        return {}
    except (ImportError, Exception) as exc:
        logger.warning(
            "Corpus %s unavailable (%s); migrating 0 provisions", corpus_id, exc
        )
        return {}


def _sha256_dict(d: dict[str, str]) -> str:
    """Deterministic SHA-256 over a {citation: text} dict, sorted by key."""
    payload = json.dumps(d, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def migrate_corpus(
    corpus_id: str,
    store: ContentStore,
    audit_log: AuditLog,
    manifests_dir: Path,
    signing_key: SigningKey | None,
    dry_run: bool,
) -> dict[str, Any]:
    """Migrate one corpus. Returns a result summary dict."""
    t0 = time.monotonic()
    logger.info("[%s] Starting migration", corpus_id)

    provisions = _load_corpus_provisions(corpus_id)
    logger.info("[%s] %d provisions loaded", corpus_id, len(provisions))

    source_hash = _sha256_dict(provisions)
    migrated = 0
    failed = 0

    if not dry_run:
        for citation, text in provisions.items():
            try:
                addr = store.put(corpus_id, citation, text, signing_key=signing_key)
                audit_log.append(
                    "migrate",
                    corpus_id,
                    citation=citation,
                    sha256=addr.sha256,
                    result="ok",
                )
                migrated += 1
            except Exception as exc:
                logger.error("[%s] Failed to migrate %s: %s", corpus_id, citation, exc)
                audit_log.append(
                    "migrate",
                    corpus_id,
                    citation=citation,
                    result="fail",
                )
                failed += 1

        # Compute snapshot hash from the store's lookup table after migration
        table = store._load_lookup(corpus_id)
        snapshot_hash = hashlib.sha256(
            json.dumps(table["entries"], sort_keys=True).encode("utf-8")
        ).hexdigest()

        manifest = LoaderManifest.record(
            corpus_id=corpus_id,
            source_description=f"Phase 1 migration of {corpus_id} corpus ({len(provisions)} provisions)",
            source_hash=source_hash,
            snapshot_hash=snapshot_hash,
            provision_count=migrated,
            signing_key=signing_key,
        )
        manifest_path = manifest.save(manifests_dir)
        logger.info("[%s] Manifest written: %s", corpus_id, manifest_path)

        audit_log.append("checkpoint", corpus_id, result="ok")
    else:
        snapshot_hash = "dry-run"
        migrated = len(provisions)
        manifest_path = None
        logger.info("[%s] DRY RUN -- no writes performed", corpus_id)

    elapsed = time.monotonic() - t0
    result = {
        "corpus_id": corpus_id,
        "provisions_available": len(provisions),
        "migrated": migrated,
        "failed": failed,
        "source_hash": source_hash,
        "snapshot_hash": snapshot_hash,
        "elapsed_s": round(elapsed, 3),
        "dry_run": dry_run,
    }
    status = "OK" if failed == 0 else "PARTIAL"
    logger.info(
        "[%s] %s -- %d migrated, %d failed in %.3fs",
        corpus_id,
        status,
        migrated,
        failed,
        elapsed,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="S.A.B.E.R. Phase 1 migration -- all four corpora in parallel"
    )
    parser.add_argument(
        "--store-path",
        type=Path,
        default=_DEFAULT_STORE,
        help="Content store directory (default: data/saber/store)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate loaders without writing to the store",
    )
    parser.add_argument(
        "--no-sign",
        action="store_true",
        help="Skip signing (no signing key required)",
    )
    parser.add_argument(
        "--corpus",
        choices=_CORPORA,
        nargs="+",
        default=_CORPORA,
        help="Limit migration to specific corpora",
    )
    args = parser.parse_args()

    store = ContentStore(args.store_path)
    audit_log = AuditLog(_DEFAULT_LOG)
    manifests_dir = _DEFAULT_MANIFESTS

    if not args.dry_run:
        store.initialize()
        audit_log.append("init", "saber", result="ok")

    signing_key: SigningKey | None = None
    if not args.no_sign and not args.dry_run:
        try:
            signing_key = SigningKey.from_env()
            logger.info("Signing key loaded from SABER_SIGNING_KEY_PATH")
        except FileNotFoundError:
            logger.warning(
                "No signing key found; proceeding unsigned. "
                "Run scripts/saber_keygen.py to generate a key."
            )

    mode = "DRY RUN" if args.dry_run else "LIVE"
    logger.info(
        "S.A.B.E.R. Phase 1 migration starting (%s) -- corpora: %s",
        mode,
        ", ".join(args.corpus),
    )

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            pool.submit(
                migrate_corpus,
                corpus_id,
                store,
                audit_log,
                manifests_dir,
                signing_key,
                args.dry_run,
            ): corpus_id
            for corpus_id in args.corpus
        }
        for future in concurrent.futures.as_completed(futures):
            corpus_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logger.error("[%s] Unhandled exception: %s", corpus_id, exc)

    print("\n" + "=" * 60)
    print(f"S.A.B.E.R. Phase 1 Migration Summary ({mode})")
    print("=" * 60)
    total_migrated = 0
    total_failed = 0
    for r in sorted(results, key=lambda x: x["corpus_id"]):
        status = "OK" if r["failed"] == 0 else "PARTIAL"
        print(
            f"  {r['corpus_id']:<12} {status:<8} "
            f"{r['migrated']:>4} provisions  "
            f"({r['elapsed_s']:.3f}s)"
        )
        total_migrated += r["migrated"]
        total_failed += r["failed"]

    if not args.dry_run:
        root = audit_log.root_hash()
        print(f"\n  Audit root hash: {root}")
        print(f"  Blobs in store:  {store.blob_count()}")

    print(f"\n  Total migrated:  {total_migrated}")
    if total_failed:
        print(f"  Total failed:    {total_failed}  (see log above)")
    print("=" * 60)

    if total_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
