"""C.O.N.T.R.A. entity registry with fuzzy name resolution.

EntityRegistry resolves commercial entity names to canonical Entity records.
In-memory mode (db_session=None) supports testing; DB mode persists to the
commercial_entities and commercial_entity_aliases tables.

Fuzzy matching uses rapidfuzz.fuzz.token_sort_ratio at the 0.88 threshold
specified in the C.O.N.T.R.A. Handoff Specification V1.0 Section 7.1.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from rapidfuzz import fuzz as _fuzz

from .normalize import normalize_corporate_suffix

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class Entity:
    """Canonical commercial entity record."""

    entity_id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    naics: Optional[str] = None
    corporate_family: Optional[str] = None
    in_contra_corpus: bool = False
    in_tulare_priority_list: bool = False

    @classmethod
    def new(
        cls,
        canonical_name: str,
        naics: Optional[str] = None,
        corporate_family: Optional[str] = None,
        in_contra_corpus: bool = True,
        in_tulare_priority_list: bool = False,
        aliases: Optional[List[str]] = None,
    ) -> "Entity":
        return cls(
            entity_id=str(uuid.uuid4()),
            canonical_name=canonical_name,
            aliases=aliases or [],
            naics=naics,
            corporate_family=corporate_family,
            in_contra_corpus=in_contra_corpus,
            in_tulare_priority_list=in_tulare_priority_list,
        )


class EntityRegistry:
    """Resolve commercial entity names to canonical Entity records.

    Supports two operating modes:
    - In-memory (db_session=None): all state lives in instance dicts.
      Used in tests and for dry-run ingestion.
    - DB-backed (db_session provided): reads from and writes to
      commercial_entities / commercial_entity_aliases tables.

    resolve() first tries exact lookup (case-insensitive), then fuzzy.
    fuzzy_match() normalizes both sides before scoring.
    """

    def __init__(self, db_session: Optional["Session"] = None) -> None:
        self._db = db_session
        # In-memory store — also used as a read-through cache for DB mode
        self._by_id: dict[str, Entity] = {}
        self._by_name: dict[str, str] = {}  # normalized_name -> entity_id
        self._by_alias: dict[str, str] = {}  # normalized_alias -> entity_id

        if db_session is not None:
            self._load_from_db()

    # ------------------------------------------------------------------
    # Public resolution interface
    # ------------------------------------------------------------------

    def resolve(self, name: str) -> Optional[Entity]:
        """Resolve a name to an Entity, exact match first then fuzzy.

        Returns None if no entity matches at the 0.88 threshold.
        """
        normalized = normalize_corporate_suffix(name).lower()

        # 1. Exact match on canonical name
        entity_id = self._by_name.get(normalized)
        if entity_id:
            return self._by_id.get(entity_id)

        # 2. Exact match on any alias
        entity_id = self._by_alias.get(normalized)
        if entity_id:
            return self._by_id.get(entity_id)

        # 3. Fuzzy fallback
        return self.fuzzy_match(name)

    def fuzzy_match(
        self, name: str, threshold: float = 0.88
    ) -> Optional[Entity]:
        """Fuzzy match name against all canonical names and aliases.

        Uses the max of token_sort_ratio (handles word-order variations)
        and partial_ratio (handles substring / prefix-match cases like
        "ATT Mobility" matching "ATT Mobility LLC"). threshold is 0-1.
        """
        normalized_input = normalize_corporate_suffix(name).lower()
        threshold_pct = threshold * 100  # rapidfuzz uses 0-100

        best_score = 0.0
        best_entity_id: Optional[str] = None

        all_keys = list(self._by_name.items()) + list(self._by_alias.items())
        for norm_key, eid in all_keys:
            score = max(
                _fuzz.token_sort_ratio(normalized_input, norm_key),
                _fuzz.partial_ratio(normalized_input, norm_key),
            )
            if score > best_score:
                best_score = score
                best_entity_id = eid

        if best_score >= threshold_pct and best_entity_id:
            return self._by_id.get(best_entity_id)
        return None

    # ------------------------------------------------------------------
    # Mutation interface
    # ------------------------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """Add or replace an entity in the registry."""
        self._by_id[entity.entity_id] = entity
        norm = normalize_corporate_suffix(entity.canonical_name).lower()
        self._by_name[norm] = entity.entity_id
        for alias in entity.aliases:
            norm_alias = normalize_corporate_suffix(alias).lower()
            self._by_alias[norm_alias] = entity.entity_id

        if self._db is not None:
            self._persist_entity(entity)

    def add_alias(self, entity_id: str, alias: str) -> None:
        """Register an additional name alias for an existing entity."""
        entity = self._by_id.get(entity_id)
        if entity is None:
            raise KeyError(f"Entity not found: {entity_id}")
        entity.aliases.append(alias)
        norm_alias = normalize_corporate_suffix(alias).lower()
        self._by_alias[norm_alias] = entity_id

        if self._db is not None:
            self._persist_alias(entity_id, alias)

    def get_by_id(self, entity_id: str) -> Optional[Entity]:
        return self._by_id.get(entity_id)

    def get_by_canonical_name(self, canonical_name: str) -> Optional[Entity]:
        """Exact normalized lookup by canonical name — no fuzzy fallback.

        Use this for deduplication during seeding where the input is
        already a known canonical name.
        """
        normalized = normalize_corporate_suffix(canonical_name).lower()
        entity_id = self._by_name.get(normalized)
        return self._by_id.get(entity_id) if entity_id else None

    def __len__(self) -> int:
        return len(self._by_id)

    # ------------------------------------------------------------------
    # DB persistence
    # ------------------------------------------------------------------

    def _load_from_db(self) -> None:
        from ..db.models import CommercialEntity, CommercialEntityAlias

        rows = self._db.query(CommercialEntity).all()  # type: ignore[union-attr]
        for row in rows:
            alias_rows = (
                self._db.query(CommercialEntityAlias)  # type: ignore[union-attr]
                .filter(CommercialEntityAlias.entity_id == row.entity_id)
                .all()
            )
            entity = Entity(
                entity_id=row.entity_id,
                canonical_name=row.canonical_name,
                aliases=[a.alias for a in alias_rows],
                naics=row.naics,
                corporate_family=row.corporate_family,
                in_contra_corpus=row.in_contra_corpus,
                in_tulare_priority_list=row.in_tulare_priority_list,
            )
            self._index_entity(entity)

    def _index_entity(self, entity: Entity) -> None:
        self._by_id[entity.entity_id] = entity
        norm = normalize_corporate_suffix(entity.canonical_name).lower()
        self._by_name[norm] = entity.entity_id
        for alias in entity.aliases:
            self._by_alias[normalize_corporate_suffix(alias).lower()] = entity.entity_id

    def _persist_entity(self, entity: Entity) -> None:
        from ..db.models import CommercialEntity, CommercialEntityAlias

        existing = (
            self._db.query(CommercialEntity)  # type: ignore[union-attr]
            .filter(CommercialEntity.entity_id == entity.entity_id)
            .first()
        )
        if existing is None:
            row = CommercialEntity(
                entity_id=entity.entity_id,
                canonical_name=entity.canonical_name,
                naics=entity.naics,
                corporate_family=entity.corporate_family,
                in_contra_corpus=entity.in_contra_corpus,
                in_tulare_priority_list=entity.in_tulare_priority_list,
            )
            self._db.add(row)  # type: ignore[union-attr]
        for alias in entity.aliases:
            alias_row = CommercialEntityAlias(
                entity_id=entity.entity_id, alias=alias
            )
            self._db.add(alias_row)  # type: ignore[union-attr]
        self._db.commit()  # type: ignore[union-attr]

    def _persist_alias(self, entity_id: str, alias: str) -> None:
        from ..db.models import CommercialEntityAlias

        row = CommercialEntityAlias(entity_id=entity_id, alias=alias)
        self._db.add(row)  # type: ignore[union-attr]
        self._db.commit()  # type: ignore[union-attr]
