# src/oraculus_di_auditor/rgk18/utils.py
"""Utility functions for Phase 18: deterministic seeding and canonicalization."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize_input(obj: Any) -> dict[str, Any]:
    """Canonicalize input for deterministic hashing.

    - Sorts dictionaries by key
    - Normalizes floats to 6 decimal places
    - Strips ephemeral fields like timestamps (if present in top-level)

    Args:
        obj: Input object to canonicalize

    Returns:
        Canonicalized dictionary
    """
    if not isinstance(obj, dict):
        # Wrap non-dict in a dict
        obj = {"value": obj}

    # Create a deep copy and normalize
    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            # Sort keys and recursively normalize
            return {k: normalize(v) for k, v in sorted(item.items())}
        elif isinstance(item, list):
            return [normalize(x) for x in item]
        elif isinstance(item, float):
            # Normalize to 6 decimal places
            return round(item, 6)
        else:
            return item

    normalized = normalize(obj)

    # Strip ephemeral fields from top level only
    ephemeral_fields = {"timestamp", "runtime_id", "process_id"}
    if isinstance(normalized, dict):
        normalized = {k: v for k, v in normalized.items() if k not in ephemeral_fields}

    return normalized


def seed_from_input(obj: Any) -> int:
    """Derive deterministic seed from input object.

    Uses SHA256 hash of canonical JSON representation.

    Args:
        obj: Input object to derive seed from

    Returns:
        Integer seed (first 16 hex digits of SHA256)
    """
    canonical = canonicalize_input(obj)
    json_str = json.dumps(canonical, sort_keys=True, default=str)
    hash_hex = hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    return int(hash_hex[:16], 16)


def sha256_hex(obj: Any) -> str:
    """Generate deterministic SHA256 hex string from object.

    Args:
        obj: Input object to hash

    Returns:
        SHA256 hex digest
    """
    json_str = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


class DeterministicRNG:
    """Simple Linear Congruential Generator for deterministic random numbers.

    Provides deterministic pseudo-random behavior for tie-breaking.
    """

    def __init__(self, seed: int):
        """Initialize RNG with seed.

        Args:
            seed: Initial seed value
        """
        self.state = seed & 0xFFFFFFFFFFFFFFFF  # Keep 64-bit

    def next_int(self, max_val: int) -> int:
        """Generate next random integer in range [0, max_val).

        Args:
            max_val: Maximum value (exclusive)

        Returns:
            Random integer in [0, max_val)
        """
        # LCG parameters (from Numerical Recipes)
        a = 1664525
        c = 1013904223
        m = 2**32
        self.state = (a * self.state + c) % m
        return self.state % max_val

    def next_float(self) -> float:
        """Generate next random float in range [0.0, 1.0).

        Returns:
            Random float in [0.0, 1.0)
        """
        return self.next_int(1000000) / 1000000.0
