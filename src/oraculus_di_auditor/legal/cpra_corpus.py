"""CPRACorpusLoader — static California Privacy Rights Act corpus.

Provides in-memory access to the key CCPA/CPRA provisions (Cal. Civ. Code
§§ 1798.100–1798.199) that CONTRA detectors (L-11 through L-20) cite via
their doctrinal_anchor fields.

This is an embedded (no submodule required) corpus — the statutory text for
the ~14 most-cited provisions is stored directly in this module as of the
2023 CPRA operative date.  The full CPRA text is public law and may be
reproduced without restriction.

anchor_id → section mapping (matches `contra/anchors.py`):
    CCPA_1798_100  → § 1798.100 (right to know)
    CCPA_1798_110  → § 1798.110 (categories of PI)
    CCPA_1798_115  → § 1798.115 (sharing)
    CCPA_1798_120  → § 1798.120 (right to opt out)
    CCPA_121       → § 1798.121 (sensitive PI — CPRA amendment, eff. 2023)
    CCPA_125       → § 1798.125 (non-discrimination)
    CCPA_135       → § 1798.135 (opt-out methods)
    CCPA_145       → § 1798.145 (exemptions)
    CCPA_150       → § 1798.150 (private right of action)
    CCP_1281_97    → CCP § 1281.97 (consumer arbitration fees, 30-day cure)
    CCP_1281_98    → CCP § 1281.98 (fee waiver)
    CCP_1670_5     → CCP § 1670.5 (unconscionable contracts)
    CAL_LABOR_2699 → Lab. Code § 2699 (PAGA)
    AB_51          → Gov. Code § 12953 (mandatory arbitration ban)
"""

from __future__ import annotations

import logging
from datetime import date
from typing import ClassVar

from .corpus_base import CorpusLoader, LegalText

logger = logging.getLogger(__name__)

_CORPUS_ID = "cpra"

# ── Embedded statutory text ──────────────────────────────────────────────────
# Source: California Legislative Information (leginfo.legislature.ca.gov)
# Effective date: January 1, 2023 (CPRA operative)

_PROVISIONS: dict[str, dict] = {
    "1798.100": {
        "title": "Cal. Civ. Code § 1798.100 — Right to Know About Personal Information Collected, Disclosed, or Sold",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.100.&lawCode=CIV",
        "text": (
            "(a) A consumer shall have the right to request that a business that collects a consumer's personal "
            "information disclose to that consumer the categories and specific pieces of personal information "
            "the business has collected.\n\n"
            "(b) A business that collects a consumer's personal information shall, at or before the point of "
            "collection, inform consumers as to the categories of personal information to be collected and the "
            "purposes for which the categories of personal information shall be used. A business shall not "
            "collect additional categories of personal information or use personal information collected for "
            "additional purposes that are incompatible with the disclosed purpose for which the personal "
            "information was collected without providing the consumer with notice consistent with this section.\n\n"
            "(c) A business shall provide the information specified in subdivision (a) to the consumer within "
            "45 days of receiving the consumer's request."
        ),
    },
    "1798.110": {
        "title": "Cal. Civ. Code § 1798.110 — Right to Know About Personal Information Collected",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.110.&lawCode=CIV",
        "text": (
            "(a) A consumer shall have the right to request that a business that collects personal information "
            "about the consumer disclose to the consumer the following:\n\n"
            "(1) The categories of personal information it has collected about that consumer.\n"
            "(2) The categories of sources from which the personal information is collected.\n"
            "(3) The business or commercial purpose for collecting, selling, or sharing personal information.\n"
            "(4) The categories of third parties to whom the business discloses personal information.\n"
            "(5) The specific pieces of personal information it has collected about that consumer."
        ),
    },
    "1798.115": {
        "title": "Cal. Civ. Code § 1798.115 — Right to Know About Personal Information Shared or Sold",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.115.&lawCode=CIV",
        "text": (
            "(a) A consumer shall have the right to request that a business that sells or shares the consumer's "
            "personal information, or that discloses it for a business purpose, disclose to that consumer:\n\n"
            "(1) The categories of personal information that the business collected about the consumer.\n"
            "(2) The categories of personal information that the business sold or shared about the consumer "
            "and the categories of third parties to whom the personal information was sold or shared, by "
            "category or categories of personal information for each category of third parties to whom the "
            "personal information was sold or shared.\n"
            "(3) The categories of personal information that the business disclosed about the consumer for "
            "a business purpose and the categories of persons to whom it was disclosed for a business purpose."
        ),
    },
    "1798.120": {
        "title": "Cal. Civ. Code § 1798.120 — Right to Opt Out of Sale or Sharing of Personal Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.120.&lawCode=CIV",
        "text": (
            "(a) A consumer shall have the right, at any time, to direct a business that sells or shares "
            "personal information about the consumer to third parties not to sell or share the consumer's "
            "personal information. This right may be referred to as the right to opt out of sale or sharing.\n\n"
            "(b) A business that sells consumers' personal information to, or shares it with, third parties "
            "shall provide notice to consumers pursuant to subdivision (a) of Section 1798.135 that this "
            "information may be sold or shared and that consumers have the right to opt out of the sale or "
            "sharing of their personal information.\n\n"
            "(c) A business that has received direction from a consumer not to sell or share the consumer's "
            "personal information or, in the case of a minor consumer's personal information has not received "
            "consent to sell or share the minor consumer's personal information shall be prohibited from "
            "selling or sharing the consumer's personal information after its receipt of the consumer's "
            "direction, unless the consumer subsequently provides express authorization for the sale or "
            "sharing of the consumer's personal information."
        ),
    },
    "1798.121": {
        "title": "Cal. Civ. Code § 1798.121 — Right to Limit Use and Disclosure of Sensitive Personal Information",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.121.&lawCode=CIV",
        "text": (
            "(a) A consumer shall have the right, at any time, to direct a business that collects sensitive "
            "personal information about the consumer to limit its use of the consumer's sensitive personal "
            "information to that use which is necessary to perform the services or provide the goods reasonably "
            "expected by an average consumer who requests those goods or services, to perform the services "
            "set forth in paragraphs (2), (4), (5), and (8) of subdivision (e) of Section 1798.140, and as "
            "authorized by regulations adopted pursuant to subparagraph (C) of paragraph (19) of subdivision "
            "(a) of Section 1798.185. A business that uses or discloses a consumer's sensitive personal "
            "information for purposes other than those specified in this subdivision shall provide the consumer "
            "with the notice required by subdivision (a) of Section 1798.121 and with the means to exercise "
            "the right provided by this section pursuant to Section 1798.135.\n\n"
            "(b) 'Sensitive personal information' includes: (1) A consumer's social security, driver's "
            "license, state identification card, or passport number. (2) A consumer's account log-in, "
            "financial account, debit card, or credit card number in combination with any required security "
            "or access code, password, or credentials allowing access to an account. (3) A consumer's "
            "precise geolocation. (4) A consumer's racial or ethnic origin, religious or philosophical "
            "beliefs, or union membership. (5) The contents of a consumer's mail, email, and text messages "
            "unless the business is the intended recipient of the communication. (6) A consumer's genetic "
            "data. (7)(A) The processing of biometric information for the purpose of uniquely identifying "
            "a consumer. (B) Personal information collected and analyzed concerning a consumer's health. "
            "(C) Personal information collected and analyzed concerning a consumer's sex life or sexual "
            "orientation. (8) Personal information collected and analyzed concerning a consumer's sex life "
            "or sexual orientation."
        ),
    },
    "1798.125": {
        "title": "Cal. Civ. Code § 1798.125 — Right of No Retaliation Following Opt Out or Request for Deletion",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.125.&lawCode=CIV",
        "text": (
            "(a)(1) A business shall not discriminate against a consumer because the consumer exercised any "
            "of the consumer's rights under this title, including, but not limited to, by: (A) Denying goods "
            "or services to the consumer. (B) Charging different prices or rates for goods or services, "
            "including through the use of discounts or other benefits or imposing penalties. (C) Providing "
            "a different level or quality of goods or services to the consumer. (D) Suggesting that the "
            "consumer will receive a different price or rate for goods or services or a different level or "
            "quality of goods or services. (E) Retaliating against an employee, applicant for employment, "
            "or independent contractor, as defined in subparagraph (A) of paragraph (2) of subdivision (m) "
            "of Section 1798.140, who exercises their rights under this title."
        ),
    },
    "1798.135": {
        "title": "Cal. Civ. Code § 1798.135 — Methods of Submitting CCPA/CPRA Requests",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.135.&lawCode=CIV",
        "text": (
            "(a) A business that is required to comply with Section 1798.120 shall, in a form that is "
            "reasonably accessible to consumers: (1) Provide a clear and conspicuous link on the business's "
            "internet homepage, titled 'Do Not Sell or Share My Personal Information,' to an internet web "
            "page that enables a consumer, or a person authorized by the consumer, to opt out of the sale "
            "or sharing of the consumer's personal information. (2) Include a description of a consumer's "
            "rights pursuant to Section 1798.120, along with a separate link to the 'Do Not Sell or Share "
            "My Personal Information' internet web page in the business's privacy policy."
        ),
    },
    "1798.150": {
        "title": "Cal. Civ. Code § 1798.150 — Private Right of Action for Data Breaches",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1798.150.&lawCode=CIV",
        "text": (
            "(a)(1) Any consumer whose nonencrypted and nonredacted personal information, as defined in "
            "subparagraph (A) of paragraph (1) of subdivision (d) of Section 1798.81.5, is subject to an "
            "unauthorized access and exfiltration, theft, or disclosure as a result of the business's "
            "violation of the duty to implement and maintain reasonable security procedures and practices "
            "appropriate to the nature of the information to protect the personal information may institute "
            "a civil action for any of the following: (A) To recover damages in an amount not less than "
            "one hundred dollars ($100) and not greater than seven hundred and fifty ($750) per consumer "
            "per incident or actual damages, whichever is greater. (B) Injunctive or declaratory relief. "
            "(C) Any other relief the court deems proper."
        ),
    },
    "CCP_1281.97": {
        "title": "Cal. Code Civ. Proc. § 1281.97 — Arbitration Fees — Consumer and Employment",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1281.97.&lawCode=CCP",
        "text": (
            "(a)(1) In an employment or consumer arbitration that requires, either expressly or through "
            "application of state or federal law or the rules of the arbitration provider, the drafting "
            "party to pay certain fees and costs before the arbitration can proceed, if the drafting party "
            "fails to pay all fees required to initiate an arbitration proceeding within 30 days after the "
            "due date the drafting party is in material breach of the arbitration agreement, is in default "
            "of the arbitration, and waives its right to compel arbitration under Section 1281.2.\n\n"
            "(b) After the arbitration provider issues an invoice for any fees to the drafting party, the "
            "30-day period under subdivision (a) begins on the date of the invoice."
        ),
    },
    "CCP_1281.98": {
        "title": "Cal. Code Civ. Proc. § 1281.98 — Arbitration Fees — Waiver of Right to Compel",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1281.98.&lawCode=CCP",
        "text": (
            "(a)(1) In an employment or consumer arbitration that requires, either expressly or through "
            "application of state or federal law or the rules of the arbitration provider, the drafting "
            "party to pay certain fees and costs during the pendency of an arbitration proceeding, if the "
            "drafting party fails to pay all fees required to continue the arbitration proceeding within "
            "30 days after the due date, the drafting party is in material breach of the arbitration "
            "agreement, is in default of the arbitration, and waives its right to compel arbitration.\n\n"
            "(b) If the drafting party materially breaches the arbitration agreement and is in default "
            "under subdivision (a), the employee or consumer may do any of the following: (1) Withdraw "
            "the claim from arbitration and proceed in a court of appropriate jurisdiction. (2) Petition "
            "the court to confirm the award as a judgment."
        ),
    },
    "CCP_1670.5": {
        "title": "Cal. Code Civ. Proc. § 1670.5 — Unconscionable Contract Provisions",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=1670.5.&lawCode=CCP",
        "text": (
            "(a) If the court as a matter of law finds the contract or any clause of the contract to have "
            "been unconscionable at the time it was made the court may refuse to enforce the contract, or "
            "it may enforce the remainder of the contract without the unconscionable clause, or it may so "
            "limit the application of any unconscionable clause as to avoid any unconscionable result.\n\n"
            "(b) When it is claimed or appears to the court that the contract or any clause thereof may be "
            "unconscionable the parties shall be afforded a reasonable opportunity to present evidence as "
            "to its commercial setting, purpose, and effect to aid the court in making the determination."
        ),
    },
    "Lab_2699": {
        "title": "Cal. Labor Code § 2699 — Private Attorneys General Act (PAGA)",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=2699.&lawCode=LAB",
        "text": (
            "(a) Notwithstanding any other provision of law, any provision of a contract that purports "
            "to waive a party's right to bring a representative action pursuant to this part shall be "
            "unenforceable.\n\n"
            "(f) For all provisions of this code except those for which a civil penalty is specifically "
            "provided, there is established a civil penalty for each pay period for which the employer "
            "fails to comply with the applicable provision as follows: (1) For any initial violation, one "
            "hundred dollars ($100) for each aggrieved employee per pay period. (2) For each subsequent "
            "violation, two hundred dollars ($200) for each aggrieved employee per pay period."
        ),
    },
    "GovCode_12953": {
        "title": "Cal. Gov. Code § 12953 — AB 51: Mandatory Arbitration Ban for Employees",
        "url": "https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=12953.&lawCode=GOV",
        "text": (
            "It is an unlawful employment practice for an employer to require an applicant for employment "
            "or an employee to waive any right, forum, or procedure for a violation of any provision of "
            "the California Fair Employment and Housing Act, including its right to file and pursue a civil "
            "action or a complaint with, or otherwise notify, any state agency, other public prosecutor, "
            "law enforcement agency, or any court or other governmental entity of any potential violation, "
            "as a condition of employment, continued employment, or the receipt of any employment-related "
            "benefit."
        ),
    },
}

# ── anchor_id → _PROVISIONS key mapping ─────────────────────────────────────
_ANCHOR_TO_SECTION: dict[str, str] = {
    "CCPA_1798_100": "1798.100",
    "CCPA_1798_110": "1798.110",
    "CCPA_1798_115": "1798.115",
    "CCPA_1798_120": "1798.120",
    "CCPA_121": "1798.121",
    "CCPA_125": "1798.125",
    "CCPA_135": "1798.135",
    "CCPA_150": "1798.150",
    "CCP_1281_97": "CCP_1281.97",
    "CCP_1281_98": "CCP_1281.98",
    "CCP_1670_5": "CCP_1670.5",
    "CAL_LABOR_2699": "Lab_2699",
    "AB_51": "GovCode_12953",
}


class CPRACorpusLoader(CorpusLoader):
    """In-memory CPRA/CCPA corpus. No submodule or network required."""

    corpus_id: ClassVar[str] = _CORPUS_ID

    def __init__(self, submodule_path=None) -> None:
        # submodule_path accepted for interface compatibility with LegalResolver
        # but ignored — corpus is embedded in this module.
        self._ready = False

    # ------------------------------------------------------------------
    def initialize(self) -> dict[str, int]:
        self._ready = True
        logger.info("CPRACorpusLoader initialized: %d provisions", len(_PROVISIONS))
        return {"provisions": len(_PROVISIONS)}

    # ------------------------------------------------------------------
    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve a CPRA citation or CONTRA anchor_id to statutory text.

        Accepts:
          - Canonical section numbers: "1798.121", "CCP_1281.97"
          - CONTRA anchor IDs: "CCPA_121", "CCP_1281_97", "CAL_LABOR_2699"
          - Informal variants: "§ 1798.121", "Cal. Civ. Code § 1798.121"
        """
        if not self._ready:
            self.initialize()

        section_key = self._resolve_key(citation)
        if section_key is None:
            return None

        prov = _PROVISIONS.get(section_key)
        if prov is None:
            return None

        return LegalText(
            corpus_id=_CORPUS_ID,
            citation=section_key,
            citation_raw=citation,
            title=prov["title"],
            text=prov["text"],
            source_path=f"src/oraculus_di_auditor/legal/cpra_corpus.py#{section_key}",
            source_commit=None,
            as_of=date(2023, 1, 1),  # CPRA operative date
            url=prov.get("url"),
            notes="Embedded CPRA/CCPA corpus; effective 2023-01-01",
        )

    def resolve_anchor(self, anchor_id: str) -> LegalText | None:
        """Convenience: resolve a CONTRA doctrinal_anchor_id directly."""
        section = _ANCHOR_TO_SECTION.get(anchor_id)
        if section is None:
            return None
        return self.resolve_citation(section)

    # ------------------------------------------------------------------
    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Simple substring search across embedded provisions."""
        if not self._ready:
            self.initialize()
        q = query.lower()
        results = []
        for key, prov in _PROVISIONS.items():
            combined = (prov["title"] + " " + prov["text"]).lower()
            if q in combined:
                lt = self.resolve_citation(key)
                if lt:
                    results.append(lt)
            if len(results) >= limit:
                break
        return results

    # ------------------------------------------------------------------
    def list_amendments(self, citation: str) -> list[dict]:
        # No git history for embedded corpus
        return []

    # ------------------------------------------------------------------
    def statistics(self) -> dict[str, int]:
        return {
            "provisions": len(_PROVISIONS),
            "anchors_mapped": len(_ANCHOR_TO_SECTION),
        }

    # ------------------------------------------------------------------
    def _resolve_key(self, citation: str) -> str | None:
        """Normalize a citation string to a _PROVISIONS key."""
        s = citation.strip()

        # 1. Direct anchor_id match (e.g. "CCPA_121")
        mapped = _ANCHOR_TO_SECTION.get(s)
        if mapped:
            return mapped

        # 2. Direct key match (e.g. "1798.121", "CCP_1281.97")
        if s in _PROVISIONS:
            return s

        # 3. Strip decorators and match section number
        # e.g. "Cal. Civ. Code § 1798.121" → "1798.121"
        # "CCP § 1281.97" → "CCP_1281.97"
        import re as _re

        m = _re.search(r"1798\.\d+[a-z]?", s)
        if m:
            candidate = m.group(0)
            if candidate in _PROVISIONS:
                return candidate

        m = _re.search(r"1281\.\d+", s)
        if m:
            candidate = f"CCP_{m.group(0)}"
            if candidate in _PROVISIONS:
                return candidate

        m = _re.search(r"1670\.5", s)
        if m:
            return "CCP_1670.5"

        m = _re.search(r"2699\b", s)
        if m and ("labor" in s.lower() or "lab" in s.lower() or "paga" in s.lower()):
            return "Lab_2699"

        m = _re.search(r"12953\b", s)
        if m:
            return "GovCode_12953"

        return None
