"""S.A.B.E.R. Pillar 3 -- Append-only Merkle audit log.

Every ContentStore write operation appends one entry. Entries are linked by
including the SHA-256 of the previous entry, forming a hash chain. Any
retrospective modification of an entry invalidates the chain from that point
forward, making tampering detectable.

The log lives at <store_root>/audit/saber.log (JSONL, one entry per line).
The root hash is published to the SynTechRev public Git repo daily (ELECT-4).

Entry schema:
    {
      "seq":        0,
      "ts":         "2026-10-04T...",
      "op":         "init|put|verify|resolve|migrate|checkpoint|key-upgrade",
      "corpus_id":  "cpra",
      "citation":   "1798.121",
      "sha256":     "<content hash or null>",
      "result":     "ok|miss|fail",
      "prev_hash":  "0000...0000",
      "entry_hash": "<sha256 of above fields serialized with sorted keys>"
    }
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_GENESIS_PREV_HASH = "0" * 64  # all-zeros for the first entry's prev_hash


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class AuditLog:
    """Append-only Merkle audit log backed by a JSONL file.

    A threading.Lock serializes all appends so concurrent writes from
    multiple threads do not interleave. Reads (verify_chain, root_hash)
    are also locked so they see a consistent state.
    """

    def __init__(self, log_path: Path | str) -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(
        self,
        op: str,
        corpus_id: str,
        citation: str | None = None,
        sha256: str | None = None,
        result: str = "ok",
    ) -> dict:
        """Append one entry and return it.

        The entry_hash covers all fields except itself, so it functions as
        a commitment to the entire entry state.
        """
        with self._lock:
            prev = self._last_hash_locked()
            seq = self._count_locked()
            entry: dict = {
                "seq": seq,
                "ts": datetime.now(UTC).isoformat(),
                "op": op,
                "corpus_id": corpus_id,
                "citation": citation,
                "sha256": sha256,
                "result": result,
                "prev_hash": prev,
            }
            entry["entry_hash"] = _sha256(
                json.dumps(entry, sort_keys=True).encode("utf-8")
            )
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        return entry

    def verify_chain(self) -> bool:
        """Walk the full chain and verify every prev_hash link and entry_hash.

        Returns True if intact. False means tampering or corruption has
        occurred at or after the first invalid entry (logged at ERROR level).
        """
        if not self._path.exists():
            return True
        with self._lock:
            prev = _GENESIS_PREV_HASH
            with self._path.open(encoding="utf-8") as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    entry = json.loads(raw_line)
                    if entry.get("prev_hash") != prev:
                        logger.error(
                            "Audit chain broken at seq=%d: prev_hash mismatch",
                            entry.get("seq"),
                        )
                        return False
                    claimed = entry.pop("entry_hash")
                    expected = _sha256(
                        json.dumps(entry, sort_keys=True).encode("utf-8")
                    )
                    entry["entry_hash"] = claimed
                    if claimed != expected:
                        logger.error(
                            "Audit chain broken at seq=%d: entry_hash mismatch",
                            entry.get("seq"),
                        )
                        return False
                    prev = claimed
        return True

    def root_hash(self) -> str:
        """SHA-256 over the concatenated entry hashes, in sequence order.

        Equivalent to the root of a flat Merkle tree. Any modification,
        deletion, or reordering of entries changes the root hash.
        """
        hashes: list[bytes] = []
        if not self._path.exists():
            return _sha256(b"")
        with self._lock:
            with self._path.open(encoding="utf-8") as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if raw_line:
                        entry_hash = json.loads(raw_line)["entry_hash"]
                        hashes.append(bytes.fromhex(entry_hash))
        if not hashes:
            return _sha256(b"")
        return _sha256(b"".join(hashes))

    def entries(self) -> list[dict]:
        """Return all entries as a list. Used for checkpoint publication."""
        if not self._path.exists():
            return []
        with self._path.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def entry_count(self) -> int:
        if not self._path.exists():
            return 0
        with self._path.open(encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())

    def write_checkpoint(self, output_path: Path | str) -> str:
        """Write a publishable checkpoint JSON and return the root hash.

        The checkpoint file is suitable for daily publication to the
        SynTechRev public Git repository (ELECT-4).
        """
        with self._lock:
            root = self._root_hash_locked()
            checkpoint = {
                "saber_audit_checkpoint": True,
                "published_at": datetime.now(UTC).isoformat(),
                "entry_count": self._count_locked(),
                "root_hash": root,
            }
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(
                json.dumps(checkpoint, indent=2), encoding="utf-8"
            )
        logger.info("Checkpoint written: root_hash=%s to %s", root[:16], output_path)
        return root

    # ── Internal helpers (call only while _lock is held or from __init__) ────

    def _root_hash_locked(self) -> str:
        hashes: list[bytes] = []
        if not self._path.exists():
            return _sha256(b"")
        with self._path.open(encoding="utf-8") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if raw_line:
                    hashes.append(bytes.fromhex(json.loads(raw_line)["entry_hash"]))
        if not hashes:
            return _sha256(b"")
        return _sha256(b"".join(hashes))

    def _last_hash_locked(self) -> str:
        if not self._path.exists() or self._path.stat().st_size == 0:
            return _GENESIS_PREV_HASH
        last_line = None
        with self._path.open(encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    last_line = stripped
        if last_line is None:
            return _GENESIS_PREV_HASH
        return json.loads(last_line)["entry_hash"]

    def _count_locked(self) -> int:
        if not self._path.exists():
            return 0
        with self._path.open(encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
