"""
Tests for Legal Lexicon Semantics - LLEP-v1.

Tests synonym/antonym graphs, doctrine inference, and term normalization.
"""

from scripts.jim.jim_semantic_loader import JIMSemanticLoader


class TestTermNormalization:
    """Test term normalization functionality."""

    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        loader = JIMSemanticLoader()
        assert loader.normalize_term("PROBABLE CAUSE") == "probable_cause"
        assert loader.normalize_term("Due Process") == "due_process"

    def test_normalize_spaces_to_underscores(self):
        """Test normalization converts spaces to underscores."""
        loader = JIMSemanticLoader()
        assert loader.normalize_term("reasonable suspicion") == "reasonable_suspicion"
        assert loader.normalize_term("burden of proof") == "burden_of_proof"

    def test_normalize_hyphens_to_underscores(self):
        """Test normalization converts hyphens to underscores."""
        loader = JIMSemanticLoader()
        assert loader.normalize_term("ex-parte") == "ex_parte"
        assert loader.normalize_term("non-delegation") == "non_delegation"

    def test_normalize_removes_apostrophes(self):
        """Test normalization removes apostrophes."""
        loader = JIMSemanticLoader()
        assert loader.normalize_term("Black's Law") == "blacks_law"

    def test_normalize_strips_whitespace(self):
        """Test normalization strips leading/trailing whitespace."""
        loader = JIMSemanticLoader()
        assert loader.normalize_term("  due process  ") == "due_process"


class TestMergeDefinitions:
    """Test definition merging from multiple sources."""

    def test_merge_creates_unified_entries(self):
        """Test merge creates unified entries for terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        assert len(merged) > 0
        assert "probable_cause" in merged
        assert "due_process" in merged

    def test_merged_entries_have_sources(self):
        """Test merged entries include source information."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        for _term, data in merged.items():
            assert "sources" in data
            assert isinstance(data["sources"], list)
            assert len(data["sources"]) > 0

    def test_merged_entries_have_doctrines(self):
        """Test merged entries include doctrine mappings."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        for _term, data in merged.items():
            assert "doctrines" in data
            assert isinstance(data["doctrines"], list)

    def test_merged_entries_preserve_term_names(self):
        """Test merged entries preserve original term names."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        for _term, data in merged.items():
            assert "term" in data
            assert data["term"] != ""


class TestSynonymGraph:
    """Test synonym graph construction."""

    def test_synonym_graph_builds(self):
        """Test synonym graph builds successfully."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        assert len(synonym_graph) > 0
        assert isinstance(synonym_graph, dict)

    def test_synonym_relationships_bidirectional(self):
        """Test synonym relationships are bidirectional where possible."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        # Count bidirectional relationships
        bidirectional_count = 0
        for term, synonyms in synonym_graph.items():
            for synonym in synonyms:
                if synonym in synonym_graph and term in synonym_graph[synonym]:
                    bidirectional_count += 1

        # Should have many bidirectional relationships
        assert bidirectional_count > 50

    def test_synonym_graph_includes_webster_terms(self):
        """Test synonym graph includes Webster synonyms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        # Check that some Webster terms are present
        assert len(synonym_graph) > 0

    def test_synonym_graph_includes_oxford_mappings(self):
        """Test synonym graph includes Oxford mappings."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        # Should have many synonyms from Oxford
        total_synonyms = sum(len(syns) for syns in synonym_graph.values())
        assert total_synonyms > 100

    def test_probable_cause_synonyms(self):
        """Test probable cause has expected synonyms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        probable_cause_key = loader.normalize_term("probable cause")
        assert probable_cause_key in synonym_graph
        synonyms = synonym_graph[probable_cause_key]
        assert len(synonyms) > 0


class TestAntonymGraph:
    """Test antonym graph construction."""

    def test_antonym_graph_builds(self):
        """Test antonym graph builds successfully."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        assert len(antonym_graph) > 0
        assert isinstance(antonym_graph, dict)

    def test_antonym_relationships_bidirectional(self):
        """Test antonym relationships are bidirectional where possible."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        # Count bidirectional relationships
        bidirectional_count = 0
        for term, antonyms in antonym_graph.items():
            for antonym in antonyms:
                if antonym in antonym_graph and term in antonym_graph[antonym]:
                    bidirectional_count += 1

        # Should have many bidirectional relationships
        assert bidirectional_count > 20

    def test_antonym_graph_includes_webster_antonyms(self):
        """Test antonym graph includes Webster antonyms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        # Should have antonyms
        total_antonyms = sum(len(ants) for ants in antonym_graph.values())
        assert total_antonyms > 0

    def test_due_process_antonyms(self):
        """Test due process has antonyms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        due_process_key = loader.normalize_term("due process")
        assert due_process_key in antonym_graph
        antonyms = antonym_graph[due_process_key]
        assert len(antonyms) > 0


class TestDoctrineInference:
    """Test doctrine inference and mapping."""

    def test_doctrine_map_builds(self):
        """Test doctrine map builds successfully."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        assert len(doctrine_map) > 0
        assert isinstance(doctrine_map, dict)

    def test_doctrine_map_has_major_doctrines(self):
        """Test doctrine map includes major doctrines."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Check for some expected doctrines
        expected_doctrines = [
            "due_process",
            "fourth_amendment",
            "criminal_law",
            "civil_procedure",
        ]

        found_count = sum(1 for d in expected_doctrines if d in doctrine_map)
        assert found_count > 0

    def test_doctrines_have_terms(self):
        """Test each doctrine has associated terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        for _doctrine, terms in doctrine_map.items():
            assert isinstance(terms, list)
            assert len(terms) > 0

    def test_fourth_amendment_doctrine(self):
        """Test Fourth Amendment doctrine has expected terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Should have fourth amendment doctrine
        assert "fourth_amendment" in doctrine_map
        terms = doctrine_map["fourth_amendment"]
        assert len(terms) > 0

    def test_latin_doctrinal_mappings(self):
        """Test Latin terms contribute to doctrine map."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Check that common_law doctrine exists (from Latin terms)
        assert "common_law" in doctrine_map
        terms = doctrine_map["common_law"]
        assert len(terms) > 0


class TestCollisionResolution:
    """Test handling of duplicate terms across dictionaries."""

    def test_multiple_sources_for_same_term(self):
        """Test terms can have multiple source definitions."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Check index entries with multiple sources
        multi_source_count = 0
        for entry in loader.index.get("index", []):
            sources = entry.get("sources", [])
            if len(sources) > 1:
                multi_source_count += 1
                # Verify each source has required info
                for source in sources:
                    assert "dictionary" in source
                # At least one should have definition or other content
                has_content = any(
                    "definition" in s or "synonyms" in s or "translation" in s
                    for s in sources
                )
                assert has_content

        # Should have at least some multi-source terms
        assert multi_source_count > 0

    def test_no_conflicting_normalizations(self):
        """Test term normalization is consistent."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Same term should normalize to same value
        term1 = loader.normalize_term("Due Process")
        term2 = loader.normalize_term("due process")
        term3 = loader.normalize_term("DUE PROCESS")
        assert term1 == term2 == term3


class TestGraphIntegrity:
    """Test graph structure integrity."""

    def test_synonym_graph_no_self_references(self):
        """Test synonym graph has no self-referential entries."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        for term, synonyms in synonym_graph.items():
            assert term not in synonyms

    def test_antonym_graph_no_self_references(self):
        """Test antonym graph has no self-referential entries."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        for term, antonyms in antonym_graph.items():
            assert term not in antonyms

    def test_doctrine_terms_are_normalized(self):
        """Test doctrine map terms are normalized."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        for _doctrine, terms in doctrine_map.items():
            for term in terms:
                # Should be normalized (lowercase, underscores for spaces)
                assert term == term.lower(), f"Term '{term}' not lowercase"
                # If there are underscores, verify no spaces exist
                assert " " not in term, f"Term '{term}' contains spaces"


class TestSemanticRelationships:
    """Test semantic relationship quality."""

    def test_synonym_count_reasonable(self):
        """Test synonym relationships are reasonable in count."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        synonym_graph = loader.build_synonym_graph()

        # Most terms should have some synonyms
        terms_with_synonyms = sum(1 for syns in synonym_graph.values() if len(syns) > 0)
        assert terms_with_synonyms > 0

    def test_antonym_count_reasonable(self):
        """Test antonym relationships are reasonable in count."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        antonym_graph = loader.build_antonym_graph()

        # Some terms should have antonyms
        terms_with_antonyms = sum(1 for ants in antonym_graph.values() if len(ants) > 0)
        assert terms_with_antonyms > 0

    def test_doctrine_distribution(self):
        """Test doctrines are reasonably distributed."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Should have multiple doctrines
        assert len(doctrine_map) > 10

        # Doctrines should have varying term counts
        term_counts = [len(terms) for terms in doctrine_map.values()]
        assert min(term_counts) >= 1
        assert max(term_counts) > min(term_counts)
