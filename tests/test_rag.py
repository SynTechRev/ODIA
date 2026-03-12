"""Tests for RAG (Retrieval-Augmented Generation) system.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import os
import pickle
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from oraculus_di_auditor.embeddings import LocalEmbedder
from oraculus_di_auditor.llm_providers import (
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
    get_provider,
)
from oraculus_di_auditor.rag import OracRAG, RAGRouter
from oraculus_di_auditor.rag_context import ContextAssembler
from oraculus_di_auditor.rag_prompts import get_prompt_for_query
from oraculus_di_auditor.retriever import Retriever

# ============================================================================
# LLM Provider Tests
# ============================================================================


def test_openai_provider_initialization():
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
    assert provider.api_key == "test-key"
    assert provider.model == "gpt-4o-mini"
    assert provider.temperature == 0.1


def test_openai_provider_is_available():
    """Test OpenAI provider availability check."""
    # With API key
    provider = OpenAIProvider(api_key="test-key")
    assert provider.is_available()

    # Without API key
    provider = OpenAIProvider(api_key=None)
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=True):
        provider = OpenAIProvider()
        assert not provider.is_available()


def test_anthropic_provider_initialization():
    """Test Anthropic provider initialization."""
    provider = AnthropicProvider(api_key="test-key")
    assert provider.api_key == "test-key"
    assert provider.model == "claude-3-haiku-20240307"


def test_ollama_provider_initialization():
    """Test Ollama provider initialization."""
    provider = OllamaProvider(model="llama3.1", base_url="http://test:11434")
    assert provider.model == "llama3.1"
    assert provider.base_url == "http://test:11434"


def test_get_provider_factory():
    """Test provider factory function."""
    # OpenAI
    provider = get_provider("openai", api_key="test")
    assert isinstance(provider, OpenAIProvider)

    # Anthropic
    provider = get_provider("anthropic", api_key="test")
    assert isinstance(provider, AnthropicProvider)

    # Ollama
    provider = get_provider("ollama")
    assert isinstance(provider, OllamaProvider)

    # Invalid provider
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("invalid")


# ============================================================================
# Context Assembler Tests
# ============================================================================


def test_context_assembler_initialization():
    """Test context assembler initialization."""
    assembler = ContextAssembler(max_tokens=1000)
    assert assembler.max_tokens == 1000


def test_context_assembler_estimate_tokens():
    """Test token estimation."""
    assembler = ContextAssembler()
    text = "a" * 400  # 400 characters
    tokens = assembler.estimate_tokens(text)
    assert tokens == 100  # 400 / 4 = 100


def test_context_assembler_deduplicate():
    """Test deduplication of results."""
    assembler = ContextAssembler()

    results = [
        {
            "index": 0,
            "score": 0.9,
            "metadata": {"id": "doc1", "file_hash": "hash1", "text": "text1"},
        },
        {
            "index": 1,
            "score": 0.8,
            "metadata": {"id": "doc1", "file_hash": "hash1", "text": "text1"},
        },
        {
            "index": 2,
            "score": 0.7,
            "metadata": {"id": "doc2", "file_hash": "hash2", "text": "text2"},
        },
    ]

    deduplicated = assembler.deduplicate_sources(results)

    # Should keep only 2 results (doc1 once, doc2 once)
    assert len(deduplicated) == 2
    # Should keep higher-scoring doc1
    doc1_results = [r for r in deduplicated if r["metadata"]["id"] == "doc1"]
    assert len(doc1_results) == 1
    assert doc1_results[0]["score"] == 0.9


def test_context_assembler_assemble():
    """Test context assembly."""
    assembler = ContextAssembler(max_tokens=1000)

    results = [
        {
            "index": 0,
            "score": 0.9,
            "metadata": {
                "id": "doc1",
                "title": "Document 1",
                "source": "file1.pdf",
                "text": "Short text content.",
            },
        },
        {
            "index": 1,
            "score": 0.8,
            "metadata": {
                "id": "doc2",
                "title": "Document 2",
                "source": "file2.pdf",
                "text": "Another short text.",
            },
        },
    ]

    context = assembler.assemble(results)

    assert "doc1" in context
    assert "doc2" in context
    assert "Document 1" in context
    assert "Short text content" in context


def test_context_assembler_format_sources():
    """Test source formatting."""
    assembler = ContextAssembler()

    results = [
        {
            "index": 0,
            "score": 0.95,
            "metadata": {
                "id": "#23-0148",
                "title": "Contract Document",
                "source": "contract.pdf",
                "text": "This is a long text that will be truncated for the snippet display.",
            },
        }
    ]

    sources = assembler.format_sources(results)

    assert len(sources) == 1
    assert sources[0]["corpus_id"] == "#23-0148"
    assert sources[0]["title"] == "Contract Document"
    assert sources[0]["relevance_score"] == 0.95
    assert "snippet" in sources[0]


# ============================================================================
# Prompt Selection Tests
# ============================================================================


def test_get_prompt_vendor_query():
    """Test vendor query prompt selection."""
    from oraculus_di_auditor.rag_prompts import VENDOR_QUERY_PROMPT

    prompt = get_prompt_for_query("What Axon contracts exist?")
    assert prompt == VENDOR_QUERY_PROMPT


def test_get_prompt_legal_query():
    """Test legal query prompt selection."""
    from oraculus_di_auditor.rag_prompts import LEGAL_QUERY_PROMPT

    prompt = get_prompt_for_query("Fourth Amendment implications?")
    assert prompt == LEGAL_QUERY_PROMPT


def test_get_prompt_anomaly_query():
    """Test anomaly query prompt selection."""
    from oraculus_di_auditor.rag_prompts import ANOMALY_QUERY_PROMPT

    prompt = get_prompt_for_query("Show missing agenda items")
    assert prompt == ANOMALY_QUERY_PROMPT


def test_get_prompt_general_query():
    """Test general query prompt selection."""
    from oraculus_di_auditor.rag_prompts import GENERAL_QUERY_PROMPT

    prompt = get_prompt_for_query("What is in the documents?")
    assert prompt == GENERAL_QUERY_PROMPT


# ============================================================================
# RAG Router Tests
# ============================================================================


def test_rag_router_vendor_query():
    """Test routing for vendor queries."""
    router = RAGRouter()
    indices = router.route_query("What vendor contracts exist?")
    assert "corpus" in indices
    assert "vicfm" in indices


def test_rag_router_legal_query():
    """Test routing for legal queries."""
    router = RAGRouter()
    indices = router.route_query("Constitutional issues?")
    assert "corpus" in indices
    assert "jim" in indices
    assert "lexicon" in indices


def test_rag_router_anomaly_query():
    """Test routing for anomaly queries."""
    router = RAGRouter()
    indices = router.route_query("Show anomaly patterns")
    assert "corpus" in indices
    assert "ace" in indices


# ============================================================================
# OracRAG Tests
# ============================================================================


def test_orac_rag_initialization():
    """Test OracRAG initialization."""
    rag = OracRAG()
    assert rag.embedder is not None
    assert rag.retriever is not None
    assert rag.context_assembler is not None
    assert not rag.is_index_loaded


def test_orac_rag_query_without_index():
    """Test query fails gracefully without loaded index."""
    rag = OracRAG()
    result = rag.query("test query")
    assert "error" in result
    assert "not loaded" in result["error"].lower()


def test_orac_rag_load_index_missing_vocab():
    """Test load_index fails with missing vocabulary."""
    rag = OracRAG()
    with pytest.raises(FileNotFoundError):
        rag.load_index(vocab_path="/nonexistent/vocab.pkl")


def test_orac_rag_query_with_mock_data(tmp_path):
    """Test RAG query with mocked components."""
    # Create mock vocabulary with enough words to match embedding dimension
    vocab_path = tmp_path / "vocab.pkl"

    # Create vocabulary with 100 words to match max_features
    vocab = {f"word{i}": i for i in range(100)}
    vocab_data = {
        "vocabulary": vocab,
        "idf": np.ones(100),
        "max_features": 100,
        "norm": "l2",
    }
    with open(vocab_path, "wb") as f:
        pickle.dump(vocab_data, f)

    # Create mock embedder and retriever
    embedder = LocalEmbedder(max_features=100)
    embedder.load_vocabulary(vocab_path)

    # Create corpus with words from vocabulary
    corpus_text = " ".join([f"word{i}" for i in range(50)])

    retriever = Retriever(vectors_dir=tmp_path)
    # Add vector with correct dimension (100)
    # Embed a document using the fitted embedder
    doc_vector = embedder.embed(corpus_text)
    retriever.add_vector(
        doc_vector,
        {
            "id": "doc1",
            "title": "Test Document",
            "source": "test.pdf",
            "text": "This is test content with " + corpus_text,
        },
    )
    retriever.save("test_collection")

    # Initialize RAG without LLM (dry-run mode)
    rag = OracRAG(embedder=embedder, retriever=retriever, vectors_dir=tmp_path)
    rag.llm = None  # Disable LLM for testing
    rag.load_index(index_name="test_collection", vocab_path=str(vocab_path))

    # Query with words from vocabulary, use low threshold
    result = rag.query("word1 word2 word3", top_k=1, threshold=0.0)

    # Verify result structure
    assert "answer" in result
    assert "sources" in result
    assert "confidence" in result
    # Should have LLM fallback message since LLM is None
    assert "LLM not available" in result["answer"]


def test_orac_rag_query_with_filter():
    """Test RAG query with corpus filter."""
    rag = OracRAG()
    # Mock loaded index
    rag.is_index_loaded = True
    rag.embedder = MagicMock()
    rag.embedder.embed.return_value = np.random.rand(2048)
    rag.retriever = MagicMock()
    rag.retriever.search.return_value = [
        (
            0,
            0.9,
            {
                "id": "#23-0148",
                "title": "Doc 1",
                "source": "file1.pdf",
                "text": "content",
            },
        ),
        (
            1,
            0.8,
            {"id": "#23-0214", "title": "Doc 2", "source": "file2.pdf", "text": "text"},
        ),
        (
            2,
            0.7,
            {"id": "#24-0001", "title": "Doc 3", "source": "file3.pdf", "text": "text"},
        ),
    ]
    rag.llm = None

    result = rag.query_with_filter("test", corpus_ids=["#23-0148", "#23-0214"], top_k=5)

    # Should only include filtered corpus IDs
    assert all(s["corpus_id"] in ["#23-0148", "#23-0214"] for s in result["sources"])


# ============================================================================
# Integration Test (requires dependencies)
# ============================================================================


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not configured"
)
def test_orac_rag_integration_with_openai(tmp_path):
    """Integration test with real OpenAI API (requires API key).

    This test is skipped unless OPENAI_API_KEY is set.
    """
    # Create minimal test corpus
    vocab_path = tmp_path / "vocab.pkl"

    vocab_data = {
        "vocabulary": {"legislative": 0, "document": 1, "contract": 2},
        "idf": np.array([1.0, 1.0, 1.0]),
        "max_features": 100,
        "norm": "l2",
    }
    with open(vocab_path, "wb") as f:
        pickle.dump(vocab_data, f)

    embedder = LocalEmbedder(max_features=100)
    embedder.load_vocabulary(vocab_path)

    retriever = Retriever(vectors_dir=tmp_path)
    retriever.add_vector(
        np.random.rand(100),
        {
            "id": "#23-0148",
            "title": "Axon Contract",
            "source": "axon.pdf",
            "text": "This is a contract for body-worn cameras with Axon Enterprise.",
        },
    )
    retriever.save("test_collection")

    # Initialize RAG with OpenAI
    rag = OracRAG(
        embedder=embedder,
        retriever=retriever,
        llm_provider="openai",
        vectors_dir=tmp_path,
    )
    rag.load_index(index_name="test_collection", vocab_path=str(vocab_path))

    # Query
    result = rag.query("What is this contract about?", top_k=1)

    # Verify response structure
    assert "answer" in result
    assert "sources" in result
    assert "confidence" in result
    assert len(result["answer"]) > 0
    assert len(result["sources"]) > 0
