"""Tests for the CorpusLoader abstract base + legal_corpora.yml registry."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
import yaml

from oraculus_di_auditor.legal.corpus_base import CorpusLoader, LegalText


def test_corpus_loader_is_abstract() -> None:
    """Direct instantiation must fail — every concrete loader must
    implement the abstract methods. This is the contract the resolver
    relies on."""
    with pytest.raises(TypeError):
        CorpusLoader()  # type: ignore[abstract]


def test_legal_text_is_frozen() -> None:
    """LegalText must be immutable so a resolved result can be safely
    cached and passed across boundaries without defensive copies."""
    lt = LegalText(
        corpus_id="us-code",
        citation="34 U.S.C. § 10152",
        citation_raw="34 U.S.C. § 10152",
        title="§ 10152. Allocation",
        text="(a) State allocations.—...",
        source_path="data/legal_corpora/us-code/uscode/title-34/...",
        source_commit=None,
        as_of=None,
        url="https://www.law.cornell.edu/uscode/text/34/10152",
        notes=None,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        lt.text = "mutated"  # type: ignore[misc]


def test_corpora_yaml_parses_cleanly() -> None:
    """legal_corpora.yml is the registry the resolver reads at boot.
    A malformed yaml file would silently kill the resolver, so we pin
    its parsability + the shape the resolver depends on."""
    yaml_path = Path("config/legal_corpora.yml")
    assert yaml_path.exists(), "config/legal_corpora.yml must exist"

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("schema_version") == "1.0"
    corpora = data.get("corpora")
    assert isinstance(corpora, list) and len(corpora) >= 1

    # Every corpus entry must have at least these fields for the
    # resolver to instantiate a loader.
    required = {"id", "enabled", "loader", "submodule_path"}
    for entry in corpora:
        missing = required - set(entry.keys())
        assert not missing, f"corpus {entry.get('id')!r} missing: {missing}"

    # Phase 1 specifically requires the USC entry to be enabled.
    usc = next((c for c in corpora if c["id"] == "us-code"), None)
    assert usc is not None, "us-code entry missing from registry"
    assert usc["enabled"] is True, "us-code must be enabled in v3.3.0"
