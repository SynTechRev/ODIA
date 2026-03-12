"""
CDSCE Semantic Drift Analyzer.

Analyzes semantic drift across eras, measuring how term meanings evolve or
degrade over time. Provides era-aware drift scoring weighted by linguistic
lineage and constitutional interpretive methods.
"""

from datetime import UTC, datetime
from typing import Any


class CDSCEDriftAnalyzer:
    """
    Semantic Drift Analyzer for CDSCE.

    Capabilities:
    - Era-aware drift detection
    - Drift scoring (0.0 = no drift, 1.0 = full inversion)
    - Linguistic lineage weighting
    - CLF interpretive method correlation
    - Court era analysis
    - Meaning evolution tracking
    """

    VERSION = "1.0.0"

    # Era definitions with weights for drift calculation
    ERAS = {
        1789: {"name": "Founding Era", "weight": 1.0},
        1791: {"name": "Bill of Rights", "weight": 1.0},
        1868: {"name": "Reconstruction (14th Amendment)", "weight": 0.95},
        1920: {"name": "Early Modern", "weight": 0.8},
        1960: {"name": "Civil Rights Era", "weight": 0.7},
        2000: {"name": "Digital Age", "weight": 0.6},
        2024: {"name": "Contemporary", "weight": 0.5},
    }

    # Linguistic lineage weights (higher = more authoritative)
    LINEAGE_WEIGHTS = {
        "latin": 1.0,  # Classical Latin - highest authority
        "greek": 0.95,  # Classical Greek
        "canon_law": 0.9,  # Medieval Canon Law
        "common_law": 0.85,  # English Common Law
        "statutory": 0.7,  # Modern statutory
        "colloquial": 0.5,  # Modern colloquial usage
    }

    def __init__(self):
        """Initialize drift analyzer."""
        self.drift_results: dict[str, Any] = {}
        self.era_comparisons: list[dict[str, Any]] = []
        self.lineage_analyses: dict[str, Any] = {}

    def calculate_drift_score(
        self,
        term: str,
        definitions: dict[int, str],
        lineage: str = "common_law",
    ) -> float:
        """
        Calculate semantic drift score for a term across eras.

        Args:
            term: Legal term being analyzed
            definitions: Dict mapping era year to definition text
            lineage: Linguistic lineage (latin, greek, canon_law, etc.)

        Returns:
            Drift score from 0.0 (no drift) to 1.0 (full meaning inversion)
        """
        if len(definitions) < 2:
            return 0.0

        # Sort definitions by era
        sorted_eras = sorted(definitions.keys())

        # Calculate pairwise drift between consecutive eras
        drift_scores = []
        for i in range(len(sorted_eras) - 1):
            era1 = sorted_eras[i]
            era2 = sorted_eras[i + 1]

            def1 = definitions[era1]
            def2 = definitions[era2]

            # Calculate lexical similarity
            pairwise_drift = self._calculate_pairwise_drift(def1, def2)

            # Weight by era difference
            era_weight = self._get_era_weight(era1, era2)

            # Weight by linguistic lineage
            lineage_weight = self.LINEAGE_WEIGHTS.get(lineage, 0.7)

            weighted_drift = pairwise_drift * era_weight * lineage_weight

            drift_scores.append(weighted_drift)

        # Return average drift
        return sum(drift_scores) / len(drift_scores) if drift_scores else 0.0

    def _calculate_pairwise_drift(self, def1: str, def2: str) -> float:
        """
        Calculate drift between two definitions.

        Uses simple word overlap metric. Lower overlap = higher drift.
        """
        if not def1 or not def2:
            return 0.5

        # Tokenize and normalize
        words1 = set(def1.lower().split())
        words2 = set(def2.lower().split())

        # Remove common words
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "that",
            "which",
        }
        words1 = words1 - stopwords
        words2 = words2 - stopwords

        if not words1 or not words2:
            return 0.5

        # Calculate Jaccard distance (1 - Jaccard similarity)
        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.5

        jaccard_similarity = intersection / union
        jaccard_distance = 1.0 - jaccard_similarity

        return jaccard_distance

    def _get_era_weight(self, era1: int, era2: int) -> float:
        """
        Get weight modifier based on era difference.

        Larger gaps in time increase drift impact.
        """
        year_diff = abs(era2 - era1)

        if year_diff <= 10:
            return 0.5
        elif year_diff <= 50:
            return 0.7
        elif year_diff <= 100:
            return 0.9
        else:
            return 1.0

    def detect_drift_spike(
        self,
        term: str,
        definitions: dict[int, str],
        threshold: float = 0.7,
    ) -> dict[str, Any]:
        """
        Detect sudden spikes in semantic drift.

        Args:
            term: Legal term being analyzed
            definitions: Dict mapping era year to definition text
            threshold: Drift threshold for spike detection (default 0.7)

        Returns:
            Drift spike detection result
        """
        sorted_eras = sorted(definitions.keys())

        spikes = []
        for i in range(len(sorted_eras) - 1):
            era1 = sorted_eras[i]
            era2 = sorted_eras[i + 1]

            def1 = definitions[era1]
            def2 = definitions[era2]

            pairwise_drift = self._calculate_pairwise_drift(def1, def2)

            if pairwise_drift >= threshold:
                spikes.append(
                    {
                        "from_era": era1,
                        "to_era": era2,
                        "drift_score": round(pairwise_drift, 3),
                        "from_definition": (
                            def1[:100] + "..." if len(def1) > 100 else def1
                        ),
                        "to_definition": (
                            def2[:100] + "..." if len(def2) > 100 else def2
                        ),
                    }
                )

        return {
            "term": term,
            "has_spike": len(spikes) > 0,
            "spike_count": len(spikes),
            "spikes": spikes,
        }

    def analyze_meaning_inversion(
        self,
        term: str,
        original_meaning: str,
        modern_meaning: str,
        inversion_indicators: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze if a term's meaning has inverted over time.

        Args:
            term: Legal term being analyzed
            original_meaning: Original/classical definition
            modern_meaning: Modern definition
            inversion_indicators: List of words indicating semantic inversion

        Returns:
            Inversion analysis result
        """
        if inversion_indicators is None:
            inversion_indicators = [
                "not",
                "opposite",
                "contrary",
                "inverse",
                "reverse",
                "no longer",
                "formerly",
                "originally",
                "now means",
            ]

        # Check for explicit inversion indicators
        modern_lower = modern_meaning.lower()
        indicators_found = [ind for ind in inversion_indicators if ind in modern_lower]

        # Calculate semantic distance
        drift_score = self._calculate_pairwise_drift(original_meaning, modern_meaning)

        # Determine if inversion likely
        is_inversion = drift_score >= 0.8 or len(indicators_found) > 0

        return {
            "term": term,
            "is_inversion": is_inversion,
            "drift_score": round(drift_score, 3),
            "inversion_indicators_found": indicators_found,
            "confidence": self._calculate_inversion_confidence(
                drift_score, len(indicators_found)
            ),
        }

    def _calculate_inversion_confidence(
        self, drift_score: float, indicator_count: int
    ) -> float:
        """Calculate confidence score for meaning inversion (0.0-1.0)."""
        # Base confidence from drift score
        confidence = drift_score * 0.7

        # Add confidence from indicators
        confidence += min(indicator_count * 0.15, 0.3)

        return min(confidence, 1.0)

    def analyze_interpretive_instability(
        self,
        term: str,
        case_definitions: dict[str, str],
    ) -> dict[str, Any]:
        """
        Analyze interpretive instability across court cases.

        Args:
            term: Legal term being analyzed
            case_definitions: Dict mapping case_id to term definition in that case

        Returns:
            Instability analysis result
        """
        if len(case_definitions) < 2:
            return {
                "term": term,
                "instability_score": 0.0,
                "is_unstable": False,
                "variation_count": 0,
            }

        # Calculate pairwise drift between all case definitions
        cases = list(case_definitions.keys())
        drift_scores = []

        for i in range(len(cases)):
            for j in range(i + 1, len(cases)):
                def1 = case_definitions[cases[i]]
                def2 = case_definitions[cases[j]]
                drift = self._calculate_pairwise_drift(def1, def2)
                drift_scores.append(drift)

        # Calculate average instability
        avg_instability = sum(drift_scores) / len(drift_scores)

        # Consider unstable if avg drift > 0.5
        is_unstable = avg_instability > 0.5

        return {
            "term": term,
            "instability_score": round(avg_instability, 3),
            "is_unstable": is_unstable,
            "variation_count": len(case_definitions),
            "pairwise_comparisons": len(drift_scores),
        }

    def generate_drift_report(
        self,
        term: str,
        correlation_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate comprehensive drift report for a term.

        Args:
            term: Legal term
            correlation_data: Full correlation data from CDSCE engine

        Returns:
            Comprehensive drift report
        """
        # Extract era definitions
        era_definitions = {}
        for era_str, era_data in correlation_data.get("era_definitions", {}).items():
            era_definitions[int(era_str)] = era_data.get("definition", "")

        # Calculate overall drift score
        lineage = "common_law"
        if correlation_data.get("etymology_lineage"):
            lineage = correlation_data["etymology_lineage"][0].get(
                "language", "common_law"
            )

        overall_drift = self.calculate_drift_score(term, era_definitions, lineage)

        # Detect drift spikes
        spike_analysis = self.detect_drift_spike(term, era_definitions)

        # Build report
        report = {
            "term": term,
            "overall_drift_score": round(overall_drift, 3),
            "linguistic_lineage": lineage,
            "era_count": len(era_definitions),
            "has_drift_spike": spike_analysis["has_spike"],
            "spike_count": spike_analysis["spike_count"],
            "spikes": spike_analysis["spikes"],
            "drift_category": self._categorize_drift(overall_drift),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        return report

    def _categorize_drift(self, drift_score: float) -> str:
        """Categorize drift score into descriptive category."""
        if drift_score < 0.2:
            return "minimal"
        elif drift_score < 0.4:
            return "low"
        elif drift_score < 0.6:
            return "moderate"
        elif drift_score < 0.8:
            return "high"
        else:
            return "severe"

    def get_statistics(self) -> dict[str, Any]:
        """Get drift analyzer statistics."""
        return {
            "version": self.VERSION,
            "terms_analyzed": len(self.drift_results),
            "era_comparisons": len(self.era_comparisons),
            "lineage_analyses": len(self.lineage_analyses),
        }
