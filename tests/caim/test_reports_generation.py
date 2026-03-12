#!/usr/bin/env python3
"""Tests for CAIM reports generation functionality.

This module tests the generate_caim_reports.py functions.
Total: 24 tests
"""

import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.generate_caim_reports import (
    CAIM_VERSION,
    SCORING_WEIGHTS,
    generate_agency_influence_report_md,
    generate_icm_explanation_md,
    get_utc_timestamp,
)


class TestGetUtcTimestamp:
    """Tests for get_utc_timestamp function."""

    def test_returns_string(self):
        """Test timestamp is a string."""
        result = get_utc_timestamp()
        assert isinstance(result, str)

    def test_iso_format(self):
        """Test timestamp is in ISO format."""
        result = get_utc_timestamp()
        # Should be parseable as datetime
        assert "T" in result
        assert result.endswith("Z")

    def test_contains_date(self):
        """Test timestamp contains current date."""
        result = get_utc_timestamp()
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in result


class TestScoringWeights:
    """Tests for SCORING_WEIGHTS constant."""

    def test_weights_exist(self):
        """Test all expected weights exist."""
        assert "vendor_overlap" in SCORING_WEIGHTS
        assert "tech_stack" in SCORING_WEIGHTS
        assert "contract_flow_sync" in SCORING_WEIGHTS
        assert "ace_anomaly_linkage" in SCORING_WEIGHTS
        assert "programmatic_continuity" in SCORING_WEIGHTS

    def test_weights_sum_to_one(self):
        """Test weights sum to 1.0."""
        total = sum(SCORING_WEIGHTS.values())
        assert total == 1.0

    def test_weight_values(self):
        """Test individual weight values."""
        assert SCORING_WEIGHTS["vendor_overlap"] == 0.25
        assert SCORING_WEIGHTS["tech_stack"] == 0.20
        assert SCORING_WEIGHTS["contract_flow_sync"] == 0.20
        assert SCORING_WEIGHTS["ace_anomaly_linkage"] == 0.20
        assert SCORING_WEIGHTS["programmatic_continuity"] == 0.15


class TestGenerateAgencyInfluenceReportMd:
    """Tests for generate_agency_influence_report_md function."""

    def test_report_has_title(self):
        """Test report includes title."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert "# Agency Influence Report" in result

    def test_report_has_version(self):
        """Test report includes version."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert CAIM_VERSION in result

    def test_report_has_executive_summary(self):
        """Test report includes executive summary."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert "## Executive Summary" in result

    def test_report_includes_agencies(self):
        """Test report includes agency data."""
        agency_data = {
            "agency_index": {
                "City Council": {
                    "name": "City Council",
                    "type": "municipal",
                    "appearance_count": 10,
                    "year_span": 5,
                    "years": ["2020", "2021"],
                }
            },
            "summary": {"unique_agencies": 1},
        }
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert "City Council" in result
        assert "municipal" in result

    def test_report_includes_high_correlation_pairs(self):
        """Test report includes high correlation pairs."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {
            "summary": {},
            "high_correlation_pairs": [
                {
                    "agency_a": "Agency A",
                    "agency_b": "Agency B",
                    "correlation_score": 0.75,
                    "tier": "High",
                }
            ],
        }

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert "Agency A" in result
        assert "Agency B" in result

    def test_report_includes_statistics(self):
        """Test report includes matrix statistics."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {
            "summary": {
                "statistics": {
                    "mean": 0.5,
                    "max": 0.8,
                }
            },
            "high_correlation_pairs": [],
        }

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        assert "Matrix Statistics" in result


class TestGenerateIcmExplanationMd:
    """Tests for generate_icm_explanation_md function."""

    def test_explanation_has_title(self):
        """Test explanation includes title."""
        result = generate_icm_explanation_md()
        assert "# Interdepartmental Correlation Matrix" in result

    def test_explanation_has_version(self):
        """Test explanation includes version."""
        result = generate_icm_explanation_md()
        assert CAIM_VERSION in result

    def test_explanation_has_formula(self):
        """Test explanation includes scoring formula."""
        result = generate_icm_explanation_md()
        assert "VendorOverlap" in result
        assert "TechStack" in result
        assert "0.25" in result

    def test_explanation_has_component_descriptions(self):
        """Test explanation includes component descriptions."""
        result = generate_icm_explanation_md()
        assert "Vendor Overlap" in result
        assert "Technology Stack" in result
        assert "Contract Flow Sync" in result
        assert "ACE Anomaly Linkage" in result
        assert "Programmatic Continuity" in result

    def test_explanation_has_tier_table(self):
        """Test explanation includes tier table."""
        result = generate_icm_explanation_md()
        assert "Critical" in result
        assert "High" in result
        assert "Moderate" in result
        assert "Low" in result
        assert "Minimal" in result

    def test_explanation_has_limitations(self):
        """Test explanation includes limitations section."""
        result = generate_icm_explanation_md()
        assert "Limitations" in result
        assert "Correlation" in result or "Causation" in result

    def test_explanation_has_usage_examples(self):
        """Test explanation includes usage examples."""
        result = generate_icm_explanation_md()
        assert "Usage Examples" in result or "Examples" in result


class TestCaImVersion:
    """Tests for CAIM version constant."""

    def test_version_format(self):
        """Test version has correct format."""
        assert isinstance(CAIM_VERSION, str)
        assert "." in CAIM_VERSION

    def test_version_value(self):
        """Test version value."""
        assert CAIM_VERSION == "1.0"


class TestReportFormatting:
    """Tests for report formatting consistency."""

    def test_agency_report_markdown_format(self):
        """Test agency report uses valid markdown."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        result = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )

        # Should have markdown elements
        assert result.count("#") > 0  # Has headers
        assert "---" in result  # Has horizontal rules

    def test_icm_explanation_markdown_format(self):
        """Test ICM explanation uses valid markdown."""
        result = generate_icm_explanation_md()

        # Should have markdown elements
        assert result.count("#") > 0  # Has headers
        assert "|" in result  # Has tables
        assert "```" in result  # Has code blocks

    def test_reports_end_with_generator_credit(self):
        """Test reports end with generator credit."""
        agency_data = {"agency_index": {}, "summary": {}}
        caim_result = {"graph": {}}
        icm_result = {"summary": {}, "high_correlation_pairs": []}

        report = generate_agency_influence_report_md(
            agency_data, caim_result, icm_result
        )
        explanation = generate_icm_explanation_md()

        assert "CAIM-ICM" in report or "CAIM" in report
        assert "CAIM-ICM" in explanation or "CAIM" in explanation
