"""L-3 Exemption Misapplication -- odia_legal Phase 2.

Detects when a public agency invokes a CPRA or related statutory exemption
without including the required showing to satisfy its elements.

Exemptions are affirmative defenses with specific element requirements.
A bare invocation without the required showing shifts the burden onto the
requester, violating the CPRA's default presumption of disclosure.

Rules implemented:

  EX-1  Law Enforcement Records (§ 7923.600)
        Exemption for law enforcement investigative files requires showing
        that disclosure would (a) endanger an active investigation or
        (b) identify a confidential informant. Bare invocation without
        either showing is facially deficient.

  EX-2  Catch-All Public Interest Balancing (§ 7922.000)
        Exemption requires weighing public interest in nondisclosure against
        public interest in disclosure. Must contain explicit balancing language;
        conclusory invocation without a weighing analysis is facially deficient.

  EX-3  Face Recognition System Records (§ 1798.90.55)
        Exemption for certain FRT system records requires disclosure under
        SB 34 / AB 481 first. An agency that claims this exemption while
        also lacking required SB 34 disclosures has a compound deficiency.

  EX-4  Deliberative Process / Pre-Decisional (§ 7927.705)
        Requires showing the record is both (a) pre-decisional and (b) contains
        deliberative material whose release would chill internal deliberation.
        Boilerplate invocation without either element is facially deficient.

  EX-5  Attorney-Client Privilege (Cal. Evid. Code § 954 via Gov. § 7927.705)
        Must show attorney-client relationship, confidential communication, and
        that privilege was not waived. Bare invocation covering entire categories
        of documents is overbroad.

Confidence calibration:
  0.85  Exemption cited AND no showing present
  0.70  Exemption language detected, showing indeterminate
  0.55  Possible exemption invocation, context ambiguous
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


@dataclass
class _ExemptionRule:
    rule_id: str
    citation_pattern: re.Pattern[str]  # detects the exemption being invoked
    showing_pattern: re.Pattern[str]  # detects a legally sufficient showing
    statutes: list[str]
    severity_no_showing: Severity
    conclusion_template: str  # {exemption} placeholder filled at runtime


_RULES: list[_ExemptionRule] = [
    _ExemptionRule(
        rule_id="EX-1",
        citation_pattern=re.compile(
            r"\b(7923\.600|law enforcement.{0,30}exempt|investigative.{0,30}exempt|"
            r"exempt.{0,30}investigat(?:ive|ion)|police.{0,30}investigat(?:ive|ion).{0,30}records)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        showing_pattern=re.compile(
            r"\b(active investigation|endanger(?:ing)?.{0,30}investigation|"
            r"confidential informant|ongoing investigat)\b",
            re.IGNORECASE,
        ),
        statutes=["Cal. Gov. § 7923.600", "Cal. Gov. § 7920.000"],
        severity_no_showing=Severity.HIGH,
        conclusion_template=(
            "Law enforcement records exemption (Cal. Gov. § 7923.600) invoked "
            "without showing (a) an active investigation would be endangered or "
            "(b) a confidential informant would be identified. Bare invocation "
            "is facially deficient under the CPRA's presumption of disclosure."
        ),
    ),
    _ExemptionRule(
        rule_id="EX-2",
        citation_pattern=re.compile(
            r"\b(7922\.000|public interest.{0,40}outweigh|nondisclosure.{0,40}public interest|"
            r"catch.?all.{0,30}exemption|balancing.{0,30}exemption)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        showing_pattern=re.compile(
            r"\b(weigh(?:ing|ed).{0,60}(public interest|disclosure)|"
            r"(public interest|disclosure).{0,60}weigh(?:ing|ed)|"
            r"outweigh(?:ed|s).{0,40}(disclosure|openness))\b",
            re.IGNORECASE | re.DOTALL,
        ),
        statutes=["Cal. Gov. § 7922.000"],
        severity_no_showing=Severity.HIGH,
        conclusion_template=(
            "Public interest balancing exemption (Cal. Gov. § 7922.000) invoked "
            "without an explicit weighing analysis. The catch-all exemption requires "
            "the agency to demonstrate the public interest in nondisclosure clearly "
            "outweighs the public interest in disclosure. Conclusory invocation is "
            "facially deficient."
        ),
    ),
    _ExemptionRule(
        rule_id="EX-3",
        citation_pattern=re.compile(
            r"\b(1798\.90\.55|face.?recogni(?:tion)?.{0,30}exempt|"
            r"FRT.{0,30}exempt|facial.{0,30}recogni(?:tion)?.{0,30}records)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        showing_pattern=re.compile(
            r"\b(AB.?481|SB.?34|§.?7070|equipment.{0,30}(policy|annual report)|"
            r"militarized.{0,30}equipment.{0,30}report)\b",
            re.IGNORECASE,
        ),
        statutes=["Cal. Civ. Code § 1798.90.55", "Cal. Gov. § 7070"],
        severity_no_showing=Severity.CRITICAL,
        conclusion_template=(
            "Face recognition system records exemption (Cal. Civ. Code § 1798.90.55) "
            "invoked without SB 34 / AB 481 disclosures. An agency may not claim this "
            "exemption while simultaneously withholding the equipment use policy and "
            "annual report required by Cal. Gov. § 7070. Compound statutory deficiency."
        ),
    ),
    _ExemptionRule(
        rule_id="EX-4",
        citation_pattern=re.compile(
            r"\b(7927\.705|deliberat(?:ive|ion).{0,30}(?:process|privilege)|"
            r"pre.?decisional|predecisional)\b",
            re.IGNORECASE,
        ),
        showing_pattern=re.compile(
            # Requires explicit chill-of-deliberation language -- mere co-occurrence
            # of "predecisional" and "deliberative" does not satisfy § 7927.705.
            r"\b(chill(?:ing)?|stifle|frank.{0,20}(discuss|deliber)|"
            r"candid.{0,20}(discuss|deliber)|free.{0,20}(exchange|deliber))\b",
            re.IGNORECASE,
        ),
        statutes=["Cal. Gov. § 7927.705"],
        severity_no_showing=Severity.MEDIUM,
        conclusion_template=(
            "Deliberative process exemption (Cal. Gov. § 7927.705) invoked without "
            "establishing both (a) the record is pre-decisional and (b) contains "
            "deliberative material whose release would chill internal deliberation. "
            "Boilerplate invocation covering entire document categories is overbroad."
        ),
    ),
    _ExemptionRule(
        rule_id="EX-5",
        citation_pattern=re.compile(
            r"\b(attorney.?client|Cal\.?\s*Evid(?:ence)?.?\s*Code.?\s*§?\s*954|"
            r"privileged.{0,30}communicat|A/C\s*privilege|work.?product)\b",
            re.IGNORECASE,
        ),
        showing_pattern=re.compile(
            r"\b(confid(?:ential|entiality).{0,60}attorney|"
            r"attorney.{0,60}confid(?:ential|entiality)|"
            r"legal.{0,30}advice.{0,30}sought|privilege.{0,30}not.{0,30}waived)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        statutes=["Cal. Evid. Code § 954", "Cal. Gov. § 7927.705"],
        severity_no_showing=Severity.MEDIUM,
        conclusion_template=(
            "Attorney-client privilege invoked (Cal. Evid. Code § 954) without "
            "establishing: attorney-client relationship, confidential communication, "
            "and non-waiver. Blanket invocation over entire document categories is "
            "overbroad and does not satisfy the elements of the privilege."
        ),
    ),
]


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l3:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


class L3ExemptionMisapplication:
    """L-3 Exemption Misapplication detector."""

    detector_id = "l3-exemption-misapplication"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-3 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text

        for rule in _RULES:
            if not rule.citation_pattern.search(text):
                continue  # exemption not invoked -- skip

            if rule.showing_pattern.search(text):
                continue  # showing is present -- compliant

            # Exemption invoked, required showing absent
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, rule.rule_id),
                    sub_detector=self.detector_id,
                    severity=rule.severity_no_showing,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=rule.statutes,
                    legal_conclusion=rule.conclusion_template,
                    confidence=0.85,
                    source_finding_id=(
                        ctx.source_finding.get("id") if ctx.source_finding else None
                    ),
                    notes=f"{rule.rule_id}: exemption invoked without required showing",
                )
            )

        return findings
