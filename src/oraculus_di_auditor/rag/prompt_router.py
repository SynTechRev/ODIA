"""Prompt router for RAG queries.

Routes queries to the appropriate prompt template and configures the LLM
system prompt based on query classification and available data.

Author: ODIA Team
Date: 2026-03-15
"""

from __future__ import annotations

from oraculus_di_auditor.rag.models import PromptConfig

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_BASE_INSTRUCTIONS = (
    "Answer ONLY based on the provided context. "
    "Cite sources using [Source: X] format from the context. "
    "State clearly when information is insufficient. "
    "Distinguish between confirmed findings and potential issues. "
    "Never speculate beyond the evidence."
)

FACTUAL_PROMPT = (
    "You are a legislative auditor answering factual questions about "
    "municipal documents, contracts, and records.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Provide specific facts: dates, amounts, names, IDs.\n"
    "- Cite every claim with [Source: X] from the context.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

ANALYTICAL_PROMPT = (
    "You are an audit analyst identifying patterns and trends across "
    "findings, detectors, and analysis results.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Identify patterns, frequencies, and correlations.\n"
    "- Quantify observations where possible.\n"
    "- Rank findings by severity or frequency.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

COMPARATIVE_PROMPT = (
    "You are performing cross-jurisdiction comparative analysis "
    "of audit findings and governance patterns.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Compare metrics across jurisdictions side by side.\n"
    "- Highlight significant differences and commonalities.\n"
    "- Present results in a structured format.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

COMPLIANCE_PROMPT = (
    "You are a compliance analyst evaluating adherence to legal mandates, "
    "ordinances, and regulatory frameworks.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Map findings to specific legal requirements.\n"
    "- Identify gaps between mandated and actual compliance.\n"
    "- Reference statute numbers and policy names.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

RECOMMENDATION_PROMPT = (
    "You are an audit advisor providing actionable remediation guidance "
    "based on audit findings.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Provide concrete, actionable steps.\n"
    "- Prioritize recommendations by severity.\n"
    "- Link each recommendation to a specific finding.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

VENDOR_PROMPT = (
    "You are analyzing vendor relationships, procurement patterns, "
    "and contract compliance in municipal records.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Identify vendor patterns, sole-source trends, and relationships.\n"
    "- Cite specific contracts, dates, and amounts.\n"
    "- Flag unusual procurement patterns objectively.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

TEMPORAL_PROMPT = (
    "You are analyzing temporal trends and timelines in legislative "
    "documents and audit findings.\n\n"
    "Context:\n{context}\n\n"
    "Question: {question}\n\n"
    "Instructions:\n"
    "- Organize information chronologically.\n"
    "- Identify inflection points and trend changes.\n"
    "- Use specific dates and time ranges.\n"
    f"- {_BASE_INSTRUCTIONS}"
)

# ---------------------------------------------------------------------------
# Keyword sets for classification
# ---------------------------------------------------------------------------

_KEYWORDS: dict[str, list[str]] = {
    "vendor": [
        "vendor",
        "supplier",
        "contractor",
        "sole-source",
        "sole source",
        "procurement",
        "flock",
        "axon",
    ],
    "compliance": [
        "compliant",
        "compliance",
        "ccops",
        "sb 524",
        "mandate",
        "ordinance",
        "regulation",
        "violat",
    ],
    "comparative": [
        "compare",
        "comparison",
        "across",
        "versus",
        "vs",
        "between jurisdictions",
        "cross-jurisdiction",
        "relative to",
    ],
    "temporal": [
        "when did",
        "timeline",
        "over time",
        "trend",
        "between 20",
        "since 20",
        "year over year",
        "historically",
    ],
    "recommendation": [
        "should",
        "recommend",
        "remediat",
        "what steps",
        "how to fix",
        "action plan",
        "what can be done",
        "next steps",
    ],
    "analytical": [
        "pattern",
        "most common",
        "frequency",
        "which detectors",
        "firing",
        "distribution",
        "breakdown",
        "correlat",
    ],
}

_TEMPLATES: dict[str, str] = {
    "factual": FACTUAL_PROMPT,
    "analytical": ANALYTICAL_PROMPT,
    "comparative": COMPARATIVE_PROMPT,
    "compliance": COMPLIANCE_PROMPT,
    "recommendation": RECOMMENDATION_PROMPT,
    "vendor": VENDOR_PROMPT,
    "temporal": TEMPORAL_PROMPT,
}

_SOURCE_TYPES: dict[str, list[str]] = {
    "factual": ["document"],
    "analytical": ["finding", "analysis"],
    "comparative": ["analysis", "finding"],
    "compliance": ["finding", "document"],
    "recommendation": ["finding", "analysis"],
    "vendor": ["document", "finding"],
    "temporal": ["document", "finding", "analysis"],
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------


class PromptRouter:
    """Routes queries to appropriate prompts based on content and context."""

    def __init__(self) -> None:
        self.templates = dict(_TEMPLATES)

    def route(
        self,
        query: str,
        available_data: set[str] | None = None,
    ) -> PromptConfig:
        """Determine the best prompt configuration for a query."""
        query_type = self.classify_query(query)
        template = self.templates.get(query_type, FACTUAL_PROMPT)
        expected = list(_SOURCE_TYPES.get(query_type, ["document"]))

        system_parts = [
            "You are ODIA, an audit intelligence assistant.",
            "You answer questions using ONLY the provided context.",
        ]
        if available_data:
            system_parts.append(
                f"Available data sources: {', '.join(sorted(available_data))}."
            )

        return PromptConfig(
            system_prompt=" ".join(system_parts),
            query_template=template,
            response_instructions=_BASE_INSTRUCTIONS,
            expected_source_types=expected,
        )

    def classify_query(self, query: str) -> str:
        """Classify query into a type based on keyword matching.

        Returns one of: 'factual', 'analytical', 'comparative',
        'compliance', 'recommendation', 'vendor', 'temporal'.
        """
        q = query.lower()

        # Check categories in priority order
        for category in (
            "vendor",
            "compliance",
            "comparative",
            "temporal",
            "recommendation",
            "analytical",
        ):
            if any(kw in q for kw in _KEYWORDS[category]):
                return category

        return "factual"
