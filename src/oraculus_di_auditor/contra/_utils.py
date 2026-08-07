"""Shared helpers for C.O.N.T.R.A. L-11 through L-20 detectors.

Internal module — not part of the public API.
"""

from __future__ import annotations

import hashlib
import re

from .base import EvidenceSpan, Finding, Severity


def _excerpt(text: str, start: int, max_words: int = 15) -> str:
    """Return up to max_words words starting at character offset start."""
    words = text[start:].split()[:max_words]
    return " ".join(words)


def make_finding(
    layer: str,
    sub: str,
    sev: Severity,
    doc_hash: str,
    text: str,
    match_start: int,
    match_end: int,
    anchor: str,
    axis: str,
    delta: int,
    remedy_channels: list[str],
    notes: str | None = None,
    prompt_id: str | None = None,
    prompt_version: str | None = None,
) -> Finding:
    """Build a Finding from a regex match position."""
    excerpt = _excerpt(text, match_start)
    return Finding(
        finding_id=f"contra:{layer}:{sub}:{doc_hash[:8]}:{match_start:08x}",
        layer=layer,
        sub_detector=sub,
        severity=sev,
        document_hash=doc_hash,
        evidence_span=EvidenceSpan(match_start, match_end, excerpt),
        doctrinal_anchor=anchor,
        scoring_input={"axis": axis, "delta": delta},
        remedy_channels=remedy_channels,
        notes=notes,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
    )


def doc_hash_for(text: str) -> str:
    """Return a deterministic SHA-256 hex digest for a document text.

    Used in tests when no real document hash is available.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_pattern(
    pattern: re.Pattern,
    text: str,
    layer: str,
    sub: str,
    sev: Severity,
    doc_hash: str,
    anchor: str,
    axis: str,
    delta: int,
    remedy_channels: list[str],
    notes: str | None = None,
    flags: int = 0,
) -> list[Finding]:
    """Run a compiled pattern on text and return one Finding per match."""
    findings: list[Finding] = []
    for m in pattern.finditer(text.lower()):
        findings.append(
            make_finding(
                layer=layer,
                sub=sub,
                sev=sev,
                doc_hash=doc_hash,
                text=text,
                match_start=m.start(),
                match_end=m.end(),
                anchor=anchor,
                axis=axis,
                delta=delta,
                remedy_channels=remedy_channels,
                notes=notes,
            )
        )
    return findings
