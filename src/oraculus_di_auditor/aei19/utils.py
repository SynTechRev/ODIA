# src/oraculus_di_auditor/aei19/utils.py
"""Utility functions for Phase 19 (AEI-19) deterministic operations."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_hex(obj: Any) -> str:
    """Generate deterministic SHA256 hash from object.

    Uses json.dumps with sort_keys=True for robust determinism.
    Follows the pattern established in Phase 17 and Phase 18.

    Args:
        obj: Object to hash (must be JSON-serializable)

    Returns:
        64-character hexadecimal SHA256 hash
    """
    json_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def canonicalize_input(data: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize input for deterministic hashing.

    Follows Phase 18 pattern:
    - Sorts dictionary keys
    - Rounds floats to 6 decimals
    - Strips ephemeral fields (timestamps, etc.)

    Args:
        data: Input dictionary to canonicalize

    Returns:
        Canonicalized dictionary ready for hashing
    """
    # Strip ephemeral fields
    ephemeral_keys = {"timestamp", "created_at", "updated_at"}
    canonical = {k: v for k, v in data.items() if k not in ephemeral_keys}

    # Recursively canonicalize nested structures
    def _canonicalize_value(v: Any) -> Any:
        if isinstance(v, float):
            return round(v, 6)
        elif isinstance(v, dict):
            return canonicalize_input(v)
        elif isinstance(v, list):
            return [_canonicalize_value(item) for item in v]
        else:
            return v

    return {k: _canonicalize_value(v) for k, v in canonical.items()}


# Bit mask for keeping seed positive and within valid range
_SEED_MASK = 0x7FFFFFFF  # 2^31 - 1 (max positive 32-bit integer)


def seed_from_input(data: dict[str, Any]) -> int:
    """Generate deterministic seed from input data.

    Follows Phase 18 pattern for deterministic pseudo-random operations.

    Args:
        data: Input dictionary

    Returns:
        Integer seed derived from input hash
    """
    canonical = canonicalize_input(data)
    hash_hex = sha256_hex(canonical)
    # Use first 16 hex chars as seed (64 bits)
    return int(hash_hex[:16], 16) & _SEED_MASK  # Keep positive for compatibility


class DeterministicRNG:
    """Deterministic pseudo-random number generator using Linear Congruential Generator.

    Follows Phase 18 pattern for deterministic tie-breaking and sampling.
    """

    def __init__(self, seed: int):
        """Initialize with seed.

        Args:
            seed: Integer seed for deterministic generation
        """
        self.state = seed
        # LCG parameters (same as Phase 18)
        self.a = 1664525
        self.c = 1013904223
        self.m = 2**32

    def next_int(self, max_val: int) -> int:
        """Generate next random integer in range [0, max_val).

        Args:
            max_val: Upper bound (exclusive)

        Returns:
            Random integer in range
        """
        self.state = (self.a * self.state + self.c) % self.m
        return self.state % max_val

    def next_float(self) -> float:
        """Generate next random float in range [0.0, 1.0).

        Returns:
            Random float
        """
        self.state = (self.a * self.state + self.c) % self.m
        return self.state / self.m

    def choice(self, items: list[Any]) -> Any:
        """Choose random item from list deterministically.

        Args:
            items: List to choose from

        Returns:
            Randomly selected item
        """
        if not items:
            raise ValueError("Cannot choose from empty list")
        idx = self.next_int(len(items))
        return items[idx]
