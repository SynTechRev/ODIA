"""
JIM Correlation Engine - Links anomalies to legal doctrines and precedents.
"""

from typing import Any

from scripts.jim.jim_case_loader import JIMCaseLoader


class JIMCorrelationEngine:
    """
    Correlates audit anomalies with constitutional doctrines and case law.

    Creates linkages between:
    - ACE anomalies → administrative law principles
    - VICFM procurement issues → due process requirements
    - CAIM agency patterns → separation of powers concerns
    - PDF forensics → evidentiary standards
    - Digital privacy violations → Fourth Amendment protections
    - Use of force incidents → constitutional torts/accountability

    Doctrine Precedence Rules (CLEP-v1):
    When multiple doctrines apply to a single anomaly:
    1. All mapped doctrines are included in correlation result
    2. Doctrines are sorted alphabetically for consistency
    3. Case relevance scoring considers all applicable doctrines
    4. Risk scoring applies weighted combination of all dimensions
    5. No single doctrine takes absolute precedence - comprehensive analysis

    Example: "excessive_force" maps to both "fourth_amendment" and
    "constitutional_torts" - both doctrines analyzed, relevant cases from
    each doctrine included, risk scores from both dimensions applied.
    """

    def __init__(self, case_loader: JIMCaseLoader):
        """
        Initialize correlation engine.

        Args:
            case_loader: Loaded JIMCaseLoader with case law database
        """
        self.case_loader = case_loader

        # Mapping of anomaly patterns to legal doctrines
        # Note: Multiple doctrines per pattern supported (analyzed collectively)
        self.anomaly_doctrine_map = {
            # ACE (Anomaly Correlation Engine) patterns
            "metadata_break": ["due_process", "administrative_law"],
            "chronological_drift": ["administrative_law"],
            "missing_required_field": ["due_process", "administrative_law"],
            "placeholder_value": ["administrative_law"],
            "cross_year_irregularity": ["administrative_law"],
            # VICFM (Vendor Influence Contract Flow Map) patterns
            "sole_source_procurement": ["equal_protection", "due_process"],
            "cost_escalation": ["administrative_law"],
            "vendor_concentration": ["administrative_law", "equal_protection"],
            "procurement_irregularity": ["due_process", "administrative_law"],
            "vendor_contract_interference": ["property_rights", "due_process"],
            # CAIM (Cross-Agency Influence Map) patterns
            "agency_coordination_gap": ["separation_of_powers", "administrative_law"],
            "cross_agency_conflict": ["separation_of_powers"],
            "delegation_without_authority": ["non_delegation", "separation_of_powers"],
            "unclear_jurisdiction": ["administrative_law"],
            # PDF Forensics patterns
            "timestamp_conflict": ["administrative_law"],
            "producer_mismatch": ["administrative_law"],
            "xmp_integrity_failure": ["administrative_law"],
            "forensic_anomaly": ["administrative_law"],
            "evidence_chain_break": ["fourth_amendment"],
            "tainted_evidence": ["fourth_amendment"],
            # Legislative timeline patterns
            "missing_legislative_history": ["administrative_law"],
            "rushed_enactment": ["due_process"],
            "inadequate_notice": ["due_process"],
            # Surveillance and privacy patterns
            "surveillance_program": ["fourth_amendment"],
            "data_collection_without_warrant": ["fourth_amendment"],
            "privacy_expectation_violated": ["fourth_amendment"],
            "warrantless_search": ["fourth_amendment"],
            "digital_privacy_violation": ["fourth_amendment"],
            "cell_site_location_tracking": ["fourth_amendment"],
            "gps_tracking": ["fourth_amendment"],
            # Identity and movement control patterns
            "identity_tracking_system": ["free_movement", "fourth_amendment"],
            "residency_requirement": ["free_movement", "equal_protection"],
            "travel_restriction": ["free_movement", "due_process"],
            "identification_demand": ["fourth_amendment", "free_movement"],
            # Use of force and accountability patterns
            "excessive_force": ["fourth_amendment", "constitutional_torts"],
            "unlawful_detention": ["fourth_amendment", "due_process"],
            "official_misconduct": ["constitutional_torts", "due_process"],
            "qualified_immunity_issue": ["constitutional_torts"],
        }

        # Issue tags that trigger specific case lookups
        self.tag_priority = {
            "due_process": [
                "procedural_due_process",
                "property_interest",
                "evidentiary_hearing",
                "presumption_of_innocence",
                "burden_of_proof",
            ],
            "non_delegation": [
                "intelligible_principle",
                "legislative_power",
                "excessive_delegation",
            ],
            "fourth_amendment": [
                "expectation_of_privacy",
                "warrantless_search",
                "electronic_surveillance",
                "digital_privacy",
                "cell_site_location",
                "gps_tracking",
                "probable_cause",
                "reasonable_suspicion",
                "stop_and_frisk",
                "fruit_of_poisonous_tree",
                "chain_of_custody",
            ],
            "administrative_law": [
                "arbitrary_and_capricious",
                "reasoned_decisionmaking",
                "chevron_deference",
                "major_questions_doctrine",
            ],
            "separation_of_powers": [
                "executive_power",
                "congressional_authorization",
                "presidential_immunity",
                "official_acts",
            ],
            "equal_protection": [
                "arbitrary_discrimination",
                "rational_basis",
            ],
            "constitutional_torts": [
                "qualified_immunity",
                "excessive_force",
                "official_misconduct",
                "section_1983",
            ],
            "property_rights": [
                "liberty_interests",
                "contractual_freedom",
                "takings",
                "economic_liberty",
            ],
            "free_movement": [
                "right_to_travel",
                "interstate_migration",
                "durational_residency",
                "identification_requirement",
            ],
        }

    def correlate_anomaly(self, anomaly: dict[str, Any]) -> dict[str, Any]:
        """
        Correlate single anomaly to legal doctrines and precedents.

        Args:
            anomaly: Anomaly data from audit systems

        Returns:
            Correlation result with linked doctrines, cases, and risk indicators.
        """
        anomaly_type = anomaly.get("type") or anomaly.get("category", "unknown")
        anomaly_source = anomaly.get("source", "unknown")

        # Map to doctrines
        doctrines = self._identify_doctrines(anomaly_type, anomaly)

        # Find relevant cases
        relevant_cases = self._find_relevant_cases(doctrines, anomaly)

        # Identify applicable canons
        canons = self._identify_canons(anomaly)

        # Assess specific legal risks
        risk_indicators = self._assess_risk_indicators(anomaly, doctrines)

        return {
            "anomaly_id": anomaly.get("id") or anomaly.get("anomaly_id", "unknown"),
            "anomaly_type": anomaly_type,
            "source_system": anomaly_source,
            "doctrines": doctrines,
            "relevant_cases": relevant_cases,
            "interpretive_canons": canons,
            "risk_indicators": risk_indicators,
            "constitutional_basis": self._identify_constitutional_basis(doctrines),
            "major_questions_applicable": self._check_major_questions(anomaly),
        }

    def _identify_doctrines(
        self, anomaly_type: str, anomaly: dict[str, Any]
    ) -> list[str]:
        """Identify applicable legal doctrines for anomaly type."""
        doctrines = set(self.anomaly_doctrine_map.get(anomaly_type, []))

        # Check for specific flags in anomaly
        if anomaly.get("affects_rights"):
            doctrines.add("due_process")
        if anomaly.get("involves_surveillance"):
            doctrines.add("fourth_amendment")
        if anomaly.get("lacks_standards"):
            doctrines.add("non_delegation")
        if anomaly.get("lacks_reasoning"):
            doctrines.add("administrative_law")
        if anomaly.get("cross_agency_issue"):
            doctrines.add("separation_of_powers")

        return sorted(list(doctrines))

    def _find_relevant_cases(
        self, doctrines: list[str], anomaly: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Find Supreme Court cases relevant to identified doctrines."""
        relevant_cases = []
        seen_cases = set()

        for doctrine in doctrines:
            # Get cases for this doctrine
            doctrine_cases = self.case_loader.get_cases_by_doctrine(doctrine)

            # Prioritize by doctrinal weight and relevance
            for case in doctrine_cases:
                case_id = case.get("case_id")
                if case_id in seen_cases:
                    continue

                seen_cases.add(case_id)

                # Calculate relevance score
                relevance = self._calculate_case_relevance(case, anomaly, doctrine)

                if relevance > 0.3:  # Threshold for inclusion
                    relevant_cases.append(
                        {
                            "case_id": case_id,
                            "name": case.get("name"),
                            "citation": case.get("citation"),
                            "year": case.get("year"),
                            "doctrine": case.get("doctrine"),
                            "holding": case.get("holding"),
                            "relevance_score": round(relevance, 3),
                            "doctrinal_weight": case.get("doctrinal_weight", 0.5),
                        }
                    )

        # Sort by relevance
        relevant_cases.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Return top 5 most relevant
        return relevant_cases[:5]

    def _calculate_case_relevance(
        self, case: dict[str, Any], anomaly: dict[str, Any], doctrine: str
    ) -> float:
        """Calculate relevance score for case to anomaly."""
        score = 0.0

        # Base score from doctrinal weight
        score += case.get("doctrinal_weight", 0.5) * 0.5

        # Check issue tag matching
        anomaly_context = anomaly.get("description", "").lower()
        for tag in case.get("issue_tags", []):
            if tag.replace("_", " ") in anomaly_context:
                score += 0.1

        # Boost recent cases for some doctrines
        if doctrine in ["administrative_law", "fourth_amendment"]:
            year = case.get("year", 1900)
            if year >= 2000:
                score += 0.2
            elif year >= 1980:
                score += 0.1

        return min(score, 1.0)

    def _identify_canons(self, anomaly: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify applicable interpretive canons."""
        canons = []

        # Major questions doctrine
        if anomaly.get("economic_significance", False) or anomaly.get(
            "major_policy_shift", False
        ):
            canon = self.case_loader.get_interpretive_canon("major_questions_doctrine")
            if canon:
                canons.append(canon)

        # Clear statement rule
        if anomaly.get("affects_rights", False):
            canon = self.case_loader.get_interpretive_canon("clear_statement_rule")
            if canon:
                canons.append(canon)

        # Constitutional avoidance
        if anomaly.get("constitutional_doubt", False):
            canon = self.case_loader.get_interpretive_canon("avoidance_canon")
            if canon:
                canons.append(canon)

        # Rule of lenity (for penal provisions)
        if anomaly.get("imposes_penalty", False):
            canon = self.case_loader.get_interpretive_canon("rule_of_lenity")
            if canon:
                canons.append(canon)

        return canons

    def _assess_risk_indicators(
        self, anomaly: dict[str, Any], doctrines: list[str]
    ) -> dict[str, Any]:
        """Assess specific legal risk indicators."""
        indicators = {
            "affects_constitutional_rights": bool(
                "due_process" in doctrines
                or "fourth_amendment" in doctrines
                or "equal_protection" in doctrines
            ),
            "separation_of_powers_concern": "separation_of_powers" in doctrines,
            "delegation_issue": "non_delegation" in doctrines,
            "administrative_procedure_violation": "administrative_law" in doctrines,
            "evidentiary_concern": anomaly.get("forensic_score", 100) < 70,
            "requires_clear_authorization": (
                "non_delegation" in doctrines
                or anomaly.get("major_policy_shift", False)
            ),
        }

        return indicators

    def _identify_constitutional_basis(self, doctrines: list[str]) -> list[str]:
        """Identify constitutional provisions implicated by doctrines."""
        basis = []

        doctrine_constitution_map = {
            "due_process": [
                "Fifth Amendment Due Process",
                "Fourteenth Amendment Due Process",
            ],
            "fourth_amendment": ["Fourth Amendment"],
            "equal_protection": ["Fourteenth Amendment Equal Protection"],
            "non_delegation": ["Article I, Section 1"],
            "separation_of_powers": ["Article I", "Article II", "Article III"],
            "administrative_law": [
                "Article I",
                "Article II",
                "Administrative Procedure Act",
            ],
        }

        for doctrine in doctrines:
            basis.extend(doctrine_constitution_map.get(doctrine, []))

        return sorted(list(set(basis)))

    def _check_major_questions(self, anomaly: dict[str, Any]) -> bool:
        """Check if major questions doctrine is applicable."""
        return bool(
            anomaly.get("economic_significance", False)
            or anomaly.get("political_significance", False)
            or anomaly.get("major_policy_shift", False)
            or anomaly.get("vast_economic_impact", False)
        )

    def correlate_multiple_anomalies(
        self, anomalies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Correlate multiple anomalies and identify patterns.

        Args:
            anomalies: List of anomalies from audit systems

        Returns:
            Aggregate correlation with pattern analysis.
        """
        correlations = []
        doctrine_frequency = {}
        case_frequency = {}

        for anomaly in anomalies:
            correlation = self.correlate_anomaly(anomaly)
            correlations.append(correlation)

            # Track doctrine frequency
            for doctrine in correlation["doctrines"]:
                doctrine_frequency[doctrine] = doctrine_frequency.get(doctrine, 0) + 1

            # Track case frequency
            for case in correlation["relevant_cases"]:
                case_id = case["case_id"]
                case_frequency[case_id] = case_frequency.get(case_id, 0) + 1

        # Identify dominant patterns
        dominant_doctrines = sorted(
            doctrine_frequency.items(), key=lambda x: x[1], reverse=True
        )[:3]

        dominant_cases = sorted(
            case_frequency.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_anomalies_correlated": len(anomalies),
            "individual_correlations": correlations,
            "doctrine_frequency": doctrine_frequency,
            "dominant_doctrines": dominant_doctrines,
            "case_frequency": case_frequency,
            "dominant_cases": dominant_cases,
            "systemic_patterns": self._identify_systemic_patterns(correlations),
        }

    def _identify_systemic_patterns(
        self, correlations: list[dict[str, Any]]
    ) -> list[str]:
        """Identify systemic legal issues from multiple correlations."""
        patterns = []

        # Count constitutional rights impacts
        rights_impacts = sum(
            1
            for c in correlations
            if c.get("risk_indicators", {}).get("affects_constitutional_rights", False)
        )
        if rights_impacts > len(correlations) * 0.3:
            patterns.append(
                f"Systemic constitutional rights concerns ({rights_impacts} instances)"
            )

        # Count delegation issues
        delegation_issues = sum(
            1
            for c in correlations
            if c.get("risk_indicators", {}).get("delegation_issue", False)
        )
        if delegation_issues > len(correlations) * 0.2:
            patterns.append(
                f"Recurring delegation problems ({delegation_issues} instances)"
            )

        # Count administrative procedure violations
        admin_violations = sum(
            1
            for c in correlations
            if c.get("risk_indicators", {}).get(
                "administrative_procedure_violation", False
            )
        )
        if admin_violations > len(correlations) * 0.4:
            patterns.append(
                f"Widespread administrative law issues ({admin_violations} instances)"
            )

        return patterns
