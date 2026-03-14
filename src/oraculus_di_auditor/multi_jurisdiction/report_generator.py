"""Comparative report generator for multi-jurisdiction analysis.

Produces JSON and Markdown reports suitable for oversight bodies,
journalists, or public disclosure.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

# ---------------------------------------------------------------------------
# Risk scoring weights
# ---------------------------------------------------------------------------

_SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 5,
    "high": 3,
    "medium": 1,
    "low": 0,
}
_PATTERN_INVOLVEMENT_BONUS = 2


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _top_severity(by_severity: dict[str, int]) -> str:
    """Return the highest severity bucket that has a non-zero count."""
    for level in ("critical", "high", "medium", "low"):
        if by_severity.get(level, 0) > 0:
            return level
    return "none"


def _risk_score(
    by_severity: dict[str, int],
    pattern_involvement: int = 0,
) -> float:
    """Compute a risk score for one jurisdiction."""
    score = sum(
        _SEVERITY_WEIGHTS.get(sev, 0) * count for sev, count in by_severity.items()
    )
    score += pattern_involvement * _PATTERN_INVOLVEMENT_BONUS
    return float(score)


def _pattern_involvement_counts(
    patterns: dict[str, Any],
) -> dict[str, int]:
    """Count how many cross-jurisdiction patterns each jurisdiction appears in."""
    counts: dict[str, int] = {}
    for pattern_list in (
        patterns.get("vendor_playbook_patterns", []),
        patterns.get("regional_governance_gaps", []),
    ):
        for p in pattern_list:
            for jid in p.get("jurisdictions_affected", []):
                counts[jid] = counts.get(jid, 0) + 1
    for p in patterns.get("procurement_parallels", []):
        for jid in p.get("jurisdictions", []):
            counts[jid] = counts.get(jid, 0) + 1
    return counts


def _all_detectors(runner_results: dict[str, dict[str, Any]]) -> list[str]:
    """Collect every detector name seen across all jurisdictions, sorted."""
    detectors: set[str] = set()
    for jdata in runner_results.values():
        detectors.update(jdata.get("anomaly_summary", {}).get("by_detector", {}).keys())
    return sorted(detectors)


def _top_findings(
    jdata: dict[str, Any],
    n: int = 3,
) -> list[str]:
    """Return top-n anomaly issue strings for a jurisdiction, highest severity first."""
    issues: list[tuple[int, str]] = []
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    for doc_result in jdata.get("results", []):
        for anomalies in doc_result.get("findings", {}).values():
            for anomaly in anomalies:
                rank = sev_order.get(anomaly.get("severity", "medium"), 2)
                issues.append((rank, anomaly.get("issue", "")))
    issues.sort(key=lambda x: x[0])
    seen: list[str] = []
    for _, issue in issues:
        if issue and issue not in seen:
            seen.append(issue)
        if len(seen) >= n:
            break
    return seen


def _extract_dates_from_results(
    runner_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Pull structured date references from anomaly details across all jurisdictions."""
    events: list[dict[str, Any]] = []
    date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")

    for jid, jdata in runner_results.items():
        for doc_result in jdata.get("results", []):
            for detector, anomalies in doc_result.get("findings", {}).items():
                for anomaly in anomalies:
                    details = anomaly.get("details", {})
                    # Prefer explicit date fields from procurement_timeline detector
                    exec_date = details.get("execution_date")
                    auth_date = details.get("authorization_date")
                    if exec_date:
                        events.append(
                            {
                                "jurisdiction": jid,
                                "date": exec_date,
                                "event_type": "contract_execution",
                                "description": anomaly.get("issue", ""),
                            }
                        )
                    if auth_date:
                        events.append(
                            {
                                "jurisdiction": jid,
                                "date": auth_date,
                                "event_type": "council_authorization",
                                "description": anomaly.get("issue", ""),
                            }
                        )
                    # Also scan issue text for any ISO dates
                    if not exec_date and not auth_date:
                        issue_text = anomaly.get("issue", "")
                        for match in date_pattern.finditer(issue_text):
                            events.append(
                                {
                                    "jurisdiction": jid,
                                    "date": match.group(1),
                                    "event_type": detector,
                                    "description": issue_text,
                                }
                            )

    events.sort(key=lambda e: (e["date"], e["jurisdiction"]))
    return events


def _build_recommendations(
    patterns: dict[str, Any],
    runner_results: dict[str, dict[str, Any]],
) -> list[str]:
    """Generate actionable recommendations from detected patterns."""
    recs: list[str] = []

    vp = patterns.get("vendor_playbook_patterns", [])
    pp = patterns.get("procurement_parallels", [])
    rg = patterns.get("regional_governance_gaps", [])

    if vp:
        jids = sorted({jid for p in vp for jid in p.get("jurisdictions_affected", [])})
        recs.append(
            f"Conduct coordinated procurement audit across "
            f"{len(jids)} jurisdiction(s) ({', '.join(jids)}) where vendor "
            "playbook replication patterns were detected."
        )

    if pp:
        keywords = sorted(
            {p.get("vendor_or_keyword", "") for p in pp if p.get("vendor_or_keyword")}
        )
        if keywords:
            recs.append(
                f"Investigate shared procurement practices around: "
                f"{', '.join(keywords[:5])}. "
                "Parallel procurement language may indicate coordinated contracting."
            )

    if rg:
        recs.append(
            f"Address systemic governance gaps found across "
            f"{len(rg)} regional pattern(s). Develop shared policy "
            "templates to close capability-without-governance deficiencies."
        )

    # Jurisdiction-level recommendations
    for jid, jdata in runner_results.items():
        by_sev = jdata.get("anomaly_summary", {}).get("by_severity", {})
        if by_sev.get("critical", 0) > 0:
            recs.append(
                f"Prioritize immediate review of {jid}: "
                f"{by_sev['critical']} critical anomaly(ies) detected."
            )

    if not recs:
        recs.append(
            "No cross-jurisdiction patterns detected. "
            "Continue routine monitoring per jurisdiction."
        )

    return recs


# ---------------------------------------------------------------------------
# Public class
# ---------------------------------------------------------------------------


class ComparativeReportGenerator:
    """Generates cross-jurisdiction comparison reports."""

    def __init__(
        self,
        runner_results: dict[str, dict[str, Any]],
        patterns: dict[str, Any],
    ) -> None:
        """
        Args:
            runner_results: From
                :meth:`~oraculus_di_auditor.multi_jurisdiction.runner.MultiJurisdictionRunner.get_all_results`.
            patterns: From
                :meth:`~oraculus_di_auditor.multi_jurisdiction.pattern_detector.CrossJurisdictionPatternDetector.detect_all_patterns`.
        """
        self._results = runner_results
        self._patterns = patterns
        self._involvement = _pattern_involvement_counts(patterns)

    # ------------------------------------------------------------------
    # generate_json_report
    # ------------------------------------------------------------------

    def generate_json_report(self) -> dict[str, Any]:
        """Generate a machine-readable comparative report.

        Returns a dict with keys: ``report_type``, ``generated_at``,
        ``jurisdictions``, ``comparison_matrix``, ``cross_jurisdiction_patterns``,
        ``risk_ranking``, ``recommendations``.
        """
        # Jurisdictions summary
        jurisdictions: dict[str, Any] = {}
        for jid, jdata in self._results.items():
            summary = jdata.get("anomaly_summary", {})
            by_sev = summary.get("by_severity", {})
            jurisdictions[jid] = {
                "name": jdata.get("jurisdiction_name", jid),
                "document_count": jdata.get("document_count", 0),
                "anomaly_count": summary.get("total", 0),
                "top_severity": _top_severity(by_sev),
            }

        # Comparison matrix: detector → {jid: count}
        detectors = _all_detectors(self._results)
        comparison_matrix: dict[str, dict[str, int]] = {}
        for det in detectors:
            comparison_matrix[det] = {}
            for jid, jdata in self._results.items():
                by_det = jdata.get("anomaly_summary", {}).get("by_detector", {})
                comparison_matrix[det][jid] = by_det.get(det, 0)

        # Risk ranking
        risk_ranking = self._build_risk_ranking()

        # Recommendations
        recommendations = _build_recommendations(self._patterns, self._results)

        return {
            "report_type": "multi_jurisdiction_comparison",
            "generated_at": datetime.now(UTC).isoformat(),
            "jurisdictions": jurisdictions,
            "comparison_matrix": comparison_matrix,
            "cross_jurisdiction_patterns": (
                self._patterns.get("vendor_playbook_patterns", [])
                + self._patterns.get("procurement_parallels", [])
                + self._patterns.get("regional_governance_gaps", [])
            ),
            "risk_ranking": risk_ranking,
            "recommendations": recommendations,
        }

    def _build_risk_ranking(self) -> list[dict[str, Any]]:
        """Return jurisdictions sorted by risk score descending."""
        ranking: list[dict[str, Any]] = []
        for jid, jdata in self._results.items():
            summary = jdata.get("anomaly_summary", {})
            by_sev = summary.get("by_severity", {})
            involvement = self._involvement.get(jid, 0)
            score = _risk_score(by_sev, involvement)
            ranking.append(
                {
                    "jurisdiction_id": jid,
                    "name": jdata.get("jurisdiction_name", jid),
                    "risk_score": score,
                    "anomaly_count": summary.get("total", 0),
                    "top_findings": _top_findings(jdata),
                }
            )
        ranking.sort(key=lambda r: (-r["risk_score"], r["jurisdiction_id"]))
        return ranking

    # ------------------------------------------------------------------
    # generate_markdown_report
    # ------------------------------------------------------------------

    def generate_markdown_report(self) -> str:
        """Generate a human-readable comparative report in Markdown."""
        json_report = self.generate_json_report()
        lines: list[str] = []

        ts = json_report["generated_at"]
        jcount = len(self._results)
        total_anomalies = sum(
            v.get("anomaly_summary", {}).get("total", 0) for v in self._results.values()
        )
        pcount = self._patterns.get("patterns_detected", 0)

        # ------------------------------------------------------------------
        # 1. Executive Summary
        # ------------------------------------------------------------------
        lines.append("# Multi-Jurisdiction Comparative Audit Report")
        lines.append("")
        lines.append(f"**Generated:** {ts}")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(f"- **Jurisdictions analyzed:** {jcount}")
        lines.append(f"- **Total anomalies detected:** {total_anomalies}")
        lines.append(f"- **Cross-jurisdiction patterns found:** {pcount}")
        most_common = self._patterns.get("summary", {}).get(
            "most_common_pattern", "none"
        )
        lines.append(f"- **Most common pattern type:** {most_common}")
        high_risk = self._patterns.get("summary", {}).get(
            "highest_risk_jurisdictions", []
        )
        if high_risk:
            lines.append(f"- **Highest-risk jurisdiction(s):** {', '.join(high_risk)}")
        lines.append("")

        # ------------------------------------------------------------------
        # 2. Jurisdiction Comparison Table
        # ------------------------------------------------------------------
        lines.append("## Jurisdiction Comparison Table")
        lines.append("")
        lines.append(
            "Anomaly counts per detector (rows) for each jurisdiction (columns)."
        )
        lines.append("")

        jids = sorted(self._results.keys())
        detectors = _all_detectors(self._results)
        matrix = json_report["comparison_matrix"]

        if jids and detectors:
            # Header row
            header = "| Detector | " + " | ".join(jids) + " |"
            sep = "| --- |" + " --- |" * len(jids)
            lines.append(header)
            lines.append(sep)
            for det in detectors:
                row_counts = [str(matrix.get(det, {}).get(jid, 0)) for jid in jids]
                lines.append(f"| {det} | " + " | ".join(row_counts) + " |")
        else:
            lines.append("_No data available._")
        lines.append("")

        # ------------------------------------------------------------------
        # 3. Cross-Jurisdiction Patterns
        # ------------------------------------------------------------------
        lines.append("## Cross-Jurisdiction Patterns")
        lines.append("")

        all_patterns = (
            self._patterns.get("vendor_playbook_patterns", [])
            + self._patterns.get("procurement_parallels", [])
            + self._patterns.get("regional_governance_gaps", [])
        )
        if all_patterns:
            for p in all_patterns:
                pid = p.get("pattern_id", "unknown")
                ptype = p.get("pattern_type", "")
                desc = p.get("description", "")
                jids_p = p.get("jurisdictions_affected") or p.get("jurisdictions", [])
                lines.append(f"### {pid}")
                lines.append("")
                lines.append(f"**Type:** {ptype}")
                lines.append("")
                lines.append(f"**Description:** {desc}")
                lines.append("")
                lines.append(f"**Jurisdictions affected:** {', '.join(sorted(jids_p))}")
                conf = p.get("confidence")
                if conf is not None:
                    lines.append(f"**Confidence:** {conf:.2f}")
                lines.append("")
        else:
            lines.append("_No cross-jurisdiction patterns detected._")
            lines.append("")

        # ------------------------------------------------------------------
        # 4. Risk Ranking
        # ------------------------------------------------------------------
        lines.append("## Risk Ranking")
        lines.append("")
        lines.append(
            "Jurisdictions ranked by risk score "
            "(critical×5 + high×3 + medium×1 + pattern involvement×2)."
        )
        lines.append("")
        lines.append("| Rank | Jurisdiction | Risk Score | Anomalies | Top Finding |")
        lines.append("| --- | --- | --- | --- | --- |")
        for rank, entry in enumerate(json_report["risk_ranking"], start=1):
            top = entry["top_findings"][0] if entry["top_findings"] else "—"
            # Truncate long findings for table readability
            if len(top) > 80:
                top = top[:77] + "..."
            lines.append(
                f"| {rank} | {entry['name']} "
                f"| {entry['risk_score']:.1f} "
                f"| {entry['anomaly_count']} "
                f"| {top} |"
            )
        lines.append("")

        # ------------------------------------------------------------------
        # 5. Recommendations
        # ------------------------------------------------------------------
        lines.append("## Recommendations")
        lines.append("")
        for rec in json_report["recommendations"]:
            lines.append(f"- {rec}")
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # generate_timeline_comparison
    # ------------------------------------------------------------------

    def generate_timeline_comparison(self) -> dict[str, Any]:
        """Generate timeline data comparing when similar contracts/actions
        occurred across jurisdictions.

        Returns:
            ::

                {
                    "timeline_events": [
                        {"jurisdiction", "date", "event_type", "description"}
                    ],
                    "parallel_timelines": [
                        {"pattern", "jurisdictions", "date_ranges"}
                    ]
                }
        """
        events = _extract_dates_from_results(self._results)

        # Build parallel timelines: for each cross-jurisdiction pattern,
        # find the date ranges of contributing jurisdictions.
        parallel_timelines: list[dict[str, Any]] = []
        all_patterns = self._patterns.get(
            "vendor_playbook_patterns", []
        ) + self._patterns.get("regional_governance_gaps", [])
        # Map jurisdiction → event dates for quick lookup
        jid_dates: dict[str, list[str]] = {}
        for event in events:
            jid = event["jurisdiction"]
            jid_dates.setdefault(jid, []).append(event["date"])

        for p in all_patterns:
            jids_p = p.get("jurisdictions_affected", [])
            date_ranges: dict[str, dict[str, str]] = {}
            for jid in jids_p:
                dates = sorted(jid_dates.get(jid, []))
                if dates:
                    date_ranges[jid] = {"earliest": dates[0], "latest": dates[-1]}
            if date_ranges:
                parallel_timelines.append(
                    {
                        "pattern": p.get("pattern_id", "unknown"),
                        "jurisdictions": sorted(jids_p),
                        "date_ranges": date_ranges,
                    }
                )

        return {
            "timeline_events": events,
            "parallel_timelines": parallel_timelines,
        }
