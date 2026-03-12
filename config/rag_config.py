"""Configuration for RAG (Retrieval-Augmented Generation) system.

This module defines configuration constants and environment variables
for the RAG query-answering system.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import os

# ============================================================================
# LLM Configuration
# ============================================================================

# Provider selection: "openai" | "anthropic" | "ollama"
RAG_LLM_PROVIDER = os.getenv("RAG_LLM_PROVIDER", "openai")

# Model names (provider-specific defaults)
RAG_LLM_MODEL = os.getenv(
    "RAG_LLM_MODEL",
    "gpt-4o-mini",  # Cost-effective default for OpenAI
)

# Sampling temperature (0.0-2.0, lower = more deterministic)
# Low temperature recommended for factual question-answering
RAG_TEMPERATURE = float(os.getenv("RAG_TEMPERATURE", "0.1"))

# Maximum tokens for LLM response
RAG_MAX_RESPONSE_TOKENS = int(os.getenv("RAG_MAX_RESPONSE_TOKENS", "1000"))

# ============================================================================
# Retrieval Configuration
# ============================================================================

# Number of documents to retrieve
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

# Minimum similarity threshold (0.0-1.0)
# Results below this threshold are filtered out
RAG_SIMILARITY_THRESHOLD = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.3"))

# Maximum tokens for context assembly
# This is the token budget for all retrieved documents combined
RAG_MAX_CONTEXT_TOKENS = int(os.getenv("RAG_MAX_CONTEXT_TOKENS", "4000"))

# ============================================================================
# API Keys (Provider Authentication)
# ============================================================================

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Anthropic API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Ollama base URL (for local models)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ============================================================================
# Vector Index Paths
# ============================================================================

# Default vector index paths for different collections
VECTOR_INDICES = {
    "corpus": "data/vectors/collection",  # Main corpus (extracted PDF text)
    "ace": "data/vectors/ace_collection",  # Anomaly reports (ACE)
    "vicfm": "data/vectors/vicfm_collection",  # Vendor influence (VICFM)
    "jim": "data/vectors/jim_collection",  # Legal correlations (JIM)
    "lexicon": "data/vectors/lexicon_collection",  # Legal dictionary
}

# Default vocabulary file path
DEFAULT_VOCAB_PATH = "data/vectors/collection_vocab.pkl"

# ============================================================================
# Feature Flags
# ============================================================================

# Enable response caching (future feature)
RAG_ENABLE_CACHING = os.getenv("RAG_ENABLE_CACHING", "true").lower() == "true"

# Enable streaming responses (future feature)
RAG_ENABLE_STREAMING = os.getenv("RAG_ENABLE_STREAMING", "false").lower() == "true"

# Enable multi-index routing (route queries to appropriate indices)
RAG_ENABLE_ROUTING = os.getenv("RAG_ENABLE_ROUTING", "true").lower() == "true"

# ============================================================================
# Logging
# ============================================================================

# RAG-specific logging level
RAG_LOG_LEVEL = os.getenv("RAG_LOG_LEVEL", "INFO")

# Log LLM API calls (useful for debugging, may expose sensitive data)
RAG_LOG_API_CALLS = os.getenv("RAG_LOG_API_CALLS", "false").lower() == "true"

# ============================================================================
# Validation
# ============================================================================


def validate_config() -> dict[str, str]:
    """Validate RAG configuration and return status report.

    Returns:
        Dictionary with validation status and warnings
    """
    issues = []

    # Check LLM provider configuration
    if RAG_LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        issues.append("OpenAI provider selected but OPENAI_API_KEY not set")
    elif RAG_LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        issues.append("Anthropic provider selected but ANTHROPIC_API_KEY not set")
    elif RAG_LLM_PROVIDER not in ["openai", "anthropic", "ollama"]:
        issues.append(f"Invalid provider: {RAG_LLM_PROVIDER}")

    # Check temperature range
    if not 0.0 <= RAG_TEMPERATURE <= 2.0:
        issues.append(f"Temperature {RAG_TEMPERATURE} outside valid range [0.0, 2.0]")

    # Check top_k is positive
    if RAG_TOP_K <= 0:
        issues.append(f"TOP_K must be positive, got {RAG_TOP_K}")

    # Check threshold range
    if not 0.0 <= RAG_SIMILARITY_THRESHOLD <= 1.0:
        issues.append(
            f"Similarity threshold {RAG_SIMILARITY_THRESHOLD} outside valid range [0.0, 1.0]"
        )

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "provider": RAG_LLM_PROVIDER,
        "model": RAG_LLM_MODEL,
    }


__all__ = [
    "RAG_LLM_PROVIDER",
    "RAG_LLM_MODEL",
    "RAG_TEMPERATURE",
    "RAG_MAX_RESPONSE_TOKENS",
    "RAG_TOP_K",
    "RAG_SIMILARITY_THRESHOLD",
    "RAG_MAX_CONTEXT_TOKENS",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OLLAMA_BASE_URL",
    "VECTOR_INDICES",
    "DEFAULT_VOCAB_PATH",
    "RAG_ENABLE_CACHING",
    "RAG_ENABLE_STREAMING",
    "RAG_ENABLE_ROUTING",
    "RAG_LOG_LEVEL",
    "RAG_LOG_API_CALLS",
    "validate_config",
]
