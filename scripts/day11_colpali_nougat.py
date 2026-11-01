#!/usr/bin/env python3
"""
Day 11 Vast.ai session: ColPali + Nougat on TCPD corpus.

Run on RTX 4090 (24GB VRAM), Ubuntu 22.04.
Designed for the instance provisioned at Day 11 of the 10-Day Challenge.

Usage:
  python day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs
  python day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase colpali
  python day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase nougat
  python day11_colpali_nougat.py --pdf-dir /data/tcpd --output-dir /outputs --phase verify

Outputs (download to local after verify):
  /outputs/colpali_page_embeddings/*.npy  -- per-document page embeddings
  /outputs/colpali_manifest.json          -- doc index with shape info
  /outputs/nougat_ocr/**/*.mmd            -- Nougat markdown for sub-threshold pages
  /outputs/colpali_checkpoint.json        -- resume state (delete to restart phase)

Download command (run locally after verify):
  rsync -avz --progress root@<INSTANCE_IP>:/outputs/ data/vectors/tcpd_colpali/

Post-download local step:
  python scripts/raia_severity_critical_gate.py  -- re-run Day 4 five-query eval
  (severity_critical must achieve >= 1 verified doc_id to promote /api/v1/raia/analyze)
"""
import argparse
import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


def _ts() -> str:
    return datetime.now(UTC).strftime("%H:%M:%S")


def _vram_check() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            gb = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"[{_ts()}] GPU: {torch.cuda.get_device_name(0)} ({gb:.1f} GB VRAM)")
        else:
            print(
                f"[{_ts()}] WARNING: CUDA not available -- running on CPU (will be slow)"
            )
    except ImportError:
        print(f"[{_ts()}] WARNING: torch not installed yet")


def phase_colpali(pdf_dir: Path, output_dir: Path) -> None:
    import fitz  # pymupdf
    import torch
    from colpali_engine.models import ColPali, ColPaliProcessor
    from PIL import Image

    model_name = "vidore/colpali-v1.2"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[{_ts()}] Loading ColPali model ({model_name}) on {device}...")
    model = ColPali.from_pretrained(model_name, torch_dtype=torch.float16).to(device)
    processor = ColPaliProcessor.from_pretrained(model_name)
    model.eval()
    print(f"[{_ts()}] ColPali loaded")

    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    print(f"[{_ts()}] Found {len(pdf_files)} PDFs in {pdf_dir}")

    embeddings_dir = output_dir / "colpali_page_embeddings"
    embeddings_dir.mkdir(exist_ok=True)
    checkpoint_path = output_dir / "colpali_checkpoint.json"

    completed: set[str] = set()
    if checkpoint_path.exists():
        completed = set(json.loads(checkpoint_path.read_text(encoding="utf-8")))
        print(f"[{_ts()}] Resuming: {len(completed)} already done")

    errors: list[str] = []

    for i, pdf_path in enumerate(pdf_files):
        stem = pdf_path.stem
        if stem in completed:
            continue

        out_file = embeddings_dir / f"{stem}.npy"

        try:
            doc = fitz.open(str(pdf_path))
            page_images: list[Image.Image] = []
            for page in doc:
                # 150 DPI gives ColPali enough resolution without excess memory
                mat = fitz.Matrix(150 / 72, 150 / 72)
                pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_images.append(img)
            doc.close()
        except Exception as exc:
            errors.append(f"{pdf_path.name}: {exc}")
            continue

        if not page_images:
            continue

        with torch.no_grad():
            # Process in batches to avoid OOM on very long PDFs
            batch_size = 8
            all_embeddings = []
            for start in range(0, len(page_images), batch_size):
                batch = page_images[start : start + batch_size]
                inputs = processor.process_images(batch).to(device)
                emb = model(**inputs).cpu().float().numpy()
                all_embeddings.append(emb)
            page_embeddings = np.concatenate(all_embeddings, axis=0)

        np.save(str(out_file), page_embeddings)
        completed.add(stem)

        if (i + 1) % 50 == 0 or i == len(pdf_files) - 1:
            checkpoint_path.write_text(json.dumps(sorted(completed)), encoding="utf-8")
            pct = 100 * len(completed) / len(pdf_files)
            print(
                f"[{_ts()}] {len(completed)}/{len(pdf_files)} ({pct:.1f}%) -- errors: {len(errors)}",
                flush=True,
            )

    checkpoint_path.write_text(json.dumps(sorted(completed)), encoding="utf-8")

    manifest: dict[str, dict] = {}
    for npy_file in sorted(embeddings_dir.glob("*.npy")):
        arr = np.load(str(npy_file))
        manifest[npy_file.stem] = {
            "n_pages": int(arr.shape[0]),
            "dim": int(arr.shape[1]) if arr.ndim > 1 else 0,
        }
    (output_dir / "colpali_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    total_pages = sum(v["n_pages"] for v in manifest.values())
    print(f"[{_ts()}] ColPali COMPLETE: {len(manifest)} docs, {total_pages} pages")
    if errors:
        print(f"[{_ts()}] Errors ({len(errors)}):")
        for e in errors[:10]:
            print(f"  {e}")


def phase_nougat(pdf_dir: Path, output_dir: Path) -> None:
    import fitz

    nougat_dir = output_dir / "nougat_ocr"
    nougat_dir.mkdir(exist_ok=True)

    low_quality: list[Path] = []
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        try:
            doc = fitz.open(str(pdf_path))
            for page in doc:
                text = page.get_text() or ""
                has_images = bool(page.get_images())
                if len(text.strip()) < 50 and has_images:
                    low_quality.append(pdf_path)
                    break
            doc.close()
        except Exception:
            pass

    print(f"[{_ts()}] Nougat target: {len(low_quality)} PDFs with sub-threshold pages")

    errors: list[str] = []
    for j, pdf_path in enumerate(low_quality):
        out_sub = nougat_dir / pdf_path.stem
        out_sub.mkdir(exist_ok=True)
        mmd_candidate = out_sub / f"{pdf_path.stem}.mmd"
        if mmd_candidate.exists():
            continue
        result = subprocess.run(
            ["nougat", str(pdf_path), "--out", str(out_sub), "--no-skipping"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            errors.append(f"{pdf_path.name}: {result.stderr[:200]}")
        if (j + 1) % 20 == 0:
            print(f"[{_ts()}] Nougat {j+1}/{len(low_quality)}", flush=True)

    print(f"[{_ts()}] Nougat COMPLETE: {len(low_quality)} PDFs, {len(errors)} errors")
    if errors:
        for e in errors[:5]:
            print(f"  {e}")


def phase_verify(output_dir: Path) -> None:
    manifest_path = output_dir / "colpali_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        total_pages = sum(v["n_pages"] for v in manifest.values())
        emb_dim = next(iter(manifest.values()), {}).get("dim", 0)
        print(
            f"ColPali manifest: {len(manifest)} docs, {total_pages} pages, dim={emb_dim}"
        )
        sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        print(f"Manifest SHA256: {sha256}")
    else:
        print("MISSING: colpali_manifest.json")

    embeddings_dir = output_dir / "colpali_page_embeddings"
    npy_count = (
        len(list(embeddings_dir.glob("*.npy"))) if embeddings_dir.exists() else 0
    )
    print(f"Embedding files: {npy_count} .npy")

    nougat_dir = output_dir / "nougat_ocr"
    mmd_count = len(list(nougat_dir.rglob("*.mmd"))) if nougat_dir.exists() else 0
    print(f"Nougat outputs: {mmd_count} .mmd files")

    checkpoint_path = output_dir / "colpali_checkpoint.json"
    if checkpoint_path.exists():
        completed = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        print(f"Checkpoint: {len(completed)} docs processed")

    print()
    print("=" * 60)
    print("READY TO DOWNLOAD -- run locally:")
    print(
        "  rsync -avz --progress root@<INSTANCE_IP>:/outputs/ data/vectors/tcpd_colpali/"
    )
    print()
    print("AFTER DOWNLOAD -- run locally:")
    print("  python -I scripts/raia_severity_critical_gate.py")
    print("  (severity_critical must achieve >= 1 cited doc_id)")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 11 Vast.ai: ColPali + Nougat")
    parser.add_argument(
        "--pdf-dir", type=Path, required=True, help="TCPD PDF directory"
    )
    parser.add_argument(
        "--output-dir", type=Path, required=True, help="Output directory"
    )
    parser.add_argument(
        "--phase",
        choices=["colpali", "nougat", "verify", "all"],
        default="all",
        help="Phase to run (default: all)",
    )
    args = parser.parse_args()

    if not args.pdf_dir.exists():
        print(f"ERROR: --pdf-dir {args.pdf_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    _vram_check()

    if args.phase in ("colpali", "all"):
        print(f"\n[{_ts()}] === PHASE: ColPali ===")
        phase_colpali(args.pdf_dir, args.output_dir)

    if args.phase in ("nougat", "all"):
        print(f"\n[{_ts()}] === PHASE: Nougat ===")
        phase_nougat(args.pdf_dir, args.output_dir)

    if args.phase in ("verify", "all"):
        print(f"\n[{_ts()}] === PHASE: Verify ===")
        phase_verify(args.output_dir)


if __name__ == "__main__":
    main()
