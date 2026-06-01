"""odia_legal.corpus — legal corpus loaders and unified LegalCorpus entry point."""

from odia_legal.corpus.california_loader import CaliforniaCodeLoader
from odia_legal.corpus.cfr_loader import CFRLoader
from odia_legal.corpus.legal_corpus import LegalCorpus

__all__ = ["LegalCorpus", "CaliforniaCodeLoader", "CFRLoader"]
