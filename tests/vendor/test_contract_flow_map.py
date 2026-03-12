#!/usr/bin/env python3
"""Tests for contract flow map functionality.

This module tests the contract_flow_map.py functions.
Total: 15 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.contract_flow_map import (
    build_tech_program_timeline,
    build_yearly_vendor_activity,
    detect_contract_renewals,
    generate_contract_flow_map,
    generate_contract_flow_map_md,
)


class TestBuildYearlyVendorActivity:
    """Tests for build_yearly_vendor_activity function."""

    def test_empty_vendor_index(self):
        """Test with empty vendor index."""
        result = build_yearly_vendor_activity({}, "2020-2022")
        assert "2020" in result
        assert "2021" in result
        assert "2022" in result
        assert result["2020"]["total_active"] == 0

    def test_vendor_across_years(self):
        """Test vendor appearing across multiple years."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021", "2022"]},
        }
        result = build_yearly_vendor_activity(vendor_index, "2020-2022")

        assert "Axon" in result["2020"]["active_vendors"]
        assert "Axon" in result["2021"]["active_vendors"]
        assert "Axon" in result["2022"]["active_vendors"]

    def test_new_vendor_detection(self):
        """Test detection of new vendors."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"]},
            "Flock": {"years": ["2021"]},
        }
        result = build_yearly_vendor_activity(vendor_index, "2020-2021")

        assert "Axon" in result["2020"]["new_vendors"]
        assert "Flock" in result["2021"]["new_vendors"]

    def test_continuing_vendor_detection(self):
        """Test detection of continuing vendors."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"]},
        }
        result = build_yearly_vendor_activity(vendor_index, "2020-2021")

        assert "Axon" in result["2021"]["continuing_vendors"]


class TestDetectContractRenewals:
    """Tests for detect_contract_renewals function."""

    def test_no_renewals_single_year(self):
        """Test no renewals for single-year vendors."""
        vendor_index = {
            "Axon": {"years": ["2020"]},
        }
        result = detect_contract_renewals(vendor_index)
        assert len(result) == 0

    def test_detect_consecutive_renewal(self):
        """Test detection of consecutive year renewal."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021", "2022"]},
        }
        result = detect_contract_renewals(vendor_index)

        assert len(result) >= 1
        assert result[0]["vendor"] == "Axon"
        assert result[0]["consecutive_years"] == 3

    def test_detect_gap_in_years(self):
        """Test handling of gaps in vendor years."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021", "2024", "2025"]},
        }
        result = detect_contract_renewals(vendor_index)

        # Should detect two separate renewal periods
        assert len(result) == 2


class TestBuildTechProgramTimeline:
    """Tests for build_tech_program_timeline function."""

    def test_empty_programs(self):
        """Test with empty tech programs."""
        result = build_tech_program_timeline({}, "2020-2022")
        assert result == {}

    def test_program_timeline(self):
        """Test program timeline building."""
        tech_programs = {
            "ALPR": {
                "years": ["2020", "2021"],
                "vendors": ["Flock"],
                "mention_count": 5,
            }
        }
        result = build_tech_program_timeline(tech_programs, "2020-2022")

        assert "ALPR" in result
        assert result["ALPR"]["first_appearance"] == "2020"
        assert result["ALPR"]["last_appearance"] == "2021"
        assert "Flock" in result["ALPR"]["vendors_associated"]

    def test_program_status_active(self):
        """Test program status for active programs."""
        tech_programs = {
            "ALPR": {
                "years": ["2022"],
                "vendors": [],
                "mention_count": 1,
            }
        }
        result = build_tech_program_timeline(tech_programs, "2020-2022")

        assert result["ALPR"]["status"] == "active"


class TestGenerateContractFlowMap:
    """Tests for generate_contract_flow_map function."""

    def test_flow_map_structure(self):
        """Test contract flow map has required structure."""
        vendor_index = {
            "Axon": {"years": ["2020"], "hist_ids": [], "appearance_count": 1},
        }
        result = generate_contract_flow_map(vendor_index, [], {}, "2020-2022")

        assert "version" in result
        assert "generated_at" in result
        assert "summary" in result
        assert "yearly_activity" in result
        assert "contract_renewals" in result
        assert "program_timeline" in result

    def test_flow_map_summary(self):
        """Test contract flow map summary."""
        vendor_index = {
            "Axon": {"years": ["2020", "2021"], "hist_ids": [], "appearance_count": 2},
            "Flock": {"years": ["2021"], "hist_ids": [], "appearance_count": 1},
        }
        result = generate_contract_flow_map(vendor_index, [], {}, "2020-2022")

        assert result["summary"]["total_vendors"] == 2
        assert result["summary"]["years_covered"] == 3


class TestGenerateContractFlowMapMd:
    """Tests for generate_contract_flow_map_md function."""

    def test_md_is_string(self):
        """Test markdown output is a string."""
        flow_map = {
            "generated_at": "2025-12-06T00:00:00Z",
            "version": "1.0",
            "summary": {
                "total_vendors": 1,
                "years_covered": 3,
                "total_renewals_detected": 0,
                "long_term_vendors": 0,
                "technology_programs_tracked": 0,
            },
            "yearly_activity": {},
            "contract_renewals": [],
            "program_timeline": {},
            "amounts_by_year": {},
            "vendor_longevity": {"long_term_5plus": [], "by_year_count": {}},
        }
        result = generate_contract_flow_map_md(flow_map)

        assert isinstance(result, str)

    def test_md_has_header(self):
        """Test markdown has header."""
        flow_map = {
            "generated_at": "2025-12-06T00:00:00Z",
            "version": "1.0",
            "summary": {
                "total_vendors": 0,
                "years_covered": 0,
                "total_renewals_detected": 0,
                "long_term_vendors": 0,
                "technology_programs_tracked": 0,
            },
            "yearly_activity": {},
            "contract_renewals": [],
            "program_timeline": {},
            "amounts_by_year": {},
            "vendor_longevity": {"long_term_5plus": [], "by_year_count": {}},
        }
        result = generate_contract_flow_map_md(flow_map)

        assert "# Contract Flow Map" in result

    def test_md_includes_summary(self):
        """Test markdown includes summary statistics."""
        flow_map = {
            "generated_at": "2025-12-06T00:00:00Z",
            "version": "1.0",
            "summary": {
                "total_vendors": 10,
                "years_covered": 5,
                "total_renewals_detected": 3,
                "long_term_vendors": 2,
                "technology_programs_tracked": 4,
            },
            "yearly_activity": {},
            "contract_renewals": [],
            "program_timeline": {},
            "amounts_by_year": {},
            "vendor_longevity": {"long_term_5plus": [], "by_year_count": {}},
        }
        result = generate_contract_flow_map_md(flow_map)

        assert "Total Vendors Tracked" in result
        assert "10" in result
