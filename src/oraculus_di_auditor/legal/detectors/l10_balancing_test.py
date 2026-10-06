"""L-10 Balancing Test Analyzer -- odia_legal Phase 2.

Identifies documents where a statutory or constitutional balancing test applies
and assesses whether the balancing analysis is present and adequate.

Two primary balancing frameworks are implemented:

  (A) CPRA Public Interest Balancing (Cal. Gov. § 7922.000)
      The catch-all exemption requires demonstrating that the public interest
      in nondisclosure clearly outweighs the public interest in disclosure.
      The California Supreme Court has held this is a high bar:
      - CBS Inc. v. Block (1986) 42 Cal.3d 646 -- agency cannot use a
        generalized or conclusory interest in nondisclosure
      - City of San Jose v. Superior Court (2017) 2 Cal.5th 608 -- CPRA
        broadly construed; exemptions narrowly

  (B) Mathews v. Eldridge Procedural Due Process Balancing
      (424 U.S. 319 (1976)) Three-factor test:
      1. The private interest at stake
      2. The risk of erroneous deprivation and the value of additional safeguards
      3. The government's interest, including fiscal/administrative burdens
      Applied to: automated benefit terminations, risk score detentions,
      parole revocations, asset seizures.

  (C) Carpenter Fourth Amendment Reasonableness Balancing
      Post-Carpenter, the third-party doctrine's near-categorical rule is
      replaced by a balancing approach for digital location data:
      - Degree of privacy intrusion
      - Comprehensiveness of the surveillance
      - Temporal duration

  (D) AB 481 / SB 34 Cost-Benefit / Necessity Analysis
      Cal. Gov. § 7071(b)(4) requires a cost-benefit analysis before adopting
      a surveillance equipment use policy. Policies lacking this analysis
      fail the statutory requirement.

Rules:

  BT-1  CPRA Balancing -- Conclusory (§ 7922.000)
        Exemption invoked with a conclusory interest (e.g., "privacy concerns")
        without specific articulation. Fires when balance language present but
        no specific interest is identified.

  BT-2  CPRA Balancing -- Absent (§ 7922.000)
        Catch-all exemption invoked with no balancing language at all.
        (Complements L-3 EX-2; provides a more detailed legal framing.)

  BT-3  Mathews Balancing -- Absent in Automated Decision
        Automated or algorithmic decision affecting liberty/property without
        any Mathews balancing analysis. (Complements L-6 CI-5.)

  BT-4  Carpenter Reasonableness -- Location Data Without Duration/Scope
        Location data collection documents that lack scope and duration
        parameters. Carpenter requires these to assess reasonableness.

  BT-5  AB 481 Cost-Benefit Missing
        Surveillance equipment policy without a documented cost-benefit or
        necessity analysis as required by § 7071(b)(4).
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l10:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# CPRA catch-all exemption invocation
_RE_CATCHALL = re.compile(
    r"\b(7922\.000|catch.?all.{0,20}exemption|public interest.{0,40}nondisclosure|"
    r"nondisclosure.{0,40}public interest|balancing.{0,20}exemption)\b",
    re.IGNORECASE,
)

# Balancing language
_RE_BALANCE_LANGUAGE = re.compile(
    r"\b(weigh(?:ing|ed|s)|balance(?:d|s|ing)?|"
    r"outweigh(?:s|ed|ing)?|offset(?:ting|ted)?|"
    r"countervailing|competing.{0,20}interest)\b",
    re.IGNORECASE,
)

# Specific interest articulated in CPRA balancing
_RE_SPECIFIC_INTEREST = re.compile(
    r"\b(?:"
    r"(ongoing|active|criminal).{0,30}(investigation|case|prosecution)|"
    r"(informant|source|witness).{0,20}(identit|safet|protect)|"
    r"(personnel|employee).{0,20}(privacy|right|safet)|"
    r"(trade secret|proprietary|competitive).{0,20}(information|data)|"
    r"(deliberat\w*|attorney.?client|privilege).{0,30}communic"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# Automated decision signals (from L-6 CI-5)
_RE_AUTO_DECISION = re.compile(
    r"\b(?:"
    r"(?:predictive|algorithmic|automated|AI.?generated|machine.?generated)"
    r".{0,40}(?:risk.?score|threat.?assessment|detain\w*|recommend\w*|decision)|"
    r"(?:risk.?score|threat.?assessment).{0,40}(?:detain|arrest|parole|bail|sentence)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# Mathews balancing factors
_RE_MATHEWS_FACTORS = re.compile(
    r"\b(?:"
    r"private interest|liberty interest|property interest|"
    r"erroneous deprivation|risk of error|false positive|"
    r"administrative burden|fiscal impact|government interest"
    r")\b",
    re.IGNORECASE,
)

# Location data signals
_RE_LOCATION_DATA = re.compile(
    r"\b(ALPR|GPS|geofence|cell.?site|CSLI|location.{0,20}data|"
    r"license.?plate.{0,20}(data|records|reader))\b",
    re.IGNORECASE,
)

# Duration / scope parameters
_RE_DURATION_SCOPE = re.compile(
    r"\b(?:"
    r"\d+.{0,5}(?:day|week|month|year).{0,10}(?:retention|kept|stored|limit)|"
    r"(?:retention|kept|stored|limit).{0,10}\d+.{0,5}(?:day|week|month|year)|"
    r"geographic.{0,20}(limit|bound\w*|area|zone)|"
    r"targeted.{0,20}(individual|subject|suspect)"
    r")\b",
    re.IGNORECASE,
)

# AB 481 equipment policy signals
_RE_AB481_POLICY = re.compile(
    r"\b(AB.?481|§.?7070|§.?7071|§.?7072|"
    r"military.?equipment.{0,20}(policy|use)|"
    r"surveillance.{0,20}equipment.{0,20}(policy|use.?policy))\b",
    re.IGNORECASE,
)

# Cost-benefit / necessity analysis language
_RE_COST_BENEFIT = re.compile(
    r"\b(?:"
    r"cost.?benefit|benefit.?cost|necessity.{0,20}(analysis|review|finding)|"
    r"(analysis|review|finding).{0,20}necessity|"
    r"least.{0,20}restrictive|proportional\w*|"
    r"§.?7071\s*\(b\)\s*\(4\)"
    r")\b",
    re.IGNORECASE,
)


class L10BalancingTest:
    """L-10 Balancing Test Analyzer."""

    detector_id = "l10-balancing-test"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-10 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # BT-1: CPRA balancing present but conclusory (no specific interest)
        if (
            _RE_CATCHALL.search(text)
            and _RE_BALANCE_LANGUAGE.search(text)
            and not _RE_SPECIFIC_INTEREST.search(text)
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "BT-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. § 7922.000",
                        "CBS Inc. v. Block, 42 Cal.3d 646 (1986)",
                        "City of San Jose v. Superior Court, 2 Cal.5th 608 (2017)",
                    ],
                    legal_conclusion=(
                        "CPRA catch-all exemption (§ 7922.000) invoked with balancing "
                        "language but no specific interest articulated to support "
                        "nondisclosure. CBS Inc. v. Block (1986) held that a generalized "
                        "or conclusory interest in nondisclosure is insufficient -- the "
                        "agency must identify a specific, concrete public interest that "
                        "clearly outweighs the public interest in disclosure."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes="BT-1: CPRA balancing -- conclusory without specific interest",
                )
            )

        # BT-2: CPRA catch-all with no balancing language at all
        elif _RE_CATCHALL.search(text) and not _RE_BALANCE_LANGUAGE.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "BT-2"),
                    sub_detector=self.detector_id,
                    severity=Severity.CRITICAL,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. § 7922.000",
                        "CBS Inc. v. Block, 42 Cal.3d 646 (1986)",
                    ],
                    legal_conclusion=(
                        "CPRA catch-all exemption (§ 7922.000) invoked with no "
                        "balancing analysis whatsoever. The catch-all exemption is not "
                        "self-executing -- it requires the agency to demonstrate that the "
                        "public interest in nondisclosure clearly outweighs the public "
                        "interest in disclosure. Bare invocation without any weighing "
                        "analysis fails the statutory standard as a matter of law "
                        "(CBS Inc. v. Block, 1986)."
                    ),
                    confidence=0.85,
                    source_finding_id=source_id,
                    notes="BT-2: CPRA balancing -- completely absent",
                )
            )

        # BT-3: Automated decision without Mathews balancing
        if _RE_AUTO_DECISION.search(text) and not _RE_MATHEWS_FACTORS.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "BT-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. XIV",
                        "Mathews v. Eldridge, 424 U.S. 319 (1976)",
                        "Cal. Const. Art. I § 7",
                    ],
                    legal_conclusion=(
                        "Automated decision-making affecting liberty or property without "
                        "a documented Mathews v. Eldridge (1976) balancing analysis. "
                        "Due process requires weighing: (1) the private interest at stake, "
                        "(2) the risk of erroneous deprivation and value of additional "
                        "safeguards, and (3) the government's interest. Automated systems "
                        "with high false-positive rates increase factor (2) significantly."
                    ),
                    confidence=0.75,
                    source_finding_id=source_id,
                    notes="BT-3: Mathews balancing -- absent in automated decision context",
                )
            )

        # BT-4: Location data without duration/scope parameters
        if _RE_LOCATION_DATA.search(text) and not _RE_DURATION_SCOPE.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "BT-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. IV",
                        "Carpenter v. United States, 138 S. Ct. 2206 (2018)",
                        "Cal. Const. Art. I § 1",
                    ],
                    legal_conclusion=(
                        "Location data collection documented without duration or geographic "
                        "scope parameters. Post-Carpenter, the reasonableness of digital "
                        "location surveillance depends on the comprehensiveness and temporal "
                        "scope of collection. A policy or program lacking these parameters "
                        "cannot establish Fourth Amendment reasonableness and cannot be "
                        "reviewed for Carpenter compliance."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="BT-4: Carpenter reasonableness -- no duration/scope parameters",
                )
            )

        # BT-5: AB 481 equipment policy without cost-benefit analysis
        if _RE_AB481_POLICY.search(text) and not _RE_COST_BENEFIT.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "BT-5"),
                    sub_detector=self.detector_id,
                    severity=Severity.MEDIUM,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. § 7071",
                        "Cal. Gov. § 7071(b)(4)",
                    ],
                    legal_conclusion=(
                        "AB 481 surveillance equipment policy lacks a cost-benefit or "
                        "necessity analysis. Cal. Gov. § 7071(b)(4) requires every "
                        "militarized/surveillance equipment use policy to include an "
                        "analysis of the benefits and potential adverse community impacts "
                        "of acquiring and using the equipment. A policy lacking this "
                        "analysis is procedurally deficient."
                    ),
                    confidence=0.75,
                    source_finding_id=source_id,
                    notes="BT-5: AB 481 equipment policy -- missing § 7071(b)(4) cost-benefit",
                )
            )

        return findings
