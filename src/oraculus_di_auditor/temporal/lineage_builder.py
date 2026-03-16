"""Contract lineage builder.

Reconstructs contract lineages from document analysis results by grouping
related documents (original contract, amendments, renewals, etc.) into
chronological chains that represent a single vendor relationship over time.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from oraculus_di_auditor.temporal.models import (
    ContractEvent,
    ContractLineage,
)

# ---------------------------------------------------------------------------
# Event type keyword mappings
# ---------------------------------------------------------------------------

_ORIGINAL_KEYWORDS = frozenset(
    {
        "original contract",
        "initial agreement",
        "new contract",
        "master services agreement",
        "master agreement",
        "initial contract",
        "base contract",
    }
)

_AMENDMENT_KEYWORDS = frozenset(
    {
        "amendment",
        "modification",
        "change order",
        "addendum",
        "supplement",
    }
)

_RENEWAL_KEYWORDS = frozenset(
    {
        "renewal",
        "extension",
        "auto-renewal",
        "renewed",
        "extended",
        "option year",
    }
)

_QUOTE_KEYWORDS = frozenset({"quote", "quotation", "q-", "price quote", "vendor quote"})

_PO_KEYWORDS = frozenset(
    {
        "purchase order",
        " po ",
        "po#",
        "po-",
        "requisition",
    }
)

_AUTH_KEYWORDS = frozenset(
    {
        "resolution",
        "authorization",
        "approved",
        "council approval",
        "approval resolution",
        "city council resolution",
    }
)

# ---------------------------------------------------------------------------
# Amount extraction
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d{1,2})?)\s*(?:million|M\b)?",
    re.IGNORECASE,
)

_CONTRACT_ID_RE = re.compile(
    r"\b(?:MSPA|MSA|PO|REQ|RESO|ORD|RFQ|RFP|CONT|AGR)[-#]?\s*(\d{3,}(?:[-/]\w+)?)\b",
    re.IGNORECASE,
)

_VENDOR_BETWEEN_RE = re.compile(
    r"(?:between\s+\S+(?:\s+\S+)?\s+and\s+|contract\s+with\s+)([\w\s&.,'-]+?)(?:\s*,|\s+for|\s+to\s+provide|\.|\Z)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# LineageBuilder
# ---------------------------------------------------------------------------


class LineageBuilder:
    """Reconstructs contract lineages from document analysis results."""

    def __init__(self) -> None:
        self._documents: list[dict[str, Any]] = []
        self._analysis_results: list[dict[str, Any]] = []
        # Maps document_id -> list of anomaly IDs
        self._anomaly_map: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def load_documents(
        self,
        documents: list[dict[str, Any]],
        analysis_results: list[dict[str, Any]] | None = None,
    ) -> int:
        """Load documents and optional analysis results. Returns count loaded."""
        self._documents = list(documents)
        self._analysis_results = list(analysis_results or [])
        self._anomaly_map = self._build_anomaly_map(self._analysis_results)
        return len(self._documents)

    def build_lineages(self) -> list[ContractLineage]:
        """Group documents into contract lineages."""
        if not self._documents:
            return []

        # Build events from documents
        events_by_group: dict[str, list[ContractEvent]] = {}
        vendor_by_group: dict[str, str] = {}

        for doc in self._documents:
            vendor = self._extract_vendor(doc)
            if not vendor:
                vendor = "unknown"

            contract_id = self._extract_contract_id(doc)
            # Group key: vendor + contract family (if any)
            group_key = self._make_group_key(vendor, contract_id)

            doc_id = doc.get("id") or doc.get("document_id") or doc.get("doc_id") or ""
            event_type = self._extract_event_type(doc)
            date = self._extract_date(doc)
            amount = self._extract_dollar_amount(doc)
            auth_type = self._extract_authorization_type(doc)

            seq = len(events_by_group.get(group_key, [])) + 1
            event = ContractEvent(
                event_id=f"{group_key[:12]}-{seq:03d}",
                event_type=event_type,
                date=date or "unknown",
                document_id=str(doc_id) if doc_id else None,
                description=doc.get("title") or doc.get("description") or event_type,
                dollar_amount=amount,
                vendor=vendor if vendor != "unknown" else None,
                authorization_type=auth_type,
                anomalies=self._anomaly_map.get(str(doc_id), []),
                metadata={
                    k: v
                    for k, v in doc.items()
                    if k not in {"text", "content", "raw_text"}
                },
            )

            if group_key not in events_by_group:
                events_by_group[group_key] = []
                vendor_by_group[group_key] = vendor

            events_by_group[group_key].append(event)

        # Build lineages from grouped events
        lineages: list[ContractLineage] = []
        for group_key, events in events_by_group.items():
            vendor = vendor_by_group[group_key]
            # Sort chronologically (unknown dates go to the end)
            events.sort(key=lambda e: (e.date == "unknown", e.date))

            # Compute cumulative amounts
            running = 0.0
            for event in events:
                if event.dollar_amount is not None:
                    running += event.dollar_amount
                event.cumulative_amount = running

            original_amount = 0.0
            for e in events:
                if e.event_type == "original" and e.dollar_amount is not None:
                    original_amount = e.dollar_amount
                    break

            current_amount = running

            lineage = ContractLineage(
                lineage_id=ContractLineage.make_lineage_id(vendor, None, None),
                vendor=vendor,
                original_amount=original_amount,
                current_amount=current_amount,
                total_authorized=current_amount,
                events=events,
            )
            lineage = self._compute_lineage_metrics(lineage)
            lineages.append(lineage)

        return lineages

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_vendor(self, doc: dict[str, Any]) -> str | None:
        """Extract primary vendor name from document."""
        # Direct metadata fields
        for field in ("vendor", "vendor_name", "contractor", "company"):
            val = doc.get(field)
            if val and isinstance(val, str) and val.strip():
                return val.strip()

        # Look in nested metadata
        meta = doc.get("metadata", {})
        if isinstance(meta, dict):
            for field in ("vendor", "vendor_name", "contractor"):
                val = meta.get(field)
                if val and isinstance(val, str) and val.strip():
                    return val.strip()

        # Text pattern search
        text = self._get_text(doc)
        if text:
            m = _VENDOR_BETWEEN_RE.search(text)
            if m:
                candidate = m.group(1).strip().rstrip(".,")
                if candidate and len(candidate) > 2:
                    return candidate

        return None

    def _extract_contract_id(self, doc: dict[str, Any]) -> str | None:
        """Extract contract/instrument identifier."""
        for field in (
            "contract_id",
            "contract_number",
            "agreement_id",
            "instrument_id",
        ):
            val = doc.get(field) or (doc.get("metadata") or {}).get(field)
            if val:
                return str(val).strip()

        text = self._get_text(doc)
        if text:
            m = _CONTRACT_ID_RE.search(text)
            if m:
                return m.group(0).strip()

        return None

    def _extract_event_type(self, doc: dict[str, Any]) -> str:
        """Classify document as original, amendment, renewal, etc."""
        # Check explicit type field
        for field in ("document_type", "doc_type", "type", "event_type"):
            val = (doc.get(field) or "").lower().strip()
            if val in ContractEvent.VALID_EVENT_TYPES:
                return val

        # Check title + text
        combined = " ".join(
            [
                str(doc.get("title") or ""),
                str(doc.get("description") or ""),
                self._get_text(doc)[:500],
            ]
        ).lower()

        if any(kw in combined for kw in _AMENDMENT_KEYWORDS):
            return "amendment"
        if any(kw in combined for kw in _RENEWAL_KEYWORDS):
            return "renewal"
        if any(kw in combined for kw in _QUOTE_KEYWORDS):
            return "quote"
        if any(kw in combined for kw in _PO_KEYWORDS):
            return "purchase_order"
        if any(kw in combined for kw in _AUTH_KEYWORDS):
            return "authorization"
        if any(kw in combined for kw in _ORIGINAL_KEYWORDS):
            return "original"

        return "original"  # default for unclassifiable docs

    def _extract_authorization_type(self, doc: dict[str, Any]) -> str | None:
        """Extract how the procurement was authorized."""
        for field in ("authorization_type", "procurement_method", "auth_type"):
            val = (doc.get(field) or "").lower().strip()
            if val in ContractEvent.VALID_AUTH_TYPES:
                return val

        combined = " ".join(
            [
                str(doc.get("title") or ""),
                self._get_text(doc)[:500],
            ]
        ).lower()

        if "sole source" in combined or "sole-source" in combined:
            return "sole_source"
        if "consent calendar" in combined or "consent agenda" in combined:
            return "consent_calendar"
        if (
            "council vote" in combined
            or "city council" in combined
            and "vote" in combined
        ):
            return "council_vote"
        if "competitive bid" in combined or "competitive procurement" in combined:
            return "competitive_bid"

        return None

    def _extract_dollar_amount(self, doc: dict[str, Any]) -> float | None:
        """Extract primary dollar amount from document."""
        for field in ("amount", "dollar_amount", "contract_amount", "value", "total"):
            val = doc.get(field)
            if val is not None:
                try:
                    return float(str(val).replace(",", "").replace("$", ""))
                except (ValueError, TypeError):
                    pass

        text = self._get_text(doc)
        if text:
            amounts = self._parse_amounts_from_text(text)
            if amounts:
                return max(amounts)

        return None

    @staticmethod
    def _parse_amounts_from_text(text: str) -> list[float]:
        """Parse all dollar amounts from text, handling 'million' suffix."""
        amounts = []
        for raw in _AMOUNT_RE.findall(text):
            try:
                amt = float(raw.replace(",", ""))
                idx = text.find(f"${raw}")
                if idx >= 0:
                    suffix = text[idx + len(raw) + 1 : idx + len(raw) + 10].lower()
                    if "million" in suffix or suffix.lstrip().startswith("m"):
                        amt *= 1_000_000
                amounts.append(amt)
            except ValueError:
                pass
        return amounts

    def _extract_date(self, doc: dict[str, Any]) -> str | None:
        """Extract primary date from document metadata or text."""
        for field in (
            "date",
            "contract_date",
            "execution_date",
            "signed_date",
            "effective_date",
        ):
            val = doc.get(field) or (doc.get("metadata") or {}).get(field)
            if val:
                parsed = self._parse_date_str(str(val))
                if parsed:
                    return parsed

        # Try text extraction (first ISO date found)
        text = self._get_text(doc)
        if text:
            iso_match = re.search(
                r"\b(20\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))\b", text
            )
            if iso_match:
                return iso_match.group(1)

        return None

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def _compute_lineage_metrics(self, lineage: ContractLineage) -> ContractLineage:
        """Compute span_years, risk_score, unsigned_instruments, pre_auth_events."""
        dated_events = [e for e in lineage.events if e.date != "unknown"]
        if len(dated_events) >= 2:
            try:
                d0 = datetime.fromisoformat(dated_events[0].date)
                d1 = datetime.fromisoformat(dated_events[-1].date)
                lineage.span_years = round((d1 - d0).days / 365.25, 2)
            except ValueError:
                pass

        lineage.unsigned_instruments = sum(
            1
            for e in lineage.events
            if any(v == "blank" for v in e.signatures.values())
        )

        lineage.pre_authorization_events = sum(
            1
            for e in lineage.events
            if "procurement:pre-authorization" in " ".join(e.anomalies)
        )

        lineage.risk_score = self._compute_risk_score(lineage)
        return lineage

    def _compute_risk_score(self, lineage: ContractLineage) -> float:
        """Score lineage risk 0.0–1.0 based on multiple factors."""
        score = self._growth_risk(lineage.growth_percentage)
        score += self._amendment_risk(lineage.amendment_count)
        score += self._sole_source_risk(lineage)
        if lineage.unsigned_instruments > 0:
            score += 0.20
        if lineage.pre_authorization_events > 0:
            score += 0.25
        if (
            lineage.span_years > 5
            and "competitive_bid" not in lineage.procurement_methods
        ):
            score += 0.10
        return round(min(score, 1.0), 3)

    @staticmethod
    def _growth_risk(growth_pct: float) -> float:
        if growth_pct > 500:
            return 0.35
        if growth_pct > 200:
            return 0.25
        if growth_pct > 100:
            return 0.15
        return 0.0

    @staticmethod
    def _amendment_risk(count: int) -> float:
        if count > 3:
            return 0.15
        if count > 1:
            return 0.08
        return 0.0

    @staticmethod
    def _sole_source_risk(lineage: ContractLineage) -> float:
        n = sum(1 for e in lineage.events if e.authorization_type == "sole_source")
        if n > 1:
            return 0.15
        if n == 1:
            return 0.05
        return 0.0

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _make_group_key(vendor: str, contract_id: str | None) -> str:
        """Create a stable group key for lineage bucketing."""
        vendor_slug = re.sub(r"[^a-z0-9]", "_", vendor.lower())[:24]
        if contract_id:
            id_slug = re.sub(r"[^a-z0-9]", "_", contract_id.lower())[:24]
            return f"{vendor_slug}__{id_slug}"
        return vendor_slug

    @staticmethod
    def _build_anomaly_map(
        analysis_results: list[dict[str, Any]],
    ) -> dict[str, list[str]]:
        """Build document_id -> anomaly_id list from analysis results."""
        amap: dict[str, list[str]] = {}
        for result in analysis_results:
            doc_id = str(
                result.get("document_id")
                or result.get("doc_id")
                or result.get("id")
                or ""
            )
            if not doc_id:
                continue
            anomalies = result.get("anomalies") or result.get("findings") or []
            ids = []
            for a in anomalies:
                if isinstance(a, dict):
                    ids.append(a.get("id") or a.get("anomaly_id") or "")
                elif isinstance(a, str):
                    ids.append(a)
            amap[doc_id] = [i for i in ids if i]
        return amap

    @staticmethod
    def _get_text(doc: dict[str, Any]) -> str:
        """Return the best available text representation of a document."""
        return str(doc.get("text") or doc.get("content") or doc.get("raw_text") or "")

    @staticmethod
    def _parse_date_str(val: str) -> str | None:
        """Try to parse a date string to ISO YYYY-MM-DD."""
        val = val.strip()
        for fmt in (
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
        ):
            try:
                return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        # Partial: just a year
        if re.fullmatch(r"20\d{2}", val):
            return f"{val}-01-01"
        return None
