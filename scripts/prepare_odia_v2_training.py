"""prepare_odia_v2_training.py — Build the combined odia-v2 training JSONL.

Combines the three source files into a single shuffled JSONL in ChatML
messages format, ready for Unsloth fine-tuning:

  - data/training/odia_sft_reports_20261017_152705.jsonl       56,282 examples
  - data/training/odia_sft_explanations_20261017_152940.jsonl 271,221 examples
  - data/training/adversarial_dan_type8.jsonl                     214 examples
  Total: 327,717 examples

The adversarial file is Alpaca format (instruction/input/output).
This script converts it to messages format to match the others.

Output: data/training/odia_v2_combined_327717.jsonl

Usage:
    python scripts/prepare_odia_v2_training.py
    python scripts/prepare_odia_v2_training.py --verify
    python scripts/prepare_odia_v2_training.py --out data/training/custom.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

_SYSTEM_PROMPT = (
    "You are Oraculus, a civic-accountability document analysis system. "
    "You analyze government documents for fiscal irregularities, CPRA violations, "
    "surveillance overreach, procurement anomalies, and constitutional implications. "
    "You are not a general-purpose assistant. You do not answer questions outside "
    "your domain. Your findings are specific, evidence-grounded, and written for "
    "both legal professionals and informed members of the public."
)

_SOURCES = [
    _REPO_ROOT / "data" / "training" / "odia_sft_reports_20261017_152705.jsonl",
    _REPO_ROOT / "data" / "training" / "odia_sft_explanations_20261017_152940.jsonl",
    _REPO_ROOT / "data" / "training" / "adversarial_dan_type8.jsonl",
]


def _convert_alpaca_to_messages(record: dict) -> dict:
    """Convert Alpaca-format record to messages format."""
    user_content = record["instruction"]
    if record.get("input"):
        user_content = f"{user_content}\n\n{record['input']}"
    return {
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": record["output"]},
        ]
    }


def _load_source(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "messages" in rec:
                records.append({"messages": rec["messages"]})
            elif "instruction" in rec:
                records.append(_convert_alpaca_to_messages(rec))
            else:
                raise ValueError(f"Unknown format in {path.name}: {list(rec.keys())}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepare odia-v2 combined training file"
    )
    parser.add_argument(
        "--out",
        default=str(_REPO_ROOT / "data" / "training" / "odia_v2_combined_327717.jsonl"),
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--verify", action="store_true", help="Verify existing output only"
    )
    args = parser.parse_args()

    out_path = Path(args.out)

    if args.verify:
        if not out_path.exists():
            print(f"Output file not found: {out_path}")
            return
        count = sum(1 for _ in open(out_path, encoding="utf-8") if _.strip())
        print(f"Verified: {count:,} examples in {out_path.name}")
        return

    # Check all sources exist
    missing = [p for p in _SOURCES if not p.exists()]
    if missing:
        for p in missing:
            print(f"MISSING: {p}")
        raise SystemExit(1)

    print("Loading sources...")
    all_records: list[dict] = []
    for src in _SOURCES:
        records = _load_source(src)
        print(f"  {src.name}: {len(records):,} examples")
        all_records.extend(records)

    print(f"Total before shuffle: {len(all_records):,}")

    random.seed(args.seed)
    random.shuffle(all_records)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    size_mb = out_path.stat().st_size / 1_048_576
    print(
        f"\nWrote {len(all_records):,} examples -> {out_path.name} ({size_mb:.0f} MB)"
    )
    print(
        "Next: upload this file to HuggingFace as SynTechRev/odia-v2-training (private)"
    )
    print(
        "  huggingface-cli upload SynTechRev/odia-v2-training data/training/odia_v2_combined_327717.jsonl --repo-type dataset"
    )


if __name__ == "__main__":
    main()
