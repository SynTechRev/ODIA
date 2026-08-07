"""LLM prompt templates for C.O.N.T.R.A. LLM-assisted sub-detectors.

PromptVersion instances are injected into detectors at construction so
that prompt IDs and versions appear in Finding.prompt_id / prompt_version.
The system_prompt and user_template fields hold the raw prompt text
consumed by any BaseLLMProvider.generate(prompt, context) implementation.

Prompt versioning follows semantic versioning; increment the version field
whenever the text changes (downstream reproducibility depends on it).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptVersion:
    """Immutable prompt template with stable ID and version string."""

    prompt_id: str
    version: str
    system_prompt: str
    user_template: str

    def render_user(self, **kwargs: str) -> str:
        """Interpolate user_template with the provided keyword arguments."""
        return self.user_template.format(**kwargs)


# ---------------------------------------------------------------------------
# L-11 Clause Extract — identify arbitration clause boundaries
# ---------------------------------------------------------------------------

L11_CLAUSE_EXTRACT = PromptVersion(
    prompt_id="contra.l11.clause_extract",
    version="1.0",
    system_prompt=(
        "You are a legal analyst specializing in consumer contract review. "
        "Your task is to identify every arbitration-related clause in the "
        "provided contract text. For each clause, return the exact verbatim "
        "opening sentence (maximum 15 words), the clause type "
        "(binding_mandatory, class_waiver, fee_allocation, administrator, "
        "confidentiality, discovery_limit, venue, appeal_waiver, faa_invocation, "
        "other), and whether it applies to BOTH parties or only to the consumer. "
        'Respond in JSON: [{"excerpt": str, "clause_type": str, '
        '"bilateral": bool}]. If no arbitration clauses exist, return [].'
    ),
    user_template="CONTRACT TEXT:\n\n{doc_excerpt}",
)

# ---------------------------------------------------------------------------
# L-13 Modification Notice — identify notice mechanism quality
# ---------------------------------------------------------------------------

L13_MODIFICATION_NOTICE = PromptVersion(
    prompt_id="contra.l13.modification_notice",
    version="1.0",
    system_prompt=(
        "You are a legal analyst reviewing how a company notifies consumers of "
        "material changes to terms of service or privacy notices. Identify the "
        "notice mechanism described in the text. Classify as one of: "
        "'email_advance' (advance email notice, reasonable time), "
        "'website_posting_only' (website or in-app posting without direct notice), "
        "'email_simultaneous' (email sent at same time as change takes effect), "
        "'no_notice_mechanism' (no notice described), or 'other'. "
        'Return JSON: {"notice_type": str, "excerpt": str (<=15 words)}.'
    ),
    user_template="CONTRACT TEXT:\n\n{doc_excerpt}",
)

# ---------------------------------------------------------------------------
# L-14 CCPA Category — classify data types per CCPA taxonomy
# ---------------------------------------------------------------------------

L14_CCPA_CATEGORY = PromptVersion(
    prompt_id="contra.l14.ccpa_category",
    version="1.0",
    system_prompt=(
        "You are a CCPA/CPRA compliance analyst. For the provided privacy notice "
        "text, identify which California Consumer Privacy Act categories of personal "
        "information are disclosed as collected. Use only these category codes: "
        "A (identifiers), B (personal records), C (protected classifications), "
        "D (commercial information), E (biometric), F (internet activity), "
        "G (geolocation), H (sensory/audio/visual), I (professional/employment), "
        "J (education), K (inferences), SPI (sensitive personal information per "
        "Cal. Civ. Code 1798.121). "
        'Return JSON: [{"category": str, "excerpt": str (<=15 words)}]. '
        "Include only categories with clear textual evidence."
    ),
    user_template="PRIVACY NOTICE TEXT:\n\n{doc_excerpt}",
)

# ---------------------------------------------------------------------------
# L-15 Retention Duration — extract explicit retention period language
# ---------------------------------------------------------------------------

L15_RETENTION_DURATION = PromptVersion(
    prompt_id="contra.l15.retention_duration",
    version="1.0",
    system_prompt=(
        "You are a data governance analyst reviewing retention language in "
        "consumer contracts and privacy notices. For each data category mentioned, "
        "identify the stated retention period (if any). If no period is stated, "
        "note 'undefined'. If vague language is used (e.g. 'as long as necessary', "
        "'for our business purposes'), note 'vague'. "
        'Return JSON: [{"data_category": str, "retention_stated": str, '
        '"excerpt": str (<=15 words)}].'
    ),
    user_template="CONTRACT/PRIVACY NOTICE TEXT:\n\n{doc_excerpt}",
)

# ---------------------------------------------------------------------------
# L-17 ML Training Scope — characterize training grant breadth
# ---------------------------------------------------------------------------

L17_TRAINING_SCOPE = PromptVersion(
    prompt_id="contra.l17.training_scope",
    version="1.0",
    system_prompt=(
        "You are an AI governance analyst reviewing consumer contracts for "
        "machine-learning training grants. Identify whether the contract grants "
        "the company the right to use consumer data for AI or ML training. "
        "For each grant found: classify the modalities covered (text, image, audio, "
        "video, biometric, other), whether the grant is perpetual, whether it is "
        "irrevocable, and whether an opt-out mechanism is provided. "
        'Return JSON: [{"modalities": [str], "perpetual": bool, '
        '"irrevocable": bool, "opt_out_available": bool, '
        '"excerpt": str (<=15 words)}]. Return [] if no training grant found.'
    ),
    user_template="CONTRACT TEXT:\n\n{doc_excerpt}",
)

# ---------------------------------------------------------------------------
# L-20 Dark Pattern Structure — structural AEC assessment
# ---------------------------------------------------------------------------

L20_DARK_PATTERN_STRUCTURE = PromptVersion(
    prompt_id="contra.l20.dark_pattern_structure",
    version="1.0",
    system_prompt=(
        "You are a consumer protection analyst trained in the Ring Order Automated "
        "Engagement Check (AEC) framework. Review the following contract text for "
        "dark patterns that impede informed consent. Classify each dark pattern "
        "found using these types: pre_checked_consent, nested_acceptance, "
        "scroll_to_accept, fine_print_exclusion, urgency_pressure, "
        "confusing_language, hidden_cost, forced_action. "
        "For each finding return: the type, the severity (low/medium/high/critical), "
        "and a verbatim excerpt (<=15 words) anchored to the problematic text. "
        'Return JSON: [{"pattern_type": str, "severity": str, '
        '"excerpt": str}]. Return [] if no dark patterns found.'
    ),
    user_template="CONTRACT TEXT:\n\n{doc_excerpt}",
)
