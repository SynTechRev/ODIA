# src/oraculus_di_auditor/emcs16/harmonization.py
from __future__ import annotations


class HarmonizationCore:
    """Merge harmonics, probabilities, and CRI into a meta_harmonic field."""

    def __init__(self):
        # weights can be config knobs later
        self.w_harm = 0.4
        self.w_prob = 0.35
        self.w_cri = 0.25

    def fuse(
        self,
        harmonics: dict[str, float],
        probabilities: dict[str, float],
        cri: dict[str, float],
    ) -> dict[str, float]:
        # simple fusion: normalize and combine by keys (stringified)
        out: dict[str, float] = {}
        # normalize harmonic by average
        avg_h = sum(harmonics.values()) / len(harmonics) if harmonics else 0.0
        for k, v in probabilities.items():
            cri_v = cri.get(k, 0.5)
            # simple score: weighted average of normalized components
            score = self.w_harm * avg_h + self.w_prob * v + self.w_cri * cri_v
            out[str(k)] = round(max(0.0, min(1.0, score)), 4)
        return out

    def emergent_patterns(self, meta_field: dict[str, float]) -> dict[str, float]:
        # detect simple motifs: high/low ranges
        patterns = {}
        for k, v in meta_field.items():
            if v >= 0.85:
                patterns[f"{k}:hotspot"] = v
            elif v <= 0.15:
                patterns[f"{k}:coldspot"] = v
        return patterns

    def score_harmony(self, component_id: str, meta_field: dict[str, float]) -> float:
        return meta_field.get(component_id, 0.0)
