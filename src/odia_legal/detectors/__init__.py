"""odia_legal.detectors — legal reasoning detectors (L-1 through L-10).

L-1: detect(doc) — Statutory Applicability (which statutes apply to a document)
L-2: detect(doc) — Procedural Compliance (CPRA timing/denial form, AB 481, JAG)
L-3: detect(doc) — Exemption Misapplication (CPRA, SB 1421, ALPR, catch-all)
L-5: detect(doc) — Federal Grant Compliance (JAG/Byrne, 2 CFR Part 200)
L-6: detect(doc) — Constitutional Implication (Fourth Amendment, Carpenter)
L-9: detect(doc) — Recodification Translation (CPRA § 6250 → § 7920.000)
"""

from odia_legal.detectors.l1_statutory_applicability import (
    detect as detect_l1_statutory_applicability,
)
from odia_legal.detectors.l2_procedural_compliance import (
    detect as detect_l2_procedural_compliance,
)
from odia_legal.detectors.l3_exemption_misapplication import (
    detect as detect_l3_exemption_misapplication,
)
from odia_legal.detectors.l5_federal_grant_compliance import (
    detect as detect_l5_federal_grant_compliance,
)
from odia_legal.detectors.l6_constitutional_implication import (
    detect as detect_l6_constitutional_implication,
)
from odia_legal.detectors.l9_recodification import detect as detect_l9_recodification

__all__ = [
    "detect_l1_statutory_applicability",
    "detect_l2_procedural_compliance",
    "detect_l3_exemption_misapplication",
    "detect_l5_federal_grant_compliance",
    "detect_l6_constitutional_implication",
    "detect_l9_recodification",
]
