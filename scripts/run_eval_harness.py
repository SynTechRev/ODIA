#!/usr/bin/env python3
"""Day 10: Run RAIA evaluation harness and emit 7-metric scorecard.

Usage:
  python -I scripts/run_eval_harness.py
  python -I scripts/run_eval_harness.py --traces data/eval/raia_day04_traces.jsonl
  python -I scripts/run_eval_harness.py --judge ollama
  python -I scripts/run_eval_harness.py --out data/eval/scorecard_day10.json
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from oraculus_di_auditor.eval.harness import EvalHarness, HeuristicJudge, OllamaJudge


def main() -> int:
    parser = argparse.ArgumentParser(description="RAIA evaluation harness (Day 10)")
    parser.add_argument(
        "--traces",
        type=Path,
        default=Path("data/eval/raia_day04_traces.jsonl"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/eval/scorecard_day10.json"),
    )
    parser.add_argument(
        "--judge",
        choices=["heuristic", "ollama"],
        default="heuristic",
    )
    parser.add_argument(
        "--latency-sla",
        type=float,
        default=300.0,
        help="P50 latency SLA in seconds (informational, not a gate)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
    )
    args = parser.parse_args()

    if not args.traces.exists():
        print(f"ERROR: traces file not found: {args.traces}", file=sys.stderr)
        return 1

    judge = OllamaJudge() if args.judge == "ollama" else HeuristicJudge()
    harness = EvalHarness(
        judge=judge,
        latency_sla=args.latency_sla,
        max_iterations=args.max_iterations,
    )

    print(f"Running evaluation on: {args.traces}")
    print(f"Judge: {type(judge).__name__}")
    print()

    scorecard = harness.run_from_traces(args.traces)
    harness.print_scorecard(scorecard)
    harness.save_scorecard(scorecard, args.out)
    print(f"\nScorecard saved: {args.out}")

    return 0 if scorecard.gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
