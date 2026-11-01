"""Day 01: Reasoning-mode evaluation script.

Runs odia-v2 against all 20 queries in reasoning_mode_queries.jsonl with both
reasoning_mode=True and reasoning_mode=False. Saves paired outputs for comparison.

Requires:
    - uvicorn API running: uvicorn oraculus_di_auditor.interface.api:app --reload
    - data/eval/reasoning_mode_queries.jsonl populated (reference_answer fields)

Output:
    data/eval/reasoning_mode_day01_outputs.jsonl

Each output line:
    {
      "id": "q01",
      "category": "cpra",
      "query": "...",
      "reasoning_off": {"answer": "...", "confidence": 0.0, "latency_s": 0.0},
      "reasoning_on":  {"answer": "...", "confidence": 0.0, "latency_s": 0.0},
      "reference_answer": "..."
    }
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests

API_BASE = "http://localhost:8000"
QUERIES_PATH = Path("data/eval/reasoning_mode_queries.jsonl")
OUTPUT_PATH = Path("data/eval/reasoning_mode_day01_outputs.jsonl")


def query_rag(question: str, reasoning_mode: bool, top_k: int = 15) -> dict:
    start = time.perf_counter()
    resp = requests.post(
        f"{API_BASE}/api/v1/rag/query",
        json={"query": question, "top_k": top_k, "reasoning_mode": reasoning_mode},
        timeout=120,
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    data = resp.json()
    return {
        "answer": data.get("answer", ""),
        "confidence": data.get("confidence"),
        "latency_s": round(elapsed, 2),
    }


def main() -> None:
    queries = []
    with QUERIES_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))

    print(f"Running {len(queries)} queries x 2 modes = {len(queries) * 2} total calls")
    print(f"Estimated time at 8s/call: ~{len(queries) * 2 * 8 / 60:.0f} min")

    results = []
    for i, q in enumerate(queries, 1):
        print(
            f"\n[{i}/{len(queries)}] {q['id']} ({q['category']}): {q['query'][:60]}..."
        )

        print("  reasoning_mode=False ...", end=" ", flush=True)
        off_result = query_rag(q["query"], reasoning_mode=False)
        print(f"done ({off_result['latency_s']}s, conf={off_result['confidence']})")

        print("  reasoning_mode=True  ...", end=" ", flush=True)
        on_result = query_rag(q["query"], reasoning_mode=True)
        print(f"done ({on_result['latency_s']}s, conf={on_result['confidence']})")

        results.append(
            {
                "id": q["id"],
                "category": q["category"],
                "query": q["query"],
                "reasoning_off": off_result,
                "reasoning_on": on_result,
                "reference_answer": q.get("reference_answer", ""),
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nOutputs written to {OUTPUT_PATH}")
    print(
        "Next step: fill reference_answer fields in queries file, then run Day 01 analysis."
    )


if __name__ == "__main__":
    main()
