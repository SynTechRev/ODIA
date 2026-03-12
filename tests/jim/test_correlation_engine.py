"""
Tests for JIM Correlation Engine - Anomaly to doctrine/precedent correlation.
"""

import pytest

from scripts.jim.jim_case_loader import JIMCaseLoader
from scripts.jim.jim_correlation_engine import JIMCorrelationEngine


class TestCorrelationEngineInitialization:
    """Test correlation engine initialization."""

    @pytest.fixture
    def loaded_loader(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return loader

    def test_engine_initializes(self, loaded_loader):
        """Test engine initializes with case loader."""
        engine = JIMCorrelationEngine(loaded_loader)
        assert engine.case_loader == loaded_loader
        assert hasattr(engine, "anomaly_doctrine_map")

    def test_engine_has_anomaly_mappings(self, loaded_loader):
        """Test engine has anomaly to doctrine mappings."""
        engine = JIMCorrelationEngine(loaded_loader)

        assert "metadata_break" in engine.anomaly_doctrine_map
        assert "sole_source_procurement" in engine.anomaly_doctrine_map
        assert "surveillance_program" in engine.anomaly_doctrine_map


class TestDoctrineIdentification:
    """Test doctrine identification from anomalies."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_identify_doctrines_metadata_break(self, engine):
        """Test identifying doctrines for metadata break."""
        anomaly = {}
        doctrines = engine._identify_doctrines("metadata_break", anomaly)

        assert "due_process" in doctrines
        assert "administrative_law" in doctrines

    def test_identify_doctrines_surveillance(self, engine):
        """Test identifying doctrines for surveillance."""
        anomaly = {}
        doctrines = engine._identify_doctrines("surveillance_program", anomaly)

        assert "fourth_amendment" in doctrines

    def test_identify_doctrines_delegation(self, engine):
        """Test identifying doctrines for delegation issues."""
        anomaly = {}
        doctrines = engine._identify_doctrines("delegation_without_authority", anomaly)

        assert "non_delegation" in doctrines
        assert "separation_of_powers" in doctrines

    def test_identify_doctrines_with_flags(self, engine):
        """Test identifying doctrines using anomaly flags."""
        anomaly = {"involves_surveillance": True, "affects_rights": True}
        doctrines = engine._identify_doctrines("unknown_type", anomaly)

        assert "fourth_amendment" in doctrines
        assert "due_process" in doctrines

    def test_identify_doctrines_sorted(self, engine):
        """Test identified doctrines are sorted."""
        anomaly = {"lacks_standards": True, "lacks_reasoning": True}
        doctrines = engine._identify_doctrines("unknown", anomaly)

        assert doctrines == sorted(doctrines)


class TestCaseRelevance:
    """Test case relevance calculation."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_calculate_relevance_base_weight(self, engine):
        """Test relevance includes base doctrinal weight."""
        case = {"doctrinal_weight": 0.9, "issue_tags": [], "year": 1980}
        anomaly = {"description": "test"}

        relevance = engine._calculate_case_relevance(case, anomaly, "due_process")

        assert relevance >= 0.45  # 0.9 * 0.5

    def test_calculate_relevance_tag_matching(self, engine):
        """Test relevance increases with tag matching."""
        case = {
            "doctrinal_weight": 0.5,
            "issue_tags": ["procedural_due_process"],
            "year": 1980,
        }
        anomaly = {"description": "procedural due process violation"}

        relevance = engine._calculate_case_relevance(case, anomaly, "due_process")

        assert relevance > 0.25  # Base + tag match

    def test_calculate_relevance_recent_case_boost(self, engine):
        """Test recent cases get relevance boost."""
        case = {"doctrinal_weight": 0.5, "issue_tags": [], "year": 2020}
        anomaly = {"description": "test"}

        relevance = engine._calculate_case_relevance(case, anomaly, "fourth_amendment")

        assert relevance > 0.25  # Base + recency boost


class TestFindRelevantCases:
    """Test finding relevant cases for anomalies."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_find_relevant_cases_due_process(self, engine):
        """Test finding due process cases."""
        anomaly = {"description": "procedural hearing issue"}
        cases = engine._find_relevant_cases(["due_process"], anomaly)

        assert len(cases) > 0
        assert all(c["doctrine"] == "due_process" for c in cases)

    def test_find_relevant_cases_limit(self, engine):
        """Test relevant cases limited to top 5."""
        anomaly = {"description": "test"}
        cases = engine._find_relevant_cases(["administrative_law"], anomaly)

        assert len(cases) <= 5

    def test_find_relevant_cases_sorted(self, engine):
        """Test relevant cases sorted by relevance."""
        anomaly = {"description": "test"}
        cases = engine._find_relevant_cases(["due_process"], anomaly)

        if len(cases) > 1:
            scores = [c["relevance_score"] for c in cases]
            assert scores == sorted(scores, reverse=True)

    def test_find_relevant_cases_no_duplicates(self, engine):
        """Test no duplicate cases returned."""
        anomaly = {"description": "test"}
        cases = engine._find_relevant_cases(
            ["due_process", "administrative_law"], anomaly
        )

        case_ids = [c["case_id"] for c in cases]
        assert len(case_ids) == len(set(case_ids))


class TestCanonIdentification:
    """Test interpretive canon identification."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_identify_canons_major_questions(self, engine):
        """Test major questions doctrine identification."""
        anomaly = {"economic_significance": True}
        canons = engine._identify_canons(anomaly)

        assert any(c.get("canon_id") == "major_questions_doctrine" for c in canons)

    def test_identify_canons_clear_statement(self, engine):
        """Test clear statement rule identification."""
        anomaly = {"affects_rights": True}
        canons = engine._identify_canons(anomaly)

        assert any(c.get("canon_id") == "clear_statement_rule" for c in canons)

    def test_identify_canons_avoidance(self, engine):
        """Test constitutional avoidance identification."""
        anomaly = {"constitutional_doubt": True}
        canons = engine._identify_canons(anomaly)

        assert any(c.get("canon_id") == "avoidance_canon" for c in canons)

    def test_identify_canons_lenity(self, engine):
        """Test rule of lenity identification."""
        anomaly = {"imposes_penalty": True}
        canons = engine._identify_canons(anomaly)

        assert any(c.get("canon_id") == "rule_of_lenity" for c in canons)


class TestRiskIndicators:
    """Test risk indicator assessment."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_risk_indicators_constitutional_rights(self, engine):
        """Test constitutional rights indicator."""
        anomaly = {}
        indicators = engine._assess_risk_indicators(anomaly, ["due_process"])

        assert indicators["affects_constitutional_rights"] is True

    def test_risk_indicators_separation_of_powers(self, engine):
        """Test separation of powers indicator."""
        anomaly = {}
        indicators = engine._assess_risk_indicators(anomaly, ["separation_of_powers"])

        assert indicators["separation_of_powers_concern"] is True

    def test_risk_indicators_delegation(self, engine):
        """Test delegation indicator."""
        anomaly = {}
        indicators = engine._assess_risk_indicators(anomaly, ["non_delegation"])

        assert indicators["delegation_issue"] is True

    def test_risk_indicators_evidentiary(self, engine):
        """Test evidentiary concern indicator."""
        anomaly = {"forensic_score": 60}
        indicators = engine._assess_risk_indicators(anomaly, [])

        assert indicators["evidentiary_concern"] is True


class TestConstitutionalBasis:
    """Test constitutional basis identification."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_constitutional_basis_due_process(self, engine):
        """Test due process constitutional basis."""
        basis = engine._identify_constitutional_basis(["due_process"])

        assert any("Fifth Amendment" in b for b in basis)

    def test_constitutional_basis_fourth_amendment(self, engine):
        """Test Fourth Amendment basis."""
        basis = engine._identify_constitutional_basis(["fourth_amendment"])

        assert any("Fourth Amendment" in b for b in basis)

    def test_constitutional_basis_multiple(self, engine):
        """Test multiple doctrines constitutional basis."""
        basis = engine._identify_constitutional_basis(
            ["due_process", "fourth_amendment"]
        )

        assert len(basis) >= 2
        assert basis == sorted(list(set(basis)))


class TestMajorQuestionsCheck:
    """Test major questions doctrine applicability check."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_major_questions_economic_significance(self, engine):
        """Test major questions with economic significance."""
        anomaly = {"economic_significance": True}
        assert engine._check_major_questions(anomaly) is True

    def test_major_questions_political_significance(self, engine):
        """Test major questions with political significance."""
        anomaly = {"political_significance": True}
        assert engine._check_major_questions(anomaly) is True

    def test_major_questions_policy_shift(self, engine):
        """Test major questions with policy shift."""
        anomaly = {"major_policy_shift": True}
        assert engine._check_major_questions(anomaly) is True

    def test_major_questions_not_applicable(self, engine):
        """Test major questions not applicable."""
        anomaly = {}
        assert engine._check_major_questions(anomaly) is False


class TestSingleAnomalyCorrelation:
    """Test correlating single anomaly."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_correlate_anomaly_basic(self, engine):
        """Test basic anomaly correlation."""
        anomaly = {
            "id": "test_001",
            "type": "metadata_break",
            "source": "ace",
        }

        correlation = engine.correlate_anomaly(anomaly)

        assert "anomaly_id" in correlation
        assert "doctrines" in correlation
        assert "relevant_cases" in correlation
        assert "interpretive_canons" in correlation
        assert "risk_indicators" in correlation

    def test_correlate_anomaly_doctrines(self, engine):
        """Test anomaly correlation includes doctrines."""
        anomaly = {"type": "surveillance_program"}

        correlation = engine.correlate_anomaly(anomaly)

        assert "fourth_amendment" in correlation["doctrines"]

    def test_correlate_anomaly_cases(self, engine):
        """Test anomaly correlation includes cases."""
        anomaly = {"type": "metadata_break", "description": "due process issue"}

        correlation = engine.correlate_anomaly(anomaly)

        assert len(correlation["relevant_cases"]) > 0

    def test_correlate_anomaly_constitutional_basis(self, engine):
        """Test anomaly correlation includes constitutional basis."""
        anomaly = {"type": "surveillance_program"}

        correlation = engine.correlate_anomaly(anomaly)

        assert len(correlation["constitutional_basis"]) > 0


class TestMultipleAnomalyCorrelation:
    """Test correlating multiple anomalies."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_correlate_multiple_basic(self, engine):
        """Test correlating multiple anomalies."""
        anomalies = [
            {"id": "a1", "type": "metadata_break"},
            {"id": "a2", "type": "surveillance_program"},
        ]

        result = engine.correlate_multiple_anomalies(anomalies)

        assert "total_anomalies_correlated" in result
        assert result["total_anomalies_correlated"] == 2
        assert len(result["individual_correlations"]) == 2

    def test_correlate_multiple_doctrine_frequency(self, engine):
        """Test doctrine frequency tracking."""
        anomalies = [
            {"type": "metadata_break"},
            {"type": "metadata_break"},
            {"type": "surveillance_program"},
        ]

        result = engine.correlate_multiple_anomalies(anomalies)

        assert "doctrine_frequency" in result
        assert result["doctrine_frequency"]["due_process"] >= 2

    def test_correlate_multiple_dominant_doctrines(self, engine):
        """Test dominant doctrine identification."""
        anomalies = [
            {"type": "metadata_break"},
            {"type": "sole_source_procurement"},
        ]

        result = engine.correlate_multiple_anomalies(anomalies)

        assert "dominant_doctrines" in result
        assert len(result["dominant_doctrines"]) > 0

    def test_correlate_multiple_systemic_patterns(self, engine):
        """Test systemic pattern identification."""
        anomalies = [
            {"type": "metadata_break", "affects_rights": True} for _ in range(5)
        ]

        result = engine.correlate_multiple_anomalies(anomalies)

        assert "systemic_patterns" in result


class TestSystemicPatterns:
    """Test systemic pattern identification."""

    @pytest.fixture
    def engine(self):
        loader = JIMCaseLoader()
        loader.load_scotus_index()
        return JIMCorrelationEngine(loader)

    def test_systemic_constitutional_rights(self, engine):
        """Test systemic constitutional rights pattern."""
        correlations = [
            {"risk_indicators": {"affects_constitutional_rights": True}}
            for _ in range(5)
        ]

        patterns = engine._identify_systemic_patterns(correlations)

        assert any("constitutional rights" in p.lower() for p in patterns)

    def test_systemic_delegation_issues(self, engine):
        """Test systemic delegation pattern."""
        correlations = [
            {"risk_indicators": {"delegation_issue": True}} for _ in range(3)
        ]

        patterns = engine._identify_systemic_patterns(correlations)

        assert any("delegation" in p.lower() for p in patterns)

    def test_systemic_administrative_violations(self, engine):
        """Test systemic administrative pattern."""
        correlations = [
            {"risk_indicators": {"administrative_procedure_violation": True}}
            for _ in range(6)
        ]

        patterns = engine._identify_systemic_patterns(correlations)

        assert any("administrative" in p.lower() for p in patterns)
