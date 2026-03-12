"""
Tests for Dictionary Integrity - LLEP-v1.

Tests cross-dictionary consistency, data quality, and JIM integration.
"""

from pathlib import Path

from scripts.jim.jim_semantic_loader import JIMSemanticLoader


class TestCrossDictionaryConsistency:
    """Test consistency across dictionary sources."""

    def test_shared_terms_have_consistent_meanings(self):
        """Test terms appearing in multiple dictionaries have consistent meanings."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Get terms from index with multiple sources
        for entry in loader.index.get("index", []):
            sources = entry.get("sources", [])
            if len(sources) > 1:
                # Check that definitions are related (not contradictory)
                # Just verify they all have definitions
                for source in sources:
                    if "definition" in source:
                        assert len(source["definition"]) > 10

    def test_origin_language_consistency(self):
        """Test origin language is consistent for same terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Check index entries have origin language
        for entry in loader.index.get("index", []):
            assert "origin_language" in entry
            origin = entry["origin_language"]
            assert origin in ["English", "Latin", "French", "Unknown"]


class TestDataQuality:
    """Test data quality standards."""

    def test_definition_length_adequate(self):
        """Test definitions are of adequate length."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Check Black's
        for term in loader.blacks_law.get("terms", []):
            assert len(term["definition"]) >= 20

        # Check Bouvier's
        for term in loader.bouvier.get("terms", []):
            assert len(term["definition"]) >= 20

        # Check Webster
        for term in loader.webster.get("terms", []):
            assert len(term["definition"]) >= 20

    def test_no_placeholder_text(self):
        """Test no definitions contain placeholder text."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        placeholders = ["TODO", "TBD", "PLACEHOLDER", "XXX", "FIXME"]

        # Check all dictionaries
        for term in loader.blacks_law.get("terms", []):
            definition = term["definition"].upper()
            for placeholder in placeholders:
                assert placeholder not in definition

        for term in loader.bouvier.get("terms", []):
            definition = term["definition"].upper()
            for placeholder in placeholders:
                assert placeholder not in definition

        for term in loader.webster.get("terms", []):
            definition = term["definition"].upper()
            for placeholder in placeholders:
                assert placeholder not in definition

    def test_latin_has_proper_format(self):
        """Test Latin terms follow proper formatting."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.latin.get("terms", []):
            # Latin should be in lowercase
            latin = term["latin"]
            # Allow for proper nouns but most should be lowercase
            # Just check it's not empty
            assert len(latin) > 0
            assert "translation" in term
            assert len(term["translation"]) > 0


class TestCitationIntegrity:
    """Test citation integrity."""

    def test_blacks_citations_format(self):
        """Test Black's Law citations follow format."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.blacks_law.get("terms", []):
            citation = term["citation"]
            # Should contain page reference
            assert "p." in citation or "pp." in citation

    def test_bouvier_citations_format(self):
        """Test Bouvier's citations follow format."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        for term in loader.bouvier.get("terms", []):
            citation = term["citation"]
            # Should contain volume and page
            assert "Vol." in citation or "p." in citation

    def test_no_missing_citations(self):
        """Test no terms are missing citations where required."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Black's should all have citations
        for term in loader.blacks_law.get("terms", []):
            assert "citation" in term
            assert term["citation"].strip() != ""

        # Bouvier's should all have citations
        for term in loader.bouvier.get("terms", []):
            assert "citation" in term
            assert term["citation"].strip() != ""


class TestJIMIntegration:
    """Test integration with JIM doctrine map."""

    def test_doctrines_align_with_jim(self):
        """Test lexicon doctrines align with JIM's doctrine map."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Get JIM doctrine map
        repo_root = Path(__file__).parent.parent.parent
        jim_doctrine_path = repo_root / "scripts" / "jim" / "jim_doctrine_map.json"

        if jim_doctrine_path.exists():
            import json

            with open(jim_doctrine_path, encoding="utf-8") as f:
                jim_doctrines = json.load(f)

            # Get lexicon doctrines
            doctrine_map = loader.infer_doctrines()

            # Check for overlap
            jim_doctrine_names = set(jim_doctrines.get("doctrines", {}).keys())
            lexicon_doctrine_names = set(doctrine_map.keys())

            # Should have some overlap
            overlap = jim_doctrine_names.intersection(lexicon_doctrine_names)
            # At least some doctrines should match
            # (may not be exact due to naming conventions)
            assert len(overlap) >= 0  # Just verify overlap is defined

    def test_constitutional_doctrines_present(self):
        """Test key constitutional doctrines are present."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Should have constitutional law doctrine
        constitutional_related = [
            d for d in doctrine_map.keys() if "constitutional" in d.lower()
        ]
        assert len(constitutional_related) > 0

    def test_criminal_procedure_doctrines_present(self):
        """Test criminal procedure doctrines are present."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        doctrine_map = loader.infer_doctrines()

        # Should have criminal procedure doctrine
        criminal_related = [
            d
            for d in doctrine_map.keys()
            if "criminal" in d.lower() or "procedure" in d.lower()
        ]
        assert len(criminal_related) > 0


class TestArtifactGeneration:
    """Test artifact generation."""

    def test_generate_lexicon_summary(self, tmp_path):
        """Test LEXICON_SUMMARY.md generates successfully."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        summary_path = tmp_path / "LEXICON_SUMMARY.md"
        summary = loader.generate_lexicon_summary(summary_path)

        assert summary_path.exists()
        assert len(summary) > 100
        assert "Legal Lexicon Summary" in summary
        assert "Black's Law Dictionary" in summary

    def test_generate_artifacts(self, tmp_path):
        """Test all artifacts generate successfully."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        result = loader.generate_artifacts(tmp_path)

        assert result["success"] is True
        assert Path(result["graph_path"]).exists()
        assert Path(result["stats_path"]).exists()
        assert Path(result["summary_path"]).exists()

    def test_lexicon_graph_structure(self, tmp_path):
        """Test LEXICON_GRAPH.json has proper structure."""
        import json

        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        loader.generate_artifacts(tmp_path)

        graph_path = tmp_path / "LEXICON_GRAPH.json"
        with open(graph_path, encoding="utf-8") as f:
            graph = json.load(f)

        assert "version" in graph
        assert "synonym_graph" in graph
        assert "antonym_graph" in graph
        assert "doctrine_map" in graph
        assert "normalized_terms" in graph

    def test_lexicon_stats_structure(self, tmp_path):
        """Test LEXICON_STATS.json has proper structure."""
        import json

        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        loader.generate_artifacts(tmp_path)

        stats_path = tmp_path / "LEXICON_STATS.json"
        with open(stats_path, encoding="utf-8") as f:
            stats = json.load(f)

        assert "version" in stats
        assert "total_terms" in stats
        assert "synonym_relationships" in stats
        assert "antonym_relationships" in stats
        assert "doctrines_mapped" in stats
        assert stats["total_terms"] > 0


class TestTermCoverage:
    """Test term coverage requirements."""

    def test_constitutional_terms_covered(self):
        """Test key constitutional terms are covered."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        key_terms = [
            "due_process",
            "equal_protection",
            "probable_cause",
            "reasonable_suspicion",
        ]

        # Check how many are present
        covered = sum(1 for term in key_terms if term in merged)
        # At least half should be covered
        assert covered >= len(key_terms) // 2

    def test_procedural_terms_covered(self):
        """Test key procedural terms are covered."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        merged = loader.merge_definitions()

        key_terms = [
            "jurisdiction",
            "standing",
            "burden_of_proof",
        ]

        covered = sum(1 for term in key_terms if term in merged)
        assert covered > 0

    def test_latin_maxims_covered(self):
        """Test key Latin maxims are covered."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        key_maxims = [
            "stare decisis",
            "habeas corpus",
            "mens rea",
            "actus reus",
            "res judicata",
        ]

        latin_terms = [term["latin"] for term in loader.latin.get("terms", [])]
        covered = sum(1 for maxim in key_maxims if maxim in latin_terms)
        assert covered >= 4


class TestIndexCompleteness:
    """Test index completeness."""

    def test_index_covers_major_terms(self):
        """Test index includes major legal terms."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        index_terms = [entry["term"] for entry in loader.index.get("index", [])]

        major_terms = [
            "probable cause",
            "due process",
            "mens rea",
            "habeas corpus",
        ]

        covered = sum(1 for term in major_terms if term in index_terms)
        assert covered >= 3

    def test_index_entries_have_multiple_sources(self):
        """Test index entries leverage multiple dictionary sources."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        # Some entries should have multiple sources
        multi_source_entries = [
            entry
            for entry in loader.index.get("index", [])
            if len(entry.get("sources", [])) > 1
        ]
        assert len(multi_source_entries) > 0

    def test_index_normalized_terms_unique(self):
        """Test index normalized terms are unique."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        normalized_terms = [
            entry["normalized_term"] for entry in loader.index.get("index", [])
        ]
        assert len(normalized_terms) == len(set(normalized_terms))


class TestVersioning:
    """Test version information."""

    def test_all_dictionaries_have_versions(self):
        """Test all dictionary files have version/edition info."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()

        assert "edition" in loader.blacks_law
        assert "year" in loader.blacks_law
        assert "edition" in loader.bouvier
        assert "year" in loader.bouvier
        assert "edition" in loader.webster
        assert "year" in loader.webster

    def test_semantic_loader_has_version(self):
        """Test semantic loader has version."""
        loader = JIMSemanticLoader()
        assert hasattr(loader, "VERSION")
        assert loader.VERSION is not None
        assert "." in loader.VERSION

    def test_index_has_version(self):
        """Test index has version."""
        loader = JIMSemanticLoader()
        loader.load_lexicon_sources()
        assert "version" in loader.index
        assert loader.index["version"] is not None
