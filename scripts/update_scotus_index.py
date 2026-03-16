"""Update SCOTUS_INDEX.json with 10 new entries from Sprint 8-FILL."""

import json
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
idx_path = REPO_ROOT / "legal" / "cases" / "SCOTUS_INDEX.json"

idx = json.load(open(idx_path, encoding="utf-8"))
existing_ids = {c["case_id"] for c in idx["cases"]}

new_entries = [
    {
        "case_id": "cooper_v_aaron_1958",
        "name": "Cooper v. Aaron",
        "citation": "358 U.S. 1 (1958)",
        "year": 1958,
        "doctrine": "constitutional_structure",
        "summary": (
            "Unanimously held that state officials are bound by Supreme Court "
            "interpretations of the Constitution under the Supremacy Clause."
        ),
        "holding": (
            "No state legislator, executive, or judicial officer can war against "
            "the Constitution. Constitutional rights established in Brown v. Board "
            "of Education bind all state officials."
        ),
        "issue_tags": [
            "judicial_supremacy",
            "constitutional_interpretation",
            "state_compliance",
            "supremacy_clause",
            "desegregation",
        ],
        "doctrinal_weight": 0.96,
        "constitutional_basis": "Article VI Supremacy Clause; Fourteenth Amendment",
        "relevance_to_audit": (
            "Local government officials cannot disregard constitutional requirements "
            "in procurement or surveillance deployment. All officials bound by their "
            "oath to support the Constitution as interpreted by the Supreme Court."
        ),
    },
    {
        "case_id": "hawkins_v_kuhne_1912",
        "name": "Hawkins v. Kuhne",
        "citation": "153 A.D. 216 (N.Y. App. Div. 1912)",
        "year": 1912,
        "doctrine": "civil_procedure",
        "summary": (
            "Established that a general appearance in court waives jurisdictional "
            "objections."
        ),
        "holding": (
            "A general appearance in a judicial proceeding without reservation "
            "constitutes voluntary submission to the court's jurisdiction and waives "
            "any prior defect in the method of bringing the defendant before it."
        ),
        "issue_tags": [
            "jurisdiction",
            "waiver",
            "general_appearance",
            "personal_jurisdiction",
            "procedural_compliance",
        ],
        "doctrinal_weight": 0.65,
        "constitutional_basis": "",
        "relevance_to_audit": (
            "Relevant to procedural compliance in audit enforcement; parties "
            "voluntarily participating in proceedings may waive jurisdictional "
            "objections."
        ),
    },
    {
        "case_id": "ex_parte_young_1908",
        "name": "Ex parte Young",
        "citation": "209 U.S. 123 (1908)",
        "year": 1908,
        "doctrine": "constitutional_structure",
        "summary": (
            "Established that state officials acting in violation of federal "
            "constitutional rights may be enjoined in federal court despite "
            "sovereign immunity."
        ),
        "holding": (
            "A state official stripped of official character by unconstitutional "
            "conduct may be sued in federal court for prospective injunctive relief; "
            "such a suit does not violate the Eleventh Amendment."
        ),
        "issue_tags": [
            "sovereign_immunity",
            "eleventh_amendment",
            "state_officials",
            "injunctive_relief",
            "constitutional_violations",
        ],
        "doctrinal_weight": 0.94,
        "constitutional_basis": "Eleventh Amendment; Fourteenth Amendment",
        "relevance_to_audit": (
            "Permits federal injunctions against state and local officials conducting "
            "unconstitutional surveillance programs or procurement schemes regardless "
            "of sovereign immunity."
        ),
    },
    {
        "case_id": "board_of_regents_v_roth_1972",
        "name": "Board of Regents of State Colleges v. Roth",
        "citation": "408 U.S. 564 (1972)",
        "year": 1972,
        "doctrine": "due_process",
        "summary": (
            "Defined what constitutes a protected property or liberty interest "
            "triggering due process protections."
        ),
        "holding": (
            "To have a protected property interest, a person must have a legitimate "
            "claim of entitlement to the benefit, not merely a unilateral expectation. "
            "Due process is not triggered absent such a protected interest."
        ),
        "issue_tags": [
            "due_process",
            "property_interest",
            "liberty_interest",
            "government_employment",
            "procedural_due_process",
            "entitlement",
        ],
        "doctrinal_weight": 0.90,
        "constitutional_basis": "Fourteenth Amendment Due Process Clause",
        "relevance_to_audit": (
            "Defines the threshold for due process protections in government action; "
            "relevant when audit findings involve terminations of contracts, licenses, "
            "grants, or employment without adequate procedural protections."
        ),
    },
    {
        "case_id": "youngstown_sheet_tube_co_v_sawyer_1952",
        "name": "Youngstown Sheet & Tube Co. v. Sawyer",
        "citation": "343 U.S. 579 (1952)",
        "year": 1952,
        "doctrine": "separation_of_powers",
        "summary": (
            "Limited executive power. President Truman's seizure of steel mills held "
            "unconstitutional. Jackson's concurrence established the three-zone "
            "framework for executive authority."
        ),
        "holding": (
            "The President's order seizing steel mills exceeded constitutional "
            "authority absent congressional authorization. Executive power to act "
            "must stem from an act of Congress or the Constitution, not inherent "
            "power alone."
        ),
        "issue_tags": [
            "executive_power",
            "separation_of_powers",
            "commander_in_chief",
            "inherent_power",
            "property_seizure",
            "congressional_authorization",
        ],
        "doctrinal_weight": 0.97,
        "constitutional_basis": "Article II; Article I",
        "relevance_to_audit": (
            "Establishes constitutional limits on executive authority absent "
            "congressional authorization; relevant when executive officials take "
            "unilateral action without statutory authorization, particularly when "
            "the legislature has declined to grant the relevant power."
        ),
    },
    {
        "case_id": "united_states_v_carolene_products_co_1938",
        "name": "United States v. Carolene Products Co.",
        "citation": "304 U.S. 144 (1938)",
        "year": 1938,
        "doctrine": "equal_protection",
        "summary": (
            "Established rational basis review for economic legislation and, in "
            "Footnote Four, suggested heightened scrutiny for laws affecting "
            "fundamental rights or discrete and insular minorities."
        ),
        "holding": (
            "Economic regulations are upheld under rational basis review. Footnote "
            "Four: statutes directed at discrete and insular minorities may call for "
            "more searching judicial inquiry."
        ),
        "issue_tags": [
            "rational_basis",
            "due_process",
            "equal_protection",
            "heightened_scrutiny",
            "discrete_insular_minority",
            "footnote_four",
        ],
        "doctrinal_weight": 0.94,
        "constitutional_basis": "Fifth Amendment Due Process Clause; Commerce Clause",
        "relevance_to_audit": (
            "Establishes tiers of scrutiny in equal protection analysis of "
            "government programs; Footnote Four provides basis for heightened "
            "scrutiny of programs disparately affecting protected minority groups."
        ),
    },
    {
        "case_id": "heart_of_atlanta_motel_v_united_states_1964",
        "name": "Heart of Atlanta Motel, Inc. v. United States",
        "citation": "379 U.S. 241 (1964)",
        "year": 1964,
        "doctrine": "federal_power",
        "summary": (
            "Upheld Title II of the Civil Rights Act under the Commerce Clause. "
            "Congress may regulate local conduct that substantially affects interstate "
            "commerce."
        ),
        "holding": (
            "Title II of the Civil Rights Act of 1964 is a valid exercise of Commerce "
            "Clause power. Racial discrimination by hotels serving interstate travelers "  # noqa: E501
            "substantially affects interstate commerce and may be regulated by Congress."  # noqa: E501
        ),
        "issue_tags": [
            "commerce_clause",
            "civil_rights_act",
            "public_accommodations",
            "racial_discrimination",
            "interstate_commerce",
            "substantial_effects_test",
        ],
        "doctrinal_weight": 0.90,
        "constitutional_basis": "Article I, Section 8 (Commerce Clause)",
        "relevance_to_audit": (
            "Provides constitutional basis for federal civil rights laws requiring "
            "non-discrimination in government contracting, procurement, and grant "
            "programs."
        ),
    },
    {
        "case_id": "garcia_v_san_antonio_metropolitan_transit_authority_1985",
        "name": "Garcia v. San Antonio Metropolitan Transit Authority",
        "citation": "469 U.S. 528 (1985)",
        "year": 1985,
        "doctrine": "federal_power",
        "summary": (
            "Federal labor laws apply to state and local governments. National League "
            "of Cities v. Usery overruled. States must rely on the political process "
            "for protection from federal regulation."
        ),
        "holding": (
            "The FLSA applies to state and local governments. States cannot claim "
            "constitutional exemption from generally applicable federal regulatory "
            "requirements under a traditional governmental functions test."
        ),
        "issue_tags": [
            "fair_labor_standards_act",
            "tenth_amendment",
            "state_sovereignty",
            "federalism",
            "commerce_clause",
            "municipal_government",
            "political_safeguards",
        ],
        "doctrinal_weight": 0.87,
        "constitutional_basis": (  # noqa: E501
            "Article I, Section 8 (Commerce Clause); Tenth Amendment"
        ),
        "relevance_to_audit": (
            "Confirms federal labor and employment laws apply to state and local "
            "governments; relevant to audit findings involving federal grant "
            "conditions, prevailing wage requirements, and labor standards imposed "
            "on municipalities."
        ),
    },
    {
        "case_id": "gregory_v_ashcroft_1991",
        "name": "Gregory v. Ashcroft",
        "citation": "501 U.S. 452 (1991)",
        "year": 1991,
        "doctrine": "federal_power",
        "summary": (
            "Clear statement rule: Congress must speak clearly when altering the "
            "federal-state balance. Federal statutes are construed not to regulate "
            "core state governmental functions absent unmistakably clear statutory "
            "language."
        ),
        "holding": (
            "The ADEA did not clearly apply to appointed state judges. If Congress "
            "intends to alter the usual constitutional balance between federal and "
            "state authority, it must make its intention unmistakably clear in the "
            "statutory language."
        ),
        "issue_tags": [
            "federalism",
            "plain_statement_rule",
            "statutory_interpretation",
            "adea",
            "state_judges",
            "tenth_amendment",
            "federal_grant_conditions",
        ],
        "doctrinal_weight": 0.85,
        "constitutional_basis": "Tenth Amendment; Article III; Supremacy Clause",
        "relevance_to_audit": (
            "Plain statement rule governs interpretation of federal grant conditions "
            "imposed on state and local governments; ambiguous federal regulations "
            "affecting state governmental operations should not be construed to alter "
            "the federal-state balance."
        ),
    },
    {
        "case_id": "bond_v_united_states_2011",
        "name": "Bond v. United States",
        "citation": "564 U.S. 211 (2011)",
        "year": 2011,
        "doctrine": "federal_power",
        "summary": (
            "Individuals have standing to challenge federal statutes as violating "
            "state sovereignty. Federalism protects individual liberty as well as "
            "state sovereignty."
        ),
        "holding": (
            "An individual has standing to raise a Tenth Amendment challenge to a "
            "federal statute. Federalism secures individual freedom; an individual "
            "injured by unconstitutionally broad federal power may invoke structural "
            "constitutional protections."
        ),
        "issue_tags": [
            "standing",
            "tenth_amendment",
            "federalism",
            "individual_liberty",
            "treaty_power",
            "enumerated_powers",
            "constitutional_accountability",
        ],
        "doctrinal_weight": 0.84,
        "constitutional_basis": (
            "Tenth Amendment; Article III (standing); Necessary and Proper Clause"
        ),
        "relevance_to_audit": (
            "Establishes that citizens, organizations, and audit petitioners have "
            "standing to challenge federal programs that exceed enumerated federal "
            "powers; relevant to accountability challenges to federally funded "
            "surveillance programs."
        ),
    },
]

added = 0
for entry in new_entries:
    if entry["case_id"] not in existing_ids:
        idx["cases"].append(entry)
        existing_ids.add(entry["case_id"])
        added += 1
        print(f"Added: {entry['case_id']}")
    else:
        print(f"Already in index: {entry['case_id']}")

idx["metadata"]["total_cases"] = len(idx["cases"])
idx["metadata"]["expanded_individual_files"] = 81
idx["generated_at"] = datetime.now(UTC).isoformat()
idx["description"] = (
    "Supreme Court constitutional doctrine index for Judicial Interpretive Matrix "
    "(JIM) - CLEP-v2 Enhanced + Sprint 8.2 + Sprint 8-FILL expansion"
)

with open(idx_path, "w", encoding="utf-8") as f:
    json.dump(idx, f, indent=2, ensure_ascii=False)

print(f"\nAdded {added} new entries. Total cases: {len(idx['cases'])}")
