"""Embedding module for document vectorization.

Author: Marcus A. Sanchez
Date: 2025-11-12
Updated: 2025-11-13 (GitHub Copilot Agent - Phase 6)
"""

import hashlib
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import (
    TfidfVectorizer,  # type: ignore[reportMissingTypeStubs]
)


class LocalEmbedder:
    """Deterministic local embedder using TF-IDF for vector generation.

    This embedder uses TF-IDF (Term Frequency-Inverse Document Frequency) for
    deterministic, reproducible embeddings suitable for retrieval tasks.
    It's more semantically meaningful than hash-based approaches.
    """

    def __init__(self, max_features: int = 2048, norm: str = "l2"):
        """Initialize TF-IDF embedder.

        Args:
            max_features: Maximum number of features (vocabulary size)
            norm: Norm used to normalize term vectors ('l1', 'l2', or None)
        """
        self.max_features = max_features
        self.norm = norm
        self.vectorizer = TfidfVectorizer(
            max_features=max_features, norm=norm, lowercase=True, stop_words="english"
        )
        self.is_fitted = False

    def fit(self, texts: list[str]) -> None:
        """Fit the vectorizer on a corpus of texts.

        Args:
            texts: List of text documents to fit the vectorizer
        """
        self.vectorizer.fit(texts)
        self.is_fitted = True

    def embed(self, text: str) -> np.ndarray:
        """Generate embedding vector for a single text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as numpy array

        Raises:
            RuntimeError: If vectorizer not fitted yet
        """
        if not self.is_fitted:
            raise RuntimeError(
                "Embedder must be fitted with fit() before calling embed()"
            )

        vector = self.vectorizer.transform([text]).toarray()[0]
        return vector.astype(np.float32)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            2D numpy array of embeddings (shape: [num_texts, embedding_dim])

        Raises:
            RuntimeError: If vectorizer not fitted yet
        """
        if not self.is_fitted:
            raise RuntimeError(
                "Embedder must be fitted with fit() before calling embed_batch()"
            )

        return self.vectorizer.transform(texts).toarray().astype(np.float32)

    def save_vocabulary(self, path: str | Path) -> None:
        """Save the fitted vocabulary to disk.

        Args:
            path: Path to save vocabulary
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save vocabulary before fitting")

        import pickle

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(
                {
                    "vocabulary": self.vectorizer.vocabulary_,
                    "idf": self.vectorizer.idf_,
                    "max_features": self.max_features,
                    "norm": self.norm,
                },
                f,
            )

    def load_vocabulary(self, path: str | Path) -> None:
        """Load a previously saved vocabulary.

        Args:
            path: Path to load vocabulary from
        """
        import pickle

        path = Path(path)
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.max_features = data["max_features"]
        self.norm = data["norm"]

        # Recreate vectorizer with saved vocabulary
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            norm=self.norm,
            vocabulary=data["vocabulary"],
            lowercase=True,
            stop_words="english",
        )
        self.vectorizer.idf_ = data["idf"]
        self.is_fitted = True


# Legacy hash-based embedder kept for backwards compatibility
class Embedder:
    """Deterministic local embedder using hash-based vectors.

    DEPRECATED: Use LocalEmbedder (TF-IDF based) for better semantic quality.
    This class is kept for backwards compatibility with existing code.
    """

    def __init__(self, embedding_dim: int = 128):
        """Initialize embedder.

        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim

    def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text.

        Args:
            text: Input text to embed

        Returns:
            Embedding vector as list of floats
        """
        # Use SHA-256 hash for deterministic embedding
        hash_obj = hashlib.sha256(text.encode("utf-8"))
        hash_bytes = hash_obj.digest()

        # Convert hash to numpy array and normalize
        # Repeat hash bytes to reach desired dimension
        repeats = (self.embedding_dim * 4) // len(hash_bytes) + 1
        extended_bytes = (hash_bytes * repeats)[: self.embedding_dim * 4]

        # Convert to float32 array
        arr = np.frombuffer(extended_bytes, dtype=np.uint8)[: self.embedding_dim]
        arr = arr.astype(np.float32)

        # Normalize to unit vector
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm

        return arr.tolist()

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Generate embedding vectors for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            2D numpy array of embeddings
        """
        embeddings = [self.embed(text) for text in texts]
        return np.array(embeddings)
