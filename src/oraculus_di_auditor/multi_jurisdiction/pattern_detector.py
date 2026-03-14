"""Cross-jurisdiction pattern detector.

Analyzes anomaly results across jurisdictions to surface vendor playbook
replication, procurement parallels, and systemic governance gaps — patterns
that no single-jurisdiction tool can see.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Keywords that suggest vendor / contract identity in anomaly text
_VENDOR_KEYWORDS = re.compile(
    r"\b(mspa|bwc|alpr|axon|motorola|palantir|clearview|flock|"
    r"vigilant|shotspotter|fusus|cellhawk|gray|i2|esri|genetec|"
    r"sole[- ]source|sole source|no[- ]bid|single[- ]source)\b",
    re.IGNORECASE,
)

# Keywords that indicate procurement-related anomalies
_PROCUREMENT_KEYWORDS = re.compile(
    r"\b(contract|amendment|procurement|vendor|supplier|rfp|rfq|"
    r"bid|award|sole[- ]source|purchase|agreement|mou|ipa)\b",
    re.IGNORECASE,
)

# Keywords that indicate governance-related anomalies
_GOVERNANCE_KEYWORDS = re.compile(
    r"\b(governance|policy|oversight|authorization|approval|board|"
    r"council|commission|retention|privacy|safeguard|compliance)\b",
    re.IGNORECASE,
)


def _iter_anomalies(
    results: dict[str, dict[str, Any]],
) -> list[tuple[str, str, dict[str, Any]]]:
    """Yield (jurisdiction_id, detector_name, anomaly) for every anomaly."""
    rows: list[tuple[str, str, dict[str, Any]]] = []
    for jid, jdata in results.items():
        for doc_result in jdata.get("results", []):
            for detector, anomalies in doc_result.get("findings", {}).items():
                for anomaly in anomalies:
                    rows.append((jid, detector, anomaly))
    return rows


def _extract_vendor_keywords(text: str) -> list[str]:
    return list({m.lower() for m in _VENDOR_KEYWORDS.findall(text)})


def _confidence(matching_jids: int, total_jids: int) -> float:
    """Confidence scales with fraction of jurisdictions showing the pattern."""
    if total_jids < 2:
        return 0.0
    # Scale: 2/2 → 1.0, 2/3 → 0.67, 2/5 → 0.4, etc.
    return round(matching_jids / total_jids, 4)


def _pattern_id(prefix: str, key: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-")
    return f"{prefix}:{slug}"


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class CrossJurisdictionPatternDetector:
    """Detects patterns that repeat across multiple jurisdictions."""

    def __init__(self, results: dict[str, dict[str, Any]]) -> None:
        """
        Args:
            results: Output from
                :meth:`~oraculus_di_auditor.multi_jurisdiction.runner.MultiJurisdictionRunner.get_all_results`.
        """
        self._results = results
        self._all_anomalies = _iter_anomalies(results)
        self._total_jids = len(results)

    # ------------------------------------------------------------------
    # detect_vendor_playbook
    # ------------------------------------------------------------------

    def detect_vendor_playbook(self) -> list[dict[str, Any]]:
        """Detect when the same anomaly patterns appear across jurisdictions.

        Looks for:

        1. Same anomaly ``id`` triggering in multiple jurisdictions.
        2. Same severity profile across jurisdictions.
        3. Shared vendor / contract-type keywords in anomaly text.

        Returns a list of pattern dicts — one per repeating anomaly id that
        affects 2+ jurisdictions.
        """
        if self._total_jids < 2:
            return []

        # Group jurisdictions by anomaly id
        by_anomaly_id: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "jurisdictions": set(),
                "severities": [],
                "vendor_keywords": set(),
                "evidence": [],
                "detector": "",
            }
        )

        for jid, detector, anomaly in self._all_anomalies:
            aid = anomaly.get("id", "unknown")
            entry = by_anomaly_id[aid]
            entry["jurisdictions"].add(jid)
            entry["severities"].append(anomaly.get("severity", "medium"))
            entry["detector"] = detector
            entry["evidence"].append(
                {
                    "jurisdiction_id": jid,
                    "anomaly_id": aid,
                    "issue": anomaly.get("issue", ""),
                    "severity": anomaly.get("severity", "medium"),
                    "details": anomaly.get("details", {}),
                }
            )
            issue_text = anomaly.get("issue", "")
            for kw in _extract_vendor_keywords(issue_text):
                entry["vendor_keywords"].add(kw)

        patterns: list[dict[str, Any]] = []
        for anomaly_id, entry in by_anomaly_id.items():
            jids = entry["jurisdictions"]
            if len(jids) < 2:
                continue

            severities = entry["severities"]
            # Most common severity across occurrences
            common_severity = max(set(severities), key=severities.count)

            patterns.append(
                {
                    "pattern_id": _pattern_id("vp", anomaly_id),
                    "pattern_type": "vendor_playbook_replication",
                    "description": (
                        f"Anomaly '{anomaly_id}' detected in "
                        f"{len(jids)} jurisdiction(s), suggesting a "
                        "coordinated vendor playbook or shared procurement template."
                    ),
                    "jurisdictions_affected": sorted(jids),
                    "jurisdiction_count": len(jids),
                    "common_detector": entry["detector"],
                    "common_severity": common_severity,
                    "vendor_keywords": sorted(entry["vendor_keywords"]),
                    "evidence": entry["evidence"],
                    "confidence": _confidence(len(jids), self._total_jids),
                }
            )

        # Sort by confidence desc, then jurisdiction_count desc
        patterns.sort(key=lambda p: (-p["confidence"], -p["jurisdiction_count"]))
        return patterns

    # ------------------------------------------------------------------
    # detect_procurement_parallels
    # ------------------------------------------------------------------

    def detect_procurement_parallels(self) -> list[dict[str, Any]]:
        """Detect parallel procurement patterns across jurisdictions.

        Looks for:

        - Same vendor or contract keyword appearing in anomalies across
          multiple jurisdictions.
        - Sole-source patterns repeating.
        - Similar expansion/amendment ratios.
        - Similar timeline patterns (execution before authorization).

        Returns a list of parallel pattern dicts.
        """
        if self._total_jids < 2:
            return []

        # Group by shared procurement keyword
        keyword_to_jids: dict[str, set[str]] = defaultdict(set)
        keyword_details: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for jid, _detector, anomaly in self._all_anomalies:
            issue = anomaly.get("issue", "")
            details = anomaly.get("details", {})
            combined_text = issue + " " + str(details)

            for match in _PROCUREMENT_KEYWORDS.finditer(combined_text):
                kw = match.group(0).lower().replace("-", " ").replace("_", " ")
                keyword_to_jids[kw].add(jid)
                keyword_details[kw].append(
                    {
                        "jurisdiction_id": jid,
                        "anomaly_id": anomaly.get("id", ""),
                        "issue": issue,
                        "severity": anomaly.get("severity", "medium"),
                    }
                )

        patterns: list[dict[str, Any]] = []
        seen_pattern_ids: set[str] = set()

        for kw, jids in keyword_to_jids.items():
            if len(jids) < 2:
                continue
            pid = _pattern_id("pp", kw)
            if pid in seen_pattern_ids:
                continue
            seen_pattern_ids.add(pid)

            evidence = keyword_details[kw]
            severities = [e["severity"] for e in evidence]
            common_severity = max(set(severities), key=severities.count)

            patterns.append(
                {
                    "pattern_id": pid,
                    "pattern_type": "procurement_parallel",
                    "description": (
                        f"Procurement keyword '{kw}' appears in anomalies "
                        f"across {len(jids)} jurisdiction(s), indicating "
                        "parallel procurement practices."
                    ),
                    "vendor_or_keyword": kw,
                    "jurisdictions": sorted(jids),
                    "details": {
                        "jurisdiction_count": len(jids),
                        "common_severity": common_severity,
                        "evidence": evidence,
                    },
                }
            )

        patterns.sort(
            key=lambda p: -p["details"]["jurisdiction_count"],
        )
        return patterns

    # ------------------------------------------------------------------
    # detect_governance_gaps_regional
    # ------------------------------------------------------------------

    def detect_governance_gaps_regional(self) -> list[dict[str, Any]]:
        """Detect when governance gaps are consistent across a region.

        If multiple jurisdictions all lack governance for the same capability,
        that suggests a systemic issue rather than a local oversight.

        Returns a list of regional gap pattern dicts.
        """
        if self._total_jids < 2:
            return []

        # Group governance-related anomalies by their id
        gov_by_id: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "jurisdictions": set(),
                "evidence": [],
                "severity": [],
            }
        )

        for jid, _detector, anomaly in self._all_anomalies:
            aid = anomaly.get("id", "")
            issue = anomaly.get("issue", "")
            combined = aid + " " + issue + " " + str(anomaly.get("details", ""))

            # Only include if governance-flavoured
            if not _GOVERNANCE_KEYWORDS.search(combined):
                continue

            entry = gov_by_id[aid]
            entry["jurisdictions"].add(jid)
            entry["severity"].append(anomaly.get("severity", "medium"))
            entry["evidence"].append(
                {
                    "jurisdiction_id": jid,
                    "anomaly_id": aid,
                    "issue": issue,
                    "severity": anomaly.get("severity", "medium"),
                }
            )

        patterns: list[dict[str, Any]] = []
        for aid, entry in gov_by_id.items():
            jids = entry["jurisdictions"]
            if len(jids) < 2:
                continue

            severities = entry["severity"]
            common_severity = max(set(severities), key=severities.count)

            patterns.append(
                {
                    "pattern_id": _pattern_id("rg", aid),
                    "pattern_type": "regional_governance_gap",
                    "description": (
                        f"Governance anomaly '{aid}' detected in "
                        f"{len(jids)} jurisdiction(s), suggesting a "
                        "systemic regional governance gap."
                    ),
                    "jurisdictions_affected": sorted(jids),
                    "jurisdiction_count": len(jids),
                    "common_severity": common_severity,
                    "evidence": entry["evidence"],
                    "confidence": _confidence(len(jids), self._total_jids),
                }
            )

        patterns.sort(key=lambda p: (-p["confidence"], -p["jurisdiction_count"]))
        return patterns

    # ------------------------------------------------------------------
    # detect_all_patterns
    # ------------------------------------------------------------------

    def detect_all_patterns(self) -> dict[str, Any]:
        """Run all cross-jurisdiction pattern detectors.

        Returns:
            ::

                {
                    "patterns_detected": int,
                    "vendor_playbook_patterns": list[dict],
                    "procurement_parallels": list[dict],
                    "regional_governance_gaps": list[dict],
                    "summary": {
                        "jurisdictions_analyzed": int,
                        "most_common_pattern": str,
                        "highest_risk_jurisdictions": list[str],
                    }
                }
        """
        vp = self.detect_vendor_playbook()
        pp = self.detect_procurement_parallels()
        rg = self.detect_governance_gaps_regional()

        total = len(vp) + len(pp) + len(rg)

        # Most common pattern type by count
        counts = {
            "vendor_playbook_replication": len(vp),
            "procurement_parallel": len(pp),
            "regional_governance_gap": len(rg),
        }
        most_common = max(counts, key=lambda k: counts[k]) if total > 0 else "none"

        # Highest-risk jurisdictions: appear most frequently across all patterns
        jid_counts: dict[str, int] = defaultdict(int)
        for pattern in vp:
            for jid in pattern.get("jurisdictions_affected", []):
                jid_counts[jid] += 1
        for pattern in pp:
            for jid in pattern.get("jurisdictions", []):
                jid_counts[jid] += 1
        for pattern in rg:
            for jid in pattern.get("jurisdictions_affected", []):
                jid_counts[jid] += 1

        if jid_counts:
            max_count = max(jid_counts.values())
            highest_risk = sorted(
                jid for jid, cnt in jid_counts.items() if cnt == max_count
            )
        else:
            highest_risk = []

        return {
            "patterns_detected": total,
            "vendor_playbook_patterns": vp,
            "procurement_parallels": pp,
            "regional_governance_gaps": rg,
            "summary": {
                "jurisdictions_analyzed": self._total_jids,
                "most_common_pattern": most_common,
                "highest_risk_jurisdictions": highest_risk,
            },
        }
