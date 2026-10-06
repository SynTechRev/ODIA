"""L-1 Statutory Applicability -- odia_legal Phase 2.

Determines which California and federal statutes apply to a given document
based on document type, jurisdiction class, and content signals.

Applicability rules (order matters -- each rule contributes independently):

  Tier 1 -- Universal (all California public agency documents):
    CPRA baseline: Cal. Gov. § 7920.000 et seq.

  Tier 2 -- Document-type triggers:
    Agendas / meeting minutes  → Brown Act (Cal. Gov. § 54950 et seq.)
    Records requests / denials → CPRA response statutes (§§ 7922.500, 7922.530)
    Grant agreements           → JAG (34 USC § 10152), COPS (34 USC § 10381)
    Contracts / MOUs           → Cal. Gov. § 53060 (special services contracts)

  Tier 3 -- Content signals:
    Surveillance technology    → AB 481 / SB 34 (Cal. Gov. § 7070 et seq.)
    Face recognition           → Cal. Civ. Code § 1798.90.55
    ALPR / license plate       → Cal. Veh. Code § 2413, Cal. Pen. § 832.18
    Arbitration clauses        → Cal. CCP § 1281.96
    AI / automated decision    → Cal. Gov. § 11546.45 (ADMT for state agencies)
    Body camera / BWC          → Cal. Pen. Code § 832.7, § 832.8

Output confidence thresholds:
  1.0 -- document_type and jurisdiction both known
  0.8 -- jurisdiction known, document_type generic/unknown
  0.6 -- inferred from text signals only
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)

# Tier 1 -- always applies to any California public agency document
_CPRA_BASELINE = "Cal. Gov. § 7920.000"

# Tier 2 -- document-type applicability map
_TYPE_STATUTES: dict[str, list[str]] = {
    "agenda": [
        "Cal. Gov. § 54950",  # Brown Act
        "Cal. Gov. § 54954.2",  # 72-hour agenda posting
    ],
    "meeting_minutes": [
        "Cal. Gov. § 54950",
        "Cal. Gov. § 54953.5",  # minutes and recordings
    ],
    "records_request": [
        "Cal. Gov. § 7922.500",  # 10-day response
        "Cal. Gov. § 7922.530",  # 14-day extension
    ],
    "records_denial": [
        "Cal. Gov. § 7922.500",
        "Cal. Gov. § 7923.000",  # exemption burden
    ],
    "grant_agreement": [
        "34 USC § 10152",  # JAG
        "34 USC § 10381",  # COPS
        "2 CFR Part 200",  # Uniform Guidance
    ],
    "contract": [
        "Cal. Gov. § 53060",  # special services contracts
    ],
    "mou": [
        "Cal. Gov. § 53060",
    ],
    "policy": [
        "Cal. Gov. § 7922.000",  # CPRA policy framework
    ],
    "annual_report": [
        "Cal. Gov. § 7072",  # AB 481 annual reporting
    ],
}

# Tier 3 -- content-signal triggers (compiled regex → list of statutes)
_SIGNAL_PATTERNS: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(
            r"\b(surveillance|CCTV|face.?recognition|facial.?recognition|Clearview|FRT)\b",
            re.IGNORECASE,
        ),
        ["Cal. Gov. § 7070", "Cal. Civ. Code § 1798.90.55"],
    ),
    (
        re.compile(r"\b(ALPR|license.?plate.?reader|Flock)\b", re.IGNORECASE),
        ["Cal. Veh. Code § 2413", "Cal. Pen. § 832.18"],
    ),
    (
        re.compile(r"\b(arbitration|arbitrate|binding arbitration)\b", re.IGNORECASE),
        ["Cal. CCP § 1281.96"],
    ),
    (
        re.compile(
            r"\b(artificial intelligence|automated decision|machine learning|predictive policing)\b",
            re.IGNORECASE,
        ),
        ["Cal. Gov. § 11546.45"],
    ),
    (
        re.compile(r"\b(body.?worn.?camera|body cam|BWC|dashcam)\b", re.IGNORECASE),
        ["Cal. Pen. Code § 832.7", "Cal. Pen. Code § 832.8"],
    ),
    (
        re.compile(
            r"\b(Taser|TASER|electronic control weapon|ECW|CEW)\b", re.IGNORECASE
        ),
        ["Cal. Gov. § 7070", "Cal. Gov. § 7072"],
    ),
    (
        re.compile(
            r"\b(drone|UAS|unmanned aerial|aerial surveillance)\b", re.IGNORECASE
        ),
        ["Cal. Gov. § 7070"],
    ),
]


class L1StatutoryApplicability:
    """L-1 Statutory Applicability detector."""

    detector_id = "l1-statutory-applicability"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,  # LegalResolver -- typed as object to avoid circular import
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-1 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        statutes: list[str] = [_CPRA_BASELINE]
        signals: list[str] = ["California public agency -- CPRA baseline"]

        # Tier 2: document type
        doc_type_key = ctx.document_type.lower().replace(" ", "_").replace("-", "_")
        type_statutes = _TYPE_STATUTES.get(doc_type_key, [])
        statutes.extend(type_statutes)
        if type_statutes:
            signals.append(f"document_type={ctx.document_type!r}")

        # Tier 3: content signals
        content_hits: list[str] = []
        for pattern, stat_list in _SIGNAL_PATTERNS:
            if pattern.search(ctx.text):
                for s in stat_list:
                    if s not in statutes:
                        statutes.append(s)
                content_hits.append(pattern.pattern.split(r"\b")[1].split(r"\b")[0])

        if content_hits:
            signals.append(f"content signals: {', '.join(content_hits[:4])}")

        # Confidence
        if ctx.document_type and ctx.document_type not in ("unknown", ""):
            confidence = 1.0
        elif ctx.jurisdiction:
            confidence = 0.8
        else:
            confidence = 0.6

        conclusion = (
            f"Document implicates {len(statutes)} statute(s): "
            + ", ".join(statutes[:5])
            + ("..." if len(statutes) > 5 else "")
            + f". Basis: {'; '.join(signals)}."
        )

        finding_id = (
            "legal:l1:"
            + hashlib.sha256(
                f"{ctx.document_hash}:{','.join(statutes)}".encode()
            ).hexdigest()[:12]
        )

        return [
            LegalFinding(
                finding_id=finding_id,
                sub_detector=self.detector_id,
                severity=Severity.LOW,
                document_hash=ctx.document_hash,
                document_id=ctx.document_id,
                statutes_applied=statutes,
                legal_conclusion=conclusion,
                confidence=confidence,
                source_finding_id=(
                    ctx.source_finding.get("id") if ctx.source_finding else None
                ),
                notes=f"Jurisdiction: {ctx.jurisdiction}",
            )
        ]
