"""Pretty-print a R.A.I.A. trace from raia_day04_traces.jsonl for Mars review.

Usage:
    python -I scripts/pretty_print_trace.py data/eval/raia_day04_traces.jsonl
    python -I scripts/pretty_print_trace.py data/eval/raia_day04_traces.jsonl --query 2
    python -I scripts/pretty_print_trace.py data/eval/raia_day04_traces.jsonl --category severity_critical
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _divider(label: str = "", width: int = 72) -> str:
    if label:
        pad = width - len(label) - 2
        left = pad // 2
        right = pad - left
        return f"{'=' * left} {label} {'=' * right}"
    return "=" * width


def _fmt_node(entry: dict) -> str:
    node = entry.get("node", "?")
    it = entry.get("iteration", "")
    it_tag = f" [iter {it}]" if it != "" else ""

    lines = [_divider(f"NODE: {node.upper()}{it_tag}")]

    if node == "analyze":
        sqs = entry.get("sub_questions", [])
        angle = entry.get("angle", "")
        lines.append(f"  analytical_angle : {angle}")
        lines.append(f"  sub_questions ({len(sqs)}):")
        for i, sq in enumerate(sqs, 1):
            lines.append(f"    {i}. {sq}")

    elif node == "cross_reference":
        lines.append(f"  passages_retrieved : {entry.get('passages_retrieved', '?')}")
        lines.append(f"  unique_docs        : {entry.get('unique_docs', '?')}")

    elif node == "deepen":
        lines.append(f"  findings_length : {entry.get('findings_length', '?')} chars")
        lines.append(f"  confidence      : {entry.get('confidence', '?'):.3f}")

    elif node == "verify":
        lines.append(f"  citations_found : {entry.get('citations_found', '?')}")
        lines.append(f"  citations_valid : {entry.get('citations_valid', '?')}")
        lines.append(f"  confidence_met  : {entry.get('confidence_met', '?')}")
        notes = entry.get("verification_notes", "")
        if notes:
            lines.append(f"  notes           : {notes}")

    elif node == "finalize":
        lines.append(f"  halt_reason     : {entry.get('halt_reason', '?')}")
        lines.append(f"  final_iteration : {entry.get('final_iteration', '?')}")
        lines.append(f"  final_confidence: {entry.get('final_confidence', '?'):.3f}")

    return "\n".join(lines)


def pretty_print_record(record: dict, show_answer: bool = True) -> None:
    print(_divider())
    print(f"QUERY      : {record['query']}")
    print(f"CATEGORY   : {record['category']}")
    print(f"QUERY ID   : {record.get('query_id', '?')}")
    print(f"HALT       : {record['halt_reason']}  (iterations={record['iterations']})")
    print(f"CONFIDENCE : {record['final_confidence']:.3f}")
    print(f"LATENCY    : {record.get('latency_sec', '?')}s")
    validity = record.get("citation_validity", {})
    if validity:
        valid = sum(1 for v in validity.values() if v)
        print(f"CITATIONS  : {valid}/{len(validity)} valid")
    else:
        print("CITATIONS  : none extracted")
    print()

    for entry in record.get("trace", []):
        print(_fmt_node(entry))
        print()

    if show_answer:
        print(_divider("FINAL ANSWER"))
        answer = record.get("final_answer", "")
        for line in answer.splitlines():
            print(f"  {line}")
        print(_divider())

    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pretty-print R.A.I.A. traces for Mars review"
    )
    parser.add_argument("traces_file", type=Path, help="Path to .jsonl traces file")
    parser.add_argument(
        "--query",
        type=int,
        default=None,
        help="Print only query #N (1-indexed)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Print only traces matching this category",
    )
    parser.add_argument(
        "--no-answer",
        action="store_true",
        help="Suppress final_answer block",
    )
    args = parser.parse_args()

    if not args.traces_file.exists():
        print(f"ERROR: {args.traces_file} not found.", file=sys.stderr)
        sys.exit(1)

    records = []
    with open(args.traces_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        print("No traces found in file.", file=sys.stderr)
        sys.exit(1)

    selected = records
    if args.query is not None:
        idx = args.query - 1
        if idx < 0 or idx >= len(records):
            print(
                f"ERROR: --query {args.query} out of range (1..{len(records)})",
                file=sys.stderr,
            )
            sys.exit(1)
        selected = [records[idx]]
    elif args.category:
        selected = [r for r in records if r.get("category") == args.category]
        if not selected:
            print(
                f"ERROR: no traces with category={args.category!r}",
                file=sys.stderr,
            )
            sys.exit(1)

    print(f"Showing {len(selected)} of {len(records)} traces from {args.traces_file}")
    print()
    for i, record in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}]")
        pretty_print_record(record, show_answer=not args.no_answer)


if __name__ == "__main__":
    main()
