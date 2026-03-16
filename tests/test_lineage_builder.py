"""Tests for the ContractLineage builder."""

from __future__ import annotations

import pytest

from oraculus_di_auditor.temporal.lineage_builder import LineageBuilder

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _doc(
    doc_id: str,
    vendor: str,
    date: str,
    event_type: str = "original",
    amount: float | None = None,
    contract_id: str | None = None,
    title: str | None = None,
    auth_type: str | None = None,
    signatures: dict | None = None,
) -> dict:
    d: dict = {
        "id": doc_id,
        "vendor": vendor,
        "date": date,
        "document_type": event_type,
        "title": title or f"{event_type} — {vendor}",
    }
    if amount is not None:
        d["amount"] = amount
    if contract_id:
        d["contract_id"] = contract_id
    if auth_type:
        d["authorization_type"] = auth_type
    if signatures:
        d["signatures"] = signatures
    return d


# ---------------------------------------------------------------------------
# Basic grouping
# ---------------------------------------------------------------------------


def test_single_document_creates_single_event_lineage():
    builder = LineageBuilder()
    builder.load_documents(
        [_doc("d1", "SecureTech", "2020-03-01", "original", 200_000.0)]
    )
    lineages = builder.build_lineages()
    assert len(lineages) == 1
    assert len(lineages[0].events) == 1
    assert lineages[0].vendor == "SecureTech"


def test_two_documents_same_vendor_grouped():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2020-03-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2022-05-15", "amendment", 400_000.0),
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    assert len(lineages) == 1
    assert len(lineages[0].events) == 2


def test_different_vendors_separate_lineages():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2020-03-01", "original", 200_000.0),
        _doc("d2", "VisionGuard", "2021-06-01", "original", 150_000.0),
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    assert len(lineages) == 2
    vendors = {ln.vendor for ln in lineages}
    assert vendors == {"SecureTech", "VisionGuard"}


def test_empty_document_list_returns_empty():
    builder = LineageBuilder()
    builder.load_documents([])
    assert builder.build_lineages() == []


# ---------------------------------------------------------------------------
# Chronological ordering
# ---------------------------------------------------------------------------


def test_events_ordered_chronologically():
    builder = LineageBuilder()
    docs = [
        _doc("d3", "SecureTech", "2023-01-10", "amendment", 600_000.0),
        _doc("d1", "SecureTech", "2020-03-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2021-09-01", "amendment", 400_000.0),
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    dates = [e.date for e in lineages[0].events]
    assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# Amount calculations
# ---------------------------------------------------------------------------


def test_cumulative_amounts_computed():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2020-03-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2021-09-01", "amendment", 500_000.0),
        _doc("d3", "SecureTech", "2023-01-10", "amendment", 300_000.0),
    ]
    builder.load_documents(docs)
    lineage = builder.build_lineages()[0]
    cumulatives = [e.cumulative_amount for e in lineage.events]
    assert cumulatives == [200_000.0, 700_000.0, 1_000_000.0]


def test_growth_percentage_computed():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2019-01-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2021-01-01", "amendment", 10_800_000.0),
    ]
    builder.load_documents(docs)
    lineage = builder.build_lineages()[0]
    # original=200k, current=total=11M, growth=(11M-200k)/200k*100 = 5400%
    assert lineage.growth_percentage == pytest.approx(5400.0)


# ---------------------------------------------------------------------------
# Amendment count
# ---------------------------------------------------------------------------


def test_amendment_count_reflects_actual_amendments():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2019-01-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2020-06-01", "amendment", 500_000.0),
        _doc("d3", "SecureTech", "2022-03-01", "amendment", 500_000.0),
        _doc("d4", "SecureTech", "2023-01-01", "renewal", 100_000.0),
    ]
    builder.load_documents(docs)
    lineage = builder.build_lineages()[0]
    assert lineage.amendment_count == 2


# ---------------------------------------------------------------------------
# Risk score
# ---------------------------------------------------------------------------


def test_risk_score_low_for_clean_lineage():
    builder = LineageBuilder()
    docs = [
        _doc(
            "d1",
            "CleanCo",
            "2022-01-01",
            "original",
            100_000.0,
            auth_type="council_vote",
        )
    ]
    builder.load_documents(docs)
    lineage = builder.build_lineages()[0]
    assert lineage.risk_score < 0.2


def test_risk_score_increases_with_risk_factors():
    """Multiple risk factors push risk_score higher."""
    builder = LineageBuilder()
    docs = [
        _doc(
            "d1",
            "RiskyVendor",
            "2017-01-01",
            "original",
            100_000.0,
            auth_type="sole_source",
        ),
        _doc(
            "d2",
            "RiskyVendor",
            "2018-06-01",
            "amendment",
            500_000.0,
            auth_type="sole_source",
        ),
        _doc(
            "d3",
            "RiskyVendor",
            "2020-06-01",
            "amendment",
            1_000_000.0,
            auth_type="sole_source",
        ),
        _doc(
            "d4",
            "RiskyVendor",
            "2022-06-01",
            "amendment",
            2_000_000.0,
            auth_type="sole_source",
        ),
        _doc(
            "d5",
            "RiskyVendor",
            "2024-06-01",
            "amendment",
            4_000_000.0,
            auth_type="sole_source",
        ),
    ]
    builder.load_documents(docs)
    lineage = builder.build_lineages()[0]
    assert lineage.risk_score > 0.4


# ---------------------------------------------------------------------------
# Anomaly attachment
# ---------------------------------------------------------------------------


def test_analysis_anomalies_attached_to_events():
    builder = LineageBuilder()
    docs = [
        _doc("d1", "SecureTech", "2020-01-01", "original", 200_000.0),
        _doc("d2", "SecureTech", "2020-01-15", "execution", 0.0),
    ]
    analysis_results = [
        {
            "document_id": "d2",
            "anomalies": [{"id": "procurement:pre-authorization-execution"}],
        }
    ]
    builder.load_documents(docs, analysis_results)
    lineage = builder.build_lineages()[0]
    event_anomalies = {e.document_id: e.anomalies for e in lineage.events}
    assert "procurement:pre-authorization-execution" in event_anomalies["d2"]
    assert event_anomalies["d1"] == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_documents_without_dates_handled_gracefully():
    builder = LineageBuilder()
    docs = [
        {
            "id": "d1",
            "vendor": "SecureTech",
            "document_type": "original",
            "amount": 100_000.0,
        },
        {
            "id": "d2",
            "vendor": "SecureTech",
            "document_type": "amendment",
            "amount": 50_000.0,
        },
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    assert len(lineages) == 1
    for event in lineages[0].events:
        assert event.date == "unknown"


def test_vendor_extracted_from_text():
    """Fall through to text extraction when no vendor metadata field."""
    builder = LineageBuilder()
    docs = [
        {
            "id": "d1",
            "date": "2021-04-01",
            "document_type": "original",
            "amount": 250_000.0,
            "text": (
                "This agreement is between the City and SkyWatch Systems"
                " for surveillance services."
            ),
        }
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    assert len(lineages) == 1
    # Vendor extracted from text pattern
    assert "skywatch" in lineages[0].vendor.lower() or lineages[0].vendor != "unknown"


def test_load_documents_returns_count():
    builder = LineageBuilder()
    n = builder.load_documents([_doc("d1", "V1", "2020-01-01")])
    assert n == 1


def test_same_vendor_different_contract_ids_separate_lineages():
    """Same vendor but different contract families should be separate lineages."""
    builder = LineageBuilder()
    docs = [
        _doc(
            "d1",
            "SecureTech",
            "2020-01-01",
            "original",
            100_000.0,
            contract_id="MSPA-001",
        ),
        _doc(
            "d2",
            "SecureTech",
            "2021-06-01",
            "original",
            200_000.0,
            contract_id="MSPA-002",
        ),
    ]
    builder.load_documents(docs)
    lineages = builder.build_lineages()
    # Different contract IDs -> different lineages
    assert len(lineages) == 2
