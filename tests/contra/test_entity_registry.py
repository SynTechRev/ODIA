"""Tests for C.O.N.T.R.A. entity registry, name normalization, and Analytical Card."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from oraculus_di_auditor.entity.normalize import normalize_corporate_suffix
from oraculus_di_auditor.entity.registry import Entity, EntityRegistry

# ---------------------------------------------------------------------------
# normalize_corporate_suffix
# ---------------------------------------------------------------------------


def test_normalize_llc_variants() -> None:
    assert normalize_corporate_suffix(
        "AT&T Mobility LLC"
    ) == normalize_corporate_suffix("AT&T Mobility L.L.C.")
    assert normalize_corporate_suffix(
        "Foo Limited Liability Company"
    ) == normalize_corporate_suffix("Foo LLC")


def test_normalize_inc_variants() -> None:
    assert normalize_corporate_suffix("Acme Inc") == normalize_corporate_suffix(
        "Acme Incorporated"
    )
    assert normalize_corporate_suffix("Acme Inc.") == normalize_corporate_suffix(
        "Acme Inc"
    )


def test_normalize_corp_variants() -> None:
    assert normalize_corporate_suffix("Foo Corp") == normalize_corporate_suffix(
        "Foo Corporation"
    )


def test_normalize_strips_punctuation() -> None:
    result = normalize_corporate_suffix("AT&T Inc")
    assert "&" not in result  # & stripped to space
    assert "  " not in result  # no double spaces


def test_normalize_preserves_meaningful_words() -> None:
    result = normalize_corporate_suffix("Southern California Edison Company")
    assert "Southern" in result
    assert "California" in result
    assert "Edison" in result


# ---------------------------------------------------------------------------
# EntityRegistry — in-memory mode
# ---------------------------------------------------------------------------


@pytest.fixture
def registry() -> EntityRegistry:
    reg = EntityRegistry()
    reg.add_entity(
        Entity.new(
            canonical_name="AT&T Mobility LLC",
            naics="5172",
            corporate_family="AT&T Inc",
            aliases=["AT&T", "ATT", "AT&T Wireless"],
        )
    )
    reg.add_entity(
        Entity.new(
            canonical_name="Comcast Cable Communications LLC",
            naics="5172",
            corporate_family="Comcast Corporation",
            aliases=["Comcast", "Xfinity", "Comcast Xfinity"],
        )
    )
    reg.add_entity(
        Entity.new(
            canonical_name="Kaiser Foundation Health Plan Inc",
            naics="5241",
            aliases=["Kaiser Permanente", "Kaiser", "KP"],
        )
    )
    return reg


def test_registry_len(registry: EntityRegistry) -> None:
    assert len(registry) == 3


def test_resolve_exact_canonical(registry: EntityRegistry) -> None:
    entity = registry.resolve("AT&T Mobility LLC")
    assert entity is not None
    assert entity.canonical_name == "AT&T Mobility LLC"


def test_resolve_exact_alias(registry: EntityRegistry) -> None:
    entity = registry.resolve("Xfinity")
    assert entity is not None
    assert entity.canonical_name == "Comcast Cable Communications LLC"


def test_resolve_att_short_alias(registry: EntityRegistry) -> None:
    entity = registry.resolve("AT&T")
    assert entity is not None
    assert "AT&T" in entity.canonical_name


def test_fuzzy_match_att_mobility(registry: EntityRegistry) -> None:
    entity = registry.fuzzy_match("ATT Mobility")
    assert entity is not None
    assert "AT&T" in entity.canonical_name


def test_fuzzy_match_kaiser_alias(registry: EntityRegistry) -> None:
    # "Kaiser Permanente" is a registered alias — fuzzy match should hit it
    entity = registry.fuzzy_match("Kaiser Permanente")
    assert entity is not None
    assert "Kaiser" in entity.canonical_name


def test_fuzzy_match_kaiser_low_threshold(registry: EntityRegistry) -> None:
    # "Kaiser Permanente Health Plan" is a plausible user query but sits below
    # the 0.88 precision threshold; at 0.75 it should resolve.
    entity = registry.fuzzy_match("Kaiser Permanente Health Plan", threshold=0.75)
    assert entity is not None
    assert "Kaiser" in entity.canonical_name


def test_resolve_returns_none_on_total_mismatch(registry: EntityRegistry) -> None:
    entity = registry.resolve("Zyzzyx Road Municipal Services")
    assert entity is None


def test_fuzzy_match_below_threshold_returns_none(registry: EntityRegistry) -> None:
    entity = registry.fuzzy_match("Zyzzyx Road Municipal Services", threshold=0.88)
    assert entity is None


def test_add_alias_makes_name_resolvable(registry: EntityRegistry) -> None:
    att = registry.resolve("AT&T Mobility LLC")
    assert att is not None
    registry.add_alias(att.entity_id, "AT and T")
    found = registry.resolve("AT and T")
    assert found is not None
    assert found.entity_id == att.entity_id


def test_add_alias_unknown_entity_raises(registry: EntityRegistry) -> None:
    with pytest.raises(KeyError):
        registry.add_alias("nonexistent-uuid", "some alias")


def test_get_by_id(registry: EntityRegistry) -> None:
    att = registry.resolve("AT&T Mobility LLC")
    assert att is not None
    found = registry.get_by_id(att.entity_id)
    assert found is att


def test_entity_new_generates_unique_ids() -> None:
    e1 = Entity.new("Foo Corp")
    e2 = Entity.new("Foo Corp")
    assert e1.entity_id != e2.entity_id


def test_entity_new_defaults() -> None:
    e = Entity.new("Test Entity LLC")
    assert e.in_contra_corpus is True
    assert e.in_tulare_priority_list is False
    assert e.aliases == []


def test_get_by_canonical_name_exact(registry: EntityRegistry) -> None:
    found = registry.get_by_canonical_name("AT&T Mobility LLC")
    assert found is not None
    assert found.canonical_name == "AT&T Mobility LLC"


def test_get_by_canonical_name_no_fuzzy_fallback(registry: EntityRegistry) -> None:
    # "AT&T Mobility" without "LLC" should NOT resolve via exact canonical lookup
    found = registry.get_by_canonical_name("AT&T Mobility")
    assert found is None


def test_get_by_canonical_name_similar_names_not_confused(
    registry: EntityRegistry,
) -> None:
    """Two similar-sounding entities must not be deduplicated by canonical lookup."""
    reg = EntityRegistry()
    reg.add_entity(Entity.new("Southern California Edison Company", naics="2211"))
    reg.add_entity(Entity.new("Southern California Gas Company", naics="2212"))
    assert len(reg) == 2
    sce = reg.get_by_canonical_name("Southern California Edison Company")
    gas = reg.get_by_canonical_name("Southern California Gas Company")
    assert sce is not None
    assert gas is not None
    assert sce.entity_id != gas.entity_id


# ---------------------------------------------------------------------------
# Analytical Card — smoke test (no CASI, no findings)
# ---------------------------------------------------------------------------


def test_build_analytical_card_creates_file() -> None:
    from oraculus_di_auditor.cards.analytical_card import (
        AnalyticalCardInput,
        build_analytical_card,
    )

    inp = AnalyticalCardInput(
        entity_name="AT&T Mobility LLC",
        entity_id="test-entity-id",
        doc_type="tos",
        effective_date="2026-01-01",
        version_label="Jan 2026",
        document_hash="a" * 64,
        source_url="https://example.com/tos",
        wayback_url=None,
        findings=[],
        casi_axes=None,
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = build_analytical_card(inp, tmp)
        assert Path(path).exists()
        assert path.endswith(".docx")
        assert Path(path).stat().st_size > 5000  # non-trivial file


def test_build_analytical_card_with_casi() -> None:
    from oraculus_di_auditor.cards.analytical_card import (
        AnalyticalCardInput,
        build_analytical_card,
    )
    from oraculus_di_auditor.scoring.casi import CasiAxes

    axes = CasiAxes(
        remedy_foreclosure=14,
        data_extraction_depth=12,
        modification_and_consent=8,
        procedural_adhesion=10,
        enforcement_cost_asymmetry=6,
    )
    assert axes.aggregate == 50
    assert axes.band == "Substantial Asymmetry"

    inp = AnalyticalCardInput(
        entity_name="Comcast Cable Communications LLC",
        entity_id="test-comcast",
        doc_type="tos",
        effective_date="2026-03-01",
        version_label=None,
        document_hash="b" * 64,
        source_url=None,
        wayback_url=None,
        findings=[],
        casi_axes=axes,
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = build_analytical_card(inp, tmp)
        assert Path(path).exists()


def test_build_analytical_card_no_emdash_in_content() -> None:
    """Verify no em-dash or en-dash characters appear in the card text."""
    from docx import Document as DocxDocument

    from oraculus_di_auditor.cards.analytical_card import (
        AnalyticalCardInput,
        build_analytical_card,
    )

    inp = AnalyticalCardInput(
        entity_name="Test Entity Corp",
        entity_id="test-id",
        doc_type="privacy_notice",
        effective_date=None,
        version_label=None,
        document_hash="c" * 64,
        source_url=None,
        wayback_url=None,
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = build_analytical_card(inp, tmp)
        doc = DocxDocument(path)
        full_text = "\n".join(p.text for p in doc.paragraphs)
        assert "—" not in full_text, "em-dash found in card text"
        assert "–" not in full_text, "en-dash found in card text"
