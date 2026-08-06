"""L-17 ML/AI Training Use detector (sub-detectors A through F).

Identifies contract provisions that grant the drafter (or its licensees) the
right to use consumer data for machine-learning model training, fine-tuning,
or AI-system improvement.  Training grants are the highest-consequence data
use because they are often irrevocable, may propagate through model weights
without attribution, and cannot be meaningfully "deleted" post-training.

Sub-detectors:
  A -- Explicit training grant (CRITICAL) — perpetual, irrevocable language
  B -- Perpetual / irrevocable license for data use (CRITICAL)
  C -- Scope of training grant (broad across modalities)
  D -- Absence of opt-out mechanism for training use (negative detection)
  E -- Biometric data included in training scope (CRITICAL)
  F -- Ring Order AEC: no clear method to review/delete model contributions

Source: C.O.N.T.R.A. Framework V1.0 Section 4.7, Handoff Spec V1.0 Section 5.7
"""

from __future__ import annotations

import re
from typing import List

from . import anchors as A
from ._utils import make_finding, scan_pattern
from .base import Finding, Severity

_LAYER = "L-17"

# ---------------------------------------------------------------------------
# Patterns (operate on lowercased text)
# ---------------------------------------------------------------------------

_P_A = re.compile(
    r"\b(?:train(?:ing|ed)?\s+(?:our\s+)?(?:artificial\s+intelligence|ai|machine\s+learning|ml|"
    r"deep\s+learning|neural\s+network\w*|language\s+model\w*|generative\s+(?:ai|model)\w*"
    r"|large\s+language\s+model\w*|llm\w*|model\w*)\b.{0,100}\b(?:your\s+)?(?:data|information|content)"
    r"|use\s+(?:your\s+)?(?:data|information|content)\b.{0,100}\b(?:train|improve|fine.?tun|develop|"
    r"creat|build)\w*\b.{0,50}\b(?:artificial\s+intelligence|ai|machine\s+learning|ml|model\w*"
    r"|algorithm\w*|system\w*)\b"
    r"|(?:model|algorithm)\s+training\b.{0,100}\b(?:your\s+)?(?:data|content|information)"
    r"|grant\w*\b.{0,50}\b(?:us|we|company|platform)\b.{0,100}\b(?:train|improve|fine.?tun"
    r"|develop)\w*\b.{0,100}\b(?:model\w*|ai|machine\s+learning|algorithm\w*))\b",
    re.DOTALL,
)

_P_B = re.compile(
    r"\b(?:(?:perpetual|irrevocable|worldwide|royalty.?free|non.?exclusive|exclusive)"
    r"\b.{0,200}\b(?:license|right|permission|grant)\b"
    r"|(?:license|right|permission|grant)\b.{0,200}\b(?:perpetual|irrevocable|worldwide"
    r"|royalty.?free))\b",
    re.DOTALL,
)

_P_C = re.compile(
    r"\b(?:text(?:\s+and\s+image)?|image(?:\s+and\s+text)?|audio|video|multimodal|"
    r"across\s+(?:all\s+)?(?:modalities?|formats?|types?\s+of\s+(?:data|content))|"
    r"all\s+(?:types?\s+of\s+)?(?:data|content|information)\s+(?:you\s+)?(?:submit|upload|"
    r"provide|share|post)|any\s+(?:data|content|information)\s+you\s+(?:provide|submit|"
    r"upload|share|generate|create))\b",
    re.DOTALL,
)

_P_D_TRAIN = re.compile(
    r"\b(?:model\s+training"
    r"|train(?:ing|ed)?\s+(?:our\s+)?(?:ai|machine\s+learning|ml|model\w*|algorithm\w*)"
    r"|training\b.{0,80}\b(?:ai|machine\s+learning|ml|model|algorithm|neural)"
    r"|(?:ai|machine\s+learning|ml)\b.{0,80}\btraining"
    r"|use\b.{0,120}\b(?:personal\s+)?(?:information|data|content)\b.{0,120}\btraining\b)\b",
    re.DOTALL,
)

_P_D_OPTOUT = re.compile(
    r"\b(?:you\s+(?:may|can)\b.{0,100}\bopt.?out\b.{0,80}\b(?:ai|training|model|machine\s+learning)"
    r"|you\s+(?:may|can)\b.{0,100}\bexclude\b.{0,80}"
    r"\b(?:your\s+)?(?:data|content|information)\s+from\s+(?:training|model|ai)"
    r"|manage\s+(?:your\s+)?(?:training|ai|data)\s+(?:preference|setting|consent)"
    r"|you\s+may\s+(?:object\s+to|withdraw\s+consent\s+(?:from|for))\b.{0,80}"
    r"\b(?:ai|training|model)\b)\b",
    re.DOTALL,
)

_P_E_BIO = re.compile(
    r"\b(?:biometric|facial\s+recognition|fingerprint|retina|iris|voice\s+(?:print|pattern)"
    r"|face\s+(?:scan|template|embedding))\b"
)

_P_F_DELETE = re.compile(
    r"\b(?:delete\w*\s+(?:your\s+)?(?:data|information|content|model\s+(?:contribution|training))"
    r"|remove\w*\s+(?:your\s+)?(?:data|information|content)\s+from\s+(?:our\s+)?(?:model|training)"
    r"|data\s+(?:deletion|removal)\s+request)"
    r"|\bmodel\s+(?:retraining|update)\b.{0,100}\b(?:reflect|incorporat\w*)\s+deletion"
    r"|\byou\s+(?:may|can)\s+request\b.{0,100}\b(?:deletion|removal)\b.{0,100}\b(?:model|training)\b",
    re.DOTALL,
)

_REMEDY_TRAINING = ["CCPA_opt_out", "CPPA_complaint", "AG_complaint"]
_REMEDY_LICENSE = ["CCPA_opt_out", "CPPA_complaint"]
_REMEDY_BIO = ["CPPA_complaint", "AG_complaint", "CCPA_delete_request"]
_REMEDY_RING = ["RING_ORDER_compliance_review", "CPPA_complaint"]


class L17MlAiTraining:
    """L-17 detector: ML/AI Training Use (sub-detectors A through F)."""

    layer: str = _LAYER

    def __init__(self, llm_client=None) -> None:
        self._llm = llm_client

    def scan(self, doc_text: str, doc_meta: dict) -> List[Finding]:
        doc_hash = doc_meta.get("document_hash", "0" * 64)
        text_lower = doc_text.lower()
        findings: List[Finding] = []

        # A: explicit training grant
        findings += scan_pattern(
            _P_A, doc_text, _LAYER, "A", Severity.CRITICAL, doc_hash,
            A.CCPA_100, "data_extraction_depth", 7, _REMEDY_TRAINING,
            notes="Training grant -- model weights cannot be retroactively purged of consumer data.",
        )

        # B: perpetual / irrevocable license
        findings += scan_pattern(
            _P_B, doc_text, _LAYER, "B", Severity.CRITICAL, doc_hash,
            A.CCPA_120, "data_extraction_depth", 7, _REMEDY_LICENSE,
            notes="Perpetual / irrevocable license -- practical impossibility of data deletion.",
        )

        # C: broad modality scope
        findings += scan_pattern(
            _P_C, doc_text, _LAYER, "C", Severity.MEDIUM, doc_hash,
            A.CCPA_110, "data_extraction_depth", 2, _REMEDY_TRAINING,
            notes="Broad multi-modal training scope increases extraction depth.",
        )

        # D: training present but no opt-out path (negative detection)
        has_train = bool(_P_D_TRAIN.search(text_lower))
        has_optout = bool(_P_D_OPTOUT.search(text_lower))
        if has_train and not has_optout:
            m = _P_D_TRAIN.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER, sub="D", sev=Severity.HIGH, doc_hash=doc_hash,
                        text=doc_text, match_start=m.start(), match_end=m.end(),
                        anchor=A.CCPA_120, axis="data_extraction_depth", delta=4,
                        remedy_channels=_REMEDY_TRAINING,
                        notes="AI training grant present with no disclosed opt-out mechanism.",
                    )
                )

        # E: biometric in training scope (CRITICAL)
        has_train2 = bool(_P_A.search(text_lower))
        has_bio = bool(_P_E_BIO.search(text_lower))
        if has_train2 and has_bio:
            m = _P_E_BIO.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER, sub="E", sev=Severity.CRITICAL, doc_hash=doc_hash,
                        text=doc_text, match_start=m.start(), match_end=m.end(),
                        anchor=A.CCPA_121, axis="data_extraction_depth", delta=7,
                        remedy_channels=_REMEDY_BIO,
                        notes="Biometric data within AI training scope -- maximum extraction severity.",
                    )
                )

        # F: Ring Order AEC -- no deletion path for model contributions
        has_delete = bool(_P_F_DELETE.search(text_lower))
        if has_train and not has_delete:
            m = _P_D_TRAIN.search(text_lower)
            if m:
                findings.append(
                    make_finding(
                        layer=_LAYER, sub="F", sev=Severity.HIGH, doc_hash=doc_hash,
                        text=doc_text, match_start=m.start(), match_end=m.end(),
                        anchor=A.RING_ORDER, axis="data_extraction_depth", delta=4,
                        remedy_channels=_REMEDY_RING,
                        notes="Ring Order AEC: no clear process to review or remove model training contributions.",
                    )
                )

        return findings
