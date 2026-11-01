#!/usr/bin/env python3
"""Convert saved DPO LoRA adapters to Q4_K_M GGUF using unsloth native export.

Run on the Vast.ai instance after train_dpo.py has saved adapters but failed
at the GGUF step (e.g. 'Quant method is not yet supported: bitsandbytes').

Usage:
  python3 scripts/convert_dpo_to_gguf.py
  python3 scripts/convert_dpo_to_gguf.py --adapters models/odia-v3-dpo-lora/adapters
  python3 scripts/convert_dpo_to_gguf.py --out models/odia-v3-dpo-lora/gguf_out
"""
import argparse
from datetime import UTC, datetime
from pathlib import Path


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DPO adapter -> Q4_K_M GGUF via unsloth"
    )
    parser.add_argument(
        "--adapters",
        type=Path,
        default=Path("models/odia-v3-dpo-lora/adapters"),
        help="Path to saved LoRA adapter directory",
    )
    parser.add_argument(
        "--base-model",
        default="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
        help="HuggingFace base model id",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("models/odia-v3-dpo-lora/gguf_out"),
        help="Output directory for GGUF file",
    )
    parser.add_argument(
        "--quant",
        default="q4_k_m",
        help="Quantization method (default: q4_k_m)",
    )
    args = parser.parse_args()

    if not args.adapters.exists():
        print(f"ERROR: adapter directory not found: {args.adapters}")
        return 1

    print(f"[{_ts()}] Adapters: {args.adapters}")
    print(f"[{_ts()}] Base model: {args.base_model}")
    print(f"[{_ts()}] Output: {args.out}")
    print(f"[{_ts()}] Quant: {args.quant}")
    print()

    from unsloth import FastLanguageModel

    # Load base + adapters together via unsloth so save_pretrained_gguf
    # can download original fp16 weights and dequantize before conversion.
    # Using PeftModel.from_pretrained separately causes "bitsandbytes" error
    # because the BNB quantization_config survives merge_and_unload().
    print(
        f"[{_ts()}] Loading base + DPO adapters via FastLanguageModel ({args.adapters})..."
    )
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(args.adapters),
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )

    args.out.mkdir(parents=True, exist_ok=True)
    gguf_stem = str(args.out / "odia-v3")
    print(
        f"[{_ts()}] Exporting {args.quant.upper()} GGUF (merge + dequant + convert)..."
    )
    print(f"[{_ts()}] This will take 15-25 minutes...")
    model.save_pretrained_gguf(gguf_stem, tokenizer, quantization_method=args.quant)

    candidates = list(args.out.rglob("*.gguf"))
    if not candidates:
        print(f"ERROR: no GGUF file found in {args.out}")
        return 1

    gguf_path = candidates[0]
    size_gb = gguf_path.stat().st_size / 1e9
    print(f"[{_ts()}] GGUF ready: {gguf_path} ({size_gb:.2f} GB)")
    print()
    print("Next steps:")
    print("  1. Download GGUF (run locally):")
    print(
        f"     scp -i ~/.ssh/odia_vast_ed25519 -P $VAST_PORT root@$VAST_IP:{gguf_path} D:/ODIA/models/odia-v3.q4_k_m.gguf"
    )
    print("  2. Register in Ollama (run locally):")
    print("     ollama create odia-v3 -f models/Modelfile.v3")
    print("  3. Run severity_critical gate:")
    print("     python -I scripts/raia_severity_critical_gate.py --model odia-v3")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
