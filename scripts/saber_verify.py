#!/usr/bin/env python3
"""S.A.B.E.R. audit chain verification script.

Verifies the integrity of the audit log and content store after migration.

Usage:
    python scripts/saber_verify.py
    python scripts/saber_verify.py --store-path /custom/store/path
    python scripts/saber_verify.py --publish-checkpoint
    python scripts/saber_verify.py --publish-checkpoint --no-sign
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.legal.saber import AuditLog, ContentStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("saber.verify")

_DEFAULT_STORE = Path(__file__).parent.parent / "data" / "saber" / "store"
_DEFAULT_LOG = Path(__file__).parent.parent / "data" / "saber" / "audit" / "saber.log"
_DEFAULT_CHECKPOINTS = Path(__file__).parent.parent / "data" / "saber" / "checkpoints"


def _sign_checkpoint(cp_path: Path, root_hash: str) -> None:
    """Sign the checkpoint JSON with the architect key (hybrid when available)."""
    try:
        from oraculus_di_auditor.legal.saber.signing import SigningKey  # noqa: PLC0415

        key = SigningKey.from_env()
        sig = key.sign(root_hash.encode("utf-8"))

        cp_data = json.loads(cp_path.read_text(encoding="utf-8"))
        cp_data["signature"] = sig.to_dict()
        cp_path.write_text(json.dumps(cp_data, indent=2), encoding="utf-8")

        print(f"         Signed with: {sig.algorithm}")
        print(f"         Ed25519:     {sig.ed25519_sig.hex()[:32]}...")
        if sig.ml_dsa_sig:
            print(f"         ML-DSA-65:   {sig.ml_dsa_sig.hex()[:32]}...")
    except FileNotFoundError:
        print(
            "  [WARN] No signing key found; checkpoint unsigned. "
            "Set SABER_SIGNING_KEY_PATH or run: python scripts/saber_keygen.py"
        )
    except Exception as exc:
        print(f"  [WARN] Checkpoint signing failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="S.A.B.E.R. integrity verification")
    parser.add_argument("--store-path", type=Path, default=_DEFAULT_STORE)
    parser.add_argument(
        "--publish-checkpoint",
        action="store_true",
        help="Write a checkpoint JSON after verification",
    )
    parser.add_argument(
        "--no-sign",
        action="store_true",
        help="Skip checkpoint signing even if a key is available",
    )
    args = parser.parse_args()

    passed = 0
    failed = 0

    # Verify audit chain
    log = AuditLog(_DEFAULT_LOG)
    logger.info("Verifying audit chain: %s", _DEFAULT_LOG)
    chain_ok = log.verify_chain()
    if chain_ok:
        entry_count = log.entry_count()
        root = log.root_hash()
        print(f"  [PASS] Audit chain intact -- {entry_count} entries")
        print(f"         Root hash: {root}")
        passed += 1
    else:
        print("  [FAIL] Audit chain verification FAILED -- see log above")
        failed += 1

    # Verify content store blobs
    store = ContentStore(args.store_path)
    if not args.store_path.exists():
        print(f"  [SKIP] Store path does not exist: {args.store_path}")
    else:
        blob_count = store.blob_count()
        corpus_ids = store.corpus_ids()
        print(f"  [INFO] Content store: {blob_count} blobs, corpora: {corpus_ids}")
        corrupt = 0
        for corpus_id in corpus_ids:
            for citation in store.list_citations(corpus_id):
                result = store.resolve_citation(corpus_id, citation)
                if result is None:
                    corrupt += 1
                    logger.error("Missing blob for %s / %s", corpus_id, citation)
                    continue
                text, addr = result
                if not addr.verify(text):
                    corrupt += 1
                    logger.error("Hash mismatch for %s / %s", corpus_id, citation)
        if corrupt == 0:
            print("  [PASS] All blobs verified")
            passed += 1
        else:
            print(f"  [FAIL] {corrupt} corrupt blobs detected")
            failed += 1

    # Publish checkpoint if requested
    if args.publish_checkpoint and chain_ok:
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        cp_path = _DEFAULT_CHECKPOINTS / f"saber-audit-{ts}.json"
        root = log.write_checkpoint(cp_path)
        print(f"  [INFO] Checkpoint written: {cp_path}")

        # Sign checkpoint with hybrid key when available
        if not args.no_sign:
            _sign_checkpoint(cp_path, root)

        print("         Publish to: https://github.com/SynTechRev/saber-audit-log")

    print(f"\n  Passed: {passed}  Failed: {failed}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
