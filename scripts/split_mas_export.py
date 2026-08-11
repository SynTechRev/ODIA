"""
split_mas_export.py — Split an oversized jurisdiction MAS JSON into
analytically-distinct chunks for Opus upload and multi-pass analysis.

Produces two independent split axes so the same corpus can be examined
from multiple analytical angles (verification through repetition):

  AXIS 1 — Severity tier  (critical / high / medium / low)
  AXIS 2 — Detector layer (surveillance / procurement / fiscal / etc.)

Each output file is self-contained: full document context + filtered
findings for that slice.  An index file maps all pieces together.

If any chunk still exceeds MAX_MB, it is automatically sub-split into
batches of documents so no file exceeds the upload limit.

Usage:
    python scripts/split_mas_export.py
    python scripts/split_mas_export.py --input data/mas_export/fresnocounty_MAS.json
    python scripts/split_mas_export.py --input data/mas_export/fresnocounty_MAS.json --out data/mas_export/fresnocounty_splits
    python scripts/split_mas_export.py --max-mb 8

Output (example for fresnocounty):
    fresnocounty_splits/
        SPLIT_INDEX.json                    <- read this first
        severity_CRITICAL.json
        severity_HIGH.json
        severity_MEDIUM.json
        severity_LOW.json
        layer_surveillance.json
        layer_procurement.json
        layer_fiscal.json
        layer_governance.json
        layer_administrative.json
        ... (one per detected layer)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


MAX_MB_DEFAULT = 8.0
SEVERITY_ORDER = ["critical", "high", "medium", "low"]


def load_mas(path: Path) -> dict:
    print(f"Loading {path.name} ({path.stat().st_size / (1024*1024):.1f} MB)...")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    docs = data.get("documents", [])
    total_findings = sum(len(d.get("findings", [])) for d in docs)
    print(f"  {len(docs):,} documents / {total_findings:,} findings loaded")
    return data


def write_chunk(path: Path, payload: dict) -> float:
    """Write JSON chunk and return size in MB."""
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path.stat().st_size / (1024 * 1024)


def slice_by_filter(
    jurisdiction: str,
    all_docs: list[dict],
    filter_key: str,
    filter_val: str,
    axis: str,
    source_summary: dict,
) -> dict:
    """
    Return a MAS-structured dict containing only documents that have at
    least one finding matching filter_key == filter_val.  Within each
    document, only the matching findings are included.
    """
    filtered_docs = []
    for doc in all_docs:
        matching = [
            f for f in doc.get("findings", [])
            if f.get(filter_key) == filter_val
        ]
        if not matching:
            continue
        filtered_docs.append({**doc, "findings": matching})

    if not filtered_docs:
        return {}

    all_findings = [f for d in filtered_docs for f in d["findings"]]
    sev_counts = Counter(f["severity"] for f in all_findings)
    layer_counts = Counter(f["layer"] for f in all_findings)

    return {
        "export_timestamp": datetime.now().isoformat(),
        "jurisdiction": jurisdiction,
        "split_axis": axis,
        "split_value": filter_val,
        "parent_summary": {
            "total_docs_in_full_corpus": source_summary.get("document_count", 0),
            "total_findings_in_full_corpus": source_summary.get("finding_count", 0),
        },
        "slice_summary": {
            "documents_in_slice": len(filtered_docs),
            "findings_in_slice": len(all_findings),
            "severity_breakdown": {s: sev_counts.get(s, 0) for s in SEVERITY_ORDER},
            "layer_breakdown": dict(layer_counts.most_common()),
        },
        "documents": filtered_docs,
    }


def sub_split(
    out_dir: Path,
    stem: str,
    payload: dict,
    max_mb: float,
) -> list[dict]:
    """
    Split docs into batches that stay under max_mb.
    Uses finding count as the budget unit (actual size driver), then
    verifies real file size and further splits any batch still over limit.
    Returns a list of index records for all written files.
    """
    docs = payload["documents"]
    total_findings = sum(len(d.get("findings", [])) for d in docs)
    total_size_mb = len(json.dumps(payload, indent=2, default=str).encode("utf-8")) / (1024 * 1024)

    # Budget: findings per MB, with a safety margin
    findings_per_mb = (total_findings / total_size_mb) if total_size_mb > 0 else 500
    target_findings = max(50, int(max_mb * findings_per_mb * 0.70))

    # Build batches by finding-count budget
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_n = 0
    for doc in docs:
        n = len(doc.get("findings", []))
        if current_n + n > target_findings and current:
            batches.append(current)
            current = [doc]
            current_n = n
        else:
            current.append(doc)
            current_n += n
    if current:
        batches.append(current)

    records = []
    part = 0
    for batch_docs in batches:
        part += 1
        all_findings = [f for d in batch_docs for f in d["findings"]]
        sev = Counter(f["severity"] for f in all_findings)

        # Build payload copy with updated slice_summary
        slice_summary = {
            **payload.get("slice_summary", {}),
            "documents_in_slice": len(batch_docs),
            "findings_in_slice": len(all_findings),
            "severity_breakdown": {s: sev.get(s, 0) for s in SEVERITY_ORDER},
        }
        batch_payload = {
            **{k: v for k, v in payload.items() if k not in ("documents", "slice_summary")},
            "slice_summary": slice_summary,
            "sub_split_part": part,
            "sub_split_total_source_docs": len(docs),
            "documents": batch_docs,
        }

        fname = out_dir / f"{stem}_part{part:02d}.json"
        size_mb = write_chunk(fname, batch_payload)

        # If still over limit, recursively halve (last-resort safety net)
        if size_mb > max_mb and len(batch_docs) > 1:
            fname.unlink()
            mid = len(batch_docs) // 2
            for sub_idx, sub_docs in enumerate([batch_docs[:mid], batch_docs[mid:]], 1):
                sub_findings = [f for d in sub_docs for f in d["findings"]]
                sub_sev = Counter(f["severity"] for f in sub_findings)
                sub_summary = {
                    **payload.get("slice_summary", {}),
                    "documents_in_slice": len(sub_docs),
                    "findings_in_slice": len(sub_findings),
                    "severity_breakdown": {s: sub_sev.get(s, 0) for s in SEVERITY_ORDER},
                }
                sub_payload = {
                    **{k: v for k, v in payload.items() if k not in ("documents", "slice_summary")},
                    "slice_summary": sub_summary,
                    "sub_split_part": f"{part}{chr(96 + sub_idx)}",
                    "sub_split_total_source_docs": len(docs),
                    "documents": sub_docs,
                }
                sub_fname = out_dir / f"{stem}_part{part:02d}{chr(96 + sub_idx)}.json"
                sub_size = write_chunk(sub_payload_path := sub_fname, sub_payload)
                print(f"    {sub_fname.name}  {sub_size:.1f} MB  ({len(sub_docs)} docs / {len(sub_findings)} findings)")
                records.append({
                    "file": sub_fname.name,
                    "size_mb": round(sub_size, 2),
                    "documents": len(sub_docs),
                    "findings": len(sub_findings),
                    "severity_breakdown": {s: sub_sev.get(s, 0) for s in SEVERITY_ORDER},
                })
        else:
            print(f"    {fname.name}  {size_mb:.1f} MB  ({len(batch_docs)} docs / {len(all_findings)} findings)")
            records.append({
                "file": fname.name,
                "size_mb": round(size_mb, 2),
                "documents": len(batch_docs),
                "findings": len(all_findings),
                "severity_breakdown": {s: sev.get(s, 0) for s in SEVERITY_ORDER},
            })

    return records


def split_mas(input_path: Path, out_dir: Path, max_mb: float) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = load_mas(input_path)

    jurisdiction = data.get("jurisdiction", input_path.stem.replace("_MAS", ""))
    all_docs = data.get("documents", [])
    source_summary = data.get("summary", {})
    jur_slug = jurisdiction.lower().replace(" ", "_").replace("/", "-")

    # Collect all layers present in the corpus
    all_layers: set[str] = set()
    for doc in all_docs:
        for f in doc.get("findings", []):
            if f.get("layer"):
                all_layers.add(f["layer"])
    layers_sorted = sorted(all_layers)

    print(f"\nJurisdiction: {jurisdiction}")
    print(f"Severity axes: {SEVERITY_ORDER}")
    print(f"Layer axes ({len(layers_sorted)}): {', '.join(layers_sorted)}")
    print(f"Max file size: {max_mb} MB")
    print(f"Output: {out_dir}")
    print()

    index_records: dict[str, list[dict]] = {
        "severity": [],
        "layer": [],
    }

    # ── AXIS 1: Severity splits ──────────────────────────────────────────────
    print("--- AXIS 1: Severity ---")
    for sev in SEVERITY_ORDER:
        payload = slice_by_filter(
            jurisdiction, all_docs,
            filter_key="severity", filter_val=sev,
            axis="severity", source_summary=source_summary,
        )
        if not payload:
            print(f"  severity={sev:8s}  0 findings — skipped")
            continue

        n_docs = payload["slice_summary"]["documents_in_slice"]
        n_find = payload["slice_summary"]["findings_in_slice"]
        stem = f"severity_{sev.upper()}"
        fname = out_dir / f"{stem}.json"

        # Test size before writing
        size_estimate = len(json.dumps(payload, indent=2, default=str).encode("utf-8")) / (1024 * 1024)
        if size_estimate > max_mb:
            print(f"  severity={sev:8s}  {n_docs:,} docs / {n_find:,} findings  -> {size_estimate:.1f} MB  [SUB-SPLITTING]")
            recs = sub_split(out_dir, stem, payload, max_mb)
            index_records["severity"].extend(recs)
        else:
            size_mb = write_chunk(fname, payload)
            print(f"  severity={sev:8s}  {n_docs:,} docs / {n_find:,} findings  -> {fname.name}  {size_mb:.1f} MB")
            index_records["severity"].append({
                "file": fname.name,
                "size_mb": round(size_mb, 2),
                "documents": n_docs,
                "findings": n_find,
                "severity_breakdown": payload["slice_summary"]["severity_breakdown"],
            })

    # ── AXIS 2: Layer splits ─────────────────────────────────────────────────
    print("\n--- AXIS 2: Detector Layer ---")
    for layer in layers_sorted:
        payload = slice_by_filter(
            jurisdiction, all_docs,
            filter_key="layer", filter_val=layer,
            axis="layer", source_summary=source_summary,
        )
        if not payload:
            continue

        n_docs = payload["slice_summary"]["documents_in_slice"]
        n_find = payload["slice_summary"]["findings_in_slice"]
        layer_slug = layer.lower().replace(" ", "_").replace("/", "-").replace(":", "")
        stem = f"layer_{layer_slug}"
        fname = out_dir / f"{stem}.json"

        size_estimate = len(json.dumps(payload, indent=2, default=str).encode("utf-8")) / (1024 * 1024)
        if size_estimate > max_mb:
            print(f"  layer={layer:30s}  {n_docs:,} docs / {n_find:,} findings  -> {size_estimate:.1f} MB  [SUB-SPLITTING]")
            recs = sub_split(out_dir, stem, payload, max_mb)
            index_records["layer"].extend(recs)
        else:
            size_mb = write_chunk(fname, payload)
            print(f"  layer={layer:30s}  {n_docs:,} docs / {n_find:,} findings  -> {fname.name}  {size_mb:.1f} MB")
            index_records["layer"].append({
                "file": fname.name,
                "size_mb": round(size_mb, 2),
                "documents": n_docs,
                "findings": n_find,
                "layer": layer,
            })

    # ── SPLIT_INDEX.json ─────────────────────────────────────────────────────
    all_sev_findings = sum(r["findings"] for r in index_records["severity"] if "findings" in r)
    all_layer_findings = sum(r["findings"] for r in index_records["layer"] if "findings" in r)

    split_index = {
        "export_timestamp": datetime.now().isoformat(),
        "jurisdiction": jurisdiction,
        "source_file": input_path.name,
        "source_size_mb": round(input_path.stat().st_size / (1024 * 1024), 2),
        "max_chunk_mb": max_mb,
        "analysis_note": (
            "Two independent split axes are provided so the same corpus can be "
            "examined from multiple analytical angles. Each file is self-contained. "
            "AXIS 1 (severity) enables tier-by-tier risk triage. "
            "AXIS 2 (layer) enables detector-specific deep-dives. "
            "A document appearing in both a severity file and a layer file is the same "
            "document — cross-referencing the two axes is the verification mechanism."
        ),
        "how_to_use": [
            "1. Start with severity_CRITICAL.json — highest priority findings first",
            "2. Run severity_HIGH.json as second pass for completeness",
            "3. Use layer_* files for detector-specific analysis (surveillance, procurement, etc.)",
            "4. Cross-reference: a document in severity_CRITICAL + layer_surveillance = apex target",
            "5. Medium and Low severity passes complete the full-corpus picture",
        ],
        "totals": {
            "source_documents": source_summary.get("document_count", 0),
            "source_findings": source_summary.get("finding_count", 0),
            "severity_axis_files": len(index_records["severity"]),
            "layer_axis_files": len(index_records["layer"]),
            "total_split_files": len(index_records["severity"]) + len(index_records["layer"]),
        },
        "severity_axis": index_records["severity"],
        "layer_axis": index_records["layer"],
    }

    idx_path = out_dir / "SPLIT_INDEX.json"
    idx_path.write_text(json.dumps(split_index, indent=2, default=str), encoding="utf-8")

    # ── Final summary ────────────────────────────────────────────────────────
    all_files = sorted(out_dir.glob("*.json"))
    total_split_kb = sum(f.stat().st_size for f in all_files) // 1024

    print(f"\n{'='*60}")
    print(f"Split complete — {jurisdiction}")
    print(f"{'='*60}")
    print(f"  Source:        {input_path.name}  ({input_path.stat().st_size // (1024*1024)} MB)")
    print(f"  Output files:  {len(all_files)}  ({total_split_kb:,} KB total)")
    print(f"  Max chunk:     {max_mb} MB")
    print()
    print(f"{'File':<45}  {'MB':>6}")
    print("-" * 55)
    for f in all_files:
        mb = f.stat().st_size / (1024 * 1024)
        flag = " *** OVER LIMIT" if mb > max_mb else ""
        print(f"  {f.name:<43}  {mb:>6.2f}{flag}")
    print()
    print(f"Upload order for Opus multi-pass analysis:")
    print(f"  1. SPLIT_INDEX.json  (read first — maps all files)")
    print(f"  2. severity_CRITICAL.json")
    print(f"  3. severity_HIGH.json")
    print(f"  4. layer_surveillance.json  (or whichever layer is priority)")
    print(f"  5. Remaining severity and layer files as needed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a large jurisdiction MAS JSON into Opus-uploadable analytical chunks"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("data/mas_export/fresnocounty_MAS.json"),
        help="Source MAS JSON file (default: data/mas_export/fresnocounty_MAS.json)",
    )
    parser.add_argument(
        "--out", "-o",
        type=Path,
        default=None,
        help="Output directory (default: data/mas_export/{jurisdiction}_splits/)",
    )
    parser.add_argument(
        "--max-mb",
        type=float,
        default=MAX_MB_DEFAULT,
        help=f"Maximum output file size in MB (default: {MAX_MB_DEFAULT})",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Default output dir: same parent as input, named {stem}_splits/
    if args.out is None:
        stem = args.input.stem.replace("_MAS", "")
        args.out = args.input.parent / f"{stem}_splits"

    split_mas(args.input, args.out, args.max_mb)


if __name__ == "__main__":
    main()
