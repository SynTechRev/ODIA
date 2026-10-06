"""S.A.B.E.R. Pillar 2 -- Reproducible loader manifest.

Records the exact state of each corpus ingest so any independent party can
verify that the same source material, loaded by the same code, produces the
same content store snapshot.

A LoaderManifest proves:
  (a) which loader code produced the snapshot (loader_hash)
  (b) what source material was loaded (source_description + source_hash)
  (c) the resulting snapshot state (snapshot_hash + provision_count)
  (d) the environment at load time (Python version, liboqs availability)
  (e) the Architect's authorization (HybridSignature over the payload)

Manifests are written to <store_root>/manifests/<corpus_id>-<ts>.json.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

from .signing import SigningKey


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_loader_module(corpus_id: str) -> str:
    """Hash the source file of a CorpusLoader module by corpus_id."""
    module_name = f"oraculus_di_auditor.legal.{corpus_id}_corpus"
    try:
        spec = importlib.util.find_spec(module_name)
        if spec and spec.origin:
            return _sha256_file(Path(spec.origin))
    except (ModuleNotFoundError, ValueError):
        pass
    return "unavailable"


class LoaderManifest:
    """Immutable record of one corpus ingest event."""

    def __init__(self, data: dict) -> None:
        self._data = data

    @classmethod
    def record(
        cls,
        corpus_id: str,
        source_description: str,
        source_hash: str,
        snapshot_hash: str,
        provision_count: int,
        signing_key: SigningKey | None = None,
    ) -> LoaderManifest:
        """Build and optionally sign a manifest for a completed corpus ingest."""
        env = {
            "python": sys.version,
            "platform": platform.platform(),
            "liboqs_available": False,
        }
        try:
            import oqs  # noqa: F401

            env["liboqs_available"] = True
        except ImportError:
            pass

        data: dict = {
            "manifest_version": "1.0",
            "saber_manifest": True,
            "corpus_id": corpus_id,
            "loader_hash": _hash_loader_module(corpus_id),
            "source_description": source_description,
            "source_hash": source_hash,
            "snapshot_hash": snapshot_hash,
            "provision_count": provision_count,
            "loaded_at": datetime.now(UTC).isoformat(),
            "loader_env": env,
            "signature": None,
        }

        if signing_key is not None:
            payload = json.dumps(
                {k: v for k, v in data.items() if k != "signature"},
                sort_keys=True,
            ).encode("utf-8")
            sig = signing_key.sign(payload)
            data["signature"] = sig.to_dict()

        return cls(data)

    def verify_signature(self) -> bool:
        """Return True if the manifest carries a valid Architect signature.

        Requires the corresponding VerifyKey; this method checks structural
        integrity only (signature field present and non-null).
        Use VerifyKey.verify() for full cryptographic verification.
        """
        return bool(self._data.get("signature"))

    def to_dict(self) -> dict:
        return dict(self._data)

    def save(self, manifests_dir: Path | str) -> Path:
        """Write to <manifests_dir>/<corpus_id>-<ts>.json."""
        d = Path(manifests_dir)
        d.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = d / f"{self._data['corpus_id']}-{ts}.json"
        path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path | str) -> LoaderManifest:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(data)

    @property
    def corpus_id(self) -> str:
        return self._data["corpus_id"]

    @property
    def snapshot_hash(self) -> str:
        return self._data["snapshot_hash"]

    @property
    def provision_count(self) -> int:
        return self._data["provision_count"]

    @property
    def loaded_at(self) -> str:
        return self._data["loaded_at"]
