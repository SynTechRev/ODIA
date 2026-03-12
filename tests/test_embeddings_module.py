"""Tests for embeddings module.

Author: Marcus A. Sanchez
Date: 2025-11-12
Updated: 2025-11-13 (GitHub Copilot Agent - Phase 6)
"""

import numpy as np
import pytest

from oraculus_di_auditor.embeddings import Embedder, LocalEmbedder


# Tests for legacy hash-based Embedder
def test_embedder_initialization():
    """Test embedder initialization."""
    embedder = Embedder(embedding_dim=128)
    assert embedder.embedding_dim == 128


def test_embed_single_text():
    """Test embedding single text."""
    embedder = Embedder(embedding_dim=128)
    text = "This is a test document"

    embedding = embedder.embed(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 128
    assert all(isinstance(x, int | float) for x in embedding)


def test_embed_deterministic():
    """Test that embeddings are deterministic."""
    embedder = Embedder(embedding_dim=128)
    text = "Same text"

    embedding1 = embedder.embed(text)
    embedding2 = embedder.embed(text)

    assert embedding1 == embedding2


def test_embed_different_texts():
    """Test that different texts produce different embeddings."""
    embedder = Embedder(embedding_dim=128)

    embedding1 = embedder.embed("Text one")
    embedding2 = embedder.embed("Text two")

    assert embedding1 != embedding2


def test_embed_batch():
    """Test batch embedding."""
    embedder = Embedder(embedding_dim=128)
    texts = ["First text", "Second text", "Third text"]

    embeddings = embedder.embed_batch(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape == (3, 128)


def test_embed_normalized():
    """Test that embeddings are normalized."""
    embedder = Embedder(embedding_dim=128)
    text = "Test normalization"

    embedding = np.array(embedder.embed(text))
    norm = np.linalg.norm(embedding)

    # Should be close to 1 (unit vector)
    assert abs(norm - 1.0) < 0.01


# Tests for new TF-IDF based LocalEmbedder
def test_local_embedder_initialization():
    """Test LocalEmbedder initialization."""
    embedder = LocalEmbedder(max_features=512)
    assert embedder.max_features == 512
    assert embedder.norm == "l2"
    assert not embedder.is_fitted


def test_local_embedder_fit():
    """Test fitting the LocalEmbedder."""
    embedder = LocalEmbedder(max_features=100)
    corpus = [
        "This is the first document",
        "This is the second document",
        "And this is the third one",
    ]

    embedder.fit(corpus)
    assert embedder.is_fitted


def test_local_embedder_embed_single():
    """Test embedding a single text with LocalEmbedder."""
    embedder = LocalEmbedder(max_features=100)
    corpus = ["legal document one", "legal document two", "statute text three"]

    embedder.fit(corpus)
    embedding = embedder.embed("legal document")

    assert isinstance(embedding, np.ndarray)
    # Vocabulary size depends on corpus, will be <= max_features
    assert embedding.shape[0] <= 100
    assert embedding.shape[0] > 0
    assert embedding.dtype == np.float32


def test_local_embedder_embed_batch():
    """Test batch embedding with LocalEmbedder."""
    embedder = LocalEmbedder(max_features=100)
    corpus = ["document one", "document two", "document three"]

    embedder.fit(corpus)
    texts = ["document", "text"]
    embeddings = embedder.embed_batch(texts)

    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == 2  # Two texts
    assert embeddings.shape[1] <= 100  # Feature count
    assert embeddings.dtype == np.float32


def test_local_embedder_deterministic():
    """Test that LocalEmbedder produces deterministic results."""
    embedder = LocalEmbedder(max_features=100)
    corpus = ["text one", "text two", "text three"]

    embedder.fit(corpus)

    embedding1 = embedder.embed("text one")
    embedding2 = embedder.embed("text one")

    np.testing.assert_array_equal(embedding1, embedding2)


def test_local_embedder_not_fitted_error():
    """Test that embed() raises error if not fitted."""
    embedder = LocalEmbedder()

    with pytest.raises(RuntimeError, match="must be fitted"):
        embedder.embed("some text")


def test_local_embedder_batch_not_fitted_error():
    """Test that embed_batch() raises error if not fitted."""
    embedder = LocalEmbedder()

    with pytest.raises(RuntimeError, match="must be fitted"):
        embedder.embed_batch(["text one", "text two"])


def test_local_embedder_different_texts():
    """Test that different texts produce different embeddings."""
    embedder = LocalEmbedder(max_features=100)
    corpus = ["document about law", "document about science", "document about history"]

    embedder.fit(corpus)

    embedding1 = embedder.embed("law")
    embedding2 = embedder.embed("science")

    # Embeddings should be different
    assert not np.array_equal(embedding1, embedding2)
