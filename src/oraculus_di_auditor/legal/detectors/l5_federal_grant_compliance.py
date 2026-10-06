"""L-5 Federal Grant Compliance -- odia_legal Phase 2.

Detects documents implicating federal grant compliance obligations and flags
when grant-funded activities appear to violate grant conditions or federal law.

Federal grants to California law enforcement agencies are governed by a layered
compliance framework: the grant statute and program requirements, 2 CFR Part 200
(Uniform Guidance), and the constitutional conditions attached to federal funds.
Violations can result in suspension, debarment, audit findings, and civil rights
liability under 42 USC § 1983.

Rules implemented:

  GC-1  JAG Byrne Grant Conditions (34 USC § 10152 / Pub. L. 90-351)
        JAG-funded activities must comply with: civil rights certifications,
        no use for mass surveillance without individualized suspicion, body cam
        requirements where applicable. Signal: JAG references without compliance
        certification language.

  GC-2  COPS Grant Conditions (34 USC § 10381)
        COPS-funded officers and equipment must be used for community policing.
        Signal: COPS references with equipment use inconsistent with program
        purpose (e.g., mass surveillance, ICE collaboration).

  GC-3  Uniform Guidance Procurement (2 CFR § 200.317 -- § 200.327)
        Federally-funded procurements must follow competitive bidding requirements.
        Signal: procurement exceeding $250,000 awarded sole-source without a
        documented exception (2 CFR § 200.320).

  GC-4  42 USC § 1983 / Civil Rights Liability Exposure
        Grant-funded activities that violate constitutional rights can ground
        a § 1983 claim. Signal: documents showing grant-funded surveillance or
        use of force with indicators of constitutional violation (see L-6).

  GC-5  Section 1621 / Immigration Enforcement Conditions (8 USC § 1373)
        Some federal grants (CAP, Secure Communities, SCAAP) condition funding
        on cooperation with immigration enforcement. Signal: 287(g) agreement
        or ICE MOU language with grant funding references.

Confidence:
  0.85  Grant program citation + compliance indicator present/absent
  0.70  Grant-funded activity inferred from document type and keyword signals
  0.55  Possible grant nexus, context insufficient
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l5:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# Grant program identifier patterns
_RE_JAG = re.compile(
    r"\b(JAG|Byrne.{0,20}grant|Edward Byrne|Justice Assistance Grant|"
    r"34\s*U\.?S\.?C\.?\s*§?\s*10152|Pub\.?\s*L\.?\s*90.?351)\b",
    re.IGNORECASE,
)
_RE_COPS = re.compile(
    r"\b(COPS.{0,20}(grant|program|office|funded)|"
    r"Community Oriented Policing|34\s*U\.?S\.?C\.?\s*§?\s*10381)\b",
    re.IGNORECASE,
)
_RE_GRANT_GENERIC = re.compile(
    r"\b(federal.{0,20}grant|grant.{0,20}fund\w*|grant\s+fund\w*|"
    r"Bureau of Justice|BJA|OJJDP|OJP|JAG\b|COPS\s+grant|Byrne)\b",
    re.IGNORECASE,
)

# Compliance certification language
_RE_CIVIL_RIGHTS_CERT = re.compile(
    # Use certif\w+ (not \b after stem) -- avoids mid-word boundary failure
    r"\b(civil rights.{0,30}certif\w+|certif\w+.{0,30}civil rights|"
    r"non.?discrimination.{0,20}certif\w+|Equal.{0,10}Employment.{0,10}certif\w+)",
    re.IGNORECASE | re.DOTALL,
)

# Procurement / sole source patterns
_RE_SOLE_SOURCE = re.compile(
    r"\b(sole.?source|single.?source|sole.?vendor|non.?competitive|"
    r"no.?bid|piggyback|cooperative.{0,20}purchase)\b",
    re.IGNORECASE,
)
_RE_SOLE_SOURCE_JUSTIFICATION = re.compile(
    r"\b(sole.?source.{0,60}justif|justif.{0,60}sole.?source|"
    r"exception.{0,30}competition|2\s*CFR.{0,10}200\.320)\b",
    re.IGNORECASE | re.DOTALL,
)

# Dollar amounts -- look for large contract amounts signaling threshold
_RE_LARGE_AMOUNT = re.compile(
    r"\$\s*(?:[2-9]\d{2}[,\s]\d{3}|\d{1,3}[,\s]\d{3}[,\s]\d{3})",  # $250K+
)

# Immigration enforcement patterns
_RE_ICE_COLLAB = re.compile(
    # No trailing \b after 287(g) -- ) is non-word char, boundary always fails there
    r"(?:287\(g\)|ICE.{0,20}(?:MOU|agreement|cooperation|detainer)|"
    r"Secure Communities|CAP.{0,20}program|SCAAP)",
    re.IGNORECASE,
)

# Section 1983 / civil rights violation indicators
_RE_CIVIL_RIGHTS_VIOLATION = re.compile(
    r"\b(§\s*1983|section 1983|42\s*U\.?S\.?C\.?\s*§?\s*1983|"
    r"constitutional.{0,20}(violation|right|claim)|"
    r"color of law|deprivation.{0,20}rights)\b",
    re.IGNORECASE,
)


class L5FederalGrantCompliance:
    """L-5 Federal Grant Compliance detector."""

    detector_id = "l5-federal-grant-compliance"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-5 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # GC-1: JAG without civil rights certification
        if _RE_JAG.search(text) and not _RE_CIVIL_RIGHTS_CERT.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "GC-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "34 USC § 10152",
                        "34 USC § 10228",  # JAG civil rights conditions
                        "42 USC § 3789d",  # LEAA nondiscrimination
                    ],
                    legal_conclusion=(
                        "JAG / Byrne grant program referenced without civil rights "
                        "certification language. 34 USC § 10228 requires all JAG "
                        "recipients to maintain nondiscrimination certifications as "
                        "a condition of award. Absent certification language in "
                        "grant documents is an audit finding trigger."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="GC-1: JAG reference without civil rights certification",
                )
            )

        # GC-2: COPS grant with non-community-policing use
        if _RE_COPS.search(text):
            surveillance_use = re.search(
                r"\b(surveillance|mass monitoring|predictive policing|"
                r"fusion center|gang database|ALPR|facial recognition)\b",
                text,
                re.IGNORECASE,
            )
            if surveillance_use:
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "GC-2"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "34 USC § 10381",
                            "34 USC § 10384",  # COPS program requirements
                        ],
                        legal_conclusion=(
                            "COPS grant-funded program co-located with surveillance "
                            "or predictive policing activities. COPS grants (34 USC "
                            "§ 10381) must be used for community-oriented policing. "
                            "Using COPS-funded positions or equipment for mass "
                            "surveillance programs may violate grant conditions."
                        ),
                        confidence=0.70,
                        source_finding_id=source_id,
                        notes="GC-2: COPS grant with surveillance use signal",
                    )
                )

        # GC-3: Federally-funded sole-source procurement without justification
        if (
            _RE_GRANT_GENERIC.search(text)
            and _RE_SOLE_SOURCE.search(text)
            and not _RE_SOLE_SOURCE_JUSTIFICATION.search(text)
        ):
            if _RE_LARGE_AMOUNT.search(text):
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "GC-3"),
                        sub_detector=self.detector_id,
                        severity=Severity.HIGH,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "2 CFR § 200.320",
                            "2 CFR § 200.317",
                        ],
                        legal_conclusion=(
                            "Federally-funded procurement appears to use sole-source "
                            "award without documented justification. 2 CFR § 200.320 "
                            "requires competitive procurement for federally-funded "
                            "contracts above simplified acquisition thresholds. "
                            "Sole-source awards require a written justification "
                            "citing a specific exception under § 200.320(f)."
                        ),
                        confidence=0.75,
                        source_finding_id=source_id,
                        notes="GC-3: federally-funded sole-source without justification",
                    )
                )

        # GC-4: Grant + civil rights violation indicators
        if _RE_GRANT_GENERIC.search(text) and _RE_CIVIL_RIGHTS_VIOLATION.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "GC-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.CRITICAL,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "42 USC § 1983",
                        "42 USC § 1981",
                        "28 CFR Part 42",  # DOJ nondiscrimination
                    ],
                    legal_conclusion=(
                        "Federal grant-funded activity co-occurs with § 1983 / civil "
                        "rights violation indicators. Grant recipients who violate "
                        "constitutional rights under color of law face both civil "
                        "rights liability (42 USC § 1983) and potential grant "
                        "suspension or debarment. Warrants immediate legal review."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="GC-4: grant + § 1983 civil rights violation indicator",
                )
            )

        # GC-5: ICE collaboration with grant funding
        if _RE_ICE_COLLAB.search(text) and _RE_GRANT_GENERIC.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "GC-5"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "8 USC § 1373",
                        "34 USC § 10153",  # JAG certification requirements
                    ],
                    legal_conclusion=(
                        "ICE collaboration or 287(g) agreement co-occurs with federal "
                        "grant references. Federal grants (including JAG) may condition "
                        "funding on immigration enforcement cooperation under 8 USC § 1373. "
                        "California's TRUST Act (Gov. Code § 7282.5) and LAEF limits "
                        "cooperation, creating potential conflict with federal conditions."
                    ),
                    confidence=0.75,
                    source_finding_id=source_id,
                    notes="GC-5: ICE collaboration with federal grant funding",
                )
            )

        return findings
