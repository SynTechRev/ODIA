"""LoRA fine-tuning runner for ODIA Layer 2 extraction model.

Fine-tunes a base LLM (Llama-3.1-8B, Qwen2.5-7B, or Mistral-7B)
using LoRA (Low-Rank Adaptation) via HuggingFace's PEFT library.

Designed for:
- Single-GPU workstation (RTX 4090 24GB, A100 40GB, or A100 80GB rental)
- Consumer-accessible fine-tuning (<$50 cloud cost per full run)
- CPU-only inference after training (quantized GGUF via llama.cpp)

Memory strategy:
- 4-bit quantized base model (bitsandbytes NF4)
- LoRA rank 16-64 (configurable; lower for smaller GPUs)
- Gradient checkpointing enabled
- Paged AdamW 8-bit optimizer

Dependencies (optional; install separately to avoid requiring GPU for package import):
    pip install torch transformers peft bitsandbytes accelerate datasets trl

This module imports ML dependencies lazily so that odia_ai can be imported
on systems without GPU/ML libraries installed.

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class LoRAConfig:
    """LoRA hyperparameters."""

    r: int = 16  # LoRA rank
    alpha: int = 32  # LoRA alpha (scaling factor)
    dropout: float = 0.05
    target_modules: list[str] = field(
        default_factory=lambda: [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ]
    )
    bias: str = "none"
    task_type: str = "CAUSAL_LM"


@dataclass
class TrainingConfig:
    """Training hyperparameters."""

    base_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    output_dir: str = "./odia_model_output"
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 1
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 16  # effective batch size = 16
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    weight_decay: float = 0.001
    max_seq_length: int = 4096
    logging_steps: int = 10
    eval_steps: int = 100
    save_steps: int = 200
    save_total_limit: int = 3
    load_in_4bit: bool = True
    bf16: bool = True
    gradient_checkpointing: bool = True
    optim: str = "paged_adamw_8bit"
    seed: int = 42
    report_to: str = "none"  # "wandb" | "tensorboard" | "none"


@dataclass
class TrainingResult:
    """Return type for train_lora(). Decoupled from heavy ML types."""

    success: bool
    model_path: str
    train_loss: float | None = None
    eval_loss: float | None = None
    num_train_examples: int = 0
    num_eval_examples: int = 0
    steps_completed: int = 0
    error_message: str | None = None
    config_snapshot: dict = field(default_factory=dict)


def _check_ml_dependencies() -> tuple[bool, str]:
    """Verify that ML dependencies are importable. Returns (ok, message)."""
    missing: list[str] = []
    for pkg in ("torch", "transformers", "peft", "datasets"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        return (
            False,
            f"Missing ML dependencies: {', '.join(missing)}. "
            f"Install with: pip install {' '.join(missing)} bitsandbytes accelerate trl",
        )
    return True, ""


def load_jsonl_dataset(path: Path) -> list[dict]:
    """Load an alpaca-format JSONL file into a list of records."""
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def format_alpaca_prompt(record: dict, tokenizer: Any = None) -> str:
    """Format an alpaca-style record into a single training string.

    Template:
        <system>
        {system}

        <instruction>
        {instruction}

        <input>
        {input}

        <output>
        {output}
    """
    system = record.get("system", "")
    instruction = record.get("instruction", "")
    input_text = record.get("input", "")
    output = record.get("output", "")

    parts = []
    if system:
        parts.append(f"### System:\n{system}")
    parts.append(f"### Instruction:\n{instruction}")
    if input_text:
        parts.append(f"### Input:\n{input_text}")
    parts.append(f"### Response:\n{output}")
    return "\n\n".join(parts)


def train_lora(
    train_path: Path,
    validation_path: Path | None,
    lora_config: LoRAConfig,
    training_config: TrainingConfig,
) -> TrainingResult:
    """Run the LoRA fine-tuning loop.

    This function imports torch/transformers/peft lazily. Users without
    GPU or ML deps will get a clear TrainingResult(success=False, error=...)
    rather than an ImportError at import time.

    Args:
        train_path: path to train.jsonl (alpaca format)
        validation_path: optional path to validation.jsonl
        lora_config: LoRA hyperparameters
        training_config: training hyperparameters

    Returns:
        TrainingResult describing the training outcome.
    """
    ok, message = _check_ml_dependencies()
    if not ok:
        return TrainingResult(
            success=False,
            model_path="",
            error_message=message,
            config_snapshot={"lora": lora_config.__dict__, "training": training_config.__dict__},
        )

    # Lazy imports (only reachable if deps present)
    import torch  # type: ignore
    from datasets import Dataset  # type: ignore
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training  # type: ignore
    from transformers import (  # type: ignore
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    output_dir = Path(training_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading tokenizer from %s", training_config.base_model)
    tokenizer = AutoTokenizer.from_pretrained(
        training_config.base_model, trust_remote_code=True
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization config
    bnb_config = None
    if training_config.load_in_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    logger.info("Loading base model %s (4-bit=%s)", training_config.base_model, training_config.load_in_4bit)
    model = AutoModelForCausalLM.from_pretrained(
        training_config.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16 if training_config.bf16 else torch.float32,
    )

    if training_config.load_in_4bit:
        model = prepare_model_for_kbit_training(model)
    if training_config.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    peft_cfg = LoraConfig(
        r=lora_config.r,
        lora_alpha=lora_config.alpha,
        target_modules=lora_config.target_modules,
        lora_dropout=lora_config.dropout,
        bias=lora_config.bias,
        task_type=lora_config.task_type,
    )
    model = get_peft_model(model, peft_cfg)
    model.print_trainable_parameters()

    # Load datasets
    logger.info("Loading train dataset from %s", train_path)
    train_records = load_jsonl_dataset(train_path)
    train_texts = [format_alpaca_prompt(r, tokenizer) for r in train_records]
    train_ds = Dataset.from_dict({"text": train_texts})

    eval_ds = None
    eval_count = 0
    if validation_path and validation_path.exists():
        eval_records = load_jsonl_dataset(validation_path)
        eval_texts = [format_alpaca_prompt(r, tokenizer) for r in eval_records]
        eval_ds = Dataset.from_dict({"text": eval_texts})
        eval_count = len(eval_records)

    def tokenize_fn(batch: dict) -> dict:
        out = tokenizer(
            batch["text"],
            truncation=True,
            max_length=training_config.max_seq_length,
            padding=False,
        )
        out["labels"] = out["input_ids"].copy()
        return out

    train_ds = train_ds.map(tokenize_fn, batched=True, remove_columns=["text"])
    if eval_ds is not None:
        eval_ds = eval_ds.map(tokenize_fn, batched=True, remove_columns=["text"])

    args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=training_config.num_train_epochs,
        per_device_train_batch_size=training_config.per_device_train_batch_size,
        per_device_eval_batch_size=training_config.per_device_eval_batch_size,
        gradient_accumulation_steps=training_config.gradient_accumulation_steps,
        learning_rate=training_config.learning_rate,
        warmup_ratio=training_config.warmup_ratio,
        lr_scheduler_type=training_config.lr_scheduler_type,
        weight_decay=training_config.weight_decay,
        logging_steps=training_config.logging_steps,
        eval_steps=training_config.eval_steps if eval_ds is not None else None,
        save_steps=training_config.save_steps,
        save_total_limit=training_config.save_total_limit,
        eval_strategy="steps" if eval_ds is not None else "no",
        bf16=training_config.bf16,
        optim=training_config.optim,
        seed=training_config.seed,
        report_to=training_config.report_to,
        gradient_checkpointing=training_config.gradient_checkpointing,
    )

    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=collator,
    )

    logger.info("Starting training: %d train examples, %d eval examples", len(train_records), eval_count)
    try:
        train_output = trainer.train()
        trainer.save_model(str(output_dir / "final"))
        tokenizer.save_pretrained(str(output_dir / "final"))

        eval_loss = None
        if eval_ds is not None:
            eval_metrics = trainer.evaluate()
            eval_loss = eval_metrics.get("eval_loss")

        return TrainingResult(
            success=True,
            model_path=str(output_dir / "final"),
            train_loss=float(train_output.training_loss),
            eval_loss=float(eval_loss) if eval_loss is not None else None,
            num_train_examples=len(train_records),
            num_eval_examples=eval_count,
            steps_completed=int(train_output.global_step),
            config_snapshot={
                "lora": lora_config.__dict__,
                "training": training_config.__dict__,
            },
        )
    except Exception as e:
        logger.exception("Training failed")
        return TrainingResult(
            success=False,
            model_path=str(output_dir),
            error_message=str(e),
            num_train_examples=len(train_records),
            num_eval_examples=eval_count,
            config_snapshot={
                "lora": lora_config.__dict__,
                "training": training_config.__dict__,
            },
        )
