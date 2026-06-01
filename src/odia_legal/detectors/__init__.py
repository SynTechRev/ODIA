"""odia_legal.detectors — legal reasoning detectors (L-1 through L-10).

L-9: detect(doc) — Recodification Translation (CPRA § 6250 → § 7920.000)
"""

from odia_legal.detectors.l9_recodification import detect as detect_l9_recodification

__all__ = ["detect_l9_recodification"]
