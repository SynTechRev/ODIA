"""odia_legal.detectors — legal reasoning detectors (L-1 through L-10).

L-1: detect(doc) — Statutory Applicability (which statutes apply to a document)
L-9: detect(doc) — Recodification Translation (CPRA § 6250 → § 7920.000)
"""

from odia_legal.detectors.l1_statutory_applicability import (
    detect as detect_l1_statutory_applicability,
)
from odia_legal.detectors.l9_recodification import detect as detect_l9_recodification

__all__ = ["detect_l1_statutory_applicability", "detect_l9_recodification"]
