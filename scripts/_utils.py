# scripts/_utils.py
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("oraculus.utils")


def sha256_of_file(path: Path, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_relpath(base: Path, path: Path) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except Exception:
        return str(path.resolve()).replace("\\", "/")


def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default
