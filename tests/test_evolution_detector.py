"""Tests for the EvolutionPatternDetector."""

from __future__ import annotations

from oraculus_di_auditor.temporal.evolution_detector import (
    EvolutionPatternDetector,
)
from oraculus_di_auditor.temporal.models import ContractEvent, ContractLineage

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    idx: int,
    event_type: str = "original",
    date: str = "2020-01-01",
    amount: float = 100_000.0,
    auth_type: str | None = None,
    description: str = "",
) -> ContractEvent:
    return ContractEvent(
        event_id=f"e{idx:03d}",
        event_type=event_type,
        date=date,
        description=description or event_type,
        dollar_amount=amount,
        cumulative_amount=amount,
        authorization_type=auth_type,
    )


def _make_lineage(
    vendor: str,
    events: list[ContractEvent],
    lineage_id: str | None = None,
    program: str | None = None,
) -> ContractLineage:
    original_amount = (
        next((e.dollar_amount for e in events if e.event_type == "original"), 0.0)
        or 0.0
    )
    current_amount = sum(e.dollar_amount or 0 for e in events)
    return ContractLineage(
        lineage_id=lineage_id or f"lid_{vendor.lower()[:8]}",
        vendor=vendor,
        program=program,
        original_amount=original_amount,
        current_amount=current_amount,
        total_authorized=current_amount,
        events=events,
    )


# ---------------------------------------------------------------------------
# Scope creep
# ---------------------------------------------------------------------------


def test_scope_creep_detected_404_percent_growth():
    events = [
        _make_event(1, "original", "2019-01-01", 766_000.0),
        _make_event(2, "amendment", "2020-06-01", 500_000.0),
        _make_event(3, "amendment", "2021-03-01", 800_000.0),
        _make_event(4, "amendment", "2022-01-01", 1_000_000.0),
        _make_event(5, "amendment", "2023-06-01", 1_034_000.0),
    ]
    lineage = _make_lineage("Axon", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_scope_creep()
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "scope_creep"
    assert patterns[0].severity in ("critical", "high")
    assert patterns[0].metrics["amendment_count"] == 4
    assert patterns[0].metrics["growth_percentage"] > 200


def test_scope_creep_not_detected_modest_growth():
    events = [
        _make_event(1, "original", "2020-01-01", 500_000.0),
        _make_event(2, "amendment", "2021-01-01", 100_000.0),
        _make_event(3, "amendment", "2022-01-01", 100_000.0),
        _make_event(4, "amendment", "2023-01-01", 100_000.0),
    ]
    lineage = _make_lineage("VendorX", events)
    # growth = (800k - 500k) / 500k * 100 = 60% — below 200% threshold
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_scope_creep()
    assert len(patterns) == 0


def test_scope_creep_requires_3_amendments():
    """Even with >200% growth, needs >=3 amendments."""
    events = [
        _make_event(1, "original", "2019-01-01", 100_000.0),
        _make_event(2, "amendment", "2020-01-01", 500_000.0),
    ]
    lineage = _make_lineage("VendorY", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_scope_creep()
    assert len(patterns) == 0


# ---------------------------------------------------------------------------
# Vendor lock-in
# ---------------------------------------------------------------------------


def test_vendor_lock_in_detected_5_sole_source_events_6_years():
    events = [
        _make_event(1, "original", "2018-01-01", 200_000.0, "sole_source"),
        _make_event(2, "amendment", "2019-06-01", 300_000.0, "sole_source"),
        _make_event(3, "renewal", "2020-06-01", 300_000.0, "sole_source"),
        _make_event(4, "amendment", "2022-01-01", 400_000.0, "sole_source"),
        _make_event(5, "renewal", "2024-06-01", 500_000.0, "sole_source"),
    ]
    lineage = _make_lineage("Axon", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_vendor_lock_in()
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "vendor_lock_in"
    assert patterns[0].metrics["total_events"] == 5
    assert patterns[0].metrics["span_years"] > 5


def test_vendor_lock_in_not_detected_with_competitive_bidding():
    events = [
        _make_event(1, "original", "2018-01-01", 200_000.0, "competitive_bid"),
        _make_event(2, "renewal", "2020-01-01", 250_000.0, "competitive_bid"),
        _make_event(3, "renewal", "2022-01-01", 300_000.0, "competitive_bid"),
        _make_event(4, "renewal", "2024-01-01", 350_000.0, "competitive_bid"),
    ]
    lineage = _make_lineage("SecureTech", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_vendor_lock_in()
    assert len(patterns) == 0


def test_vendor_lock_in_not_detected_short_span():
    """3 events but span < 3 years — not lock-in."""
    events = [
        _make_event(1, "original", "2023-01-01", 100_000.0, "sole_source"),
        _make_event(2, "amendment", "2023-09-01", 50_000.0, "sole_source"),
        _make_event(3, "renewal", "2024-06-01", 50_000.0, "sole_source"),
    ]
    lineage = _make_lineage("NewVendor", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_vendor_lock_in()
    assert len(patterns) == 0


# ---------------------------------------------------------------------------
# Capability embedding
# ---------------------------------------------------------------------------


def test_capability_embedding_detected_new_tech_in_amendments():
    events = [
        _make_event(
            1,
            "original",
            "2019-01-01",
            500_000.0,
            description="body camera program initial contract",
        ),
        _make_event(
            2,
            "amendment",
            "2020-06-01",
            300_000.0,
            description="amendment adds ALPR license plate reader expansion",
        ),
        _make_event(
            3,
            "amendment",
            "2021-09-01",
            400_000.0,
            description="amendment includes Fusus real-time video integration",
        ),
    ]
    lineage = _make_lineage("Axon", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_capability_embedding()
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "capability_embedding"
    assert len(patterns[0].metrics["new_capabilities"]) >= 1


def test_capability_embedding_not_detected_no_new_tech():
    events = [
        _make_event(
            1,
            "original",
            "2019-01-01",
            500_000.0,
            description="body camera program",
        ),
        _make_event(
            2,
            "amendment",
            "2020-06-01",
            100_000.0,
            description="body camera storage expansion",
        ),
    ]
    lineage = _make_lineage("Axon", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_capability_embedding()
    assert len(patterns) == 0


# ---------------------------------------------------------------------------
# Authorization erosion
# ---------------------------------------------------------------------------


def test_authorization_erosion_detected_council_to_consent():
    events = [
        _make_event(1, "original", "2018-01-01", 200_000.0, "council_vote"),
        _make_event(2, "authorization", "2019-06-01", 50_000.0, "council_vote"),
        _make_event(3, "amendment", "2021-01-01", 300_000.0, "consent_calendar"),
        _make_event(4, "renewal", "2023-01-01", 400_000.0, None),
    ]
    lineage = _make_lineage("SecureTech", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_authorization_erosion()
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "authorization_erosion"
    assert patterns[0].metrics["early_council_votes"] >= 1
    assert patterns[0].metrics["late_weak_authorizations"] >= 1


def test_authorization_erosion_not_detected_consistent_council():
    events = [
        _make_event(1, "original", "2018-01-01", 200_000.0, "council_vote"),
        _make_event(2, "amendment", "2020-01-01", 100_000.0, "council_vote"),
        _make_event(3, "renewal", "2022-01-01", 100_000.0, "council_vote"),
        _make_event(4, "renewal", "2024-01-01", 100_000.0, "council_vote"),
    ]
    lineage = _make_lineage("VendorZ", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_authorization_erosion()
    assert len(patterns) == 0


# ---------------------------------------------------------------------------
# Parallel vendor expansion
# ---------------------------------------------------------------------------


def test_parallel_expansion_detected_same_vendor_two_lineages():
    events_a = [
        _make_event(1, "original", "2019-01-01", 300_000.0),
        _make_event(2, "amendment", "2020-06-01", 200_000.0),
        _make_event(3, "amendment", "2022-01-01", 300_000.0),
    ]
    events_b = [
        _make_event(4, "original", "2020-01-01", 100_000.0),
        _make_event(5, "amendment", "2021-06-01", 150_000.0),
        _make_event(6, "amendment", "2022-09-01", 200_000.0),
    ]
    lineage_a = _make_lineage(
        "Axon", events_a, lineage_id="lid_axon_bwc", program="BWC"
    )
    lineage_b = _make_lineage(
        "Axon", events_b, lineage_id="lid_axon_alpr", program="ALPR"
    )
    detector = EvolutionPatternDetector([lineage_a, lineage_b])
    patterns = detector.detect_parallel_vendor_expansion()
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "parallel_expansion"
    assert "Axon" in patterns[0].vendors
    assert patterns[0].metrics["lineage_count"] == 2


def test_parallel_expansion_not_detected_single_lineage():
    events = [
        _make_event(1, "original", "2019-01-01", 300_000.0),
        _make_event(2, "amendment", "2021-01-01", 200_000.0),
    ]
    lineage = _make_lineage("SingleVendor", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_parallel_vendor_expansion()
    assert len(patterns) == 0


# ---------------------------------------------------------------------------
# detect_all_patterns
# ---------------------------------------------------------------------------


def test_detect_all_patterns_returns_combined_results():
    """A high-risk lineage with scope creep + lock-in shows multiple pattern types."""
    events = [
        _make_event(1, "original", "2018-01-01", 200_000.0, "council_vote"),
        _make_event(2, "amendment", "2019-01-01", 400_000.0, "sole_source"),
        _make_event(3, "amendment", "2020-01-01", 600_000.0, "sole_source"),
        _make_event(4, "amendment", "2021-01-01", 800_000.0, "sole_source"),
        _make_event(5, "amendment", "2022-01-01", 1_000_000.0, "consent_calendar"),
        _make_event(6, "renewal", "2024-01-01", 1_200_000.0, None),
    ]
    lineage = _make_lineage("RiskyVendor", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_all_patterns()
    pattern_types = {p.pattern_type for p in patterns}
    # Should detect at least scope_creep + vendor_lock_in + authorization_erosion
    assert "scope_creep" in pattern_types
    assert "vendor_lock_in" in pattern_types
    assert len(patterns) >= 2


def test_empty_lineages_returns_empty_patterns():
    detector = EvolutionPatternDetector([])
    assert detector.detect_all_patterns() == []


def test_single_event_lineage_produces_no_temporal_patterns():
    events = [_make_event(1, "original", "2022-01-01", 100_000.0)]
    lineage = _make_lineage("CleanVendor", events)
    detector = EvolutionPatternDetector([lineage])
    patterns = detector.detect_all_patterns()
    assert len(patterns) == 0
