"""Export ODIA DB findings to instruction-tuning format for Oraculus model training.

Reads all Anomaly + Document rows from oraculus_audit.db and writes a JSONL
file of (instruction, input, output) triples suitable for supervised
fine-tuning.

Three export modes:
  --mode findings    (default) — one sample per finding: "identify legal issues
                      in this excerpt" → structured finding description
  --mode explanation — one sample per finding: "explain this finding in plain
                      language" → community-oriented plain-language explanation
  --mode memorandum  — one sample per document (all findings): "write a legal
                      memorandum" → full memorandum text

Run from repo root:
    python scripts/export_training_data.py
    python scripts/export_training_data.py --mode explanation --out data/training_explanation.jsonl
    python scripts/export_training_data.py --layer l3_exemption_misapplication
    python scripts/export_training_data.py --severity high --limit 500

Output file: data/training_data.jsonl (or --out path)
Schema per line:
    {
        "id":          "<document_id>:<anomaly_id>",
        "instruction": "<task description>",
        "input":       "<document text excerpt, up to --max-chars chars>",
        "output":      "<expected model output>",
        "metadata": {
            "document_id":  str,
            "anomaly_id":   str,
            "severity":     str,
            "layer":        str,
            "mode":         str,
        }
    }
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from oraculus_di_auditor.db.models import Analysis, Anomaly, Document  # noqa: E402
from oraculus_di_auditor.db.session import get_db, init_db  # noqa: E402

# ---------------------------------------------------------------------------
# Instructions
# ---------------------------------------------------------------------------

_INSTR_FINDINGS = (
    "You are a legal document auditor. Analyze the following government agency "
    "document excerpt and identify any legal compliance issues, citing the "
    "specific statute, regulation, or case law that applies. Format your "
    "response as a structured finding."
)

_INSTR_EXPLANATION = (
    "You are a plain-language legal educator. Read the following government "
    "agency document excerpt and explain any legal compliance issues in simple, "
    "jargon-free language that a member of the public can understand without "
    "a law degree."
)

_INSTR_MEMORANDUM = (
    "You are a legal analyst. Based on the following government agency document, "
    "write a formal legal memorandum summarizing all identified compliance "
    "issues, citing applicable statutes and case law, grouped by severity."
)

# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------


def _finding_output(
    anomaly_id: str, issue: str, severity: str, layer: str, details: dict
) -> str:
    """Format a single finding as structured output text."""
    lines = [
        f"FINDING: {issue}",
        f"SEVERITY: {severity.upper()}",
        f"DETECTOR: {layer}",
        f"ID: {anomaly_id}",
    ]
    if details.get("statute"):
        lines.append(f"STATUTE: {details['statute']}")
    if details.get("regulation"):
        lines.append(f"REGULATION: {details['regulation']}")
    if details.get("framework"):
        lines.append(f"FRAMEWORK: {details['framework']}")
    if details.get("detail") or details.get("relevance"):
        detail_text = details.get("detail") or details.get("relevance", "")
        wrapped = textwrap.fill(detail_text, width=80)
        lines.append(f"EXPLANATION: {wrapped}")
    return "\n".join(lines)


def _explanation_output(issue: str, severity: str, details: dict) -> str:
    """Format a plain-language explanation of a finding."""
    # Map severity to urgency phrase
    urgency = {
        "high": "This is a serious concern that may require immediate attention.",
        "medium": "This issue is worth investigating further.",
        "low": "This is informational background about laws that apply to this document.",
    }.get(severity, "")

    detail_text = details.get("detail") or details.get("relevance") or ""
    parts = [urgency, issue]
    if detail_text:
        parts.append(f"What this means: {detail_text}")
    return " ".join(p for p in parts if p)


def _memorandum_output(
    doc_title: str,
    agency: str,
    findings: list[tuple[Anomaly, dict]],
) -> str:
    """Format all findings for a document as a memorandum output."""
    total = len(findings)
    high = sum(1 for a, _ in findings if a.severity == "high")
    medium = sum(1 for a, _ in findings if a.severity == "medium")
    low = sum(1 for a, _ in findings if a.severity == "low")

    lines = [
        "MEMORANDUM",
        f"RE: Legal Audit Findings: {doc_title} — {agency}",
        "",
        f"OVERVIEW: {total} finding(s) — {high} high, {medium} medium, {low} low severity.",
        "",
        "FINDINGS:",
    ]
    for i, (anomaly, details) in enumerate(findings, 1):
        lines.append(f"\n{i}. [{anomaly.severity.upper()}] {anomaly.issue}")
        if details.get("statute"):
            lines.append(f"   Statute: {details['statute']}")
        if details.get("detail"):
            wrapped = textwrap.fill(
                details["detail"],
                width=76,
                initial_indent="   ",
                subsequent_indent="   ",
            )
            lines.append(wrapped)

    lines.append("\nCONCLUSION:")
    if high > 0:
        lines.append(
            f"The {high} high-severity finding(s) above require immediate agency response "
            "and review by legal counsel."
        )
    else:
        lines.append(
            "The identified findings represent areas for policy review. No immediate "
            "litigation risk identified at this time."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Export logic
# ---------------------------------------------------------------------------


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + " [...]"


def export(
    *,
    mode: str,
    out_path: Path,
    layer_filter: str | None,
    severity_filter: str | None,
    limit: int | None,
    max_chars: int,
) -> int:
    """Run the export. Returns count of records written."""
    init_db()
    db = next(get_db())

    written = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as fh:
        if mode == "memorandum":
            written = _export_memorandum(
                db, fh, layer_filter, severity_filter, limit, max_chars
            )
        else:
            written = _export_per_finding(
                db, fh, mode, layer_filter, severity_filter, limit, max_chars
            )

    return written


def _export_per_finding(db, fh, mode, layer_filter, severity_filter, limit, max_chars):
    written = 0
    instruction = _INSTR_FINDINGS if mode == "findings" else _INSTR_EXPLANATION

    query = (
        db.query(Anomaly, Document)
        .join(Analysis, Anomaly.analysis_id == Analysis.id)
        .join(Document, Analysis.document_id == Document.document_id)
    )
    if layer_filter:
        query = query.filter(Anomaly.layer == layer_filter)
    if severity_filter:
        query = query.filter(Anomaly.severity == severity_filter)
    if limit:
        query = query.limit(limit)

    for anomaly, document in query:
        text = document.text or document.raw_text or ""
        if not text.strip():
            continue

        details: dict = {}
        if anomaly.details_json:
            try:
                details = json.loads(anomaly.details_json)
            except (json.JSONDecodeError, TypeError):
                pass

        if mode == "findings":
            output = _finding_output(
                anomaly.anomaly_id,
                anomaly.issue,
                anomaly.severity,
                anomaly.layer,
                details,
            )
        else:
            output = _explanation_output(anomaly.issue, anomaly.severity, details)

        record = {
            "id": f"{document.document_id}:{anomaly.anomaly_id}",
            "instruction": instruction,
            "input": _truncate(text, max_chars),
            "output": output,
            "metadata": {
                "document_id": document.document_id,
                "anomaly_id": anomaly.anomaly_id,
                "severity": anomaly.severity,
                "layer": anomaly.layer,
                "mode": mode,
            },
        }
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        written += 1

    return written


def _export_memorandum(db, fh, layer_filter, severity_filter, limit, max_chars):
    written = 0

    # Load documents
    doc_query = db.query(Document)
    if limit:
        doc_query = doc_query.limit(limit)

    for document in doc_query:
        text = document.text or document.raw_text or ""
        if not text.strip():
            continue

        # Get all findings for this document's analyses
        sub = (
            db.query(Anomaly)
            .join(Analysis, Anomaly.analysis_id == Analysis.id)
            .filter(Analysis.document_id == document.document_id)
        )
        if layer_filter:
            sub = sub.filter(Anomaly.layer == layer_filter)
        if severity_filter:
            sub = sub.filter(Anomaly.severity == severity_filter)

        anomalies = sub.all()
        if not anomalies:
            continue

        findings_with_details: list[tuple[Anomaly, dict]] = []
        for a in anomalies:
            details: dict = {}
            if a.details_json:
                try:
                    details = json.loads(a.details_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            findings_with_details.append((a, details))

        agency = getattr(document, "jurisdiction", "") or ""
        title = getattr(document, "title", "") or document.document_id

        output = _memorandum_output(title, agency, findings_with_details)
        record = {
            "id": f"{document.document_id}:memorandum",
            "instruction": _INSTR_MEMORANDUM,
            "input": _truncate(text, max_chars),
            "output": output,
            "metadata": {
                "document_id": document.document_id,
                "anomaly_id": "memorandum",
                "severity": "mixed",
                "layer": "all",
                "mode": "memorandum",
            },
        }
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        written += 1

    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Export ODIA DB findings to instruction-tuning JSONL for Oraculus training."
    )
    p.add_argument(
        "--mode",
        choices=["findings", "explanation", "memorandum"],
        default="findings",
        help="Export mode (default: findings)",
    )
    p.add_argument(
        "--out",
        default="data/training_data.jsonl",
        help="Output JSONL file path (default: data/training_data.jsonl)",
    )
    p.add_argument(
        "--layer",
        default=None,
        help="Filter by detector layer (e.g. l3_exemption_misapplication)",
    )
    p.add_argument(
        "--severity",
        choices=["low", "medium", "high"],
        default=None,
        help="Filter by severity level",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of records to export",
    )
    p.add_argument(
        "--max-chars",
        type=int,
        default=4000,
        dest="max_chars",
        help="Maximum document text chars per sample (default: 4000)",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    out_path = REPO_ROOT / args.out

    print(f"Exporting training data: mode={args.mode}, out={out_path}")
    if args.layer:
        print(f"  Layer filter: {args.layer}")
    if args.severity:
        print(f"  Severity filter: {args.severity}")
    if args.limit:
        print(f"  Limit: {args.limit}")

    count = export(
        mode=args.mode,
        out_path=out_path,
        layer_filter=args.layer,
        severity_filter=args.severity,
        limit=args.limit,
        max_chars=args.max_chars,
    )

    print(f"Wrote {count} training samples to {out_path}")
