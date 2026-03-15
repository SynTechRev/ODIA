"""Tests for audit-aware query enrichment."""

from oraculus_di_auditor.rag import EnrichedQuery, QueryEnricher

# -- test: surveillance expands to ALPR, BWC, etc. --------------------------


def test_surveillance_expansion():
    enricher = QueryEnricher()
    eq = enricher.enrich("surveillance cameras in the city")

    assert isinstance(eq, EnrichedQuery)
    assert eq.original_query == "surveillance cameras in the city"
    assert "surveillance" in eq.detected_concepts
    assert "ALPR" in eq.expanded_terms
    assert "BWC" in eq.expanded_terms
    assert "body camera" in eq.expanded_terms
    assert len(eq.search_queries) > 1


# -- test: unsigned contracts expands to MSPA, placeholder, etc. -------------


def test_unsigned_contract_expansion():
    enricher = QueryEnricher()
    eq = enricher.enrich("unsigned contracts found in the audit")

    assert "unsigned" in eq.detected_concepts
    assert "contract" in eq.detected_concepts
    assert "signature blank" in eq.expanded_terms
    assert "placeholder" in eq.expanded_terms
    assert "MSPA" in eq.expanded_terms
    assert "amendment" in eq.expanded_terms


# -- test: no domain terms returns original unchanged ------------------------


def test_no_domain_terms():
    enricher = QueryEnricher()
    eq = enricher.enrich("how many documents were analyzed?")

    assert eq.original_query == "how many documents were analyzed?"
    assert eq.expanded_terms == []
    assert eq.detected_concepts == []
    assert eq.search_queries == ["how many documents were analyzed?"]


# -- test: detect_concepts identifies correct categories ---------------------


def test_detect_concepts():
    enricher = QueryEnricher()

    assert "surveillance" in enricher.detect_concepts("surveillance policy")
    assert "vendor" in enricher.detect_concepts("vendor contract list")
    assert "grant" in enricher.detect_concepts("federal grant funding")
    assert "governance" in enricher.detect_concepts("governance framework")
    assert enricher.detect_concepts("random question") == []


# -- test: multiple concepts in one query all expand -------------------------


def test_multiple_concepts_expand():
    enricher = QueryEnricher()
    eq = enricher.enrich("surveillance vendor procurement patterns")

    assert "surveillance" in eq.detected_concepts
    assert "vendor" in eq.detected_concepts
    assert "procurement" in eq.detected_concepts
    # Expansions from all three concepts present
    assert "ALPR" in eq.expanded_terms  # surveillance
    assert "Axon" in eq.expanded_terms  # vendor
    assert "RFP" in eq.expanded_terms  # procurement
    # Multiple search queries generated
    assert len(eq.search_queries) == 4  # original + 3 concept expansions
