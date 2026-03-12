#!/usr/bin/env python3
"""Tests for procurement irregularities detection.

This module tests the procurement irregularity scanning functionality.
Total: 25 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.vendor_map_extractor import (
    infer_contract_relationships,
    scan_for_procurement_irregularities,
)


class TestScanForProcurementIrregularities:
    """Tests for scan_for_procurement_irregularities function."""

    def test_empty_data(self):
        """Test with empty data returns no irregularities."""
        result = scan_for_procurement_irregularities({}, [], {}, {})
        assert result == []

    def test_detect_sole_source(self):
        """Test detection of sole-source mentions."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "This is a sole source procurement for services."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        sole_source_flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(sole_source_flags) >= 1

    def test_detect_single_source(self):
        """Test detection of single-source mentions."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "Single source contract with vendor."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        sole_source_flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(sole_source_flags) >= 1

    def test_detect_non_competitive(self):
        """Test detection of non-competitive mentions."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "Non-competitive procurement approved."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(flags) >= 1

    def test_detect_emergency_procurement(self):
        """Test detection of emergency procurement."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "Emergency procurement authorized due to urgency."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(flags) >= 1

    def test_detect_piggyback_contract(self):
        """Test detection of piggyback contract."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "Piggyback contract on state agreement."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(flags) >= 1

    def test_detect_inconsistent_labeling(self):
        """Test detection of inconsistent vendor labeling."""
        vendor_index = {
            "Axon": {
                "years": ["2020", "2021", "2022"],
                "sources": ["filename", "metadata", "text"],
            }
        }

        result = scan_for_procurement_irregularities(vendor_index, [], {}, {})

        inconsistent = [r for r in result if r["type"] == "inconsistent_labeling"]
        assert len(inconsistent) >= 1

    def test_detect_cost_escalation(self):
        """Test detection of cost escalation > 40%."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 100000},
            {"vendor": "Axon", "year": "2021", "total_amount": 150000},
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert len(escalations) >= 1
        assert escalations[0]["increase_percent"] == 50.0

    def test_no_escalation_under_40_percent(self):
        """Test no escalation flag for <40% increase."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 100000},
            {"vendor": "Axon", "year": "2021", "total_amount": 130000},
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert len(escalations) == 0

    def test_detect_multi_year_vendor(self):
        """Test detection of multi-year vendor (>3 years)."""
        vendor_index = {
            "Axon": {
                "years": ["2018", "2019", "2020", "2021"],
                "sources": ["text"],
            },
        }

        result = scan_for_procurement_irregularities(vendor_index, [], {}, {})

        multi_year = [r for r in result if r["type"] == "multi_year_vendor"]
        assert len(multi_year) >= 1
        assert multi_year[0]["year_count"] == 4

    def test_cost_escalation_severity_high(self):
        """Test high severity for >100% cost increase."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 100000},
            {"vendor": "Axon", "year": "2021", "total_amount": 250000},
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert len(escalations) >= 1
        assert escalations[0]["severity"] == "high"

    def test_cost_escalation_severity_medium(self):
        """Test medium severity for 40-100% cost increase."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 100000},
            {"vendor": "Axon", "year": "2021", "total_amount": 180000},
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert len(escalations) >= 1
        assert escalations[0]["severity"] == "medium"

    def test_sole_source_context_extraction(self):
        """Test context is extracted for sole-source flags."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": (
                    "The council approved a sole source procurement "
                    "for emergency services worth $50,000."
                )
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert len(flags) >= 1
        assert "context" in flags[0]
        assert len(flags[0]["context"]) > 0


class TestInferContractRelationships:
    """Tests for infer_contract_relationships function."""

    def test_empty_data(self):
        """Test with empty data returns empty list."""
        result = infer_contract_relationships({}, [], {})
        assert result == []

    def test_link_vendor_to_amounts(self):
        """Test linking vendor to amounts in same corpus."""
        vendor_index = {
            "Axon": {
                "hist_ids": ["HIST-1234"],
            }
        }
        amounts = [
            {"hist_id": "HIST-1234", "parsed_amount": 50000},
        ]
        corpora = {"HIST-1234": "2020-01-15"}

        result = infer_contract_relationships(vendor_index, amounts, corpora)

        assert len(result) >= 1
        assert result[0]["vendor"] == "Axon"
        assert result[0]["total_amount"] == 50000

    def test_relationship_includes_year(self):
        """Test relationship includes year from corpus."""
        vendor_index = {
            "Axon": {"hist_ids": ["HIST-1234"]},
        }
        amounts = [
            {"hist_id": "HIST-1234", "parsed_amount": 50000},
        ]
        corpora = {"HIST-1234": "2020-01-15"}

        result = infer_contract_relationships(vendor_index, amounts, corpora)

        assert result[0]["year"] == "2020"

    def test_aggregate_multiple_amounts(self):
        """Test aggregation of multiple amounts for same vendor/corpus."""
        vendor_index = {
            "Axon": {"hist_ids": ["HIST-1234"]},
        }
        amounts = [
            {"hist_id": "HIST-1234", "parsed_amount": 50000},
            {"hist_id": "HIST-1234", "parsed_amount": 30000},
        ]
        corpora = {"HIST-1234": "2020-01-15"}

        result = infer_contract_relationships(vendor_index, amounts, corpora)

        assert result[0]["total_amount"] == 80000
        assert result[0]["amount_count"] == 2

    def test_no_relationship_without_amounts(self):
        """Test no relationship if no amounts in corpus."""
        vendor_index = {
            "Axon": {"hist_ids": ["HIST-1234"]},
        }
        amounts = []  # No amounts
        corpora = {"HIST-1234": "2020-01-15"}

        result = infer_contract_relationships(vendor_index, amounts, corpora)

        assert len(result) == 0


class TestIrregularityDetails:
    """Tests for irregularity detail fields."""

    def test_sole_source_has_details(self):
        """Test sole source flag has details field."""
        data = {
            "extracted_text_cache": {
                "HIST-1234/file.txt": "Sole source procurement approved."
            }
        }
        corpora = {"HIST-1234": "2020-01-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert "details" in flags[0]

    def test_cost_escalation_has_details(self):
        """Test cost escalation has details with amounts."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 100000},
            {"vendor": "Axon", "year": "2021", "total_amount": 150000},
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert "details" in escalations[0]
        assert "100,000" in escalations[0]["details"]
        assert "150,000" in escalations[0]["details"]

    def test_multi_year_vendor_has_years_list(self):
        """Test multi-year vendor flag includes years list."""
        vendor_index = {
            "Axon": {
                "years": ["2018", "2019", "2020", "2021"],
                "sources": ["text"],
            },
        }

        result = scan_for_procurement_irregularities(vendor_index, [], {}, {})

        multi_year = [r for r in result if r["type"] == "multi_year_vendor"]
        assert "years" in multi_year[0]
        assert len(multi_year[0]["years"]) == 4

    def test_year_is_extracted_correctly(self):
        """Test year is extracted from corpus date."""
        data = {
            "extracted_text_cache": {"HIST-1234/file.txt": "Sole source procurement."}
        }
        corpora = {"HIST-1234": "2021-06-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert flags[0]["year"] == "2021"

    def test_hist_id_in_flag(self):
        """Test hist_id is included in irregularity flag."""
        data = {
            "extracted_text_cache": {"HIST-5678/file.txt": "Sole source procurement."}
        }
        corpora = {"HIST-5678": "2020-03-15"}

        result = scan_for_procurement_irregularities({}, [], data, corpora)

        flags = [r for r in result if r["type"] == "sole_source_flag"]
        assert flags[0]["hist_id"] == "HIST-5678"

    def test_multi_year_vendor_not_triggered_under_threshold(self):
        """Test multi-year vendor flag not triggered for <=3 years."""
        vendor_index = {
            "Axon": {
                "years": ["2020", "2021", "2022"],  # Exactly 3 years
                "sources": ["text"],
            },
        }

        result = scan_for_procurement_irregularities(vendor_index, [], {}, {})

        multi_year = [r for r in result if r["type"] == "multi_year_vendor"]
        assert len(multi_year) == 0  # Threshold is >3

    def test_cost_decrease_not_flagged(self):
        """Test that cost decreases don't trigger escalation flags."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": []},
        }
        relationships = [
            {"vendor": "Axon", "year": "2020", "total_amount": 200000},
            {"vendor": "Axon", "year": "2021", "total_amount": 100000},  # Decrease
        ]

        result = scan_for_procurement_irregularities(
            vendor_index, relationships, {}, {}
        )

        escalations = [r for r in result if r["type"] == "cost_escalation"]
        assert len(escalations) == 0
