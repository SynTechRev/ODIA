"""
Tests for CLEP-v1 Case Law Expansion - Risk Scoring with New Dimensions.
"""

import pytest

from scripts.jim.jim_risk_scoring import JIMRiskScoring


class TestCLEPv1RiskScoringWeights:
    """Test updated risk scoring weights for CLEP-v1."""

    def test_weights_include_new_dimensions(self):
        """Test weights include digital_privacy_risk and accountability_concern."""
        scorer = JIMRiskScoring()
        assert "digital_privacy_risk" in scorer.WEIGHTS
        assert "accountability_concern" in scorer.WEIGHTS

    def test_weights_sum_to_one(self):
        """Test all weights sum to approximately 1.0."""
        scorer = JIMRiskScoring()
        total_weight = sum(scorer.WEIGHTS.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_weight_values_valid_range(self):
        """Test all weight values are between 0 and 1."""
        scorer = JIMRiskScoring()
        for key, weight in scorer.WEIGHTS.items():
            assert 0.0 <= weight <= 1.0, f"Invalid weight for {key}: {weight}"


class TestDigitalPrivacyRiskScoring:
    """Test digital privacy risk scoring dimension."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_digital_privacy_with_location_tracking(self, scorer):
        """Test digital privacy score with location tracking."""
        anomaly = {"involves_location_tracking": True}
        linkage = {"doctrines": ["fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert "digital_privacy_risk" in result["component_scores"]
        assert result["component_scores"]["digital_privacy_risk"] > 0.0

    def test_digital_privacy_with_database_query(self, scorer):
        """Test digital privacy score with database query."""
        anomaly = {"database_query": True, "digital_search": True}
        linkage = {"doctrines": ["fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["digital_privacy_risk"] >= 0.2

    def test_digital_privacy_with_electronic_comms(self, scorer):
        """Test digital privacy score with electronic communications."""
        anomaly = {"electronic_communications": True}
        linkage = {"doctrines": ["fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["digital_privacy_risk"] > 0.0

    def test_digital_privacy_high_score_with_multiple_factors(self, scorer):
        """Test high digital privacy score with multiple factors."""
        anomaly = {
            "involves_location_tracking": True,
            "digital_search": True,
            "electronic_communications": True,
        }
        linkage = {
            "doctrines": ["fourth_amendment"],
            "relevant_cases": [
                {
                    "case_id": "carpenter_v_us_2018",
                    "name": "Carpenter v. United States",
                },
                {"case_id": "riley_v_california_2014", "name": "Riley v. California"},
            ],
        }

        result = scorer.score_anomaly(anomaly, linkage)
        # Should score high with multiple digital privacy factors
        assert result["component_scores"]["digital_privacy_risk"] >= 0.5

    def test_digital_privacy_zero_without_factors(self, scorer):
        """Test digital privacy scores zero without relevant factors."""
        anomaly = {"lacks_reasoning": True}  # Non-digital issue
        linkage = {"doctrines": ["administrative_law"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["digital_privacy_risk"] == 0.0


class TestAccountabilityConcernScoring:
    """Test accountability concern scoring dimension."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_accountability_with_use_of_force(self, scorer):
        """Test accountability score with use of force."""
        anomaly = {"involves_force": True}
        linkage = {"doctrines": ["constitutional_torts"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert "accountability_concern" in result["component_scores"]
        assert result["component_scores"]["accountability_concern"] > 0.0

    def test_accountability_with_deadly_force(self, scorer):
        """Test accountability score with deadly force."""
        anomaly = {"involves_force": True, "deadly_force": True}
        linkage = {"doctrines": ["constitutional_torts", "fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        # Deadly force should score higher
        assert result["component_scores"]["accountability_concern"] >= 0.5

    def test_accountability_with_qualified_immunity(self, scorer):
        """Test accountability score with qualified immunity."""
        anomaly = {"qualified_immunity_applicable": True}
        linkage = {"doctrines": ["constitutional_torts"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["accountability_concern"] >= 0.2

    def test_accountability_with_official_misconduct(self, scorer):
        """Test accountability score with official misconduct."""
        anomaly = {"official_misconduct": True}
        linkage = {"doctrines": ["constitutional_torts"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["accountability_concern"] >= 0.2

    def test_accountability_high_with_multiple_factors(self, scorer):
        """Test high accountability score with multiple factors."""
        anomaly = {
            "involves_force": True,
            "deadly_force": True,
            "qualified_immunity_applicable": True,
            "official_misconduct": True,
        }
        linkage = {"doctrines": ["constitutional_torts", "fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        # Should max out at 1.0
        assert result["component_scores"]["accountability_concern"] >= 0.8

    def test_accountability_zero_without_factors(self, scorer):
        """Test accountability scores zero without relevant factors."""
        anomaly = {"forensic_score": 75}
        linkage = {"doctrines": ["administrative_law"]}

        result = scorer.score_anomaly(anomaly, linkage)
        assert result["component_scores"]["accountability_concern"] == 0.0


class TestCLEPv1OverallScoring:
    """Test overall scoring with CLEP-v1 dimensions."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_digital_surveillance_scenario(self, scorer):
        """Test scoring for digital surveillance scenario."""
        anomaly = {
            "type": "digital_privacy_violation",
            "involves_location_tracking": True,
            "digital_search": True,
            "involves_surveillance": True,
            "lacks_warrant": False,  # Has warrant, so lower 4A score
        }
        linkage = {
            "doctrines": ["fourth_amendment"],
            "relevant_cases": [{"case_id": "carpenter_v_us_2018"}],
        }

        result = scorer.score_anomaly(anomaly, linkage)
        # Should have elevated digital privacy risk
        assert result["component_scores"]["digital_privacy_risk"] > 0.3
        # Overall score should reflect this
        assert result["overall_score"] > 0.0

    def test_use_of_force_scenario(self, scorer):
        """Test scoring for use of force scenario."""
        anomaly = {
            "type": "excessive_force",
            "involves_force": True,
            "official_misconduct": True,
        }
        linkage = {
            "doctrines": ["fourth_amendment", "constitutional_torts"],
            "relevant_cases": [{"case_id": "graham_v_connor_1989"}],
        }

        result = scorer.score_anomaly(anomaly, linkage)
        # Should have elevated accountability concern
        assert result["component_scores"]["accountability_concern"] > 0.3
        assert result["component_scores"]["fourth_amendment_concern"] > 0.0

    def test_comprehensive_violation_scenario(self, scorer):
        """Test scoring for comprehensive multi-doctrine violation."""
        anomaly = {
            "type": "systemic_violation",
            "affects_rights": True,
            "lacks_standards": True,
            "involves_surveillance": True,
            "involves_location_tracking": True,
            "lacks_reasoning": True,
            "forensic_score": 45,
            "timestamp_conflict": True,
            "involves_force": True,
        }
        linkage = {
            "doctrines": [
                "due_process",
                "non_delegation",
                "fourth_amendment",
                "administrative_law",
                "constitutional_torts",
            ],
        }

        result = scorer.score_anomaly(anomaly, linkage)
        # Should score high overall with multiple violations
        assert result["overall_score"] >= 0.45
        assert result["severity"] in ["high", "medium", "critical"]


class TestCLEPv1RiskFactorCompilation:
    """Test risk factor compilation with new dimensions."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_digital_privacy_factor_included(self, scorer):
        """Test digital privacy risk factor included in compilation."""
        anomaly = {
            "involves_location_tracking": True,
            "digital_search": True,
        }
        linkage = {"doctrines": ["fourth_amendment"]}

        result = scorer.score_anomaly(anomaly, linkage)
        factors = result["risk_factors"]
        # Should include digital privacy factor if score > 0.3
        if result["component_scores"]["digital_privacy_risk"] > 0.3:
            assert any("digital privacy" in f.lower() for f in factors)

    def test_accountability_factor_included(self, scorer):
        """Test accountability concern factor included in compilation."""
        anomaly = {
            "involves_force": True,
            "qualified_immunity_applicable": True,
        }
        linkage = {"doctrines": ["constitutional_torts"]}

        result = scorer.score_anomaly(anomaly, linkage)
        factors = result["risk_factors"]
        # Should include accountability factor if score > 0.3
        if result["component_scores"]["accountability_concern"] > 0.3:
            assert any("accountability" in f.lower() for f in factors)


class TestCLEPv1Recommendations:
    """Test recommendations with new dimensions."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_digital_privacy_recommendations(self, scorer):
        """Test recommendations for high digital privacy risk."""
        anomaly = {
            "involves_location_tracking": True,
            "digital_search": True,
            "electronic_communications": True,
        }
        linkage = {
            "doctrines": ["fourth_amendment"],
            "relevant_cases": [{"case_id": "riley_v_california_2014"}],
        }

        result = scorer.score_anomaly(anomaly, linkage)
        recommendations = result["recommended_actions"]

        # Should recommend digital privacy framework review
        if result["component_scores"]["digital_privacy_risk"] > 0.5:
            assert any(
                "carpenter" in r.lower() or "riley" in r.lower()
                for r in recommendations
            )

    def test_accountability_recommendations(self, scorer):
        """Test recommendations for high accountability concern."""
        anomaly = {
            "involves_force": True,
            "deadly_force": True,
        }
        linkage = {"doctrines": ["fourth_amendment", "constitutional_torts"]}

        result = scorer.score_anomaly(anomaly, linkage)
        recommendations = result["recommended_actions"]

        # Should recommend Graham v. Connor review
        if result["component_scores"]["accountability_concern"] > 0.5:
            assert any("graham" in r.lower() for r in recommendations)


class TestCLEPv1AggregateReporting:
    """Test aggregate reporting with CLEP-v1 dimensions."""

    @pytest.fixture
    def scorer(self):
        """Provide risk scorer."""
        return JIMRiskScoring()

    def test_aggregate_with_digital_privacy_cases(self, scorer):
        """Test aggregate report with digital privacy cases."""
        scored_anomalies = []
        for _i in range(3):
            anomaly = {
                "involves_location_tracking": True,
                "digital_search": True,
            }
            linkage = {"doctrines": ["fourth_amendment"]}
            scored_anomalies.append(scorer.score_anomaly(anomaly, linkage))

        report = scorer.aggregate_risk_report(scored_anomalies)
        assert report["total_anomalies"] == 3
        assert "risk_distribution" in report

    def test_aggregate_mixed_new_dimensions(self, scorer):
        """Test aggregate report with mixed new dimension anomalies."""
        scenarios = [
            ({"involves_location_tracking": True}, {"doctrines": ["fourth_amendment"]}),
            ({"involves_force": True}, {"doctrines": ["constitutional_torts"]}),
            ({"lacks_reasoning": True}, {"doctrines": ["administrative_law"]}),
        ]

        scored_anomalies = []
        for anomaly, linkage in scenarios:
            scored_anomalies.append(scorer.score_anomaly(anomaly, linkage))

        report = scorer.aggregate_risk_report(scored_anomalies)
        assert report["total_anomalies"] == 3
        assert "average_score" in report
