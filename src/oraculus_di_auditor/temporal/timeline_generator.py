"""Timeline visualization data generator.

Generates structured timeline data for contract evolution visualisation —
JSON for the frontend dashboard and Markdown/text for reports.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Any

from oraculus_di_auditor.temporal.evolution_detector import EvolutionPattern
from oraculus_di_auditor.temporal.models import (
    ContractLineage,
    TemporalSnapshot,
)

# ---------------------------------------------------------------------------
# Severity flags for Markdown output
# ---------------------------------------------------------------------------

_SEVERITY_ICONS = {
    "critical": "[CRITICAL]",
    "high": "[HIGH]",
    "medium": "[MEDIUM]",
    "low": "[LOW]",
}

_AUTH_WARNINGS = {
    "sole_source": "Sole-source",
    "consent_calendar": "Consent calendar",
    "none": "No authorization",
}

# ---------------------------------------------------------------------------
# TimelineGenerator
# ---------------------------------------------------------------------------


class TimelineGenerator:
    """Generates timeline visualizations from contract lineages."""

    def __init__(
        self,
        lineages: list[ContractLineage],
        patterns: list[EvolutionPattern] | None = None,
    ) -> None:
        self.lineages = lineages
        self.patterns = patterns or []

    # ------------------------------------------------------------------
    # JSON timeline
    # ------------------------------------------------------------------

    def generate_timeline_json(self) -> dict[str, Any]:
        """Generate JSON structure for frontend timeline visualization."""
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        timeline_id = hashlib.sha256(
            (now + str(len(self.lineages))).encode()
        ).hexdigest()[:16]

        tracks = [self._lineage_to_track(ln) for ln in self.lineages]
        patterns_out = [self._pattern_to_json(p) for p in self.patterns]
        milestones = self._extract_milestones()
        date_range = self._overall_date_range()

        return {
            "timeline_id": timeline_id,
            "generated_at": now,
            "date_range": date_range,
            "tracks": tracks,
            "patterns": patterns_out,
            "milestones": milestones,
        }

    def _lineage_to_track(self, lineage: ContractLineage) -> dict[str, Any]:
        sorted_events = sorted(
            lineage.events, key=lambda e: (e.date == "unknown", e.date)
        )
        events_out = [
            {
                "date": e.date,
                "type": e.event_type,
                "label": e.description,
                "amount": e.dollar_amount,
                "cumulative": e.cumulative_amount,
                "severity": _event_severity(e),
                "has_anomaly": bool(e.anomalies),
                "authorization_type": e.authorization_type,
            }
            for e in sorted_events
        ]
        return {
            "track_id": lineage.lineage_id,
            "vendor": lineage.vendor,
            "program": lineage.program,
            "events": events_out,
            "metrics": {
                "total_amount": lineage.current_amount,
                "growth": lineage.growth_percentage,
                "amendments": lineage.amendment_count,
                "risk_score": lineage.risk_score,
            },
        }

    def _pattern_to_json(self, pattern: EvolutionPattern) -> dict[str, Any]:
        return {
            "pattern_type": pattern.pattern_type,
            "severity": pattern.severity,
            "description": pattern.description,
            "affected_tracks": pattern.lineage_ids,
            "date_range": pattern.date_range,
        }

    def _extract_milestones(self) -> list[dict[str, Any]]:
        """Extract significant events as milestones."""
        milestones: list[dict[str, Any]] = []
        for lineage in self.lineages:
            for event in lineage.events:
                if event.date == "unknown":
                    continue
                significance = _milestone_significance(event, lineage)
                if significance:
                    milestones.append(
                        {
                            "date": event.date,
                            "label": f"{lineage.vendor}: {event.description}",
                            "significance": significance,
                        }
                    )
        # Sort by date, dedup by label
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for m in sorted(milestones, key=lambda x: x["date"]):
            key = f"{m['date']}:{m['label']}"
            if key not in seen:
                seen.add(key)
                unique.append(m)
        return unique

    def _overall_date_range(self) -> dict[str, str]:
        all_dates = [
            d
            for ln in self.lineages
            for d in (ln.original_date, ln.latest_date)
            if d and d != "unknown"
        ]
        if not all_dates:
            return {"start": "", "end": ""}
        return {"start": min(all_dates), "end": max(all_dates)}

    # ------------------------------------------------------------------
    # Markdown timeline
    # ------------------------------------------------------------------

    def generate_timeline_markdown(self) -> str:
        lines: list[str] = ["## Contract Evolution Timeline", ""]

        for lineage in self.lineages:
            program = f" — {lineage.program}" if lineage.program else ""
            lines.append(f"### {lineage.vendor}{program}")
            lines.append("")
            lines.append("| Date | Event | Amount | Cumulative | Flags |")
            lines.append("|------|-------|--------|------------|-------|")

            sorted_events = sorted(
                lineage.events, key=lambda e: (e.date == "unknown", e.date)
            )
            for event in sorted_events:
                amt = f"${event.dollar_amount:,.0f}" if event.dollar_amount else "—"
                cum = (
                    f"${event.cumulative_amount:,.0f}"
                    if event.cumulative_amount
                    else "—"
                )
                flags = _event_flags(event)
                lines.append(
                    f"| {event.date} | {event.description} | {amt} | {cum} | {flags} |"
                )

            lines.append("")
            lines.append(
                f"Growth: {lineage.growth_percentage:.0f}% | "
                f"Amendments: {lineage.amendment_count} | "
                f"Risk Score: {lineage.risk_score:.2f}"
            )
            lines.append("")

        if self.patterns:
            lines.append("### Detected Patterns")
            lines.append("")
            for pattern in self.patterns:
                icon = _SEVERITY_ICONS.get(pattern.severity, "[?]")
                ptype = pattern.pattern_type.upper().replace("_", " ")
                lines.append(f"{icon} {ptype}: {pattern.description}")
            lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Periodic snapshots
    # ------------------------------------------------------------------

    def generate_snapshots(self, interval: str = "yearly") -> list[TemporalSnapshot]:
        """Generate periodic snapshots of procurement state."""
        all_dates = [
            d
            for ln in self.lineages
            for e in ln.events
            if (d := e.date) and d != "unknown"
        ]
        if not all_dates:
            return []

        snapshot_dates = _generate_interval_dates(
            min(all_dates), max(all_dates), interval
        )
        snapshots: list[TemporalSnapshot] = []
        for snap_date in snapshot_dates:
            snapshots.append(self._snapshot_at(snap_date))
        return snapshots

    def _snapshot_at(self, snap_date: str) -> TemporalSnapshot:
        """Compute procurement state as-of a given date."""
        active_contracts = 0
        total_committed = 0.0
        vendors: set[str] = set()
        open_anomalies = 0

        for lineage in self.lineages:
            # A lineage is active if it has events on or before snap_date
            active_events = [
                e for e in lineage.events if e.date != "unknown" and e.date <= snap_date
            ]
            if not active_events:
                continue

            active_contracts += 1
            vendors.add(lineage.vendor)
            # Use highest cumulative amount seen up to snap_date
            cums = [
                e.cumulative_amount
                for e in active_events
                if e.cumulative_amount is not None
            ]
            if cums:
                total_committed += max(cums)
            open_anomalies += sum(len(e.anomalies) for e in active_events)

        return TemporalSnapshot(
            snapshot_date=snap_date,
            active_contracts=active_contracts,
            total_committed=round(total_committed, 2),
            vendors=sorted(vendors),
            open_anomalies=open_anomalies,
        )

    # ------------------------------------------------------------------
    # Growth chart data
    # ------------------------------------------------------------------

    def generate_growth_chart_data(self) -> dict[str, Any]:
        """Generate data for a cumulative spending chart."""
        series: list[dict[str, Any]] = []
        all_points: dict[str, float] = {}

        for lineage in self.lineages:
            data_points: list[dict[str, Any]] = []
            for event in sorted(
                lineage.events, key=lambda e: (e.date == "unknown", e.date)
            ):
                if event.date == "unknown":
                    continue
                if event.cumulative_amount is not None:
                    point = {
                        "date": event.date,
                        "cumulative_amount": event.cumulative_amount,
                    }
                    data_points.append(point)
                    # Track totals by date
                    all_points[event.date] = (
                        all_points.get(event.date, 0) + event.cumulative_amount
                    )

            if data_points:
                series.append(
                    {
                        "vendor": lineage.vendor,
                        "program": lineage.program,
                        "data": data_points,
                    }
                )

        # Build total series
        total_series = [
            {"date": d, "cumulative_total": v} for d, v in sorted(all_points.items())
        ]

        return {
            "x_axis": "date",
            "series": series,
            "total": total_series,
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _event_severity(event: Any) -> str | None:
    if event.anomalies:
        return "high"
    if event.authorization_type in ("none", None) and event.event_type not in (
        "original",
    ):
        return "medium"
    return None


def _event_flags(event: Any) -> str:
    flags: list[str] = []
    if event.authorization_type in _AUTH_WARNINGS:
        flags.append(_AUTH_WARNINGS[event.authorization_type])
    if event.anomalies:
        flags.append(f"{len(event.anomalies)} anomaly(s)")
    return ", ".join(flags) if flags else ""


def _milestone_significance(event: Any, lineage: ContractLineage) -> str | None:
    """Return significance string for noteworthy events, else None."""
    if event.event_type == "original":
        return "contract_start"
    if event.event_type == "termination":
        return "contract_end"
    if event.anomalies:
        return "anomaly_detected"
    if event.authorization_type == "sole_source" and lineage.amendment_count > 2:
        return "repeated_sole_source"
    if (
        event.dollar_amount
        and lineage.original_amount > 0
        and event.cumulative_amount
        and event.cumulative_amount > lineage.original_amount * 3
    ):
        return "significant_growth"
    return None


def _generate_interval_dates(start: str, end: str, interval: str) -> list[str]:
    """Generate a list of dates at the given interval between start and end."""
    try:
        d_start = date.fromisoformat(start)
        d_end = date.fromisoformat(end)
    except ValueError:
        return []

    dates: list[str] = []
    current = d_start.replace(month=1, day=1)

    if interval == "yearly":
        while current <= d_end:
            dates.append(current.strftime("%Y-%m-%d"))
            current = current.replace(year=current.year + 1)
    elif interval == "quarterly":
        quarter_months = (1, 4, 7, 10)
        current = d_start.replace(month=1, day=1)
        while current <= d_end:
            for month in quarter_months:
                snap = current.replace(month=month, day=1)
                if d_start <= snap <= d_end:
                    dates.append(snap.strftime("%Y-%m-%d"))
            current = current.replace(year=current.year + 1)
    elif interval == "monthly":
        current = d_start.replace(day=1)
        while current <= d_end:
            dates.append(current.strftime("%Y-%m-%d"))
            month = current.month + 1
            year = current.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            current = current.replace(year=year, month=month, day=1)
    else:
        dates.append(start)

    return dates
