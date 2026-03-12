"""
CDSCE Core Engine - Cross-Dictionary Semiotic Correlation Engine v1.

This is the semantic fusion layer that correlates:
- Legal dictionaries (Black's, Bouvier's, Webster, Oxford, Latin)
- Case law doctrines
- Etymology (Latin, Greek, Canon)
- Era-based meaning shifts
- Constitutional linguistic frameworks (CLF)
- JIM semantic weights
- MSH harmonization layers

The engine becomes the interpreter of interpreters, enabling Oraculus to see
how meanings relate, conflict, evolve, or degrade across time, sources, and
legal traditions.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.jim.etymology_loader import EtymologyLoader
from scripts.jim.framework_loader import ConstitutionalFrameworkLoader
from scripts.jim.jim_case_loader import JIMCaseLoader
from scripts.jim.jim_semantic_loader import JIMSemanticLoader
from scripts.jim.semantic_harmonizer import SemanticHarmonizer


class CDSCEEngine:
    """
    Cross-Dictionary Semiotic Correlation Engine.

    Capabilities:
    - Multi-dictionary correlation system
    - Semiotic anomaly detection
    - Semantic drift analysis
    - Contradiction detection
    - Graph model generation
    - Era-aware analysis
    - CLF integration
    """

    VERSION = "1.0.0"
    SCHEMA_VERSION = "1.0"

    def __init__(
        self,
        lexicon_dir: Path | None = None,
        etymology_dir: Path | None = None,
        cases_dir: Path | None = None,
        constitutional_dir: Path | None = None,
        output_dir: Path | None = None,
    ):
        """
        Initialize CDSCE engine.

        Args:
            lexicon_dir: Path to legal/lexicon directory
            etymology_dir: Path to legal/etymology directory
            cases_dir: Path to legal/cases directory
            constitutional_dir: Path to constitutional directory
            output_dir: Path to output directory for semiotics
        """
        # Initialize component loaders
        self.semantic_loader = JIMSemanticLoader(lexicon_dir)
        self.etymology_loader = EtymologyLoader(etymology_dir)
        self.case_loader = JIMCaseLoader(cases_dir)
        self.framework_loader = ConstitutionalFrameworkLoader(constitutional_dir)
        self.harmonizer = SemanticHarmonizer(lexicon_dir)

        # Set output directory
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / "legal" / "semiotics"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # State
        self.loaded = False
        self.corpus: dict[str, Any] = {}
        self.correlations: dict[str, list[dict[str, Any]]] = {}
        self.anomalies: list[dict[str, Any]] = []
        self.drift_scores: dict[str, float] = {}
        self.contradictions: list[dict[str, Any]] = []
        self.graphs: dict[str, Any] = {}

    def initialize(self) -> dict[str, Any]:
        """
        Initialize CDSCE by loading all component systems.

        Returns:
            Initialization report with status and metadata
        """
        try:
            # Load semantic lexicon
            lexicon_result = self.semantic_loader.load_lexicon_sources()
            if not lexicon_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to load lexicon: {lexicon_result.get('error')}",
                }

            # Load etymology sources
            etymology_result = self.etymology_loader.load_all_sources()
            if not etymology_result["success"]:
                return {
                    "success": False,
                    "error": (
                        f"Failed to load etymology: " f"{etymology_result.get('error')}"
                    ),
                }

            # Load case law
            self.case_loader.load_scotus_index()
            case_validation = self.case_loader.validate_index()
            if not case_validation["valid"]:
                return {
                    "success": False,
                    "error": "Case index validation failed",
                    "validation_errors": case_validation["errors"],
                }

            # Load constitutional frameworks
            framework_result = self.framework_loader.load_frameworks()
            if not framework_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to load CLF: {framework_result.get('error')}",
                }

            # Load harmonization matrix
            harmonization_result = self.harmonizer.load_lexicon_sources()
            if not harmonization_result["success"]:
                return {
                    "success": False,
                    "error": (
                        f"Failed to load harmonization: "
                        f"{harmonization_result.get('error')}"
                    ),
                }

            self.loaded = True

            return {
                "success": True,
                "version": self.VERSION,
                "components": {
                    "lexicon_terms": lexicon_result.get("total_terms", 0),
                    "etymology_entries": etymology_result.get("total_entries", 0),
                    "cases_loaded": self.case_loader.get_metadata()[
                        "total_cases_loaded"
                    ],
                    "frameworks_loaded": framework_result.get("total_frameworks", 0),
                    "harmonized_terms": harmonization_result.get("total_terms", 0),
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Initialization failed: {str(e)}",
            }

    def correlate_term(self, term: str) -> dict[str, Any]:
        """
        Perform full cross-dictionary correlation for a term.

        Correlates across:
        - Dictionary definitions (Black's, Bouvier's, Webster, Oxford, Latin)
        - Etymology (Latin, Greek, Canon)
        - Case law doctrines
        - Constitutional frameworks
        - Era-based meanings

        Args:
            term: Legal term to correlate

        Returns:
            Comprehensive correlation structure
        """
        if not self.loaded:
            raise RuntimeError("CDSCE not initialized. Call initialize() first.")

        term_lower = term.lower()

        # Get dictionary definitions
        dictionary_sources = self._get_dictionary_sources(term_lower)

        # Get etymology lineage
        etymology_lineage = self._get_etymology_lineage(term_lower)

        # Get doctrinal mappings
        doctrinal_mappings = self._get_doctrinal_mappings(term_lower)

        # Get era definitions
        era_definitions = self._get_era_definitions(term_lower)

        # Get constitutional framework context
        framework_context = self._get_framework_context(term_lower)

        # Build correlation structure
        correlation = {
            "term": term,
            "canonical": term_lower.replace("_", " "),
            "dictionary_sources": dictionary_sources,
            "etymology_lineage": etymology_lineage,
            "doctrinal_mappings": doctrinal_mappings,
            "era_definitions": era_definitions,
            "framework_context": framework_context,
            "correlation_strength": self._calculate_correlation_strength(
                dictionary_sources, etymology_lineage, doctrinal_mappings
            ),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return correlation

    def _get_dictionary_sources(self, term: str) -> list[dict[str, Any]]:
        """Get definitions from all dictionary sources."""
        sources = []

        # Get from semantic loader
        definitions = self.semantic_loader.merged_definitions
        if term in definitions:
            term_data = definitions[term]
            for source_key, source_data in term_data.get("sources", {}).items():
                sources.append(
                    {
                        "source": source_key,
                        "definition": source_data.get("definition", ""),
                        "year": source_data.get("year", 0),
                        "citation": source_data.get("citation", ""),
                    }
                )

        return sources

    def _get_etymology_lineage(self, term: str) -> list[dict[str, Any]]:
        """Get etymology lineage for a term."""
        lineage = []

        # Check Latin maxims
        if term in self.etymology_loader.latin_maxims.get("maxims", {}):
            maxim = self.etymology_loader.latin_maxims["maxims"][term]
            lineage.append(
                {
                    "language": "latin",
                    "root": maxim.get("latin", ""),
                    "meaning": maxim.get("meaning", ""),
                    "era": "classical",
                }
            )

        # Check Greek roots
        if term in self.etymology_loader.greek_roots.get("roots", {}):
            root = self.etymology_loader.greek_roots["roots"][term]
            lineage.append(
                {
                    "language": "greek",
                    "root": root.get("greek", ""),
                    "meaning": root.get("meaning", ""),
                    "era": "classical",
                }
            )

        # Check Canon law roots
        if term in self.etymology_loader.canon_roots.get("entries", {}):
            canon = self.etymology_loader.canon_roots["entries"][term]
            lineage.append(
                {
                    "language": "canon_law",
                    "root": canon.get("latin", ""),
                    "meaning": canon.get("meaning", ""),
                    "era": "medieval",
                }
            )

        return lineage

    def _get_doctrinal_mappings(self, term: str) -> list[dict[str, Any]]:
        """Get case law doctrine mappings for a term."""
        mappings = []

        # Get from harmonizer merged definitions
        definitions = self.harmonizer.merged_definitions
        if term in definitions:
            term_data = definitions[term]
            doctrines = term_data.get("doctrines", [])
            for doctrine in doctrines:
                # Find related cases
                related_cases = []
                for case_id, case_data in self.case_loader.cases.items():
                    if doctrine in case_data.get("doctrines", []):
                        related_cases.append(
                            {
                                "case_id": case_id,
                                "title": case_data.get("title", ""),
                                "year": case_data.get("year", 0),
                            }
                        )

                mappings.append(
                    {
                        "doctrine": doctrine,
                        "related_cases": related_cases[:5],  # Limit to 5
                    }
                )

        return mappings

    def _get_era_definitions(self, term: str) -> dict[str, Any]:
        """Get era-specific definitions for a term."""
        era_defs = {}

        # Get from harmonizer
        definitions = self.harmonizer.merged_definitions
        if term in definitions:
            term_data = definitions[term]
            era_adjustments = term_data.get("era_adjustments", {})
            for era, definition in era_adjustments.items():
                era_defs[era] = {
                    "definition": definition,
                    "era_name": self.harmonizer.ERAS.get(int(era), "Unknown"),
                }

        return era_defs

    def _get_framework_context(self, term: str) -> list[dict[str, Any]]:
        """Get constitutional framework context for a term."""
        contexts = []

        # Check each framework for relevance
        for framework_id, framework in self.framework_loader.frameworks.items():
            # Simple keyword matching for now
            framework_text = json.dumps(framework).lower()
            if term in framework_text:
                contexts.append(
                    {
                        "framework": framework_id,
                        "name": framework.get("name", ""),
                        "era": framework.get("era", ""),
                        "weight": framework.get("jim_weight", 0.0),
                    }
                )

        return contexts

    def _calculate_correlation_strength(
        self,
        dictionary_sources: list[dict[str, Any]],
        etymology_lineage: list[dict[str, Any]],
        doctrinal_mappings: list[dict[str, Any]],
    ) -> float:
        """
        Calculate correlation strength score (0.0-1.0).

        Based on:
        - Number of dictionary sources
        - Etymology lineage depth
        - Doctrinal connections
        """
        score = 0.0

        # Dictionary sources (max 0.4)
        score += min(len(dictionary_sources) * 0.08, 0.4)

        # Etymology lineage (max 0.3)
        score += min(len(etymology_lineage) * 0.1, 0.3)

        # Doctrinal mappings (max 0.3)
        score += min(len(doctrinal_mappings) * 0.075, 0.3)

        return min(score, 1.0)

    def generate_corpus(self, terms: list[str] | None = None) -> dict[str, Any]:
        """
        Generate semiotic corpus for specified terms or all available terms.

        Args:
            terms: List of terms to include, or None for all terms

        Returns:
            Generation report with corpus statistics
        """
        if not self.loaded:
            raise RuntimeError("CDSCE not initialized. Call initialize() first.")

        # Get terms to process
        if terms is None:
            terms = list(self.semantic_loader.merged_definitions.keys())

        # Build corpus
        corpus_terms = {}
        for term in terms:
            try:
                correlation = self.correlate_term(term)
                corpus_terms[term] = correlation
            except Exception as e:
                print(f"Warning: Failed to correlate term '{term}': {e}")

        self.corpus = {
            "version": self.VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_terms": len(corpus_terms),
            "terms": corpus_terms,
        }

        return {
            "success": True,
            "terms_processed": len(corpus_terms),
            "corpus_size": len(corpus_terms),
        }

    def save_corpus(self) -> dict[str, Any]:
        """
        Save semiotic corpus to disk.

        Returns:
            Save status report
        """
        output_path = self.output_dir / "SEMIOTIC_CORPUS.json"

        try:
            with open(output_path, "w") as f:
                json.dump(self.corpus, f, indent=2)

            return {
                "success": True,
                "output_path": str(output_path),
                "size_bytes": output_path.stat().st_size,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save corpus: {str(e)}",
            }

    def get_statistics(self) -> dict[str, Any]:
        """
        Get CDSCE statistics.

        Returns:
            Comprehensive statistics report
        """
        return {
            "version": self.VERSION,
            "loaded": self.loaded,
            "corpus_terms": len(self.corpus.get("terms", {})),
            "correlations": len(self.correlations),
            "anomalies": len(self.anomalies),
            "contradictions": len(self.contradictions),
            "drift_scores": len(self.drift_scores),
            "graphs": list(self.graphs.keys()),
        }
