"""Tests for the RAG prompt router.

Tests query classification, prompt routing, and available_data influence.
"""

from oraculus_di_auditor.rag import PromptConfig, PromptRouter

# -- test: factual query routes correctly -----------------------------------


def test_factual_query_routes():
    router = PromptRouter()
    cfg = router.route("What contracts were approved in 2023?")

    assert isinstance(cfg, PromptConfig)
    assert "document" in cfg.expected_source_types
    assert len(cfg.system_prompt) > 0
    assert len(cfg.query_template) > 0
    assert len(cfg.response_instructions) > 0


# -- test: comparative query routes correctly --------------------------------


def test_comparative_query_routes():
    router = PromptRouter()
    cfg = router.route("Compare surveillance spending across jurisdictions")

    assert "analysis" in cfg.expected_source_types
    assert (
        router.classify_query("Compare surveillance spending across jurisdictions")
        == "comparative"
    )


# -- test: vendor keywords trigger vendor prompt -----------------------------


def test_vendor_keywords_trigger_vendor():
    router = PromptRouter()

    for query in [
        "Show me the Flock Safety pattern",
        "Which vendors appear in sole-source procurements?",
        "What supplier contracts exist?",
    ]:
        qtype = router.classify_query(query)
        assert qtype == "vendor", f"Expected 'vendor' for: {query}"

    cfg = router.route("Which vendors appear in sole-source procurements?")
    assert "document" in cfg.expected_source_types


# -- test: compliance keywords trigger compliance prompt ---------------------


def test_compliance_keywords_trigger_compliance():
    router = PromptRouter()

    for query in [
        "Is this jurisdiction compliant with SB 524?",
        "What CCOPS mandates are being violated?",
        "Show compliance status for the ordinance",
    ]:
        qtype = router.classify_query(query)
        assert qtype == "compliance", f"Expected 'compliance' for: {query}"


# -- test: classify_query returns valid type ---------------------------------


def test_classify_query_returns_valid_type():
    router = PromptRouter()
    valid_types = {
        "factual",
        "analytical",
        "comparative",
        "compliance",
        "recommendation",
        "vendor",
        "temporal",
    }

    queries = [
        "What contracts were approved?",
        "What patterns are most common?",
        "Compare these jurisdictions",
        "Is this compliant?",
        "What should the council do?",
        "Which vendors are involved?",
        "When did spending increase?",
        "How many documents were analyzed?",
    ]

    for query in queries:
        qtype = router.classify_query(query)
        assert qtype in valid_types, f"Invalid type '{qtype}' for: {query}"


# -- test: available_data affects system prompt ------------------------------


def test_available_data_in_system_prompt():
    router = PromptRouter()

    cfg_without = router.route("What happened?")
    cfg_with = router.route(
        "What happened?",
        available_data={"documents", "findings", "analysis"},
    )

    assert "Available data sources" not in cfg_without.system_prompt
    assert "Available data sources" in cfg_with.system_prompt
    assert "analysis" in cfg_with.system_prompt
    assert "documents" in cfg_with.system_prompt
    assert "findings" in cfg_with.system_prompt


# -- test: temporal query routes correctly -----------------------------------


def test_temporal_query_routes():
    router = PromptRouter()
    qtype = router.classify_query("When did surveillance spending start increasing?")
    assert qtype == "temporal"


# -- test: recommendation query routes correctly -----------------------------


def test_recommendation_query_routes():
    router = PromptRouter()
    qtype = router.classify_query("What remediation steps are needed?")
    assert qtype == "recommendation"


# -- test: analytical query routes correctly ---------------------------------


def test_analytical_query_routes():
    router = PromptRouter()
    qtype = router.classify_query("Which detectors are firing most frequently?")
    assert qtype == "analytical"


# -- test: default to factual -----------------------------------------------


def test_default_factual():
    router = PromptRouter()
    qtype = router.classify_query("Tell me about document X")
    assert qtype == "factual"
