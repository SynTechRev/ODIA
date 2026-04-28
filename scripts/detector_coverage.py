"""Detector coverage diagnostic.

Exercises every registered detector against a stress corpus that
deliberately triggers every known finding ID, then reports:

  • detector module
  • finding ID
  • severity
  • whether the finding has a populated `details` dict
  • whether a plain-language template exists for it
  • statute citation (if extractable from the finding details)

Run with::

    python scripts/detector_coverage.py
    python scripts/detector_coverage.py --json     # machine-readable output

This is the v2.9.3 Track E.1 self-describing registry — the answer to
"what does ODIA actually look for?" — without forcing a refactor of
every detector to expose a static FINDING_DEFINITIONS list (which the
handoff originally proposed but would touch 9 modules unnecessarily
when introspection by emission-replay gives the same answer).

Coverage is empirical: a finding ID is "registered" if at least one
canned input triggers it. The stress corpus lives below as
``STRESS_DOCS``. Adding detectors is a matter of adding a doc that
trips the new finding ID — the script discovers it automatically.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

# Stress corpus — each dict triggers one or more finding IDs across
# the detector pipeline. Built empirically from the Run-12 evidence
# packet so coverage stays grounded in real audit shapes.
STRESS_DOCS: list[dict[str, Any]] = [
    # Doc 1 — surveillance + JAG + COPS combo, missing every governance gate.
    {
        "document_id": "stress-1",
        "title": "Body-worn camera procurement using JAG funds",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The Department shall acquire body-worn cameras from Axon "
                    "Enterprise (Evidence.com, OSP7) using JAG grant funds "
                    "under the Edward Byrne Memorial program. COPS hiring "
                    "grant assists with personnel. ALPR cameras supplied by "
                    "Flock Safety. Sole-source procurement justified by "
                    "proprietary vendor status. Contract automatically renews."
                ),
            }
        ],
    },
    # Doc 2 — fiscal amount without appropriation reference.
    {
        "document_id": "stress-2",
        "title": "Authorization for $1,750,000 expenditure",
        "sections": [
            {
                "section_id": "1",
                "content": "The City shall authorize $1,750,000 for equipment.",
            }
        ],
    },
    # Doc 3 — administrative gaps: blank fields + missing final action.
    {
        "document_id": "stress-3",
        "title": "Resolution approved by council",
        "sections": [{"section_id": "1", "content": "Resolution was approved."}],
    },
    # Doc 4 — retroactive authorization (admin) + capability without approval.
    {
        "document_id": "stress-4",
        "title": "Retroactive authorization",
        "final_action": "Approved",
        "status": "Closed",
        "vote_result": "5-0",
        "meeting_date": "2024-09-23",
        "agenda_number": "24-0987",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "This contract is retroactive to January 1. The "
                    "Department deployed Flock Safety ALPR cameras without "
                    "prior council approval."
                ),
            }
        ],
    },
    # Doc 5 — drone/UAS without AB 481 (military equipment annual report).
    {
        "document_id": "stress-5",
        "title": "Unmanned Aerial System program",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "The Department operates a drone program with unmanned "
                    "aerial system equipment. No AB 481 annual report has "
                    "been published."
                ),
            }
        ],
    },
    # Doc 6 — facial recognition + AI report writing without SB 524.
    {
        "document_id": "stress-6",
        "title": "AI-driven analytics deployment",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "Facial recognition system deployed. Draft One AI report "
                    "writing automated. No SB 524 transparency disclosure."
                ),
            }
        ],
    },
    # Doc 7 — criminal-intelligence reference without 28 CFR Part 23.
    {
        "document_id": "stress-7",
        "title": "Criminal intelligence database",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "Department maintains a gang intelligence database with "
                    "criminal intelligence files. No 28 CFR Part 23 citation."
                ),
            }
        ],
    },
    # Doc 8 — scope expansion / amendment without baseline.
    {
        "document_id": "stress-8",
        "title": "Amendment to camera contract",
        "sections": [
            {
                "section_id": "1",
                "content": (
                    "This amendment expands the deployment by 50 cameras. "
                    "The original baseline contract is referenced but not "
                    "attached."
                ),
            }
        ],
    },
]


def _iter_findings() -> list[dict[str, Any]]:
    """Run analyze_document over the stress corpus and collect every finding."""
    from oraculus_di_auditor.analysis import analyze_document

    out: list[dict[str, Any]] = []
    for doc in STRESS_DOCS:
        result = analyze_document(doc)
        for f in result.get("anomalies", []):
            out.append(f)
    return out


def _summarise(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reduce raw findings to one row per finding-ID."""
    seen: dict[str, dict[str, Any]] = {}
    for f in findings:
        fid = f.get("id")
        if not fid:
            continue
        if fid in seen:
            seen[fid]["emit_count"] += 1
            continue
        seen[fid] = {
            "finding_id": fid,
            "detector": f.get("layer", "?"),
            "severity": f.get("severity", "?"),
            "has_details": bool(f.get("details")),
            "statute": (f.get("details") or {}).get("statute"),
            "issue": f.get("issue", ""),
            "emit_count": 1,
        }

    # Try to resolve plain-language template coverage too. plain_language
    # keys finding IDs by their post-prefix tail (e.g. the
    # `surveillance:bwc-without-cjis-addendum` finding's template lives
    # under `bwc-without-cjis-addendum` inside the `surveillance` bucket).
    try:
        from oraculus_di_auditor.reporting.plain_language import TRANSLATIONS

        templates_flat: set[str] = set()
        for layer, by_id in TRANSLATIONS.items():
            for fid in by_id:
                templates_flat.add(f"{layer}:{fid}")
                templates_flat.add(fid)

        for row in seen.values():
            tail = row["finding_id"].split(":", 1)
            short = tail[1] if len(tail) == 2 else tail[0]
            row["plain_template"] = (
                row["finding_id"] in templates_flat or short in templates_flat
            )
    except Exception:
        for row in seen.values():
            row["plain_template"] = None

    rows = sorted(
        seen.values(),
        key=lambda r: (r["detector"], r["finding_id"]),
    )
    return rows


def _print_human(rows: list[dict[str, Any]]) -> None:
    detectors_seen: set[str] = set()
    print(
        f"{'detector':<22}  {'finding_id':<55}  {'sev':<8}  "
        f"{'details':<8}  {'plain':<6}  statute"
    )
    print("-" * 130)
    for r in rows:
        detectors_seen.add(r["detector"])
        details_flag = "yes" if r["has_details"] else "EMPTY"
        plain_flag = (
            "yes" if r.get("plain_template") is True
            else "no" if r.get("plain_template") is False
            else "?"
        )
        statute = r.get("statute") or "—"
        print(
            f"{r['detector']:<22}  {r['finding_id']:<55}  {r['severity']:<8}  "
            f"{details_flag:<8}  {plain_flag:<6}  {statute}"
        )
    print()
    print(f"Detector modules surfaced: {len(detectors_seen)}")
    print(f"Distinct finding IDs:      {len(rows)}")
    empty_evidence = [r for r in rows if not r["has_details"]]
    if empty_evidence:
        print()
        print(f"WARNING: {len(empty_evidence)} finding ID(s) with empty details:")
        for r in empty_evidence:
            print(f"  - {r['finding_id']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    rows = _summarise(_iter_findings())
    if args.json:
        print(json.dumps(rows, indent=2, default=str))
    else:
        _print_human(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
