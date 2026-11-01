from .hybrid import HybridRetriever

# ColBERTRetriever requires torch, which is not installed in the base CI
# environment (no GPU). Guard the import so the retrieval package loads
# cleanly in test environments and falls back gracefully when torch is absent.
try:
    from .colbert_index import ColBERTRetriever

    __all__ = ["HybridRetriever", "ColBERTRetriever"]
except ImportError:
    __all__ = ["HybridRetriever"]
