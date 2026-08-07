"""Unit tests for the AAA retrieval client using the HTML fixture.

All tests pass pre-fetched HTML (the fixture) so no network access occurs.
The fixture is at tests/contra/fixtures/aaa_q1_2024_snapshot.html.
"""

import json
from pathlib import Path

import pytest

from oraculus_di_auditor.analytics.section1281_96.normalize import NormalizedCase
from oraculus_di_auditor.analytics.section1281_96.retrieval_aaa import (
    AAARetriever,
)

FIXTURE = (
    Path(__file__).parent.parent.parent
    / "contra"
    / "fixtures"
    / "aaa_q1_2024_snapshot.html"
)


@pytest.fixture
def fixture_html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


@pytest.fixture
def retriever() -> AAARetriever:
    return AAARetriever(rate_limit_secs=0.0)


# ---------------------------------------------------------------------------
# Index parsing
# ---------------------------------------------------------------------------


class TestFetchQuarterlyIndex:
    def test_finds_csv_links(self, retriever, fixture_html):
        releases = retriever.fetch_quarterly_index(html_source=fixture_html)
        assert len(releases) >= 2

    def test_infers_year_2024(self, retriever, fixture_html):
        releases = retriever.fetch_quarterly_index(html_source=fixture_html)
        years = {r.year for r in releases}
        assert 2024 in years

    def test_infers_quarter_1(self, retriever, fixture_html):
        releases = retriever.fetch_quarterly_index(html_source=fixture_html)
        q1_releases = [r for r in releases if r.year == 2024 and r.quarter == 1]
        assert len(q1_releases) >= 1

    def test_url_absolute(self, retriever, fixture_html):
        releases = retriever.fetch_quarterly_index(html_source=fixture_html)
        for r in releases:
            assert r.url.startswith("http")

    def test_format_detection(self, retriever, fixture_html):
        releases = retriever.fetch_quarterly_index(html_source=fixture_html)
        fmts = {r.fmt for r in releases}
        assert fmts & {"csv", "excel"}


# ---------------------------------------------------------------------------
# HTML table parsing
# ---------------------------------------------------------------------------


class TestParseHtmlTable:
    def test_returns_list_of_normalized_cases(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert isinstance(cases, list)
        assert len(cases) > 0
        assert all(isinstance(c, NormalizedCase) for c in cases)

    def test_correct_row_count(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert len(cases) == 20

    def test_provider_is_aaa(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert all(c.provider == "AAA" for c in cases)

    def test_year_and_quarter_set(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert all(c.case_year == 2024 for c in cases)
        assert all(c.case_quarter == 1 for c in cases)

    def test_party_name_populated(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert all(
            c.non_consumer_party_name and c.non_consumer_party_name != "UNKNOWN"
            for c in cases
        )

    def test_award_after_hearing_cases(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        award_cases = [c for c in cases if c.disposition_type == "AWARD_AFTER_HEARING"]
        assert len(award_cases) >= 10

    def test_settled_cases_present(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        settled = [c for c in cases if c.disposition_type == "SETTLED"]
        assert len(settled) >= 3

    def test_consumer_wins_parsed(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        consumer_wins = [
            c
            for c in cases
            if c.disposition_type == "AWARD_AFTER_HEARING"
            and c.prevailing_party == "CONSUMER"
        ]
        assert len(consumer_wins) >= 4

    def test_claim_amounts_parsed(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_amounts = [c for c in cases if c.claim_amount_usd is not None]
        assert len(with_amounts) > 0
        assert all(c.claim_amount_usd > 0 for c in with_amounts)

    def test_claim_tiers_assigned(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_tiers = [c for c in cases if c.claim_amount_tier is not None]
        assert len(with_tiers) > 0
        valid_tiers = {"UNDER_1K", "1K_10K", "10K_75K", "75K_300K", "OVER_300K"}
        assert all(c.claim_amount_tier in valid_tiers for c in with_tiers)

    def test_fee_split_computed(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_fees = [c for c in cases if c.arbitrator_fee_total_usd is not None]
        assert len(with_fees) > 0
        assert all(c.arbitrator_fee_total_usd >= 0 for c in with_fees)

    def test_arbitrator_names_parsed(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_arb = [c for c in cases if c.arbitrator_names]
        assert len(with_arb) > 0

    def test_panel_arbitrator_split(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        panel = [c for c in cases if len(c.arbitrator_names) > 1]
        assert len(panel) >= 1

    def test_fee_waiver_parsed(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_waiver = [c for c in cases if c.fee_waiver is not None]
        assert len(with_waiver) > 0
        waived = [c for c in with_waiver if c.fee_waiver is True]
        assert len(waived) >= 1

    def test_case_id_unique(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        ids = [c.case_id for c in cases]
        assert len(ids) == len(set(ids))

    def test_days_to_disposition_positive(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        with_days = [c for c in cases if c.days_to_disposition is not None]
        assert all(d >= 0 for d in (c.days_to_disposition for c in with_days))

    def test_quality_flags_list(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        assert all(isinstance(c.quality_flags, list) for c in cases)

    def test_to_db_dict_roundtrip(self, retriever, fixture_html):
        cases = retriever.parse_html_table(fixture_html, year=2024, quarter=1)
        for c in cases:
            d = c.to_db_dict()
            assert d["provider"] == "AAA"
            assert isinstance(json.loads(d["arbitrator_names"]), list)


# ---------------------------------------------------------------------------
# CSV parsing (synthetic)
# ---------------------------------------------------------------------------


class TestParseCSVBytes:
    def _make_csv(self) -> bytes:
        lines = [
            "Business Name,Dispute Type,Claim Amount,Disposition,Prevailing Party,"
            "Award Amount,Consumer Represented,Arbitrator,Business Fees,Consumer Fees,"
            "Fee Waiver,Filing Date,Close Date",
            "Tech Widgets Inc.,Consumer Contract,$5000.00,Award After Hearing,"
            "Consumer,$4500.00,Yes,Jane Doe,$1200.00,$250.00,No,01/10/2024,02/28/2024",
            "Credit Finance Corp.,Consumer Debt,$8000.00,Settled,,"
            ",No,,$0.00,$0.00,No,01/15/2024,01/25/2024",
        ]
        return "\n".join(lines).encode("utf-8")

    def test_parses_two_rows(self, retriever):
        cases = retriever.parse_csv_bytes(self._make_csv(), year=2024, quarter=1)
        assert len(cases) == 2

    def test_first_case_fields(self, retriever):
        cases = retriever.parse_csv_bytes(self._make_csv(), year=2024, quarter=1)
        c = cases[0]
        assert c.non_consumer_party_name == "Tech Widgets Inc."
        assert c.claim_amount_usd == pytest.approx(5000.0)
        assert c.disposition_type == "AWARD_AFTER_HEARING"
        assert c.prevailing_party == "CONSUMER"
        assert c.award_amount_usd == pytest.approx(4500.0)
        assert c.consumer_represented == "YES"
        assert c.arbitrator_names == ["Jane Doe"]

    def test_settled_no_prevailing(self, retriever):
        cases = retriever.parse_csv_bytes(self._make_csv(), year=2024, quarter=1)
        c = cases[1]
        assert c.disposition_type == "SETTLED"
        assert c.prevailing_party is None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_no_table_returns_empty(self, retriever):
        html = "<html><body><p>No table here.</p></body></html>"
        cases = retriever.parse_html_table(html, year=2024, quarter=1)
        assert cases == []

    def test_table_no_matching_headers_returns_empty(self, retriever):
        html = """
        <table>
          <tr><th>Foo</th><th>Bar</th></tr>
          <tr><td>X</td><td>Y</td></tr>
        </table>
        """
        cases = retriever.parse_html_table(html, year=2024, quarter=1)
        assert cases == []

    def test_empty_csv_returns_empty(self, retriever):
        cases = retriever.parse_csv_bytes(b"", year=2024, quarter=1)
        assert cases == []

    def test_source_url_stored(self, retriever, fixture_html):
        cases = retriever.parse_html_table(
            fixture_html, year=2024, quarter=1, source_url="https://www.adr.org/test"
        )
        assert all(c.case_url == "https://www.adr.org/test" for c in cases)
