#!/usr/bin/env python3
"""Run odia_legal Phase 2 L-detectors (L-1 through L-6) over the corpus.

Reads documents from oraculus_audit.db, runs all Phase 2 L-detectors on
each document, and writes LegalFinding objects to the anomalies table with
layer="legal".

Usage:
    # Dry run (print findings, no DB writes):
    python scripts/run_legal_detectors.py --dry-run

    # Run on a specific jurisdiction:
    python scripts/run_legal_detectors.py --jurisdiction fresnocounty

    # Run on a specific document:
    python scripts/run_legal_detectors.py --document-id <doc_id>

    # Full corpus run (slow -- use --limit for testing):
    python scripts/run_legal_detectors.py --limit 100

    # Full production run:
    python scripts/run_legal_detectors.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _build_resolver():
    """Build and initialize the LegalResolver. Returns resolver or None on failure."""
    try:
        from oraculus_di_auditor.legal.legal_resolver import LegalResolver

        resolver = LegalResolver()
        resolver.initialize()
        return resolver
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "LegalResolver init failed (%s) -- detectors will run without resolution",
            exc,
        )
        return None


def _load_documents(
    session, jurisdiction: str | None, document_id: str | None, limit: int | None
):
    """Query documents from DB."""
    from oraculus_di_auditor.db.models import Document

    q = session.query(Document)
    if jurisdiction:
        q = q.filter(Document.jurisdiction == jurisdiction)
    if document_id:
        q = q.filter(Document.document_id == document_id)
    if limit:
        q = q.limit(limit)
    return q.all()


def _get_document_text(doc) -> str:
    """Extract document text from metadata_json or return empty string."""
    if doc.metadata_json:
        try:
            meta = json.loads(doc.metadata_json)
            return meta.get("text", meta.get("content", meta.get("raw_text", "")))
        except (json.JSONDecodeError, KeyError):
            return ""
    return ""


def _run(args) -> None:
    from oraculus_di_auditor.db.models import Anomaly
    from oraculus_di_auditor.db.session import get_session
    from oraculus_di_auditor.legal.detectors import PHASE2_DETECTORS, DocContext

    resolver = _build_resolver()
    session = get_session()

    docs = _load_documents(
        session,
        jurisdiction=args.jurisdiction,
        document_id=args.document_id,
        limit=args.limit,
    )
    logger.info("Loaded %d documents", len(docs))

    total_findings = 0
    total_docs_with_findings = 0
    skipped = 0

    for doc in docs:
        text = _get_document_text(doc)
        if not text.strip():
            skipped += 1
            continue

        version_date = None
        if doc.version_date:
            version_date = (
                doc.version_date.date() if hasattr(doc.version_date, "date") else None
            )

        ctx = DocContext(
            document_id=doc.document_id,
            document_hash=doc.document_id,  # use doc ID as hash surrogate
            document_type=doc.document_type or "unknown",
            jurisdiction=doc.jurisdiction or "",
            authority=doc.authority,
            version_date=version_date,
            text=text,
        )

        doc_findings = []
        for detector in PHASE2_DETECTORS:
            try:
                found = detector.detect(ctx, resolver)
                doc_findings.extend(found)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Detector %s failed on %s: %s",
                    detector.detector_id,
                    doc.document_id,
                    exc,
                )

        if not doc_findings:
            continue

        total_docs_with_findings += 1
        total_findings += len(doc_findings)

        if args.dry_run:
            for f in doc_findings:
                d = f.to_anomaly_dict()
                print(
                    f"[{d['severity'].upper():8}] {d['id']} | " f"{d['issue'][:80]}..."
                )
        else:
            for f in doc_findings:
                d = f.to_anomaly_dict()
                anomaly = Anomaly(
                    document_id=doc.id,
                    anomaly_type=d["id"],
                    description=d["issue"],
                    severity=d["severity"],
                    layer=d["layer"],
                    details=json.dumps(d["details"]),
                    detected_at=datetime.now(UTC),
                )
                session.add(anomaly)

    if not args.dry_run:
        session.commit()
        logger.info("Committed %d findings to DB", total_findings)

    logger.info(
        "Done. %d docs processed | %d docs with findings | %d findings | %d skipped (no text)",
        len(docs),
        total_docs_with_findings,
        total_findings,
        skipped,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run odia_legal Phase 2 L-detectors")
    parser.add_argument("--jurisdiction", help="Filter by jurisdiction slug")
    parser.add_argument(
        "--document-id", dest="document_id", help="Run on specific document"
    )
    parser.add_argument("--limit", type=int, help="Limit number of documents processed")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print findings; do not write to DB",
    )
    args = parser.parse_args()
    _run(args)


if __name__ == "__main__":
    main()
