"""L-8 Case Law Currency -- odia_legal Phase 2.

Detects documents that rely on superseded, overruled, or significantly limited
legal authority. Government agency documents -- particularly use-of-force
policies, CPRA denials, surveillance contracts, and civil rights defenses --
frequently carry stale legal citations that no longer represent controlling law.

Rules implemented:

  CC-1  Third-Party Doctrine -- Smith v. Maryland Stale for Digital Records
        (Carpenter v. United States, 138 S. Ct. 2206 (2018))
        Smith v. Maryland (1979) held that phone call metadata conveyed to a
        third party carries no reasonable expectation of privacy. Carpenter
        (2018) substantially eroded this doctrine for digital location data,
        holding the third-party doctrine does not apply to seven days or more
        of CSLI. Documents that invoke Smith v. Maryland or the third-party
        doctrine for digital records, location data, or metadata without
        acknowledging Carpenter's limiting holding rely on stale authority.
        Signal: Smith v. Maryland or third-party doctrine + digital/location
        records context WITHOUT Carpenter citation.

  CC-2  Repealed CPRA Section Citations
        (Stats. 2021, ch. 614 (AB 473); eff. Jan. 1, 2023)
        The California Public Records Act was recodified from Government Code
        §§ 6250-6276.48 to §§ 7920-7930.215 effective January 1, 2023. The old
        sections were repealed. Documents citing §§ 6250-6276 as authority after
        2022 are citing repealed law. This is common in CPRA denial letters and
        agency policy documents that have not been updated since the recodification.
        Signal: Old CPRA section numbers (§ 6250, § 6254, § 6255, § 6276) WITHOUT
        a new § 7920 et seq. citation, suggesting the document was not updated after
        the 2023 recodification.

  CC-3  Pre-Riley Search-Incident-to-Arrest for Digital Devices
        (Riley v. California, 573 U.S. 373 (2014))
        Riley v. California (2014) unanimously held that officers must generally
        obtain a warrant before searching a cell phone found during an arrest.
        Pre-Riley doctrine (United States v. Robinson; Chimel v. California)
        permitted broad searches incident to arrest. Documents that assert
        search-incident-to-arrest authority over cell phones, smartphones, or
        digital devices without acknowledging Riley rely on superseded authority.
        Signal: search-incident-to-arrest + digital device/phone WITHOUT Riley.

  CC-4  Pre-AB 392 "Reasonable Force" Standard for California Law Enforcement
        (Cal. Pen. Code § 835a, as amended by AB 392, eff. Jan. 1, 2020)
        California AB 392 (2019) amended Penal Code § 835a to raise the standard
        for use of deadly force from "reasonable force" to force only when
        "necessary." The federal Graham v. Connor "objective reasonableness"
        standard remains applicable for federal civil rights claims, but
        California state law imposes a stricter "necessary" standard. A
        use-of-force policy that applies only the "reasonable force" standard
        without the California "necessary" standard is operating under pre-2020
        superseded state law.
        Signal: "reasonable force" + California LE use-of-force context WITHOUT
        "necessary" standard or AB 392 / § 835a citation.

  CC-5  Qualified Immunity Asserted Against California Constitutional Claims
        (Cal. SB 2, eff. Jan. 1, 2022; Cal. Pen. Code § 1021.7)
        California SB 2 (2021) eliminated qualified immunity as a defense to
        California constitutional rights claims under the Tom Bane Civil Rights
        Act. Qualified immunity remains available for federal § 1983 claims, but
        any document asserting qualified immunity as a complete defense to
        California state constitutional claims cites pre-SB 2 authority that is
        no longer valid for state law claims.
        Signal: qualified immunity + California constitutional claim WITHOUT
        SB 2 / § 1021.7 / Bane Act acknowledgment distinguishing federal and
        state claims.

Confidence calibration:
  0.85  Direct citation to the superseded authority + confirmed absence of
        the limiting/overruling precedent
  0.75  Strong contextual signal; superseded framework applied without update
  0.65  Moderate signal; superseded citation present but context may limit scope
"""

from __future__ import annotations

import hashlib
import logging
import re

from ._base import DocContext, LegalFinding, Severity

logger = logging.getLogger(__name__)


def _finding_id(ctx: DocContext, rule_id: str) -> str:
    return (
        "legal:l8:"
        + hashlib.sha256(f"{ctx.document_hash}:{rule_id}".encode()).hexdigest()[:12]
    )


# ---------------------------------------------------------------------------
# CC-1: Smith v. Maryland stale for digital records (pre-Carpenter)
# ---------------------------------------------------------------------------
_RE_SMITH_THIRD_PARTY = re.compile(
    r"\b(?:"
    r"Smith v\.? Maryland|"
    r"Miller v\.? United States.{0,30}(?:third.?party|no expectation)|"
    r"third.?party doctrine.{0,60}"
    r"(?:digital|electronic|location|metadata|cell|phone|email|subscriber)|"
    r"(?:digital|electronic|location|metadata|cell|phone|email|subscriber)"
    r".{0,60}third.?party doctrine"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_CARPENTER = re.compile(
    r"\b(?:"
    r"Carpenter v\.? United States|138 S\.? Ct\.? 2206|"
    r"Carpenter.{0,30}(?:CSLI|location|third.?party|warrant)|"
    r"mosaic theory.{0,30}(?:Carpenter|location|CSLI)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# CC-2: Repealed CPRA section citations (§ 6250-§ 6276)
# ---------------------------------------------------------------------------
# Old sections: 6250 (purpose), 6252 (definitions), 6253 (right to inspect),
# 6254 (exemptions), 6255 (catch-all), 6276 (enforcement)
_RE_OLD_CPRA = re.compile(
    r"\b(?:"
    r"Government Code §§? 62[5-7][0-9](?:\.[0-9]+)?|"
    r"Gov(?:\.|ernment) Code §§? 62[5-7][0-9](?:\.[0-9]+)?|"
    r"§§? 6254(?:\.[0-9]+)?|"
    r"§§? 6255|"
    r"§§? 6276(?:\.[0-9]+)?|"
    r"§§? 6250(?:\.[0-9]+)?"
    r")\b",
    re.IGNORECASE,
)
_RE_NEW_CPRA = re.compile(
    r"\b(?:"
    r"Government Code §§? 79[0-9]{2}(?:\.[0-9]+)?|"
    r"Gov(?:\.|ernment) Code §§? 79[0-9]{2}(?:\.[0-9]+)?|"
    r"§§? 79[0-9]{2}(?:\.[0-9]+)?|"
    r"CPRA.{0,30}(?:recodif\w*|2023|new section|revised section)"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# CC-3: Pre-Riley search incident to arrest for digital devices
# ---------------------------------------------------------------------------
# The phrase appears in two surface forms:
#   "search-incident-to-arrest" (hyphenated, as a doctrine name)
#   "search [device] incident to arrest" (device between search and incident to)
# Alternatives also cover device-first phrasing and Robinson/Chimel citations.
_RE_SITA_DIGITAL = re.compile(
    r"(?:"
    # hyphenated doctrine name anywhere near a device keyword (within 120 chars)
    r"search.{0,3}incident.{0,3}to.{0,3}arrest.{0,120}"
    r"(?:cell\s*phone|smartphone|mobile\s+(?:phone|device)|digital\s+device|"
    r"electronic\s+device|phone|tablet|laptop)|"
    # device keyword first, then "search incident to arrest" within 100 chars
    r"(?:cell\s*phone|smartphone|mobile\s+(?:phone|device)|digital\s+device|"
    r"electronic\s+device).{0,100}"
    r"search.{0,3}incident.{0,3}to.{0,3}(?:a\s+)?(?:lawful\s+)?arrest|"
    # "search [device] incident to [lawful] arrest" -- device between search and incident
    r"search\s+(?:cell\s*phones?|smartphones?|mobile\s+(?:phones?|devices?)|"
    r"digital\s+devices?|electronic\s+devices?|phones?)\s+incident\s+to\s+"
    r"(?:a\s+)?(?:lawful\s+)?arrest|"
    # Robinson or Chimel cited for a digital device
    r"(?:Robinson|Chimel).{0,60}(?:cell\s*phone|smartphone|digital|electronic\s+device)"
    r")",
    re.IGNORECASE | re.DOTALL,
)
_RE_RILEY = re.compile(
    r"\b(?:"
    r"Riley v\.? California|573 U\.?S\.? 373|"
    r"Riley.{0,30}(?:cell phone|warrant|smartphone|digital)|"
    r"warrant required.{0,30}(?:cell phone|smartphone|digital device)"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)

# ---------------------------------------------------------------------------
# CC-4: Pre-AB 392 "reasonable force" without "necessary" standard
# ---------------------------------------------------------------------------
_RE_REASONABLE_FORCE_LE = re.compile(
    r"\b(?:"
    r"reasonable force.{0,60}(?:officer|law enforcement|deputy|police|peace officer)|"
    r"(?:officer|law enforcement|deputy|police|peace officer).{0,60}reasonable force|"
    r"objective(?:ly)? reasonable.{0,40}(?:force|use of force)|"
    r"Graham v\.? Connor.{0,60}(?:California|state law|force)|"
    r"use.?of.?force.{0,40}reasonable"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_NECESSARY_STANDARD = re.compile(
    r"\b(?:"
    r"necessary(?:\s+to\s+\w+)?.{0,30}(?:force|deadly force|use of force)|"
    r"(?:force|deadly force).{0,30}necessary|"
    r"AB 392|"
    r"Penal Code §§? 835a|"
    r"Cal\.? Pen(?:al)?\.? Code §§? 835a|"
    r"necessary (?:standard|force standard|use.?of.?force)"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# CC-5: Qualified immunity asserted for California constitutional claims
# ---------------------------------------------------------------------------
_RE_QUALIFIED_IMMUNITY = re.compile(
    r"\b(?:"
    r"qualified immunity.{0,80}"
    r"(?:California|Cal\.|state.?law|Cal\. Const|Bane Act|state claim|"
    r"Tom Bane|Civil Rights Act)|"
    r"(?:California|Cal\.|state.?law|Cal\. Const|Bane Act|state claim)"
    r".{0,80}qualified immunity"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)
_RE_SB2_ACKNOWLEDGMENT = re.compile(
    r"\b(?:"
    r"SB 2.{0,20}(?:2021|qualified immunity|Bane Act)|"
    r"Penal Code §§? 1021\.7|"
    r"Cal\.? Pen(?:al)?\.? Code §§? 1021\.7|"
    r"qualified immunity.{0,40}(?:does not apply|not available|eliminated|"
    r"abolished).{0,40}(?:California|state|Bane Act)|"
    r"Tom Bane Civil Rights Act.{0,40}qualified immunity"
    r")\b",
    re.IGNORECASE | re.DOTALL,
)


class L8CaseLawCurrency:
    """L-8 Case Law Currency detector."""

    detector_id = "l8-case-law-currency"

    def detect(
        self,
        ctx: DocContext,
        resolver: object,
    ) -> list[LegalFinding]:
        try:
            return self._run(ctx)
        except Exception:  # noqa: BLE001
            logger.exception("L-8 failed on document %s", ctx.document_id)
            return []

    def _run(self, ctx: DocContext) -> list[LegalFinding]:
        findings: list[LegalFinding] = []
        text = ctx.text
        source_id = ctx.source_finding.get("id") if ctx.source_finding else None

        # CC-1: Smith v. Maryland / third-party doctrine without Carpenter
        if _RE_SMITH_THIRD_PARTY.search(text) and not _RE_CARPENTER.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CC-1"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Carpenter v. United States, 138 S. Ct. 2206 (2018)",
                        "Smith v. Maryland, 442 U.S. 735 (1979)",
                        "U.S. Const. amend. IV",
                        "Cal. Const. Art. I § 1",
                    ],
                    legal_conclusion=(
                        "Document invokes the third-party doctrine (Smith v. Maryland, "
                        "1979) for digital records or location data without acknowledging "
                        "Carpenter v. United States (2018), which substantially eroded "
                        "that doctrine for digital location data. Carpenter held that the "
                        "third-party doctrine does not apply to seven or more days of "
                        "cell-site location information, treating such collection as a "
                        "Fourth Amendment search requiring a warrant. Reliance on Smith v. "
                        "Maryland alone for digital records access is stale authority."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes="CC-1: Smith v. Maryland third-party doctrine stale -- Carpenter not cited",
                )
            )

        # CC-2: Repealed CPRA sections without recodification acknowledgment
        if _RE_OLD_CPRA.search(text) and not _RE_NEW_CPRA.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CC-2"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Gov. Code §§ 7920-7930.215",
                        "Stats. 2021, ch. 614 (AB 473)",
                    ],
                    legal_conclusion=(
                        "Document cites California Public Records Act sections from the "
                        "pre-2023 numbering scheme (Government Code §§ 6250-6276). Those "
                        "sections were repealed and recodified to §§ 7920-7930.215 effective "
                        "January 1, 2023 (AB 473, Stats. 2021, ch. 614). Citations to the "
                        "old section numbers are citations to repealed law. CPRA denial "
                        "letters, agency policies, and legal opinions that have not been "
                        "updated to the new section numbers may also contain outdated "
                        "interpretations from pre-recodification case law."
                    ),
                    confidence=0.85,
                    source_finding_id=source_id,
                    notes="CC-2: repealed CPRA section numbers cited (§ 6250-6276 era) without § 7920 recodification",
                )
            )

        # CC-3: Search incident to arrest for digital devices without Riley
        if _RE_SITA_DIGITAL.search(text) and not _RE_RILEY.search(text):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CC-3"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Riley v. California, 573 U.S. 373 (2014)",
                        "U.S. Const. amend. IV",
                        "Cal. Const. Art. I § 13",
                    ],
                    legal_conclusion=(
                        "Document asserts search-incident-to-arrest authority over cell "
                        "phones or digital devices without citing Riley v. California "
                        "(2014). The Supreme Court unanimously held in Riley that the "
                        "search-incident-to-arrest exception does not justify a warrantless "
                        "search of a cell phone's digital contents. Pre-Riley authorities "
                        "(United States v. Robinson; Chimel v. California) no longer support "
                        "warrantless cell phone searches incident to arrest. A warrant "
                        "supported by probable cause is required absent exigent circumstances."
                    ),
                    confidence=0.80,
                    source_finding_id=source_id,
                    notes="CC-3: search-incident-to-arrest for digital devices without Riley v. California",
                )
            )

        # CC-4: "Reasonable force" standard without AB 392 "necessary" standard
        if _RE_REASONABLE_FORCE_LE.search(text) and not _RE_NECESSARY_STANDARD.search(
            text
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CC-4"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Pen. Code § 835a (as amended by AB 392, eff. Jan. 1, 2020)",
                        "Graham v. Connor, 490 U.S. 386 (1989)",
                        "AB 392 (2019)",
                    ],
                    legal_conclusion=(
                        "Document applies the 'reasonable force' standard to California law "
                        "enforcement use of force without acknowledging that California AB 392 "
                        "(2019) amended Penal Code § 835a to impose a stricter 'necessary' "
                        "standard effective January 1, 2020. Under California law, deadly "
                        "force is justified only when 'necessary to defend against an imminent "
                        "threat of death or serious bodily injury.' The federal Graham v. "
                        "Connor 'objective reasonableness' standard remains applicable to "
                        "§ 1983 federal claims, but California state law requires more. A "
                        "use-of-force policy citing only 'reasonable force' without the "
                        "California 'necessary' standard is operating under pre-2020 "
                        "superseded state law."
                    ),
                    confidence=0.78,
                    source_finding_id=source_id,
                    notes="CC-4: pre-AB 392 'reasonable force' standard without 'necessary' standard (Cal. Pen. Code § 835a)",
                )
            )

        # CC-5: Qualified immunity asserted for California constitutional claims
        #        without SB 2 / Cal. Pen. Code § 1021.7 acknowledgment
        if _RE_QUALIFIED_IMMUNITY.search(text) and not _RE_SB2_ACKNOWLEDGMENT.search(
            text
        ):
            findings.append(
                LegalFinding(
                    finding_id=_finding_id(ctx, "CC-5"),
                    sub_detector=self.detector_id,
                    severity=Severity.HIGH,
                    document_hash=ctx.document_hash,
                    document_id=ctx.document_id,
                    statutes_applied=[
                        "Cal. Pen. Code § 1021.7",
                        "Cal. SB 2 (2021), eff. Jan. 1, 2022",
                        "Tom Bane Civil Rights Act, Cal. Civ. Code § 52.1",
                    ],
                    legal_conclusion=(
                        "Document invokes qualified immunity as a defense in connection "
                        "with California constitutional claims without acknowledging that "
                        "California SB 2 (2021) eliminated qualified immunity as a defense "
                        "to claims brought under California law (Cal. Pen. Code § 1021.7, "
                        "eff. Jan. 1, 2022). Qualified immunity remains available for federal "
                        "§ 1983 claims, but any assertion of qualified immunity against a "
                        "California civil rights claim under the Bane Act or California "
                        "Constitution is citing pre-SB 2 authority that no longer controls "
                        "for state law claims."
                    ),
                    confidence=0.78,
                    source_finding_id=source_id,
                    notes="CC-5: qualified immunity asserted for California claims without SB 2 / Pen. Code § 1021.7",
                )
            )

        return findings
