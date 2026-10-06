"""L-7 Regulatory Authority -- odia_legal Phase 2.

Detects documents where a government agency purports to act beyond its
delegated statutory authority, bypasses required rulemaking procedures,
conflicts with preempting state law, improperly sub-delegates discretion to
a private contractor, or invokes emergency powers without the required
legislative findings.

Rules implemented:

  RA-1  Ultra Vires Action (Cal. Gov. Code § 11342; Cal. Const. Art. XI § 5)
        An agency may act only within the scope of its enabling authority.
        Documents that describe significant government actions -- procurements,
        surveillance deployments, data-sharing programs -- without citing any
        enabling statute are an audit gap: the agency has either failed to
        articulate its authority or is acting without one.
        Signal: significant action language (contract, surveillance, data
        sharing) with no statutory citation.

  RA-2  APA Rulemaking Bypass (Cal. Gov. Code §§ 11340-11361; 5 USC § 553)
        Binding agency directives of general applicability must be adopted
        through notice-and-comment rulemaking. An agency may not impose
        mandatory obligations on officers, employees, or the public through
        an internal policy memo or directive without following the California
        APA. These "shadow regulations" are void if not adopted through OAL.
        Signal: binding directive language (shall/must/required) with no
        rulemaking or OAL citation.

  RA-3  Conflict with Preempting State Statute (Cal. Const. Art. XI § 7)
        California Constitution Art. XI § 7 provides that a charter city's
        ordinance or regulation is invalid to the extent it conflicts with
        general state law in a field the Legislature has preempted. The CPRA,
        AB 481, SB 1421, and SB 978 are fully preempted fields.
        Signal: local policy attempting to restrict or expand obligations in
        a state-preempted field without citing consistency with state law.

  RA-4  Sub-Delegation to Private Contractor Without Standards
        (Whitman v. Am. Trucking Ass'ns, 531 U.S. 457 (2001);
         Cal. Const. Art. IV § 1 non-delegation)
        A government agency may not abdicate its statutory function by
        delegating final decision-making authority to a private contractor
        without specifying legal standards that the contractor must follow.
        Surveillance technology contracts (Flock Safety, Axon, PredPol) that
        give vendors sole discretion over significant functions are the primary
        corpus signal.
        Signal: contractor discretion language without corresponding government
        oversight standards.

  RA-5  Emergency Action Without Required Legislative Finding
        (Cal. Gov. Code §§ 11346.1, 11349.1)
        Emergency or urgency regulations bypass normal notice-and-comment but
        require a specific finding of immediate threat to public health, safety,
        or welfare and OAL review within 180 days. Emergency ordinances similarly
        require specific findings. Absence of those findings is an APA violation.
        Signal: emergency regulation/urgency ordinance without required finding
        language.

Confidence calibration:
  0.85  Clear statutory trigger with explicit conflict or absence marker
  0.75  Strong signal; absence of required element confirmed
  0.70  Moderate signal; context may explain absence
  0.60  Weak signal; further review required
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l7:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# ---------------------------------------------------------------------------
# RA-1: Significant action without enabling authority
# ---------------------------------------------------------------------------
_RE_SIGNIFICANT_ACTION = re.compile(
    r"\b(?:"
    # High-value contracts
    r"(?:contract|agreement|MOU|memorandum of understanding).{0,40}"
    r"(?:\$[\d,]{4,}|thousand|million|hundred thousand)|"
    # Surveillance deployment
    r"(?:deploy|install|operat\w+|implement\w*).{0,40}"
    r"(?:ALPR|facial recognition|body.?worn|drone|UAV|camera system|"
    r"ShotSpotter|gunshot detection|license plate reader)|"
    # Data-sharing program
    r"(?:data.?sharing|information.?sharing|data.?exchange).{0,30}"
    r"(?:program|agreement|arrangement|system)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_ENABLING_AUTHORITY = re.compile(
    r"\b(?:"
    r"pursuant to|authorized (?:by|under)|authority of|"
    r"in accordance with (?:Government|Cal\.|California|Penal|Public Contract|"
    r"Health|Education|Vehicle|Labor) Code|"
    r"under (?:Government Code|Cal\.|California|Public Contract Code|"
    r"Penal Code|Health & Safety|Education Code|Vehicle Code|"
    r"34 U\.?S\.?C|42 U\.?S\.?C|28 C\.?F\.?R)|"
    r"§\s*\d{3,}|U\.S\.C\.|C\.F\.R\.|Cal\. Code Regs?"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# RA-2: Binding directive without APA rulemaking
# ---------------------------------------------------------------------------
_RE_BINDING_DIRECTIVE = re.compile(
    r"\b(?:"
    r"(?:policy|directive|order|instruction|guideline|standard|protocol)"
    r".{0,30}(?:shall|must|is required|are required|is prohibited|are prohibited)|"
    r"(?:all|every|each).{0,15}(?:officer|employee|department|unit|personnel)"
    r".{0,30}(?:shall|must|is required|are required)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_RULEMAKING_CITATION = re.compile(
    r"\b(?:"
    r"notice.?of.?proposed.?rulemaking|notice.?and.?comment|"
    r"public comment period|"
    r"Office of Administrative Law|OAL.{0,20}approv\w*|"
    r"California Regulatory Notice Register|Cal\. Reg\. Notice|"
    r"Government Code § 1134[0-9]|5 U\.?S\.?C\.? § 553|"
    r"APA.{0,20}(?:rulemaking|procedure)|"
    r"adopted (?:pursuant to|under) (?:the )?(?:Cal\. )?APA"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# RA-3: Local policy conflicting with preempted state field
# ---------------------------------------------------------------------------
_RE_LOCAL_RESTRICTION = re.compile(
    r"\b(?:"
    r"(?:city|county|district|local).{0,30}"
    r"(?:policy|ordinance|regulation|rule|resolution).{0,40}"
    r"(?:requir\w+|prohibit\w+|restrict\w+|limit\w+|expand\w+|"
    r"provide\w*|establish\w*|creat\w*).{0,30}"
    r"(?:exemption|exception|disclosure|access|retention|use|deployment)|"
    r"(?:more restrictive|less restrictive|stricter than|broader than)"
    r".{0,30}state law"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_PREEMPTED_FIELD = re.compile(
    r"\b(?:"
    r"CPRA|California Public Records Act|"
    r"Government Code § 792[0-9]|Government Code §§ 7920|"
    r"AB 481|Government Code § 36045|"
    r"SB 1421|Penal Code § 832\.7|"
    r"SB 978|body.?worn camera policy|"
    r"POST (?:training|certification|standard)"
    r")\b",
    re.IGNORECASE,
)
_RE_PREEMPTION_ACKNOWLEDGMENT = re.compile(
    r"\b(?:"
    r"(?:state law|state statute) (?:preempts|controls|governs)|"
    r"consistent with (?:state law|state statute|California law)|"
    r"subject to (?:state|California).{0,20}(?:requirement|law|statute)|"
    r"preempted by|no (?:greater|fewer|less) than state"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# RA-4: Sub-delegation to private contractor without oversight standards
# ---------------------------------------------------------------------------
_RE_CONTRACTOR_DISCRETION = re.compile(
    r"\b(?:"
    r"(?:contractor|vendor|company|service provider|provider).{0,50}"
    r"(?:shall determine|has (?:sole )?discretion|may decide|"
    r"at.{0,15}(?:sole|its|their) discretion|final (?:decision|authority)|"
    r"sole authority)|"
    r"(?:delegate\w*|transfer\w*|assign\w*).{0,40}"
    r"(?:authority|power|discretion|responsibility).{0,30}"
    r"(?:contractor|vendor|company|service provider)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_OVERSIGHT_STANDARDS = re.compile(
    r"\b(?:"
    r"subject to (?:agency|city|county|government|department).{0,30}"
    r"(?:approval|oversight|review|supervision|control)|"
    r"(?:oversight|supervision).{0,20}(?:committee|board|officer|official)|"
    r"standards.{0,30}(?:set|established|defined).{0,30}"
    r"(?:by|in).{0,20}(?:city|county|agency|law|statute|contract)|"
    r"does not relieve.{0,40}(?:agency|city|county|department).{0,30}"
    r"(?:responsibility|liability|obligation)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# RA-5: Emergency action without required finding
# ---------------------------------------------------------------------------
_RE_EMERGENCY_ACTION = re.compile(
    r"\b(?:"
    r"emergency (?:regulation|ordinance|order|rule|policy|declaration)|"
    r"urgency (?:ordinance|statute|measure|regulation)|"
    r"interim (?:regulation|policy|rule).{0,20}(?:effect\w*|immediat\w*)|"
    r"immediate(?:ly)? (?:effective|in effect)"
    r")\b",
    re.IGNORECASE,
)
_RE_EMERGENCY_FINDING = re.compile(
    r"\b(?:"
    r"immediate.{0,30}(?:threat|peril|danger).{0,30}"
    r"(?:public health|public safety|public welfare|general welfare)|"
    r"finding.{0,30}(?:imminent|immediate|urgent|emergency).{0,30}"
    r"(?:threat|necessity|peril)|"
    r"Government Code § 11346\.1|"
    r"(?:urgency|emergency).{0,20}finding\w*|"
    r"declared.{0,30}(?:emergency|urgency).{0,30}(?:health|safety|welfare)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)


class L7RegulatoryAuthority:
    """L-7 Regulatory Authority detector."""

    detector_id = "l7-regulatory-authority"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-7 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # RA-1: Significant action without enabling authority
        if _RE_SIGNIFICANT_ACTION.search(text) and not _RE_ENABLING_AUTHORITY.search(
            text
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "RA-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. Code § 11342",
                        "Cal. Const. Art. XI § 5",
                        "Cal. Const. Art. XI § 7",
                    ],
                    legal_conclusion=(
                        "Document describes a significant government action -- procurement, "
                        "surveillance deployment, or data-sharing program -- without citing "
                        "any enabling statutory authority. An agency may act only within the "
                        "scope of its enabling legislation. Failure to identify the authorizing "
                        "statute is an ultra vires audit gap. Cal. Gov. Code § 11342 requires "
                        "that agency regulations be within the scope of granted authority."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes="RA-1: significant action without enabling authority cited",
                )
            )

        # RA-2: Binding directive without APA rulemaking
        if _RE_BINDING_DIRECTIVE.search(text) and not _RE_RULEMAKING_CITATION.search(
            text
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "RA-2"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. Code §§ 11340-11361",
                        "Cal. Gov. Code § 11342.600",  # definition of regulation
                        "5 USC § 553",
                    ],
                    legal_conclusion=(
                        "Document contains mandatory directive language (shall/must/required) "
                        "of general applicability without citing adoption through notice-and-comment "
                        "rulemaking under the California APA (Gov. Code §§ 11340-11361). "
                        "A directive that imposes binding obligations on officers, employees, "
                        "or the public constitutes a 'regulation' under Cal. Gov. Code § 11342.600 "
                        "and is void unless adopted through Office of Administrative Law review. "
                        "Shadow regulations that bypass OAL are unenforceable."
                    ),
                    confidence=0.72,
                    source_finding_id=source_id,
                    notes="RA-2: binding policy directive without APA rulemaking citation",
                )
            )

        # RA-3: Local policy in state-preempted field without preemption acknowledgment
        if (
            _RE_LOCAL_RESTRICTION.search(text)
            and _RE_PREEMPTED_FIELD.search(text)
            and not _RE_PREEMPTION_ACKNOWLEDGMENT.search(text)
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "RA-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Const. Art. XI § 7",
                        "Cal. Gov. Code § 7920 et seq.",  # CPRA (preempted field)
                        "Cal. Gov. Code § 36045",  # AB 481 (preempted field)
                    ],
                    legal_conclusion=(
                        "Document reflects a local policy creating obligations or restrictions "
                        "in a field preempted by state law (CPRA, AB 481, SB 1421, or SB 978) "
                        "without acknowledging the preemption framework or affirming consistency "
                        "with state law. Cal. Const. Art. XI § 7 provides that a local ordinance "
                        "or regulation is invalid to the extent it conflicts with preempting "
                        "general law. Local rules that expand or restrict preempted fields "
                        "without explicit legislative authority are void."
                    ),
                    confidence=0.75,
                    source_finding_id=source_id,
                    notes="RA-3: local policy in preempted field without preemption acknowledgment",
                )
            )

        # RA-4: Contractor discretion without oversight standards
        if _RE_CONTRACTOR_DISCRETION.search(
            text
        ) and not _RE_OVERSIGHT_STANDARDS.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "RA-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Const. Art. IV § 1",  # non-delegation
                        "Whitman v. Am. Trucking Ass'ns, 531 U.S. 457 (2001)",
                        "Cal. Gov. Code § 1090",  # conflict of interest
                    ],
                    legal_conclusion=(
                        "Document grants a private contractor sole or final discretion over "
                        "a government function without specifying the legal standards the "
                        "contractor must apply or the oversight mechanism the agency retains. "
                        "Under the non-delegation doctrine (Whitman v. Am. Trucking Ass'ns) "
                        "and Cal. Const. Art. IV § 1, a public agency may not abdicate its "
                        "statutory function to a private party. Surveillance technology "
                        "contracts that vest vendors with discretion over law enforcement "
                        "functions require explicit agency oversight standards."
                    ),
                    confidence=0.72,
                    source_finding_id=source_id,
                    notes="RA-4: contractor discretion without agency oversight standards",
                )
            )

        # RA-5: Emergency action without required legislative finding
        if _RE_EMERGENCY_ACTION.search(text) and not _RE_EMERGENCY_FINDING.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "RA-5"),
                    sub_detector=self.detector_id,
                    severity=Severity.MEDIUM,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. Code § 11346.1",  # emergency regulation procedure
                        "Cal. Gov. Code § 11349.1",  # OAL review standards
                        "Cal. Gov. Code § 36937",  # urgency ordinance findings
                    ],
                    legal_conclusion=(
                        "Document invokes emergency or urgency rulemaking authority without "
                        "the required finding of immediate threat to public health, safety, "
                        "or welfare. Cal. Gov. Code § 11346.1 requires that an emergency "
                        "regulation include a written finding that the regulation is necessary "
                        "for immediate preservation of the public peace, health, safety, or "
                        "general welfare. Cal. Gov. Code § 36937 imposes the same finding "
                        "requirement for urgency ordinances. Absence of the required finding "
                        "renders the emergency action procedurally defective."
                    ),
                    confidence=0.72,
                    source_finding_id=source_id,
                    notes="RA-5: emergency/urgency action without required legislative finding",
                )
            )

        return findings
