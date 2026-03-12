"""
JIM Semantic Harmonizer - Multi-Source Semantic Harmonization Engine.

Transforms the multi-dictionary legal lexicon into a unified semantic engine
that resolves conflicting meanings, handles temporal drift, normalizes doctrine
interpretations, and detects meaning divergence across eras and sources.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.jim.jim_semantic_loader import JIMSemanticLoader


class SemanticHarmonizer:
    """
    Multi-Source Semantic Harmonization Engine.

    Capabilities:
    - Assign harmonization weights based on source authoritativeness
    - Track semantic drift over time (era-based)
    - Detect conflicts between sources
    - Generate harmonization matrix
    - Generate meaning divergence index
    - Apply era-specific adjustments
    """

    VERSION = "1.0.0"
    SCHEMA_VERSION = "1.0"

    # Source authority weights (0.0-1.0) based on authoritativeness
    SOURCE_WEIGHTS = {
        "blacks": 0.35,  # Black's Law Dictionary - most authoritative modern source
        "bouvier": 0.20,  # Bouvier's 1856 - historical constitutional-era authority
        "webster": 0.20,  # Webster Legal - modern interpretations
        "oxford": 0.15,  # Oxford Law - synonym authority
        "latin": 0.10,  # Latin maxims - foundational principles
    }

    # Era definitions for temporal analysis
    ERAS = {
        1791: "Constitutional Founding Era",
        1868: "Reconstruction Era (14th Amendment)",
        1920: "Early Modern Era",
        1960: "Civil Rights Era",
        2000: "Digital Age",
        2024: "Contemporary Era",
    }

    def __init__(self, lexicon_dir: Path | None = None, output_dir: Path | None = None):
        """
        Initialize semantic harmonizer.

        Args:
            lexicon_dir: Path to legal/lexicon directory
            output_dir: Path to artifacts output directory
        """
        # Initialize semantic loader
        self.loader = JIMSemanticLoader(lexicon_dir)

        # Set output directory
        if output_dir is None:
            repo_root = Path(__file__).parent.parent.parent
            output_dir = repo_root / "artifacts"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Processed data
        self.harmonization_matrix: dict[str, Any] = {}
        self.divergence_index: dict[str, Any] = {}
        self.conflicts: list[dict[str, Any]] = []
        self.merged_definitions: dict[str, Any] = {}

    def load_lexicon_sources(self) -> dict[str, Any]:
        """
        Load all lexicon sources from semantic loader.

        Returns:
            Status report with loaded source counts
        """
        result = self.loader.load_lexicon_sources()

        if not result["success"]:
            return result

        # Validate schema
        validation = self.loader.validate_lexicon_schema()
        if not validation["valid"]:
            return {
                "success": False,
                "error": "Schema validation failed",
                "validation_errors": validation["errors"],
            }

        # Build semantic structures
        self.merged_definitions = self.loader.merge_definitions()

        return {
            "success": True,
            "sources_loaded": result["sources_loaded"],
            "total_terms": len(self.merged_definitions),
            "blacks_terms": result["blacks_terms"],
            "bouvier_terms": result["bouvier_terms"],
            "webster_terms": result["webster_terms"],
            "oxford_mappings": result["oxford_mappings"],
            "latin_terms": result["latin_terms"],
        }

    def compute_harmonization_weights(self, term: str) -> dict[str, float]:
        """
        Compute harmonization weights for a term based on source availability.

        Weights are normalized based on which sources define the term.

        Args:
            term: Normalized term name

        Returns:
            Dictionary mapping source names to normalized weights
        """
        if term not in self.merged_definitions:
            return {}

        term_data = self.merged_definitions[term]
        sources = term_data.get("sources", [])

        # Build weight map for available sources
        available_weights = {}
        for source in sources:
            # Handle dict sources from index
            if isinstance(source, dict):
                source_name = source.get("dictionary", "")
            else:
                source_name = source

            source_key = self._map_source_to_key(source_name)
            if source_key in self.SOURCE_WEIGHTS:
                available_weights[source_key] = self.SOURCE_WEIGHTS[source_key]

        # Normalize weights to sum to 1.0
        total_weight = sum(available_weights.values())
        if total_weight > 0:
            normalized_weights = {
                source: weight / total_weight
                for source, weight in available_weights.items()
            }
        else:
            normalized_weights = {}

        return normalized_weights

    def _map_source_to_key(self, source: str) -> str:
        """
        Map source dictionary name to weight key.

        Args:
            source: Source name from lexicon

        Returns:
            Key for SOURCE_WEIGHTS lookup
        """
        source_lower = source.lower()
        if "black" in source_lower:
            return "blacks"
        elif "bouvier" in source_lower:
            return "bouvier"
        elif "webster" in source_lower:
            return "webster"
        elif "oxford" in source_lower:
            return "oxford"
        elif "latin" in source_lower:
            return "latin"
        else:
            return "unknown"

    def build_harmonization_matrix(self) -> dict[str, Any]:
        """
        Build the complete semantic harmonization matrix.

        For each term, creates a harmonized entry with:
        - Canonical form
        - Source definitions
        - Harmonized meaning (weighted combination)
        - Weights
        - Doctrines
        - Era adjustments

        Returns:
            Harmonization matrix dictionary
        """
        matrix = {}

        for normalized_term, term_data in self.merged_definitions.items():
            term_name = term_data["term"]

            # Get source-specific definitions
            source_definitions = self._extract_source_definitions(normalized_term)

            # Compute weights
            weights = self.compute_harmonization_weights(normalized_term)

            # Build harmonized meaning
            harmonized_meaning = self._build_harmonized_meaning(
                source_definitions, weights
            )

            # Get doctrines
            doctrines = term_data.get("doctrines", [])

            # Apply era adjustments
            era_adjustments = self._compute_era_adjustments(
                normalized_term, source_definitions
            )

            # Build matrix entry
            matrix[normalized_term] = {
                "canonical": term_name,
                "sources": source_definitions,
                "harmonized_meaning": harmonized_meaning,
                "weights": weights,
                "doctrines": doctrines,
                "era_adjustments": era_adjustments,
                "related_terms": term_data.get("related_terms", []),
                "antonyms": term_data.get("antonyms", []),
                "origin_language": term_data.get("origin_language", "Unknown"),
            }

        self.harmonization_matrix = matrix
        return matrix

    def _extract_source_definitions(  # noqa: C901
        self, normalized_term: str
    ) -> dict[str, Any]:
        """
        Extract definitions from all sources for a term.

        Args:
            normalized_term: Normalized term name

        Returns:
            Dictionary mapping source keys to definition data
        """
        source_definitions = {}

        # Extract from Black's Law
        for term_entry in self.loader.blacks_law.get("terms", []):
            if self.loader.normalize_term(term_entry["term"]) == normalized_term:
                source_definitions["blacks"] = {
                    "definition": term_entry.get("definition", ""),
                    "citation": term_entry.get("citation", ""),
                    "edition": "11th",
                    "year": 2019,
                }
                break

        # Extract from Bouvier's
        for term_entry in self.loader.bouvier.get("terms", []):
            if self.loader.normalize_term(term_entry["term"]) == normalized_term:
                source_definitions["bouvier"] = {
                    "definition": term_entry.get("definition", ""),
                    "citation": term_entry.get("citation", ""),
                    "edition": "1856",
                    "year": 1856,
                }
                break

        # Extract from Webster
        for term_entry in self.loader.webster.get("terms", []):
            if self.loader.normalize_term(term_entry["term"]) == normalized_term:
                source_definitions["webster"] = {
                    "definition": term_entry.get("definition", ""),
                    "synonyms": term_entry.get("synonyms", []),
                    "antonyms": term_entry.get("antonyms", []),
                    "year": 2023,
                }
                break

        # Extract from Oxford
        for mapping in self.loader.oxford.get("synonym_mappings", []):
            if self.loader.normalize_term(mapping["term"]) == normalized_term:
                source_definitions["oxford"] = {
                    "synonyms": mapping.get("synonyms", []),
                    "year": 2023,
                }
                break

        # Extract from Latin
        for term_entry in self.loader.latin.get("terms", []):
            if (
                self.loader.normalize_term(term_entry.get("latin", ""))
                == normalized_term
            ):
                source_definitions["latin"] = {
                    "latin": term_entry.get("latin", ""),
                    "translation": term_entry.get("translation", ""),
                    "jurisprudential_usage": term_entry.get(
                        "jurisprudential_usage", ""
                    ),
                    "doctrinal_mapping": term_entry.get("doctrinal_mapping", []),
                }
                break

        return source_definitions

    def _build_harmonized_meaning(
        self, source_definitions: dict[str, Any], weights: dict[str, float]
    ) -> str:
        """
        Build harmonized meaning from source definitions using weights.

        Prioritizes sources by weight, combining definitions intelligently.

        Args:
            source_definitions: Dictionary of source definitions
            weights: Dictionary of source weights

        Returns:
            Harmonized meaning string
        """
        if not source_definitions:
            return ""

        # Sort sources by weight (highest first)
        sorted_sources = sorted(weights.items(), key=lambda x: x[1], reverse=True)

        # Start with the highest-weighted source
        harmonized_parts = []
        for source_key, weight in sorted_sources:
            if source_key in source_definitions:
                source_def = source_definitions[source_key]

                # Extract definition text
                if "definition" in source_def:
                    harmonized_parts.append(source_def["definition"])
                elif "jurisprudential_usage" in source_def:
                    harmonized_parts.append(source_def["jurisprudential_usage"])

                # For primary source, use it as the base
                if weight == max(weights.values()) and harmonized_parts:
                    break

        # Return the primary definition (highest weight)
        if harmonized_parts:
            return harmonized_parts[0]
        return ""

    def _compute_era_adjustments(
        self, normalized_term: str, source_definitions: dict[str, Any]
    ) -> dict[str, str]:
        """
        Compute era-specific adjustments for term meanings.

        Args:
            normalized_term: Normalized term name
            source_definitions: Dictionary of source definitions

        Returns:
            Dictionary mapping era years to era-specific meanings
        """
        era_adjustments = {}

        # 1791 (Constitutional Founding) - use Bouvier's if available
        if "bouvier" in source_definitions:
            era_adjustments["1791"] = source_definitions["bouvier"].get(
                "definition", ""
            )

        # 1868 (Reconstruction) - use Bouvier's or modern interpretation
        if "bouvier" in source_definitions:
            era_adjustments["1868"] = source_definitions["bouvier"].get(
                "definition", ""
            )
        elif "blacks" in source_definitions:
            era_adjustments["1868"] = source_definitions["blacks"].get("definition", "")

        # 2024 (Contemporary) - use Black's or Webster
        if "blacks" in source_definitions:
            era_adjustments["2024"] = source_definitions["blacks"].get("definition", "")
        elif "webster" in source_definitions:
            era_adjustments["2024"] = source_definitions["webster"].get(
                "definition", ""
            )

        return era_adjustments

    def detect_semantic_conflicts(self) -> list[dict[str, Any]]:
        """
        Detect conflicts between source definitions.

        Identifies terms where sources provide contradictory or
        significantly divergent meanings.

        Returns:
            List of conflict entries
        """
        conflicts = []

        for normalized_term, term_data in self.merged_definitions.items():
            source_defs = self._extract_source_definitions(normalized_term)

            if len(source_defs) < 2:
                continue  # Need at least 2 sources to have conflict

            # Check for definition length divergence
            definitions = [
                d.get("definition", "")
                for d in source_defs.values()
                if "definition" in d
            ]

            if len(definitions) >= 2:
                # Simple conflict detection: check if definitions differ significantly
                unique_defs = set(definitions)
                if len(unique_defs) > 1:
                    # Potential conflict - definitions are different
                    conflict_sources = list(source_defs.keys())

                    conflicts.append(
                        {
                            "term": term_data["term"],
                            "normalized_term": normalized_term,
                            "conflict_type": "definition_divergence",
                            "sources": conflict_sources,
                            "severity": "low",  # Default severity
                            "description": (
                                f"Multiple distinct definitions found "
                                f"across {len(conflict_sources)} sources"
                            ),
                        }
                    )

        self.conflicts = conflicts
        return conflicts

    def compute_meaning_divergence_index(self) -> dict[str, Any]:
        """
        Compute meaning divergence index for all terms.

        Measures semantic drift and conflict levels.

        Returns:
            Divergence index dictionary
        """
        divergence_index = {}

        for normalized_term, _term_data in self.merged_definitions.items():
            source_defs = self._extract_source_definitions(normalized_term)

            # Calculate divergence score
            divergence_score = self._calculate_divergence_score(source_defs)

            # Identify conflict sources
            conflict_sources = []
            for conflict in self.conflicts:
                if conflict["normalized_term"] == normalized_term:
                    conflict_sources = conflict["sources"]
                    break

            # Calculate era drift
            era_drift = self._calculate_era_drift(source_defs)

            divergence_index[normalized_term] = {
                "divergence_score": divergence_score,
                "conflict_sources": conflict_sources,
                "era_drift": era_drift,
                "source_count": len(source_defs),
            }

        self.divergence_index = divergence_index
        return divergence_index

    def _calculate_divergence_score(self, source_defs: dict[str, Any]) -> float:
        """
        Calculate divergence score based on definition variations.

        Args:
            source_defs: Dictionary of source definitions

        Returns:
            Divergence score (0.0-1.0)
        """
        if len(source_defs) < 2:
            return 0.0

        # Extract definitions
        definitions = [
            d.get("definition", "") for d in source_defs.values() if "definition" in d
        ]

        if len(definitions) < 2:
            return 0.0

        # Simple divergence: ratio of unique definitions to total
        unique_count = len(set(definitions))
        total_count = len(definitions)

        # Calculate divergence (higher when more unique definitions)
        divergence = (unique_count - 1) / total_count if total_count > 1 else 0.0

        # Cap at 1.0
        return min(divergence, 1.0)

    def _calculate_era_drift(self, source_defs: dict[str, Any]) -> dict[str, float]:
        """
        Calculate era-to-era semantic drift.

        Args:
            source_defs: Dictionary of source definitions

        Returns:
            Dictionary mapping era ranges to drift scores
        """
        era_drift = {}

        # Compare historical (Bouvier 1856) to contemporary (Black's 2019)
        if "bouvier" in source_defs and "blacks" in source_defs:
            bouvier_def = source_defs["bouvier"].get("definition", "")
            blacks_def = source_defs["blacks"].get("definition", "")

            if bouvier_def and blacks_def:
                # Simple drift measure: 0 if same, 1 if different
                drift = 0.0 if bouvier_def == blacks_def else 1.0
                era_drift["1791→2024"] = drift

        return era_drift

    def apply_era_adjustments(self, era: int) -> dict[str, Any]:
        """
        Apply era-specific adjustments to harmonization matrix.

        Args:
            era: Year representing the era (e.g., 1791, 1868, 2024)

        Returns:
            Era-adjusted harmonization matrix
        """
        era_adjusted = {}

        for normalized_term, entry in self.harmonization_matrix.items():
            era_adjustments = entry.get("era_adjustments", {})

            # Find the closest era
            closest_era = self._find_closest_era(era, list(era_adjustments.keys()))

            if closest_era:
                # Create adjusted entry
                era_adjusted[normalized_term] = {
                    **entry,
                    "era_specific_meaning": era_adjustments[closest_era],
                    "applied_era": closest_era,
                }
            else:
                # No era adjustment available
                era_adjusted[normalized_term] = entry

        return era_adjusted

    def _find_closest_era(self, target_era: int, available_eras: list[str]) -> str:
        """
        Find the closest available era to the target era.

        Args:
            target_era: Target year
            available_eras: List of available era year strings

        Returns:
            Closest era year as string, or empty string if none available
        """
        if not available_eras:
            return ""

        # Convert to integers
        era_years = [int(era) for era in available_eras]

        # Find closest
        closest = min(era_years, key=lambda x: abs(x - target_era))

        return str(closest)

    def generate_artifacts(self) -> dict[str, Any]:
        """
        Generate all harmonization artifacts.

        Creates:
        - SEMANTIC_HARMONIZATION_MATRIX.json
        - MEANING_DIVERGENCE_INDEX.json

        Returns:
            Status report with artifact paths
        """
        # Build harmonization matrix if not already built
        if not self.harmonization_matrix:
            self.build_harmonization_matrix()

        # Detect conflicts if not already detected
        if not self.conflicts:
            self.detect_semantic_conflicts()

        # Compute divergence index if not already computed
        if not self.divergence_index:
            self.compute_meaning_divergence_index()

        # Generate SEMANTIC_HARMONIZATION_MATRIX.json
        matrix_data = {
            "version": self.VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_terms": len(self.harmonization_matrix),
            "source_weights": self.SOURCE_WEIGHTS,
            "terms": self.harmonization_matrix,
        }
        matrix_path = self.output_dir / "SEMANTIC_HARMONIZATION_MATRIX.json"
        with open(matrix_path, "w", encoding="utf-8") as f:
            json.dump(matrix_data, f, indent=2, ensure_ascii=False)

        # Generate MEANING_DIVERGENCE_INDEX.json
        divergence_data = {
            "version": self.VERSION,
            "schema_version": self.SCHEMA_VERSION,
            "generated": datetime.now(UTC).isoformat(),
            "total_terms": len(self.divergence_index),
            "conflict_count": len(self.conflicts),
            "conflicts": self.conflicts,
            "terms": self.divergence_index,
        }
        divergence_path = self.output_dir / "MEANING_DIVERGENCE_INDEX.json"
        with open(divergence_path, "w", encoding="utf-8") as f:
            json.dump(divergence_data, f, indent=2, ensure_ascii=False)

        return {
            "success": True,
            "matrix_path": str(matrix_path),
            "divergence_path": str(divergence_path),
            "total_terms": len(self.harmonization_matrix),
            "conflicts_detected": len(self.conflicts),
        }


def main():
    """CLI entry point for semantic harmonizer."""
    harmonizer = SemanticHarmonizer()

    print("Loading lexicon sources...")
    load_result = harmonizer.load_lexicon_sources()
    print(f"Loaded: {load_result}")

    if not load_result["success"]:
        print("Failed to load lexicon sources")
        return

    print("\nBuilding harmonization matrix...")
    matrix = harmonizer.build_harmonization_matrix()
    print(f"Matrix built with {len(matrix)} terms")

    print("\nDetecting semantic conflicts...")
    conflicts = harmonizer.detect_semantic_conflicts()
    print(f"Detected {len(conflicts)} conflicts")

    print("\nComputing meaning divergence index...")
    divergence = harmonizer.compute_meaning_divergence_index()
    print(f"Divergence index computed for {len(divergence)} terms")

    print("\nGenerating artifacts...")
    artifacts = harmonizer.generate_artifacts()
    print(f"Artifacts: {artifacts}")

    print("\n[OK] Semantic harmonization complete!")


if __name__ == "__main__":
    main()
