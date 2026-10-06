"""S.A.B.E.R. Pillar 4 -- Crypto-agile hybrid signature framework.

Primary primitive:   Ed25519 (PyCA cryptography -- always available via python-jose dep)
Secondary primitive: ML-DSA-65 (liboqs-python -- optional, FIPS 204 / CRYSTALS-Dilithium)

A HybridSignature carries both components when liboqs is present.
Either component alone is sufficient for verification; both must be valid
when both are present. This hybrid protects against two independent failure
modes simultaneously:
  (a) A future break in Ed25519 -- the ML-DSA component still verifies.
  (b) A future break in lattice cryptography -- Ed25519 still verifies.

Usage:
    key = SigningKey.generate()
    key.save(Path("~/.odia/saber/signing.key").expanduser())

    sig = key.sign(b"corpus manifest bytes")
    assert key.public_key().verify(b"corpus manifest bytes", sig)

Key directory layout (written by .save()):
    <key_dir>/
        ed25519.pem     -- PKCS8 PEM, Ed25519 private key
        ml_dsa.bin      -- Raw ML-DSA-65 secret key (omitted when liboqs absent)
        public.json     -- Public key bundle; distribute to verifiers
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
)

logger = logging.getLogger(__name__)

try:
    import oqs  # liboqs-python

    _ML_DSA_AVAILABLE = True
    _ML_DSA_ALG = "ML-DSA-65"
except ImportError:
    oqs = None  # type: ignore[assignment]
    _ML_DSA_AVAILABLE = False
    _ML_DSA_ALG = None
    logger.debug(
        "liboqs-python not installed; S.A.B.E.R. signing operates Ed25519-only. "
        "To enable post-quantum ML-DSA-65: pip install liboqs-python"
    )

_ALGORITHM_HYBRID = "ed25519+ml-dsa-65"
_ALGORITHM_ED25519_ONLY = "ed25519"


@dataclass(frozen=True)
class HybridSignature:
    """Dual-algorithm signature over an arbitrary byte payload."""

    ed25519_sig: bytes
    ml_dsa_sig: bytes | None  # None when liboqs not installed
    algorithm: str  # "ed25519+ml-dsa-65" | "ed25519"

    def to_dict(self) -> dict:
        return {
            "algorithm": self.algorithm,
            "ed25519_sig": self.ed25519_sig.hex(),
            "ml_dsa_sig": self.ml_dsa_sig.hex() if self.ml_dsa_sig else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> HybridSignature:
        return cls(
            ed25519_sig=bytes.fromhex(d["ed25519_sig"]),
            ml_dsa_sig=bytes.fromhex(d["ml_dsa_sig"]) if d.get("ml_dsa_sig") else None,
            algorithm=d["algorithm"],
        )


class SigningKey:
    """Ed25519 + optional ML-DSA-65 private key pair.

    The oqs.Signature API does not expose a public-key accessor after the fact --
    generate_keypair() returns the public key bytes but there is no way to retrieve
    them from the object later. So _ml_pub is tracked explicitly and is the only
    authoritative source of the ML-DSA public key for both save() and public_key().
    """

    def __init__(
        self,
        ed25519_private: Ed25519PrivateKey,
        ml_dsa_signer: object | None = None,
        ml_dsa_pub: bytes | None = None,
    ) -> None:
        self._ed = ed25519_private
        self._ml = ml_dsa_signer  # oqs.Signature instance
        self._ml_pub = (
            ml_dsa_pub  # authoritative public key bytes; None when Ed25519-only
        )

    @classmethod
    def generate(cls) -> SigningKey:
        """Generate a fresh hybrid key pair."""
        ed = Ed25519PrivateKey.generate()
        ml = None
        ml_pub = None
        if _ML_DSA_AVAILABLE:
            ml = oqs.Signature(_ML_DSA_ALG)
            ml_pub = ml.generate_keypair()  # returns public key bytes
        return cls(ed, ml, ml_pub)

    @classmethod
    def load(cls, path: Path | str) -> SigningKey:
        """Load from the key directory written by .save()."""
        p = Path(path)
        ed_pem = (p / "ed25519.pem").read_bytes()
        ed = load_pem_private_key(ed_pem, password=None)
        ml = None
        ml_pub = None
        ml_path = p / "ml_dsa.bin"
        if _ML_DSA_AVAILABLE and ml_path.exists():
            raw_sk = ml_path.read_bytes()
            ml = oqs.Signature(_ML_DSA_ALG)
            # generate_keypair() is required to initialise the oqs object; the
            # throwaway public key is immediately discarded.  The stored secret key
            # is then overwritten with the saved one.
            ml.generate_keypair()
            ml.secret_key = raw_sk
            # Public key must come from public.json -- oqs has no pk-from-sk export.
            pub_json = json.loads((p / "public.json").read_text(encoding="utf-8"))
            ml_pub_hex = pub_json.get("ml_dsa_pub")
            if ml_pub_hex:
                ml_pub = bytes.fromhex(ml_pub_hex)
        return cls(ed, ml, ml_pub)

    @classmethod
    def from_env(cls) -> SigningKey:
        """Load from the path at SABER_SIGNING_KEY_PATH (ELECT-3 default env var)."""
        raw = os.environ.get("SABER_SIGNING_KEY_PATH")
        if raw:
            return cls.load(Path(raw).expanduser())
        default = Path("~/.odia/saber/signing.key").expanduser()
        if default.exists():
            return cls.load(default)
        raise FileNotFoundError(
            "No signing key found. Set SABER_SIGNING_KEY_PATH or run: "
            "python scripts/saber_keygen.py"
        )

    def save(self, path: Path | str) -> None:
        """Write key material to a directory. Idempotent."""
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        pem = self._ed.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        (p / "ed25519.pem").write_bytes(pem)
        if self._ml is not None:
            (p / "ml_dsa.bin").write_bytes(self._ml.secret_key)
        pub_bundle = {
            "algorithm": _ALGORITHM_HYBRID if self._ml else _ALGORITHM_ED25519_ONLY,
            "ed25519_pub": self._ed.public_key()
            .public_bytes(Encoding.Raw, PublicFormat.Raw)
            .hex(),
            "ml_dsa_pub": self._ml_pub.hex() if self._ml_pub is not None else None,
        }
        (p / "public.json").write_text(
            json.dumps(pub_bundle, indent=2), encoding="utf-8"
        )

    def sign(self, data: bytes) -> HybridSignature:
        """Sign data with all available algorithms."""
        ed_sig = self._ed.sign(data)
        ml_sig = None
        if self._ml is not None:
            ml_sig = self._ml.sign(data)
        return HybridSignature(
            ed25519_sig=ed_sig,
            ml_dsa_sig=ml_sig,
            algorithm=_ALGORITHM_HYBRID if ml_sig else _ALGORITHM_ED25519_ONLY,
        )

    def public_key(self) -> VerifyKey:
        return VerifyKey(ed25519_pub=self._ed.public_key(), ml_dsa_pub=self._ml_pub)


class VerifyKey:
    """Public key material for signature verification."""

    def __init__(
        self,
        ed25519_pub: Ed25519PublicKey,
        ml_dsa_pub: bytes | None = None,
    ) -> None:
        self._ed = ed25519_pub
        self._ml_pub = ml_dsa_pub

    def verify(self, data: bytes, sig: HybridSignature) -> bool:
        """Returns True only when all present signature components are valid.

        Conservative rule: if an ML-DSA signature is present in sig but
        liboqs is not available locally, verification fails. Install
        liboqs-python to verify hybrid signatures.
        """
        try:
            self._ed.verify(sig.ed25519_sig, data)
        except Exception:
            return False
        if sig.ml_dsa_sig is not None:
            if not _ML_DSA_AVAILABLE or self._ml_pub is None:
                logger.warning(
                    "ML-DSA component present in signature but liboqs unavailable; "
                    "verification fails conservatively. Install liboqs-python."
                )
                return False
            verifier = oqs.Signature(_ML_DSA_ALG)
            ok = verifier.verify(data, sig.ml_dsa_sig, self._ml_pub)
            if not ok:
                return False
        return True

    @classmethod
    def load(cls, path: Path | str) -> VerifyKey:
        """Load from the public.json written by SigningKey.save()."""
        p = Path(path)
        pub = json.loads((p / "public.json").read_text(encoding="utf-8"))
        ed_raw = bytes.fromhex(pub["ed25519_pub"])
        ed = Ed25519PublicKey.from_public_bytes(ed_raw)
        ml_pub = bytes.fromhex(pub["ml_dsa_pub"]) if pub.get("ml_dsa_pub") else None
        return cls(ed25519_pub=ed, ml_dsa_pub=ml_pub)
