"""Audit-aware query enrichment for RAG.

Expands user queries with ODIA-specific terminology so retrieval finds
relevant documents even when the user uses colloquial terms.

Author: ODIA Team
Date: 2026-03-15
"""

from __future__ import annotations

from oraculus_di_auditor.rag.models import EnrichedQuery


class QueryEnricher:
    """Enriches queries with domain-specific terminology."""

    CONCEPT_EXPANSIONS: dict[str, list[str]] = {
        "surveillance": [
            "ALPR",
            "license plate reader",
            "body camera",
            "BWC",
            "facial recognition",
            "drone",
            "UAS",
            "geofence",
            "stingray",
            "real-time",
        ],
        "contract": [
            "MSPA",
            "MSA",
            "PSA",
            "SOW",
            "MOU",
            "amendment",
            "order form",
            "agreement",
        ],
        "procurement": [
            "sole source",
            "sole-source",
            "competitive bid",
            "RFP",
            "RFQ",
            "purchase order",
            "requisition",
        ],
        "unsigned": [
            "signature blank",
            "not executed",
            "placeholder",
            "DocuSign pending",
            "unsigned",
        ],
        "governance": [
            "privacy policy",
            "use policy",
            "retention policy",
            "oversight",
            "audit log",
            "CCOPS",
            "SIR",
        ],
        "grant": [
            "JAG",
            "Byrne",
            "COPS",
            "BJA",
            "OJP",
            "DOJ grant",
            "ARPA",
            "federal grant",
        ],
        "vendor": [
            "Axon",
            "Flock",
            "Motorola",
            "Vigilant",
            "Ring",
            "Clearview",
            "Palantir",
        ],
    }

    def enrich(self, query: str) -> EnrichedQuery:
        """Expand query with domain terminology."""
        concepts = self.detect_concepts(query)

        if not concepts:
            return EnrichedQuery(
                original_query=query,
                expanded_terms=[],
                search_queries=[query],
                detected_concepts=[],
            )

        expanded: list[str] = []
        for concept in concepts:
            expanded.extend(self.CONCEPT_EXPANSIONS[concept])

        # Build additional search queries by appending key expansion terms
        search_queries = [query]
        for concept in concepts:
            terms = self.CONCEPT_EXPANSIONS[concept]
            augmented = f"{query} {' '.join(terms[:3])}"
            search_queries.append(augmented)

        return EnrichedQuery(
            original_query=query,
            expanded_terms=expanded,
            search_queries=search_queries,
            detected_concepts=concepts,
        )

    def detect_concepts(self, query: str) -> list[str]:
        """Identify which concept categories appear in the query."""
        q = query.lower()
        return [concept for concept in self.CONCEPT_EXPANSIONS if concept in q]
