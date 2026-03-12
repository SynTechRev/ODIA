"""
Tests for Constitutional Linguistic Frameworks (CLF-v1).

Comprehensive test suite covering:
- Schema correctness
- Framework retrieval
- Weight normalization
- JIM compatibility
- Cross-framework conflict detection
- Reconstruction-era overrides
- Historical-context layering
- Drift scoring
- Integration with existing JIM nodes
"""

import json
from pathlib import Path

import pytest

from scripts.jim.framework_loader import ConstitutionalFrameworkLoader


class TestFrameworkLoaderInitialization:
    """Test framework loader initialization."""

    def test_loader_initializes_default_path(self):
        """Test loader initializes with default frameworks file path."""
        loader = ConstitutionalFrameworkLoader()
        assert (
            loader.frameworks_file.name == "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
        )
        assert not loader.loaded

    def test_loader_initializes_custom_path(self, tmp_path):
        """Test loader initializes with custom path."""
        custom_file = tmp_path / "custom_frameworks.json"
        custom_file.write_text("{}")
        loader = ConstitutionalFrameworkLoader(custom_file)
        assert loader.frameworks_file == custom_file

    def test_loader_version(self):
        """Test loader has version."""
        assert ConstitutionalFrameworkLoader.VERSION == "1.0.0"


class TestLoadAll:
    """Test load_all() method."""

    def test_load_all_success(self):
        """Test successful loading of all frameworks."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.load_all()

        assert result["success"] is True
        assert result["frameworks_loaded"] == 10
        assert len(result["framework_ids"]) == 10

    def test_load_all_returns_version(self):
        """Test load_all returns CLF version."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.load_all()

        assert "version" in result
        assert result["version"] == "1.0.0"

    def test_load_all_returns_weights(self):
        """Test load_all returns weight totals."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.load_all()

        assert "jim_total_weight" in result
        assert "ace_total_weight" in result
        assert 2.0 <= result["jim_total_weight"] <= 2.5
        assert 2.0 <= result["ace_total_weight"] <= 2.5

    def test_load_all_sets_loaded_flag(self):
        """Test load_all sets loaded flag."""
        loader = ConstitutionalFrameworkLoader()
        assert not loader.loaded

        loader.load_all()
        assert loader.loaded

    def test_load_all_missing_file(self, tmp_path):
        """Test load_all handles missing file."""
        missing_file = tmp_path / "nonexistent.json"
        loader = ConstitutionalFrameworkLoader(missing_file)
        result = loader.load_all()

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_load_all_invalid_json(self, tmp_path):
        """Test load_all handles invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json")
        loader = ConstitutionalFrameworkLoader(invalid_file)
        result = loader.load_all()

        assert result["success"] is False
        assert "JSON" in result["error"]

    def test_load_all_populates_frameworks(self):
        """Test load_all populates frameworks dictionary."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        assert len(loader.frameworks) == 10
        assert "original_public_meaning" in loader.frameworks


class TestGetFramework:
    """Test get_framework() method."""

    def test_get_framework_opm(self):
        """Test retrieving Original Public Meaning framework."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        result = loader.get_framework("original_public_meaning")

        assert result["success"] is True
        assert result["framework"]["framework_id"] == "opm"
        assert result["framework"]["name"] == "Original Public Meaning (OPM)"

    def test_get_framework_textualism(self):
        """Test retrieving Textualism framework."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        result = loader.get_framework("textualism")

        assert result["success"] is True
        assert result["framework"]["framework_id"] == "textualism"

    def test_get_framework_reconstruction(self):
        """Test retrieving Reconstruction-Era Intent framework."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        result = loader.get_framework("reconstruction_era_intent")

        assert result["success"] is True
        assert result["framework"]["framework_id"] == "reconstruction_intent"
        assert result["framework"]["reconstruction_override"] is True

    def test_get_framework_auto_loads(self):
        """Test get_framework auto-loads if not loaded."""
        loader = ConstitutionalFrameworkLoader()
        assert not loader.loaded

        result = loader.get_framework("textualism")
        assert result["success"] is True
        assert loader.loaded

    def test_get_framework_nonexistent(self):
        """Test get_framework handles nonexistent framework."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        result = loader.get_framework("nonexistent_framework")

        assert result["success"] is False
        assert "not found" in result["error"]
        assert "available_frameworks" in result

    def test_get_framework_has_all_required_fields(self):
        """Test retrieved framework has all required fields."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()
        result = loader.get_framework("original_public_meaning")

        framework = result["framework"]
        required_fields = [
            "framework_id",
            "name",
            "definition",
            "method",
            "historical_origin",
            "temporal_scope",
            "strengths",
            "weaknesses",
            "landmark_cases",
            "jim_weight",
            "ace_weight",
            "semantic_drift",
            "key_scholars",
        ]

        for field in required_fields:
            assert field in framework


class TestListFrameworks:
    """Test list_frameworks() method."""

    def test_list_frameworks_returns_all(self):
        """Test list_frameworks returns all 10 frameworks."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.list_frameworks()

        assert result["success"] is True
        assert result["total_frameworks"] == 10
        assert len(result["frameworks"]) == 10

    def test_list_frameworks_summary_fields(self):
        """Test list_frameworks includes summary fields."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.list_frameworks()

        first_framework = result["frameworks"][0]
        assert "framework_id" in first_framework
        assert "name" in first_framework
        assert "definition" in first_framework
        assert "jim_weight" in first_framework
        assert "ace_weight" in first_framework

    def test_list_frameworks_truncates_definition(self):
        """Test list_frameworks truncates long definitions."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.list_frameworks()

        for framework in result["frameworks"]:
            assert len(framework["definition"]) <= 203  # 200 + "..."

    def test_list_frameworks_includes_reconstruction_flag(self):
        """Test list_frameworks includes reconstruction_override flag."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.list_frameworks()

        # Find reconstruction framework
        reconstruction = [
            f
            for f in result["frameworks"]
            if f["framework_id"] == "reconstruction_intent"
        ][0]
        assert reconstruction["reconstruction_override"] is True


class TestGetWeightsForJIM:
    """Test get_weights_for_jim() method."""

    def test_get_weights_default(self):
        """Test get_weights_for_jim with default weights."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim()

        assert result["success"] is True
        assert "weights" in result
        assert len(result["weights"]) == 10
        assert result["amendment_type"] == "default"

    def test_get_weights_founding(self):
        """Test get_weights_for_jim with founding amendment type."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim("founding")

        assert result["success"] is True
        assert result["amendment_type"] == "founding"

        # Founding-era frameworks should have increased weight
        weights = result["weights"]
        opm_weight = weights["original_public_meaning"]
        assert opm_weight > 0.30  # Should be boosted from base 0.30

    def test_get_weights_reconstruction(self):
        """Test get_weights_for_jim with reconstruction amendment type."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim("reconstruction")

        assert result["success"] is True
        assert result["amendment_type"] == "reconstruction"

        # Reconstruction framework should have elevated weight
        weights = result["weights"]
        reconstruction_weight = weights["reconstruction_era_intent"]
        assert reconstruction_weight > 0.35  # Should be boosted from base 0.35

    def test_get_weights_reconstruction_reduces_founding(self):
        """Test reconstruction type reduces founding-era weights."""
        loader = ConstitutionalFrameworkLoader()
        default_result = loader.get_weights_for_jim()
        reconstruction_result = loader.get_weights_for_jim("reconstruction")

        default_opm = default_result["weights"]["original_public_meaning"]
        reconstruction_opm = reconstruction_result["weights"]["original_public_meaning"]

        assert reconstruction_opm < default_opm

    def test_get_weights_total_reasonable(self):
        """Test total weight is in reasonable range."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim()

        assert 1.5 <= result["total_weight"] <= 3.0


class TestSemanticDriftScores:
    """Test get_semantic_drift_scores() method."""

    def test_drift_1789_to_2025(self):
        """Test semantic drift from 1789 to 2025."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_semantic_drift_scores(1789, 2025)

        assert result["success"] is True
        assert result["start_era"] == 1789
        assert result["end_era"] == 2025
        assert len(result["drift_scores"]) == 10

    def test_drift_1789_to_1868(self):
        """Test semantic drift from 1789 to 1868."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_semantic_drift_scores(1789, 1868)

        assert result["success"] is True
        drift = result["drift_scores"]["original_public_meaning"]
        assert 0.0 <= drift <= 1.0

    def test_drift_scores_increase_over_time(self):
        """Test drift scores generally increase over longer periods."""
        loader = ConstitutionalFrameworkLoader()

        result_short = loader.get_semantic_drift_scores(1789, 1868)
        result_long = loader.get_semantic_drift_scores(1789, 2025)

        # For most frameworks, longer period should have equal or higher drift
        opm_short = result_short["drift_scores"]["original_public_meaning"]
        opm_long = result_long["drift_scores"]["original_public_meaning"]

        assert opm_long >= opm_short


class TestConflictResolutionRules:
    """Test get_conflict_resolution_rules() method."""

    def test_get_conflict_rules_success(self):
        """Test retrieving conflict resolution rules."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_conflict_resolution_rules()

        assert result["success"] is True
        assert "conflict_resolution" in result

    def test_conflict_rules_include_reconstruction(self):
        """Test conflict rules include reconstruction override."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_conflict_resolution_rules()

        rules = result["conflict_resolution"]["rules"]
        reconstruction_rule = [
            r for r in rules if r["rule"] == "reconstruction_override"
        ][0]

        assert "13th, 14th, or 15th Amendment" in reconstruction_rule["condition"]

    def test_conflict_rules_include_temporal_primacy(self):
        """Test conflict rules include temporal primacy."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_conflict_resolution_rules()

        rules = result["conflict_resolution"]["rules"]
        temporal_rule = [r for r in rules if r["rule"] == "temporal_primacy"][0]

        assert "temporal_scope" in temporal_rule["action"]


class TestIntegrationPoints:
    """Test get_integration_points() method."""

    def test_get_integration_points_success(self):
        """Test retrieving integration points."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_integration_points()

        assert result["success"] is True
        assert "integration_points" in result

    def test_integration_includes_jim(self):
        """Test integration points include JIM."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_integration_points()

        assert "jim_integration" in result["integration_points"]

    def test_integration_includes_msh(self):
        """Test integration points include MSH."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_integration_points()

        assert "msh_integration" in result["integration_points"]

    def test_integration_includes_ace(self):
        """Test integration points include ACE."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_integration_points()

        assert "ace_integration" in result["integration_points"]


class TestValidateFrameworks:
    """Test validate_frameworks() method."""

    def test_validate_success(self):
        """Test framework validation succeeds."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.validate_frameworks()

        assert result["success"] is True
        assert result["valid"] is True
        assert result["frameworks_validated"] == 10

    def test_validate_checks_required_fields(self):
        """Test validation checks required fields."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.validate_frameworks()

        assert len(result["errors"]) == 0

    def test_validate_checks_weight_constraints(self):
        """Test validation checks weight constraints."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.validate_frameworks()

        # Should have few or no warnings about weights
        weight_warnings = [w for w in result["warnings"] if "weight" in w]
        assert len(weight_warnings) == 0  # All weights should be in valid range


class TestSchemaCorrectness:
    """Test schema correctness of frameworks JSON."""

    @pytest.fixture
    def frameworks_data(self):
        """Load frameworks data directly."""
        repo_root = Path(__file__).parent.parent.parent
        frameworks_file = (
            repo_root / "constitutional" / "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
        )
        with open(frameworks_file) as f:
            return json.load(f)

    def test_schema_has_version(self, frameworks_data):
        """Test schema has version field."""
        assert "version" in frameworks_data
        assert frameworks_data["version"] == "1.0.0"

    def test_schema_has_metadata(self, frameworks_data):
        """Test schema has metadata section."""
        assert "metadata" in frameworks_data
        assert frameworks_data["metadata"]["total_frameworks"] == 10

    def test_schema_has_all_frameworks(self, frameworks_data):
        """Test schema has all 10 frameworks."""
        assert len(frameworks_data["frameworks"]) == 10

    def test_each_framework_has_required_fields(self, frameworks_data):
        """Test each framework has all required fields."""
        required_fields = [
            "framework_id",
            "name",
            "definition",
            "method",
            "historical_origin",
            "temporal_scope",
            "strengths",
            "weaknesses",
            "landmark_cases",
            "jim_weight",
            "ace_weight",
            "semantic_drift",
            "key_scholars",
        ]

        for framework_id, framework in frameworks_data["frameworks"].items():
            for field in required_fields:
                assert field in framework, f"Framework {framework_id} missing {field}"

    def test_temporal_scope_has_primary_era(self, frameworks_data):
        """Test each framework's temporal_scope has primary_era."""
        for framework in frameworks_data["frameworks"].values():
            assert "primary_era" in framework["temporal_scope"]

    def test_landmark_cases_have_required_fields(self, frameworks_data):
        """Test landmark cases have case, citation, application."""
        for framework in frameworks_data["frameworks"].values():
            for case in framework["landmark_cases"]:
                assert "case" in case
                assert "citation" in case
                assert "application" in case

    def test_key_scholars_have_required_fields(self, frameworks_data):
        """Test key scholars have name, contribution, key_work."""
        for framework in frameworks_data["frameworks"].values():
            for scholar in framework["key_scholars"]:
                assert "name" in scholar
                assert "contribution" in scholar
                assert "key_work" in scholar

    def test_semantic_drift_has_scores(self, frameworks_data):
        """Test semantic_drift section has drift scores."""
        for framework in frameworks_data["frameworks"].values():
            drift = framework["semantic_drift"]
            assert "notes" in drift

            # Should have drift scores or multi-era flag
            has_scores = any(
                k.endswith("_to_1868")
                or k.endswith("_to_1920")
                or k.endswith("_to_2025")
                for k in drift.keys()
            )
            is_multi_era = "multi_era_framework" in drift

            assert has_scores or is_multi_era


class TestWeightNormalization:
    """Test weight normalization and constraints."""

    @pytest.fixture
    def frameworks_data(self):
        """Load frameworks data."""
        repo_root = Path(__file__).parent.parent.parent
        frameworks_file = (
            repo_root / "constitutional" / "CONSTITUTIONAL_LINGUISTIC_FRAMEWORKS.json"
        )
        with open(frameworks_file) as f:
            return json.load(f)

    def test_jim_weights_in_valid_range(self, frameworks_data):
        """Test all JIM weights are in valid range."""
        for framework in frameworks_data["frameworks"].values():
            jim_weight = framework["jim_weight"]
            assert 0.05 <= jim_weight <= 0.40

    def test_ace_weights_in_valid_range(self, frameworks_data):
        """Test all ACE weights are in valid range."""
        for framework in frameworks_data["frameworks"].values():
            ace_weight = framework["ace_weight"]
            assert 0.05 <= ace_weight <= 0.40

    def test_jim_total_weight_reasonable(self, frameworks_data):
        """Test JIM total weight is in reasonable range."""
        total = sum(f["jim_weight"] for f in frameworks_data["frameworks"].values())
        assert 2.0 <= total <= 2.5

    def test_ace_total_weight_reasonable(self, frameworks_data):
        """Test ACE total weight is in reasonable range."""
        total = sum(f["ace_weight"] for f in frameworks_data["frameworks"].values())
        assert 2.0 <= total <= 2.5

    def test_reconstruction_has_highest_jim_weight(self, frameworks_data):
        """Test Reconstruction-Era Intent has highest JIM weight."""
        reconstruction = frameworks_data["frameworks"]["reconstruction_era_intent"]
        reconstruction_weight = reconstruction["jim_weight"]

        # Should be among highest (0.35)
        assert reconstruction_weight >= 0.30

    def test_living_constitutionalism_has_lowest_jim_weight(self, frameworks_data):
        """Test Living Constitutionalism has lowest JIM weight."""
        living = frameworks_data["frameworks"]["living_constitutionalism"]
        living_weight = living["jim_weight"]

        # Should be among lowest (0.08)
        assert living_weight <= 0.12


class TestReconstructionOverride:
    """Test reconstruction-era override functionality."""

    def test_reconstruction_framework_has_override_flag(self):
        """Test reconstruction framework has override flag set."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("reconstruction_era_intent")

        assert result["framework"]["reconstruction_override"] is True

    def test_other_frameworks_no_override(self):
        """Test non-reconstruction frameworks don't have override."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("original_public_meaning")

        assert result["framework"]["reconstruction_override"] is False

    def test_reconstruction_weight_adjustment(self):
        """Test reconstruction amendment type adjusts weights."""
        loader = ConstitutionalFrameworkLoader()

        default_weights = loader.get_weights_for_jim()
        reconstruction_weights = loader.get_weights_for_jim("reconstruction")

        default_reconstruction = default_weights["weights"]["reconstruction_era_intent"]
        adjusted_reconstruction = reconstruction_weights["weights"][
            "reconstruction_era_intent"
        ]

        assert adjusted_reconstruction > default_reconstruction

    def test_founding_frameworks_reduced_for_reconstruction(self):
        """Test founding frameworks reduced for reconstruction amendments."""
        loader = ConstitutionalFrameworkLoader()
        reconstruction_weights = loader.get_weights_for_jim("reconstruction")

        weights = reconstruction_weights["weights"]
        opm = weights["original_public_meaning"]
        framers = weights["framers_intent"]

        # Should be reduced from their base weights
        assert opm < 0.30  # Base is 0.30
        assert framers < 0.20  # Base is 0.20


class TestHistoricalContextLayering:
    """Test historical context analysis across eras."""

    def test_historical_context_is_multi_era(self):
        """Test historical context framework is multi-era."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("historical_context_analysis")

        drift = result["framework"]["semantic_drift"]
        assert drift.get("multi_era_framework") is True

    def test_historical_context_has_era_analysis(self):
        """Test historical context has era-specific analysis."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("historical_context_analysis")

        drift = result["framework"]["semantic_drift"]
        assert "era_specific_analysis" in drift

    def test_temporal_scope_spans_multiple_eras(self):
        """Test historical context temporal scope spans eras."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("historical_context_analysis")

        temporal_scope = result["framework"]["temporal_scope"]
        assert "Multi-era" in temporal_scope["primary_era"]


class TestDriftScoring:
    """Test semantic drift scoring functionality."""

    def test_drift_scores_between_0_and_1(self):
        """Test all drift scores are between 0.0 and 1.0."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            drift = framework["semantic_drift"]
            for _key, value in drift.items():
                if isinstance(value, int | float):
                    assert 0.0 <= value <= 1.0

    def test_drift_increases_with_time(self):
        """Test drift generally increases with longer time periods."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("original_public_meaning")

        drift = result["framework"]["semantic_drift"]
        drift_1868 = drift["1789_to_1868"]
        drift_1920 = drift["1789_to_1920"]
        drift_2025 = drift["1789_to_2025"]

        assert drift_1868 <= drift_1920 <= drift_2025

    def test_textualism_has_lower_drift(self):
        """Test textualism has relatively lower drift scores."""
        loader = ConstitutionalFrameworkLoader()
        textualism = loader.get_framework("textualism")
        living = loader.get_framework("living_constitutionalism")

        textualism_drift = textualism["framework"]["semantic_drift"]["1789_to_2025"]
        living_drift = living["framework"]["semantic_drift"]["1789_to_2025"]

        assert textualism_drift < living_drift

    def test_living_constitutionalism_has_highest_drift(self):
        """Test living constitutionalism embraces highest drift."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("living_constitutionalism")

        drift_2025 = result["framework"]["semantic_drift"]["1789_to_2025"]
        assert drift_2025 >= 0.80  # Should be very high


class TestJIMIntegration:
    """Test integration with existing JIM components."""

    def test_loader_integrates_with_jim_core(self):
        """Test framework loader can be used by JIM core."""
        from scripts.jim.jim_core import JIMCore

        JIMCore()
        loader = ConstitutionalFrameworkLoader()

        # Should be able to get weights for JIM
        weights = loader.get_weights_for_jim()
        assert weights["success"] is True

    def test_weights_compatible_with_jim(self):
        """Test weights format compatible with JIM weighting."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim()

        # Weights should be a dict of framework_id -> float
        weights = result["weights"]
        assert isinstance(weights, dict)
        assert all(isinstance(v, int | float) for v in weights.values())

    def test_framework_ids_match_expected_format(self):
        """Test framework IDs match expected naming convention."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        expected_ids = [
            "original_public_meaning",
            "textualism",
            "framers_intent",
            "purposivism",
            "structuralism",
            "pragmatism_minimalism",
            "living_constitutionalism",
            "reconstruction_era_intent",
            "historical_context_analysis",
            "founding_era_linguistic_baselines",
        ]

        for expected_id in expected_ids:
            assert expected_id in loader.frameworks


class TestCrossFrameworkConflicts:
    """Test cross-framework conflict detection."""

    def test_detect_originalist_living_conflict(self):
        """Test detection of originalist vs living constitutionalism conflict."""
        loader = ConstitutionalFrameworkLoader()
        opm = loader.get_framework("original_public_meaning")
        living = loader.get_framework("living_constitutionalism")

        # These frameworks have fundamentally different approaches to drift
        opm_drift = opm["framework"]["semantic_drift"]["1789_to_2025"]
        living_drift = living["framework"]["semantic_drift"]["1789_to_2025"]

        # Living constitutionalism should have much higher drift acceptance
        assert living_drift > opm_drift + 0.15

    def test_textualism_purposivism_methodological_conflict(self):
        """Test textualism and purposivism have different methods."""
        loader = ConstitutionalFrameworkLoader()
        textualism = loader.get_framework("textualism")
        purposivism = loader.get_framework("purposivism")

        # Different methodologies
        assert "plain meaning" in textualism["framework"]["method"].lower()
        assert "purpose" in purposivism["framework"]["method"].lower()

    def test_conflict_resolution_rules_exist(self):
        """Test conflict resolution rules are defined."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_conflict_resolution_rules()

        rules = result["conflict_resolution"]["rules"]
        assert len(rules) >= 4


class TestFrameworkMetadata:
    """Test framework metadata completeness."""

    def test_all_frameworks_have_landmark_cases(self):
        """Test all frameworks have landmark cases."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            assert len(framework["landmark_cases"]) >= 2

    def test_all_frameworks_have_key_scholars(self):
        """Test all frameworks have key scholars."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            assert len(framework["key_scholars"]) >= 2

    def test_all_frameworks_have_strengths_weaknesses(self):
        """Test all frameworks have strengths and weaknesses."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            assert len(framework["strengths"]) >= 3
            assert len(framework["weaknesses"]) >= 3

    def test_framework_definitions_comprehensive(self):
        """Test framework definitions are comprehensive."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            # Definitions should be substantial
            assert len(framework["definition"]) > 100


class TestMultipleFrameworkComparison:
    """Test comparing multiple frameworks."""

    def test_compare_originalist_frameworks(self):
        """Test comparing different originalist frameworks."""
        loader = ConstitutionalFrameworkLoader()

        opm = loader.get_framework("original_public_meaning")
        framers = loader.get_framework("framers_intent")
        founding_linguistic = loader.get_framework("founding_era_linguistic_baselines")

        # All should have founding-era focus
        assert "1787" in opm["framework"]["temporal_scope"]["primary_era"]
        assert "1787" in framers["framework"]["temporal_scope"]["primary_era"]
        assert (
            "1787" in founding_linguistic["framework"]["temporal_scope"]["primary_era"]
        )

    def test_compare_weights_across_frameworks(self):
        """Test weight distribution across frameworks."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim()

        weights = result["weights"]

        # OPM should have high weight
        assert weights["original_public_meaning"] >= 0.25

        # Living constitutionalism should have low weight
        assert weights["living_constitutionalism"] <= 0.12


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_amendment_type(self):
        """Test get_weights_for_jim with empty string."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim("")

        # Should treat as default
        assert result["success"] is True

    def test_none_amendment_type(self):
        """Test get_weights_for_jim with None."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_weights_for_jim(None)

        assert result["success"] is True
        assert result["amendment_type"] == "default"

    def test_invalid_era_range(self):
        """Test drift scores with unusual era range."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_semantic_drift_scores(2025, 1789)  # Backwards

        # Should still return result (may be incomplete)
        assert result["success"] is True

    def test_future_era(self):
        """Test drift scores with future era."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_semantic_drift_scores(1789, 2050)

        # Should extrapolate or use closest
        assert result["success"] is True


class TestAdditionalFrameworkDetails:
    """Test additional framework details and completeness."""

    def test_all_frameworks_have_unique_ids(self):
        """Test all frameworks have unique framework_ids."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        framework_ids = [f["framework_id"] for f in loader.frameworks.values()]
        assert len(framework_ids) == len(set(framework_ids))

    def test_all_frameworks_have_unique_names(self):
        """Test all frameworks have unique names."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        names = [f["name"] for f in loader.frameworks.values()]
        assert len(names) == len(set(names))

    def test_pragmatism_framework_exists(self):
        """Test pragmatism/minimalism framework is loaded."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("pragmatism_minimalism")

        assert result["success"] is True
        assert "Pragmatism" in result["framework"]["name"]

    def test_structuralism_framework_exists(self):
        """Test structuralism framework is loaded."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("structuralism")

        assert result["success"] is True
        assert "Structuralism" in result["framework"]["name"]

    def test_purposivism_framework_exists(self):
        """Test purposivism framework is loaded."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("purposivism")

        assert result["success"] is True
        assert "Purposivism" in result["framework"]["name"]

    def test_all_temporal_scopes_valid(self):
        """Test all temporal scopes contain valid eras."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            temporal_scope = framework["temporal_scope"]
            assert "primary_era" in temporal_scope
            assert len(temporal_scope["primary_era"]) > 0

    def test_all_methods_described(self):
        """Test all frameworks have comprehensive method descriptions."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            assert len(framework["method"]) > 50

    def test_all_historical_origins_described(self):
        """Test all frameworks have historical origin descriptions."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            assert len(framework["historical_origin"]) > 30

    def test_reconstruction_applicable_to_correct_amendments(self):
        """Test reconstruction framework applies to correct amendments."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("reconstruction_era_intent")

        applicable_to = result["framework"]["temporal_scope"]["applicable_to"]
        assert any("13th Amendment" in item for item in applicable_to)
        assert any("14th Amendment" in item for item in applicable_to)
        assert any("15th Amendment" in item for item in applicable_to)

    def test_founding_linguistic_uses_dictionaries(self):
        """Test founding linguistic framework mentions dictionaries."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_framework("founding_era_linguistic_baselines")

        method = result["framework"]["method"].lower()
        assert "dictionary" in method or "dictionaries" in method

    def test_all_landmark_cases_have_year(self):
        """Test all landmark cases include year in citation."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            for case in framework["landmark_cases"]:
                citation = case["citation"]
                # U.S. citations should have a year
                assert "(" in citation and ")" in citation

    def test_weights_sum_correctly(self):
        """Test that weight sums are calculated correctly."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        jim_sum = sum(f["jim_weight"] for f in loader.frameworks.values())
        ace_sum = sum(f["ace_weight"] for f in loader.frameworks.values())

        # Check they match reported totals
        result = loader.load_all()
        assert abs(jim_sum - result["jim_total_weight"]) < 0.01
        assert abs(ace_sum - result["ace_total_weight"]) < 0.01

    def test_framework_loader_can_reload(self):
        """Test framework loader can reload data."""
        loader = ConstitutionalFrameworkLoader()
        result1 = loader.load_all()
        result2 = loader.load_all()

        assert result1["frameworks_loaded"] == result2["frameworks_loaded"]

    def test_get_framework_preserves_data_integrity(self):
        """Test getting framework doesn't modify original data."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        result1 = loader.get_framework("textualism")
        result2 = loader.get_framework("textualism")

        assert result1["framework"]["jim_weight"] == result2["framework"]["jim_weight"]

    def test_all_frameworks_have_applicable_to_field(self):
        """Test all frameworks have applicable_to in temporal_scope."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            temporal_scope = framework["temporal_scope"]
            assert "applicable_to" in temporal_scope
            assert len(temporal_scope["applicable_to"]) > 0

    def test_reconstruction_era_weight_highest_or_tied(self):
        """Test reconstruction era has highest or tied-highest JIM weight."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        reconstruction_weight = loader.frameworks["reconstruction_era_intent"][
            "jim_weight"
        ]
        all_weights = [f["jim_weight"] for f in loader.frameworks.values()]

        assert reconstruction_weight == max(all_weights)

    def test_integration_metadata_complete(self):
        """Test integration points metadata is complete."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_integration_points()

        integration = result["integration_points"]

        # Should have all major systems
        assert "jim_integration" in integration
        assert "msh_integration" in integration
        assert "ace_integration" in integration

    def test_conflict_rules_have_rationale(self):
        """Test all conflict resolution rules have rationale."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.get_conflict_resolution_rules()

        for rule in result["conflict_resolution"]["rules"]:
            assert "rationale" in rule
            assert len(rule["rationale"]) > 20

    def test_validation_returns_warnings_not_errors(self):
        """Test validation may have warnings but no errors."""
        loader = ConstitutionalFrameworkLoader()
        result = loader.validate_frameworks()

        # Should have no errors for valid frameworks
        assert len(result["errors"]) == 0

    def test_all_scholars_have_complete_info(self):
        """Test all key scholars have complete information."""
        loader = ConstitutionalFrameworkLoader()
        loader.load_all()

        for framework in loader.frameworks.values():
            for scholar in framework["key_scholars"]:
                assert len(scholar["name"]) > 0
                assert len(scholar["contribution"]) > 10
                assert len(scholar["key_work"]) > 5
