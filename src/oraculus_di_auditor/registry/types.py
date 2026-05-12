"""Typed dataclasses for the O.D.I.A. Cross-Entity Registry.

Mirrors the schema documented at the top of registry/entities.yml.
The loader deserialises the YAML into instances of these types; the
D-13 cross-entity detector consumes them.

Every dataclass is frozen for two reasons:

  1. Registry data is immutable for a given run; freezing surfaces
     accidental mutation as a TypeError instead of silent corruption.
  2. Frozen dataclasses are hashable, so they can be placed in sets
     and used as dict keys for alias indexing.

Tuples are used for any list-shaped field for the same reason - lists
are not hashable; frozen dataclasses that contain lists are not
hashable either.
"""

from __future__ import annotations

from dataclasses import dataclass

# Tier IDs used across the schema.
TIER_PRIMARY_JURISDICTIONS = 1
TIER_GOVERNANCE = 2
TIER_VENDORS = 3
TIER_EXTERNAL_SOURCES = 4


@dataclass(frozen=True)
class Entity:
    """An entity in the registry.

    Populated fields differ by tier:

      Tier 1 (primary jurisdictions): name, abbreviation, aliases,
          mas_status, alert_prefix, next_alert, sub_detectors, notes
      Tier 2 (governance / oversight): name, abbreviation, aliases,
          relevance
      Tier 3 (vendors): name, aliases, presence, notes
      Tier 4 (external sources): name, contribution
    """

    id: str
    name: str
    tier: int
    abbreviation: str | None = None
    aliases: tuple[str, ...] = ()
    mas_status: str | None = None
    alert_prefix: str | None = None
    next_alert: int = 1
    sub_detectors: tuple[str, ...] = ()
    # Tier 3 vendors: list of E-IDs where confirmed.
    presence: tuple[str, ...] = ()
    # Tier 4 only.
    contribution: str | None = None
    # Tier 2 only.
    relevance: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class PersonnelHistoryEntry:
    """One row in a Personnel.history sequence.

    Each entry records a single (jurisdiction, role) appearance with
    optional evidence pointers back into the audit corpus.
    """

    entity: str | None  # entity ID where this person appears (None == unaffiliated)
    role: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class Personnel:
    """An individual named in the audit corpus, mapped across appearances."""

    id: str
    name: str
    aliases: tuple[str, ...] = ()
    # vendor ID (V-NNN) when this person represents a vendor.
    affiliation: str | None = None
    history: tuple[PersonnelHistoryEntry, ...] = ()
    notes: str | None = None


@dataclass(frozen=True)
class FindingType:
    """One of the seven cross-entity finding type rules (A through G)."""

    id: str  # one of "A" through "G"
    name: str
    severity_default: str  # "HIGH" | "CRITICAL"
    # Human-readable elevation rule (e.g. "CRITICAL when new vendor revealed").
    severity_elevation: str | None = None


@dataclass(frozen=True)
class NonStandardCategory:
    """A "Leave No Stone Unturned" non-standard record category.

    These are categories that have historically produced CRITICAL
    findings invisible to standard ingestion paths. Every audit run
    must verify these categories have been swept.
    """

    category: str
    precedent: str
