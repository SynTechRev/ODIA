#!/usr/bin/env python3
# ruff: noqa: E501
"""
Build Constitutional Linguistic Frameworks (CLF-v1) JSON artifact.

This script generates the complete CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json
file with all 10 constitutional interpretation models.
"""

import json
from datetime import UTC, datetime
from pathlib import Path


def build_all_frameworks():
    """Build complete CLF data structure with all 10 frameworks."""

    clf_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "generated": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "description": "Constitutional Linguistic Frameworks (CLF-v1) - Machine-actionable constitutional interpretation models for JIM, ACE, VICFM, CAIM, and MSH integration",
        "metadata": {
            "total_frameworks": 10,
            "integration_targets": [
                "JIM (Judicial Interpretive Matrix)",
                "ACE (Anomaly Correlation Engine)",
                "VICFM (Vendor/Influence Constitutional Framing Model)",
                "MSH (Multi-Source Semantic Harmonization)",
                "CAIM (Cross-Agency Influence Mapping)",
            ],
            "temporal_range": "1787-2025",
            "primary_eras": [
                "Founding Era (1787-1789)",
                "Reconstruction Era (1865-1870)",
                "Progressive Era (1900-1920)",
                "Civil Rights Era (1954-1968)",
                "Contemporary Era (1980-2025)",
            ],
        },
        "frameworks": {},
    }

    # Define all 10 frameworks with complete metadata
    frameworks_data = get_frameworks_data()

    clf_data["frameworks"] = frameworks_data

    # Add weight normalization
    clf_data["weight_normalization"] = {
        "description": "JIM weights represent relative importance in constitutional interpretation. ACE weights represent relevance to anomaly detection and constitutional risk scoring.",
        "jim_total": sum(f["jim_weight"] for f in frameworks_data.values()),
        "ace_total": sum(f["ace_weight"] for f in frameworks_data.values()),
        "normalization_method": "Weights assigned based on judicial practice, doctrinal authority, and scholarly consensus.",
    }

    # Add conflict resolution rules
    clf_data["conflict_resolution"] = get_conflict_resolution_rules()

    # Add integration points
    clf_data["integration_points"] = get_integration_points()

    # Add validation rules
    clf_data["validation_rules"] = get_validation_rules()

    return clf_data


def get_frameworks_data():
    """Return all 10 constitutional interpretation frameworks."""

    frameworks = {}

    # 1. Original Public Meaning (OPM)
    frameworks["original_public_meaning"] = {
        "framework_id": "opm",
        "name": "Original Public Meaning (OPM)",
        "definition": "Constitutional interpretation based on the public understanding of the text at the time it was ratified. Focuses on how a reasonable person at the time would have understood the language, considering linguistic conventions, legal dictionaries, and common usage of the era.",
        "method": "Analyze constitutional text using contemporaneous dictionaries (e.g., Samuel Johnson's Dictionary, Webster's 1828), legal treatises, public debates, newspapers, and other founding-era sources to determine original meaning.",
        "historical_origin": "Developed in late 20th century by scholars like Randy Barnett and Justice Scalia as evolution of originalism.",
        "temporal_scope": {
            "primary_era": "1787-1791",
            "applicable_to": ["Original Constitution (1787)", "Bill of Rights (1791)"],
        },
        "strengths": [
            "Provides objective, verifiable anchor point",
            "Respects democratic legitimacy of ratification",
            "Constrains judicial discretion",
            "More accessible than framers' subjective intent",
        ],
        "weaknesses": [
            "Difficult to reconstruct public understanding with certainty",
            "May not address modern circumstances",
            "Requires extensive historical research",
            "Public understanding may have been diverse",
        ],
        "landmark_cases": [
            {
                "case": "District of Columbia v. Heller",
                "citation": "554 U.S. 570 (2008)",
                "application": "Analyzed founding-era understanding of 'bear arms' and 'militia'.",
            },
            {
                "case": "Crawford v. Washington",
                "citation": "541 U.S. 36 (2004)",
                "application": "Examined original meaning of 'confrontation' in Sixth Amendment.",
            },
        ],
        "jim_weight": 0.30,
        "ace_weight": 0.28,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.15,
            "1789_to_1920": 0.35,
            "1789_to_2025": 0.65,
            "notes": "Significant drift in 'commerce', 'speech', 'arms'.",
        },
        "key_scholars": [
            {
                "name": "Randy Barnett",
                "contribution": "Systematic OPM methodology",
                "key_work": "Restoring the Lost Constitution (2004)",
            },
            {
                "name": "Antonin Scalia",
                "contribution": "Applied OPM in Supreme Court",
                "key_work": "A Matter of Interpretation (1997)",
            },
        ],
    }

    # 2. Textualism
    frameworks["textualism"] = {
        "framework_id": "textualism",
        "name": "Textualism",
        "definition": "Interpretation based strictly on plain meaning of constitutional text using ordinary linguistic tools without resort to legislative history, framers' intentions, or policy considerations.",
        "method": "Apply linguistic canons: plain meaning rule, whole text canon, harmonious reading, grammar analysis. Use contemporaneous dictionaries for technical terms.",
        "historical_origin": "Championed by Justice Scalia and Judge Frank Easterbrook. Gained prominence in 1980s-1990s.",
        "temporal_scope": {
            "primary_era": "1787-present",
            "applicable_to": ["All constitutional provisions"],
        },
        "strengths": [
            "Promotes rule of law through predictable interpretation",
            "Respects separation of powers",
            "Accessible to lawyers and judges",
            "Reduces partisan manipulation",
        ],
        "weaknesses": [
            "May produce absurd results",
            "Ignores context and purpose",
            "Linguistic canons can be indeterminate",
            "Assumes unified 'plain meaning'",
        ],
        "landmark_cases": [
            {
                "case": "United States v. Apel",
                "citation": "571 U.S. 359 (2014)",
                "application": "Textualist interpretation of 'military base'.",
            },
            {
                "case": "Bostock v. Clayton County",
                "citation": "590 U.S. 644 (2020)",
                "application": "Textualist analysis of 'sex' in Title VII.",
            },
        ],
        "jim_weight": 0.25,
        "ace_weight": 0.22,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.10,
            "1789_to_1920": 0.20,
            "1789_to_2025": 0.40,
            "notes": "Moderate drift in abstract terms, minimal in concrete terms.",
        },
        "key_scholars": [
            {
                "name": "Antonin Scalia",
                "contribution": "Primary judicial proponent",
                "key_work": "Reading Law (2012)",
            },
            {
                "name": "John Manning",
                "contribution": "Theoretical defense",
                "key_work": "What Divides Textualists from Purposivists? (1997)",
            },
        ],
    }

    # 3. Framers' Intent
    frameworks["framers_intent"] = {
        "framework_id": "framers_intent",
        "name": "Framers' Intent (1787–1789)",
        "definition": "Constitutional interpretation seeking to discern and apply specific intentions of individuals who drafted and ratified the Constitution.",
        "method": "Analyze Constitutional Convention debates, Federalist Papers, ratification debates, private correspondence of framers.",
        "historical_origin": "Dominant in 19th century. Associated with judges like Robert Bork in modern era.",
        "temporal_scope": {
            "primary_era": "1787-1789",
            "applicable_to": [
                "Original Constitution articles",
                "Bill of Rights through Madison",
            ],
        },
        "strengths": [
            "Respects constitutional design",
            "Provides insight into structural elements",
            "Rich historical record available",
        ],
        "weaknesses": [
            "Framers often disagreed",
            "Subjective intent difficult to reconstruct",
            "Privileges elite framers over ratifying public",
            "Could not anticipate modern circumstances",
        ],
        "landmark_cases": [
            {
                "case": "Myers v. United States",
                "citation": "272 U.S. 52 (1926)",
                "application": "Reviewed Convention debates on presidential removal power.",
            },
            {
                "case": "INS v. Chadha",
                "citation": "462 U.S. 919 (1983)",
                "application": "Analyzed framers' design of bicameralism.",
            },
        ],
        "jim_weight": 0.20,
        "ace_weight": 0.18,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.20,
            "1789_to_1920": 0.40,
            "1789_to_2025": 0.70,
            "notes": "Framers' intentions less relevant as society changes.",
        },
        "key_scholars": [
            {
                "name": "Robert Bork",
                "contribution": "Modern advocate of original intent",
                "key_work": "The Tempting of America (1990)",
            },
            {
                "name": "Jack Rakove",
                "contribution": "Historical analysis of framers' understandings",
                "key_work": "Original Meanings (1996)",
            },
        ],
    }

    # 4. Purposivism
    frameworks["purposivism"] = {
        "framework_id": "purposivism",
        "name": "Purposivism",
        "definition": "Constitutional interpretation identifying and advancing underlying purposes, values, and principles that animate constitutional provisions.",
        "method": "Identify constitutional purpose through text, structure, historical context, and evolving values. Consider practical consequences. Balance competing purposes.",
        "historical_origin": "Rooted in legal process school of 1950s-60s. Championed by Justice Breyer in modern Court.",
        "temporal_scope": {
            "primary_era": "1787-present",
            "applicable_to": [
                "All constitutional provisions",
                "Abstract provisions like Due Process, Equal Protection",
            ],
        },
        "strengths": [
            "Allows Constitution to adapt",
            "Focuses on substantive goals",
            "Considers practical consequences",
            "Accommodates reasonable disagreement",
        ],
        "weaknesses": [
            "Purposes often contested",
            "Risks judicial policymaking",
            "Difficult to distinguish from amendment",
            "May subordinate text",
        ],
        "landmark_cases": [
            {
                "case": "United States v. Booker",
                "citation": "543 U.S. 220 (2005)",
                "application": "Purposivist analysis of Sentencing Guidelines.",
            },
            {
                "case": "NFIB v. Sebelius",
                "citation": "567 U.S. 519 (2012)",
                "application": "Construed mandate as tax consistent with purpose.",
            },
        ],
        "jim_weight": 0.15,
        "ace_weight": 0.20,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.25,
            "1789_to_1920": 0.45,
            "1789_to_2025": 0.50,
            "notes": "Purposivism accepts drift by focusing on underlying goals.",
        },
        "key_scholars": [
            {
                "name": "Stephen Breyer",
                "contribution": "Active liberty and purposive interpretation",
                "key_work": "Active Liberty (2005)",
            },
            {
                "name": "William Eskridge",
                "contribution": "Dynamic statutory interpretation",
                "key_work": "Dynamic Statutory Interpretation (1994)",
            },
        ],
    }

    # 5. Structuralism
    frameworks["structuralism"] = {
        "framework_id": "structuralism",
        "name": "Structuralism",
        "definition": "Constitutional interpretation from inferences about relationships among provisions and institutions. Emphasizes overall design and internal coherence.",
        "method": "Analyze relationships between provisions. Examine allocation of powers. Identify structural implications of federalism, separation of powers, checks and balances.",
        "historical_origin": "Articulated by Charles Black (1969). Reflected in Marshall's McCulloch and Marbury opinions.",
        "temporal_scope": {
            "primary_era": "1787-present",
            "applicable_to": [
                "Federal-state relationships",
                "Separation of powers",
                "Implied principles",
            ],
        },
        "strengths": [
            "Captures principles not explicit in text",
            "Emphasizes systemic coherence",
            "Useful for novel structural questions",
            "Respects framers' architecture",
        ],
        "weaknesses": [
            "Structural inferences can be indeterminate",
            "Risks judicial creativity",
            "May subordinate text to concepts",
            "Hard to distinguish valid from invalid arguments",
        ],
        "landmark_cases": [
            {
                "case": "McCulloch v. Maryland",
                "citation": "17 U.S. 316 (1819)",
                "application": "Structural inferences from federal supremacy.",
            },
            {
                "case": "Printz v. United States",
                "citation": "521 U.S. 898 (1997)",
                "application": "Structural federalism to prohibit commandeering.",
            },
        ],
        "jim_weight": 0.18,
        "ace_weight": 0.16,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.15,
            "1789_to_1920": 0.30,
            "1789_to_2025": 0.35,
            "notes": "Structural principles stable but applications evolve.",
        },
        "key_scholars": [
            {
                "name": "Charles Black",
                "contribution": "Foundational articulation",
                "key_work": "Structure and Relationship (1969)",
            },
            {
                "name": "Akhil Amar",
                "contribution": "Structural analysis of sovereignty",
                "key_work": "America's Constitution (2005)",
            },
        ],
    }

    # 6. Pragmatism / Judicial Minimalism
    frameworks["pragmatism_minimalism"] = {
        "framework_id": "pragmatism_minimalism",
        "name": "Pragmatism / Judicial Minimalism",
        "definition": "Constitutional interpretation emphasizing practical consequences, incremental decision-making, and narrow rulings. Combines consequentialism with judicial restraint.",
        "method": "Decide cases on narrowest grounds. Consider practical consequences. Prefer rules allowing democratic experimentation. Avoid broad pronouncements.",
        "historical_origin": "Pragmatism rooted in American philosophers. Judicial minimalism articulated by Cass Sunstein.",
        "temporal_scope": {
            "primary_era": "1787-present",
            "applicable_to": [
                "All constitutional questions",
                "Evolving technologies and social issues",
            ],
        },
        "strengths": [
            "Reduces error costs",
            "Promotes judicial legitimacy",
            "Allows democratic processes",
            "Considers real-world consequences",
            "Builds consensus",
        ],
        "weaknesses": [
            "May sacrifice clarity",
            "Risks inconsistent precedents",
            "Can appear unprincipled",
            "Delays important resolutions",
            "Hard to distinguish from politics",
        ],
        "landmark_cases": [
            {
                "case": "Grutter v. Bollinger",
                "citation": "539 U.S. 306 (2003)",
                "application": "Minimalist approach with 25-year sunset.",
            },
            {
                "case": "NFIB v. Sebelius",
                "citation": "567 U.S. 519 (2012)",
                "application": "Avoided crisis by narrow tax construction.",
            },
        ],
        "jim_weight": 0.12,
        "ace_weight": 0.15,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.20,
            "1789_to_1920": 0.40,
            "1789_to_2025": 0.45,
            "notes": "Accepts moderate drift, focuses on contemporary consequences.",
        },
        "key_scholars": [
            {
                "name": "Cass Sunstein",
                "contribution": "Theoretical foundation for minimalism",
                "key_work": "One Case at a Time (1999)",
            },
            {
                "name": "Richard Posner",
                "contribution": "Pragmatic approach",
                "key_work": "How Judges Think (2008)",
            },
        ],
    }

    # 7. Living Constitutionalism
    frameworks["living_constitutionalism"] = {
        "framework_id": "living_constitutionalism",
        "name": "Living Constitutionalism",
        "definition": "Constitutional interpretation viewing Constitution as evolving document whose meaning adapts to changing social values. Used for comparative weighting only.",
        "method": "Interpret abstract provisions in light of evolving standards, contemporary values, changed circumstances. Consider moral philosophy and social science.",
        "historical_origin": "Articulated by Woodrow Wilson (1908). Developed through Warren Court. Defended by Strauss, Balkin, Post.",
        "temporal_scope": {
            "primary_era": "1787-present (emphasis on present)",
            "applicable_to": [
                "Abstract provisions",
                "Rights and liberties",
                "Structural provisions requiring adaptation",
            ],
        },
        "strengths": [
            "Addresses modern problems",
            "Responds to evolving consensus",
            "Maintains constitutional relevance",
            "Accommodates civil rights progress",
        ],
        "weaknesses": [
            "Risks untethered policymaking",
            "Hard to distinguish from amendment",
            "May undermine democratic control",
            "Lacks clear constraints",
            "Can privilege judicial preferences",
        ],
        "landmark_cases": [
            {
                "case": "Brown v. Board of Education",
                "citation": "347 U.S. 483 (1954)",
                "application": "Overruled Plessy using evolving understanding.",
            },
            {
                "case": "Obergefell v. Hodges",
                "citation": "576 U.S. 644 (2015)",
                "application": "Marriage equality through evolving understanding.",
            },
        ],
        "jim_weight": 0.08,
        "ace_weight": 0.10,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.30,
            "1789_to_1920": 0.60,
            "1789_to_2025": 0.85,
            "notes": "Embraces drift as feature. High scores reflect intentional updating.",
        },
        "key_scholars": [
            {
                "name": "David Strauss",
                "contribution": "Common-law constitutionalism",
                "key_work": "The Living Constitution (2010)",
            },
            {
                "name": "Jack Balkin",
                "contribution": "Living originalism framework",
                "key_work": "Living Originalism (2011)",
            },
        ],
    }

    # 8. Reconstruction-Era Intent
    frameworks["reconstruction_era_intent"] = {
        "framework_id": "reconstruction_intent",
        "name": "Reconstruction-Era Intent (13A, 14A, 15A; 1865–1870)",
        "definition": "Constitutional interpretation specific to Reconstruction Amendments based on understanding of Republican Congress and ratifying states in post-Civil War period.",
        "method": "Analyze Reconstruction Congressional debates, Civil Rights Acts, Freedmen's Bureau Acts, ratification debates. Emphasize Section 5 enforcement powers.",
        "historical_origin": "Emerged from Reconstruction scholarship (Foner, Curtis, Nelson). Gained traction through Justice Thomas's concurrences.",
        "temporal_scope": {
            "primary_era": "1865-1870",
            "applicable_to": [
                "13th Amendment (1865)",
                "14th Amendment (1868)",
                "15th Amendment (1870)",
                "Reconstruction civil rights statutes",
            ],
        },
        "strengths": [
            "Captures transformative anti-slavery purposes",
            "Emphasizes federal enforcement power",
            "Rich historical record",
            "Strong foundation for civil rights",
        ],
        "weaknesses": [
            "Compromises complicate intent",
            "Questions about scope remain",
            "Ratification under duress",
            "Understanding may have been narrower",
        ],
        "landmark_cases": [
            {
                "case": "The Slaughter-House Cases",
                "citation": "83 U.S. 36 (1873)",
                "application": "First 14th Amendment interpretation, narrowly construed.",
            },
            {
                "case": "McDonald v. City of Chicago",
                "citation": "561 U.S. 742 (2010)",
                "application": "Thomas analyzed Reconstruction-era Privileges or Immunities.",
            },
        ],
        "jim_weight": 0.35,
        "ace_weight": 0.32,
        "reconstruction_override": True,
        "semantic_drift": {
            "1868_to_1920": 0.25,
            "1868_to_1960": 0.40,
            "1868_to_2025": 0.55,
            "notes": "Initially undermined by narrow construction. Warren Court revived purposes.",
        },
        "key_scholars": [
            {
                "name": "Eric Foner",
                "contribution": "Comprehensive Reconstruction history",
                "key_work": "Reconstruction: America's Unfinished Revolution (1988)",
            },
            {
                "name": "Michael Kent Curtis",
                "contribution": "14th Amendment framing",
                "key_work": "No State Shall Abridge (1986)",
            },
        ],
    }

    # 9. Historical-Context Analysis
    frameworks["historical_context_analysis"] = {
        "framework_id": "historical_context",
        "name": "Historical-Context Analysis (Multi-Era)",
        "definition": "Constitutional interpretation using historical context across multiple eras to understand provisions and track semantic evolution.",
        "method": "Identify relevant era(s). Analyze political, social, economic, intellectual context. Examine how context influenced meaning. Consider path dependency.",
        "historical_origin": "Rooted in legal history scholarship. Developed by historians like Bailyn, Wood, and constitutional scholars.",
        "temporal_scope": {
            "primary_era": "Multi-era (1787-present)",
            "applicable_to": [
                "Founding Era (1787-1791)",
                "Reconstruction Era (1865-1870)",
                "Progressive Era (1900-1920)",
                "Civil Rights Era (1954-1968)",
            ],
        },
        "strengths": [
            "Rich contextual understanding",
            "Accounts for different meanings across eras",
            "Sophisticated treatment of development",
            "Illuminates purposes while recognizing change",
        ],
        "weaknesses": [
            "Context can be contested",
            "Requires extensive expertise",
            "Risk of anachronistic reading",
            "May not provide determinate answers",
        ],
        "landmark_cases": [
            {
                "case": "Home Building & Loan v. Blaisdell",
                "citation": "290 U.S. 398 (1934)",
                "application": "Interpreted Contracts Clause in light of economic emergency.",
            },
            {
                "case": "Youngstown Sheet & Tube v. Sawyer",
                "citation": "343 U.S. 579 (1952)",
                "application": "Jackson's historically-grounded separation of powers framework.",
            },
        ],
        "jim_weight": 0.22,
        "ace_weight": 0.25,
        "reconstruction_override": False,
        "semantic_drift": {
            "multi_era_framework": True,
            "era_specific_analysis": {
                "1787_1791": 0.0,
                "1791_1868": 0.20,
                "1868_1920": 0.35,
                "1920_1960": 0.50,
                "1960_2025": 0.40,
            },
            "notes": "Explicitly addresses drift by examining meaning across eras.",
        },
        "key_scholars": [
            {
                "name": "Bernard Bailyn",
                "contribution": "Intellectual origins of Revolution",
                "key_work": "Ideological Origins (1967)",
            },
            {
                "name": "Bruce Ackerman",
                "contribution": "Constitutional moments",
                "key_work": "We the People (1991)",
            },
        ],
    }

    # 10. Founding-Era Linguistic Baselines
    frameworks["founding_era_linguistic_baselines"] = {
        "framework_id": "founding_linguistic",
        "name": "Founding-Era Linguistic Baselines",
        "definition": "Systematic linguistic analysis establishing baseline meanings using founding-era dictionaries, treatises, and contemporaneous usage patterns.",
        "method": "Consult founding-era dictionaries (Johnson 1755, Webster 1828), Blackstone, common law treatises, state constitutions. Document semantic range. Trace etymology.",
        "historical_origin": "Developed through modern originalist scholarship. Corpus linguistics methodology emerging in 2010s-2020s.",
        "temporal_scope": {
            "primary_era": "1750-1800 (emphasis 1787-1791)",
            "applicable_to": [
                "Original Constitution (1787)",
                "Bill of Rights (1791)",
                "Baseline for later amendments",
            ],
        },
        "strengths": [
            "Provides objective evidence",
            "Grounds interpretation in linguistic evidence",
            "Corpus linguistics enables empirical analysis",
            "Distinguishes core from peripheral meaning",
        ],
        "weaknesses": [
            "Sources may be incomplete",
            "Terms often had multiple meanings",
            "Legal terms may differ from ordinary usage",
            "Difficult to weight sources",
            "Results can be manipulated",
        ],
        "landmark_cases": [
            {
                "case": "District of Columbia v. Heller",
                "citation": "554 U.S. 570 (2008)",
                "application": "Analyzed founding-era dictionaries and usage.",
            },
            {
                "case": "Carpenter v. United States",
                "citation": "585 U.S. 296 (2018)",
                "application": "Gorsuch used founding-era property concepts.",
            },
        ],
        "jim_weight": 0.28,
        "ace_weight": 0.26,
        "reconstruction_override": False,
        "semantic_drift": {
            "1789_to_1868": 0.18,
            "1789_to_1920": 0.38,
            "1789_to_2025": 0.68,
            "notes": "Documents precise extent of drift. 'Commerce', 'speech', 'arms' show measurable drift.",
        },
        "key_scholars": [
            {
                "name": "Lawrence Solum",
                "contribution": "Semantic originalism and fixation",
                "key_work": "Semantic Originalism (2008)",
            },
            {
                "name": "Thomas Lee & Stephen Mouritsen",
                "contribution": "Corpus linguistics methodology",
                "key_work": "Judging Ordinary Meaning (2018)",
            },
        ],
    }

    return frameworks


def get_conflict_resolution_rules():
    """Return conflict resolution rules."""
    return {
        "description": "Rules for resolving conflicts between constitutional interpretation frameworks",
        "rules": [
            {
                "rule": "reconstruction_override",
                "condition": "Constitutional provision is 13th, 14th, or 15th Amendment",
                "action": "Apply reconstruction_era_intent with elevated weight (0.35) and reduce founding_era weights by 30%",
                "rationale": "Reconstruction Amendments specifically amended original Constitution",
            },
            {
                "rule": "temporal_primacy",
                "condition": "Analyzing historical constitutional provision",
                "action": "Prioritize frameworks with temporal_scope matching enactment era",
                "rationale": "Provisions should be interpreted in light of ratification understanding",
            },
            {
                "rule": "structural_deference",
                "condition": "Issue involves separation of powers or federalism",
                "action": "Increase structuralism weight by 50%",
                "rationale": "Structural issues best resolved through architectural analysis",
            },
            {
                "rule": "semantic_drift_adjustment",
                "condition": "High semantic drift score (>0.60) for relevant term",
                "action": "Reduce pure originalist weights, increase historical_context and pragmatism weights",
                "rationale": "Significant linguistic evolution requires contextual analysis",
            },
        ],
    }


def get_integration_points():
    """Return integration points with other systems."""
    return {
        "jim_integration": {
            "description": "Constitutional frameworks integrate with JIM case correlation and risk scoring",
            "methods": ["load_all()", "get_weights_for_jim()", "get_framework(name)"],
            "use_cases": [
                "Weight constitutional doctrines by interpretive framework",
                "Analyze anomalies through multiple interpretive lenses",
                "Generate multi-framework risk assessments",
            ],
        },
        "msh_integration": {
            "description": "CLF harmonizes with MSH semantic harmonization for term disambiguation",
            "methods": [
                "Semantic drift scores align with MSH era-specific definitions",
                "Framework weights inform MSH source authority calculations",
            ],
        },
        "ace_integration": {
            "description": "CLF supports ACE semantic_misalignment anomaly detection",
            "methods": [
                "ACE weights identify constitutional interpretation gaps",
                "Semantic drift scores flag temporal misalignment",
            ],
        },
    }


def get_validation_rules():
    """Return validation rules for schema compliance."""
    return {
        "schema_requirements": [
            "Each framework must have framework_id, name, definition, method, historical_origin",
            "Each framework must have temporal_scope with primary_era",
            "Each framework must have strengths and weaknesses arrays",
            "Each framework must have landmark_cases array",
            "Each framework must have jim_weight and ace_weight",
            "Each framework must have semantic_drift object",
            "Each framework must have key_scholars array",
        ],
        "weight_constraints": [
            "jim_weight must be between 0.05 and 0.40",
            "ace_weight must be between 0.05 and 0.40",
        ],
        "semantic_drift_constraints": [
            "Drift scores must be between 0.0 and 1.0",
            "Later eras must have equal or higher drift than earlier eras",
        ],
    }


def main():
    """Build and save CLF frameworks JSON."""
    # Get repository root
    repo_root = Path(__file__).parent.parent
    output_file = (
        repo_root / "constitutional" / "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
    )

    # Build data
    clf_data = build_all_frameworks()

    # Write to file
    with open(output_file, "w") as f:
        json.dump(clf_data, f, indent=2)

    print(f"✓ Created {output_file}")
    print(f"✓ {clf_data['metadata']['total_frameworks']} frameworks")
    print(f"✓ JIM total weight: {clf_data['weight_normalization']['jim_total']:.2f}")
    print(f"✓ ACE total weight: {clf_data['weight_normalization']['ace_total']:.2f}")


if __name__ == "__main__":
    main()
