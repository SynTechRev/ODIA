"""Day 03: Generate retrieval benchmark visualization.

Reads data/eval/retrieval_benchmark_day03.json and produces
data/eval/retrieval_benchmark_day03.png with two sub-plots:

Sub-plot A: Overall comparison (P@10 and MRR@10) across three systems.
Sub-plot B: Category-level breakdown showing per-category MRR@10 per system.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

INPUT_PATH = Path("data/eval/retrieval_benchmark_day03.json")
OUTPUT_PATH = Path("data/eval/retrieval_benchmark_day03.png")

_SYSTEM_LABELS = {
    "tfidf_bm25": "TF-IDF/BM25",
    "hybrid_bge_m3": "Hybrid\n(BGE-M3+BM25+\nreranker)",
    "colbertv2": "ColBERTv2\n(late interaction)",
}
_COLORS = {
    "tfidf_bm25": "#4C72B0",
    "hybrid_bge_m3": "#DD8452",
    "colbertv2": "#55A868",
}
_CATEGORY_ORDER = [
    "instrument_type",
    "dollar_range",
    "severity_critical",
    "gap_pattern",
    "combined",
]
_CAT_LABELS = {
    "instrument_type": "Instrument\nType",
    "dollar_range": "Dollar\nRange",
    "severity_critical": "Severity\nCritical",
    "gap_pattern": "Gap\nPattern",
    "combined": "Combined /\nAnalytical",
}


def main() -> None:
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    configs = data["configurations"]
    systems = list(configs.keys())

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        f"Retrieval Benchmark Day 03 | {data['corpus_size']}-doc Fresno corpus | {data['query_count']} queries",
        fontsize=12,
        fontweight="bold",
    )

    # Sub-plot A: Overall P@10 and MRR@10
    x = np.arange(len(systems))
    width = 0.35
    p_at_10 = [configs[s]["p_at_10_overall"] for s in systems]
    mrr_at_10 = [configs[s]["mrr_at_10_overall"] for s in systems]
    labels = [_SYSTEM_LABELS.get(s, s) for s in systems]

    bars_p = ax_a.bar(
        x - width / 2,
        p_at_10,
        width,
        label="P@10",
        color=[_COLORS.get(s, "#888") for s in systems],
        alpha=0.9,
    )
    bars_m = ax_a.bar(
        x + width / 2,
        mrr_at_10,
        width,
        label="MRR@10",
        color=[_COLORS.get(s, "#888") for s in systems],
        alpha=0.6,
        hatch="//",
    )
    ax_a.set_title("Overall Performance", fontsize=11)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(labels, fontsize=9)
    ax_a.set_ylim(0, 1.05)
    ax_a.set_ylabel("Score")
    ax_a.legend(fontsize=9)
    ax_a.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars_p, p_at_10, strict=False):
        ax_a.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.01,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for bar, val in zip(bars_m, mrr_at_10, strict=False):
        ax_a.text(
            bar.get_x() + bar.get_width() / 2,
            val + 0.01,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Sub-plot B: Category-level MRR@10
    categories = [
        c
        for c in _CATEGORY_ORDER
        if all(c in configs[s].get("by_category", {}) for s in systems)
    ]
    n_cats = len(categories)
    n_sys = len(systems)
    group_width = 0.7
    bar_width = group_width / n_sys
    cat_x = np.arange(n_cats)

    for i, sys in enumerate(systems):
        offsets = cat_x + (i - (n_sys - 1) / 2) * bar_width
        vals = [
            configs[sys]["by_category"].get(cat, {}).get("mrr_at_10", 0)
            for cat in categories
        ]
        ax_b.bar(
            offsets,
            vals,
            bar_width,
            label=_SYSTEM_LABELS.get(sys, sys),
            color=_COLORS.get(sys, "#888"),
            alpha=0.85,
        )

    ax_b.set_title("MRR@10 by Query Category", fontsize=11)
    ax_b.set_xticks(cat_x)
    ax_b.set_xticklabels([_CAT_LABELS.get(c, c) for c in categories], fontsize=9)
    ax_b.set_ylim(0, 1.05)
    ax_b.set_ylabel("MRR@10")
    ax_b.legend(fontsize=8, loc="upper right")
    ax_b.grid(axis="y", linestyle="--", alpha=0.4)

    # Annotate build times at the bottom of the figure
    build_notes = " | ".join(
        f"{_SYSTEM_LABELS.get(s, s).replace(chr(10), ' ')}: build={configs[s]['index_build_time_sec']:.0f}s "
        f"p50={configs[s]['latency_p50_ms']:.0f}ms"
        for s in systems
    )
    fig.text(0.5, 0.01, build_notes, ha="center", fontsize=8, style="italic")

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(OUTPUT_PATH), dpi=150, bbox_inches="tight")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
