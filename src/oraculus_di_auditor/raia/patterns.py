"""Cross-jurisdictional pattern detection over persisted anomalies.

This is the DB-backed cousin of
``multi_jurisdiction.pattern_detector.CrossJurisdictionPatternDetector``:
where that module takes an in-memory results dict from a synchronous
multi-audit run, this one consumes already-flattened
``JurisdictionSummary`` objects built from ``Document``/``Analysis``/
``Anomaly`` rows. That decoupling is what lets R.A.I.A. assemble a
synthesis from webhook ingests that arrived hours or days apart.

Three pattern types are produced:
  1. ``shared_anomaly_id``     — strongest: identical detector emits fire
                                 in 2+ jurisdictions.
  2. ``shared_layer_spike``    — 2+ jurisdictions with the same detector
                                 layer as their #1 producer.
  3. ``vendor_convergence``    — vendor keyword hits across jurisdictions,
                                 tying findings to a common playbook
                                 (Flock, Axon, Lexipol, etc.).
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from oraculus_di_auditor.raia.schemas import (
        AnomalyRow,
        CrossJurisdictionPattern,
        JurisdictionSummary,
    )

from oraculus_di_auditor.raia.schemas import (
    AnomalyRow,
    CrossJurisdictionPattern,
    JurisdictionSummary,
)

# Vendors / procurement mechanisms we want to surface when the same
# name appears across multiple jurisdictions. Mirrors the catalogue
# used by the in-memory multi-jurisdiction detector plus the v2.2.2
# vendor_database additions.
_VENDOR_KEYWORDS = re.compile(
    r"\b(flock|axon|motorola|palantir|clearview|"
    r"vigilant|shotspotter|fusus|cellhawk|gray|genetec|lexipol|"
    r"mspa|bwc|alpr|"
    r"sole[- ]source|sole source|no[- ]bid|single[- ]source)\b",
    re.IGNORECASE,
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "unknown"


def _extract_vendor_keywords(anomaly: AnomalyRow) -> set[str]:
    """Vendor keyword hits in the free-text fields of an anomaly row.

    Scans ``issue`` and stringified ``details`` together so a vendor
    name mentioned only inside the structured evidence block still
    counts. Returns a lowercased, de-duplicated set.
    """
    hay = anomaly.issue or ""
    if anomaly.details:
        # Convert nested details dict to a flat string without having
        # to walk it — the regex just needs to see the vendor word.
        hay = f"{hay} {anomaly.details}"
    return {m.lower() for m in _VENDOR_KEYWORDS.findall(hay)}


def _confidence(matching: int, total: int) -> float:
    if total < 2:
        return 0.0
    return round(matching / total, 4)


# ---------------------------------------------------------------------------
# Individual pattern detectors
# ---------------------------------------------------------------------------


def _shared_anomaly_ids(
    summaries: list[JurisdictionSummary],
) -> list[CrossJurisdictionPattern]:
    """Flag detector-emitted IDs that appear in 2+ jurisdictions.

    v3.0.5: iterates the FULL anomaly set (``all_anomalies``) not the
    display-capped ``top_anomalies``. Without this, finding IDs outside
    each jurisdiction's top-N window were invisible to pattern detection
    — observed live against the Visalia+Porterville corpus where only
    2 of 8 actually-shared finding IDs surfaced as patterns. Falls back
    to ``top_anomalies`` if ``all_anomalies`` is empty so older callers
    that build summaries by hand still work.
    """
    # anomaly_id -> set(jurisdiction_id)
    by_id: dict[str, set[str]] = defaultdict(set)
    # anomaly_id -> example issue text (first seen)
    example: dict[str, str] = {}
    for s in summaries:
        source = s.all_anomalies if s.all_anomalies else s.top_anomalies
        for a in source:
            by_id[a.anomaly_id].add(s.jurisdiction_id)
            example.setdefault(a.anomaly_id, a.issue)

    total = len(summaries)
    patterns: list[CrossJurisdictionPattern] = []
    for anomaly_id, jids in by_id.items():
        if len(jids) < 2:
            continue
        patterns.append(
            CrossJurisdictionPattern(
                pattern_id=f"shared-anomaly:{_slug(anomaly_id)}",
                pattern_type="shared_anomaly_id",
                jurisdictions_affected=sorted(jids),
                confidence=_confidence(len(jids), total),
                description=(
                    f"Detector fired the same anomaly `{anomaly_id}` in "
                    f"{len(jids)} jurisdictions: {sorted(jids)}. "
                    f"Example issue: {example.get(anomaly_id, '')[:160]}"
                ),
                evidence={
                    "anomaly_id": anomaly_id,
                    "jurisdictions": sorted(jids),
                    "example_issue": example.get(anomaly_id, ""),
                },
            )
        )
    patterns.sort(key=lambda p: (-p.confidence, p.pattern_id))
    return patterns


def _shared_layer_spikes(
    summaries: list[JurisdictionSummary],
    *,
    min_count: int = 1,
) -> list[CrossJurisdictionPattern]:
    """Flag detector layers that are a top producer in 2+ jurisdictions.

    A layer qualifies for a jurisdiction when it produced at least
    ``min_count`` anomalies and is tied for the highest per-jurisdiction
    count. (Ties are included — two layers each producing 5 anomalies
    each both count as "top".) The pattern fires when 2+ jurisdictions
    share a top layer.
    """
    # jurisdiction_id -> set(layer that is tied-top)
    top_layers: dict[str, set[str]] = {}
    for s in summaries:
        if not s.layer_counts:
            continue
        best = max(s.layer_counts.values())
        if best < min_count:
            continue
        top_layers[s.jurisdiction_id] = {
            layer for layer, c in s.layer_counts.items() if c == best
        }

    layer_to_jids: dict[str, set[str]] = defaultdict(set)
    for jid, layers in top_layers.items():
        for layer in layers:
            layer_to_jids[layer].add(jid)

    total = len(summaries)
    patterns: list[CrossJurisdictionPattern] = []
    for layer, jids in layer_to_jids.items():
        if len(jids) < 2:
            continue
        patterns.append(
            CrossJurisdictionPattern(
                pattern_id=f"shared-layer:{_slug(layer)}",
                pattern_type="shared_layer_spike",
                jurisdictions_affected=sorted(jids),
                confidence=_confidence(len(jids), total),
                description=(
                    f"Detector layer `{layer}` is a top anomaly producer "
                    f"in {len(jids)} jurisdictions: {sorted(jids)}. "
                    f"Suggests the same category of governance gap "
                    f"is recurring."
                ),
                evidence={
                    "layer": layer,
                    "jurisdictions": sorted(jids),
                },
            )
        )
    patterns.sort(key=lambda p: (-p.confidence, p.pattern_id))
    return patterns


def _vendor_convergences(
    summaries: list[JurisdictionSummary],
) -> list[CrossJurisdictionPattern]:
    """Flag vendor names present in anomalies across 2+ jurisdictions.

    v3.0.5: same fix as ``_shared_anomaly_ids`` — iterate the full
    anomaly set so a vendor mentioned only in lower-severity findings
    still surfaces. ``surveillance:vendor-detected:axon-enterprise``
    type findings are typically not top-of-jurisdiction (sit behind
    `signature:unsigned-instrument` CRITICALs) and were therefore
    invisible to vendor-convergence detection pre-v3.0.5.
    """
    vendor_to_jids: dict[str, set[str]] = defaultdict(set)
    vendor_counts: dict[str, Counter] = defaultdict(Counter)
    for s in summaries:
        source = s.all_anomalies if s.all_anomalies else s.top_anomalies
        seen: set[str] = set()
        for a in source:
            seen.update(_extract_vendor_keywords(a))
        for vendor in seen:
            vendor_to_jids[vendor].add(s.jurisdiction_id)
            vendor_counts[vendor][s.jurisdiction_id] += 1

    total = len(summaries)
    patterns: list[CrossJurisdictionPattern] = []
    for vendor, jids in vendor_to_jids.items():
        if len(jids) < 2:
            continue
        patterns.append(
            CrossJurisdictionPattern(
                pattern_id=f"vendor-convergence:{_slug(vendor)}",
                pattern_type="vendor_convergence",
                jurisdictions_affected=sorted(jids),
                confidence=_confidence(len(jids), total),
                description=(
                    f"Vendor keyword `{vendor}` appears in anomalies across "
                    f"{len(jids)} jurisdictions: {sorted(jids)}. "
                    f"Consistent with a shared vendor playbook or "
                    f"boilerplate contract."
                ),
                evidence={
                    "vendor": vendor,
                    "jurisdictions": sorted(jids),
                    "per_jurisdiction_hits": dict(vendor_counts[vendor]),
                },
            )
        )
    patterns.sort(key=lambda p: (-p.confidence, p.pattern_id))
    return patterns


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect_patterns(
    summaries: list[JurisdictionSummary],
) -> list[CrossJurisdictionPattern]:
    """Run all cross-jurisdiction detectors and return the combined list.

    Requires at least two jurisdictions with data to produce anything;
    returns ``[]`` otherwise (a single jurisdiction cannot exhibit a
    cross-jurisdiction pattern by definition).
    """
    populated = [s for s in summaries if s.document_count > 0]
    if len(populated) < 2:
        return []
    out: list[CrossJurisdictionPattern] = []
    out.extend(_shared_anomaly_ids(populated))
    out.extend(_shared_layer_spikes(populated))
    out.extend(_vendor_convergences(populated))
    # Stable sort: strongest first (highest confidence), then pattern_id
    # so equal-confidence patterns come out in a predictable order.
    out.sort(key=lambda p: (-p.confidence, p.pattern_id))
    return out


__all__ = ["detect_patterns"]
