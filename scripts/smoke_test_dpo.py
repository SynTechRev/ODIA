#!/usr/bin/env python3
"""
Day 6: 10-step DPO smoke test.

Two modes:
  --mode format  : validates JSONL schema only (no model, always runs locally)
  --mode forward : 10 gradient steps (requires GPU + trl + transformers; Vast.ai)

Output: data/eval/dpo_smoke_test_day06.json

Usage:
  python -I scripts/smoke_test_dpo.py               # format mode (default)
  python -I scripts/smoke_test_dpo.py --mode forward  # forward pass (GPU needed)
  python -I scripts/smoke_test_dpo.py --beta 0.05    # test a specific beta (Watch 1)
"""

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def validate_format(preferences_path: Path) -> list[dict]:
    """Validate JSONL format and DPO signal quality. Returns the parsed pairs."""
    if not preferences_path.exists():
        raise FileNotFoundError(
            f"preferences_v1.jsonl not found at {preferences_path}\n"
            "Run first: python -I scripts/generate_preferences_v1.py"
        )

    pairs: list[dict] = []
    with preferences_path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                pair = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {lineno}: JSON parse error -- {exc}") from exc

            missing = [k for k in ("prompt", "chosen", "rejected") if k not in pair]
            if missing:
                raise ValueError(f"Line {lineno}: missing required keys: {missing}")

            for key in ("prompt", "chosen", "rejected"):
                if not isinstance(pair[key], str) or not pair[key].strip():
                    raise ValueError(
                        f"Line {lineno}: '{key}' must be a non-empty string"
                    )

            pairs.append(pair)

    return pairs


def check_dpo_signal(pairs: list[dict]) -> dict:
    """Check that chosen responses carry citations and rejected do not."""
    doc_id_pattern = re.compile(r"\(doc_id:[0-9a-f]{64}\)")

    results = []
    for i, pair in enumerate(pairs):
        chosen_hits = len(doc_id_pattern.findall(pair["chosen"]))
        rejected_hits = len(doc_id_pattern.findall(pair["rejected"]))
        len_ratio = len(pair["rejected"]) / max(len(pair["chosen"]), 1)

        # Watch 3: length ratio check
        len_ratio_ok = 0.85 <= len_ratio <= 1.15

        results.append(
            {
                "pair_index": i,
                "chosen_citations": chosen_hits,
                "rejected_citations": rejected_hits,
                "chosen_len": len(pair["chosen"]),
                "rejected_len": len(pair["rejected"]),
                "length_ratio": round(len_ratio, 3),
                "length_ratio_ok": len_ratio_ok,
                "signal_clear": rejected_hits == 0,
            }
        )

    n_clear = sum(1 for r in results if r["signal_clear"])
    n_ratio_ok = sum(1 for r in results if r["length_ratio_ok"])
    return {
        "total_pairs": len(results),
        "signal_clear": n_clear,
        "signal_unclear": len(results) - n_clear,
        "length_ratio_ok": n_ratio_ok,
        "details": results,
    }


def run_format_check(preferences_path: Path, output_path: Path, beta: float) -> dict:
    """Mode: format. Validates data quality without loading a model."""
    print(f"[{_ts()}] Mode: format -- validating {preferences_path}")

    pairs = validate_format(preferences_path)
    print(f"[{_ts()}] Parsed {len(pairs)} pairs -- schema OK")

    signal = check_dpo_signal(pairs)
    print(f"[{_ts()}] DPO signal check:")
    print(f"  Total pairs    : {signal['total_pairs']}")
    print(f"  Signal clear   : {signal['signal_clear']} (rejected has 0 citations)")
    print(
        f"  Length ratio OK: {signal['length_ratio_ok']} / {signal['total_pairs']} (Watch 3)"
    )

    for detail in signal["details"]:
        ratio_flag = "" if detail["length_ratio_ok"] else " [WARN]"
        signal_flag = (
            "" if detail["signal_clear"] else " [WARN: rejected has citations]"
        )
        print(
            f"  pair {detail['pair_index']}: chosen_citations={detail['chosen_citations']} "
            f"rejected_citations={detail['rejected_citations']} "
            f"len_ratio={detail['length_ratio']}{ratio_flag}{signal_flag}"
        )

    result = {
        "mode": "format",
        "run_date": datetime.now(UTC).isoformat(),
        "preferences_file": str(preferences_path),
        "beta_config": beta,
        "format_ok": True,
        "signal_check": signal,
        "verdict": (
            "PASS" if signal["signal_clear"] == signal["total_pairs"] else "WARN"
        ),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[{_ts()}] Result: {result['verdict']} -- written to {output_path}")
    return result


def run_forward_pass(preferences_path: Path, output_path: Path, beta: float) -> dict:
    """Mode: forward. 10 gradient steps to verify numerical stability (Watch 2)."""
    try:
        import torch
        from trl import DPOConfig, DPOTrainer
        from unsloth import FastLanguageModel
    except ImportError as exc:
        print(
            f"[{_ts()}] ERROR: forward mode requires torch, trl, unsloth -- {exc}\n"
            "Run format mode locally: python -I scripts/smoke_test_dpo.py --mode format\n"
            "Run forward mode on Vast.ai: python -I scripts/smoke_test_dpo.py --mode forward",
            file=sys.stderr,
        )
        sys.exit(1)

    import yaml

    config_path = Path("config/dpo_config_v1.yaml")
    with config_path.open(encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    model_name = cfg["model"]["hf_base"]
    max_seq = cfg["model"]["max_seq_length"]

    print(
        f"[{_ts()}] Loading model {model_name} for forward pass (Watch 2 memory check)..."
    )
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg["lora"]["r"],
        lora_alpha=cfg["lora"]["lora_alpha"],
        lora_dropout=cfg["lora"]["lora_dropout"],
        target_modules=cfg["lora"]["target_modules"],
        bias=cfg["lora"]["bias"],
    )

    if torch.cuda.is_available():
        peak_vram_before = torch.cuda.memory_allocated() / 1e9
        print(f"[{_ts()}] VRAM after policy model: {peak_vram_before:.2f} GB (Watch 2)")

    # Load pairs
    pairs = validate_format(preferences_path)
    from datasets import Dataset

    dataset = Dataset.from_list(pairs)

    dpo_args = DPOConfig(
        output_dir="/tmp/dpo_smoke",
        num_train_epochs=1,
        max_steps=10,  # 10-step smoke test
        per_device_train_batch_size=1,
        gradient_accumulation_steps=1,
        learning_rate=5.0e-7,
        beta=beta,
        logging_steps=1,
        report_to="none",
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        remove_unused_columns=False,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,  # None = use implicit reference (frozen copy)
        args=dpo_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print(f"[{_ts()}] Running 10 gradient steps (beta={beta})...")
    trainer.train()

    history = trainer.state.log_history
    losses = [h["loss"] for h in history if "loss" in h]
    rewards_chosen = [h.get("rewards/chosen", None) for h in history]
    rewards_rejected = [h.get("rewards/rejected", None) for h in history]

    has_nan = any(l != l for l in losses)
    loss_decreasing = len(losses) >= 2 and losses[-1] < losses[0]
    margin_positive = all(
        (c or 0) > (r or 0)
        for c, r in zip(rewards_chosen, rewards_rejected, strict=False)
        if c is not None and r is not None
    )

    if torch.cuda.is_available():
        peak_vram = torch.cuda.max_memory_allocated() / 1e9
        print(f"[{_ts()}] Peak VRAM (dual-model): {peak_vram:.2f} GB (Watch 2)")

    print(f"[{_ts()}] Losses: {[round(l, 4) for l in losses]}")
    print(f"[{_ts()}] Loss decreasing: {loss_decreasing}")
    print(f"[{_ts()}] Has NaN: {has_nan}")
    print(f"[{_ts()}] Reward margin positive: {margin_positive}")

    verdict = "PASS" if (loss_decreasing and not has_nan) else "FAIL"

    result = {
        "mode": "forward",
        "run_date": datetime.now(UTC).isoformat(),
        "beta": beta,
        "steps": len(losses),
        "losses": [round(l, 6) for l in losses],
        "loss_decreasing": loss_decreasing,
        "has_nan": has_nan,
        "margin_positive": margin_positive,
        "peak_vram_gb": round(peak_vram, 2) if torch.cuda.is_available() else None,
        "verdict": verdict,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"[{_ts()}] Result: {verdict} -- written to {output_path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 6 DPO smoke test")
    parser.add_argument(
        "--mode",
        choices=["format", "forward"],
        default="format",
        help="format = data validation only; forward = 10 gradient steps (GPU)",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/preferences_v1.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/eval/dpo_smoke_test_day06.json"),
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=0.1,
        help="DPO beta (Watch 1: sweep 0.05, 0.1, 0.2, 0.3 for production run)",
    )
    args = parser.parse_args()

    if args.mode == "format":
        result = run_format_check(args.input, args.output, args.beta)
    else:
        result = run_forward_pass(args.input, args.output, args.beta)

    sys.exit(0 if result["verdict"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()
