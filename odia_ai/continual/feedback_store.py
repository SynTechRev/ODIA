"""Continual-learning feedback loop.

Collects human corrections to Layer 2 extraction output, persists them
in a labeled-corrections store, and triggers re-training when enough
new corrections have accumulated or when evaluation metrics regress.

Design:
- Local SQLite persistence (works offline; integrates with desktop app)
- Corrections are versioned against the model that produced them
  (so we can attribute which corrections target which model version)
- Three correction types: ADDITION (missed extraction), DELETION
  (false positive), MODIFICATION (wrong field value)
- Configurable re-training triggers: correction count threshold, time
  since last training, or evaluation-regression signal

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


CorrectionType = Literal["addition", "deletion", "modification"]


@dataclass
class Correction:
    """A single user correction to an extraction output."""

    correction_id: str
    document_hash: str  # SHA-256 of input_text (stable document identity)
    field_name: str  # e.g. "vendors", "anomaly_candidates"
    correction_type: CorrectionType
    original_value: str  # JSON string of what the model produced
    corrected_value: str  # JSON string of what the user says is correct
    input_text: str  # the document passage being extracted from
    model_version_id: str  # which model produced the original extraction
    jurisdiction: str = ""
    reviewer_id: str = ""  # e.g. "mars" or a session ID
    reviewer_note: str = ""  # free-text reasoning from the reviewer
    created_at: float = field(default_factory=time.time)
    reviewed: bool = False  # True after a senior reviewer confirms the correction
    applied_to_training: bool = False  # True after included in a training run

    def to_dict(self) -> dict:
        return asdict(self)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS corrections (
    correction_id TEXT PRIMARY KEY,
    document_hash TEXT NOT NULL,
    field_name TEXT NOT NULL,
    correction_type TEXT NOT NULL,
    original_value TEXT NOT NULL,
    corrected_value TEXT NOT NULL,
    input_text TEXT NOT NULL,
    model_version_id TEXT NOT NULL,
    jurisdiction TEXT,
    reviewer_id TEXT,
    reviewer_note TEXT,
    created_at REAL NOT NULL,
    reviewed INTEGER DEFAULT 0,
    applied_to_training INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_corrections_hash ON corrections(document_hash);
CREATE INDEX IF NOT EXISTS idx_corrections_field ON corrections(field_name);
CREATE INDEX IF NOT EXISTS idx_corrections_model ON corrections(model_version_id);
CREATE INDEX IF NOT EXISTS idx_corrections_applied ON corrections(applied_to_training);

CREATE TABLE IF NOT EXISTS training_triggers (
    trigger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    triggered_at REAL NOT NULL,
    trigger_reason TEXT NOT NULL,
    corrections_included INTEGER,
    model_version_id TEXT
);
"""


class CorrectionStore:
    """SQLite-backed persistent store of user corrections."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def record(self, correction: Correction) -> str:
        """Persist a correction; returns the correction_id."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO corrections
                (correction_id, document_hash, field_name, correction_type,
                 original_value, corrected_value, input_text, model_version_id,
                 jurisdiction, reviewer_id, reviewer_note, created_at,
                 reviewed, applied_to_training)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    correction.correction_id,
                    correction.document_hash,
                    correction.field_name,
                    correction.correction_type,
                    correction.original_value,
                    correction.corrected_value,
                    correction.input_text,
                    correction.model_version_id,
                    correction.jurisdiction,
                    correction.reviewer_id,
                    correction.reviewer_note,
                    correction.created_at,
                    int(correction.reviewed),
                    int(correction.applied_to_training),
                ),
            )
        return correction.correction_id

    def mark_applied(self, correction_ids: list[str]) -> int:
        """Mark a batch of corrections as included in a training run."""
        if not correction_ids:
            return 0
        with self._conn() as conn:
            placeholders = ",".join(["?"] * len(correction_ids))
            cur = conn.execute(
                f"UPDATE corrections SET applied_to_training=1 "
                f"WHERE correction_id IN ({placeholders})",
                correction_ids,
            )
            return cur.rowcount

    def mark_reviewed(self, correction_ids: list[str]) -> int:
        if not correction_ids:
            return 0
        with self._conn() as conn:
            placeholders = ",".join(["?"] * len(correction_ids))
            cur = conn.execute(
                f"UPDATE corrections SET reviewed=1 "
                f"WHERE correction_id IN ({placeholders})",
                correction_ids,
            )
            return cur.rowcount

    def pending_for_training(self, min_reviewed: bool = True) -> list[Correction]:
        """Return all corrections not yet applied to training."""
        with self._conn() as conn:
            where = "applied_to_training = 0"
            if min_reviewed:
                where += " AND reviewed = 1"
            rows = conn.execute(
                f"SELECT * FROM corrections WHERE {where} ORDER BY created_at"
            ).fetchall()
            return [self._row_to_correction(r) for r in rows]

    def all(self, limit: int | None = None) -> list[Correction]:
        with self._conn() as conn:
            query = "SELECT * FROM corrections ORDER BY created_at DESC"
            if limit:
                query += f" LIMIT {int(limit)}"
            rows = conn.execute(query).fetchall()
            return [self._row_to_correction(r) for r in rows]

    def count(self, reviewed_only: bool = False, unapplied_only: bool = False) -> int:
        where: list[str] = []
        if reviewed_only:
            where.append("reviewed = 1")
        if unapplied_only:
            where.append("applied_to_training = 0")
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        with self._conn() as conn:
            cur = conn.execute(f"SELECT COUNT(*) FROM corrections {clause}")
            return int(cur.fetchone()[0])

    def stats_by_field(self) -> dict[str, int]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT field_name, COUNT(*) FROM corrections GROUP BY field_name"
            ).fetchall()
            return {r[0]: int(r[1]) for r in rows}

    def stats_by_jurisdiction(self) -> dict[str, int]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT jurisdiction, COUNT(*) FROM corrections "
                "WHERE jurisdiction IS NOT NULL AND jurisdiction != '' "
                "GROUP BY jurisdiction"
            ).fetchall()
            return {r[0]: int(r[1]) for r in rows}

    def record_training_trigger(
        self, reason: str, corrections_included: int, model_version_id: str
    ) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO training_triggers
                   (triggered_at, trigger_reason, corrections_included, model_version_id)
                   VALUES (?, ?, ?, ?)""",
                (time.time(), reason, corrections_included, model_version_id),
            )
            return int(cur.lastrowid or 0)

    def last_training_trigger(self) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM training_triggers ORDER BY triggered_at DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _row_to_correction(row: sqlite3.Row) -> Correction:
        return Correction(
            correction_id=row["correction_id"],
            document_hash=row["document_hash"],
            field_name=row["field_name"],
            correction_type=row["correction_type"],
            original_value=row["original_value"],
            corrected_value=row["corrected_value"],
            input_text=row["input_text"],
            model_version_id=row["model_version_id"],
            jurisdiction=row["jurisdiction"] or "",
            reviewer_id=row["reviewer_id"] or "",
            reviewer_note=row["reviewer_note"] or "",
            created_at=float(row["created_at"]),
            reviewed=bool(row["reviewed"]),
            applied_to_training=bool(row["applied_to_training"]),
        )


# ------------------------------------------------------------------
# Trigger logic
# ------------------------------------------------------------------

@dataclass
class TriggerConfig:
    """Thresholds for automatic re-training triggers."""

    min_new_corrections: int = 50
    min_days_since_last_training: int = 30
    min_reviewed_fraction: float = 0.8
    regression_f1_threshold: float = 0.02  # trigger if F1 drops by 2%


@dataclass
class TriggerDecision:
    should_retrain: bool
    reason: str
    corrections_count: int
    days_since_last_training: float | None


def should_trigger_retraining(
    store: CorrectionStore, config: TriggerConfig
) -> TriggerDecision:
    """Decide whether accumulated corrections warrant a retraining run."""
    unapplied = store.count(reviewed_only=True, unapplied_only=True)

    last = store.last_training_trigger()
    days_since = None
    if last and last.get("triggered_at"):
        days_since = (time.time() - float(last["triggered_at"])) / 86400.0

    # Trigger 1: accumulated reviewed corrections exceed threshold
    if unapplied >= config.min_new_corrections:
        return TriggerDecision(
            should_retrain=True,
            reason=f"{unapplied} reviewed corrections accumulated "
                   f"(>= {config.min_new_corrections})",
            corrections_count=unapplied,
            days_since_last_training=days_since,
        )

    # Trigger 2: time-based trigger (accumulates smaller corrections over time)
    if (
        days_since is not None
        and days_since >= config.min_days_since_last_training
        and unapplied > 0
    ):
        return TriggerDecision(
            should_retrain=True,
            reason=f"{days_since:.0f} days since last training with {unapplied} pending",
            corrections_count=unapplied,
            days_since_last_training=days_since,
        )

    return TriggerDecision(
        should_retrain=False,
        reason=f"{unapplied} reviewed/unapplied corrections; threshold {config.min_new_corrections}",
        corrections_count=unapplied,
        days_since_last_training=days_since,
    )


def correction_to_training_example(correction: Correction) -> dict:
    """Convert a Correction record into an alpaca-format training record.

    Used to fold human corrections back into the training dataset when
    a re-training run is triggered.
    """
    try:
        corrected = json.loads(correction.corrected_value)
    except (json.JSONDecodeError, TypeError):
        corrected = {}

    from odia_ai.training.dataset_builder import EXTRACTION_INSTRUCTION, SYSTEM_PROMPT

    # The user-corrected extraction is the new gold output. We preserve the
    # full extraction schema structure, merging the corrected field into a
    # baseline that matches the fine-tuning schema.
    full_output = {
        "vendors": [],
        "persons": [],
        "dollar_amounts": [],
        "statutes_cited": [],
        "procurement_instruments": [],
        "governance_bodies": [],
        "anomaly_candidates": [],
    }
    full_output[correction.field_name] = (
        corrected if isinstance(corrected, list) else [corrected]
    )

    return {
        "instruction": EXTRACTION_INSTRUCTION,
        "input": correction.input_text,
        "output": json.dumps(full_output, ensure_ascii=False),
        "system": SYSTEM_PROMPT,
        "_correction_id": correction.correction_id,
        "_jurisdiction": correction.jurisdiction,
    }


def new_correction(
    input_text: str,
    field_name: str,
    correction_type: CorrectionType,
    original_value: str,
    corrected_value: str,
    model_version_id: str,
    *,
    jurisdiction: str = "",
    reviewer_id: str = "",
    reviewer_note: str = "",
) -> Correction:
    """Factory for a new Correction with SHA-256 document hash and UUID id."""
    import hashlib
    doc_hash = hashlib.sha256(input_text.encode("utf-8")).hexdigest()
    return Correction(
        correction_id=str(uuid.uuid4()),
        document_hash=doc_hash,
        field_name=field_name,
        correction_type=correction_type,
        original_value=original_value,
        corrected_value=corrected_value,
        input_text=input_text,
        model_version_id=model_version_id,
        jurisdiction=jurisdiction,
        reviewer_id=reviewer_id,
        reviewer_note=reviewer_note,
    )
