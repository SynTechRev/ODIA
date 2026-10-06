#!/usr/bin/env python3
"""Add ML-DSA-65 post-quantum component to an Ed25519-only S.A.B.E.R. signing key.

Preserves the existing Ed25519 private key and all prior Ed25519-only signatures.
Run once after liboqs-python has a working native oqs.dll (CMake + MinGW build).

Usage:
    python scripts/saber_upgrade_key.py
    python scripts/saber_upgrade_key.py --key-path /custom/key/path
    python scripts/saber_upgrade_key.py --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("saber.upgrade_key")

_DEFAULT_KEY_PATH = Path("~/.odia/saber/signing.key").expanduser()
_DEFAULT_LOG = Path(__file__).parent.parent / "data" / "saber" / "audit" / "saber.log"
_ALGORITHM_HYBRID = "ed25519+ml-dsa-65"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upgrade SABER signing key: add ML-DSA-65 post-quantum component"
    )
    parser.add_argument(
        "--key-path",
        type=Path,
        default=_DEFAULT_KEY_PATH,
        help=f"Key directory (default: {_DEFAULT_KEY_PATH})",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=_DEFAULT_LOG,
        help="Audit log path",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without writing any files",
    )
    args = parser.parse_args()

    # Import liboqs -- require it to be available
    try:
        import oqs  # type: ignore[import]

        ml_dsa_alg = "ML-DSA-65"
        if ml_dsa_alg not in oqs.get_enabled_sig_mechanisms():
            print(f"ERROR: {ml_dsa_alg} not in oqs.get_enabled_sig_mechanisms()")
            sys.exit(1)
    except ImportError:
        print(
            "ERROR: liboqs-python not installed.\n"
            "Build liboqs from source and install liboqs-python:\n"
            "  pip install liboqs-python"
        )
        sys.exit(1)

    key_dir = args.key_path
    if not key_dir.exists():
        print(f"ERROR: Key directory not found: {key_dir}")
        print("Generate a key first: python scripts/saber_keygen.py")
        sys.exit(1)

    pub_path = key_dir / "public.json"
    ml_path = key_dir / "ml_dsa.bin"

    if not pub_path.exists():
        print(f"ERROR: {pub_path} not found -- not a valid SABER key directory")
        sys.exit(1)

    pub = json.loads(pub_path.read_text(encoding="utf-8"))

    if pub.get("ml_dsa_pub") and ml_path.exists():
        print("Key already has ML-DSA-65 component.")
        print(f"  Key dir:   {key_dir}")
        print(f"  Algorithm: {pub['algorithm']}")
        print(f"  ML-DSA pub: {pub['ml_dsa_pub'][:32]}...")
        sys.exit(0)

    print(f"Key directory:     {key_dir}")
    print(f"Current algorithm: {pub['algorithm']}")
    print(f"Dry run:           {args.dry_run}")

    # Generate ML-DSA-65 keypair
    ml = oqs.Signature(ml_dsa_alg)
    ml_pub: bytes = ml.generate_keypair()
    ml_sk: bytes = ml.secret_key

    pub_fingerprint = _sha256(ml_pub)
    print("\nGenerated ML-DSA-65 keypair:")
    print(f"  Public key:  {ml_pub.hex()[:32]}... ({len(ml_pub)} bytes)")
    print(f"  Secret key:  {len(ml_sk)} bytes")
    print(f"  Fingerprint: {pub_fingerprint[:16]}...")

    if args.dry_run:
        print("\n[DRY RUN] Would write:")
        print(f"  {ml_path}  ({len(ml_sk)} bytes)")
        print(f"  {pub_path}  (algorithm: {_ALGORITHM_HYBRID})")
        print("  audit log key-upgrade entry")
        return

    # Write ML-DSA secret key
    ml_path.write_bytes(ml_sk)
    logger.info("Written ML-DSA secret key: %s", ml_path)

    # Update public.json
    pub["algorithm"] = _ALGORITHM_HYBRID
    pub["ml_dsa_pub"] = ml_pub.hex()
    pub_path.write_text(json.dumps(pub, indent=2), encoding="utf-8")
    logger.info("Updated public.json: algorithm=%s", _ALGORITHM_HYBRID)

    # Append audit log entry recording the upgrade
    from oraculus_di_auditor.legal.saber.audit_log import AuditLog  # noqa: PLC0415

    log = AuditLog(args.log_path)
    entry = log.append(
        op="key-upgrade",
        corpus_id="saber",
        citation=ml_dsa_alg,
        sha256=pub_fingerprint,
        result="ok",
    )
    logger.info("Audit log: seq=%d key-upgrade entry appended", entry["seq"])

    print("\nUpgrade complete.")
    print(f"  Algorithm:    {pub['algorithm']}")
    print(f"  ML-DSA pub:   {ml_pub.hex()[:48]}...")
    print(f"  Audit seq:    {entry['seq']}")
    print("\nNext step -- re-sign the Phase 1 checkpoint with hybrid key:")
    print("  python scripts/saber_verify.py --publish-checkpoint")


if __name__ == "__main__":
    main()
