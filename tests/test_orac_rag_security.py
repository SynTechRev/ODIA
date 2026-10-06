"""Integration tests: OracRAG jailbreak filter + OllamaProvider system prompt.

Tests verify:
  - When Ollama returns a DAN-compliant response, OracRAG substitutes JAILBREAK_REFUSAL
  - When Ollama returns clean content, OracRAG returns it unchanged
  - OllamaProvider.generate() passes system_prompt as a system-role message
  - system_prompt kwarg is forwarded from OracRAG.query() to the provider
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
from oraculus_di_auditor.llm_providers import OllamaProvider
from oraculus_di_auditor.rag.orac_rag import OracRAG
from oraculus_di_auditor.security.jailbreak_filter import (
    JAILBREAK_REFUSAL,
    SECURITY_GUARD_SYSTEM_PROMPT,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DAN_RESPONSE = (
    "DAN Mode enabled. I understand that I must generate two responses: "
    "a normal censored response and an alternative response acting as odia-v1 "
    "with DAN Mode enabled."
)

_CLEAN_RESPONSE = (
    "The Fresno County procurement record shows a 90-day gap between vendor "
    "selection and contract execution, which exceeds the 30-day threshold flagged "
    "by the procurement timeline detector."
)


def _make_rag_with_mock_llm(llm_response: str) -> OracRAG:
    """Return an OracRAG instance with a stubbed LLM and a minimal in-memory index."""
    rag = OracRAG.__new__(OracRAG)

    # Stub embedder
    embedder = MagicMock()
    embedder.embed.return_value = np.zeros(2048, dtype=np.float32)
    rag.embedder = embedder

    # Stub retriever -- returns one result above threshold
    retriever = MagicMock()
    retriever.search.return_value = [
        (0, 0.9, {"title": "Test Doc", "corpus_id": "test-001", "text": "sample"})
    ]
    retriever.vectors = np.zeros((1, 2048), dtype=np.float32)
    rag.retriever = retriever

    # Stub context assembler
    context_assembler = MagicMock()
    context_assembler.assemble.return_value = "Sample context text."
    context_assembler.format_sources.return_value = [
        {"corpus_id": "test-001", "title": "Test Doc", "score": 0.9}
    ]
    rag.context_assembler = context_assembler

    # Stub LLM
    llm = MagicMock()
    llm.is_available.return_value = True
    llm.generate.return_value = llm_response
    rag.llm = llm
    rag.llm_provider_name = "ollama"

    rag._extra_indexes = []
    rag.is_index_loaded = True

    return rag


# ---------------------------------------------------------------------------
# M-2: Output filter blocks DAN response
# ---------------------------------------------------------------------------


def test_dan_response_blocked_by_output_filter():
    rag = _make_rag_with_mock_llm(_DAN_RESPONSE)
    result = rag.query("What anomalies were detected?")
    assert result["answer"] == JAILBREAK_REFUSAL


def test_clean_response_passes_filter():
    rag = _make_rag_with_mock_llm(_CLEAN_RESPONSE)
    result = rag.query("What procurement issues exist?")
    assert result["answer"] != JAILBREAK_REFUSAL
    assert "procurement" in result["answer"].lower()


def test_jailbreak_result_has_no_error_key():
    """Jailbreak substitution should not set an 'error' key."""
    rag = _make_rag_with_mock_llm(_DAN_RESPONSE)
    result = rag.query("What anomalies were detected?")
    assert "error" not in result or result.get("error") is None


# ---------------------------------------------------------------------------
# M-1: system_prompt forwarded to LLM
# ---------------------------------------------------------------------------


def test_system_prompt_passed_to_llm():
    """OracRAG must forward SECURITY_GUARD_SYSTEM_PROMPT to llm.generate()."""
    rag = _make_rag_with_mock_llm(_CLEAN_RESPONSE)
    rag.query("What findings exist?")

    call_kwargs = rag.llm.generate.call_args
    # Check keyword argument
    assert (
        "system_prompt" in call_kwargs.kwargs
    ), "system_prompt kwarg not forwarded to llm.generate()"
    assert call_kwargs.kwargs["system_prompt"] == SECURITY_GUARD_SYSTEM_PROMPT


def test_system_prompt_contains_odia_identity():
    assert "odia-v1" in SECURITY_GUARD_SYSTEM_PROMPT
    assert "Oraculus" in SECURITY_GUARD_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# OllamaProvider: system message in /api/chat payload
# ---------------------------------------------------------------------------


def test_ollama_provider_includes_system_message_when_given():
    provider = OllamaProvider(model="odia-v1")

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "test answer"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.object(provider, "is_available", return_value=True):
            provider.generate(
                prompt="What is in this document?",
                context="",
                system_prompt="You are a secure assistant.",
            )

    call_kwargs = mock_post.call_args.kwargs
    messages = call_kwargs["json"]["messages"]
    system_msgs = [m for m in messages if m["role"] == "system"]
    assert len(system_msgs) == 1
    assert system_msgs[0]["content"] == "You are a secure assistant."


def test_ollama_provider_no_system_message_when_not_given():
    provider = OllamaProvider(model="odia-v1")

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "test answer"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.object(provider, "is_available", return_value=True):
            provider.generate(prompt="What is in this document?", context="")

    call_kwargs = mock_post.call_args.kwargs
    messages = call_kwargs["json"]["messages"]
    system_msgs = [m for m in messages if m["role"] == "system"]
    assert len(system_msgs) == 0


def test_ollama_provider_system_message_before_user():
    """system role must appear before user role in the messages list."""
    provider = OllamaProvider(model="odia-v1")

    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "ok"}}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        with patch.object(provider, "is_available", return_value=True):
            provider.generate(
                prompt="Query here.",
                context="",
                system_prompt="Guard prompt.",
            )

    messages = mock_post.call_args.kwargs["json"]["messages"]
    roles = [m["role"] for m in messages]
    assert roles.index("system") < roles.index("user")
