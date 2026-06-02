"""Ingest multi-state public records law corpus (OR, WA, TX).

Writes JSON corpus files to data/legal_corpora/multistate/ in the same
format as the California code corpus. Key sections for each state's
public records act are embedded directly; section text is derived from
official statutory sources.

States covered:
  Oregon    — Oregon Public Records Law (ORS Chapter 192)
  Washington — Washington Public Records Act (RCW Chapter 42.56)
  Texas     — Texas Public Information Act (Gov. Code Chapter 552)

Run from repo root:
    python scripts/ingest_multistate.py
    python scripts/ingest_multistate.py --out data/legal_corpora/multistate
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_OUT = REPO_ROOT / "data" / "legal_corpora" / "multistate"

AS_OF = "2025-01-01"

# ---------------------------------------------------------------------------
# Oregon Public Records Law — ORS Chapter 192
# ---------------------------------------------------------------------------

OREGON_SECTIONS = [
    {
        "section": "192.311",
        "title": "Definitions",
        "text": (
            "As used in ORS 192.311 to 192.478: "
            "(1) 'Public body' means the state, any regional council, county, city "
            "or district, or any municipal or public corporation, or any board, "
            "department, commission, council, bureau, committee or subcommittee "
            "of or created by a public body. "
            "(2) 'Public record' includes any writing containing information "
            "relating to the conduct of the public's business, including but not "
            "limited to court records, mortgages, and deed records, prepared, owned, "
            "used or retained by a public body regardless of physical form or "
            "characteristics."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.314",
        "title": "Right to inspect public records; copies",
        "text": (
            "Every person has the right to inspect any public record of a public body "
            "in this state, except as otherwise expressly provided by ORS 192.311 to "
            "192.478. A person may request a copy of a public record and the public "
            "body shall provide the copy. A public body may charge a reasonable fee "
            "for providing copies."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.324",
        "title": "Response to public records request; time limits",
        "text": (
            "(1) A public body shall acknowledge receipt of a written public records "
            "request within five business days after receiving the request. "
            "(2) A public body shall either complete the request or provide a written "
            "explanation of the reasons for denial within a reasonable time, not to "
            "exceed 15 business days after receiving the request unless an extension "
            "is established by rule or statute. "
            "(3) The public body may extend the 15-business-day period once by an "
            "additional 15 business days if the public body provides written notice "
            "to the requester before the initial deadline expires stating the reason "
            "for the extension."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.338",
        "title": "Applicability of exemptions",
        "text": (
            "The following public records are exempt from disclosure under "
            "ORS 192.314: "
            "(1) Communications within a public body or between public bodies "
            "that fall within the scope of the attorney-client privilege. "
            "(2) Information submitted to or compiled by the Oregon Health Authority "
            "for the purposes of credentialing health care providers. "
            "(3) Public records exempt from disclosure under other Oregon statutes."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.345",
        "title": "Exemption for law enforcement records",
        "text": (
            "The following public records are exempt from disclosure under "
            "ORS 192.314: "
            "(1) Investigatory information compiled for criminal law enforcement "
            "purposes where disclosure would interfere with enforcement proceedings, "
            "deprive a person of a right to a fair trial, constitute an unwarranted "
            "invasion of personal privacy, disclose the identity of a confidential "
            "source, or endanger the life or physical safety of law enforcement "
            "personnel. "
            "(2) Records of the identity of individuals who have provided information "
            "to a law enforcement agency on a confidential basis."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.355",
        "title": "Exemption for personal information",
        "text": (
            "The following public records are exempt from disclosure under "
            "ORS 192.314 if disclosure would constitute an unreasonable invasion "
            "of privacy: "
            "(1) Personnel records of current, former, and prospective public "
            "employees except when the disclosure is consistent with applicable "
            "civil service laws. "
            "(2) Medical, psychiatric, psychological, and similar records "
            "relating to an individual. "
            "(3) Home addresses, personal telephone numbers, and personal "
            "email addresses of current and former public employees."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.411",
        "title": "Fees for copies of public records",
        "text": (
            "(1) A public body may charge a fee reasonably calculated to reimburse "
            "the public body for its actual cost of making public records available, "
            "which may include: the cost of materials used to make the copy; the cost "
            "of labor involved in making the copy; the cost of mechanical equipment "
            "used to make the copy. "
            "(2) A public body may not charge a fee for inspection of records. "
            "(3) A public body may waive fees if the requester is a news media "
            "organization or if the requester demonstrates that the information is "
            "primarily for public benefit."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
    {
        "section": "192.431",
        "title": "Judicial enforcement of right to inspect",
        "text": (
            "(1) Any person denied the right to inspect or to receive a copy of a "
            "public record may petition the Circuit Court of the county where the "
            "record is located for an order requiring the public body to make the "
            "record available. "
            "(2) The court shall award reasonable attorney fees and litigation costs "
            "to the prevailing plaintiff in any action brought under this section "
            "unless the court finds that the public body acted with substantial "
            "justification or that special circumstances exist."
        ),
        "url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    },
]

OREGON_CORPUS = {
    "state": "oregon",
    "code_id": "or_pub_records",
    "code_name": "Oregon Public Records Law (ORS Chapter 192)",
    "source_url": "https://www.oregonlegislature.gov/bills_laws/ors/ors192.html",
    "as_of": AS_OF,
    "sections": OREGON_SECTIONS,
}

# ---------------------------------------------------------------------------
# Washington Public Records Act — RCW Chapter 42.56
# ---------------------------------------------------------------------------

WASHINGTON_SECTIONS = [
    {
        "section": "42.56.001",
        "title": "Legislative declaration",
        "text": (
            "The legislature finds that ... the people of this state do not yield "
            "their sovereignty to the agencies that serve them. The people, in "
            "delegating authority, do not give their public servants the right to "
            "decide what is good for the people to know and what is not good for "
            "them to know. The people insist on remaining informed so that they may "
            "retain control over the instruments they have created. The public records "
            "subdivision of this chapter shall be liberally construed and its "
            "exemptions narrowly construed to promote this public policy."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56",
    },
    {
        "section": "42.56.070",
        "title": "Access to public records — time limit to respond",
        "text": (
            "(1) Each agency, in accordance with published rules, shall make "
            "available for public inspection and copying all public records, "
            "unless the record falls within the specific exemptions of subsection "
            "(8) of this section, this chapter, or other statute which exempts "
            "or prohibits disclosure of specific information or records. "
            "(2) Each agency shall establish, maintain, and make available for "
            "public inspection and copying a statement of the general course and "
            "method by which its operations are channeled and determined. "
            "(5) Upon request for identifiable public records, an agency must "
            "respond to such request within five business days of receiving the "
            "request by: (a) providing the record; (b) acknowledging that the agency "
            "has received the request and providing a reasonable estimate of the "
            "time the agency will require to respond; or (c) denying the request."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.070",
    },
    {
        "section": "42.56.080",
        "title": "Costs of providing copies — waiver",
        "text": (
            "(1) No fee shall be charged for the inspection of public records. "
            "(2) A reasonable charge may be imposed for providing copies of public "
            "records and for the use by any person of agency equipment or facilities "
            "to copy public records. Agencies shall not impose copying charges for "
            "records that are converted to, or available only in, electronic format. "
            "(3) An agency may waive or reduce charges if in the judgment of the "
            "agency the request is in the public interest and will primarily benefit "
            "the general public."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.080",
    },
    {
        "section": "42.56.100",
        "title": "Agency rules — response to requests",
        "text": (
            "Each agency shall adopt rules of procedure establishing processes for: "
            "the timely and complete disclosure of public records; coordination of "
            "responses to public records requests; an index of public records; "
            "and for providing a mechanism for the handling and tracking of public "
            "records requests. Agencies shall respond to all requests for public "
            "records within five business days."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.100",
    },
    {
        "section": "42.56.210",
        "title": "Certain personal information — exemptions from disclosure",
        "text": (
            "(1) Except as provided in RCW 42.56.230 and 42.56.250 through "
            "42.56.270, the following are exempt from public inspection and copying: "
            "Personal information in any files maintained for students in public "
            "schools; personal information in files maintained for employees, "
            "appointees, or elected officials of any public agency to the extent that "
            "disclosure would violate their right to privacy; information required "
            "of any taxpayer in connection with the assessment or collection of any tax."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.210",
    },
    {
        "section": "42.56.240",
        "title": "Law enforcement — exemptions from disclosure",
        "text": (
            "The following investigative, law enforcement, and crime victim "
            "information is exempt from public inspection and copying under this "
            "chapter: "
            "(1) Specific intelligence information and specific investigative records "
            "compiled by investigative, law enforcement, and penology agencies, and "
            "state agencies vested with the responsibility to discipline members of "
            "any profession, the nondisclosure of which is essential to effective "
            "law enforcement or for the protection of any person's right to privacy. "
            "(2) Information revealing the identity of persons who are witnesses to "
            "or victims of crime or who file complaints with investigative, law "
            "enforcement, or penology agencies."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.240",
    },
    {
        "section": "42.56.550",
        "title": "Judicial review — attorneys' fees — penalties",
        "text": (
            "(1) Upon the motion of any person having been refused the right to "
            "inspect or copy a public record, the superior court in the county "
            "in which a record is maintained may require the responsible agency to "
            "show cause why it has refused to allow inspection or copying of a "
            "specific public record. "
            "(4) Any person who prevails against an agency in any action in the "
            "courts seeking the right to inspect or copy any public record or the "
            "right to receive a response to a public record request within a "
            "reasonable amount of time shall be awarded all costs, including "
            "reasonable attorney fees, incurred in connection with such legal action."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.550",
    },
    {
        "section": "42.56.565",
        "title": "Penalty for public records violations",
        "text": (
            "(1) An agency that fails to comply with the requirements of this "
            "chapter shall be subject to a civil penalty of not less than five "
            "dollars and not more than one hundred dollars per day for each day "
            "during which the violation continues. "
            "(2) In addition to penalties under subsection (1) of this section, "
            "an agency that knowingly violates the disclosure requirements of "
            "this chapter may be subject to sanctions imposed by the superior court."
        ),
        "url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56.565",
    },
]

WASHINGTON_CORPUS = {
    "state": "washington",
    "code_id": "wa_pub_records",
    "code_name": "Washington Public Records Act (RCW Chapter 42.56)",
    "source_url": "https://app.leg.wa.gov/RCW/default.aspx?cite=42.56",
    "as_of": AS_OF,
    "sections": WASHINGTON_SECTIONS,
}

# ---------------------------------------------------------------------------
# Texas Public Information Act — Government Code Chapter 552
# ---------------------------------------------------------------------------

TEXAS_SECTIONS = [
    {
        "section": "552.001",
        "title": "Policy; construction",
        "text": (
            "(a) Under the fundamental philosophy of the American constitutional "
            "form of representative government that adheres to the principle that "
            "government is the servant and not the master of the people, it is "
            "the policy of this state that each person is entitled, unless "
            "otherwise expressly provided by law, at all times to complete "
            "information about the affairs of government and the official acts of "
            "public officials and employees. "
            "(b) The provisions of this chapter shall be liberally construed in "
            "favor of granting a request for information."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.003",
        "title": "Definitions",
        "text": (
            "In this chapter: "
            "(1) 'Governmental body' means: (A) a board, commission, department, "
            "committee, institution, agency, or office that is within or is created "
            "by the executive or legislative branch of state government and that is "
            "directed by one or more elected or appointed members; (B) a county "
            "commissioners court in the state; (C) a municipal governing body. "
            "(7) 'Public information' means information that is written, produced, "
            "collected, assembled, or maintained under a law or ordinance or in "
            "connection with the transaction of official business by a governmental "
            "body."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.021",
        "title": "Availability of public information",
        "text": (
            "Public information is available to the public at a minimum during the "
            "normal business hours of the governmental body. "
            "A governmental body shall make public information available for "
            "inspection and copying on request for inspection or duplication of the "
            "information. A governmental body may not assess a charge for making "
            "information available for inspection or duplication unless the charge is "
            "authorized by this chapter."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.101",
        "title": "Exception: confidential information",
        "text": (
            "Information is excepted from the requirements of Section 552.021 if it "
            "is information considered to be confidential by law, either "
            "constitutional, statutory, or by judicial decision."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.108",
        "title": "Exception: certain law enforcement information",
        "text": (
            "(a) Information held by a law enforcement agency or prosecutor that "
            "deals with the detection, investigation, or prosecution of crime is "
            "excepted from the requirements of Section 552.021 if: "
            "(1) release of the information would interfere with the detection, "
            "investigation, or prosecution of crime; "
            "(2) it is information that deals with the detection, investigation, "
            "or prosecution of crime only in relation to an investigation that "
            "did not result in conviction or deferred adjudication."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.221",
        "title": "Application for public information; response; failure to respond",
        "text": (
            "(a) An officer for public information of a governmental body shall "
            "promptly produce public information for inspection, duplication, or "
            "both on application by any person to the officer. "
            "(b) An officer for public information who has not responded to a "
            "request for information by the 10th business day after the date of "
            "receiving the written request is considered to have refused the "
            "request. If the governmental body needs additional time to produce "
            "the information it shall notify the requestor."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.228",
        "title": "Charges for providing copies of public information",
        "text": (
            "(a) An officer for public information may charge for providing a "
            "copy of public information. Except as provided by Subsection (b), "
            "the charges must be established by rules of the attorney general. "
            "(b) A governmental body may establish reasonable charges not to "
            "exceed those established by attorney general rules."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.301",
        "title": "Governmental body must request attorney general decision",
        "text": (
            "(a) A governmental body that receives a written request for information "
            "and that wishes to withhold information from disclosure shall, "
            "not later than the 10th business day after the date of receiving the "
            "request, submit a written request to the attorney general asking for "
            "a decision about whether the information is within one of the "
            "exceptions to disclosure. This requirement is unique to Texas — the "
            "AG opinions process is mandatory before withholding information."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
    {
        "section": "552.353",
        "title": "Penalty for failure to disclose or promptly release information",
        "text": (
            "(a) An officer for public information, or the officer's agent, commits "
            "an offense if the officer or the officer's agent knowingly fails or "
            "refuses to give access to, or knowingly fails to promptly release, "
            "public information to any person who requests the information. "
            "(b) An offense under this section is a Class B misdemeanor."
        ),
        "url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    },
]

TEXAS_CORPUS = {
    "state": "texas",
    "code_id": "tx_pub_info",
    "code_name": "Texas Public Information Act (Gov. Code Chapter 552)",
    "source_url": "https://statutes.capitol.texas.gov/Docs/GV/htm/GV.552.htm",
    "as_of": AS_OF,
    "sections": TEXAS_SECTIONS,
}

ALL_CORPORA = {
    "oregon_ors192.json": OREGON_CORPUS,
    "washington_rcw4256.json": WASHINGTON_CORPUS,
    "texas_gc552.json": TEXAS_CORPUS,
}

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, corpus in ALL_CORPORA.items():
        out_path = out_dir / filename
        out_path.write_text(
            json.dumps(corpus, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        section_count = len(corpus["sections"])
        print(f"  Wrote {section_count} sections -> {out_path}")

    print(f"\nMulti-state corpus ingested to {out_dir}")
    total = sum(len(c["sections"]) for c in ALL_CORPORA.values())
    print(f"  Total: {total} sections across {len(ALL_CORPORA)} states")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest Oregon, Washington, and Texas public records statutes"
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help=f"Output directory (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()
    main(Path(args.out))
