# src/oraculus_di_auditor/emcs16/meta_supervisor.py
from __future__ import annotations

import hashlib
from typing import Any

# Configurable thresholds
COHERENCE_THRESHOLD = 0.5
CONTRADICTION_THRESHOLD = 0.3


def _sha256_hex(obj: Any) -> str:
    """Generate deterministic hash from object representation.

    Note: Using repr() for simplicity in this skeleton implementation.
    For production, consider json.dumps(obj, sort_keys=True) for more
    robust deterministic serialization.
    """
    h = hashlib.sha256()
    h.update(repr(obj).encode("utf8"))
    return h.hexdigest()


class MetaSupervisor:
    """Meta-Cognitive Supervisor - deterministic checks and recommendations."""

    def __init__(self, coherence_threshold: float = COHERENCE_THRESHOLD):
        self.coherence_threshold = coherence_threshold

    def validate_inputs(self, req: dict[str, Any]) -> tuple[bool, str]:
        # quick validation: required keys + input hash
        required = (
            "system_state",
            "phase12_harmonics",
            "phase13_probabilities",
            "phase14_outputs",
        )
        for r in required:
            if r not in req:
                return False, f"Missing required key: {r}"
        return True, _sha256_hex(req)

    def run_checks(self, req: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic supervision report."""
        ok, input_hash = self.validate_inputs(req)
        issues: list[dict[str, Any]] = []
        recommended: list[dict[str, Any]] = []

        # Simple coherence check: compare average harmonic vs average probability
        harmonics = req.get("phase12_harmonics", {}) or {}
        probs = req.get("phase13_probabilities", {}) or {}
        avg_h = sum(harmonics.values()) / len(harmonics) if harmonics else 0.0
        avg_p = sum(probs.values()) / len(probs) if probs else 0.0

        coherence_diff = abs(avg_h - avg_p)
        integrity_score = max(0.0, 1.0 - min(1.0, coherence_diff))

        if coherence_diff > self.coherence_threshold:
            issues.append({"id": "meta:coherence-mismatch", "diff": coherence_diff})
            recommended.append(
                {
                    "id": "rec:adjust-harmonics",
                    "description": (
                        "Consider re-weighting scalar harmonics to match "
                        "observed probabilities"
                    ),
                    "confidence": 0.6,
                    "estimated_effort_hours": 2.0,
                    "risk_level": "low",
                    "reversible": True,
                }
            )

        # Contradiction detection (very simple): compare CRI values if present
        cri = req.get("phase14_outputs", {}).get("cri_rankings", {})
        if cri:
            # deterministic minimal check
            avg_cri = sum(cri.values()) / (len(cri) or 1)
            if avg_cri < CONTRADICTION_THRESHOLD:
                issues.append({"id": "meta:cri-low", "avg_cri": avg_cri})

        report = {
            "input_hash": input_hash,
            "ok": ok,
            "issues": issues,
            "recommended_actions": recommended,
            "integrity_score": integrity_score,
        }
        return report
