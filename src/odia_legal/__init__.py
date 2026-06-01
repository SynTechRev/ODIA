"""odia_legal — Legal corpus integration for O.D.I.A.

Integrates US Code, California Codes, CFR, and case law into the ODIA
detector and reasoning pipeline. Transforms documentary observations into
legally-framed conclusions suitable for litigation-grade reporting.

Public API:
    from odia_legal import LegalCorpus, CitationResolver, LegalReasoner

Specification: ODIA_Legal_Corpus_Integration_Spec.docx
Milestone: v3.0.0 — Sunshine Dragnet deadline 2028-07-02
"""

from __future__ import annotations

__version__ = "0.2.0"
