# src/oraculus_di_auditor/emcs16/self_modeling.py
from __future__ import annotations

import random
from typing import Any


def _seed_from_hash(data_hash: str) -> int:
    # deterministic integer seed within int range
    return int(data_hash[:16], 16)


class RecursiveSelfModeling:
    """Builds a compact self-model and deterministic projection."""

    def __init__(self, time_depth: int = 12):
        self.time_depth = time_depth

    def build_meta_state(self, system_state: dict[str, Any]) -> dict[str, Any]:
        # compact summary: counts, keys, simple topology hint
        components = system_state.get("components", {}) or {}
        comp_count = len(components)
        keys = sorted(list(system_state.keys()))
        return {
            "component_count": comp_count,
            "topology_signature": "-".join(keys[:3]),
            "component_ids": list(components.keys())[:10],
        }

    def simulate_projection(
        self, meta_state: dict[str, Any], seed: int
    ) -> dict[str, Any]:
        """Deterministic projection created by seeded RNG based on input hash."""
        rng = random.Random(seed)
        # Simple projection: vary a 'stability' score across time depth
        projections = []
        base_stability = 0.8
        state = dict(meta_state)
        for t in range(self.time_depth):
            # deterministic noise
            noise = (rng.random() - 0.5) * 0.1
            stability = max(0.0, min(1.0, base_stability + noise - 0.01 * t))
            projections.append({"t": t, "stability": round(stability, 4)})
            # deterministic update to state (lightweight)
            state["last_t"] = t
        return {"projections": projections, "final_state": state}

    def build_and_project(
        self, system_state: dict[str, Any], input_hash: str
    ) -> dict[str, Any]:
        meta = self.build_meta_state(system_state)
        seed = _seed_from_hash(input_hash)
        projection = self.simulate_projection(meta, seed)
        return {"meta_state": meta, "projection": projection, "seed": seed}
