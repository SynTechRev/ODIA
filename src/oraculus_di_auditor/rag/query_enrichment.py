"""Audit-aware query enrichment for RAG.

Expands user queries with ODIA-specific terminology so retrieval finds
relevant documents even when the user uses colloquial or abbreviated terms.

Two-layer matching:
  1. Concept keys — the concept name itself appears in the query ("grant")
  2. Trigger terms — an abbreviation or alias triggers the concept ("JAG")
"""

from __future__ import annotations

from oraculus_di_auditor.rag.models import EnrichedQuery


class QueryEnricher:
    """Enriches queries with domain-specific and legal terminology."""

    CONCEPT_EXPANSIONS: dict[str, list[str]] = {
        # --- Documentary / operational concepts ---
        "surveillance": [
            "ALPR",
            "license plate reader",
            "LPR",
            "body camera",
            "BWC",
            "body-worn camera",
            "facial recognition",
            "drone",
            "UAS",
            "geofence",
            "stingray",
            "real-time tracking",
            "Flock Safety",
            "Axon",
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
            "executed",
            "authorization",
        ],
        "procurement": [
            "sole source",
            "sole-source",
            "competitive bid",
            "RFP",
            "RFQ",
            "purchase order",
            "requisition",
            "consent calendar",
        ],
        "governance": [
            "privacy policy",
            "use policy",
            "data retention",
            "oversight",
            "audit log",
            "CCOPS",
            "AB 481",
            "annual report",
            "technology use policy",
        ],
        "vendor": [
            "Axon",
            "Flock Safety",
            "Motorola",
            "Vigilant",
            "Ring",
            "Clearview",
            "Palantir",
            "BCS Consulting",
            "surveillance vendor",
        ],
        # --- Grant and federal compliance ---
        "grant": [
            "JAG",
            "Justice Assistance Grant",
            "Edward Byrne",
            "Byrne grant",
            "COPS",
            "BJA",
            "Bureau of Justice Assistance",
            "OJP",
            "Office of Justice Programs",
            "DOJ grant",
            "ARPA",
            "federal grant",
            "anti-supplanting",
            "award number",
            "grant certification",
            "2 CFR",
            "Uniform Guidance",
            "34 USC 10152",
            "34 U.S.C. 10152",
            "grant compliance",
        ],
        # --- Public records and CPRA ---
        "public_records": [
            "CPRA",
            "California Public Records Act",
            "Government Code 7920",
            "Gov. Code 7920",
            "Government Code 6250",
            "public records request",
            "FOIA",
            "records request",
            "disclosure",
            "exemption",
            "AB 1421",
            "SB 1421",
        ],
        # --- Surveillance law ---
        "surveillance_law": [
            "AB 481",
            "AB481",
            "Civil Code 1798.90",
            "Civil Code section 1798",
            "SB 34",
            "ALPR data retention",
            "usage policy",
            "privacy policy citation",
            "data-retention policy",
            "community oversight",
            "technology use policy",
            "annual report",
            "SSHRB",
        ],
        # --- Constitutional and civil rights ---
        "constitutional": [
            "Fourth Amendment",
            "42 USC 1983",
            "42 U.S.C. 1983",
            "Carpenter",
            "mosaic theory",
            "reasonable expectation of privacy",
            "due process",
            "Fourteenth Amendment",
            "equal protection",
        ],
        # --- Retroactive / vote-date anomalies ---
        "retroactive": [
            "retroactive",
            "nunc pro tunc",
            "pre-authorization",
            "executed before",
            "ratification",
            "consent calendar",
            "urgency ordinance",
            "four-fifths vote",
            "backdated",
        ],
    }

    # Maps trigger words / phrases → the concept they should activate.
    # Keys are lowercase. Checked against query.lower().
    TRIGGER_MAP: dict[str, str] = {
        # Grant triggers
        "jag": "grant",
        "byrne": "grant",
        "bja": "grant",
        "ojp": "grant",
        "anti-supplanting": "grant",
        "supplanting": "grant",
        "award number": "grant",
        "2 cfr": "grant",
        "uniform guidance": "grant",
        "34 u.s.c": "grant",
        "10152": "grant",
        # Surveillance triggers
        "alpr": "surveillance",
        "license plate": "surveillance",
        "body camera": "surveillance",
        "body-worn": "surveillance",
        "bwc": "surveillance",
        "flock": "surveillance",
        "flock safety": "vendor",
        "axon": "vendor",
        # Public records triggers
        "cpra": "public_records",
        "public records": "public_records",
        "records request": "public_records",
        "6250": "public_records",
        "7920": "public_records",
        "7923": "public_records",
        "6258": "public_records",
        "foia": "public_records",
        # Surveillance law triggers
        "ab 481": "surveillance_law",
        "ab481": "surveillance_law",
        "1798.90": "surveillance_law",
        "sb 34": "surveillance_law",
        "technology use policy": "surveillance_law",
        # Constitutional triggers
        "fourth amendment": "constitutional",
        "1983": "constitutional",
        "42 usc": "constitutional",
        "carpenter": "constitutional",
        "mosaic": "constitutional",
        # Retroactive / vote-date triggers
        "retroactive": "retroactive",
        "nunc pro tunc": "retroactive",
        "pre-authorization": "retroactive",
        "urgency": "retroactive",
        "consent calendar": "procurement",
    }

    def enrich(self, query: str) -> EnrichedQuery:
        """Expand query with domain and legal terminology."""
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

        search_queries = [query]
        for concept in concepts:
            terms = self.CONCEPT_EXPANSIONS[concept]
            search_queries.append(f"{query} {' '.join(terms[:4])}")

        return EnrichedQuery(
            original_query=query,
            expanded_terms=expanded,
            search_queries=search_queries,
            detected_concepts=concepts,
        )

    def detect_concepts(self, query: str) -> list[str]:
        """Identify concept categories from the query.

        Checks both concept keys and trigger terms so abbreviated or
        legal-term queries (e.g. 'JAG violations') activate the right
        expansion group ('grant') even when the key word is absent.
        """
        q = query.lower()
        detected: set[str] = set()

        # Layer 1: concept key appears in query
        for concept in self.CONCEPT_EXPANSIONS:
            if concept in q:
                detected.add(concept)

        # Layer 2: trigger term appears in query
        for trigger, concept in self.TRIGGER_MAP.items():
            if trigger in q:
                detected.add(concept)

        return sorted(detected)
