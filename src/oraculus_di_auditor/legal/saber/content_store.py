"""S.A.B.E.R. Pillar 1 -- Content-addressed immutable provision storage.

Every legal provision is identified by the SHA-256 hash of its UTF-8 content.
SHA3-512 is recorded as a secondary hash for crypto-agility (the store can
migrate primary algorithms without invalidating stored content).

Directory layout under store_root:
    blobs/                  one UTF-8 text file per unique provision: <sha256>.txt
    lookup/                 citation-to-hash mapping per corpus: <corpus_id>.json
    index.json              store metadata: created_at, corpus_ids, blob_count

Lookup table schema (lookup/<corpus_id>.json):
    {
      "corpus_id": "cpra",
      "entries": {
        "<canonical_citation>": {
          "sha256":         "<64 hex chars>",
          "sha3_512":       "<128 hex chars>",
          "effective_dates": {"2023-01-01": "<sha256_of_that_version>"},
          "latest":         "<sha256>"
        }
      },
      "table_sha256": "<sha256 of entries dict serialized with sorted keys>",
      "signature":    { ... }   // HybridSignature.to_dict() or null
    }
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path

from .signing import HybridSignature, SigningKey, VerifyKey

logger = logging.getLogger(__name__)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha3_512(data: bytes) -> str:
    return hashlib.sha3_512(data).hexdigest()


def _dual_hash(text: str) -> tuple[str, str]:
    """Return (sha256_hex, sha3_512_hex) for a provision text string."""
    raw = text.encode("utf-8")
    return _sha256(raw), _sha3_512(raw)


class ContentAddress:
    """Dual-hash address for a stored provision."""

    __slots__ = ("sha256", "sha3_512", "content_length")

    def __init__(self, sha256: str, sha3_512: str, content_length: int) -> None:
        self.sha256 = sha256
        self.sha3_512 = sha3_512
        self.content_length = content_length

    def to_dict(self) -> dict:
        return {
            "sha256": self.sha256,
            "sha3_512": self.sha3_512,
            "content_length": self.content_length,
        }

    def verify(self, text: str) -> bool:
        """Return True if text hashes match this address exactly."""
        s256, s3 = _dual_hash(text)
        return s256 == self.sha256 and s3 == self.sha3_512

    def __repr__(self) -> str:
        return (
            f"ContentAddress(sha256={self.sha256[:16]}..., len={self.content_length})"
        )


class ContentStore:
    """Content-addressed provision store backed by a local directory.

    Read operations are thread-safe. Write operations (put) should be
    serialized by the caller; the Phase 1 migration script is single-threaded.
    """

    def __init__(self, store_root: Path | str) -> None:
        self._root = Path(store_root)
        self._blobs = self._root / "blobs"
        self._lookup_dir = self._root / "lookup"
        self._index_path = self._root / "index.json"

    def initialize(self) -> None:
        """Create the directory structure. Idempotent."""
        self._blobs.mkdir(parents=True, exist_ok=True)
        self._lookup_dir.mkdir(parents=True, exist_ok=True)
        if not self._index_path.exists():
            meta = {
                "saber_store": True,
                "created_at": datetime.now(UTC).isoformat(),
                "corpus_ids": [],
                "blob_count": 0,
            }
            self._index_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            logger.info("Initialized S.A.B.E.R. content store at %s", self._root)

    def put(
        self,
        corpus_id: str,
        citation: str,
        text: str,
        effective_date: date | None = None,
        signing_key: SigningKey | None = None,
    ) -> ContentAddress:
        """Store a provision and return its content address.

        Storing identical content for the same citation is idempotent:
        the blob is not rewritten and the existing address is returned.
        Storing new content for an existing citation adds a version and
        updates latest.
        """
        sha256, sha3 = _dual_hash(text)
        addr = ContentAddress(sha256, sha3, len(text.encode("utf-8")))

        blob_path = self._blobs / f"{sha256}.txt"
        if not blob_path.exists():
            blob_path.write_text(text, encoding="utf-8")

        table = self._load_lookup(corpus_id)
        entry = table["entries"].get(citation)
        if entry is None:
            entry = {
                "sha256": sha256,
                "sha3_512": sha3,
                "effective_dates": {},
                "latest": sha256,
            }
            table["entries"][citation] = entry
        else:
            entry["latest"] = sha256

        if effective_date is not None:
            entry["effective_dates"][effective_date.isoformat()] = sha256

        table_payload = json.dumps(table["entries"], sort_keys=True).encode("utf-8")
        table["table_sha256"] = _sha256(table_payload)

        if signing_key is not None:
            sig = signing_key.sign(table["table_sha256"].encode("utf-8"))
            table["signature"] = sig.to_dict()

        lookup_path = self._lookup_dir / f"{corpus_id}.json"
        lookup_path.write_text(json.dumps(table, indent=2), encoding="utf-8")

        self._update_index(corpus_id)
        return addr

    def get(self, sha256: str) -> str | None:
        """Retrieve provision text by SHA-256 hash. Returns None on miss."""
        blob_path = self._blobs / f"{sha256}.txt"
        if not blob_path.exists():
            return None
        return blob_path.read_text(encoding="utf-8")

    def verify_blob(self, addr: ContentAddress) -> bool:
        """Verify that a blob still matches its expected dual hash."""
        text = self.get(addr.sha256)
        if text is None:
            return False
        return addr.verify(text)

    def resolve_citation(
        self,
        corpus_id: str,
        citation: str,
        as_of: date | None = None,
    ) -> tuple[str, ContentAddress] | None:
        """Resolve a citation to (text, address). Returns None on miss.

        When as_of is provided, returns the most recent version of the
        provision that was in effect on that date, not the latest version.
        """
        table = self._load_lookup(corpus_id)
        entry = table["entries"].get(citation)
        if entry is None:
            return None

        if as_of is not None and entry["effective_dates"]:
            candidates = [
                (date.fromisoformat(d), h)
                for d, h in entry["effective_dates"].items()
                if date.fromisoformat(d) <= as_of
            ]
            if not candidates:
                return None
            sha256 = max(candidates, key=lambda x: x[0])[1]
        else:
            sha256 = entry["latest"]

        text = self.get(sha256)
        if text is None:
            return None

        addr = ContentAddress(
            sha256=sha256,
            sha3_512=entry["sha3_512"],
            content_length=len(text.encode("utf-8")),
        )
        return text, addr

    def list_citations(self, corpus_id: str) -> list[str]:
        """Return all known citations for a corpus, sorted."""
        return sorted(self._load_lookup(corpus_id)["entries"].keys())

    def verify_lookup_signature(
        self,
        corpus_id: str,
        verify_key: VerifyKey,
    ) -> bool:
        """Verify the lookup table's Architect signature.

        Returns False if no signature is present or if the signature is invalid.
        """
        table = self._load_lookup(corpus_id)
        sig_dict = table.get("signature")
        if not sig_dict:
            return False
        actual_hash = _sha256(
            json.dumps(table["entries"], sort_keys=True).encode("utf-8")
        )
        if actual_hash != table.get("table_sha256"):
            logger.error("Lookup table_sha256 mismatch for corpus %s", corpus_id)
            return False
        sig = HybridSignature.from_dict(sig_dict)
        return verify_key.verify(actual_hash.encode("utf-8"), sig)

    def blob_count(self) -> int:
        return sum(1 for _ in self._blobs.glob("*.txt"))

    def corpus_ids(self) -> list[str]:
        """Return all corpus IDs that have lookup tables."""
        return [p.stem for p in self._lookup_dir.glob("*.json")]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _load_lookup(self, corpus_id: str) -> dict:
        path = self._lookup_dir / f"{corpus_id}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {
            "corpus_id": corpus_id,
            "entries": {},
            "table_sha256": "",
            "signature": None,
        }

    def _update_index(self, corpus_id: str) -> None:
        if not self._index_path.exists():
            return
        meta = json.loads(self._index_path.read_text(encoding="utf-8"))
        if corpus_id not in meta.get("corpus_ids", []):
            meta.setdefault("corpus_ids", []).append(corpus_id)
        meta["blob_count"] = self.blob_count()
        meta["updated_at"] = datetime.now(UTC).isoformat()
        self._index_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
