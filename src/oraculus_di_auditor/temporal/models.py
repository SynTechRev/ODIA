"""Temporal contract lineage models.

Defines data structures for tracking how a contract or vendor relationship
evolves over time — original award, amendments, renewals, scope expansions —
and detecting patterns that only become visible across the full arc.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel, Field, model_validator


class ContractEvent(BaseModel):
    """A single event in a contract's lifecycle."""

    event_id: str
    event_type: str  # "original", "amendment", "renewal", "expansion",
    # "quote", "purchase_order", "authorization",
    # "execution", "payment", "termination"
    date: str  # ISO date (YYYY-MM-DD)
    document_id: str | None = None
    description: str
    dollar_amount: float | None = None
    cumulative_amount: float | None = None  # Running total at this point
    vendor: str | None = None
    authorization_type: str | None = None  # "council_vote", "consent_calendar",
    # "sole_source", "competitive_bid", "none"
    signatures: dict[str, str] = Field(default_factory=dict)  # role -> status
    anomalies: list[str] = Field(default_factory=list)  # Anomaly IDs
    metadata: dict[str, Any] = Field(default_factory=dict)

    VALID_EVENT_TYPES: ClassVar[frozenset[str]] = frozenset(
        {
            "original",
            "amendment",
            "renewal",
            "expansion",
            "quote",
            "purchase_order",
            "authorization",
            "execution",
            "payment",
            "termination",
        }
    )

    VALID_AUTH_TYPES: ClassVar[frozenset[str]] = frozenset(
        {
            "council_vote",
            "consent_calendar",
            "sole_source",
            "competitive_bid",
            "none",
        }
    )


class ContractLineage(BaseModel):
    """Complete lifecycle of a contract/vendor relationship."""

    lineage_id: str  # SHA-256 hash
    vendor: str
    jurisdiction: str | None = None
    program: str | None = None  # "BWC", "ALPR", "5G Infrastructure", etc.
    original_date: str | None = None
    latest_date: str | None = None
    span_years: float = 0.0
    events: list[ContractEvent] = Field(default_factory=list)
    total_authorized: float = 0.0
    total_spent: float = 0.0
    original_amount: float = 0.0
    current_amount: float = 0.0
    growth_percentage: float = 0.0  # (current - original) / original * 100
    amendment_count: int = 0
    procurement_methods: list[str] = Field(default_factory=list)  # Unique methods
    unsigned_instruments: int = 0
    pre_authorization_events: int = 0
    anomaly_count: int = 0
    risk_score: float = 0.0

    @model_validator(mode="after")
    def compute_derived_fields(self) -> ContractLineage:
        """Compute growth_percentage and amendment_count from events if not set."""
        if self.events:
            # Amendment count
            if self.amendment_count == 0:
                self.amendment_count = sum(
                    1 for e in self.events if e.event_type == "amendment"
                )

            # Growth percentage
            if self.growth_percentage == 0.0 and self.original_amount > 0:
                self.growth_percentage = (
                    (self.current_amount - self.original_amount)
                    / self.original_amount
                    * 100
                )

            # Date span
            dates = sorted(
                e.date for e in self.events if e.date and e.date != "unknown"
            )
            if dates and not self.original_date:
                self.original_date = dates[0]
            if dates and not self.latest_date:
                self.latest_date = dates[-1]
            if self.span_years == 0.0 and len(dates) >= 2:
                self.span_years = self._compute_span_years(dates[0], dates[-1])

            # Anomaly count
            if self.anomaly_count == 0:
                all_anomalies: set[str] = set()
                for e in self.events:
                    all_anomalies.update(e.anomalies)
                self.anomaly_count = len(all_anomalies)

            # Procurement methods
            if not self.procurement_methods:
                methods = {
                    e.authorization_type
                    for e in self.events
                    if e.authorization_type and e.authorization_type != "none"
                }
                self.procurement_methods = sorted(methods)

        return self

    @staticmethod
    def _compute_span_years(start: str, end: str) -> float:
        try:
            d0 = datetime.fromisoformat(start)
            d1 = datetime.fromisoformat(end)
            return round((d1 - d0).days / 365.25, 2)
        except ValueError:
            return 0.0

    @classmethod
    def make_lineage_id(
        cls, vendor: str, jurisdiction: str | None, program: str | None
    ) -> str:
        """Generate a stable SHA-256 lineage ID from key fields."""
        payload = json.dumps(
            {"vendor": vendor, "jurisdiction": jurisdiction, "program": program},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:24]


class TemporalSnapshot(BaseModel):
    """State of all contracts at a specific point in time."""

    snapshot_date: str
    jurisdiction: str | None = None
    active_contracts: int = 0
    total_committed: float = 0.0
    vendors: list[str] = Field(default_factory=list)
    technology_types: list[str] = Field(default_factory=list)
    open_anomalies: int = 0


class EvolutionTimeline(BaseModel):
    """Complete temporal view of a jurisdiction's procurement history."""

    timeline_id: str
    jurisdiction: str | None = None
    date_range: dict[str, str] = Field(default_factory=dict)  # {earliest, latest}
    lineages: list[ContractLineage] = Field(default_factory=list)
    snapshots: list[TemporalSnapshot] = Field(default_factory=list)
    total_lineages: int = 0
    total_events: int = 0
    total_spend: float = 0.0
    growth_patterns: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def aggregate_from_lineages(self) -> EvolutionTimeline:
        """Compute totals from lineages when not explicitly set."""
        if self.lineages:
            if self.total_lineages == 0:
                self.total_lineages = len(self.lineages)
            if self.total_events == 0:
                self.total_events = sum(len(ln.events) for ln in self.lineages)
            if self.total_spend == 0.0:
                self.total_spend = sum(ln.total_authorized for ln in self.lineages)

            # Date range
            if not self.date_range:
                all_dates = []
                for ln in self.lineages:
                    if ln.original_date:
                        all_dates.append(ln.original_date)
                    if ln.latest_date:
                        all_dates.append(ln.latest_date)
                if all_dates:
                    self.date_range = {
                        "earliest": min(all_dates),
                        "latest": max(all_dates),
                    }

        return self
