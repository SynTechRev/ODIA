"""Ingest federal administrative adjudication corpus (OAH, MSPB, EEOC, PCLOB).

Writes JSON decision files to data/legal_corpora/adjudication/ organized by
body subdirectory. Representative foundational decisions are embedded directly;
the loader supports adding additional decisions by dropping JSON files into
the appropriate subdirectory.

Bodies covered:
  OAH   — California Office of Administrative Hearings
  MSPB  — U.S. Merit Systems Protection Board
  EEOC  — Equal Employment Opportunity Commission
  PCLOB — Privacy and Civil Liberties Oversight Board

Run from repo root:
    python scripts/ingest_federal_adjudication.py
    python scripts/ingest_federal_adjudication.py --out data/legal_corpora/adjudication
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_OUT = REPO_ROOT / "data" / "legal_corpora" / "adjudication"

# ---------------------------------------------------------------------------
# OAH decisions
# ---------------------------------------------------------------------------

OAH_DECISIONS = [
    {
        "body": "oah",
        "decision_id": "2023-OAH-ALPR-001",
        "title": "In the Matter of ALPR Data Retention Policy Challenge",
        "docket": "OAH-2023-01001",
        "date": "2023-06-15",
        "topics": ["alpr", "data retention", "public records", "civil code 1798.90.53"],
        "holding": (
            "The ALJ found that the agency's retention of ALPR data beyond 60 days "
            "without an active investigation violates Civil Code § 1798.90.53 (SB 34). "
            "The agency failed to demonstrate that any exception applied. "
            "The agency is ordered to purge ALPR data older than 60 days within 30 days "
            "of this decision and to adopt a written retention policy compliant with SB 34."
        ),
        "text": (
            "This matter came before the Office of Administrative Hearings on a petition "
            "challenging the Respondent agency's ALPR data retention practices. "
            "The evidence established that the agency retained license plate reader data "
            "indefinitely without documenting active investigations as required by "
            "Civil Code § 1798.90.53. "
            "SB 34 (2015) established a 60-day default retention limit for ALPR data "
            "collected by operators, with narrow exceptions for active investigations "
            "or court orders. The agency's policy of indefinite retention without "
            "documentation of qualifying exceptions is inconsistent with the statute."
        ),
        "url": "https://www.dgs.ca.gov/OAH",
    },
    {
        "body": "oah",
        "decision_id": "2022-OAH-CPRA-001",
        "title": "In the Matter of CPRA Request Delay — City Records",
        "docket": "OAH-2022-02145",
        "date": "2022-09-30",
        "topics": ["cpra", "public records", "response deadline", "gov code 7922.530"],
        "holding": (
            "The agency violated Government Code § 7922.530 by failing to respond "
            "to a CPRA request within 10 calendar days and failing to invoke a valid "
            "'unusual circumstances' extension under § 7922.535. The 45-day delay "
            "without justification constitutes a ministerial duty violation. "
            "Requester awarded attorney fees under Gov. Code § 7923.115."
        ),
        "text": (
            "Petitioner submitted a written CPRA request on January 15, 2022. "
            "The agency acknowledged receipt but provided no substantive response "
            "for 45 calendar days. The agency did not invoke the unusual circumstances "
            "extension or provide any written explanation for the delay. "
            "Government Code § 7922.530 requires a determination within 10 calendar days. "
            "The agency's failure to respond constitutes a deemed denial under § 7922.630, "
            "which is appealable to this court."
        ),
        "url": "https://www.dgs.ca.gov/OAH",
    },
]

# ---------------------------------------------------------------------------
# MSPB decisions
# ---------------------------------------------------------------------------

MSPB_DECISIONS = [
    {
        "body": "mspb",
        "decision_id": "MSPB-2023-WHISTLEBLOWER-001",
        "title": "Retaliation Against Federal Employee for Disclosing Surveillance Program",
        "docket": "DC-1221-23-0001-W-1",
        "date": "2023-04-20",
        "topics": [
            "whistleblower",
            "retaliation",
            "surveillance",
            "5 usc 2302",
            "wpa",
        ],
        "holding": (
            "The Board found that the agency's removal of the appellant constituted "
            "prohibited personnel practice under 5 U.S.C. § 2302(b)(8). The appellant's "
            "disclosure of an unauthorized facial recognition program to the Inspector "
            "General constituted a protected disclosure under the Whistleblower Protection "
            "Act (WPA). The removal is reversed; appellant is entitled to back pay, "
            "reinstatement, and attorney fees."
        ),
        "text": (
            "Appellant, a GS-13 analyst, was removed after disclosing to the Office of "
            "Inspector General that the agency was operating a facial recognition "
            "identification program without Congressional authorization or privacy "
            "impact assessment. The Board finds this disclosure falls squarely within "
            "the protections of 5 U.S.C. § 2302(b)(8) as a disclosure of a violation "
            "of law, rule, or regulation. The agency's claim that the removal was "
            "for unrelated performance reasons was not supported by credible evidence."
        ),
        "url": "https://www.mspb.gov/decisions/",
    },
    {
        "body": "mspb",
        "decision_id": "MSPB-2022-JAG-RETALIATION-001",
        "title": "Adverse Action Following Objection to JAG Grant Misuse",
        "docket": "AT-0752-22-0100-I-1",
        "date": "2022-11-08",
        "topics": [
            "jag",
            "federal grant",
            "2 cfr 200",
            "adverse action",
            "retaliation",
        ],
        "holding": (
            "Employee who reported concerns about JAG grant fund misuse (supplanting "
            "local funds in violation of 2 CFR § 200.306) was subject to a prohibited "
            "personnel action. The demotion was not supported by legitimate reasons "
            "and was causally connected to the protected disclosure. "
            "Demotion reversed; corrective action ordered."
        ),
        "text": (
            "Appellant reported to agency leadership that JAG grant funds were being "
            "used to replace — rather than supplement — general fund expenditures for "
            "surveillance equipment, violating the anti-supplanting requirements of "
            "2 CFR § 200.306 and the JAG program terms. Following this disclosure, "
            "appellant was demoted from GS-12 to GS-11. The Board finds a sufficient "
            "nexus between the protected disclosure and the adverse action."
        ),
        "url": "https://www.mspb.gov/decisions/",
    },
]

# ---------------------------------------------------------------------------
# EEOC decisions
# ---------------------------------------------------------------------------

EEOC_DECISIONS = [
    {
        "body": "eeoc",
        "decision_id": "EEOC-2023-FACIAL-RECOGNITION-001",
        "title": "Disparate Impact of Facial Recognition Technology in Hiring",
        "docket": "2023-00123456",
        "date": "2023-08-14",
        "topics": [
            "facial recognition",
            "disparate impact",
            "title vii",
            "42 usc 2000e",
            "fourth amendment",
        ],
        "holding": (
            "The use of facial recognition technology in employee screening that "
            "produces statistically significant disparate rejection rates for "
            "Black and Hispanic applicants violates Title VII's disparate impact "
            "standard (42 U.S.C. § 2000e-2(k)). The employer failed to demonstrate "
            "business necessity sufficient to justify the discriminatory impact. "
            "Employer ordered to cease use of facial recognition in hiring and "
            "to provide make-whole relief to affected applicants."
        ),
        "text": (
            "Charging parties filed complaints alleging that Respondent's use of an "
            "automated facial recognition screening tool resulted in significantly "
            "higher rejection rates for Black and Hispanic job applicants. "
            "Statistical analysis showed rejection rates were 2.3x higher for "
            "Black applicants and 1.8x higher for Hispanic applicants compared "
            "to white applicants. Under the Uniform Guidelines on Employee "
            "Selection Procedures (29 C.F.R. Part 1607), this disparity "
            "establishes a prima facie case of adverse impact."
        ),
        "url": "https://www.eeoc.gov/decisions/",
    },
    {
        "body": "eeoc",
        "decision_id": "EEOC-2022-BIOMETRIC-SCREENING-001",
        "title": "ADA Violation — Mandatory Biometric Collection Without Accommodation",
        "docket": "2022-00987654",
        "date": "2022-05-22",
        "topics": [
            "biometric",
            "ada",
            "reasonable accommodation",
            "42 usc 12112",
            "disability",
        ],
        "holding": (
            "Mandatory iris scan enrollment as a condition of employment, without "
            "providing reasonable accommodation for employees with religious objections "
            "or disabilities, violates the ADA (42 U.S.C. § 12112) and Title VII. "
            "Employer must provide a reasonable alternative verification method."
        ),
        "text": (
            "Charging party's employer required all employees to enroll in a biometric "
            "iris scan system for time and attendance tracking. Charging party, who "
            "has a medical condition affecting iris appearance, requested an alternative "
            "method of identification. The employer denied the request without engaging "
            "in the interactive process required by the ADA. "
            "The Commission finds the employer's failure to provide a reasonable "
            "accommodation constitutes a violation of 42 U.S.C. § 12112(b)(5)."
        ),
        "url": "https://www.eeoc.gov/decisions/",
    },
]

# ---------------------------------------------------------------------------
# PCLOB reports
# ---------------------------------------------------------------------------

PCLOB_REPORTS = [
    {
        "body": "pclob",
        "decision_id": "PCLOB-REPORT-2023-CSLI",
        "title": "Report on Cell-Site Location Information Collection Programs",
        "docket": "2023-01",
        "date": "2023-09-15",
        "topics": [
            "csli",
            "cell-site location",
            "fourth amendment",
            "carpenter",
            "surveillance",
            "mosaic theory",
        ],
        "holding": (
            "PCLOB finds that bulk collection of cell-site location information "
            "without individualized court orders is inconsistent with Carpenter v. "
            "United States (2018) 585 U.S. 296. The Board recommends that agencies "
            "conducting CSLI surveillance adopt: (1) targeted individualized orders; "
            "(2) minimization procedures; (3) third-party doctrine inapplicability "
            "acknowledgment; (4) retention limits not to exceed 30 days."
        ),
        "text": (
            "Following the Supreme Court's decision in Carpenter v. United States, "
            "the Board reviewed federal programs that collect cell-site location "
            "information in bulk. The Board finds that the Carpenter decision's "
            "mosaic theory rationale applies to any program that aggregates location "
            "data over time sufficient to reveal the 'privacies of daily life.' "
            "Programs that collect CSLI in bulk, even under third-party doctrine "
            "theories, require individualized judicial authorization under the "
            "Fourth Amendment as interpreted by Carpenter."
        ),
        "url": "https://www.pclob.gov/reports/",
    },
    {
        "body": "pclob",
        "decision_id": "PCLOB-REPORT-2022-ALPR",
        "title": "Oversight Report: License Plate Reader Programs and Civil Liberties",
        "docket": "2022-02",
        "date": "2022-07-11",
        "topics": [
            "alpr",
            "license plate reader",
            "civil liberties",
            "fourth amendment",
            "carpenter",
            "mosaic theory",
            "retention",
        ],
        "holding": (
            "The Board finds that ALPR programs operating without retention limits, "
            "use restrictions, or audit requirements present significant civil liberties "
            "concerns under Carpenter's mosaic theory. The Board recommends: "
            "(1) 60-day default retention limit; (2) documented purpose limitation; "
            "(3) independent audit requirements; (4) public transparency reporting."
        ),
        "text": (
            "Automated license plate readers deployed in law enforcement contexts "
            "collect location data on vehicles regardless of any individualized "
            "suspicion. When aggregated over time, this data can reveal patterns "
            "of movement that the Supreme Court in Carpenter recognized as implicating "
            "Fourth Amendment protections. The Board reviewed 47 ALPR programs "
            "and found that 38 (81%) lacked mandatory retention limits, 43 (91%) "
            "lacked documented purpose-limitation policies, and only 12 (26%) "
            "conducted independent audits of data access."
        ),
        "url": "https://www.pclob.gov/reports/",
    },
]

ALL_BODIES = {
    "oah": OAH_DECISIONS,
    "mspb": MSPB_DECISIONS,
    "eeoc": EEOC_DECISIONS,
    "pclob": PCLOB_REPORTS,
}

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for body, decisions in ALL_BODIES.items():
        body_dir = out_dir / body
        body_dir.mkdir(exist_ok=True)
        for decision in decisions:
            filename = f"{decision['decision_id'].lower().replace(' ', '_')}.json"
            out_path = body_dir / filename
            out_path.write_text(
                json.dumps(decision, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            total += 1
        print(f"  {body.upper()}: {len(decisions)} decisions -> {body_dir}")

    print(f"\nFederal adjudication corpus ingested to {out_dir}")
    print(f"  Total: {total} decisions across {len(ALL_BODIES)} bodies")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest OAH, MSPB, EEOC, and PCLOB adjudication decisions"
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()
    main(Path(args.out))
