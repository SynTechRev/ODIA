"""Procurement Timeline Detector.

Detects contract execution dates that precede council authorization dates,
indicating a contract was executed before the required governing-body approval
was obtained. This is a structural integrity check — it does not assess the
substance of the underlying authorization.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _parse_date(value: Any) -> date | None:
    """Parse an ISO-format date string (YYYY-MM-DD) into a date object.

    Returns None on any parse failure so the caller can skip gracefully.
    """
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def detect_procurement_timeline_anomalies(
    documents: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Identify contracts executed before council authorization.

    Iterates over each document and compares ``execution_date`` against
    ``authorization_date``.  A finding is emitted whenever execution strictly
    precedes authorization, indicating the contract was signed before the
    required governing-body approval was obtained.

    Args:
        documents: List of document dicts.  Each document may contain:
            - ``execution_date``: ISO date string (YYYY-MM-DD) of contract
              execution / signing.
            - ``authorization_date``: ISO date string (YYYY-MM-DD) of council
              or governing-body authorization.
            - ``document_id`` (optional): stable identifier used in findings.
            - ``title`` (optional): human-readable label used in findings.

    Returns:
        List of anomaly dicts, one per violation found.  Each dict has the
        shape ``{id, issue, severity, layer, details}`` consistent with all
        other detectors in this package.  Returns an empty list if no
        violations are found or if the input is not a list.
    """
    anomalies: list[dict[str, Any]] = []

    if not isinstance(documents, list):
        return anomalies

    for idx, doc in enumerate(documents):
        if not isinstance(doc, dict):
            continue

        doc_id = doc.get("document_id") or doc.get("id") or f"doc[{idx}]"
        title = doc.get("title", "")

        exec_raw = doc.get("execution_date")
        auth_raw = doc.get("authorization_date")

        exec_date = _parse_date(exec_raw)
        auth_date = _parse_date(auth_raw)

        # Skip documents with missing or unparseable dates — no data, no finding.
        if exec_date is None or auth_date is None:
            continue

        if exec_date < auth_date:
            delta_days = (auth_date - exec_date).days
            anomalies.append(
                {
                    "id": "procurement:execution-precedes-authorization",
                    "issue": (
                        f"Contract executed {delta_days} day(s) before "
                        "council authorization"
                    ),
                    "severity": "high",
                    "layer": "procurement",
                    "details": {
                        "document_id": doc_id,
                        "title": title,
                        "execution_date": exec_raw,
                        "authorization_date": auth_raw,
                        "days_early": delta_days,
                    },
                }
            )

    return anomalies
