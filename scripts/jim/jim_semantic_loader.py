"""
JIM Semantic Loader - Legal Lexicon Loading and Processing Engine.

Loads and integrates multiple legal dictionary sources into a unified semantic graph
for use in Judicial Interpretive Matrix (JIM) analysis.
"""

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JIMSemanticLoader:
    """
    Legal lexicon semantic loader for JIM.

    Capabilities:
    - Load all dictionary sources
    - Validate schema and integrity
    - Build synonym/antonym graphs
    - Normalize and merge terms
    - Infer doctrinal relationships
    - Generate summary artifacts
    """

    VERSION = "1.0.0"

    def __init__(self, lexicon_dir: Path | None = None):
        """
        Initialize semantic loader.

        Args:
            lexicon_dir: Path to legal/lexicon directory
        """
        if lexicon_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            lexicon_dir = repo_root / "legal" / "lexicon"
        self.lexicon_dir = Path(lexicon_dir)

        # Loaded data
        self.blacks_law: dict[str, Any] = {}
        self.bouvier: dict[str, Any] = {}
        self.webster: dict[str, Any] = {}
        self.oxford: dict[str, Any] = {}
        self.latin: dict[str, Any] = {}
        self.index: dict[str, Any] = {}

        # Processed structures
        self.synonym_graph: dict[str, list[str]] = defaultdict(list)
        self.antonym_graph: dict[str, list[str]] = defaultdict(list)
        self.doctrine_map: dict[str, list[str]] = defaultdict(list)
        self.normalized_terms: dict[str, str] = {}

    def load_lexicon_sources(self) -> dict[str, Any]:
        """
        Load all dictionary sources from lexicon directory.

        Returns:
            Status report with loaded term counts
        """
        try:
            # Load Black's Law Dictionary
            blacks_path = self.lexicon_dir / "black_law_subset.json"
            with open(blacks_path, encoding="utf-8") as f:
                self.blacks_law = json.load(f)

            # Load Bouvier's 1856
            bouvier_path = self.lexicon_dir / "bouvier_1856.json"
            with open(bouvier_path, encoding="utf-8") as f:
                self.bouvier = json.load(f)

            # Load Webster Legal
            webster_path = self.lexicon_dir / "webster_legal_subset.json"
            with open(webster_path, encoding="utf-8") as f:
                self.webster = json.load(f)

            # Load Oxford synonyms
            oxford_path = self.lexicon_dir / "oxford_law_synonyms.json"
            with open(oxford_path, encoding="utf-8") as f:
                self.oxford = json.load(f)

            # Load Latin foundational
            latin_path = self.lexicon_dir / "latin_foundational.json"
            with open(latin_path, encoding="utf-8") as f:
                self.latin = json.load(f)

            # Load unified index
            index_path = self.lexicon_dir / "LEGAL_DICTIONARY_INDEX.json"
            with open(index_path, encoding="utf-8") as f:
                self.index = json.load(f)

            return {
                "success": True,
                "sources_loaded": 6,
                "blacks_terms": len(self.blacks_law.get("terms", [])),
                "bouvier_terms": len(self.bouvier.get("terms", [])),
                "webster_terms": len(self.webster.get("terms", [])),
                "oxford_mappings": len(self.oxford.get("synonym_mappings", [])),
                "latin_terms": len(self.latin.get("terms", [])),
                "index_entries": len(self.index.get("index", [])),
            }

        except FileNotFoundError as e:
            return {"success": False, "error": f"Lexicon file not found: {e}"}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON in lexicon file: {e}"}

    def validate_lexicon_schema(self) -> dict[str, Any]:
        """
        Validate schema integrity of all loaded lexicon sources.

        Returns:
            Validation report with errors if any
        """
        errors = []

        # Validate Black's Law Dictionary
        if not self.blacks_law:
            errors.append("Black's Law Dictionary not loaded")
        else:
            for i, term in enumerate(self.blacks_law.get("terms", [])):
                if "term" not in term:
                    errors.append(f"Black's term {i}: missing 'term' field")
                if "definition" not in term:
                    errors.append(f"Black's term {i}: missing 'definition' field")
                if "citation" not in term:
                    errors.append(f"Black's term {i}: missing 'citation' field")

        # Validate Bouvier's
        if not self.bouvier:
            errors.append("Bouvier's Dictionary not loaded")
        else:
            for i, term in enumerate(self.bouvier.get("terms", [])):
                if "term" not in term:
                    errors.append(f"Bouvier term {i}: missing 'term' field")
                if "definition" not in term:
                    errors.append(f"Bouvier term {i}: missing 'definition' field")
                if "citation" not in term:
                    errors.append(f"Bouvier term {i}: missing 'citation' field")

        # Validate Webster
        if not self.webster:
            errors.append("Webster Legal Dictionary not loaded")
        else:
            for i, term in enumerate(self.webster.get("terms", [])):
                if "term" not in term:
                    errors.append(f"Webster term {i}: missing 'term' field")
                if "definition" not in term:
                    errors.append(f"Webster term {i}: missing 'definition' field")

        # Validate Oxford
        if not self.oxford:
            errors.append("Oxford Law Dictionary not loaded")
        else:
            for i, mapping in enumerate(self.oxford.get("synonym_mappings", [])):
                if "term" not in mapping:
                    errors.append(f"Oxford mapping {i}: missing 'term' field")
                if "synonyms" not in mapping:
                    errors.append(f"Oxford mapping {i}: missing 'synonyms' field")

        # Validate Latin
        if not self.latin:
            errors.append("Latin Legal Maxims not loaded")
        else:
            for i, term in enumerate(self.latin.get("terms", [])):
                if "latin" not in term:
                    errors.append(f"Latin term {i}: missing 'latin' field")
                if "translation" not in term:
                    errors.append(f"Latin term {i}: missing 'translation' field")
                if "jurisprudential_usage" not in term:
                    errors.append(
                        f"Latin term {i}: missing 'jurisprudential_usage' field"
                    )
                if "doctrinal_mapping" not in term:
                    errors.append(f"Latin term {i}: missing 'doctrinal_mapping' field")

        # Validate Index
        if not self.index:
            errors.append("Legal Dictionary Index not loaded")
        else:
            for i, entry in enumerate(self.index.get("index", [])):
                if "term" not in entry:
                    errors.append(f"Index entry {i}: missing 'term' field")
                if "sources" not in entry:
                    errors.append(f"Index entry {i}: missing 'sources' field")
                if "doctrines" not in entry:
                    errors.append(f"Index entry {i}: missing 'doctrines' field")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "error_count": len(errors),
        }

    def normalize_term(self, term: str) -> str:
        """
        Normalize a legal term to canonical form.

        Args:
            term: Raw term string

        Returns:
            Normalized term (lowercase, underscores, no special chars)
        """
        normalized = term.lower().strip()
        normalized = normalized.replace(" ", "_")
        normalized = normalized.replace("-", "_")
        normalized = normalized.replace("'", "")
        return normalized

    def merge_definitions(self) -> dict[str, Any]:
        """
        Merge definitions from multiple sources for each term.

        Returns:
            Dictionary mapping normalized terms to merged definitions
        """
        merged = {}

        # Process index entries
        for entry in self.index.get("index", []):
            term = entry["term"]
            normalized = self.normalize_term(term)
            self.normalized_terms[normalized] = term

            merged[normalized] = {
                "term": term,
                "normalized": normalized,
                "sources": entry.get("sources", []),
                "doctrines": entry.get("doctrines", []),
                "origin_language": entry.get("origin_language", "Unknown"),
                "related_terms": entry.get("related_terms", []),
                "antonyms": entry.get("antonyms", []),
            }

        return merged

    def build_synonym_graph(self) -> dict[str, list[str]]:
        """
        Build synonym relationship graph from all sources.

        Returns:
            Dictionary mapping terms to their synonyms
        """
        # Process Webster synonyms
        for term_entry in self.webster.get("terms", []):
            term = term_entry["term"]
            normalized = self.normalize_term(term)
            synonyms = term_entry.get("synonyms", [])
            for synonym in synonyms:
                syn_normalized = self.normalize_term(synonym)
                if syn_normalized not in self.synonym_graph[normalized]:
                    self.synonym_graph[normalized].append(syn_normalized)
                # Bidirectional
                if normalized not in self.synonym_graph[syn_normalized]:
                    self.synonym_graph[syn_normalized].append(normalized)

        # Process Oxford synonym mappings
        for mapping in self.oxford.get("synonym_mappings", []):
            term = mapping["term"]
            normalized = self.normalize_term(term)
            synonyms = mapping.get("synonyms", [])
            for synonym in synonyms:
                syn_normalized = self.normalize_term(synonym)
                if syn_normalized not in self.synonym_graph[normalized]:
                    self.synonym_graph[normalized].append(syn_normalized)
                # Bidirectional
                if normalized not in self.synonym_graph[syn_normalized]:
                    self.synonym_graph[syn_normalized].append(normalized)

        # Process index related terms
        for entry in self.index.get("index", []):
            term = entry["term"]
            normalized = self.normalize_term(term)
            related = entry.get("related_terms", [])
            for rel_term in related:
                rel_normalized = self.normalize_term(rel_term)
                if rel_normalized not in self.synonym_graph[normalized]:
                    self.synonym_graph[normalized].append(rel_normalized)

        return dict(self.synonym_graph)

    def build_antonym_graph(self) -> dict[str, list[str]]:
        """
        Build antonym relationship graph from all sources.

        Returns:
            Dictionary mapping terms to their antonyms
        """
        # Process Webster antonyms
        for term_entry in self.webster.get("terms", []):
            term = term_entry["term"]
            normalized = self.normalize_term(term)
            antonyms = term_entry.get("antonyms", [])
            for antonym in antonyms:
                ant_normalized = self.normalize_term(antonym)
                if ant_normalized not in self.antonym_graph[normalized]:
                    self.antonym_graph[normalized].append(ant_normalized)
                # Bidirectional
                if normalized not in self.antonym_graph[ant_normalized]:
                    self.antonym_graph[ant_normalized].append(normalized)

        # Process index antonyms
        for entry in self.index.get("index", []):
            term = entry["term"]
            normalized = self.normalize_term(term)
            antonyms = entry.get("antonyms", [])
            for antonym in antonyms:
                ant_normalized = self.normalize_term(antonym)
                if ant_normalized not in self.antonym_graph[normalized]:
                    self.antonym_graph[normalized].append(ant_normalized)
                # Bidirectional
                if normalized not in self.antonym_graph[ant_normalized]:
                    self.antonym_graph[ant_normalized].append(normalized)

        return dict(self.antonym_graph)

    def infer_doctrines(self) -> dict[str, list[str]]:
        """
        Build doctrine-to-term mapping for doctrinal inference.

        Returns:
            Dictionary mapping doctrine names to associated terms
        """
        # Process index doctrine mappings
        for entry in self.index.get("index", []):
            term = entry["term"]
            normalized = self.normalize_term(term)
            doctrines = entry.get("doctrines", [])
            for doctrine in doctrines:
                if normalized not in self.doctrine_map[doctrine]:
                    self.doctrine_map[doctrine].append(normalized)

        # Process Latin doctrinal mappings
        for term_entry in self.latin.get("terms", []):
            latin_term = term_entry.get("latin", "")
            normalized = self.normalize_term(latin_term)
            doctrinal_mapping = term_entry.get("doctrinal_mapping", [])
            for doctrine in doctrinal_mapping:
                if normalized not in self.doctrine_map[doctrine]:
                    self.doctrine_map[doctrine].append(normalized)

        return dict(self.doctrine_map)

    def generate_lexicon_summary(self, output_path: Path | None = None) -> str:
        """
        Generate LEXICON_SUMMARY.md markdown report.

        Args:
            output_path: Optional output path for summary

        Returns:
            Markdown summary text
        """
        if output_path is None:
            repo_root = Path(__file__).parent.parent.parent
            output_path = repo_root / "LEXICON_SUMMARY.md"

        merged = self.merge_definitions()
        synonym_graph = self.build_synonym_graph()
        antonym_graph = self.build_antonym_graph()
        doctrine_map = self.infer_doctrines()

        summary = f"""# Legal Lexicon Summary v{self.VERSION}

**Generated:** {datetime.now(UTC).isoformat()}

## Overview

The Legal Lexicon Expansion Pack (LLEP-v1) provides a comprehensive, multi-source legal dictionary system for the Judicial Interpretive Matrix (JIM).

## Statistics

- **Total Terms:** {len(merged)}
- **Synonym Relationships:** {sum(len(syns) for syns in synonym_graph.values()) // 2}
- **Antonym Relationships:** {sum(len(ants) for ants in antonym_graph.values()) // 2}
- **Doctrines Mapped:** {len(doctrine_map)}
- **Source Dictionaries:** 5

## Source Dictionary Breakdown

### Black's Law Dictionary (11th Edition, 2019)
- Terms: {len(self.blacks_law.get('terms', []))}
- Focus: Constitutional and procedural law

### Bouvier's Law Dictionary (1856)
- Terms: {len(self.bouvier.get('terms', []))}
- Focus: Historical legal foundations

### Merriam-Webster Legal Dictionary (2023)
- Terms: {len(self.webster.get('terms', []))}
- Focus: Modern interpretations with synonyms/antonyms

### Oxford English Law Dictionary (2023)
- Synonym Mappings: {len(self.oxford.get('synonym_mappings', []))}
- Focus: Equivalent terminology

### Latin Legal Maxims
- Terms: {len(self.latin.get('terms', []))}
- Focus: Foundational Latin legal vocabulary

## Top Doctrines by Term Coverage

"""
        # Add top doctrines
        doctrine_counts = {
            doctrine: len(terms) for doctrine, terms in doctrine_map.items()
        }
        sorted_doctrines = sorted(
            doctrine_counts.items(), key=lambda x: x[1], reverse=True
        )
        for doctrine, count in sorted_doctrines[:15]:
            summary += f"- **{doctrine}**: {count} terms\n"

        summary += """
## Term Categories

Distribution by legal category:

"""
        # Count categories
        category_counts: dict[str, int] = defaultdict(int)
        for term_data in self.blacks_law.get("terms", []):
            category = term_data.get("category", "other")
            category_counts[category] += 1
        for term_data in self.bouvier.get("terms", []):
            category = term_data.get("category", "other")
            category_counts[category] += 1

        for category, count in sorted(
            category_counts.items(), key=lambda x: x[1], reverse=True
        ):
            summary += f"- {category}: {count}\n"

        summary += """
## Integration with JIM

The lexicon integrates with JIM's doctrinal analysis by:

1. **Semantic Matching**: Terms in anomaly descriptions are normalized and matched to lexicon entries
2. **Doctrine Inference**: Matched terms trigger associated doctrinal frameworks for analysis
3. **Synonym Expansion**: Synonym graph allows recognition of equivalent legal terminology
4. **Historical Context**: Bouvier's 1856 definitions provide constitutional-era interpretations
5. **Latin Maxim Support**: Latin terms are recognized and mapped to jurisprudential principles

## Schema

See `docs/lexicon_schema_reference.md` for complete schema documentation.
"""

        # Write to file
        Path(output_path).write_text(summary, encoding="utf-8")
        return summary

    def generate_artifacts(self, output_dir: Path | None = None) -> dict[str, Any]:
        """
        Generate all lexicon artifacts (LEXICON_GRAPH.json, LEXICON_STATS.json).

        Args:
            output_dir: Optional output directory for artifacts

        Returns:
            Status report with artifact paths
        """
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root

        # Ensure all graphs are built
        merged = self.merge_definitions()
        synonym_graph = self.build_synonym_graph()
        antonym_graph = self.build_antonym_graph()
        doctrine_map = self.infer_doctrines()

        # Generate LEXICON_GRAPH.json
        graph_data = {
            "version": self.VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "synonym_graph": synonym_graph,
            "antonym_graph": antonym_graph,
            "doctrine_map": doctrine_map,
            "normalized_terms": self.normalized_terms,
        }
        graph_path = output_dir / "LEXICON_GRAPH.json"
        with open(graph_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        # Generate LEXICON_STATS.json
        stats_data = {
            "version": self.VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_terms": len(merged),
            "synonym_relationships": sum(len(syns) for syns in synonym_graph.values())
            // 2,
            "antonym_relationships": sum(len(ants) for ants in antonym_graph.values())
            // 2,
            "doctrines_mapped": len(doctrine_map),
            "source_dictionaries": 5,
            "blacks_terms": len(self.blacks_law.get("terms", [])),
            "bouvier_terms": len(self.bouvier.get("terms", [])),
            "webster_terms": len(self.webster.get("terms", [])),
            "oxford_mappings": len(self.oxford.get("synonym_mappings", [])),
            "latin_terms": len(self.latin.get("terms", [])),
            "index_entries": len(self.index.get("index", [])),
        }
        stats_path = output_dir / "LEXICON_STATS.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)

        # Generate LEXICON_SUMMARY.md
        summary_path = output_dir / "LEXICON_SUMMARY.md"
        self.generate_lexicon_summary(summary_path)

        return {
            "success": True,
            "graph_path": str(graph_path),
            "stats_path": str(stats_path),
            "summary_path": str(summary_path),
        }


def main():
    """CLI entry point for semantic loader."""
    loader = JIMSemanticLoader()

    print("Loading lexicon sources...")
    load_result = loader.load_lexicon_sources()
    print(f"Loaded: {load_result}")

    print("\nValidating schema...")
    validation = loader.validate_lexicon_schema()
    print(f"Valid: {validation['valid']}")
    if not validation["valid"]:
        print(f"Errors: {validation['errors']}")
        return

    print("\nMerging definitions...")
    merged = loader.merge_definitions()
    print(f"Merged {len(merged)} terms")

    print("\nBuilding graphs...")
    synonym_graph = loader.build_synonym_graph()
    antonym_graph = loader.build_antonym_graph()
    print(f"Synonym relationships: {len(synonym_graph)}")
    print(f"Antonym relationships: {len(antonym_graph)}")

    print("\nInferring doctrines...")
    doctrine_map = loader.infer_doctrines()
    print(f"Doctrines mapped: {len(doctrine_map)}")

    print("\nGenerating artifacts...")
    artifacts = loader.generate_artifacts()
    print(f"Artifacts: {artifacts}")

    print("\n[OK] Lexicon processing complete!")


if __name__ == "__main__":
    main()
