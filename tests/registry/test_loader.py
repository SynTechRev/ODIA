"""Tests for the Cross-Entity Registry loader.

The protocol-compliance bar is that every tier count, every personnel
record, and every alias mapping in entities.yml round-trips through
the loader without loss. These tests are intentionally exact - any
schema drift in entities.yml that breaks a count or an alias mapping
fails CI immediately.
"""

from __future__ import annotations

import pytest

from oraculus_di_auditor.registry import EntityRegistry, load_default_registry


@pytest.fixture(scope="module")
def registry() -> EntityRegistry:
    return load_default_registry()


def test_loads_without_error(registry: EntityRegistry) -> None:
    assert registry.schema_version == "1.0"


def test_tier1_entity_count(registry: EntityRegistry) -> None:
    assert len(list(registry.tier1_entities())) == 12


def test_tier2_entity_count(registry: EntityRegistry) -> None:
    assert len(list(registry.tier2_entities())) == 8


def test_tier3_entity_count(registry: EntityRegistry) -> None:
    assert len(list(registry.tier3_entities())) == 10


def test_tier4_entity_count(registry: EntityRegistry) -> None:
    assert len(list(registry.tier4_entities())) == 6


def test_total_entity_count(registry: EntityRegistry) -> None:
    assert len(list(registry.all_entities())) == 36


def test_personnel_count(registry: EntityRegistry) -> None:
    assert len(list(registry.all_personnel())) == 13


def test_finding_types_count_and_ids(registry: EntityRegistry) -> None:
    types = list(registry.all_finding_types())
    assert len(types) == 7
    assert {t.id for t in types} == set("ABCDEFG")


def test_entity_lookup_tcpd(registry: EntityRegistry) -> None:
    tcpd = registry.entity_by_id("E-010")
    assert tcpd is not None
    assert tcpd.abbreviation == "TCPD"
    assert tcpd.tier == 1


def test_entity_lookup_tcdao(registry: EntityRegistry) -> None:
    tcdao = registry.entity_by_id("E-011")
    assert tcdao is not None
    assert tcdao.abbreviation == "TCDAO"
    assert "Bureau of Investigations" in tcdao.aliases


def test_vendor_aliases_include_flock_and_flockos(registry: EntityRegistry) -> None:
    flock = registry.entity_by_id("V-002")
    assert flock is not None
    assert "Flock" in flock.aliases
    assert "FlockOS" in flock.aliases


def test_alias_lookup_case_insensitive(registry: EntityRegistry) -> None:
    upper = registry.entity_ids_for_alias("FLOCKOS")
    lower = registry.entity_ids_for_alias("flockos")
    mixed = registry.entity_ids_for_alias("FlockOS")
    assert upper == lower == mixed == {"V-002"}


def test_sub_detectors_tcpd(registry: EntityRegistry) -> None:
    subs = registry.sub_detectors_for("E-010")
    assert subs == (
        "seu_operations",
        "fourth_amendment_waiver_scope",
        "ab109_funding_flow",
        "electronic_monitoring_vendor",
        "probationer_flock_data_access",
    )


def test_sub_detectors_vpd_empty(registry: EntityRegistry) -> None:
    # VPD is Tier 1 but has no sub-detectors registered yet.
    assert registry.sub_detectors_for("E-001") == ()


def test_sub_detectors_unknown_entity_empty(registry: EntityRegistry) -> None:
    assert registry.sub_detectors_for("E-999") == ()


def test_personnel_lookup_fahoum(registry: EntityRegistry) -> None:
    person = registry.personnel_by_id("P-003")
    assert person is not None
    assert "Fahoum" in person.aliases
    # Fahoum appears at both VPD (procurement authority) and TCDAO
    # (subject of felony prosecution) - the canonical personnel
    # migration precedent the protocol cites.
    entities_visited = {h.entity for h in person.history}
    assert {"E-001", "E-011"}.issubset(entities_visited)


def test_personnel_alias_lookup(registry: EntityRegistry) -> None:
    # Both first-name-last-name and just-last-name forms should resolve.
    assert registry.personnel_ids_for_alias("Fahoum") == {"P-003"}
    assert registry.personnel_ids_for_alias("Luma Fahoum") == {"P-003"}
    assert registry.personnel_ids_for_alias("FAHOUM") == {"P-003"}


def test_vendor_presence_axon_full_footprint(registry: EntityRegistry) -> None:
    axon = registry.entity_by_id("V-001")
    assert axon is not None
    # Axon's confirmed presence list: all 9 Tier-1 city PDs + TCSO
    # (E-001 through E-009).
    assert set(axon.presence) == {
        "E-001",
        "E-002",
        "E-003",
        "E-004",
        "E-005",
        "E-006",
        "E-007",
        "E-008",
        "E-009",
    }


def test_finding_type_default_severity(registry: EntityRegistry) -> None:
    assert registry.finding_type_default_severity("A") == "HIGH"
    assert registry.finding_type_default_severity("C") == "CRITICAL"
    # Lower-case input also resolves.
    assert registry.finding_type_default_severity("c") == "CRITICAL"
    # Unknown finding type falls back to MEDIUM.
    assert registry.finding_type_default_severity("Z") == "MEDIUM"


def test_non_standard_categories_present(registry: EntityRegistry) -> None:
    categories = registry.non_standard_categories()
    # 11 known categories per entities.yml.
    assert len(categories) == 11
    # The Farmersville Axon Fleet 3 CIP precedent should be in here.
    assert any(
        "Planning Commission CIP" in c.category and "Farmersville" in c.precedent
        for c in categories
    )


def test_entity_dataclass_is_frozen(registry: EntityRegistry) -> None:
    ent = registry.entity_by_id("E-001")
    assert ent is not None
    with pytest.raises((AttributeError, TypeError)):
        ent.name = "tampered"  # type: ignore[misc]
