"""odia_v2_train.py — Unsloth QLoRA fine-tuning script for odia-v2.

Run this on the Vast.ai RTX 4090 Unsloth Studio instance.

Prerequisites on the instance:
    pip install datasets huggingface_hub

Usage:
    python odia_v2_train.py

The script:
  1. Downloads odia_v2_combined_327717.jsonl from HuggingFace (private dataset)
  2. Loads unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit as the base
  3. Applies QLoRA (r=16, alpha=32) — same config as odia-v1
  4. Trains 1 epoch (~12–15h on RTX 4090)
  5. Saves LoRA adapters to ./odia-v2-lora/
  6. Merges adapters and exports Q4_K_M GGUF to ./odia-v2.q4_k_m.gguf
  7. Uploads GGUF to SynTechRev/odia-v2 on HuggingFace
"""

import os

# ── 0. HuggingFace token (set as env var on the instance) ────────────────────
HF_TOKEN = os.environ.get("HF_TOKEN")
if not HF_TOKEN:
    raise SystemExit("Set HF_TOKEN environment variable before running.")

# ── 1. Load model + tokenizer via Unsloth ────────────────────────────────────
from unsloth import FastLanguageModel  # noqa: E402

MAX_SEQ_LEN = 2048

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit",
    max_seq_length=MAX_SEQ_LEN,
    dtype=None,  # auto-detect: bfloat16 on Ampere+
    load_in_4bit=True,
    token=HF_TOKEN,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    lora_alpha=32,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=42,
)

# ── 2. Load dataset from HuggingFace ─────────────────────────────────────────
from datasets import load_dataset  # noqa: E402

dataset = load_dataset(
    "json",
    data_files={
        "train": "hf://datasets/SynTechRev/odia-v2-training/odia_v2_combined_327717.jsonl"
    },
    split="train",
    token=HF_TOKEN,
)
print(f"Dataset loaded: {len(dataset):,} examples")


# ── 3. Apply chat template ────────────────────────────────────────────────────
def format_example(example):
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


dataset = dataset.map(format_example, num_proc=4)

# ── 4. Trainer ────────────────────────────────────────────────────────────────
from transformers import TrainingArguments  # noqa: E402
from trl import SFTTrainer  # noqa: E402
from unsloth import is_bfloat16_supported  # noqa: E402

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=MAX_SEQ_LEN,
    dataset_num_proc=2,
    args=TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,  # effective batch = 16
        warmup_steps=100,
        num_train_epochs=1,  # 1 epoch — dataset is 3.7x v1
        learning_rate=2e-4,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=25,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=42,
        output_dir="./odia-v2-checkpoints",
        save_strategy="steps",
        save_steps=500,
        save_total_limit=2,
    ),
)

print("Starting training...")
trainer_stats = trainer.train()
print(f"Training complete. Runtime: {trainer_stats.metrics['train_runtime']:.0f}s")

# ── 5. Save LoRA adapters ─────────────────────────────────────────────────────
model.save_pretrained("./odia-v2-lora")
tokenizer.save_pretrained("./odia-v2-lora")
print("LoRA adapters saved to ./odia-v2-lora/")

# ── 6. Export Q4_K_M GGUF ────────────────────────────────────────────────────
# Merge adapters into full weights first, then quantize
print("Merging adapters and exporting GGUF (Q4_K_M)...")
model.save_pretrained_gguf(
    "./odia-v2-gguf",
    tokenizer,
    quantization_method="q4_k_m",
)
print("GGUF export complete → ./odia-v2-gguf/")

# ── 7. Upload to HuggingFace ──────────────────────────────────────────────────
from huggingface_hub import HfApi  # noqa: E402

api = HfApi(token=HF_TOKEN)

# Upload LoRA adapters
api.create_repo("SynTechRev/odia-v2", repo_type="model", private=True, exist_ok=True)
api.upload_folder(
    folder_path="./odia-v2-lora",
    repo_id="SynTechRev/odia-v2",
    repo_type="model",
    path_in_repo="lora-adapters/",
)
print("LoRA adapters uploaded to SynTechRev/odia-v2/lora-adapters/")

# Upload GGUF
import glob  # noqa: E402

gguf_files = glob.glob("./odia-v2-gguf/*.gguf")
for gguf_path in gguf_files:
    print(f"Uploading {gguf_path}...")
    api.upload_file(
        path_or_fileobj=gguf_path,
        path_in_repo=os.path.basename(gguf_path),
        repo_id="SynTechRev/odia-v2",
        repo_type="model",
    )
print("All uploads complete. Verify on HuggingFace then destroy the instance.")
