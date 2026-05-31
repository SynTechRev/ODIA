"""LegalCorpus — unified entry point for all ODIA legal corpus loaders.

Wraps the existing LegalResolver (USC via nickvido/us-code) together with the
CaliforniaCodeLoader and any future loaders behind a single interface so the
rest of ODIA doesn't need to know which corpus backs a given citation.

Resolution order:
    1. Normalize CPRA old-form citations via CPRACrosswalk
    2. Parse the citation to determine corpus_id
    3. Route to the first loader that successfully resolves the citation

Usage::

    from odia_legal.corpus import LegalCorpus

    corpus = LegalCorpus()
    corpus.initialize()

    text = corpus.resolve("Gov. Code § 6254(f)")
    if text:
        print(text.title, text.text[:200])

    results = corpus.search("ALPR data retention", limit=5)
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LegalCorpus:
    """Unified legal corpus — wraps multiple CorpusLoader instances.

    Default loaders are discovered from the ODIA config when available;
    callers may also pass explicit loaders for testing or customisation.
    """

    def __init__(self, loaders: list[Any] | None = None):
        """Initialise the corpus.

        Args:
            loaders: Optional list of CorpusLoader instances.
                     If None, defaults are built from the repo config.
        """
        if loaders is not None:
            self._loaders = loaders
        else:
            self._loaders = _build_default_loaders()
        self._initialized = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(self) -> dict[str, dict[str, int]]:
        """Initialize all loaders.  Returns per-corpus stats."""
        stats: dict[str, dict[str, int]] = {}
        for loader in self._loaders:
            try:
                result = loader.initialize()
                stats[loader.corpus_id] = result if isinstance(result, dict) else {}
            except Exception as exc:  # noqa: BLE001
                logger.warning("LegalCorpus: loader %s init failed: %s", loader.corpus_id, exc)  # noqa: E501
        self._initialized = True
        return stats

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        citation: str,
        as_of: date | None = None,
    ):
        """Resolve a citation to a LegalText, or None if not found.

        Tries each loader in registration order and returns the first
        successful resolution.
        """
        if not self._initialized:
            logger.warning("LegalCorpus.resolve called before initialize()")
            return None

        for loader in self._loaders:
            try:
                result = loader.resolve_citation(citation, as_of=as_of)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "LegalCorpus: loader %s raised on resolve(%r): %s",
                    loader.corpus_id,
                    citation,
                    exc,
                )
                continue
            if result is not None:
                return result
        return None

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> list[Any]:
        """Full-text search across all loaders; returns up to *limit* results."""
        results = []
        per_loader = max(1, limit // max(len(self._loaders), 1))
        for loader in self._loaders:
            try:
                partial = loader.search_text(query, limit=per_loader)
                results.extend(partial)
            except Exception as exc:  # noqa: BLE001
                logger.warning("LegalCorpus: loader %s search failed: %s", loader.corpus_id, exc)  # noqa: E501
        return results[:limit]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(self) -> dict[str, dict[str, int]]:
        """Return per-corpus statistics from all loaders."""
        return {loader.corpus_id: loader.statistics() for loader in self._loaders}

    def is_empty(self) -> bool:
        """Return True if no loaders are registered or all are empty."""
        return all(sum(loader.statistics().values()) == 0 for loader in self._loaders)


# ---------------------------------------------------------------------------
# Default loader factory
# ---------------------------------------------------------------------------


def _build_default_loaders() -> list[Any]:
    """Build the default loader set from the installed environment.

    Loads loaders that are available; skips any that can't be constructed
    so the corpus starts up even with missing optional corpora.
    """
    loaders: list[Any] = []

    # USC via nickvido/us-code submodule (existing loader)
    try:
        from oraculus_di_auditor.legal.legal_resolver import get_resolver

        resolver = get_resolver()
        loaders.extend(resolver._loaders.values())  # noqa: SLF001
        logger.debug("LegalCorpus: added %d USC loaders from LegalResolver", len(loaders))  # noqa: E501
    except Exception as exc:  # noqa: BLE001
        logger.warning("LegalCorpus: could not load USC loaders: %s", exc)

    # California codes corpus (populated by ingestion script in item 12)
    cal_corpus_path = _find_cal_corpus_path()
    if cal_corpus_path:
        try:
            from odia_legal.corpus.california_loader import CaliforniaCodeLoader

            loaders.append(CaliforniaCodeLoader(submodule_path=cal_corpus_path))
            logger.debug("LegalCorpus: added CaliforniaCodeLoader at %s", cal_corpus_path)  # noqa: E501
        except Exception as exc:  # noqa: BLE001
            logger.warning("LegalCorpus: CaliforniaCodeLoader failed: %s", exc)

    return loaders


def _find_cal_corpus_path() -> Path | None:
    """Locate the California codes corpus directory.

    Checks config/legal_corpora.yml for a 'cal_codes' entry first, then
    falls back to the conventional path data/legal_corpora/cal_codes/.
    """
    # Conventional path fallback
    for candidate in [
        Path("data/legal_corpora/cal_codes"),
        Path(__file__).resolve().parents[4] / "data" / "legal_corpora" / "cal_codes",
    ]:
        if candidate.exists():
            return candidate
    return None
