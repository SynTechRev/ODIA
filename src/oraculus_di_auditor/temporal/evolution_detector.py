"""Evolution pattern detector for contract lineage temporal analysis.

Detects patterns that only become visible when examining the full arc of
a vendor relationship — scope creep, vendor lock-in, capability embedding,
authorization erosion, payment acceleration, and parallel expansion.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, Field

from oraculus_di_auditor.temporal.models import ContractLineage

# ---------------------------------------------------------------------------
# Technology capability keywords for capability-embedding detection
# ---------------------------------------------------------------------------

_CAPABILITY_KEYWORDS: list[str] = [
    "alpr",
    "license plate",
    "facial recognition",
    "face recognition",
    "drone",
    "unmanned aerial",
    "uav",
    "fusus",
    "real-time video",
    "real time video",
    "predictive policing",
    "shot spotter",
    "shotspotter",
    "virtual reality",
    "vr training",
    "body camera",
    "body-worn camera",
    "bwc",
    "ai report",
    "automated report",
    "gunshot detection",
    "social media monitoring",
    "stingray",
    "cell-site simulator",
    "imsi catcher",
]


# ---------------------------------------------------------------------------
# EvolutionPattern model
# ---------------------------------------------------------------------------


class EvolutionPattern(BaseModel):
    """A detected temporal evolution pattern across contract lineages."""

    pattern_id: str
    # pattern_type values: scope_creep | vendor_lock_in | capability_embedding
    #   | authorization_erosion | payment_acceleration | parallel_expansion
    pattern_type: str
    severity: str  # critical | high | medium
    description: str
    lineage_ids: list[str] = Field(default_factory=list)
    vendors: list[str] = Field(default_factory=list)
    date_range: dict[str, str] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    recommendation: str = ""


# ---------------------------------------------------------------------------
# EvolutionPatternDetector
# ---------------------------------------------------------------------------


class EvolutionPatternDetector:
    """Detects temporal evolution patterns in contract lineages."""

    def __init__(self, lineages: list[ContractLineage]) -> None:
        self.lineages = lineages

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def detect_all_patterns(self) -> list[EvolutionPattern]:
        """Run all pattern detectors and return combined results."""
        patterns: list[EvolutionPattern] = []
        patterns.extend(self.detect_scope_creep())
        patterns.extend(self.detect_vendor_lock_in())
        patterns.extend(self.detect_capability_embedding())
        patterns.extend(self.detect_authorization_erosion())
        patterns.extend(self.detect_payment_acceleration())
        patterns.extend(self.detect_parallel_vendor_expansion())
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Scope Creep
    # ------------------------------------------------------------------

    def detect_scope_creep(self) -> list[EvolutionPattern]:
        """Detect gradual scope expansion via successive amendments.

        Threshold: total amount exceeds original by >200% AND 3+ amendments.
        """
        patterns: list[EvolutionPattern] = []
        for lineage in self.lineages:
            if lineage.amendment_count < 3:
                continue
            if lineage.original_amount <= 0:
                continue
            if lineage.growth_percentage <= 200.0:
                continue

            severity = "critical" if lineage.growth_percentage > 400 else "high"
            evidence = [
                {
                    "event_id": e.event_id,
                    "event_type": e.event_type,
                    "date": e.date,
                    "dollar_amount": e.dollar_amount,
                    "cumulative_amount": e.cumulative_amount,
                }
                for e in lineage.events
                if e.event_type in ("original", "amendment", "renewal")
            ]

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id("scope_creep", lineage.lineage_id),
                    pattern_type="scope_creep",
                    severity=severity,
                    description=(
                        f"{lineage.vendor}: contract grew "
                        f"{lineage.growth_percentage:.0f}% "
                        f"from ${lineage.original_amount:,.0f} to "
                        f"${lineage.current_amount:,.0f} across "
                        f"{lineage.amendment_count} amendments"
                    ),
                    lineage_ids=[lineage.lineage_id],
                    vendors=[lineage.vendor],
                    date_range=_date_range(lineage),
                    evidence=evidence,
                    metrics={
                        "growth_percentage": lineage.growth_percentage,
                        "original_amount": lineage.original_amount,
                        "current_amount": lineage.current_amount,
                        "amendment_count": lineage.amendment_count,
                        "span_years": lineage.span_years,
                    },
                    recommendation=(
                        "Conduct independent review of all amendments. "
                        "Determine whether scope expansions required separate "
                        "competitive procurement under applicable purchasing rules."
                    ),
                )
            )
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Vendor Lock-In
    # ------------------------------------------------------------------

    def detect_vendor_lock_in(self) -> list[EvolutionPattern]:
        """Detect sustained sole-source procurement over 3+ years with no competition.

        Threshold: 3+ contract events, span 3+ years, no competitive_bid at any stage.
        """
        patterns: list[EvolutionPattern] = []
        for lineage in self.lineages:
            if len(lineage.events) < 3:
                continue
            if lineage.span_years < 3.0:
                continue
            if "competitive_bid" in lineage.procurement_methods:
                continue

            sole_source_count = sum(
                1 for e in lineage.events if e.authorization_type == "sole_source"
            )
            total_events = len(lineage.events)
            sole_source_pct = (
                sole_source_count / total_events * 100 if total_events else 0
            )

            severity = "critical" if lineage.span_years >= 7 else "high"

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id("vendor_lock_in", lineage.lineage_id),
                    pattern_type="vendor_lock_in",
                    severity=severity,
                    description=(
                        f"{lineage.vendor}: {total_events} contract events over "
                        f"{lineage.span_years:.1f} years with no competitive bidding "
                        f"({sole_source_pct:.0f}% sole-source)"
                    ),
                    lineage_ids=[lineage.lineage_id],
                    vendors=[lineage.vendor],
                    date_range=_date_range(lineage),
                    evidence=[
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "date": e.date,
                            "authorization_type": e.authorization_type,
                        }
                        for e in lineage.events
                    ],
                    metrics={
                        "span_years": lineage.span_years,
                        "total_events": total_events,
                        "sole_source_count": sole_source_count,
                        "sole_source_percentage": round(sole_source_pct, 1),
                        "procurement_methods": lineage.procurement_methods,
                    },
                    recommendation=(
                        "Initiate competitive procurement process. "
                        "Document justification for all sole-source awards. "
                        "Review compliance with procurement code requirements for "
                        "competitive bidding above applicable thresholds."
                    ),
                )
            )
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Capability Embedding
    # ------------------------------------------------------------------

    def detect_capability_embedding(self) -> list[EvolutionPattern]:
        """Detect new technology capabilities added inside existing contracts.

        Looks for technology keywords appearing in amendments/renewals that
        were absent from the original contract events.
        """
        patterns: list[EvolutionPattern] = []
        for lineage in self.lineages:
            original_events = [e for e in lineage.events if e.event_type == "original"]
            later_events = [
                e
                for e in lineage.events
                if e.event_type in ("amendment", "renewal", "expansion")
            ]
            if not original_events or not later_events:
                continue

            original_caps = _extract_capabilities(original_events)
            later_caps = _extract_capabilities(later_events)
            new_caps = later_caps - original_caps

            if not new_caps:
                continue

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id("capability_embedding", lineage.lineage_id),
                    pattern_type="capability_embedding",
                    severity="high",
                    description=(
                        f"{lineage.vendor}: {len(new_caps)} new capability type(s) "
                        f"added via amendments without separate authorization: "
                        f"{', '.join(sorted(new_caps))}"
                    ),
                    lineage_ids=[lineage.lineage_id],
                    vendors=[lineage.vendor],
                    date_range=_date_range(lineage),
                    evidence=[
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "date": e.date,
                            "detected_capabilities": sorted(_extract_capabilities([e])),
                        }
                        for e in later_events
                        if _extract_capabilities([e]) - original_caps
                    ],
                    metrics={
                        "original_capabilities": sorted(original_caps),
                        "new_capabilities": sorted(new_caps),
                        "new_capability_count": len(new_caps),
                    },
                    recommendation=(
                        "Each new surveillance technology requires independent "
                        "public authorization. Review whether these capabilities "
                        "required separate council approval or CCOPS-compliant "
                        "surveillance impact assessment."
                    ),
                )
            )
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Authorization Erosion
    # ------------------------------------------------------------------

    def detect_authorization_erosion(self) -> list[EvolutionPattern]:
        """Detect declining authorization rigor over time.

        Pattern: Early events have council_vote authorization; later events
        shift to consent_calendar, none, or no authorization type recorded.
        """
        patterns: list[EvolutionPattern] = []
        for lineage in self.lineages:
            dated = [e for e in lineage.events if e.date != "unknown"]
            if len(dated) < 2:
                continue

            # Split into first-half and second-half by date order
            mid = len(dated) // 2
            early = dated[:mid]
            late = dated[mid:]

            early_council = sum(
                1 for e in early if e.authorization_type == "council_vote"
            )
            late_council = sum(
                1 for e in late if e.authorization_type == "council_vote"
            )
            late_weak = sum(
                1
                for e in late
                if e.authorization_type in ("consent_calendar", "none", None)
            )

            # Pattern: had council votes early, lost them later
            if early_council == 0:
                continue
            if late_weak == 0:
                continue

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id("authorization_erosion", lineage.lineage_id),
                    pattern_type="authorization_erosion",
                    severity="high",
                    description=(
                        f"{lineage.vendor}: authorization quality declined over time — "
                        f"{early_council} council vote(s) in early events, "
                        f"{late_council} in later events; "
                        f"{late_weak} later event(s) with weak/no authorization"
                    ),
                    lineage_ids=[lineage.lineage_id],
                    vendors=[lineage.vendor],
                    date_range=_date_range(lineage),
                    evidence=[
                        {
                            "event_id": e.event_id,
                            "event_type": e.event_type,
                            "date": e.date,
                            "authorization_type": e.authorization_type,
                            "period": "early" if e in early else "late",
                        }
                        for e in dated
                    ],
                    metrics={
                        "early_council_votes": early_council,
                        "late_council_votes": late_council,
                        "late_weak_authorizations": late_weak,
                    },
                    recommendation=(
                        "Restore full council authorization for all contract renewals "
                        "and amendments above the consent calendar threshold. "
                        "Review whether consent calendar placement was appropriate."
                    ),
                )
            )
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Payment Acceleration
    # ------------------------------------------------------------------

    def detect_payment_acceleration(self) -> list[EvolutionPattern]:
        """Detect year-over-year payment amounts increasing faster than expected.

        Pattern: 3+ events with dollar amounts, year-over-year growth >50%.
        """
        patterns: list[EvolutionPattern] = []
        for lineage in self.lineages:
            dated_with_amount = [
                e
                for e in lineage.events
                if e.date != "unknown" and e.dollar_amount and e.dollar_amount > 0
            ]
            if len(dated_with_amount) < 3:
                continue

            # Compute year-over-year growth rates
            yoy_rates: list[float] = []
            for i in range(1, len(dated_with_amount)):
                prev = dated_with_amount[i - 1].dollar_amount or 0
                curr = dated_with_amount[i].dollar_amount or 0
                if prev > 0:
                    yoy_rates.append((curr - prev) / prev * 100)

            if not yoy_rates:
                continue

            avg_growth = sum(yoy_rates) / len(yoy_rates)
            if avg_growth <= 50.0:
                continue

            severity = "critical" if avg_growth > 150 else "medium"

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id("payment_acceleration", lineage.lineage_id),
                    pattern_type="payment_acceleration",
                    severity=severity,
                    description=(
                        f"{lineage.vendor}: payment amounts accelerating at "
                        f"{avg_growth:.0f}% average year-over-year growth across "
                        f"{len(dated_with_amount)} events"
                    ),
                    lineage_ids=[lineage.lineage_id],
                    vendors=[lineage.vendor],
                    date_range=_date_range(lineage),
                    evidence=[
                        {
                            "event_id": e.event_id,
                            "date": e.date,
                            "dollar_amount": e.dollar_amount,
                        }
                        for e in dated_with_amount
                    ],
                    metrics={
                        "avg_yoy_growth_pct": round(avg_growth, 1),
                        "yoy_rates": [round(r, 1) for r in yoy_rates],
                        "event_count": len(dated_with_amount),
                    },
                    recommendation=(
                        "Review contract escalation clauses. "
                        "Confirm payment increases are within authorized terms. "
                        "Consider whether scope expansions are driving cost growth."
                    ),
                )
            )
        return patterns

    # ------------------------------------------------------------------
    # Pattern: Parallel Vendor Expansion
    # ------------------------------------------------------------------

    def detect_parallel_vendor_expansion(self) -> list[EvolutionPattern]:
        """Detect same vendor expanding across multiple simultaneous lineages.

        Pattern: Vendor A has 2+ growing lineages (growth >50%) with overlapping
        date ranges, suggesting coordinated vendor strategy.
        """
        from collections import defaultdict

        vendor_lineages: dict[str, list[ContractLineage]] = defaultdict(list)
        for lineage in self.lineages:
            vendor_lineages[lineage.vendor.lower()].append(lineage)

        patterns: list[EvolutionPattern] = []
        for _vendor_key, lins in vendor_lineages.items():
            # Need 2+ growing lineages
            growing = [
                ln for ln in lins if ln.growth_percentage > 50 and len(ln.events) >= 2
            ]
            if len(growing) < 2:
                continue

            # Check for overlapping date ranges
            overlapping = _find_overlapping_lineages(growing)
            if not overlapping:
                continue

            vendor_name = growing[0].vendor
            total_value = sum(ln.current_amount for ln in overlapping)
            all_dates = [
                d for ln in overlapping for d in (ln.original_date, ln.latest_date) if d
            ]

            patterns.append(
                EvolutionPattern(
                    pattern_id=_pattern_id(
                        "parallel_expansion",
                        "_".join(ln.lineage_id for ln in overlapping[:2]),
                    ),
                    pattern_type="parallel_expansion",
                    severity="high",
                    description=(
                        f"{vendor_name}: {len(overlapping)} simultaneously expanding "
                        f"contract lineages totalling ${total_value:,.0f}"
                    ),
                    lineage_ids=[ln.lineage_id for ln in overlapping],
                    vendors=[vendor_name],
                    date_range={
                        "start": min(all_dates) if all_dates else "",
                        "end": max(all_dates) if all_dates else "",
                    },
                    evidence=[
                        {
                            "lineage_id": ln.lineage_id,
                            "program": ln.program,
                            "original_date": ln.original_date,
                            "latest_date": ln.latest_date,
                            "growth_percentage": ln.growth_percentage,
                            "current_amount": ln.current_amount,
                        }
                        for ln in overlapping
                    ],
                    metrics={
                        "lineage_count": len(overlapping),
                        "total_value": total_value,
                        "growth_percentages": [
                            round(ln.growth_percentage, 1) for ln in overlapping
                        ],
                    },
                    recommendation=(
                        "Conduct aggregate vendor spend analysis. "
                        "Determine whether combined contract value triggers "
                        "formal competitive procurement requirements. "
                        "Review for potential contract splitting."
                    ),
                )
            )
        return patterns


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _pattern_id(pattern_type: str, key: str) -> str:
    """Generate a stable 16-char pattern ID."""
    raw = f"{pattern_type}:{key}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _date_range(lineage: ContractLineage) -> dict[str, str]:
    return {
        "start": lineage.original_date or "",
        "end": lineage.latest_date or "",
    }


def _extract_capabilities(events: list) -> set[str]:
    """Extract technology capability keywords from event metadata/description."""
    found: set[str] = set()
    for event in events:
        text_parts = [
            event.description or "",
            str(event.metadata.get("text", "")),
            str(event.metadata.get("title", "")),
            str(event.metadata.get("content", "")),
        ]
        combined = " ".join(text_parts).lower()
        for kw in _CAPABILITY_KEYWORDS:
            if kw in combined:
                found.add(kw)
    return found


def _find_overlapping_lineages(
    lineages: list[ContractLineage],
) -> list[ContractLineage]:
    """Return lineages whose date ranges overlap with at least one other."""
    overlapping: set[int] = set()
    for i, a in enumerate(lineages):
        if not a.original_date or not a.latest_date:
            continue
        for j, b in enumerate(lineages):
            if i >= j:
                continue
            if not b.original_date or not b.latest_date:
                continue
            # Overlap: a starts before b ends AND b starts before a ends
            if a.original_date <= b.latest_date and b.original_date <= a.latest_date:
                overlapping.add(i)
                overlapping.add(j)
    return [lineages[i] for i in sorted(overlapping)]
