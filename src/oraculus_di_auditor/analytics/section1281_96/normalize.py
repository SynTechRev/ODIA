"""NormalizedCase dataclass and field-level normalization helpers.

Every retrieval client (AAA, JAMS, smaller providers) converts its raw rows
into NormalizedCase instances using the helpers here.  The dataclass maps
1-to-1 onto the S128196Case DB model -- to_db_dict() produces the flat dict
for SQLAlchemy Core insert.

non_consumer_party_entity_id is populated by passing the raw business name
through EntityRegistry.resolve(); callers that don't have a registry available
leave it None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------------------
# Claim-amount tier
# ---------------------------------------------------------------------------

# Upper-exclusive break points: (ceiling, tier_label)
_TIER_BREAKS: list[tuple[float, str]] = [
    (1_000.0, "UNDER_1K"),
    (10_000.0, "1K_10K"),
    (75_000.0, "10K_75K"),
    (300_000.0, "75K_300K"),
]


def claim_amount_tier(amount_usd: float | None) -> str | None:
    """Map a dollar amount to the standard claim tier label."""
    if amount_usd is None:
        return None
    for ceiling, label in _TIER_BREAKS:
        if amount_usd < ceiling:
            return label
    return "OVER_300K"


# ---------------------------------------------------------------------------
# Field parsers
# ---------------------------------------------------------------------------


def parse_amount(raw: str | float | None) -> float | None:
    """Parse a money string or float into float, stripping $, commas, whitespace."""
    if raw is None:
        return None
    if isinstance(raw, int | float):
        return float(raw) if raw == raw else None  # NaN guard
    cleaned = str(raw).strip().lstrip("$").replace(",", "").replace(" ", "")
    if not cleaned or cleaned.upper() in ("N/A", "NA", "NONE", "-", ""):
        return None
    try:
        return float(Decimal(cleaned))
    except InvalidOperation:
        return None


_DATE_FORMATS = (
    "%m/%d/%Y",
    "%Y-%m-%d",
    "%m-%d-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%m/%d/%y",
    "%Y",
)


def parse_date(raw: str | None) -> date | None:
    """Try common date formats; return None on failure or empty input."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() in ("none", "nan", "n/a", ""):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def normalize_consumer_represented(raw: str | None) -> str:
    """Normalize raw representation field to YES / NO / UNKNOWN."""
    if not raw:
        return "UNKNOWN"
    val = str(raw).strip().upper()
    if val in ("YES", "Y", "TRUE", "1", "REPRESENTED", "ATTORNEY"):
        return "YES"
    if val in ("NO", "N", "FALSE", "0", "UNREPRESENTED", "PRO SE", "SELF"):
        return "NO"
    return "UNKNOWN"


def normalize_disposition(raw: str | None) -> str:
    """Map raw disposition text to the controlled vocabulary.

    Controlled values:
        AWARD_AFTER_HEARING  -- arbitrator issued an award on the merits
        DEFAULT_AWARD        -- award issued in absence of respondent
        SETTLED              -- parties reached a settlement
        WITHDRAWN            -- claimant withdrew before hearing
        DISMISSED            -- case administratively dismissed
        ADMIN_CLOSED         -- closed without award (not settled, not withdrawn)
        OTHER
    """
    if not raw:
        return "UNKNOWN"
    val = str(raw).strip().upper()
    if "AWARD" in val and any(w in val for w in ("HEARING", "MERITS", "FINAL")):
        return "AWARD_AFTER_HEARING"
    if "DEFAULT" in val and "AWARD" in val:
        return "DEFAULT_AWARD"
    if "SETTL" in val:
        return "SETTLED"
    if "WITHDRAW" in val:
        return "WITHDRAWN"
    if "DISMISS" in val:
        return "DISMISSED"
    if "ADMIN" in val or "ADMINISTRATIVE" in val:
        return "ADMIN_CLOSED"
    if "AWARD" in val:
        # Award present but no hearing/merits qualifier -- treat as AWARD_AFTER_HEARING
        return "AWARD_AFTER_HEARING"
    return "OTHER"


def normalize_prevailing(raw: str | None, disposition: str) -> str | None:
    """Map raw prevailing-party text to CONSUMER / BUSINESS / NEITHER / None.

    Only meaningful for AWARD_AFTER_HEARING and DEFAULT_AWARD dispositions.
    All other dispositions return None.
    """
    if disposition not in ("AWARD_AFTER_HEARING", "DEFAULT_AWARD"):
        return None
    if not raw:
        return None
    val = str(raw).strip().upper()
    consumer_terms = ("CONSUMER", "CLAIMANT", "EMPLOYEE", "PLAINTIFF", "PETITIONER")
    business_terms = (
        "BUSINESS",
        "COMPANY",
        "RESPONDENT",
        "EMPLOYER",
        "DEFENDANT",
        "CORPORATION",
        "INC",
        "LLC",
        "LP",
    )
    if any(t in val for t in consumer_terms):
        return "CONSUMER"
    if any(t in val for t in business_terms):
        return "BUSINESS"
    if any(t in val for t in ("NEITHER", "SPLIT", "EACH PARTY", "MUTUAL")):
        return "NEITHER"
    return None


def normalize_bool(raw: str | bool | None) -> bool | None:
    """Parse Y/N/Yes/No/True/False/1/0 to bool, None on ambiguity."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    val = str(raw).strip().upper()
    if val in ("YES", "Y", "TRUE", "1"):
        return True
    if val in ("NO", "N", "FALSE", "0"):
        return False
    return None


def normalize_arbitrator_names(raw: str | list | None) -> list[str]:
    """Parse a delimited or list arbitrator name field to a clean list."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(n).strip() for n in raw if str(n).strip()]
    # Semicolon, pipe, or newline delimited
    for sep in (";", "|", "\n"):
        if sep in str(raw):
            return [n.strip() for n in str(raw).split(sep) if n.strip()]
    name = str(raw).strip()
    return [name] if name else []


# ---------------------------------------------------------------------------
# Stable case_id derivation
# ---------------------------------------------------------------------------


def make_case_id(provider: str, raw_row: dict) -> str:
    """SHA-256 of provider + sorted raw row JSON -- stable across re-runs."""
    payload = f"{provider}::{json.dumps(raw_row, sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def make_retrieval_sha256(raw_row: dict) -> str:
    """SHA-256 of the raw row -- used as provenance fingerprint."""
    return hashlib.sha256(
        json.dumps(raw_row, sort_keys=True, default=str).encode()
    ).hexdigest()


# ---------------------------------------------------------------------------
# NormalizedCase dataclass
# ---------------------------------------------------------------------------


@dataclass
class NormalizedCase:
    """Canonical arbitration case record for the CCP § 1281.96 pipeline.

    One NormalizedCase corresponds to one row in the s1281_96_cases table.
    Retrieval clients build these via their provider-specific column mapping;
    the helpers above handle the common parsing steps.

    non_consumer_party_entity_id is set by the retrieval client by passing
    non_consumer_party_name through EntityRegistry.resolve() -- left None
    when no registry is provided or when resolution falls below threshold.
    """

    # --- Identity / provenance ---
    case_id: str
    provider: str  # AAA | JAMS | ADRS | JUDICATE_WEST | FEDARB | NAM
    case_url: str | None
    retrieval_ts: datetime
    retrieval_sha256: str

    # --- Temporal ---
    case_year: int
    case_quarter: int | None
    filing_date: date | None
    disposition_date: date | None
    days_to_disposition: int | None

    # --- Parties ---
    non_consumer_party_name: str
    non_consumer_party_entity_id: str | None  # nullable -- EntityRegistry.resolve()
    non_consumer_initiating: bool | None

    # --- Dispute classification ---
    dispute_type: str | None
    dispute_subtype: str | None
    consumer_represented: str  # YES | NO | UNKNOWN

    # --- Outcome ---
    prevailing_party: str | None  # CONSUMER | BUSINESS | NEITHER | None
    claim_amount_usd: float | None
    claim_amount_tier: str | None
    award_amount_usd: float | None
    claim_to_award_ratio: float | None
    disposition_type: str  # controlled vocabulary

    # --- Arbitrator ---
    arbitrator_names: list[str] = field(default_factory=list)

    # --- Fees ---
    arbitrator_fee_total_usd: float | None = None
    arbitrator_fee_alloc_consumer_pct: float | None = None
    fee_waiver: bool | None = None

    # --- Other ---
    other_relief: str | None = None
    quality_flags: list[str] = field(default_factory=list)

    def to_db_dict(self) -> dict:
        """Flat dict for S128196Case Core insert."""

        def _to_dt(d: date | None) -> datetime | None:
            return datetime(d.year, d.month, d.day) if d else None

        return {
            "case_id": self.case_id,
            "provider": self.provider,
            "case_url": self.case_url,
            "retrieval_ts": self.retrieval_ts,
            "retrieval_sha256": self.retrieval_sha256,
            "case_year": self.case_year,
            "case_quarter": self.case_quarter,
            "filing_date": _to_dt(self.filing_date),
            "disposition_date": _to_dt(self.disposition_date),
            "days_to_disposition": self.days_to_disposition,
            "non_consumer_party_name": self.non_consumer_party_name,
            "non_consumer_entity_id": self.non_consumer_party_entity_id,
            "non_consumer_initiating": self.non_consumer_initiating,
            "dispute_type": self.dispute_type,
            "dispute_subtype": self.dispute_subtype,
            "consumer_represented": self.consumer_represented,
            "prevailing_party": self.prevailing_party,
            "claim_amount_usd": self.claim_amount_usd,
            "claim_amount_tier": self.claim_amount_tier,
            "award_amount_usd": self.award_amount_usd,
            "claim_to_award_ratio": self.claim_to_award_ratio,
            "disposition_type": self.disposition_type,
            "arbitrator_names": json.dumps(self.arbitrator_names),
            "arbitrator_fee_total_usd": self.arbitrator_fee_total_usd,
            "arbitrator_fee_alloc_consumer_pct": self.arbitrator_fee_alloc_consumer_pct,
            "fee_waiver": self.fee_waiver,
            "other_relief": self.other_relief,
            "quality_flags": json.dumps(self.quality_flags),
        }
