#!/usr/bin/env python3
"""Tests for ICM matrix generation functionality.

This module tests the interdepartmental_matrix.py functions.
Total: 34 tests
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from scripts.interdepartmental_matrix import (
    WEIGHT_ACE_ANOMALY_LINKAGE,
    WEIGHT_CONTRACT_FLOW_SYNC,
    WEIGHT_PROGRAMMATIC_CONTINUITY,
    WEIGHT_TECH_STACK,
    WEIGHT_VENDOR_OVERLAP,
    build_agency_maps,
    build_correlation_matrix,
    calculate_icm_score,
    calculate_jaccard_similarity,
    calculate_matrix_statistics,
    categorize_correlation,
    generate_influence_matrix_csv,
    generate_matrix_numpy_format,
    identify_high_correlation_pairs,
)


class TestCalculateJaccardSimilarity:
    """Tests for calculate_jaccard_similarity function."""

    def test_identical_sets(self):
        """Test similarity of identical sets."""
        set_a = {"a", "b", "c"}
        set_b = {"a", "b", "c"}
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 1.0

    def test_disjoint_sets(self):
        """Test similarity of disjoint sets."""
        set_a = {"a", "b"}
        set_b = {"c", "d"}
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 0.0

    def test_partial_overlap(self):
        """Test similarity with partial overlap."""
        set_a = {"a", "b", "c"}
        set_b = {"b", "c", "d"}
        # Intersection: {b, c} = 2
        # Union: {a, b, c, d} = 4
        # Jaccard: 2/4 = 0.5
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 0.5

    def test_empty_set_a(self):
        """Test similarity with empty first set."""
        set_a = set()
        set_b = {"a", "b"}
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 0.0

    def test_empty_set_b(self):
        """Test similarity with empty second set."""
        set_a = {"a", "b"}
        set_b = set()
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 0.0

    def test_both_empty(self):
        """Test similarity with both sets empty."""
        set_a = set()
        set_b = set()
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 0.0

    def test_single_element_match(self):
        """Test similarity with single matching element."""
        set_a = {"a"}
        set_b = {"a"}
        result = calculate_jaccard_similarity(set_a, set_b)
        assert result == 1.0


class TestBuildAgencyMaps:
    """Tests for build_agency_maps function."""

    def test_basic_maps(self):
        """Test basic agency map building."""
        agency_index = {
            "City Council": {
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
            }
        }
        vendor_map, tech_map, years_map, hist_map, anomaly_map = build_agency_maps(
            agency_index, None, None
        )

        assert "City Council" in hist_map
        assert "HIST-1234" in hist_map["City Council"]
        assert "2020" in years_map["City Council"]

    def test_empty_agency_index(self):
        """Test with empty agency index."""
        vendor_map, tech_map, years_map, hist_map, anomaly_map = build_agency_maps(
            {}, None, None
        )
        assert len(vendor_map) == 0
        assert len(tech_map) == 0
        assert len(years_map) == 0
        assert len(hist_map) == 0
        assert len(anomaly_map) == 0


class TestCalculateIcmScore:
    """Tests for calculate_icm_score function."""

    def test_self_correlation(self):
        """Test that agencies have high self-correlation components."""
        vendor_map = {"Agency A": {"Vendor1"}}
        tech_map = {"Agency A": {"ALPR"}}
        years_map = {"Agency A": {"2020"}}
        hist_map = {"Agency A": {"HIST-1234"}}
        anomaly_map = {"Agency A": set()}

        result = calculate_icm_score(
            "Agency A",
            "Agency A",
            vendor_map,
            tech_map,
            years_map,
            hist_map,
            anomaly_map,
        )

        # Self-similarity should be high for non-empty sets
        assert result["vendor_overlap"] == 1.0
        assert result["tech_stack"] == 1.0

    def test_different_agencies(self):
        """Test score between different agencies."""
        vendor_map = {"Agency A": {"Vendor1"}, "Agency B": {"Vendor2"}}
        tech_map = {"Agency A": {"ALPR"}, "Agency B": {"BWC"}}
        years_map = {"Agency A": {"2020"}, "Agency B": {"2021"}}
        hist_map = {"Agency A": {"HIST-1234"}, "Agency B": {"HIST-5678"}}
        anomaly_map = {"Agency A": set(), "Agency B": set()}

        result = calculate_icm_score(
            "Agency A",
            "Agency B",
            vendor_map,
            tech_map,
            years_map,
            hist_map,
            anomaly_map,
        )

        assert result["vendor_overlap"] == 0.0
        assert result["tech_stack"] == 0.0
        assert result["total_score"] == 0.0

    def test_score_components(self):
        """Test that all score components are present."""
        vendor_map = {"A": set(), "B": set()}
        tech_map = {"A": set(), "B": set()}
        years_map = {"A": set(), "B": set()}
        hist_map = {"A": set(), "B": set()}
        anomaly_map = {"A": set(), "B": set()}

        result = calculate_icm_score(
            "A", "B", vendor_map, tech_map, years_map, hist_map, anomaly_map
        )

        assert "vendor_overlap" in result
        assert "tech_stack" in result
        assert "contract_flow_sync" in result
        assert "ace_anomaly_linkage" in result
        assert "programmatic_continuity" in result
        assert "total_score" in result


class TestBuildCorrelationMatrix:
    """Tests for build_correlation_matrix function."""

    def test_empty_matrix(self):
        """Test building matrix with empty input."""
        agency_names, matrix, detailed = build_correlation_matrix({}, None, None)
        assert len(agency_names) == 0
        assert len(matrix) == 0

    def test_single_agency_matrix(self):
        """Test building matrix with single agency."""
        agency_index = {
            "City Council": {
                "hist_ids": ["HIST-1234"],
                "years": ["2020"],
            }
        }
        agency_names, matrix, detailed = build_correlation_matrix(
            agency_index, None, None
        )

        assert len(agency_names) == 1
        assert agency_names[0] == "City Council"
        assert matrix[0][0] == 1.0  # Self-correlation

    def test_two_agency_matrix(self):
        """Test building matrix with two agencies."""
        agency_index = {
            "Agency A": {"hist_ids": ["HIST-1234"], "years": ["2020"]},
            "Agency B": {"hist_ids": ["HIST-5678"], "years": ["2021"]},
        }
        agency_names, matrix, detailed = build_correlation_matrix(
            agency_index, None, None
        )

        assert len(agency_names) == 2
        assert len(matrix) == 2
        assert len(matrix[0]) == 2
        # Diagonal should be 1.0
        assert matrix[0][0] == 1.0
        assert matrix[1][1] == 1.0

    def test_matrix_symmetry(self):
        """Test that matrix is symmetric."""
        agency_index = {
            "Agency A": {"hist_ids": ["HIST-1234"], "years": ["2020"]},
            "Agency B": {"hist_ids": ["HIST-1234"], "years": ["2020"]},
        }
        agency_names, matrix, detailed = build_correlation_matrix(
            agency_index, None, None
        )

        # matrix[0][1] should equal matrix[1][0]
        assert matrix[0][1] == matrix[1][0]


class TestGenerateInfluenceMatrixCsv:
    """Tests for generate_influence_matrix_csv function."""

    def test_csv_headers(self):
        """Test CSV includes proper headers."""
        agency_names = ["Agency A", "Agency B"]
        matrix = [[1.0, 0.5], [0.5, 1.0]]

        rows = generate_influence_matrix_csv(agency_names, matrix)

        assert rows[0][0] == "Agency"
        assert rows[0][1] == "Agency A"
        assert rows[0][2] == "Agency B"

    def test_csv_data_rows(self):
        """Test CSV includes data rows."""
        agency_names = ["Agency A", "Agency B"]
        matrix = [[1.0, 0.5], [0.5, 1.0]]

        rows = generate_influence_matrix_csv(agency_names, matrix)

        assert len(rows) == 3  # Header + 2 data rows
        assert rows[1][0] == "Agency A"
        assert rows[2][0] == "Agency B"


class TestGenerateMatrixNumpyFormat:
    """Tests for generate_matrix_numpy_format function."""

    def test_numpy_format_structure(self):
        """Test NumPy format has correct structure."""
        agency_names = ["Agency A", "Agency B"]
        matrix = [[1.0, 0.5], [0.5, 1.0]]

        result = generate_matrix_numpy_format(agency_names, matrix)

        assert "agency_names" in result
        assert "matrix" in result
        assert "shape" in result
        assert "dtype" in result

    def test_numpy_format_shape(self):
        """Test NumPy format has correct shape."""
        agency_names = ["A", "B", "C"]
        matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

        result = generate_matrix_numpy_format(agency_names, matrix)

        assert result["shape"] == [3, 3]


class TestIdentifyHighCorrelationPairs:
    """Tests for identify_high_correlation_pairs function."""

    def test_above_threshold(self):
        """Test identifying pairs above threshold."""
        agency_names = ["A", "B"]
        matrix = [[1.0, 0.5], [0.5, 1.0]]

        pairs = identify_high_correlation_pairs(agency_names, matrix, threshold=0.3)

        assert len(pairs) == 1
        assert pairs[0]["agency_a"] == "A"
        assert pairs[0]["agency_b"] == "B"
        assert pairs[0]["correlation_score"] == 0.5

    def test_below_threshold(self):
        """Test no pairs below threshold."""
        agency_names = ["A", "B"]
        matrix = [[1.0, 0.1], [0.1, 1.0]]

        pairs = identify_high_correlation_pairs(agency_names, matrix, threshold=0.3)

        assert len(pairs) == 0

    def test_sorted_by_score(self):
        """Test pairs are sorted by score descending."""
        agency_names = ["A", "B", "C"]
        matrix = [
            [1.0, 0.3, 0.8],
            [0.3, 1.0, 0.5],
            [0.8, 0.5, 1.0],
        ]

        pairs = identify_high_correlation_pairs(agency_names, matrix, threshold=0.2)

        # Should be sorted by score: (A,C)=0.8, (B,C)=0.5, (A,B)=0.3
        assert pairs[0]["correlation_score"] == 0.8
        assert pairs[1]["correlation_score"] == 0.5


class TestCategorizeCorrelation:
    """Tests for categorize_correlation function."""

    def test_critical_tier(self):
        """Test critical tier classification."""
        assert categorize_correlation(0.85) == "Critical"
        assert categorize_correlation(0.80) == "Critical"
        assert categorize_correlation(1.0) == "Critical"

    def test_high_tier(self):
        """Test high tier classification."""
        assert categorize_correlation(0.65) == "High"
        assert categorize_correlation(0.79) == "High"

    def test_moderate_tier(self):
        """Test moderate tier classification."""
        assert categorize_correlation(0.45) == "Moderate"
        assert categorize_correlation(0.59) == "Moderate"

    def test_low_tier(self):
        """Test low tier classification."""
        assert categorize_correlation(0.25) == "Low"
        assert categorize_correlation(0.39) == "Low"

    def test_minimal_tier(self):
        """Test minimal tier classification."""
        assert categorize_correlation(0.1) == "Minimal"
        assert categorize_correlation(0.0) == "Minimal"


class TestCalculateMatrixStatistics:
    """Tests for calculate_matrix_statistics function."""

    def test_empty_matrix(self):
        """Test statistics for empty matrix."""
        stats = calculate_matrix_statistics([])

        assert stats["mean"] == 0.0
        assert stats["max"] == 0.0
        assert stats["min"] == 0.0
        assert stats["density"] == 0.0

    def test_single_element_matrix(self):
        """Test statistics for single element matrix."""
        matrix = [[1.0]]
        stats = calculate_matrix_statistics(matrix)

        # No off-diagonal elements
        assert stats["mean"] == 0.0

    def test_two_by_two_matrix(self):
        """Test statistics for 2x2 matrix."""
        matrix = [[1.0, 0.5], [0.5, 1.0]]
        stats = calculate_matrix_statistics(matrix)

        # Off-diagonal values are both 0.5
        assert stats["mean"] == 0.5
        assert stats["max"] == 0.5
        assert stats["min"] == 0.5
        assert stats["density"] == 1.0  # Both non-zero

    def test_sparse_matrix(self):
        """Test statistics for sparse matrix."""
        matrix = [[1.0, 0.0], [0.0, 1.0]]
        stats = calculate_matrix_statistics(matrix)

        # Off-diagonal values are both 0.0
        assert stats["mean"] == 0.0
        assert stats["density"] == 0.0


class TestIcmWeights:
    """Tests for ICM weight constants."""

    def test_weights_sum_to_one(self):
        """Test that all weights sum to 1.0."""
        total = (
            WEIGHT_VENDOR_OVERLAP
            + WEIGHT_TECH_STACK
            + WEIGHT_CONTRACT_FLOW_SYNC
            + WEIGHT_ACE_ANOMALY_LINKAGE
            + WEIGHT_PROGRAMMATIC_CONTINUITY
        )
        assert total == 1.0

    def test_weight_values(self):
        """Test individual weight values match spec."""
        assert WEIGHT_VENDOR_OVERLAP == 0.25
        assert WEIGHT_TECH_STACK == 0.20
        assert WEIGHT_CONTRACT_FLOW_SYNC == 0.20
        assert WEIGHT_ACE_ANOMALY_LINKAGE == 0.20
        assert WEIGHT_PROGRAMMATIC_CONTINUITY == 0.15
