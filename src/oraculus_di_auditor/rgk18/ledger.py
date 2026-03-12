# src/oraculus_di_auditor/rgk18/ledger.py
"""Certified immutable decision ledger for RGK-18."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .constants import LEDGER_SIGNATURE_KEY
from .schemas import LedgerEntry


class Ledger:
    """Append-only, cryptographically-signed decision ledger."""

    def __init__(self, db_adapter: Any | None = None):
        """Initialize ledger.

        Args:
            db_adapter: Optional database adapter for persistence
        """
        self.db_adapter = db_adapter
        self.entries: list[LedgerEntry] = []
        self.last_signature = self._init_signature()

    def _init_signature(self) -> str:
        """Initialize chain signature.

        Returns:
            Initial signature based on ledger key
        """
        return hashlib.sha256(LEDGER_SIGNATURE_KEY.encode("utf-8")).hexdigest()

    def append(self, entry_data: dict[str, Any]) -> LedgerEntry:
        """Append a new entry to the ledger.

        Args:
            entry_data: Entry data (will be converted to LedgerEntry)

        Returns:
            Created LedgerEntry with signature
        """
        # Create entry payload for signature
        payload = {
            "entry_id": entry_data.get("entry_id"),
            "input_hash": entry_data.get("input_hash"),
            "decision": (
                entry_data["decision"].model_dump()
                if hasattr(entry_data["decision"], "model_dump")
                else entry_data["decision"]
            ),
            "score": (
                entry_data["score"].model_dump()
                if hasattr(entry_data["score"], "model_dump")
                else entry_data["score"]
            ),
            "policies_checked": [
                (p.model_dump() if hasattr(p, "model_dump") else p)
                for p in entry_data.get("policies_checked", [])
            ],
            "provenance": entry_data.get("provenance", {}),
        }

        # Compute chain signature
        signature = self._compute_signature(payload)

        # Create ledger entry
        entry = LedgerEntry(
            entry_id=entry_data["entry_id"],
            input_hash=entry_data["input_hash"],
            decision=entry_data["decision"],
            score=entry_data["score"],
            policies_checked=entry_data.get("policies_checked", []),
            provenance=entry_data.get("provenance", {}),
            signature=signature,
        )

        # Store in memory
        self.entries.append(entry)
        self.last_signature = signature

        # Persist to DB if adapter is available
        if self.db_adapter:
            self._persist_entry(entry)

        return entry

    def _compute_signature(self, payload: dict[str, Any]) -> str:
        """Compute chain signature for payload.

        Args:
            payload: Entry payload

        Returns:
            SHA256 chain signature
        """
        # Chain: prev_signature + current_payload
        json_str = json.dumps(payload, sort_keys=True, default=str)
        combined = self.last_signature + json_str
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    def _persist_entry(self, entry: LedgerEntry) -> None:
        """Persist entry to database.

        Args:
            entry: Ledger entry to persist
        """
        # Placeholder for DB adapter integration
        # In production, this would call db_adapter.insert_ledger_entry(entry)
        pass

    def get_entry(self, entry_id: str) -> LedgerEntry | None:
        """Retrieve an entry by ID.

        Args:
            entry_id: Entry identifier

        Returns:
            LedgerEntry if found, None otherwise
        """
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def get_chain_proof(self, entry_id: str) -> list[LedgerEntry]:
        """Get chain proof for an entry (all entries up to and including it).

        Args:
            entry_id: Entry identifier

        Returns:
            List of ledger entries forming the chain
        """
        proof = []
        for entry in self.entries:
            proof.append(entry)
            if entry.entry_id == entry_id:
                break
        return proof

    def verify_chain(self) -> bool:
        """Verify integrity of the entire ledger chain.

        Returns:
            True if chain is valid, False otherwise
        """
        current_sig = self._init_signature()
        for entry in self.entries:
            # Reconstruct payload
            payload = {
                "entry_id": entry.entry_id,
                "input_hash": entry.input_hash,
                "decision": entry.decision.model_dump(),
                "score": entry.score.model_dump(),
                "policies_checked": [p.model_dump() for p in entry.policies_checked],
                "provenance": entry.provenance,
            }
            # Compute expected signature
            json_str = json.dumps(payload, sort_keys=True, default=str)
            combined = current_sig + json_str
            expected_sig = hashlib.sha256(combined.encode("utf-8")).hexdigest()

            if entry.signature != expected_sig:
                return False

            current_sig = entry.signature

        return True

    def get_all_entries(self) -> list[LedgerEntry]:
        """Get all ledger entries.

        Returns:
            List of all ledger entries
        """
        return self.entries.copy()
