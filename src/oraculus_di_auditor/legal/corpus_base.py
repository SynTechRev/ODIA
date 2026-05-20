"""Abstract base for addressable legal corpora.

Every corpus loader (USC, CFR, SCOTUS, Federal Circuit, CRS, OIG)
implements this interface. The legal_resolver consumes them
uniformly so the plain_language templates don't need to know what
*kind* of legal text they're surfacing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LegalText:
    """A resolved statutory / regulatory / case-law text snippet.

    Returned from every CorpusLoader.resolve_citation() call.

    Fields are deliberately wide so a single LegalText can carry
    statutory, regulatory, or case-law content. Fields irrelevant
    to a given corpus are None.
    """

    corpus_id: str  # "us-code" | "cfr" | "scotus" | etc.
    citation: str  # canonical normalized citation
    citation_raw: str  # citation as originally provided
    title: str  # human-readable title of the section
    text: str  # the actual text of the provision
    source_path: str  # repo-relative path to source file
    source_commit: str | None  # git SHA the text was resolved at
    as_of: date | None  # effective date (if temporal lookup)
    url: str | None  # canonical external URL (LII, OLRC, etc.)
    notes: str | None  # extraction notes if any


class CorpusLoader(ABC):
    """Every legal corpus loader implements this contract."""

    corpus_id: str
    """Short identifier; must match the legal_corpora.yml key."""

    @abstractmethod
    def initialize(self) -> dict[str, int]:
        """Build any indexes. Called once at boot. Returns stats dict."""

    @abstractmethod
    def resolve_citation(
        self,
        citation: str,
        as_of: date | None = None,
    ) -> LegalText | None:
        """Resolve a citation string to LegalText.

        Returns None if the citation can't be parsed or doesn't
        resolve to a known provision in this corpus. Never raises;
        caller decides how to handle misses.
        """

    @abstractmethod
    def search_text(
        self,
        query: str,
        limit: int = 10,
    ) -> list[LegalText]:
        """Free-text search across the corpus."""

    @abstractmethod
    def list_amendments(self, citation: str) -> list[dict]:
        """Return git-derived amendment history for the cited provision.

        Each entry: {commit, date, message, summary_diff}. For corpora
        without git history (case law), return empty list.
        """

    @abstractmethod
    def statistics(self) -> dict[str, int]:
        """Return corpus-size metrics. Used by /api/v1/legal/status."""
