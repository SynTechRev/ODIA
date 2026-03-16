"""CCOPS compliance framework adapter.

Encodes the ACLU Community Control Over Police Surveillance (CCOPS) model
bill's 11 mandates as structured reference data that ODIA can evaluate
against. All mandate data is public information from the ACLU model bill.

Reference: https://www.aclu.org/legal-document/community-control-over-police-surveillance-ccops-model-bill
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from oraculus_di_auditor.adapters.base import DataSourceAdapter


class CCOPSMandate(BaseModel):
    """A single CCOPS model bill mandate."""

    mandate_id: str
    title: str
    description: str
    required_evidence: list[str]
    verification_detectors: list[str]
    severity_if_missing: str


class CCOPSProfile(BaseModel):
    """CCOPS compliance profile for a jurisdiction."""

    jurisdiction: str
    has_ordinance: bool = False
    adoption_date: str | None = None
    mandates: list[CCOPSMandate]
    ordinance_url: str | None = None


class CCOPSAdapter(DataSourceAdapter):
    """CCOPS compliance framework adapter.

    Provides the 11 CCOPS model bill mandates as structured data and
    maps them to ODIA detectors for automated compliance verification.
    """

    MANDATES: list[CCOPSMandate] = [
        CCOPSMandate(
            mandate_id="M-01",
            title="City Council Approval Required",
            description=(
                "Elected body must approve acquisition of surveillance technology "
                "before purchase or deployment."
            ),
            required_evidence=[
                "council_resolution",
                "vote_record",
                "authorization_date",
            ],
            verification_detectors=["procurement_timeline"],
            severity_if_missing="critical",
        ),
        CCOPSMandate(
            mandate_id="M-02",
            title="Surveillance Impact Report",
            description=(
                "Agency must prepare and publish a Surveillance Impact Report (SIR) "
                "describing the technology, its purpose, data collection scope, civil "
                "liberties impact, and fiscal cost."
            ),
            required_evidence=["surveillance_impact_report", "public_filing"],
            verification_detectors=["governance_gap"],
            severity_if_missing="critical",
        ),
        CCOPSMandate(
            mandate_id="M-03",
            title="Public Hearing Required",
            description=(
                "A public hearing must be held before acquisition where community "
                "members can provide input."
            ),
            required_evidence=[
                "public_hearing_notice",
                "hearing_minutes",
                "public_comment_record",
            ],
            verification_detectors=["procurement_timeline", "administrative_integrity"],
            severity_if_missing="critical",
        ),
        CCOPSMandate(
            mandate_id="M-04",
            title="Use Policy Required",
            description=(
                "A written use policy governing how the technology may and may not be "
                "used must be adopted."
            ),
            required_evidence=[
                "use_policy",
                "department_policy",
                "operating_procedures",
            ],
            verification_detectors=["governance_gap"],
            severity_if_missing="high",
        ),
        CCOPSMandate(
            mandate_id="M-05",
            title="Data Retention Limits",
            description=(
                "Policy must specify how long data is retained and procedures for "
                "deletion."
            ),
            required_evidence=["retention_policy", "deletion_schedule"],
            verification_detectors=["governance_gap"],
            severity_if_missing="high",
        ),
        CCOPSMandate(
            mandate_id="M-06",
            title="Data Sharing Restrictions",
            description=(
                "Policy must restrict sharing of surveillance data with other agencies "
                "and define authorization requirements."
            ),
            required_evidence=[
                "data_sharing_agreement",
                "MOU",
                "access_controls",
            ],
            verification_detectors=["surveillance", "governance_gap"],
            severity_if_missing="high",
        ),
        CCOPSMandate(
            mandate_id="M-07",
            title="Annual Audit Report",
            description=(
                "Agency must publish annual report on surveillance technology use "
                "including statistics, complaints, and policy compliance."
            ),
            required_evidence=["annual_report", "audit_report", "compliance_report"],
            verification_detectors=["administrative_integrity"],
            severity_if_missing="high",
        ),
        CCOPSMandate(
            mandate_id="M-08",
            title="Community Oversight Body",
            description=(
                "An independent oversight body or committee must be established to "
                "monitor surveillance technology use."
            ),
            required_evidence=[
                "oversight_committee",
                "advisory_board",
                "civilian_review",
            ],
            verification_detectors=["governance_gap"],
            severity_if_missing="medium",
        ),
        CCOPSMandate(
            mandate_id="M-09",
            title="Vendor Contract Transparency",
            description=(
                "Contracts with surveillance technology vendors must be publicly "
                "available and include terms governing data access."
            ),
            required_evidence=[
                "executed_contract",
                "public_contract",
                "vendor_agreement",
            ],
            verification_detectors=["signature_chain", "governance_gap"],
            severity_if_missing="high",
        ),
        CCOPSMandate(
            mandate_id="M-10",
            title="Funding Source Disclosure",
            description=(
                "All funding sources for surveillance technology must be publicly "
                "disclosed including grants, donations, and third-party funding."
            ),
            required_evidence=[
                "funding_disclosure",
                "grant_documentation",
                "budget_authorization",
            ],
            verification_detectors=["fiscal"],
            severity_if_missing="medium",
        ),
        CCOPSMandate(
            mandate_id="M-11",
            title="Penalty for Non-Compliance",
            description=(
                "The ordinance must include enforcement mechanisms for non-compliance "
                "including technology moratorium or removal."
            ),
            required_evidence=[
                "enforcement_clause",
                "penalty_provision",
                "compliance_mechanism",
            ],
            verification_detectors=["administrative_integrity"],
            severity_if_missing="medium",
        ),
    ]

    def __init__(self, cache_dir: Path | str = "cache/adapters"):
        super().__init__("ccops", cache_dir)

    def fetch(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        """Return CCOPS mandates. Query can filter by mandate_id or severity."""
        mandates = list(self.MANDATES)
        if "mandate_id" in query:
            mandates = [m for m in mandates if m.mandate_id == query["mandate_id"]]
        if "severity" in query:
            mandates = [
                m for m in mandates if m.severity_if_missing == query["severity"]
            ]
        return [m.model_dump() for m in mandates]

    def normalize(self, raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Already normalized — pass through."""
        return raw_records

    def get_all_mandates(self) -> list[CCOPSMandate]:
        """Return all 11 CCOPS mandates."""
        return list(self.MANDATES)

    def get_mandate(self, mandate_id: str) -> CCOPSMandate | None:
        """Get a specific mandate by ID."""
        for m in self.MANDATES:
            if m.mandate_id == mandate_id:
                return m
        return None

    def get_profile(
        self,
        jurisdiction: str,
        has_ordinance: bool = False,
        adoption_date: str | None = None,
    ) -> CCOPSProfile:
        """Create a CCOPS compliance profile for a jurisdiction."""
        return CCOPSProfile(
            jurisdiction=jurisdiction,
            has_ordinance=has_ordinance,
            adoption_date=adoption_date,
            mandates=list(self.MANDATES),
        )

    def get_detectors_for_mandate(self, mandate_id: str) -> list[str]:
        """Return which ODIA detectors verify a specific mandate."""
        mandate = self.get_mandate(mandate_id)
        return mandate.verification_detectors if mandate else []

    def get_mandates_for_detector(self, detector_name: str) -> list[CCOPSMandate]:
        """Return which mandates a specific detector can verify."""
        return [m for m in self.MANDATES if detector_name in m.verification_detectors]
