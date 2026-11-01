#!/usr/bin/env python3
"""Day 11 Vast.ai: Full DPO training run to produce odia-v3.

Run on RTX 4090 (24GB VRAM), Ubuntu 22.04, AFTER smoke_test_dpo.py --mode forward passes.

Training flow:
  1. Load base model: unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit
  2. Load odia-v2 LoRA adapters from SynTechRev/odia-v2 (if HF_TOKEN set)
  3. Apply LoRA for DPO fine-tuning
  4. Train 1 epoch on data/preferences_v1.jsonl (5 pairs)
  5. Report Watch 1 (loss), Watch 2 (VRAM), Watch 3 (reward margin)
  6. Merge adapters to full model
  7. Convert merged model to GGUF q4_k_m
  8. Push GGUF to HuggingFace SynTechRev/odia-v3-dpo (requires HF_TOKEN)

Usage (on Vast.ai instance):
  HF_TOKEN=hf_... python train_dpo.py
  HF_TOKEN=hf_... python train_dpo.py --config config/dpo_config_v1.yaml
  HF_TOKEN=hf_... python train_dpo.py --skip-push  # train + GGUF, no HF upload
  HF_TOKEN=hf_... python train_dpo.py --skip-gguf  # adapters only

Post-training on local machine:
  - Download GGUF from HuggingFace browser UI (faster than rsync from instance)
  - ollama create odia-v3 -f models/Modelfile.v3
  - python -I scripts/raia_severity_critical_gate.py --model odia-v3
"""
import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def _vram_gb() -> float:
    try:
        import torch

        return torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        return 0.0


def _load_config(config_path: Path) -> dict:
    import yaml

    with config_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_model_and_tokenizer(cfg: dict, hf_token: str | None):
    from unsloth import FastLanguageModel

    base_model = cfg["model"]["hf_base"]
    max_seq = cfg["model"]["max_seq_length"]

    print(f"[{_ts()}] Loading base model: {base_model}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=base_model,
        max_seq_length=max_seq,
        load_in_4bit=True,
        token=hf_token,
    )

    # Load odia-v2 adapters on top of base if available.
    # This DPO run starts from odia-v2 weights, not the raw base model,
    # so the preference signal builds on the SFT capability foundation.
    odia_v2_repo = "SynTechRev/odia-v2"
    if hf_token:
        try:
            print(f"[{_ts()}] Loading odia-v2 adapters from {odia_v2_repo}...")
            from peft import PeftModel

            model = PeftModel.from_pretrained(
                model,
                odia_v2_repo,
                token=hf_token,
                is_trainable=False,
            )
            model = model.merge_and_unload()
            print(
                f"[{_ts()}] odia-v2 adapters merged into base -- DPO starts from odia-v2"
            )
        except Exception as exc:
            print(
                f"[{_ts()}] WARNING: could not load odia-v2 adapters ({exc}). "
                "DPO will start from base model only."
            )
    else:
        print(
            f"[{_ts()}] HF_TOKEN not set -- skipping odia-v2 adapter load (base model only)"
        )

    lora_cfg = cfg["lora"]
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        target_modules=lora_cfg["target_modules"],
        bias=lora_cfg["bias"],
    )
    print(f"[{_ts()}] LoRA applied (r={lora_cfg['r']}, alpha={lora_cfg['lora_alpha']})")
    return model, tokenizer


def _build_dataset(data_path: Path):
    from datasets import Dataset

    pairs = []
    with data_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    print(f"[{_ts()}] Loaded {len(pairs)} preference pairs from {data_path}")
    return Dataset.from_list(pairs)


def _run_training(model, tokenizer, dataset, cfg: dict, output_dir: Path) -> list[dict]:
    import torch
    from trl import DPOConfig, DPOTrainer

    train_cfg = cfg["training"]
    dpo_cfg = cfg["dpo"]

    dpo_args = DPOConfig(
        output_dir=str(output_dir),
        num_train_epochs=train_cfg["epochs"],
        per_device_train_batch_size=train_cfg["per_device_train_batch_size"],
        gradient_accumulation_steps=train_cfg["gradient_accumulation_steps"],
        learning_rate=train_cfg["learning_rate"],
        lr_scheduler_type=train_cfg["lr_scheduler_type"],
        warmup_ratio=train_cfg["warmup_ratio"],
        weight_decay=train_cfg["weight_decay"],
        max_grad_norm=train_cfg["max_grad_norm"],
        bf16=train_cfg["bf16"] and torch.cuda.is_bf16_supported(),
        fp16=train_cfg["fp16"],
        optim=train_cfg["optim"],
        logging_steps=train_cfg["logging_steps"],
        save_steps=train_cfg["save_steps"],
        seed=train_cfg["seed"],
        beta=dpo_cfg["beta"],
        loss_type=dpo_cfg["loss_type"],
        label_smoothing=dpo_cfg["label_smoothing"],
        report_to="none",
        remove_unused_columns=False,
    )

    trainer = DPOTrainer(
        model=model,
        ref_model=None,
        args=dpo_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print(
        f"[{_ts()}] Starting DPO training (beta={dpo_cfg['beta']}, epochs={train_cfg['epochs']})..."
    )
    if torch.cuda.is_available():
        vram_before = torch.cuda.memory_allocated() / 1e9
        print(f"[{_ts()}] Watch 2 -- VRAM at training start: {vram_before:.2f} GB")

    trainer.train()

    history = trainer.state.log_history
    if torch.cuda.is_available():
        peak_vram = torch.cuda.max_memory_allocated() / 1e9
        print(
            f"[{_ts()}] Watch 2 -- Peak VRAM (dual-model): {peak_vram:.2f} GB / {_vram_gb():.1f} GB"
        )

    losses = [h["loss"] for h in history if "loss" in h]
    rewards_chosen = [h.get("rewards/chosen") for h in history if "rewards/chosen" in h]
    rewards_rejected = [
        h.get("rewards/rejected") for h in history if "rewards/rejected" in h
    ]

    print(
        f"[{_ts()}] Watch 1 -- Losses: {[round(l, 4) for l in losses[:5]]}...{[round(l, 4) for l in losses[-3:]]}"
    )

    if rewards_chosen and rewards_rejected:
        margins = [
            c - r for c, r in zip(rewards_chosen, rewards_rejected, strict=False)
        ]
        mean_margin = sum(margins) / len(margins)
        margin_positive = mean_margin > 0
        print(
            f"[{_ts()}] Watch 3 -- Mean reward margin: {mean_margin:.4f} ({'positive' if margin_positive else 'NEGATIVE -- check pairs'})"
        )

    return history


def _export_gguf(model, tokenizer, output_dir: Path) -> Path:
    # unsloth's save_pretrained_gguf handles BNB dequant + merge + llama.cpp conversion
    # in one call; avoids the 'Quant method is not yet supported: bitsandbytes' error
    # that occurs when calling convert_hf_to_gguf.py directly on a 4-bit merged model.
    gguf_dir = output_dir / "gguf_out"
    gguf_dir.mkdir(parents=True, exist_ok=True)
    # Model still has LoRA adapters active -- unsloth's save_pretrained_gguf
    # downloads original fp16 weights, applies adapters, and converts.
    # Do NOT call merge_and_unload() here: that leaves BNB quantization_config
    # in the config.json which llama.cpp cannot handle.
    print(
        f"[{_ts()}] Exporting Q4_K_M GGUF via unsloth (fp16 download + adapter merge + convert)..."
    )
    model.save_pretrained_gguf(
        str(gguf_dir / "odia-v3"), tokenizer, quantization_method="q4_k_m"
    )
    # unsloth appends the quant suffix: odia-v3-Q4_K_M.gguf
    candidates = list(gguf_dir.rglob("*.gguf"))
    if not candidates:
        raise RuntimeError(f"No GGUF file produced in {gguf_dir}")
    gguf_path = candidates[0]
    print(
        f"[{_ts()}] GGUF saved: {gguf_path} ({gguf_path.stat().st_size / 1e9:.2f} GB)"
    )
    return gguf_path


def _push_to_hub(gguf_path: Path, repo_id: str, hf_token: str) -> None:
    from huggingface_hub import HfApi

    api = HfApi(token=hf_token)
    print(f"[{_ts()}] Creating/verifying HuggingFace repo: {repo_id}...")
    api.create_repo(repo_id=repo_id, private=True, exist_ok=True)
    print(f"[{_ts()}] Uploading {gguf_path.name} to {repo_id}...")
    api.upload_file(
        path_or_fileobj=str(gguf_path),
        path_in_repo=gguf_path.name,
        repo_id=repo_id,
        token=hf_token,
    )
    print(f"[{_ts()}] Upload complete: https://huggingface.co/{repo_id}")
    print()
    print("Download GGUF to local machine via HuggingFace browser (faster than rsync).")
    print(f"  URL: https://huggingface.co/{repo_id}/resolve/main/{gguf_path.name}")
    print()
    print("After download, register in Ollama:")
    print("  Copy models/Modelfile and update FROM line:")
    print(f"    FROM D:\\ODIA\\models\\{gguf_path.name}")
    print("  ollama create odia-v3 -f models/Modelfile.v3")
    print()
    print("Then run the gate locally:")
    print("  python -I scripts/raia_severity_critical_gate.py --model odia-v3")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Day 11 Vast.ai: DPO training for odia-v3"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/dpo_config_v1.yaml"),
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/preferences_v1.jsonl"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/odia-v3-dpo-lora"),
    )
    parser.add_argument(
        "--skip-gguf",
        action="store_true",
        help="Save adapters only, skip GGUF conversion",
    )
    parser.add_argument(
        "--skip-push",
        action="store_true",
        help="Skip HuggingFace upload (GGUF stays on instance)",
    )
    parser.add_argument(
        "--beta",
        type=float,
        default=None,
        help="Override beta from config (Watch 1 sweep: 0.05, 0.1, 0.2, 0.3)",
    )
    args = parser.parse_args()

    hf_token: str | None = os.getenv("HF_TOKEN")
    if not hf_token:
        print(
            "WARNING: HF_TOKEN not set. odia-v2 adapters will not be loaded and "
            "GGUF will not be pushed to HuggingFace.",
            file=sys.stderr,
        )

    if not args.config.exists():
        print(f"ERROR: config not found: {args.config}", file=sys.stderr)
        return 1
    if not args.data.exists():
        print(f"ERROR: preferences file not found: {args.data}", file=sys.stderr)
        return 1

    cfg = _load_config(args.config)
    if args.beta is not None:
        cfg["dpo"]["beta"] = args.beta
        print(f"[{_ts()}] Beta override: {args.beta}")

    print(f"[{_ts()}] === Day 11 odia-v3 DPO Training ===")
    print(f"[{_ts()}] Config: {args.config}")
    print(f"[{_ts()}] Data: {args.data}")
    print(f"[{_ts()}] Output: {args.output_dir}")
    print(f"[{_ts()}] GPU: {_vram_gb():.1f} GB VRAM")
    print()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    model, tokenizer = _load_model_and_tokenizer(cfg, hf_token)
    dataset = _build_dataset(args.data)
    history = _run_training(model, tokenizer, dataset, cfg, args.output_dir)

    # Save adapters regardless of downstream steps
    adapter_path = args.output_dir / "adapters"
    model.save_pretrained(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))
    print(f"[{_ts()}] Adapters saved: {adapter_path}")

    losses = [h["loss"] for h in history if "loss" in h]
    has_nan = any(l != l for l in losses)
    loss_ok = len(losses) >= 2 and losses[-1] < losses[0] and not has_nan

    if not loss_ok:
        print(
            f"[{_ts()}] ERROR: training did not converge (losses={losses[:5]}). Stopping."
        )
        return 1

    if args.skip_gguf:
        print(f"[{_ts()}] --skip-gguf: stopping after adapter save.")
        return 0

    gguf_path = _export_gguf(model, tokenizer, args.output_dir)

    if not gguf_path.exists():
        print(
            f"[{_ts()}] GGUF conversion failed or skipped. Adapters are at {adapter_path}."
        )
        return 1

    report = {
        "run_date": datetime.now(UTC).isoformat(),
        "config": str(args.config),
        "beta": cfg["dpo"]["beta"],
        "loss_final": losses[-1] if losses else None,
        "loss_initial": losses[0] if losses else None,
        "loss_ok": loss_ok,
        "has_nan": has_nan,
        "gguf_path": str(gguf_path),
        "gguf_size_gb": round(gguf_path.stat().st_size / 1e9, 2),
        "history_steps": len(losses),
    }
    report_path = args.output_dir / "train_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[{_ts()}] Training report: {report_path}")

    if not args.skip_push:
        if not hf_token:
            print(f"[{_ts()}] HF_TOKEN not set -- skipping HuggingFace push.")
            print(f"GGUF is at: {gguf_path}")
        else:
            repo_id = cfg["output"]["hub_model_id"]
            _push_to_hub(gguf_path, repo_id, hf_token)
    else:
        print(f"[{_ts()}] --skip-push: GGUF at {gguf_path}")
        print("Download with rsync:")
        print(f"  rsync -avz --progress root@<INSTANCE_IP>:{gguf_path} D:/ODIA/models/")

    print(f"\n[{_ts()}] odia-v3 training COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
