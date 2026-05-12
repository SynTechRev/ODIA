"""YAML loader for the O.D.I.A. Cross-Entity Registry.

Reads ``registry/entities.yml`` at application startup and exposes
typed accessors for the D-13 cross-entity detector and downstream
consumers.

Thread-safe for read operations after initialisation. Mutations (e.g.
updating Personnel as new audit findings surface) flow through the
separate PersonnelRegistry write path, not this loader.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from oraculus_di_auditor.registry.types import (
    Entity,
    FindingType,
    NonStandardCategory,
    Personnel,
    PersonnelHistoryEntry,
)

# Default location: the entities.yml shipped beside this loader module.
DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parent / "entities.yml"


class EntityRegistry:
    """Authoritative read-only access to the Cross-Entity Registry.

    Loaded once per process from ``entities.yml``. After ``__init__``
    returns, the registry is read-only; concurrent reads from multiple
    threads are safe (no mutation).
    """

    def __init__(self, path: Path | str | None = None) -> None:
        self.path: Path = Path(path) if path else DEFAULT_REGISTRY_PATH
        self.schema_version: str = ""
        self._entities: dict[str, Entity] = {}
        self._entities_by_tier: dict[int, list[Entity]] = {}
        self._personnel: dict[str, Personnel] = {}
        self._finding_types: dict[str, FindingType] = {}
        self._non_standard: tuple[NonStandardCategory, ...] = ()
        self._alias_to_entity_ids: dict[str, set[str]] = {}
        self._alias_to_personnel_ids: dict[str, set[str]] = {}
        self._load()

    # ----------------------------- loading ----------------------------------

    def _load(self) -> None:
        try:
            import yaml  # type: ignore
        except ImportError as e:  # pragma: no cover - dev dep usually present
            raise ImportError(
                "EntityRegistry requires PyYAML. "
                "Install with: pip install pyyaml"
            ) from e

        text = self.path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}

        self.schema_version = str(data.get("schema_version", "unknown"))

        for tier_block in data.get("tiers", []):
            tier_id = int(tier_block.get("tier_id"))
            for raw in tier_block.get("entities", []):
                ent = _build_entity(raw, tier_id)
                self._entities[ent.id] = ent
                self._entities_by_tier.setdefault(tier_id, []).append(ent)
                self._index_aliases(ent)

        for raw in data.get("personnel", []):
            person = _build_personnel(raw)
            self._personnel[person.id] = person
            self._index_personnel_aliases(person)

        for raw in data.get("finding_types", []):
            ftype = FindingType(
                id=str(raw.get("id")),
                name=str(raw.get("name")),
                severity_default=str(raw.get("severity_default")),
                severity_elevation=raw.get("severity_elevation"),
            )
            self._finding_types[ftype.id] = ftype

        self._non_standard = tuple(
            NonStandardCategory(
                category=str(raw.get("category")),
                precedent=str(raw.get("precedent", "")),
            )
            for raw in data.get("leave_no_stone_unturned", [])
        )

    def _index_aliases(self, entity: Entity) -> None:
        # Canonical name and every alias are indexed case-insensitively.
        for token in (entity.name, *entity.aliases):
            if token:
                self._alias_to_entity_ids.setdefault(
                    token.lower(), set()
                ).add(entity.id)

    def _index_personnel_aliases(self, person: Personnel) -> None:
        for token in (person.name, *person.aliases):
            if token:
                self._alias_to_personnel_ids.setdefault(
                    token.lower(), set()
                ).add(person.id)

    # ----------------------------- access -----------------------------------

    def entity_by_id(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def personnel_by_id(self, personnel_id: str) -> Personnel | None:
        return self._personnel.get(personnel_id)

    def all_entities(self) -> Iterable[Entity]:
        return list(self._entities.values())

    def entities_by_tier(self, tier: int) -> Iterable[Entity]:
        return list(self._entities_by_tier.get(tier, ()))

    def tier1_entities(self) -> Iterable[Entity]:
        return self.entities_by_tier(1)

    def tier2_entities(self) -> Iterable[Entity]:
        return self.entities_by_tier(2)

    def tier3_entities(self) -> Iterable[Entity]:
        return self.entities_by_tier(3)

    def tier4_entities(self) -> Iterable[Entity]:
        return self.entities_by_tier(4)

    def all_personnel(self) -> Iterable[Personnel]:
        return list(self._personnel.values())

    def all_finding_types(self) -> Iterable[FindingType]:
        return list(self._finding_types.values())

    def finding_type(self, ftype_id: str) -> FindingType | None:
        return self._finding_types.get(ftype_id.upper())

    def finding_type_default_severity(self, ftype_id: str) -> str:
        ftype = self.finding_type(ftype_id)
        return ftype.severity_default if ftype else "MEDIUM"

    def sub_detectors_for(self, entity_id: str) -> tuple[str, ...]:
        ent = self.entity_by_id(entity_id)
        return ent.sub_detectors if ent else ()

    def non_standard_categories(self) -> tuple[NonStandardCategory, ...]:
        return self._non_standard

    # ----------------------------- alias lookup -----------------------------

    def entity_ids_for_alias(self, alias: str) -> set[str]:
        """Case-insensitive alias lookup; returns the set of entity IDs."""
        return set(self._alias_to_entity_ids.get(alias.lower(), set()))

    def personnel_ids_for_alias(self, alias: str) -> set[str]:
        return set(self._alias_to_personnel_ids.get(alias.lower(), set()))


# --------------------------- module-level helpers ---------------------------


def load_default_registry() -> EntityRegistry:
    """Load the registry from the default path beside this module."""
    return EntityRegistry(DEFAULT_REGISTRY_PATH)


def _build_entity(raw: dict[str, Any], tier: int) -> Entity:
    return Entity(
        id=str(raw.get("id")),
        name=str(raw.get("name")),
        tier=tier,
        abbreviation=raw.get("abbreviation"),
        aliases=tuple(raw.get("aliases", []) or []),
        mas_status=raw.get("mas_status"),
        alert_prefix=raw.get("alert_prefix"),
        next_alert=int(raw.get("next_alert", 1)),
        sub_detectors=tuple(raw.get("sub_detectors", []) or []),
        presence=tuple(raw.get("presence", []) or []),
        contribution=raw.get("contribution"),
        relevance=raw.get("relevance"),
        notes=raw.get("notes"),
    )


def _build_personnel(raw: dict[str, Any]) -> Personnel:
    history = tuple(
        PersonnelHistoryEntry(
            entity=h.get("entity"),
            role=str(h.get("role", "")),
            evidence_refs=tuple(h.get("evidence_refs", []) or []),
        )
        for h in (raw.get("history") or [])
    )
    return Personnel(
        id=str(raw.get("id")),
        name=str(raw.get("name")),
        aliases=tuple(raw.get("aliases", []) or []),
        affiliation=raw.get("affiliation"),
        history=history,
        notes=raw.get("notes"),
    )
