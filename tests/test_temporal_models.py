"""Tests for temporal contract lineage models."""

from __future__ import annotations

import json

import pytest

from oraculus_di_auditor.temporal import (
    ContractEvent,
    ContractLineage,
    EvolutionTimeline,
    TemporalSnapshot,
)

# ---------------------------------------------------------------------------
# ContractEvent
# ---------------------------------------------------------------------------


def test_contract_event_validates_correctly():
    event = ContractEvent(
        event_id="evt-001",
        event_type="original",
        date="2019-03-15",
        description="Original BWC contract",
        dollar_amount=200_000.0,
        vendor="SecureTech",
        authorization_type="council_vote",
    )
    assert event.event_id == "evt-001"
    assert event.event_type == "original"
    assert event.dollar_amount == 200_000.0
    assert event.vendor == "SecureTech"
    assert event.signatures == {}
    assert event.anomalies == []


def test_contract_event_defaults_are_empty():
    event = ContractEvent(
        event_id="evt-002",
        event_type="amendment",
        date="2021-06-01",
        description="Amendment 1",
    )
    assert event.signatures == {}
    assert event.anomalies == []
    assert event.metadata == {}
    assert event.dollar_amount is None
    assert event.document_id is None


def test_contract_event_with_signatures_and_anomalies():
    event = ContractEvent(
        event_id="evt-003",
        event_type="execution",
        date="2019-03-10",
        description="Executed before authorization",
        signatures={"city_manager": "signed", "city_council": "blank"},
        anomalies=["procurement:pre-authorization-execution"],
    )
    assert event.signatures["city_council"] == "blank"
    assert "procurement:pre-authorization-execution" in event.anomalies


# ---------------------------------------------------------------------------
# ContractLineage
# ---------------------------------------------------------------------------


def _make_lineage_with_events() -> ContractLineage:
    events = [
        ContractEvent(
            event_id="e1",
            event_type="original",
            date="2019-01-10",
            description="Original contract",
            dollar_amount=200_000.0,
            authorization_type="council_vote",
        ),
        ContractEvent(
            event_id="e2",
            event_type="amendment",
            date="2021-03-01",
            description="Amendment 1 — scope expansion",
            dollar_amount=5_000_000.0,
            authorization_type="sole_source",
        ),
        ContractEvent(
            event_id="e3",
            event_type="amendment",
            date="2023-07-15",
            description="Amendment 2 — ALPR add-on",
            dollar_amount=6_000_000.0,
            authorization_type="sole_source",
            anomalies=["fiscal:unsigned-contract"],
        ),
    ]
    return ContractLineage(
        lineage_id=ContractLineage.make_lineage_id("SecureTech", "Example City", "BWC"),
        vendor="SecureTech",
        jurisdiction="Example City",
        program="BWC",
        original_amount=200_000.0,
        current_amount=11_200_000.0,
        total_authorized=11_200_000.0,
        events=events,
    )


def test_contract_lineage_growth_percentage():
    lineage = _make_lineage_with_events()
    expected = (11_200_000.0 - 200_000.0) / 200_000.0 * 100
    assert abs(lineage.growth_percentage - expected) < 0.01


def test_contract_lineage_amendment_count():
    lineage = _make_lineage_with_events()
    assert lineage.amendment_count == 2


def test_contract_lineage_date_derivation():
    lineage = _make_lineage_with_events()
    assert lineage.original_date == "2019-01-10"
    assert lineage.latest_date == "2023-07-15"


def test_contract_lineage_procurement_methods():
    lineage = _make_lineage_with_events()
    assert "council_vote" in lineage.procurement_methods
    assert "sole_source" in lineage.procurement_methods


def test_contract_lineage_anomaly_count():
    lineage = _make_lineage_with_events()
    assert lineage.anomaly_count == 1  # one unique anomaly ID across all events


def test_contract_lineage_make_lineage_id_stable():
    id1 = ContractLineage.make_lineage_id("VendorA", "CityX", "BWC")
    id2 = ContractLineage.make_lineage_id("VendorA", "CityX", "BWC")
    assert id1 == id2
    assert len(id1) == 24


def test_contract_lineage_make_lineage_id_differs():
    id1 = ContractLineage.make_lineage_id("VendorA", "CityX", "BWC")
    id2 = ContractLineage.make_lineage_id("VendorB", "CityX", "BWC")
    assert id1 != id2


def test_contract_lineage_growth_zero_when_no_original():
    lineage = ContractLineage(
        lineage_id="abc123",
        vendor="VisionGuard",
        original_amount=0.0,
        current_amount=500_000.0,
    )
    # growth_percentage stays 0.0 when original_amount == 0 (avoid division by zero)
    assert lineage.growth_percentage == 0.0


# ---------------------------------------------------------------------------
# TemporalSnapshot
# ---------------------------------------------------------------------------


def test_temporal_snapshot_captures_point_in_time():
    snap = TemporalSnapshot(
        snapshot_date="2021-06-30",
        jurisdiction="Example City",
        active_contracts=3,
        total_committed=5_200_000.0,
        vendors=["SecureTech", "VisionGuard"],
        technology_types=["BWC", "ALPR"],
        open_anomalies=2,
    )
    assert snap.snapshot_date == "2021-06-30"
    assert snap.active_contracts == 3
    assert "BWC" in snap.technology_types
    assert snap.open_anomalies == 2


def test_temporal_snapshot_defaults():
    snap = TemporalSnapshot(snapshot_date="2020-01-01")
    assert snap.vendors == []
    assert snap.technology_types == []
    assert snap.active_contracts == 0


# ---------------------------------------------------------------------------
# EvolutionTimeline
# ---------------------------------------------------------------------------


def _make_timeline() -> EvolutionTimeline:
    lineage1 = _make_lineage_with_events()
    lineage2 = ContractLineage(
        lineage_id=ContractLineage.make_lineage_id(
            "VisionGuard", "Example City", "ALPR"
        ),
        vendor="VisionGuard",
        jurisdiction="Example City",
        program="ALPR",
        original_amount=150_000.0,
        current_amount=800_000.0,
        total_authorized=800_000.0,
        events=[
            ContractEvent(
                event_id="e10",
                event_type="original",
                date="2020-04-01",
                description="ALPR original",
                dollar_amount=150_000.0,
                authorization_type="council_vote",
            )
        ],
    )
    return EvolutionTimeline(
        timeline_id="tl-001",
        jurisdiction="Example City",
        lineages=[lineage1, lineage2],
    )


def test_evolution_timeline_aggregates_lineages():
    timeline = _make_timeline()
    assert timeline.total_lineages == 2
    assert timeline.total_events == 4  # 3 + 1
    assert timeline.total_spend == pytest.approx(12_000_000.0)


def test_evolution_timeline_date_range():
    timeline = _make_timeline()
    assert timeline.date_range["earliest"] == "2019-01-10"
    assert timeline.date_range["latest"] == "2023-07-15"


def test_evolution_timeline_defaults():
    tl = EvolutionTimeline(timeline_id="tl-empty", jurisdiction="Test")
    assert tl.lineages == []
    assert tl.total_lineages == 0
    assert tl.growth_patterns == []


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def test_contract_event_serializes_to_dict():
    event = ContractEvent(
        event_id="evt-ser",
        event_type="payment",
        date="2022-09-01",
        description="Q3 payment",
        dollar_amount=75_000.0,
    )
    data = event.model_dump()
    assert data["event_id"] == "evt-ser"
    assert data["dollar_amount"] == 75_000.0
    assert isinstance(data["signatures"], dict)


def test_contract_lineage_serializes_to_json():
    lineage = _make_lineage_with_events()
    raw = lineage.model_dump()
    # Verify it's JSON-serializable
    serialized = json.dumps(raw)
    restored = json.loads(serialized)
    assert restored["vendor"] == "SecureTech"
    assert len(restored["events"]) == 3


def test_evolution_timeline_serializes_to_json():
    timeline = _make_timeline()
    raw = timeline.model_dump()
    serialized = json.dumps(raw)
    restored = json.loads(serialized)
    assert restored["total_lineages"] == 2
    assert restored["jurisdiction"] == "Example City"
