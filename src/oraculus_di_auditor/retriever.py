"""Vector retrieval module for similarity search.

Author: Marcus A. Sanchez
Date: 2025-11-12
"""

from pathlib import Path

import numpy as np


class Retriever:
    """Simple vector storage and similarity search."""

    def __init__(self, vectors_dir: Path | None = None):
        """Initialize retriever.

        Args:
            vectors_dir: Directory to store vectors (optional)
        """
        self.vectors_dir = vectors_dir or Path("data/vectors")
        self.vectors_dir.mkdir(parents=True, exist_ok=True)
        self.vectors: list[np.ndarray] = []
        self.metadata: list[dict] = []

    def add_vector(self, vector: np.ndarray, metadata: dict):
        """Add a vector with metadata.

        Args:
            vector: Embedding vector
            metadata: Associated metadata (id, text, etc.)
        """
        self.vectors.append(vector)
        self.metadata.append(metadata)

    def search(
        self, query_vector: np.ndarray, top_k: int = 5
    ) -> list[tuple[int, float, dict]]:
        """Search for similar vectors using cosine similarity.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of (index, similarity_score, metadata) tuples
        """
        if not self.vectors:
            return []

        vectors_array = np.array(self.vectors)

        # Normalize query vector
        query_norm = np.linalg.norm(query_vector)
        if query_norm > 0:
            query_vector = query_vector / query_norm

        # Compute cosine similarities
        similarities = np.dot(vectors_array, query_vector)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (int(idx), float(similarities[idx]), self.metadata[idx])
            for idx in top_indices
        ]

        return results

    def save(self, filename: str):
        """Save vectors and metadata to disk.

        Args:
            filename: Base filename (without extension)
        """
        vectors_path = self.vectors_dir / f"{filename}_vectors.npy"
        metadata_path = self.vectors_dir / f"{filename}_metadata.npy"

        np.save(vectors_path, np.array(self.vectors))
        np.save(metadata_path, np.array(self.metadata, dtype=object))

    def load(self, filename: str):
        """Load vectors and metadata from disk.

        Args:
            filename: Base filename (without extension)
        """
        vectors_path = self.vectors_dir / f"{filename}_vectors.npy"
        metadata_path = self.vectors_dir / f"{filename}_metadata.npy"

        if vectors_path.exists() and metadata_path.exists():
            self.vectors = np.load(vectors_path).tolist()
            self.metadata = np.load(metadata_path, allow_pickle=True).tolist()
