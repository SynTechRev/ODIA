"""C.O.N.T.R.A. — Commercial Contract Asymmetry detector suite.

Extension of the O.D.I.A. platform into commercial adhesion contracts,
privacy notices, and terms-of-service analysis. Adds detector layers
L-11 through L-20 and the CASI scoring instrument.

Framework Version: 1.0 (August 2026)
"""

from .base import Detector, EvidenceSpan, Finding, Severity
from .l11_arbitration_architecture import L11ArbitrationArchitecture
from .l12_choice_of_law_forum import L12ChoiceOfLawForum
from .l13_unilateral_modification import L13UnilateralModification
from .l14_data_collection_depth import L14DataCollectionDepth
from .l15_data_retention import L15DataRetention
from .l16_onward_transfer import L16OnwardTransfer
from .l17_ml_ai_training import L17MlAiTraining
from .l18_remedy_foreclosure import L18RemedyForeclosure
from .l19_enforcement_asymmetry import L19EnforcementAsymmetry
from .l20_dark_pattern import L20DarkPattern

__all__ = [
    "Detector",
    "EvidenceSpan",
    "Finding",
    "Severity",
    "L11ArbitrationArchitecture",
    "L12ChoiceOfLawForum",
    "L13UnilateralModification",
    "L14DataCollectionDepth",
    "L15DataRetention",
    "L16OnwardTransfer",
    "L17MlAiTraining",
    "L18RemedyForeclosure",
    "L19EnforcementAsymmetry",
    "L20DarkPattern",
]
