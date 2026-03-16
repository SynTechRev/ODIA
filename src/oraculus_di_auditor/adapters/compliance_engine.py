"""CCOPS Compliance Assessment Engine.

Merges CCOPS model bill mandates with ODIA analysis findings to produce
structured compliance assessments for jurisdictions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

from oraculus_di_auditor.adapters.atlas_adapter import AtlasAdapter
from oraculus_di_auditor.adapters.ccops_adapter import CCOPSAdapter, CCOPSMandate


class ComplianceStatus(BaseModel):
    """Status of a single CCOPS mandate for a jurisdiction."""

    mandate_id: str
    mandate_title: str
    status: str  # "compliant", "non_compliant", "unknown", "partial"
    evidence_found: list[str]  # What evidence was found
    violations: list[dict]  # ODIA findings that indicate non-compliance
    detector_results: dict[str, int]  # detector_name -> anomaly count
    severity: str  # severity if non-compliant


class ComplianceScorecard(BaseModel):
    """Complete CCOPS compliance assessment for a jurisdiction."""

    jurisdiction: str
    assessment_date: str
    has_ccops_ordinance: bool
    total_mandates: int = 11
    compliant_count: int = 0
    non_compliant_count: int = 0
    unknown_count: int = 0
    partial_count: int = 0
    compliance_percentage: float = 0.0
    overall_risk: str = "unknown"  # "low", "moderate", "high", "critical"
    mandate_statuses: list[ComplianceStatus] = []
    technology_inventory: list[dict] = []  # From Atlas if available
    recommendations: list[str] = []


_STATUS_SYMBOL: dict[str, str] = {
    "compliant": "PASS",
    "non_compliant": "FAIL",
    "partial": "PARTIAL",
    "unknown": "UNKNOWN",
}


class ComplianceAssessmentEngine:
    """Merges CCOPS requirements with ODIA findings for compliance assessment."""

    def __init__(
        self,
        ccops: CCOPSAdapter,
        atlas: AtlasAdapter | None = None,
    ):
        self.ccops = ccops
        self.atlas = atlas

    def assess(
        self,
        jurisdiction: str,
        analysis_results: list[dict[str, Any]],
        state: str | None = None,
        has_ccops_ordinance: bool = False,
        ran_detectors: set[str] | None = None,
    ) -> ComplianceScorecard:
        """Run complete CCOPS compliance assessment.

        Steps:
        1. Get all 11 CCOPS mandates.
        2. For each mandate, check which ODIA detectors are relevant.
        3. Look through analysis_results for findings from those detectors.
        4. If relevant detectors found violations -> non_compliant.
        5. If relevant detectors ran but found nothing -> compliant.
        6. If only some relevant detectors ran and found nothing -> partial.
        7. If no relevant detectors ran -> unknown.
        8. If Atlas data available, include technology inventory.
        9. Compute overall compliance score and risk level.
        10. Generate specific recommendations for non-compliant mandates.

        Args:
            jurisdiction: Name of the jurisdiction being assessed.
            analysis_results: ODIA anomaly findings (each dict must have a
                ``layer`` key matching an ODIA detector name).
            state: Optional state abbreviation used for Atlas inventory lookup.
            has_ccops_ordinance: Whether the jurisdiction has adopted a CCOPS
                ordinance.
            ran_detectors: Explicit set of detector names that were executed.
                If ``None``, inferred from the ``layer`` values in
                ``analysis_results``. Pass a full set to mark detectors as
                having run even when they produced no findings.
        """
        if ran_detectors is None:
            ran_detectors = {r["layer"] for r in analysis_results if "layer" in r}

        mandates = self.ccops.get_all_mandates()
        mandate_statuses = [
            self._assess_mandate(m, analysis_results, ran_detectors) for m in mandates
        ]

        counts: dict[str, int] = {
            "compliant": 0,
            "non_compliant": 0,
            "partial": 0,
            "unknown": 0,
        }
        for ms in mandate_statuses:
            counts[ms.status] = counts.get(ms.status, 0) + 1

        compliance_pct = round(counts["compliant"] / len(mandates) * 100, 2)

        tech_inventory: list[dict] = []
        if self.atlas is not None and self.atlas.is_loaded():
            query: dict[str, Any] = {"agency": jurisdiction}
            if state:
                query["state"] = state
            tech_inventory = self.atlas.fetch(query)

        scorecard = ComplianceScorecard(
            jurisdiction=jurisdiction,
            assessment_date=datetime.now(UTC).strftime("%Y-%m-%d"),
            has_ccops_ordinance=has_ccops_ordinance,
            total_mandates=len(mandates),
            compliant_count=counts["compliant"],
            non_compliant_count=counts["non_compliant"],
            unknown_count=counts["unknown"],
            partial_count=counts["partial"],
            compliance_percentage=compliance_pct,
            mandate_statuses=mandate_statuses,
            technology_inventory=tech_inventory,
        )

        scorecard.overall_risk = self._compute_risk_level(scorecard)
        scorecard.recommendations = self._generate_recommendations(scorecard)
        return scorecard

    def _assess_mandate(
        self,
        mandate: CCOPSMandate,
        analysis_results: list[dict[str, Any]],
        ran_detectors: set[str],
    ) -> ComplianceStatus:
        """Assess compliance for a single mandate."""
        detector_results: dict[str, int] = {}
        violations: list[dict] = []
        evidence_found: list[str] = []

        for detector in mandate.verification_detectors:
            findings = [r for r in analysis_results if r.get("layer") == detector]
            count = len(findings)
            detector_results[detector] = count
            violations.extend(findings)

            if detector in ran_detectors:
                label = (
                    f"{detector}: {count} violation(s) found"
                    if count > 0
                    else f"{detector}: no violations found"
                )
                evidence_found.append(label)

        relevant_ran = [d for d in mandate.verification_detectors if d in ran_detectors]
        relevant_not_ran = [
            d for d in mandate.verification_detectors if d not in ran_detectors
        ]

        if violations:
            status = "non_compliant"
        elif not relevant_ran:
            status = "unknown"
        elif relevant_not_ran:
            status = "partial"
        else:
            status = "compliant"

        return ComplianceStatus(
            mandate_id=mandate.mandate_id,
            mandate_title=mandate.title,
            status=status,
            evidence_found=evidence_found,
            violations=violations,
            detector_results=detector_results,
            severity=mandate.severity_if_missing,
        )

    def _compute_risk_level(self, scorecard: ComplianceScorecard) -> str:
        """Compute overall risk level.

        critical — any critical-severity mandate is non_compliant
        high     — more than 3 mandates are non_compliant or partial
        moderate — 1–3 mandates are non_compliant or partial
        low      — no violations found (all compliant or unknown)
        """
        critical_mandate_ids = {
            m.mandate_id
            for m in self.ccops.get_all_mandates()
            if m.severity_if_missing == "critical"
        }

        for ms in scorecard.mandate_statuses:
            if ms.status == "non_compliant" and ms.mandate_id in critical_mandate_ids:
                return "critical"

        failing = sum(
            1
            for ms in scorecard.mandate_statuses
            if ms.status in ("non_compliant", "partial")
        )
        if failing > 3:
            return "high"
        if failing >= 1:
            return "moderate"
        return "low"

    def _generate_recommendations(self, scorecard: ComplianceScorecard) -> list[str]:
        """Generate actionable recommendations for each non-compliant mandate."""
        recs: list[str] = []
        for ms in scorecard.mandate_statuses:
            if ms.status == "compliant":
                continue
            mandate = self.ccops.get_mandate(ms.mandate_id)
            if mandate is None:
                continue
            evidence_list = ", ".join(mandate.required_evidence)
            detectors_list = ", ".join(mandate.verification_detectors)
            if ms.status == "non_compliant":
                recs.append(
                    f"[{mandate.mandate_id}] {mandate.title}: Resolve "
                    f"{len(ms.violations)} violation(s) detected by "
                    f"{detectors_list}. "
                    f"Required evidence: {evidence_list}."
                )
            elif ms.status == "partial":
                recs.append(
                    f"[{mandate.mandate_id}] {mandate.title}: Partial — "
                    f"complete verification with: {detectors_list}. "
                    f"Required evidence: {evidence_list}."
                )
            else:  # unknown
                recs.append(
                    f"[{mandate.mandate_id}] {mandate.title}: Status unknown — "
                    f"run detector(s): {detectors_list}. "
                    f"Required evidence: {evidence_list}."
                )
        return recs

    def generate_scorecard_markdown(self, scorecard: ComplianceScorecard) -> str:
        """Render the scorecard as a formatted Markdown document."""
        lines: list[str] = []

        lines.append(f"# CCOPS Compliance Scorecard: {scorecard.jurisdiction}")
        lines.append("")
        lines.append(f"**Assessment Date**: {scorecard.assessment_date}  ")
        has_ord = "Yes" if scorecard.has_ccops_ordinance else "No"
        lines.append(f"**CCOPS Ordinance Adopted**: {has_ord}  ")
        lines.append(f"**Overall Risk**: {scorecard.overall_risk.upper()}")
        lines.append("")

        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Mandates | {scorecard.total_mandates} |")
        lines.append(f"| Compliant | {scorecard.compliant_count} |")
        lines.append(f"| Non-Compliant | {scorecard.non_compliant_count} |")
        lines.append(f"| Partial | {scorecard.partial_count} |")
        lines.append(f"| Unknown | {scorecard.unknown_count} |")
        lines.append(
            f"| **Compliance Score** | **{scorecard.compliance_percentage:.1f}%** |"
        )
        lines.append("")

        lines.append("## Mandate Status")
        lines.append("")
        lines.append("| Mandate | Title | Status | Severity |")
        lines.append("|---------|-------|--------|----------|")
        for ms in scorecard.mandate_statuses:
            symbol = _STATUS_SYMBOL.get(ms.status, ms.status.upper())
            lines.append(
                f"| {ms.mandate_id} | {ms.mandate_title} | {symbol} | {ms.severity} |"
            )
        lines.append("")

        if scorecard.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(scorecard.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        if scorecard.technology_inventory:
            lines.append("## Technology Inventory")
            lines.append("")
            lines.append("| Agency | Technology | Vendor | Year |")
            lines.append("|--------|------------|--------|------|")
            for item in scorecard.technology_inventory:
                vendor = item.get("vendor") or "\u2014"
                year = item.get("year_identified") or "\u2014"
                lines.append(
                    f"| {item.get('agency_name', '')} "
                    f"| {item.get('technology_type', '')} "
                    f"| {vendor} "
                    f"| {year} |"
                )
            lines.append("")

        return "\n".join(lines)
