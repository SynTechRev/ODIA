"""Legal R.A.I.A. Vector 3 — Temporal Re-Evaluation Engine.

Re-evaluates prior ODIA legal findings against the current state of the law.
Designed to run on a recurring cadence (daily/weekly/monthly) to surface:

  NEW        — findings that were not present in the prior run but are now triggered
  RESOLVED   — findings from the prior run that no longer trigger
  UPGRADED   — findings whose severity increased (low → medium, medium → high)
  DOWNGRADED — findings whose severity decreased (high → medium, medium → low)
  UNCHANGED  — findings still present with the same severity

Additionally performs a case-law currency sweep:
  STALE_LAW  — a case cited in findings has been deprecated, limited, or overruled
               since the prior run date

Usage::

    from odia_legal.vector3 import LegalVector3, ReEvaluationResult

    evaluator = LegalVector3()
    result = evaluator.reeval(
        doc={"text": "..."},
        prior_findings=prior_run_findings,
        prior_run_date="2024-01-01",
    )
    print(result.summary())
    print(result.changed_count)
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from odia_legal.treatment.case_currency import check_document_currency

# ---------------------------------------------------------------------------
# Detector registry — all L-n modules that expose detect(doc) -> list[dict]
# ---------------------------------------------------------------------------

_DETECTOR_MODULES = [
    "odia_legal.detectors.l1_statutory_applicability",
    "odia_legal.detectors.l2_procedural_compliance",
    "odia_legal.detectors.l3_exemption_misapplication",
    "odia_legal.detectors.l5_federal_grant_compliance",
    "odia_legal.detectors.l6_constitutional_implication",
    "odia_legal.detectors.l9_recodification",
    "odia_legal.detectors.l10_balancing_test",
]

_SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2}


def _load_detectors() -> list[Any]:
    """Import and return the detect() callables for all registered detectors."""
    detectors = []
    for mod_path in _DETECTOR_MODULES:
        try:
            mod = importlib.import_module(mod_path)
            detectors.append(mod.detect)
        except (ImportError, AttributeError):
            pass
    return detectors


def _run_all_detectors(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Run every registered detector on *doc* and return merged findings."""
    findings: list[dict[str, Any]] = []
    for detect_fn in _load_detectors():
        try:
            findings.extend(detect_fn(doc))
        except Exception:  # noqa: BLE001  # one bad detector must not abort
            pass
    return findings


def _findings_index(findings: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a dict keyed by finding ID."""
    return {f["id"]: f for f in findings if "id" in f}


# ---------------------------------------------------------------------------
# Currency change helper
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurrencyChange:
    """A case-law treatment change detected since the prior run."""

    case_name: str
    prior_status: str
    current_status: str
    notes: str


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ReEvaluationResult:
    """Outcome of a Vector 3 temporal re-evaluation run."""

    doc_id: str
    run_date: str
    prior_run_date: str

    new_findings: list[dict[str, Any]] = field(default_factory=list)
    resolved_findings: list[dict[str, Any]] = field(default_factory=list)
    upgraded_findings: list[dict[str, Any]] = field(default_factory=list)
    downgraded_findings: list[dict[str, Any]] = field(default_factory=list)
    unchanged_findings: list[dict[str, Any]] = field(default_factory=list)
    currency_changes: list[CurrencyChange] = field(default_factory=list)

    @property
    def changed_count(self) -> int:
        return (
            len(self.new_findings)
            + len(self.resolved_findings)
            + len(self.upgraded_findings)
            + len(self.downgraded_findings)
        )

    @property
    def current_findings(self) -> list[dict[str, Any]]:
        """All findings from the current run (new + upgraded + downgraded + unchanged)."""
        return (
            self.new_findings
            + self.upgraded_findings
            + self.downgraded_findings
            + self.unchanged_findings
        )

    def summary(self) -> str:
        lines = [
            f"Vector 3 Re-Evaluation: {self.doc_id}",
            f"  Prior run : {self.prior_run_date}",
            f"  This run  : {self.run_date}",
            f"  NEW       : {len(self.new_findings)}",
            f"  RESOLVED  : {len(self.resolved_findings)}",
            f"  UPGRADED  : {len(self.upgraded_findings)}",
            f"  DOWNGRADED: {len(self.downgraded_findings)}",
            f"  UNCHANGED : {len(self.unchanged_findings)}",
        ]
        if self.currency_changes:
            lines.append(
                f"  STALE LAW : {len(self.currency_changes)} case(s) changed treatment"
            )
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "run_date": self.run_date,
            "prior_run_date": self.prior_run_date,
            "new": [f["id"] for f in self.new_findings],
            "resolved": [f["id"] for f in self.resolved_findings],
            "upgraded": [f["id"] for f in self.upgraded_findings],
            "downgraded": [f["id"] for f in self.downgraded_findings],
            "unchanged": [f["id"] for f in self.unchanged_findings],
            "currency_changes": [
                {
                    "case_name": c.case_name,
                    "prior_status": c.prior_status,
                    "current_status": c.current_status,
                    "notes": c.notes,
                }
                for c in self.currency_changes
            ],
            "changed_count": self.changed_count,
        }


# ---------------------------------------------------------------------------
# Vector 3 engine
# ---------------------------------------------------------------------------


class LegalVector3:
    """Legal R.A.I.A. Vector 3 — temporal re-evaluation of prior findings.

    Compares a fresh detector run against a prior run to surface what
    changed. Also sweeps cited cases for treatment changes since the
    prior run date.
    """

    def reeval(
        self,
        doc: dict[str, Any],
        prior_findings: list[dict[str, Any]],
        *,
        prior_run_date: str,
        run_date: str | None = None,
        doc_id: str | None = None,
    ) -> ReEvaluationResult:
        """Re-evaluate a document against its prior findings.

        Args:
            doc:             The original document dict (must contain 'text').
            prior_findings:  Finding dicts from the previous run.
            prior_run_date:  ISO date string of the previous run.
            run_date:        ISO date of this run; defaults to today.
            doc_id:          Identifier for the document (for reporting).

        Returns:
            ReEvaluationResult with categorized deltas and currency changes.
        """
        if run_date is None:
            run_date = date.today().isoformat()
        if doc_id is None:
            doc_id = doc.get("document_id") or doc.get("id") or "unknown"

        current_findings = _run_all_detectors(doc)
        result = self._diff(prior_findings, current_findings)
        currency_changes = self._sweep_currency(doc, prior_run_date)

        return ReEvaluationResult(
            doc_id=doc_id,
            run_date=run_date,
            prior_run_date=prior_run_date,
            new_findings=result["new"],
            resolved_findings=result["resolved"],
            upgraded_findings=result["upgraded"],
            downgraded_findings=result["downgraded"],
            unchanged_findings=result["unchanged"],
            currency_changes=currency_changes,
        )

    # ------------------------------------------------------------------

    def _diff(
        self,
        prior: list[dict[str, Any]],
        current: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        prior_idx = _findings_index(prior)
        current_idx = _findings_index(current)

        new: list[dict[str, Any]] = []
        resolved: list[dict[str, Any]] = []
        upgraded: list[dict[str, Any]] = []
        downgraded: list[dict[str, Any]] = []
        unchanged: list[dict[str, Any]] = []

        # Findings only in current run
        for fid, finding in current_idx.items():
            if fid not in prior_idx:
                new.append(finding)
            else:
                prior_sev = _SEVERITY_RANK.get(prior_idx[fid].get("severity", "low"), 0)
                curr_sev = _SEVERITY_RANK.get(finding.get("severity", "low"), 0)
                if curr_sev > prior_sev:
                    upgraded.append(finding)
                elif curr_sev < prior_sev:
                    downgraded.append(finding)
                else:
                    unchanged.append(finding)

        # Findings only in prior run (no longer triggered)
        for fid, finding in prior_idx.items():
            if fid not in current_idx:
                resolved.append(finding)

        return {
            "new": new,
            "resolved": resolved,
            "upgraded": upgraded,
            "downgraded": downgraded,
            "unchanged": unchanged,
        }

    def _sweep_currency(
        self,
        doc: dict[str, Any],
        prior_run_date: str,
    ) -> list[CurrencyChange]:
        """Check for case-law treatment changes since prior_run_date."""
        try:
            prior_year = int(prior_run_date[:4])
        except (ValueError, TypeError):
            return []

        signals = check_document_currency(doc)
        changes: list[CurrencyChange] = []
        for signal in signals:
            # Flag if the treatment was assessed after the prior run date,
            # meaning there may be new information the prior run didn't have.
            if signal.as_of_year > prior_year and signal.status != "GOOD":
                changes.append(
                    CurrencyChange(
                        case_name=signal.case_name,
                        prior_status="GOOD",  # assumed good in prior run
                        current_status=signal.status,
                        notes=signal.notes or "",
                    )
                )
        return changes


# ---------------------------------------------------------------------------
# Convenience batch function
# ---------------------------------------------------------------------------


def cadenced_reeval(
    docs_and_prior: list[dict[str, Any]],
    *,
    prior_run_date: str,
    run_date: str | None = None,
) -> list[ReEvaluationResult]:
    """Batch re-evaluate multiple documents on a cadence.

    Each entry in *docs_and_prior* must have:
      'doc'             — the document dict
      'prior_findings'  — list of prior finding dicts
      'doc_id'          — (optional) document identifier

    Returns a list of ReEvaluationResult, one per document.
    """
    evaluator = LegalVector3()
    results: list[ReEvaluationResult] = []
    for entry in docs_and_prior:
        results.append(
            evaluator.reeval(
                doc=entry["doc"],
                prior_findings=entry.get("prior_findings", []),
                prior_run_date=prior_run_date,
                run_date=run_date,
                doc_id=entry.get("doc_id"),
            )
        )
    return results
