"""Cross-Entity Registry package for O.D.I.A.

Public surface::

    from oraculus_di_auditor.registry import (
        EntityRegistry,
        load_default_registry,
        Entity,
        Personnel,
        FindingType,
    )

The registry is the canonical Sunshine Dragnet entity catalogue defined
in the Cross-Entity Analysis Protocol V1.0 (May 2026). Every document
entering the O.D.I.A. ingestion pipeline is classified against this
registry; the D-13 cross-entity detector consumes it to surface
references between the document's primary entity and any other entity
in the catalogue.
"""

from oraculus_di_auditor.registry.loader import (
    DEFAULT_REGISTRY_PATH,
    EntityRegistry,
    load_default_registry,
)
from oraculus_di_auditor.registry.types import (
    Entity,
    FindingType,
    NonStandardCategory,
    Personnel,
    PersonnelHistoryEntry,
)

__all__ = [
    "DEFAULT_REGISTRY_PATH",
    "Entity",
    "EntityRegistry",
    "FindingType",
    "NonStandardCategory",
    "Personnel",
    "PersonnelHistoryEntry",
    "load_default_registry",
]
