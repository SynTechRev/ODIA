#!/usr/bin/env python3
"""S.A.B.E.R. key generation script.

Generates an Ed25519 + ML-DSA-65 (if liboqs available) signing key pair and
saves it to the directory specified by SABER_SIGNING_KEY_PATH, or to the
default path ~/.odia/saber/signing.key if the env var is not set.

Usage:
    python scripts/saber_keygen.py
    python scripts/saber_keygen.py --path /custom/path/to/keydir

ELECT-3: Architect sole control, key file at env path (Phase 1 implementation).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from oraculus_di_auditor.legal.saber.signing import (
    _ALGORITHM_ED25519_ONLY,
    _ALGORITHM_HYBRID,
    _ML_DSA_AVAILABLE,
    SigningKey,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate S.A.B.E.R. signing key pair")
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Key directory path (overrides SABER_SIGNING_KEY_PATH and default)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing key without prompting",
    )
    args = parser.parse_args()

    if args.path:
        key_dir = args.path.expanduser()
    elif "SABER_SIGNING_KEY_PATH" in os.environ:
        key_dir = Path(os.environ["SABER_SIGNING_KEY_PATH"]).expanduser()
    else:
        key_dir = Path("~/.odia/saber/signing.key").expanduser()

    if (key_dir / "ed25519.pem").exists() and not args.force:
        print(f"Key already exists at: {key_dir}")
        print("Use --force to overwrite. Aborting.")
        sys.exit(1)

    print(f"Generating S.A.B.E.R. signing key pair at: {key_dir}")
    if _ML_DSA_AVAILABLE:
        print(f"  Algorithm: {_ALGORITHM_HYBRID} (Ed25519 + ML-DSA-65 / FIPS 204)")
    else:
        print(f"  Algorithm: {_ALGORITHM_ED25519_ONLY} (Ed25519 only)")
        print(
            "  Note: install liboqs-python to enable ML-DSA-65 post-quantum component:"
            "\n  pip install liboqs-python"
        )

    key = SigningKey.generate()
    key.save(key_dir)

    pub_path = key_dir / "public.json"
    print("\nKey generation complete.")
    print(f"  Private key: {key_dir}/ed25519.pem")
    if _ML_DSA_AVAILABLE:
        print(f"  ML-DSA key:  {key_dir}/ml_dsa.bin")
    print(f"  Public bundle: {pub_path}")
    print(
        f"\nDistribute {pub_path} to anyone who needs to verify S.A.B.E.R. signatures."
    )
    print("Keep the key directory private. Do not commit it to Git.")
    print(
        f"\nSet environment variable to use this key:"
        f"\n  SABER_SIGNING_KEY_PATH={key_dir}"
    )


if __name__ == "__main__":
    main()
