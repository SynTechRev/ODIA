"""D-13 -- Cross-Entity Detector (function-style).

The 13th detector in the O.D.I.A. analytical suite. Where D-1 through
D-12 each look for a single forensic pattern within a single document
under a single jurisdiction's analytical track, D-13 sweeps every
document against the full Cross-Entity Registry and emits findings
whenever a document tagged to one entity contains substantive
references to any other entity in the registry.

Adapted from the Cross-Entity Analysis Protocol V1.0 (May 2026)
"cross_entity_detector.py" handoff bundle. Two structural changes
from the bundled module:

  1. Function-style, returns ``list[dict]`` per the
     ``analysis/`` package convention -- not class-style with a
     ``Detector`` ABC and ``Finding`` instances. (The ABC stack the
     handoff assumed does not exist in this codebase.)

  2. Type B (Personnel Migration) classifier carries a ``kind`` flag
     through ``AliasHit`` instead of inferring it from the target
     entity ID. The bundled module checked
     ``target_entity_id.startswith("P-")`` after personnel hits had
     already been re-keyed under their entity targets (E-NNN / V-NNN),
     so Type B never fired. The fix is mechanical -- mark each hit at
     scan time and read the mark at classify time.

Activation: requires the document to be tagged with
``metadata.primary_entity = "E-NNN"``. Documents without that tag are
not yet routed through the cross-entity track; D-13 silently returns
``[]`` (no warning, no noise) so older corpora pre-protocol still
ingest cleanly.

Confidence scoring follows the protocol docstring:

  + entity-canonical-name or alias match (base):     +0.50
  + multiple mentions of same target (>=3 hits):     +0.10
  + dollar amount within the excerpt:                +0.10
  + multi-signal co-occurrence:                      +0.05 each
  + low-confidence floor (< 0.40) -> severity demoted to "low"

Severity per finding type follows protocol section 4.3 (registry's
``finding_types`` block); type-specific elevation rules are encoded
in ``_resolve_severity``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from oraculus_di_auditor.analysis.text_utils import extract_text_content
from oraculus_di_auditor.registry import (
    EntityRegistry,
    load_default_registry,
)

# ---------------------------------------------------------------------------
# Module-level lazy singletons.
#
# Loading the YAML registry is non-trivial (~36 entities, 13 personnel,
# alias indexing) and we don't want to pay it on every detector call.
# First call hydrates; subsequent calls reuse.
# ---------------------------------------------------------------------------

_REGISTRY: EntityRegistry | None = None
_ENTITY_ALIAS_PATTERNS: dict[str, re.Pattern[str]] | None = None
_PERSONNEL_ALIAS_PATTERNS: dict[str, re.Pattern[str]] | None = None

# Minimum text length below which we don't run D-13. Empty or
# near-empty bodies produce no useful cross-references; running
# regex on them just inflates the noise floor.
_MIN_TEXT_LENGTH = 100

# Excerpts wider than this number of characters per side aren't more
# informative for forensic review; they just blow up the finding
# payload size.
_EXCERPT_HALF_WIDTH = 150


def _get_registry() -> EntityRegistry:
    """Return the process-singleton registry, loading on first call."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = load_default_registry()
    return _REGISTRY


def _reset_caches_for_tests() -> None:
    """Test helper: clear the cached registry and pattern indexes.

    Pytest fixtures use a registry loaded from a custom YAML; clearing
    the cache between tests lets the next call pick up the test
    fixture instead of the production entities.yml.
    """
    global _REGISTRY, _ENTITY_ALIAS_PATTERNS, _PERSONNEL_ALIAS_PATTERNS
    _REGISTRY = None
    _ENTITY_ALIAS_PATTERNS = None
    _PERSONNEL_ALIAS_PATTERNS = None


# ---------------------------------------------------------------------------
# AliasHit -- internal record for a single matched alias.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AliasHit:
    """A single regex hit of an entity or personnel alias in document text.

    ``kind`` records whether the matched alias came from the entity
    index (kind="entity") or the personnel index (kind="personnel").
    This is the field that drives Type-B (Personnel Migration)
    classification later; the original handoff module inferred it
    from the target entity ID, which was always wrong because
    personnel hits get re-keyed under their entity targets.
    """

    matched_id: str  # E-NNN | V-NNN | P-NNN
    kind: str  # "entity" or "personnel"
    alias_matched: str
    span: tuple[int, int]
    excerpt: str


# ---------------------------------------------------------------------------
# Alias pattern compilation.
# ---------------------------------------------------------------------------


def _build_alias_pattern(aliases) -> re.Pattern[str] | None:
    """Build a single compiled regex matching any alias as a whole word.

    Word boundaries (``\\b``) prevent false matches like "DPD" inside
    "DPDx" or "Ford" inside "Stafford". Aliases are sorted
    longest-first so the longer alias (e.g. "Tulare County Sheriff's
    Office") wins over the shorter one ("Tulare County Sheriff") when
    they share a prefix.
    """
    cleaned = sorted({a for a in aliases if a}, key=len, reverse=True)
    if not cleaned:
        return None
    escaped = "|".join(re.escape(a) for a in cleaned)
    return re.compile(rf"\b(?:{escaped})\b", re.IGNORECASE)


def _get_alias_patterns() -> tuple[
    dict[str, re.Pattern[str]],
    dict[str, re.Pattern[str]],
]:
    """Return (entity_patterns, personnel_patterns), compiling on first call."""
    global _ENTITY_ALIAS_PATTERNS, _PERSONNEL_ALIAS_PATTERNS
    if _ENTITY_ALIAS_PATTERNS is None or _PERSONNEL_ALIAS_PATTERNS is None:
        reg = _get_registry()
        entity_patterns: dict[str, re.Pattern[str]] = {}
        for ent in reg.all_entities():
            pat = _build_alias_pattern(ent.aliases)
            if pat is not None:
                entity_patterns[ent.id] = pat
        personnel_patterns: dict[str, re.Pattern[str]] = {}
        for person in reg.all_personnel():
            pat = _build_alias_pattern(person.aliases)
            if pat is not None:
                personnel_patterns[person.id] = pat
        _ENTITY_ALIAS_PATTERNS = entity_patterns
        _PERSONNEL_ALIAS_PATTERNS = personnel_patterns
    return _ENTITY_ALIAS_PATTERNS, _PERSONNEL_ALIAS_PATTERNS


def _scan(
    text: str,
    patterns: dict[str, re.Pattern[str]],
    kind: str,
) -> list[AliasHit]:
    """Scan text for every pattern in the index, returning AliasHit records."""
    hits: list[AliasHit] = []
    for record_id, pat in patterns.items():
        for match in pat.finditer(text):
            start = max(0, match.start() - _EXCERPT_HALF_WIDTH)
            end = min(len(text), match.end() + _EXCERPT_HALF_WIDTH)
            excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
            hits.append(
                AliasHit(
                    matched_id=record_id,
                    kind=kind,
                    alias_matched=match.group(0),
                    span=(match.start(), match.end()),
                    excerpt=excerpt,
                )
            )
    return hits


# ---------------------------------------------------------------------------
# Finding-type classification signals.
# ---------------------------------------------------------------------------

_BUDGET_FISCAL_SIGNALS = re.compile(
    r"\b(?:\$[\d,]+|budget|appropriation|line\s*item|expenditure|"
    r"allocation|fiscal\s*year|FY\d{2,4}|cost\s*center|grant\s*award|"
    r"approximately\s*\$|amount\s*not\s*to\s*exceed|NTE)\b",
    re.IGNORECASE,
)

_PERSONNEL_MIGRATION_SIGNALS = re.compile(
    r"\b(?:promoted|appointed|former|formerly|hired\s*from|previously|"
    r"transferred|resigned|sworn\s*in|MOU|mutual\s*aid|loaned)\b",
    re.IGNORECASE,
)

_OPERATIONAL_INTERSECT_SIGNALS = re.compile(
    r"\b(?:joint\s*operation|task\s*force|multi[- ]?agency|cooperation|"
    r"in\s*coordination\s*with|assisted\s*by|with\s*assistance\s*from|"
    r"deputized|deployed|served\s*warrant)\b",
    re.IGNORECASE,
)

_GOVERNANCE_CHAIN_SIGNALS = re.compile(
    r"\b(?:resolution|ordinance|approved\s*by|authorized\s*by|"
    r"consent\s*calendar|item\s*\d+\.\d+|agenda\s*item|board\s*"
    r"action|council\s*action|5-0\s*vote|unanimous)\b",
    re.IGNORECASE,
)

_GRANT_FUNDING_SIGNALS = re.compile(
    r"\b(?:JAG|Edward\s*Byrne|COPS|SLESF|AB\s*109|realignment|"
    r"grant\s*application|grant\s*award|federal\s*funds|state\s*funds|"
    r"matching\s*funds|sub-?recipient)\b",
    re.IGNORECASE,
)

_DATA_EVIDENCE_SIGNALS = re.compile(
    r"\b(?:Evidence\.com|evidence\s*management|case\s*management\s*"
    r"system|access\s*to\s*data|data\s*sharing|FlockOS|video\s*footage|"
    r"BWC\s*footage|ALPR\s*data|export\s*to|integration\s*with|"
    r"interfaces?\s*with|consumes?|ingests?)\b",
    re.IGNORECASE,
)


def _classify_hit(
    hit: AliasHit,
    primary_entity: str,
    target_entity,  # registry.types.Entity
) -> tuple[str, float]:
    """Classify one hit into a finding type (A-G) with a base confidence.

    Returns ``(finding_type, base_confidence)``. Vendor cross-
    contamination (Type C) is detected geometrically -- the target is
    a Tier-3 vendor and the primary entity is NOT in the vendor's
    confirmed presence list. That overrides every other signal because
    Type C is the most consequential cross-reference per the protocol
    (Farmersville / Woodlake / Visalia Axon Outpost precedents).
    """
    excerpt = hit.excerpt
    is_personnel = hit.kind == "personnel"
    type_scores: dict[str, float] = {
        "A": 1.0 if _BUDGET_FISCAL_SIGNALS.search(excerpt) else 0.0,
        "B": (
            1.0
            if is_personnel and _PERSONNEL_MIGRATION_SIGNALS.search(excerpt)
            else 0.0
        ),
        "C": 0.0,  # handled by the vendor-presence override below
        "D": 1.0 if _OPERATIONAL_INTERSECT_SIGNALS.search(excerpt) else 0.0,
        "E": 1.0 if _GOVERNANCE_CHAIN_SIGNALS.search(excerpt) else 0.0,
        "F": 1.0 if _GRANT_FUNDING_SIGNALS.search(excerpt) else 0.0,
        "G": 1.0 if _DATA_EVIDENCE_SIGNALS.search(excerpt) else 0.0,
    }

    # Vendor cross-contamination: Tier-3 vendor referenced in a
    # jurisdiction not in its confirmed presence list. Always Type C,
    # always CRITICAL, outrank every other signal.
    if target_entity.tier == 3:
        if primary_entity not in (target_entity.presence or ()):
            type_scores["C"] = 2.0

    # B alone needs the personnel-migration verb to fire. If a
    # personnel hit landed but no migration verb, fall through to D
    # (operational intersection) so the cross-reference is still
    # surfaced rather than lost.
    if is_personnel and type_scores["B"] == 0.0 and type_scores["D"] == 0.0:
        type_scores["D"] = 0.5

    if not any(type_scores.values()):
        # No specific signal -- the alias matched but the surrounding
        # context fits no canonical pattern. Default Type D at very low
        # confidence; the analyst can promote it in RAIA review.
        return ("D", 0.25)

    best_type = max(type_scores, key=lambda k: type_scores[k])
    # Confidence floor for any positive-signal hit, plus a small bonus
    # for multi-signal co-occurrence.
    signal_count = sum(1 for s in type_scores.values() if s > 0)
    confidence = 0.50 + 0.05 * signal_count
    return (best_type, min(confidence, 1.0))


# ---------------------------------------------------------------------------
# Severity resolution per protocol section 4.3.
# ---------------------------------------------------------------------------

# Default severity per finding type (mirrors entities.yml.finding_types).
# Lowercase to match the rest of the analysis package's output shape.
_SEVERITY_DEFAULT: dict[str, str] = {
    "A": "high",
    "B": "high",
    "C": "critical",
    "D": "high",
    "E": "high",
    "F": "high",
    "G": "high",
}


def _resolve_severity(
    finding_type: str,
    target_entity,  # registry.types.Entity
    primary_entity: str,
    excerpt: str,
    registry: EntityRegistry,
) -> str:
    """Apply protocol section 4.3 severity rules; return lowercase string."""
    excerpt_lower = excerpt.lower()

    # Type A elevation: new vendor presence revealed via budget reference
    if finding_type == "A":
        for vendor in registry.tier3_entities():
            if primary_entity in (vendor.presence or ()):
                continue  # already known; not new
            for alias in vendor.aliases:
                if not alias:
                    continue
                if re.search(rf"\b{re.escape(alias)}\b", excerpt, re.IGNORECASE):
                    return "critical"
        return "high"

    # Type B elevation: authority -> prosecution migration (Fahoum precedent)
    if finding_type == "B":
        if any(
            term in excerpt_lower
            for term in ("prosecution", "felony", "indictment", "charged")
        ):
            return "critical"
        return "high"

    # Type C is always CRITICAL by definition (vendor cross-contamination)
    if finding_type == "C":
        return "critical"

    # Type E elevation: governance action creates unmet obligation
    if finding_type == "E":
        if re.search(r"\b(?:obligation|required|must|shall)\b", excerpt, re.IGNORECASE):
            if re.search(
                r"\b(?:absent|missing|gap|no\s*record|never)\b",
                excerpt,
                re.IGNORECASE,
            ):
                return "critical"
        return "high"

    # Type G elevation: data flow without disclosed governance
    if finding_type == "G":
        if re.search(r"\b(?:access|integration|interfaces?)\b", excerpt, re.IGNORECASE):
            if not re.search(
                r"\b(?:approved|authorized|MOU|agreement|consent)\b",
                excerpt,
                re.IGNORECASE,
            ):
                return "critical"
        return "high"

    return _SEVERITY_DEFAULT.get(finding_type, "medium")


# ---------------------------------------------------------------------------
# Aggregation -- group hits by (primary, target) pair.
# ---------------------------------------------------------------------------


def _group_hits_by_target(
    entity_hits: list[AliasHit],
    personnel_hits: list[AliasHit],
    primary_entity: str,
    registry: EntityRegistry,
) -> dict[str, list[AliasHit]]:
    """Group raw alias hits by (primary -> target) entity pair.

    Entity hits get keyed under their matched entity. Personnel hits
    get keyed under every entity in the matched person's history
    (except the primary), so a Fahoum reference in a VPD document
    surfaces as XREFs to both VPD (where Fahoum was procurement
    authority) and TCDAO (where Fahoum is now a prosecution subject).
    """
    grouped: dict[str, list[AliasHit]] = {}

    for hit in entity_hits:
        if hit.matched_id == primary_entity:
            continue  # self-reference, skip
        grouped.setdefault(hit.matched_id, []).append(hit)

    for hit in personnel_hits:
        person = registry.personnel_by_id(hit.matched_id)
        if not person:
            continue
        for history_entry in person.history:
            target = history_entry.entity
            if target and target != primary_entity:
                grouped.setdefault(target, []).append(hit)

    return grouped


# ---------------------------------------------------------------------------
# Finding emission.
# ---------------------------------------------------------------------------


def _doc_id(doc: dict[str, Any]) -> str:
    meta = doc.get("metadata") or {}
    return (
        meta.get("document_id")
        or meta.get("id")
        or doc.get("document_id")
        or doc.get("id")
        or "unknown-doc"
    )


def _build_finding(
    finding_type: str,
    primary_entity: str,
    target_entity_id: str,
    target_entity_name: str,
    severity: str,
    confidence: float,
    alias_matched: str,
    excerpts: list[str],
    occurrence_count: int,
    document_id: str,
) -> dict[str, Any]:
    """Construct one finding dict in the canonical analysis-output shape."""
    xref_notation = (
        f"XREF-{primary_entity}-{target_entity_id}-{document_id}-"
        f"{finding_type}-{alias_matched[:30].replace(' ', '_')}"
    )
    return {
        "id": f"cross_entity:type-{finding_type.lower()}",
        "issue": (
            f"Cross-entity reference: document tagged to {primary_entity} "
            f"references {target_entity_name} ({target_entity_id}) via "
            f'alias "{alias_matched}" (Type {finding_type}).'
        ),
        "severity": severity,
        "layer": "cross_entity",
        "details": {
            "source_entity": primary_entity,
            "target_entity": target_entity_id,
            "target_entity_name": target_entity_name,
            "finding_type": finding_type,
            "alias_matched": alias_matched,
            "occurrence_count": occurrence_count,
            "confidence": round(confidence, 2),
            "xref_notation": xref_notation,
            "excerpts": excerpts[:3],
        },
    }


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------


def detect_cross_entity_anomalies(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the D-13 cross-entity sweep on a single normalised document.

    Args:
        doc: Normalised document dict. Expected metadata:
            ``doc["metadata"]["primary_entity"]`` -- the entity ID
            this document is tagged to. Without it, D-13 returns an
            empty list (the document isn't part of the cross-entity
            track yet; older corpora pass through unchanged).

    Returns:
        List of finding dicts in the standard analysis-output shape
        (``{id, issue, severity, layer, details}``). Empty when no
        cross-references are present or when the document is not
        tagged for cross-entity analysis.
    """
    findings: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return findings

    metadata = doc.get("metadata") or {}
    primary_entity = metadata.get("primary_entity") or doc.get("primary_entity")
    if not primary_entity:
        return findings

    text = extract_text_content(doc)
    if len(text.strip()) < _MIN_TEXT_LENGTH:
        return findings

    registry = _get_registry()
    entity_patterns, personnel_patterns = _get_alias_patterns()

    entity_hits = _scan(text, entity_patterns, kind="entity")
    personnel_hits = _scan(text, personnel_patterns, kind="personnel")

    grouped = _group_hits_by_target(
        entity_hits, personnel_hits, primary_entity, registry
    )

    document_id = _doc_id(doc)

    for target_entity_id, hits in grouped.items():
        target = registry.entity_by_id(target_entity_id)
        if not target:
            continue

        # Score every hit; the highest-confidence one becomes the
        # representative for the aggregated finding.
        best_type, best_confidence = _classify_hit(hits[0], primary_entity, target)
        best_hit = hits[0]
        for hit in hits[1:]:
            ftype, conf = _classify_hit(hit, primary_entity, target)
            if conf > best_confidence:
                best_type, best_confidence, best_hit = ftype, conf, hit

        confidence = best_confidence
        if len(hits) >= 3:
            confidence += 0.10  # repeated reference -> stronger signal
        if re.search(r"\$[\d,]+", best_hit.excerpt):
            confidence += 0.10
        confidence = min(confidence, 1.0)

        severity = _resolve_severity(
            best_type, target, primary_entity, best_hit.excerpt, registry
        )
        if confidence < 0.40:
            # Low-confidence demotion: keep the finding surfaced but
            # at the lowest severity so the analyst can promote in
            # RAIA review rather than ignoring.
            severity = "low"

        findings.append(
            _build_finding(
                finding_type=best_type,
                primary_entity=primary_entity,
                target_entity_id=target_entity_id,
                target_entity_name=target.name,
                severity=severity,
                confidence=confidence,
                alias_matched=best_hit.alias_matched,
                excerpts=[h.excerpt for h in hits[:3]],
                occurrence_count=len(hits),
                document_id=document_id,
            )
        )

    return findings
