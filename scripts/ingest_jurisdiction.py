"""ingest_jurisdiction — operator CLI for bringing up a new jurisdiction.

Drives a full ingest pass against ONE jurisdiction:

  - Discover document URLs via an adapter or an explicit URL list
  - Download each via the adapter's session (cookie-bearing where needed)
  - Run the v3.2.5 Tier-1 pipeline on each (extract → analyze → score)
  - Persist via webhook._persist_tier1_result (same DB shape as the
    /scrape-and-ingest-async path)
  - Print a summary

Designed to be re-runnable: docs already in SeenHash are skipped.
Progress is persisted to a per-jurisdiction JSON log so a CTRL-C +
restart resumes where it left off.

Usage:
    # Via a registered adapter (currently: questys)
    python scripts/ingest_jurisdiction.py \\
        --jurisdiction-id kern-county \\
        --adapter questys \\
        --portal-url https://publicdocs.example.gov/questys.cmx.webclient/

    # Via an explicit URL list (one URL per line)
    python scripts/ingest_jurisdiction.py \\
        --jurisdiction-id porterville \\
        --url-file urls.txt

    # Filter to specific extensions
    python scripts/ingest_jurisdiction.py \\
        --jurisdiction-id tulare-county \\
        --adapter questys \\
        --portal-url https://publicdocs.co.tulare.ca.us/questys.cmx.webclient/ \\
        --extensions pdf,doc,docx,tif

The script lives in scripts/ rather than as a CLI entry point because
ingest is an operator workflow, not a runtime feature of the API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)


_DEFAULT_EXTENSIONS = ("pdf", "doc", "docx", "html", "htm", "tif", "tiff")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ingest_jurisdiction",
        description="Drive a full ingest pass for one jurisdiction.",
    )
    p.add_argument(
        "--jurisdiction-id",
        required=True,
        help="DB jurisdiction label (e.g. 'kern-county').",
    )
    p.add_argument(
        "--adapter",
        choices=("questys", "url-list"),
        default="url-list",
        help="Discovery source: 'questys' or 'url-list'.",
    )
    p.add_argument(
        "--portal-url",
        help="Required for --adapter questys (Questys CMX portal URL).",
    )
    p.add_argument(
        "--url-file",
        type=Path,
        help="Required for --adapter url-list (one URL per line).",
    )
    p.add_argument(
        "--extensions",
        default=",".join(_DEFAULT_EXTENSIONS),
        help=f"Comma-separated extensions; default {','.join(_DEFAULT_EXTENSIONS)}",
    )
    p.add_argument(
        "--log-path",
        type=Path,
        help="Resume-log JSON path. Default: _ingest_<jurisdiction_id>.json",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Stop after N documents (0 = no limit). Useful for smoke tests.",
    )
    p.add_argument(
        "--pause-sec",
        type=float,
        default=3.0,
        help="Sleep between per-document HTTP fetches (politeness).",
    )
    p.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable INFO-level logging from the adapter and pipeline.",
    )
    return p


def _resolve_log_path(jurisdiction_id: str, override: Path | None) -> Path:
    return override or Path(f"_ingest_{jurisdiction_id}.json")


def _load_log(log_path: Path) -> dict:
    if log_path.exists():
        try:
            return json.loads(log_path.read_text(encoding="utf-8-sig"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("log %s parse failed: %s; starting fresh", log_path, exc)
    return {}


def _save_log(log_path: Path, data: dict) -> None:
    log_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _discover_questys(
    portal_url: str, extensions: set[str]
) -> list[tuple[str, str, str]]:
    """Return [(doc_id, filename, ext), ...] via QuestysAdapter."""
    from oraculus_di_auditor.adapters.questys_adapter import QuestysAdapter

    a = QuestysAdapter(portal_url=portal_url)
    a.warm_session()
    catalog = a.harvest_ids()
    out = []
    for did, meta in catalog.items():
        if extensions and meta.ext not in extensions:
            continue
        out.append((did, meta.filename, meta.ext))
    return out, a  # return adapter so caller can reuse the session


def _discover_url_list(url_file: Path) -> list[tuple[str, str, str]]:
    """Return [(url, filename, ext), ...] from a one-URL-per-line file."""
    out = []
    for line in url_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Best-effort filename + extension from the URL tail
        filename = line.rsplit("/", 1)[-1] or "unknown"
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        out.append((line, filename, ext))
    return out


def _fetch_url(url: str) -> bytes | None:
    """Plain HTTP GET (Tier-1) for the --adapter url-list path."""
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return r.read()
    except Exception as exc:  # noqa: BLE001
        logger.warning("url-list fetch failed for %s: %s", url, exc)
        return None


def _ingest_one(
    file_bytes: bytes, filename: str, jurisdiction_id: str
) -> tuple[int, float, str] | None:
    """Run pipeline + persist. Returns (findings_count, score, sha256) or None."""
    from oraculus_di_auditor.interface.routes.webhook import (
        _dedup_check,
        _persist_tier1_result,
        _record_seen_hash,
        _run_tier1_pipeline,
    )

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    if _dedup_check(sha256):
        return (0, 1.0, sha256)  # marker: already seen
    try:
        result = _run_tier1_pipeline(
            file_bytes=file_bytes, filename=filename, jurisdiction_id=jurisdiction_id
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("pipeline failed for %s: %s", filename, exc)
        return None
    try:
        doc_id = (result.get("document") or {}).get("document_id")
        _record_seen_hash(
            sha256=sha256, document_id=doc_id, jurisdiction_id=jurisdiction_id
        )
        _persist_tier1_result(
            sha256=sha256,
            filename=filename,
            jurisdiction_id=jurisdiction_id,
            result=result,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("persist failed for %s: %s", filename, exc)
    findings = (result.get("findings") or {}).get("count", 0)
    score = result.get("recursive_scalar_score", 1.0)
    return (findings, score, sha256)


def _discover_targets(args, extensions, adapter_holder):
    """Resolve the candidate target list + the adapter (if any).

    adapter_holder is a single-element list used as an out-parameter so
    the caller can keep a reference to the adapter session for downloads.
    Returns (targets, error_code) — error_code is 0 on success, non-zero
    on a CLI usage error that should abort main.
    """
    if args.adapter == "questys":
        if not args.portal_url:
            print(
                "ERROR: --portal-url required when --adapter questys", file=sys.stderr
            )
            return [], 2
        print(f"[discover] Questys portal: {args.portal_url}")
        targets, adapter = _discover_questys(args.portal_url, extensions)
        adapter_holder[0] = adapter
        return targets, 0
    # url-list path
    if not args.url_file:
        print("ERROR: --url-file required when --adapter url-list", file=sys.stderr)
        return [], 2
    print(f"[discover] url-list: {args.url_file}")
    targets = _discover_url_list(args.url_file)
    if extensions:
        targets = [(u, fn, e) for u, fn, e in targets if e in extensions]
    return targets, 0


def _process_one_target(
    target, idx, total, args, adapter, log, log_path
) -> tuple[str, int]:
    """Fetch + ingest a single target. Returns ('ok', findings) /
    ('failed', 0) / ('skipped', 0). Mutates log; does NOT save_log
    (caller batches the save)."""
    key, filename, ext = target

    # Fetch
    if adapter is not None:
        dl = adapter.download(key)
        content = dl.content if dl is not None else None
    else:
        content = _fetch_url(key)

    if content is None:
        log[key] = {"status": "download_failed", "filename": filename, "ext": ext}
        _save_log(log_path, log)
        print(f"  [{idx:>4}/{total}] {filename[:40]:<40} FAIL fetch")
        return ("failed", 0)

    # Ingest
    ingested = _ingest_one(content, filename, args.jurisdiction_id)
    if ingested is None:
        log[key] = {
            "status": "pipeline_failed",
            "filename": filename,
            "ext": ext,
            "bytes": len(content),
        }
        _save_log(log_path, log)
        return ("failed", 0)

    findings, score, sha256 = ingested
    log[key] = {
        "status": "completed",
        "filename": filename,
        "ext": ext,
        "bytes": len(content),
        "findings": findings,
        "score": score,
        "sha256": sha256,
    }
    print(
        f"  [{idx:>4}/{total}] {filename[:40]:<40} "
        f"OK {len(content):>9}B findings={findings} score={score:.3f}"
    )
    return ("ok", findings)


def main(argv: list[str] | None = None) -> int:
    args = _build_argparser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # CRITICAL: init_db before importing webhook helpers (the singleton
    # session is created lazily; if we don't trigger init the persistence
    # calls will silently fail).
    from oraculus_di_auditor.db.session import init_db

    init_db()

    extensions = {
        e.strip().lstrip(".").lower() for e in args.extensions.split(",") if e.strip()
    }
    log_path = _resolve_log_path(args.jurisdiction_id, args.log_path)
    log = _load_log(log_path)

    # Discovery
    adapter_holder: list = [None]
    targets, err = _discover_targets(args, extensions, adapter_holder)
    if err:
        return err
    adapter = adapter_holder[0]
    print(f"  discovered: {len(targets)} candidate documents")

    # Filter out targets we've already completed (resume)
    todo = [
        t
        for t in targets
        if not (
            log.get(t[0], {}).get("status") == "completed"
            and log[t[0]].get("findings", 0) >= 0
        )
    ]
    print(f"  to ingest: {len(todo)} (after dedup skip)")

    if args.limit > 0:
        todo = todo[: args.limit]
        print(f"  limited to: {len(todo)} for this run")

    # Ingest loop
    completed = 0
    failed = 0
    total_findings = 0
    start = time.time()

    for i, target in enumerate(todo, 1):
        if i > 1:
            time.sleep(args.pause_sec)
        outcome, findings = _process_one_target(
            target, i, len(todo), args, adapter, log, log_path
        )
        if outcome == "ok":
            completed += 1
            total_findings += findings
        elif outcome == "failed":
            failed += 1
        if i % 5 == 0:
            _save_log(log_path, log)

    _save_log(log_path, log)
    elapsed = time.time() - start

    print()
    print("=== DONE ===")
    print(f"  jurisdiction:    {args.jurisdiction_id}")
    print(f"  completed:       {completed}")
    print(f"  failed:          {failed}")
    print(f"  total findings:  {total_findings}")
    print(f"  elapsed:         {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  log:             {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
