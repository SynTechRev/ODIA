"""L-6 Constitutional Implication -- odia_legal Phase 2.

Detects documents whose content implicates constitutional rights and flags
when government activity appears to lack the constitutional predicate required
by Fourth Amendment doctrine (particularly Carpenter v. United States, 138 S.
Ct. 2206 (2018)) and related California constitutional provisions.

This detector focuses on the Fourth Amendment mosaic theory and California's
parallel but often broader privacy rights under Cal. Const. Art. I, § 1.

Rules implemented:

  CI-1  Carpenter Mosaic Threshold (Fourth Amendment / Cal. Const. Art. I § 1)
        Carpenter held that the warrantless collection of 7+ days of CSLI
        constitutes a Fourth Amendment search. The mosaic theory holds that
        aggregating location data over time creates a "detailed chronicle"
        requiring judicial authorization.
        Signal: documents referencing extended ALPR retention, CSLI/cell tower
        requests, or aggregated location data without warrant language.

  CI-2  Third-Party Doctrine Erosion (Carpenter; Cal. Const. Art. I § 1)
        Carpenter partially eroded the third-party doctrine for digital
        location data. Documents referencing acquisition of metadata,
        electronic records, or transaction data from third parties without
        identifying the legal process used implicate this erosion.
        Signal: subpoena / legal process language for digital records
        without specificity about the legal authority used.

  CI-3  First Amendment Chilling Effect (Cal. Const. Art. I § 2)
        Surveillance programs targeting political speech, association, or
        religious practice implicate First Amendment rights. Assembly
        monitoring, political protest surveillance, or targeting based on
        political ideology requires compelling government interest.
        Signal: protest, demonstration, political organization, or religious
        community references in surveillance context.

  CI-4  Fourteenth Amendment Equal Protection / SB 1421 (Cal. Pen. § 832.7)
        Racially disparate use of surveillance technology triggers equal
        protection analysis. Disparate impact data combined with surveillance
        use is a Fourteenth Amendment equal protection red flag.
        Signal: demographic data + surveillance technology co-occurrence without
        impact analysis.

  CI-5  Automated Decision / Due Process (Mathews v. Eldridge, 424 U.S. 319)
        Automated systems that affect liberty or property interests without
        meaningful review implicate procedural due process. Predictive policing,
        automated detention recommendations, or algorithmic parole decisions
        without human review raise due process concerns.
        Signal: predictive/automated decision language affecting person's
        liberty or property without human review documentation.

Confidence calibration:
  0.85  Clear constitutional trigger + absence of required legal predicate
  0.70  Constitutional trigger present; legal predicate unclear
  0.55  Possible constitutional implication; context limited
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l6:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# CI-1: Location data aggregation / Carpenter signals
_RE_LOCATION_AGG = re.compile(
    # No trailing \b on stems (collect\w+, retain\w+, etc.) -- \b fails mid-word
    r"\b(?:"
    r"ALPR.{0,30}(?:retain\w*|stor\w*|database|pool\w*|30.day|60.day|90.day|year)\b|"
    r"(?:location|GPS|geofence|cell.?site|CSLI|tower.?dump).{0,40}(?:collect\w*|retain\w*|aggregat\w*|histor\w*|month|year|day\b)|"
    r"(?:cell.?site|CSLI|historical.{0,10}location).{0,30}(?:request\w*|obtain\w*|acquir\w*|subpoena\w*)"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_RE_WARRANT_LANGUAGE = re.compile(
    r"\b(search warrant|warrant.{0,20}issue|judicial.{0,20}authoriz|"
    r"probable cause.{0,30}(found|determin)|court.{0,20}order(?:ed)?)\b",
    re.IGNORECASE,
)

# CI-2: Third-party digital records without identified legal process
_RE_THIRD_PARTY_DIGITAL = re.compile(
    r"\b(?:"
    r"(?:subpoena|legal process|request).{0,40}(?:Google|Apple|Facebook|Meta|Twitter|X Corp|"
    r"Comcast|AT&T|Verizon|T-Mobile|Sprint|email|subscriber|account|metadata)|"
    r"(?:Google|Apple|Facebook|Meta|Twitter|Comcast|AT&T|Verizon).{0,40}(?:subpoena|legal process|request|compli)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_LEGAL_PROCESS_SPECIFICITY = re.compile(
    r"\b(18\s*U\.?S\.?C\.?\s*§?\s*2703|Stored Communications Act|"
    r"ECPA|Electronic Communications Privacy|pen register|"
    r"18\s*U\.?S\.?C\.?\s*§?\s*3123)\b",
    re.IGNORECASE,
)

# CI-3: First Amendment surveillance
_RE_FIRST_AMEND_TARGET = re.compile(
    # Stems use \w* (not \b) to match full word forms: organiz\w* = organizing/organized
    r"\b(?:"
    r"(?:protest|demonstration|rally|march|picket).{0,40}(?:monitor\w*|surveil\w*|photograph\w*|record\w*|document\w*)|"
    r"(?:monitor\w*|surveil\w*|photograph\w*|record\w*).{0,40}(?:protest|demonstration|rally|march|picket)|"
    r"political.{0,30}(?:organiz\w*|activit\w*|group\b|affili\w*)|"
    r"religious.{0,30}(?:monitor\w*|surveil\w*|organiz\w*|community\b|congregation\b)"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_RE_FIRST_AMEND_PREDICATE = re.compile(
    r"\b(specific.{0,20}criminal|articulable.{0,20}suspicion|probable cause|"
    r"nexus.{0,20}criminal|counter.?terrorism.{0,20}intelligence)\b",
    re.IGNORECASE,
)

# CI-4: Demographic + surveillance disparity
_RE_DEMOGRAPHIC = re.compile(
    r"\b(race|racial|ethnicity|ethnic|Black|Hispanic|Latino|Asian|"
    r"minority.{0,20}(community|neighborhood|area)|demographic)\b",
    re.IGNORECASE,
)
_RE_SURVEILLANCE_DEPLOYMENT = re.compile(
    r"\b(ALPR|facial recognition|license plate|surveillance camera|"
    r"gunshot detection|ShotSpotter|predictive policing|gang database)\b",
    re.IGNORECASE,
)
_RE_DISPARITY_ANALYSIS = re.compile(
    r"\b(impact.{0,20}analysis|disparate.{0,20}impact|equity.{0,20}review|"
    r"civil rights.{0,20}analysis|bias.{0,20}audit)\b",
    re.IGNORECASE,
)

# CI-5: Automated decision affecting liberty/property without human review
_RE_AUTO_DECISION = re.compile(
    r"\b(?:"
    r"(?:predictive|algorithmic|automated|AI.?generated|machine.?generated)"
    r".{0,40}(?:risk.?score|threat.?assessment|detain(?:tion)?|recommend(?:ation)?|decision)|"
    r"(?:risk.?score|threat.?assessment).{0,40}(?:detain|arrest|parole|bail|sentence)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_HUMAN_REVIEW = re.compile(
    r"\b(human.{0,20}review|officer.{0,20}review(?:ed|s)|supervisor.{0,20}approv|"
    r"final.{0,20}determin(?:ation)?.{0,30}human|discretion.{0,30}officer)\b",
    re.IGNORECASE,
)


class L6ConstitutionalImplication:
    """L-6 Constitutional Implication detector."""

    detector_id = "l6-constitutional-implication"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-6 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # CI-1: Location data aggregation without warrant
        if _RE_LOCATION_AGG.search(text) and not _RE_WARRANT_LANGUAGE.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CI-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.CRITICAL,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. IV",
                        "Cal. Const. Art. I § 1",
                        "Carpenter v. United States, 138 S. Ct. 2206 (2018)",
                    ],
                    legal_conclusion=(
                        "Document reflects aggregated location data collection without "
                        "warrant authorization. Carpenter v. United States (2018) held "
                        "that warrantless collection of historical CSLI constitutes a "
                        "Fourth Amendment search. Extended ALPR retention and pooled "
                        "location databases create the same 'detailed chronicle' that "
                        "Carpenter forbids absent a warrant based on probable cause. "
                        "Cal. Const. Art. I § 1 may provide broader protection."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes="CI-1: Carpenter mosaic -- location aggregation without warrant",
                )
            )

        # CI-2: Third-party digital records without ECPA/SCA predicate
        if _RE_THIRD_PARTY_DIGITAL.search(
            text
        ) and not _RE_LEGAL_PROCESS_SPECIFICITY.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CI-2"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. IV",
                        "18 USC § 2703",  # Stored Communications Act
                        "Cal. Const. Art. I § 1",
                    ],
                    legal_conclusion=(
                        "Document references legal process directed at digital service "
                        "providers without identifying the specific statutory authority. "
                        "Carpenter partially eroded the third-party doctrine for digital "
                        "records. The Stored Communications Act (18 USC § 2703) requires "
                        "varying levels of process depending on the type of records sought. "
                        "Absence of specific legal process identification is an audit gap."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="CI-2: third-party digital records -- legal process not identified",
                )
            )

        # CI-3: First Amendment surveillance without criminal nexus
        if _RE_FIRST_AMEND_TARGET.search(text) and not _RE_FIRST_AMEND_PREDICATE.search(
            text
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CI-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.CRITICAL,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. I",
                        "U.S. Const. amend. IV",
                        "Cal. Const. Art. I §§ 2, 3",
                        "NAACP v. Alabama, 357 U.S. 449 (1958)",
                    ],
                    legal_conclusion=(
                        "Document reflects surveillance targeting protected First Amendment "
                        "activity (protest, political organization, or religious community) "
                        "without articulating a specific criminal nexus or articulable "
                        "suspicion. Such targeting implicates the right of association "
                        "(NAACP v. Alabama), chilling effects on speech (Cal. Const. Art. I "
                        "§ 2), and Fourth Amendment protection of political beliefs. "
                        "Viewpoint-based surveillance requires compelling government interest."
                    ),
                    confidence=0.85,
                    source_finding_id=source_id,
                    notes="CI-3: First Amendment surveillance without criminal predicate",
                )
            )

        # CI-4: Demographic + surveillance without disparity analysis
        if (
            _RE_DEMOGRAPHIC.search(text)
            and _RE_SURVEILLANCE_DEPLOYMENT.search(text)
            and not _RE_DISPARITY_ANALYSIS.search(text)
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CI-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. XIV",
                        "Cal. Gov. § 12926",  # FEHA disparate impact
                        "42 USC § 1981",
                        "42 USC § 2000d",  # Title VI -- federal funding condition
                    ],
                    legal_conclusion=(
                        "Document references both demographic populations and surveillance "
                        "technology deployment without a disparate impact or equity analysis. "
                        "Racially disparate deployment of surveillance technology can violate "
                        "the Fourteenth Amendment Equal Protection Clause and Title VI "
                        "(42 USC § 2000d) where federal funds are involved. "
                        "An equity impact analysis is required before deployment."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="CI-4: demographic + surveillance without disparity analysis",
                )
            )

        # CI-5: Automated liberty/property decision without human review
        if _RE_AUTO_DECISION.search(text) and not _RE_HUMAN_REVIEW.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CI-5"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "U.S. Const. amend. XIV",
                        "Mathews v. Eldridge, 424 U.S. 319 (1976)",
                        "Cal. Const. Art. I § 7",  # Cal. due process
                    ],
                    legal_conclusion=(
                        "Document reflects automated or algorithmic decision-making "
                        "affecting liberty or property interests without documented "
                        "human review. Mathews v. Eldridge balancing requires weighing "
                        "the private interest, risk of erroneous deprivation, and "
                        "government interest. Fully automated decisions affecting "
                        "detention, bail, or parole without meaningful human review "
                        "fail procedural due process."
                    ),
                    confidence=0.75,
                    source_finding_id=source_id,
                    notes="CI-5: automated liberty/property decision without human review",
                )
            )

        return findings
