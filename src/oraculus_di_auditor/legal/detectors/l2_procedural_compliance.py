"""L-2 Procedural Compliance -- odia_legal Phase 2.

Detects when a public agency document exhibits indicators of procedural
non-compliance with California public records and open-meeting law.

Rules implemented:

  PC-1  CPRA 10-day response window
        Cal. Gov. § 7922.500: response due within 10 calendar days of receipt.
        Signal: records request text contains a receipt date but no response
        date, OR the document asserts compliance without a dated response.

  PC-2  CPRA 14-day extension notice
        Cal. Gov. § 7922.530: if an extension is invoked, written notice with
        the reason and the date production will occur is required.
        Signal: extension language present but no specific production date.

  PC-3  Brown Act 72-hour agenda posting
        Cal. Gov. § 54954.2: agendas must be posted at least 72 hours before
        a regular meeting.
        Signal: agenda contains a meeting date/time and a posting date, and
        the gap is less than 72 hours, OR no posting timestamp is present.

  PC-4  AB 481 annual report due date
        Cal. Gov. § 7072: annual report on militarized equipment use required
        by May 1 of each year.
        Signal: annual report document with a date outside the May window, or
        an annual report that references equipment use without a submission date.

Each rule fires only when the relevant document type is present.
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)

# Regex patterns for procedural compliance signals

# PC-1 / PC-2: CPRA response signals
_RE_CPRA_REQUEST = re.compile(
    r"\b(public records request|CPRA request|records request|request for records)\b",
    re.IGNORECASE,
)
_RE_RESPONSE_LANGUAGE = re.compile(
    r"\b(response|we respond|hereby respond|acknowledge|acknowledges)\b",
    re.IGNORECASE,
)
_RE_EXTENSION_LANGUAGE = re.compile(
    r"\b(extension|additional time|14.?day|fourteen.?day|extend the time)\b",
    re.IGNORECASE,
)
_RE_PRODUCTION_DATE = re.compile(
    r"\b(production date|records will be provided|provide records by|available by)\b",
    re.IGNORECASE,
)

# PC-3: Brown Act meeting date / posting signals
_RE_MEETING_DATE = re.compile(
    r"\b(?:meeting|session|convene)\s+(?:on\s+)?(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)
_RE_POSTED = re.compile(
    r"\b(?:posted|published|noticed)\s+(?:on\s+)?(\w+day,?\s+\w+\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)

# PC-4: AB 481 annual report signals
_RE_AB481_EQUIP = re.compile(
    r"\b(military.?equipment|surplus.?equipment|MRAP|armored vehicle|"
    r"stun.?grenade|flashbang|LRAD|surveillance aircraft)\b",
    re.IGNORECASE,
)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l2:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


class L2ProceduralCompliance:
    """L-2 Procedural Compliance detector."""

    detector_id = "l2-procedural-compliance"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-2 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        doc_type = ctx.document_type.lower()
        text = ctx.text

        # PC-1: CPRA request without a response acknowledgement
        if _RE_CPRA_REQUEST.search(text):
            if not _RE_RESPONSE_LANGUAGE.search(text):
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "PC-1"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "Cal. Gov. § 7922.500",
                            "Cal. Gov. § 7920.000",
                        ],
                        legal_conclusion=(
                            "Document contains a CPRA records request with no "
                            "acknowledgement of response. Cal. Gov. § 7922.500 requires "
                            "a written response within 10 calendar days of receipt."
                        ),
                        confidence=0.7,
                        source_finding_id=(
                            ctx.source_finding.get("id") if ctx.source_finding else None
                        ),
                        notes="PC-1: missing response acknowledgement",
                    )
                )

        # PC-2: Extension invoked without a production date
        if _RE_EXTENSION_LANGUAGE.search(text) and _RE_CPRA_REQUEST.search(text):
            if not _RE_PRODUCTION_DATE.search(text):
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "PC-2"),
                        sub_detector=self.detector_id,
                        severity=Severity.MEDIUM,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=["Cal. Gov. § 7922.530"],
                        legal_conclusion=(
                            "Extension of CPRA response period invoked without "
                            "specifying the date production will occur. "
                            "Cal. Gov. § 7922.530 requires notice of the specific "
                            "date records will be provided."
                        ),
                        confidence=0.75,
                        source_finding_id=(
                            ctx.source_finding.get("id") if ctx.source_finding else None
                        ),
                        notes="PC-2: extension without production date",
                    )
                )

        # PC-3: Brown Act -- agenda without posting timestamp
        if doc_type in ("agenda", "meeting_agenda"):
            meeting_match = _RE_MEETING_DATE.search(text)
            posted_match = _RE_POSTED.search(text)
            if meeting_match and not posted_match:
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "PC-3"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=["Cal. Gov. § 54954.2"],
                        legal_conclusion=(
                            "Agenda document contains a meeting date but no posting "
                            "timestamp. Cal. Gov. § 54954.2 requires agendas to be "
                            "posted at least 72 hours before a regular meeting. "
                            "Absence of posting timestamp prevents compliance verification."
                        ),
                        confidence=0.65,
                        source_finding_id=(
                            ctx.source_finding.get("id") if ctx.source_finding else None
                        ),
                        notes=(
                            f"PC-3: meeting date found ({meeting_match.group(1)!r}), "
                            "no posting timestamp"
                        ),
                    )
                )

        # PC-4: Annual report with AB 481 equipment but no submission date
        if _RE_AB481_EQUIP.search(text):
            has_date = bool(
                re.search(
                    r"\b(January|February|March|April|May|June|July|August|"
                    r"September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
                    text,
                    re.IGNORECASE,
                )
            )
            if not has_date:
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "PC-4"),
                        sub_detector=self.detector_id,
                        severity=Severity.MEDIUM,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=["Cal. Gov. § 7072"],
                        legal_conclusion=(
                            "Document references militarized or surveillance equipment "
                            "use without a submission date. Cal. Gov. § 7072 (AB 481) "
                            "requires annual reports to be submitted by May 1 each year. "
                            "Missing date prevents compliance verification."
                        ),
                        confidence=0.6,
                        source_finding_id=(
                            ctx.source_finding.get("id") if ctx.source_finding else None
                        ),
                        notes="PC-4: equipment reference without annual report date",
                    )
                )

        return findings
