"""L-4 Ministerial Duty Analysis -- odia_legal Phase 2.

Detects documents that implicate a public agency's mandatory (ministerial)
duties -- obligations imposed by statute where the agency has no discretion --
and flags when those duties appear to have been omitted or defaulted.

Under California law, a public agency owes a non-discretionary duty where a
statute requires a specific act without leaving room for judgment. Failure to
perform a mandatory duty exposes the agency to liability under Gov. Code § 815.6.
Unlike discretionary acts, mandatory duties do not receive public-entity immunity.

Rules implemented:

  MD-1  CPRA Mandatory Disclosure (Cal. Gov. §§ 7920.000, 7922.000)
        CPRA creates a mandatory duty to disclose public records absent a
        specific exemption. A denial without citing a specific exemption
        by section number implicates § 815.6 mandatory duty failure.

  MD-2  Brown Act Mandatory Notice (Cal. Gov. § 54954.2)
        Posting the agenda 72 hours before a regular meeting is mandatory.
        Meeting minutes that reference items discussed but not noticed
        implicate § 815.6.

  MD-3  AB 481 Mandatory Annual Report (Cal. Gov. § 7072)
        Annual reporting on militarized equipment use by May 1 is mandatory.
        Corpus documents referencing equipment deployment without evidence
        of the required annual report implicate § 815.6.

  MD-4  SB 34 Mandatory ALPR Policy (Cal. Veh. Code § 2413)
        Agencies operating ALPR systems must adopt and publish an ALPR
        policy. Use of ALPR without a cited policy is a mandatory duty failure.

  MD-5  Mandatory Officer Misconduct Disclosure (Cal. Pen. Code § 832.7)
        Peace officer records involving sustained misconduct, uses of force
        causing injury/death, and vehicle pursuits are mandatorily disclosable.
        Blanket denial of such records implicates § 832.7 and § 832.8.

Confidence:
  0.80  Statutory trigger present, duty omission clearly indicated
  0.65  Statutory trigger present, omission inferred from document structure
  0.50  Possible trigger, context insufficient for high confidence
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l4:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# CPRA denial without specific exemption citation
_RE_DENIAL = re.compile(
    r"\b(denied|denial|withhold(?:ing)?|withheld|not.{0,20}provid(?:e|ed|ing)|"
    r"unable to.{0,20}(provide|release|disclose)|exempt)\b",
    re.IGNORECASE,
)
_RE_EXEMPTION_CITE = re.compile(
    r"\b(§\s*\d{4,5}|section\s+\d{4,5}|Government Code\s+\d{4,5}|"
    r"7923\.\d+|7927\.\d+|7922\.\d+)\b",
    re.IGNORECASE,
)

# Brown Act: items discussed but not on agenda
_RE_AGENDA_ITEM = re.compile(
    r"\b(added to.{0,20}agenda|not.{0,20}(noticed|agendized)|"
    r"emergency.{0,20}(item|action)|urgency.{0,20}(item|action))\b",
    re.IGNORECASE,
)

# AB 481 equipment deployment without annual report evidence
_RE_DEPLOYMENT = re.compile(
    # Match "deployed/used MRAP" OR "MRAP was deployed" (either order)
    r"\b(?:"
    r"(?:deployed|used|utilized|operated).{0,50}"
    r"(?:MRAP|drone|UAS|LRAD|flashbang|stun.?grenade|armored.?vehicle|surveillance.?aircraft|aerial.{0,10}surveillance)"
    r"|"
    r"(?:MRAP|drone|UAS|LRAD|flashbang|stun.?grenade|armored.?vehicle|surveillance.?aircraft|aerial.{0,10}surveillance)"
    r".{0,50}(?:deployed|used|utilized|operated)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_ANNUAL_REPORT = re.compile(
    r"\b(annual report|§.?7072|AB.?481.{0,20}report|equipment.{0,20}report)\b",
    re.IGNORECASE,
)

# ALPR use without policy
_RE_ALPR_USE = re.compile(
    r"\b(ALPR|Flock|license.?plate.?reader|LPR.{0,10}(system|camera|data))\b",
    re.IGNORECASE,
)
_RE_ALPR_POLICY = re.compile(
    r"\b(ALPR.{0,30}policy|license.?plate.{0,30}policy|§.?2413|"
    r"Vehicle Code.{0,10}2413)\b",
    re.IGNORECASE,
)

# Peace officer records denial
_RE_OFFICER_RECORDS = re.compile(
    r"\b(officer.{0,30}(misconduct|complaint|discipline|sustained)|"
    r"use.?of.?force.{0,30}records|vehicle pursuit.{0,20}records|"
    r"§.?832\.7|Penal Code.{0,10}832\.7)\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_PC_EXEMPTION = re.compile(
    r"\b(Penal Code.{0,10}832\.7|§.?832\.7|officer.{0,20}personnel.{0,20}file)\b",
    re.IGNORECASE,
)


class L4MinisterialDuty:
    """L-4 Ministerial Duty Analysis detector."""

    detector_id = "l4-ministerial-duty"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-4 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # MD-1: CPRA denial without specific exemption citation
        if _RE_DENIAL.search(text) and not _RE_EXEMPTION_CITE.search(text):
            if "records" in text.lower() or "request" in text.lower():
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "MD-1"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "Cal. Gov. § 815.6",
                            "Cal. Gov. § 7920.000",
                            "Cal. Gov. § 7922.000",
                        ],
                        legal_conclusion=(
                            "CPRA denial without specific statutory exemption citation. "
                            "Cal. Gov. § 7920.000 creates a mandatory duty to disclose. "
                            "Denial without citing the exemption by section number "
                            "fails the mandatory duty under Cal. Gov. § 815.6."
                        ),
                        confidence=0.65,
                        source_finding_id=source_id,
                        notes="MD-1: denial without exemption cite",
                    )
                )

        # MD-2: Meeting minutes reference non-noticed items
        if ctx.document_type.lower() in ("meeting_minutes", "minutes"):
            if _RE_AGENDA_ITEM.search(text):
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "MD-2"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "Cal. Gov. § 815.6",
                            "Cal. Gov. § 54954.2",
                            "Cal. Gov. § 54954.3",
                        ],
                        legal_conclusion=(
                            "Meeting minutes reference items added to the agenda "
                            "or discussed without prior 72-hour notice. "
                            "Cal. Gov. § 54954.2 creates a mandatory duty to provide "
                            "agenda notice. Emergency exceptions are narrowly construed "
                            "and must be documented. Implicates § 815.6 mandatory duty."
                        ),
                        confidence=0.75,
                        source_finding_id=source_id,
                        notes="MD-2: non-noticed item in meeting minutes",
                    )
                )

        # MD-3: Equipment deployment without annual report reference
        if _RE_DEPLOYMENT.search(text) and not _RE_ANNUAL_REPORT.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "MD-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.MEDIUM,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. § 815.6",
                        "Cal. Gov. § 7072",
                    ],
                    legal_conclusion=(
                        "Militarized or surveillance equipment deployment documented "
                        "without reference to the mandatory AB 481 annual report. "
                        "Cal. Gov. § 7072 creates a mandatory duty to file the annual "
                        "report by May 1. Absence of this documentation implicates § 815.6."
                    ),
                    confidence=0.65,
                    source_finding_id=source_id,
                    notes="MD-3: equipment deployment without annual report reference",
                )
            )

        # MD-4: ALPR use without policy reference
        if _RE_ALPR_USE.search(text) and not _RE_ALPR_POLICY.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "MD-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. § 815.6",
                        "Cal. Veh. Code § 2413",
                    ],
                    legal_conclusion=(
                        "Automated License Plate Reader (ALPR) use documented without "
                        "reference to a required ALPR policy. Cal. Veh. Code § 2413 "
                        "creates a mandatory duty to adopt and make available an ALPR "
                        "policy before operating ALPR systems. Implicates § 815.6."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes="MD-4: ALPR use without policy reference",
                )
            )

        # MD-5: Peace officer record denial without § 832.7 carve-out
        if _RE_DENIAL.search(text) and _RE_OFFICER_RECORDS.search(text):
            if not re.search(
                r"\b(sustained|use.?of.?force|vehicle.?pursuit|officer.?involved)\b",
                text,
                re.IGNORECASE,
            ) or _RE_PC_EXEMPTION.search(text):
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "MD-5"),
                        sub_detector=self.detector_id,
                        severity=Severity.CRITICAL,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "Cal. Gov. § 815.6",
                            "Cal. Pen. Code § 832.7",
                            "Cal. Pen. Code § 832.8",
                        ],
                        legal_conclusion=(
                            "Peace officer misconduct or use-of-force records withheld "
                            "without meeting the mandatory disclosure exceptions. "
                            "Cal. Pen. Code § 832.7 mandates disclosure of records "
                            "involving sustained misconduct, uses of force causing "
                            "injury or death, and vehicle pursuits. Invoking the "
                            "personnel file exemption (§ 832.8) for these categories "
                            "is precluded by statute. Implicates § 815.6."
                        ),
                        confidence=0.80,
                        source_finding_id=source_id,
                        notes="MD-5: peace officer records withheld -- § 832.7 mandatory disclosure",
                    )
                )

        return findings
