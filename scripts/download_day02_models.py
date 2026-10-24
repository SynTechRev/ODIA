"""Download BGE-M3, bge-reranker-v2-m3, and colbertv2.0 to models/ directory."""

import sys
from pathlib import Path

from huggingface_hub import snapshot_download

BASE = Path(__file__).parent.parent
MODELS_DIR = BASE / "models"
MODELS_DIR.mkdir(exist_ok=True)

downloads = [
    ("BAAI/bge-m3", MODELS_DIR / "bge-m3"),
    ("BAAI/bge-reranker-v2-m3", MODELS_DIR / "bge-reranker-v2-m3"),
    ("colbert-ir/colbertv2.0", MODELS_DIR / "colbertv2.0"),
]

for repo_id, local_dir in downloads:
    if local_dir.exists() and any(local_dir.iterdir()):
        print(f"SKIP {repo_id} (already at {local_dir})")
        continue
    print(f"Downloading {repo_id} -> {local_dir} ...")
    sys.stdout.flush()
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(local_dir),
            ignore_patterns=["*.ot", "*.h5", "flax_*", "tf_*"],
        )
        print(f"DONE {repo_id}")
    except Exception as e:
        print(f"ERROR {repo_id}: {e}")
    sys.stdout.flush()

print("All downloads complete.")
