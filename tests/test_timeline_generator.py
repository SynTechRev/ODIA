"""Tests for TimelineGenerator."""

from __future__ import annotations

from oraculus_di_auditor.temporal.evolution_detector import EvolutionPattern
from oraculus_di_auditor.temporal.models import ContractEvent, ContractLineage
from oraculus_di_auditor.temporal.timeline_generator import TimelineGenerator

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event(
    idx: int,
    event_type: str = "original",
    date: str = "2020-01-01",
    amount: float = 100_000.0,
    cumulative: float | None = None,
    anomalies: list[str] | None = None,
    auth_type: str | None = None,
    description: str = "",
) -> ContractEvent:
    return ContractEvent(
        event_id=f"e{idx:03d}",
        event_type=event_type,
        date=date,
        description=description or event_type,
        dollar_amount=amount,
        cumulative_amount=cumulative if cumulative is not None else amount,
        authorization_type=auth_type,
        anomalies=anomalies or [],
    )


def _lineage(
    vendor: str,
    events: list[ContractEvent],
    program: str | None = None,
    lineage_id: str | None = None,
) -> ContractLineage:
    original_amount = (
        next((e.dollar_amount for e in events if e.event_type == "original"), 0.0)
        or 0.0
    )
    current_amount = max(
        (e.cumulative_amount for e in events if e.cumulative_amount), default=0.0
    )
    return ContractLineage(
        lineage_id=lineage_id or f"lid_{vendor.lower()[:8]}",
        vendor=vendor,
        program=program,
        original_amount=original_amount,
        current_amount=current_amount,
        total_authorized=current_amount,
        events=events,
    )


def _simple_lineage(
    vendor: str = "SecureTech", program: str | None = None
) -> ContractLineage:
    events = [
        _event(1, "original", "2019-06-01", 200_000.0, 200_000.0),
        _event(2, "amendment", "2021-03-15", 500_000.0, 700_000.0),
        _event(3, "renewal", "2023-09-01", 300_000.0, 1_000_000.0),
    ]
    return _lineage(vendor, events, program=program)


# ---------------------------------------------------------------------------
# Test: JSON structure
# ---------------------------------------------------------------------------


def test_timeline_json_has_correct_top_level_keys():
    gen = TimelineGenerator([_simple_lineage()])
    result = gen.generate_timeline_json()
    for key in (
        "timeline_id",
        "generated_at",
        "date_range",
        "tracks",
        "patterns",
        "milestones",
    ):
        assert key in result, f"Missing key: {key}"


def test_timeline_json_track_structure():
    gen = TimelineGenerator([_simple_lineage("Axon", program="BWC")])
    tracks = gen.generate_timeline_json()["tracks"]
    assert len(tracks) == 1
    track = tracks[0]
    for key in ("track_id", "vendor", "program", "events", "metrics"):
        assert key in track
    assert track["vendor"] == "Axon"
    assert track["program"] == "BWC"
    metrics = track["metrics"]
    for key in ("total_amount", "growth", "amendments", "risk_score"):
        assert key in metrics


def test_timeline_json_event_structure():
    gen = TimelineGenerator([_simple_lineage()])
    events = gen.generate_timeline_json()["tracks"][0]["events"]
    assert len(events) == 3
    for e in events:
        for key in (
            "date",
            "type",
            "label",
            "amount",
            "cumulative",
            "severity",
            "has_anomaly",
        ):
            assert key in e


def test_events_chronologically_ordered():
    events = [
        _event(3, "renewal", "2023-09-01", 300_000.0, 1_000_000.0),
        _event(1, "original", "2019-06-01", 200_000.0, 200_000.0),
        _event(2, "amendment", "2021-03-15", 500_000.0, 700_000.0),
    ]
    lineage = _lineage("Axon", events)
    gen = TimelineGenerator([lineage])
    track_events = gen.generate_timeline_json()["tracks"][0]["events"]
    dates = [e["date"] for e in track_events]
    assert dates == sorted(dates)


def test_patterns_included_in_json():
    pattern = EvolutionPattern(
        pattern_id="abc123",
        pattern_type="scope_creep",
        severity="high",
        description="Contract grew 400%",
        lineage_ids=["lid_axon"],
        vendors=["Axon"],
        date_range={"start": "2019-01-01", "end": "2023-01-01"},
    )
    gen = TimelineGenerator([_simple_lineage()], patterns=[pattern])
    patterns_out = gen.generate_timeline_json()["patterns"]
    assert len(patterns_out) == 1
    assert patterns_out[0]["pattern_type"] == "scope_creep"
    assert patterns_out[0]["severity"] == "high"
    assert "affected_tracks" in patterns_out[0]


def test_milestones_extracted_from_significant_events():
    events = [
        _event(1, "original", "2019-06-01", 200_000.0, 200_000.0),
        _event(
            2,
            "amendment",
            "2021-03-15",
            800_000.0,
            1_000_000.0,
            anomalies=["fiscal:missing-hash"],
        ),
    ]
    lineage = _lineage("Axon", events)
    gen = TimelineGenerator([lineage])
    milestones = gen.generate_timeline_json()["milestones"]
    assert len(milestones) >= 1
    # Original contract should be a milestone
    types = {m["significance"] for m in milestones}
    assert "contract_start" in types


# ---------------------------------------------------------------------------
# Test: Markdown output
# ---------------------------------------------------------------------------


def test_markdown_contains_table_formatting():
    gen = TimelineGenerator([_simple_lineage("Axon", program="BWC")])
    md = gen.generate_timeline_markdown()
    assert "## Contract Evolution Timeline" in md
    assert "### Axon — BWC" in md
    assert "| Date |" in md
    assert "|------|" in md
    assert "Growth:" in md


def test_markdown_contains_pattern_section_when_patterns_present():
    pattern = EvolutionPattern(
        pattern_id="abc123",
        pattern_type="vendor_lock_in",
        severity="critical",
        description="Axon sole-source for 8 years",
        lineage_ids=["lid_axon"],
        vendors=["Axon"],
        date_range={"start": "2016-01-01", "end": "2024-01-01"},
    )
    gen = TimelineGenerator([_simple_lineage()], patterns=[pattern])
    md = gen.generate_timeline_markdown()
    assert "### Detected Patterns" in md
    assert (
        "VENDOR LOCK IN" in md or "VENDOR_LOCK_IN" in md or "vendor lock" in md.lower()
    )


# ---------------------------------------------------------------------------
# Test: Snapshots
# ---------------------------------------------------------------------------


def test_snapshots_generated_at_yearly_intervals():
    gen = TimelineGenerator([_simple_lineage()])
    snapshots = gen.generate_snapshots(interval="yearly")
    # Events span 2019–2023 → expect snapshots at 2019, 2020, 2021, 2022, 2023
    assert len(snapshots) >= 3
    dates = [s.snapshot_date for s in snapshots]
    assert dates == sorted(dates)
    # All snapshot dates should be Jan 1 (yearly)
    for d in dates:
        assert d.endswith("-01-01")


def test_snapshots_reflect_active_contracts():
    gen = TimelineGenerator([_simple_lineage()])
    snapshots = gen.generate_snapshots(interval="yearly")
    # Before 2019-06-01 there should be 0 active contracts
    before = [s for s in snapshots if s.snapshot_date < "2019-06-01"]
    if before:
        assert before[-1].active_contracts == 0
    # After 2019-06-01 there should be 1 active contract
    after = [s for s in snapshots if s.snapshot_date >= "2019-06-01"]
    assert any(s.active_contracts == 1 for s in after)


# ---------------------------------------------------------------------------
# Test: Growth chart data
# ---------------------------------------------------------------------------


def test_growth_chart_data_has_series_per_vendor():
    lineage_a = _simple_lineage("Axon", program="BWC")
    lineage_b = _simple_lineage("Flock", program="ALPR")
    gen = TimelineGenerator([lineage_a, lineage_b])
    chart = gen.generate_growth_chart_data()
    assert "series" in chart
    assert "total" in chart
    assert chart["x_axis"] == "date"
    vendors = {s["vendor"] for s in chart["series"]}
    assert {"Axon", "Flock"} == vendors


def test_growth_chart_data_points_chronological():
    gen = TimelineGenerator([_simple_lineage()])
    chart = gen.generate_growth_chart_data()
    series = chart["series"][0]["data"]
    dates = [p["date"] for p in series]
    assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------


def test_empty_lineages_produce_valid_empty_timeline():
    gen = TimelineGenerator([])
    result = gen.generate_timeline_json()
    assert result["tracks"] == []
    assert result["patterns"] == []
    assert result["milestones"] == []
    assert result["date_range"] == {"start": "", "end": ""}


def test_single_lineage_produces_valid_timeline():
    gen = TimelineGenerator([_simple_lineage()])
    result = gen.generate_timeline_json()
    assert len(result["tracks"]) == 1
    assert len(result["tracks"][0]["events"]) == 3
