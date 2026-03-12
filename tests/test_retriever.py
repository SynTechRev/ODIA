"""Tests for retriever module.

Author: GitHub Copilot Agent
Date: 2025-11-13
"""

import numpy as np
import pytest

from oraculus_di_auditor.retriever import Retriever


def test_retriever_initialization():
    """Test retriever initialization."""
    retriever = Retriever()
    assert retriever.vectors == []
    assert retriever.metadata == []


def test_retriever_initialization_with_dir(tmp_path):
    """Test retriever initialization with custom directory."""
    retriever = Retriever(vectors_dir=tmp_path)
    assert retriever.vectors_dir == tmp_path


def test_add_vector():
    """Test adding a vector with metadata."""
    retriever = Retriever()
    vector = np.array([1.0, 0.0, 0.0])
    metadata = {"id": "doc1", "text": "test"}

    retriever.add_vector(vector, metadata)

    assert len(retriever.vectors) == 1
    assert len(retriever.metadata) == 1
    assert retriever.metadata[0]["id"] == "doc1"


def test_search_empty():
    """Test search on empty index."""
    retriever = Retriever()
    query = np.array([1.0, 0.0, 0.0])

    results = retriever.search(query)

    assert results == []


def test_search_single_vector():
    """Test search with single vector."""
    retriever = Retriever()
    vector = np.array([1.0, 0.0, 0.0])
    metadata = {"id": "doc1", "text": "test"}

    retriever.add_vector(vector, metadata)

    query = np.array([1.0, 0.0, 0.0])
    results = retriever.search(query, top_k=1)

    assert len(results) == 1
    assert results[0][0] == 0  # index
    assert results[0][1] == pytest.approx(1.0, abs=0.01)  # perfect match
    assert results[0][2]["id"] == "doc1"


def test_search_multiple_vectors():
    """Test search with multiple vectors."""
    retriever = Retriever()

    vectors = [
        np.array([1.0, 0.0, 0.0]),  # Similar to query
        np.array([0.0, 1.0, 0.0]),  # Different from query
        np.array([0.8, 0.2, 0.0]),  # Somewhat similar to query
    ]
    metadata = [
        {"id": "doc1", "text": "first"},
        {"id": "doc2", "text": "second"},
        {"id": "doc3", "text": "third"},
    ]

    for vec, meta in zip(vectors, metadata, strict=True):
        retriever.add_vector(vec, meta)

    query = np.array([1.0, 0.0, 0.0])
    results = retriever.search(query, top_k=3)

    assert len(results) == 3
    assert results[0][2]["id"] == "doc1"


def test_search_top_k():
    """Test that top_k parameter limits results."""
    retriever = Retriever()

    # Add 5 vectors
    for i in range(5):
        vector = np.random.rand(10)
        metadata = {"id": f"doc{i}"}
        retriever.add_vector(vector, metadata)

    query = np.random.rand(10)
    results = retriever.search(query, top_k=3)

    assert len(results) == 3


def test_save_and_load(tmp_path):
    """Test saving and loading vectors."""
    retriever = Retriever(vectors_dir=tmp_path)

    # Add some vectors
    vectors = [np.array([1.0, 0.0]), np.array([0.0, 1.0])]
    metadata = [{"id": "doc1"}, {"id": "doc2"}]

    for vec, meta in zip(vectors, metadata, strict=True):
        retriever.add_vector(vec, meta)

    # Save
    retriever.save("test_collection")

    # Create new retriever and load
    retriever2 = Retriever(vectors_dir=tmp_path)
    retriever2.load("test_collection")

    assert len(retriever2.vectors) == 2
    assert len(retriever2.metadata) == 2
    assert retriever2.metadata[0]["id"] == "doc1"


def test_cosine_similarity():
    """Test that cosine similarity is used correctly."""
    retriever = Retriever()

    # Add orthogonal vectors
    retriever.add_vector(np.array([1.0, 0.0]), {"id": "doc1"})
    retriever.add_vector(np.array([0.0, 1.0]), {"id": "doc2"})

    # Query with first vector
    query = np.array([1.0, 0.0])
    results = retriever.search(query, top_k=2)

    # First result should have similarity ~1.0
    assert results[0][1] == pytest.approx(1.0, abs=0.01)
    # Second result should have similarity ~0.0 (orthogonal)
    assert results[1][1] == pytest.approx(0.0, abs=0.01)


def test_search_with_normalized_query():
    """Test search with unnormalized query vector."""
    retriever = Retriever()

    vector = np.array([1.0, 0.0])
    retriever.add_vector(vector, {"id": "doc1"})

    # Query with unnormalized vector (should be normalized internally)
    query = np.array([5.0, 0.0])
    results = retriever.search(query, top_k=1)

    # Should still find perfect match
    assert results[0][1] == pytest.approx(1.0, abs=0.01)
