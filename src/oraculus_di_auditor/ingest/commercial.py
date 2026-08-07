"""12-step commercial document ingest pipeline (C.O.N.T.R.A. Phase G).

ingest_commercial_document() is the single entry point for adding a commercial
contract, ToS, privacy notice, or EULA to the C.O.N.T.R.A. corpus.

Pipeline steps:
  1.  Detect format (PDF vs text); extract text via ingestion engine
  2.  SHA-256 content hash
  3.  Duplicate check (idempotent — re-ingesting same content returns early)
  4.  Provenance record construction
  5.  Entity resolution (canonical name -> entity_id via EntityRegistry)
  6.  L-1 through L-10 legal detectors (odia_legal submodule; skipped if absent)
  7.  L-11 through L-20 C.O.N.T.R.A. detectors
  8.  CASI score computation (compute_casi)
  9.  Wayback snapshot retrieval (optional)
  10. DB insert: CommercialDocument + ContraFinding rows + CasiScore
  11. Analytical Card DOCX generation (build_analytical_card)
  12. Return IngestionResult

Constraints:
  - Do NOT hardcode API keys; pass llm_api_key explicitly or via env var
  - Do NOT use datetime.utcnow(); use datetime.now(UTC)
  - Open all text files with encoding='utf-8'
  - Entity names from CLAUDE.md security rules — no jurisdiction-specific literals
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------


@dataclass
class IngestionResult:
    """Result returned by ingest_commercial_document()."""

    document_hash: str
    entity_id: str | None
    entity_name: str
    doc_type: str
    text_length: int
    extraction_method: str
    l1_l10_findings: int
    l11_l20_findings: int
    total_findings: int
    casi_aggregate: int
    casi_band: str
    wayback_url: str | None
    analytical_card_path: str | None
    skipped_duplicate: bool = False
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Step 1: Text extraction
# ---------------------------------------------------------------------------


def _extract_text(source_path: Path) -> tuple[str, str]:
    """Extract text from PDF or plain text source. Returns (text, method)."""
    suffix = source_path.suffix.lower()

    if suffix == ".pdf":
        try:
            from ..ingestion.engine import (  # noqa: PLC0415
                TextExtractionResult,
                extract_text_from_pdf_with_metadata,
            )

            result: TextExtractionResult = extract_text_from_pdf_with_metadata(
                source_path
            )
            return result.text, result.method
        except ImportError:
            pass
        # Fallback: try pypdf directly
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(source_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text, "pypdf"
        except Exception as exc:
            log.warning("PDF extraction failed for %s: %s", source_path, exc)
            return "", "failed"
    else:
        with source_path.open("r", encoding="utf-8") as fh:
            return fh.read(), "plaintext"


# ---------------------------------------------------------------------------
# Step 2: SHA-256 hash
# ---------------------------------------------------------------------------


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# ---------------------------------------------------------------------------
# Step 6: L-1 through L-10 legal detectors (odia_legal, optional)
# ---------------------------------------------------------------------------


def _run_legal_detectors(doc_text: str, doc_meta: dict) -> list[Any]:
    try:
        from odia_legal import get_detectors as _get_legal_detectors

        findings = []
        for detector in _get_legal_detectors():
            findings.extend(detector.scan(doc_text, doc_meta))
        return findings
    except ImportError:
        return []


# ---------------------------------------------------------------------------
# Step 7: L-11 through L-20 C.O.N.T.R.A. detectors
# ---------------------------------------------------------------------------

_CONTRA_DETECTOR_CLASSES = [
    "L11ArbitrationArchitecture",
    "L12ChoiceOfLawForum",
    "L13UnilateralModification",
    "L14DataCollectionDepth",
    "L15DataRetention",
    "L16OnwardTransfer",
    "L17MlAiTraining",
    "L18RemedyForeclosure",
    "L19EnforcementAsymmetry",
    "L20DarkPattern",
]


def _run_contra_detectors(doc_text: str, doc_meta: dict) -> list[Any]:
    import importlib

    contra_module = importlib.import_module("oraculus_di_auditor.contra")
    findings = []
    for cls_name in _CONTRA_DETECTOR_CLASSES:
        cls = getattr(contra_module, cls_name, None)
        if cls is None:
            continue
        try:
            detector = cls()
            findings.extend(detector.scan(doc_text, doc_meta))
        except Exception as exc:
            log.warning("Detector %s raised: %s", cls_name, exc)
    return findings


# ---------------------------------------------------------------------------
# Step 10: DB persistence helpers
# ---------------------------------------------------------------------------


def _persist(
    session: Session,
    document_hash: str,
    entity_id: str | None,
    doc_type: str,
    effective_date: datetime | None,
    version_label: str | None,
    source_url: str | None,
    wayback_url: str | None,
    retrieval_ts: datetime,
    legal_findings: list[Any],
    contra_findings: list[Any],
    casi_axes: Any,
) -> None:
    from ..db.models import CasiScore, CommercialDocument, ContraFinding

    doc = CommercialDocument(
        document_hash=document_hash,
        entity_id=entity_id,
        doc_type=doc_type,
        effective_date=effective_date,
        version_label=version_label,
        source_url=source_url,
        wayback_url=wayback_url,
        retrieval_ts=retrieval_ts,
        ingest_ts=datetime.now(UTC),
    )
    session.add(doc)
    session.flush()

    all_findings = list(legal_findings) + list(contra_findings)
    for finding in all_findings:
        db_dict = finding.to_db_dict()
        db_dict["document_hash"] = document_hash
        row = ContraFinding(**db_dict)
        session.add(row)

    score = CasiScore(
        document_hash=document_hash,
        remedy_foreclosure=casi_axes.remedy_foreclosure,
        data_extraction_depth=casi_axes.data_extraction_depth,
        modification_and_consent=casi_axes.modification_and_consent,
        procedural_adhesion=casi_axes.procedural_adhesion,
        enforcement_cost_asymmetry=casi_axes.enforcement_cost_asymmetry,
        aggregate=casi_axes.aggregate,
        band=casi_axes.band,
        framework_version="1.0",
        computed_at=datetime.now(UTC),
    )
    session.add(score)
    session.commit()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def ingest_commercial_document(
    source_path: str | Path,
    entity_name: str,
    doc_type: str,
    session: Session,
    effective_date: datetime | None = None,
    version_label: str | None = None,
    source_url: str | None = None,
    output_dir: str | Path | None = None,
    fetch_wayback: bool = True,
    wayback_years: int = 3,
    entity_registry: Any | None = None,
) -> IngestionResult:
    """Ingest a commercial document through the full C.O.N.T.R.A. pipeline.

    Arguments:
        source_path     -- local file to ingest (PDF or text)
        entity_name     -- company name; resolved to entity_id via registry
        doc_type        -- 'tos', 'privacy_notice', 'arbitration', 'employment', 'eula'
        session         -- active SQLAlchemy session
        effective_date  -- document effective/published date (UTC)
        version_label   -- human-readable version string (e.g. 'v2024-01')
        source_url      -- canonical URL where the document was retrieved
        output_dir      -- directory for the Analytical Card DOCX output
        fetch_wayback   -- whether to retrieve a Wayback snapshot URL
        wayback_years   -- how many prior years to check on Wayback
        entity_registry -- EntityRegistry instance; auto-constructed if None

    Returns IngestionResult with all pipeline outputs.
    Raises ValueError if source_path does not exist.
    """
    source_path = Path(source_path)
    if not source_path.exists():
        raise ValueError(f"Source file not found: {source_path}")

    warnings: list[str] = []

    # ------------------------------------------------------------------
    # Step 1: Extract text
    # ------------------------------------------------------------------
    doc_text, extraction_method = _extract_text(source_path)
    if not doc_text.strip():
        warnings.append(f"Extraction produced empty text via '{extraction_method}'")

    # ------------------------------------------------------------------
    # Step 2: SHA-256 hash of raw bytes
    # ------------------------------------------------------------------
    raw_bytes = source_path.read_bytes()
    document_hash = _sha256(raw_bytes)

    # ------------------------------------------------------------------
    # Step 3: Duplicate check
    # ------------------------------------------------------------------
    from ..db.models import CommercialDocument

    existing = session.get(CommercialDocument, document_hash)
    if existing is not None:
        log.info("Duplicate ingest skipped: %s already in DB", document_hash[:16])

        casi_row = existing.casi_score
        return IngestionResult(
            document_hash=document_hash,
            entity_id=existing.entity_id,  # type: ignore[arg-type]
            entity_name=entity_name,
            doc_type=existing.doc_type,
            text_length=len(doc_text),
            extraction_method=extraction_method,
            l1_l10_findings=0,
            l11_l20_findings=0,
            total_findings=len(existing.findings),
            casi_aggregate=casi_row.aggregate if casi_row else 0,
            casi_band=casi_row.band if casi_row else "Unknown",
            wayback_url=existing.wayback_url,
            analytical_card_path=None,
            skipped_duplicate=True,
        )

    retrieval_ts = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Step 4: Provenance record (in-memory only; no Provenance table for commercial docs)
    # ------------------------------------------------------------------
    provenance_note = (
        f"sha256:{document_hash} size:{len(raw_bytes)} method:{extraction_method}"
    )
    log.debug("Provenance: %s", provenance_note)

    # ------------------------------------------------------------------
    # Step 5: Entity resolution
    # ------------------------------------------------------------------
    from ..entity.registry import Entity, EntityRegistry

    if entity_registry is None:
        entity_registry = EntityRegistry(db_session=session)

    entity = entity_registry.resolve(entity_name)
    if entity is None:
        # Auto-create entity so entity_id (NOT NULL FK) can be satisfied.
        # Log the auto-creation so operators can review unrecognized entities.
        entity = Entity.new(canonical_name=entity_name, in_contra_corpus=True)
        entity_registry.add_entity(entity)
        warnings.append(
            f"Entity '{entity_name}' not found in registry; "
            f"auto-created with entity_id={entity.entity_id}"
        )
    entity_id: str = entity.entity_id

    # ------------------------------------------------------------------
    # Step 6: L-1 through L-10 legal detectors (optional)
    # ------------------------------------------------------------------
    doc_meta: dict = {
        "entity_id": entity_id,
        "entity_name": entity_name,
        "doc_type": doc_type,
        "effective_date": effective_date.isoformat() if effective_date else None,
        "document_hash": document_hash,
        "source_url": source_url,
    }
    legal_findings = _run_legal_detectors(doc_text, doc_meta)
    if not legal_findings:
        log.debug("odia_legal not available or returned no findings")

    # ------------------------------------------------------------------
    # Step 7: L-11 through L-20 C.O.N.T.R.A. detectors
    # ------------------------------------------------------------------
    contra_findings = _run_contra_detectors(doc_text, doc_meta)

    # ------------------------------------------------------------------
    # Step 8: CASI score computation
    # ------------------------------------------------------------------
    from ..scoring.casi import compute_casi

    casi_axes = compute_casi(contra_findings)

    # ------------------------------------------------------------------
    # Step 9: Wayback snapshot retrieval
    # ------------------------------------------------------------------
    wayback_url: str | None = None
    if fetch_wayback and source_url:
        try:
            from .wayback import find_capture

            capture = find_capture(
                source_url, target_date=effective_date or retrieval_ts
            )
            if capture:
                wayback_url = capture.snapshot_url
        except Exception as exc:
            warnings.append(f"Wayback lookup failed: {exc}")

    # ------------------------------------------------------------------
    # Step 10: DB insert
    # ------------------------------------------------------------------
    _persist(
        session=session,
        document_hash=document_hash,
        entity_id=entity_id,
        doc_type=doc_type,
        effective_date=effective_date,
        version_label=version_label,
        source_url=source_url,
        wayback_url=wayback_url,
        retrieval_ts=retrieval_ts,
        legal_findings=legal_findings,
        contra_findings=contra_findings,
        casi_axes=casi_axes,
    )

    # ------------------------------------------------------------------
    # Step 11: Analytical Card DOCX
    # ------------------------------------------------------------------
    analytical_card_path: str | None = None
    if output_dir is not None:
        try:
            from ..cards.analytical_card import (
                AnalyticalCardInput,
                build_analytical_card,
            )

            card_input = AnalyticalCardInput(
                entity_name=entity_name,
                entity_id=entity_id,
                doc_type=doc_type,
                effective_date=(
                    effective_date.strftime("%Y-%m-%d") if effective_date else None
                ),
                version_label=version_label,
                document_hash=document_hash,
                source_url=source_url,
                wayback_url=wayback_url,
                findings=contra_findings,
                casi_axes=casi_axes,
            )
            analytical_card_path = build_analytical_card(card_input, output_dir)
        except Exception as exc:
            warnings.append(f"Analytical Card generation failed: {exc}")
            log.warning("Analytical Card failed for %s: %s", document_hash[:16], exc)

    # ------------------------------------------------------------------
    # Step 12: Return IngestionResult
    # ------------------------------------------------------------------
    if warnings:
        for w in warnings:
            log.warning("[ingest] %s", w)

    return IngestionResult(
        document_hash=document_hash,
        entity_id=entity_id,
        entity_name=entity_name,
        doc_type=doc_type,
        text_length=len(doc_text),
        extraction_method=extraction_method,
        l1_l10_findings=len(legal_findings),
        l11_l20_findings=len(contra_findings),
        total_findings=len(legal_findings) + len(contra_findings),
        casi_aggregate=casi_axes.aggregate,
        casi_band=casi_axes.band,
        wayback_url=wayback_url,
        analytical_card_path=analytical_card_path,
        skipped_duplicate=False,
        warnings=warnings,
    )
