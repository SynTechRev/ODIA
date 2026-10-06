"""L-9 Statute Citation Auditor -- odia_legal Phase 2.

Uses the CalCitation and StatuteCitation structured parsers rather than raw
regex to identify citation-level anomalies. This detector runs the full
citation parsing pass that other detectors approximate with heuristic patterns,
providing precise section-number findings and catching format variations
(hyphenated section numbers, dropped § symbols, bare numeric citations) that
regex misses.

Rules implemented:

  SA-1  Old CPRA Government Code Section (Structured)
        Gov. Code §§ 6250-6276 were repealed and recodified to §§ 7920-7930.215
        effective January 1, 2023 (Stats. 2021, ch. 614, AB 473). This rule uses
        parse_cal_citations() to find structured Gov. Code citations whose section
        number falls in the 6250-6276 range, then reports the exact section(s)
        cited. Complement to L-8 CC-2: this rule catches informal citations that
        the regex misses (e.g., "Gov. Code 6254" without §) and reports the
        precise section numbers for audit records.
        Signal: parsed CalCitation with code == "Gov. Code" and section root
        as integer in range 6250-6276.

  SA-2  CCP § 1281.97/98 Arbitration Cost-Shifting Without § 1281.96 Reporting
        Cal. Code Civ. Proc. § 1281.97 (employer cost-shifting for arbitration
        initiation fees) and § 1281.98 (consumer cost-shifting) create mandatory
        protections for employees and consumers in arbitration agreements. Cal.
        Code Civ. Proc. § 1281.96 imposes a separate mandatory public reporting
        requirement: businesses that require arbitration for employment or consumer
        disputes must collect and publish statistical data on arbitration outcomes.
        A contract or policy that cites §§ 1281.97 or 1281.98 without citing
        § 1281.96 may be acknowledging the cost-shifting protection while omitting
        the companion transparency obligation. This is directly relevant to the
        C.O.N.T.R.A. gig economy and consumer contract analysis.
        Signal: CCP § 1281.97 or § 1281.98 cited; § 1281.96 absent.

  SA-3  Pen. Code § 832.7 Without SB 1421 Mandatory Disclosure Scope
        Cal. Pen. Code § 832.7 historically provided broad confidentiality for
        peace officer personnel records in CPRA responses. SB 1421 (2018, eff.
        Jan. 1, 2019) amended § 832.7 to add subsection (b), which mandates
        disclosure of records related to: (1) serious use of force by the
        officer, (2) sustained findings of dishonesty, (3) sustained findings
        of sexual assault, and (4) sustained findings of unlawful arrest or
        search. A CPRA denial or document that cites § 832.7 broadly without
        acknowledging the § 832.7(b) mandatory disclosure categories is applying
        pre-2019 law and potentially withholding records that must be disclosed.
        Signal: Pen. Code § 832.7 cited WITHOUT a specific "(b)" subsection
        reference or textual acknowledgment of the SB 1421 categories.

  SA-4  Federal Grant Citation Without California Oversight Companion
        Federal grant programs, most commonly Byrne JAG (34 U.S.C. § 10152
        et seq.), require local governmental compliance with both federal
        conditions and California state law. A document that cites only a
        federal USC authority (title 28, 34, or 42 -- Justice, COPS, or civil
        rights grant programs) without any parsed California statute governing
        the same subject creates an oversight gap: the document may be operating
        under the federal framework alone, without the California procurement,
        transparency, and civil rights statutes that impose additional obligations
        on local agencies.
        Signal: USC citations in grant-relevant titles (28, 34, 42) present;
        zero Cal. Gov. Code citations in the same document.

  SA-5  CPRA-Adjacent Document With No Parsed Statute Citations
        A document that uses the language of a CPRA response (terms like
        "public record", "exempt", "withhold", "disclose") without citing any
        parseable California statute is presenting legal conclusions without
        statutory authority. This is a common pattern in informal CPRA denials
        where an agency withholds records based on unstated exemptions. The
        absence of any statute citation does not exclude regulatory authority;
        however, combined with 3+ CPRA-adjacent terms, it is a strong signal
        that the document relies on implicit or unstated legal authority.
        Signal: 3+ CPRA-adjacent terms in text; zero CalCitation objects parsed.

Confidence calibration:
  0.90  SA-1 structured exact section match (very low false-positive rate)
  0.80  SA-3 § 832.7 without (b) (direct structural citation gap)
  0.78  SA-2 § 1281.97/98 without § 1281.96 (arbitration accountability gap)
  0.70  SA-4 federal grant without California companion (context-dependent)
  0.65  SA-5 CPRA-adjacent without statute citations (document-type sensitive)
"""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Sequence

from ..statute_citation import CalCitation, parse_cal_citations, parse_usc_citations
from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l9:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# ---------------------------------------------------------------------------
# SA-1 helpers: old CPRA section range detection
# ---------------------------------------------------------------------------
_OLD_CPRA_ROOT_MIN = 6250
_OLD_CPRA_ROOT_MAX = 6276


def _is_old_cpra_section(cite: CalCitation) -> bool:
    if cite.code != "Gov. Code":
        return False
    try:
        root = int(cite.section.split(".")[0])
        return _OLD_CPRA_ROOT_MIN <= root <= _OLD_CPRA_ROOT_MAX
    except ValueError:
        return False


def _has_new_cpra(citations: Sequence[CalCitation]) -> bool:
    for c in citations:
        if c.code != "Gov. Code":
            continue
        try:
            root = int(c.section.split(".")[0])
            if root >= 7920:
                return True
        except ValueError:
            continue
    return False


# ---------------------------------------------------------------------------
# SA-3 helpers: § 832.7(b) acknowledgment
# ---------------------------------------------------------------------------
_RE_832B = re.compile(
    r"\b(?:"
    r"§§?\s*832\.7\s*\(b\)|"
    r"SB\s*1421|"
    r"832\.7\(b\).{0,60}(?:use of force|dishonest|sexual assault|unlawful arrest)|"
    r"mandatory disclosure.{0,40}(?:peace officer|personnel record)|"
    r"must be disclosed.{0,30}(?:officer|force|use of force)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# SA-4 helpers: grant-relevant USC titles
# ---------------------------------------------------------------------------
_GRANT_USC_TITLES = {28, 34, 42}  # Justice / COPS / civil rights


def _has_cal_gov_code(citations: Sequence[CalCitation]) -> bool:
    return any(c.code == "Gov. Code" for c in citations)


# ---------------------------------------------------------------------------
# SA-5 helpers: CPRA-adjacent terms
# ---------------------------------------------------------------------------
_CPRA_ADJACENT = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\bpublic record",
        r"\b(?:exempt|exemption)\b",
        r"\bwithhold\b",
        r"\bdisclose\b",
        r"\bdisclosure\b",
        r"\bconfidential\b",
        r"\brecords request\b",
        r"\bCPRA\b",
    ]
]
_CPRA_ADJACENT_THRESHOLD = 3


class L9StatuteCitationAuditor:
    """L-9 Statute Citation Auditor detector."""

    detector_id = "l9-statute-citation-auditor"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-9 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        cal_citations = parse_cal_citations(text)
        usc_citations = parse_usc_citations(text)

        # SA-1: Old CPRA Gov. Code sections via structured parser
        old_cpra = [c for c in cal_citations if _is_old_cpra_section(c)]
        if old_cpra and not _has_new_cpra(cal_citations):
            cited = ", ".join(sorted({c.canonical for c in old_cpra}))
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "SA-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. Code §§ 7920-7930.215",
                        "Stats. 2021, ch. 614 (AB 473), eff. Jan. 1, 2023",
                    ],
                    legal_conclusion=(
                        f"Structured citation parser identified reference(s) to repealed "
                        f"California Public Records Act section(s): {cited}. These sections "
                        f"were repealed and recodified to Government Code §§ 7920-7930.215 "
                        f"effective January 1, 2023 (AB 473, Stats. 2021, ch. 614). Any "
                        f"legal analysis, exemption assertion, or procedural right based on "
                        f"the old section numbering should be re-verified against the current "
                        f"§ 7920 et seq. text, as some provisions were amended during "
                        f"recodification."
                    ),
                    confidence=0.90,
                    source_finding_id=source_id,
                    notes=f"SA-1: old CPRA sections via structured parser: {cited}",
                )
            )

        # SA-2: CCP § 1281.97/98 without § 1281.96
        arb_cost = [
            c
            for c in cal_citations
            if c.code == "CCP" and c.section in ("1281.97", "1281.98")
        ]
        arb_report = any(
            c.code == "CCP" and c.section == "1281.96" for c in cal_citations
        )
        if arb_cost and not arb_report:
            cited_cost = ", ".join(sorted({c.canonical for c in arb_cost}))
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "SA-2"),
                    sub_detector=self.detector_id,
                    severity=Severity.MEDIUM,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Code Civ. Proc. § 1281.96",
                        "Cal. Code Civ. Proc. § 1281.97",
                        "Cal. Code Civ. Proc. § 1281.98",
                    ],
                    legal_conclusion=(
                        f"Document cites {cited_cost} (California mandatory arbitration "
                        f"cost-shifting provisions) without citing Cal. Code Civ. Proc. "
                        f"§ 1281.96, which requires companies that impose mandatory "
                        f"arbitration on employees or consumers to collect and publicly "
                        f"report statistics on arbitration outcomes. The cost-shifting "
                        f"protections and the transparency reporting requirement are "
                        f"companion provisions of the 2019 FAIR Act (AB 51). Citing "
                        f"§ 1281.97 or § 1281.98 without § 1281.96 may indicate the "
                        f"document was drafted to acknowledge individual protections while "
                        f"omitting the systemic accountability obligation."
                    ),
                    confidence=0.78,
                    source_finding_id=source_id,
                    notes=f"SA-2: CCP arbitration cost-shifting ({cited_cost}) without § 1281.96 reporting",
                )
            )

        # SA-3: Pen. Code § 832.7 without SB 1421 (§ 832.7(b)) acknowledgment
        shield_cite = [
            c
            for c in cal_citations
            if c.code == "Pen. Code"
            and c.section in ("832.7", "832.8")
            and "(b)" not in c.subsection_path
        ]
        if shield_cite and not _RE_832B.search(text):
            cited_shield = ", ".join(sorted({c.canonical for c in shield_cite}))
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "SA-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Pen. Code § 832.7(b)",
                        "SB 1421 (2018), eff. Jan. 1, 2019",
                        "SB 16 (2021), eff. Jan. 1, 2022",
                    ],
                    legal_conclusion=(
                        f"Document cites {cited_shield} as authority for withholding or "
                        f"limiting disclosure of peace officer records, without acknowledging "
                        f"§ 832.7(b)'s mandatory disclosure categories. SB 1421 (2018) amended "
                        f"§ 832.7 to add subsection (b), which requires disclosure of records "
                        f"related to: serious use of force, sustained findings of dishonesty "
                        f"in the performance of duties, sexual assault, and unlawful arrest or "
                        f"search. Invoking § 832.7 without the SB 1421 carve-outs applies "
                        f"pre-2019 law and may result in unlawful withholding of records that "
                        f"must now be disclosed. SB 16 (2021) further expanded the categories "
                        f"effective January 1, 2022."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes=f"SA-3: Pen. Code § 832.7 cited ({cited_shield}) without SB 1421 § 832.7(b)",
                )
            )

        # SA-4: Federal grant citation without California oversight companion
        grant_usc = [c for c in usc_citations if c.title in _GRANT_USC_TITLES]
        if grant_usc and not _has_cal_gov_code(cal_citations):
            cited_usc = ", ".join(
                sorted({f"{c.title} U.S.C. § {c.section}" for c in grant_usc})
            )
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "SA-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.MEDIUM,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "34 U.S.C. § 10152 (Byrne JAG)",
                        "Cal. Gov. Code §§ 26220-26229 (county purchasing)",
                        "Cal. Gov. Code § 7928.710 (CPRA -- grant records)",
                    ],
                    legal_conclusion=(
                        f"Document cites federal statute(s) {cited_usc} (in a Justice, "
                        f"COPS, or civil rights grant title) without any parsed California "
                        f"Government Code companion statute. Federal grant programs require "
                        f"local agencies to comply with both federal conditions and California "
                        f"state procurement, oversight, and transparency statutes. A document "
                        f"that operates only under the federal framework and omits the "
                        f"California statutory layer may be hiding additional obligations "
                        f"imposed by state law, including procurement requirements, public "
                        f"records disclosure duties for grant documents, and civil rights "
                        f"compliance certifications required under California law."
                    ),
                    confidence=0.70,
                    source_finding_id=source_id,
                    notes=f"SA-4: federal grant USC citation ({cited_usc}) with no Cal. Gov. Code companion",
                )
            )

        # SA-5: CPRA-adjacent language with zero parsed statute citations
        if not cal_citations and not usc_citations:
            hits = sum(1 for pat in _CPRA_ADJACENT if pat.search(text))
            if hits >= _CPRA_ADJACENT_THRESHOLD:
                findings.append(
                    LegalFinding(
                        finding_id=_finding_id(ctx, "SA-5"),
                        sub_detector=self.detector_id,
                        severity=Severity.MEDIUM,
                        document_hash=ctx.document_hash,
                        document_id=ctx.document_id,
                        statutes_applied=[
                            "Cal. Gov. Code §§ 7920-7930.215 (CPRA)",
                        ],
                        legal_conclusion=(
                            f"Document uses CPRA-adjacent terminology "
                            f"({hits} signal terms matched) but contains no parseable "
                            f"California or federal statute citations. Records responses, "
                            f"exemption assertions, and withholding decisions must identify "
                            f"the specific statutory exemption or authority on which they "
                            f"rely. A document that withholds, redacts, or conditions "
                            f"disclosure without citing a specific statute section does not "
                            f"satisfy the CPRA's requirement that any exemption be justified "
                            f"by citing the specific provision of law that makes the record "
                            f"exempt from disclosure (Cal. Gov. Code § 7922.000(b))."
                        ),
                        confidence=0.65,
                        source_finding_id=source_id,
                        notes=f"SA-5: CPRA-adjacent language ({hits} terms) with zero parsed statute citations",
                    )
                )

        return findings
