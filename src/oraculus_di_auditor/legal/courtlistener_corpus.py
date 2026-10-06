"""CourtListener corpus loader — CorpusLoader implementation for case law.

Bridges CourtListenerClient ↔ CaseLawBuilder ↔ CorpusLoader so the
legal_resolver can surface CourtListener opinions alongside USC and CFR text.

Case records are cached to legal/cases/ as CaseLawRecord JSON files and
loaded from disk first (no API hit if already present). The harvest script
(scripts/build_courtlistener_corpus.py) populates the cache on first run.

ODIA audit focus areas, weighted by relevance to known corpus anomalies:
  - CPRA / California public records law (exemptions, disclosure duties)
  - 4th Amendment surveillance (automated license plate readers, body cams)
  - AB 481 military equipment (transparency requirements)
  - Federal grant accountability (JAG, Byrne, Title IV-E)
  - Privacy / biometric surveillance (BIPA analogues)
  - Public meeting law (Brown Act, First Amendment access)
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from .case_law_builder import CaseLawBuilder, CaseLawRecord
from .corpus_base import CorpusLoader, LegalText
from .courtlistener_client import CourtListenerClient

logger = logging.getLogger(__name__)

# CourtListener court slugs most relevant to ODIA (Tulare + Fresno Counties)
# ca9 = Ninth Circuit, cal = California Supreme Court, caca = CA Court of Appeal
_ODIA_RELEVANT_COURTS = ["scotus", "ca9", "cal", "caca"]

# Queries to populate the initial ODIA case law corpus.
# These run at harvest time; results are saved as CaseLawRecord JSON.
ODIA_HARVEST_QUERIES: list[dict] = [
    # ---- CPRA / Public Records ----
    {
        "query": "California Public Records Act CPRA exemption disclosure",
        "courts": ["cal", "caca"],
        "topic": "cpra",
        "max_results": 30,
    },
    {
        "query": "public records act exemption law enforcement",
        "courts": ["cal", "caca"],
        "topic": "cpra",
        "max_results": 20,
    },
    # ---- 4th Amendment Surveillance ----
    {
        "query": "automated license plate reader ALPR Fourth Amendment",
        "courts": ["scotus", "ca9", "cal"],
        "topic": "surveillance",
        "max_results": 15,
    },
    {
        "query": "GPS tracking Fourth Amendment warrant requirement",
        "courts": ["scotus", "ca9"],
        "topic": "surveillance",
        "max_results": 15,
    },
    {
        "query": "body camera footage public records disclosure",
        "courts": ["cal", "caca", "ca9"],
        "topic": "surveillance",
        "max_results": 15,
    },
    # ---- AB 481 Military Equipment ----
    {
        "query": "military equipment police transparency accountability",
        "courts": ["ca9", "cal"],
        "topic": "ab481",
        "max_results": 10,
    },
    # ---- Federal Grant / JAG Compliance ----
    {
        "query": "Byrne JAG grant compliance conditions federal funding",
        "courts": ["scotus", "ca9"],
        "topic": "federal_grants",
        "max_results": 15,
    },
    {
        "query": "conditional spending federal grant constitutional limits",
        "courts": ["scotus"],
        "topic": "federal_grants",
        "max_results": 10,
    },
    # ---- Probation / Juvenile Justice ----
    {
        "query": "probation conditions Fourth Amendment search waiver",
        "courts": ["scotus", "ca9", "cal"],
        "topic": "probation",
        "max_results": 15,
    },
    {
        "query": "juvenile detention due process procedural rights",
        "courts": ["scotus", "ca9", "cal"],
        "topic": "probation",
        "max_results": 10,
    },
    # ---- Public Meeting / Brown Act ----
    {
        "query": "Brown Act public meeting open government California",
        "courts": ["cal", "caca"],
        "topic": "open_meetings",
        "max_results": 15,
    },
    # ---- Privacy / Biometric ----
    {
        "query": "biometric data collection privacy Fourth Amendment",
        "courts": ["scotus", "ca9"],
        "topic": "privacy",
        "max_results": 10,
    },
]


def _cluster_to_case_record(
    cluster: dict, opinion: dict | None = None, topic: str = ""
) -> CaseLawRecord | None:
    """Convert a CourtListener cluster+opinion dict to CaseLawRecord.

    Returns None if essential fields are missing.
    """
    case_name = cluster.get("case_name") or cluster.get("caseName", "")
    if not case_name:
        return None

    citations = cluster.get("citations", [])
    citation_str = citations[0].get("cite", "") if citations else ""
    if not citation_str:
        citation_str = cluster.get("citation_string", "")

    date_filed = cluster.get("date_filed", "") or ""
    year = (
        int(date_filed[:4]) if len(date_filed) >= 4 and date_filed[:4].isdigit() else 0
    )

    court_id = cluster.get("court_id", "") or cluster.get("court", "")
    court_map = {
        "scotus": "SCOTUS",
        "ca9": "9th Circuit",
        "cal": "California Supreme Court",
        "caca": "CA Court of Appeal",
    }
    court = court_map.get(str(court_id).lower(), str(court_id).upper())

    plain_text = ""
    summary = ""
    if opinion:
        plain_text = (opinion.get("plain_text") or "").strip()
        summary = plain_text[:500] if plain_text else ""

    cluster_id = cluster.get("id", "")
    case_id = f"cl_{cluster_id}" if cluster_id else ""
    if not case_id:
        return None

    source_url = f"https://www.courtlistener.com/opinion/{cluster_id}/"

    return CaseLawRecord(
        case_id=case_id,
        name=case_name,
        citation=citation_str,
        year=year,
        court=court,
        doctrine=topic,
        summary=summary,
        source_url=source_url,
    )


class CourtListenerCorpusLoader(CorpusLoader):
    """CorpusLoader backed by CourtListener + local CaseLawRecord cache.

    Resolution strategy:
      1. Parse the citation as a cluster ID (numeric) or case name fragment
      2. Check local CaseLawRecord JSON files first (no API hit if cached)
      3. Fall back to CourtListener API search if not cached
    """

    corpus_id = "courtlistener"

    def __init__(
        self,
        cases_dir: Path | str = "legal/cases",
        client: CourtListenerClient | None = None,
    ):
        self._builder = CaseLawBuilder(cases_dir=cases_dir)
        self._client = client or CourtListenerClient()
        self._cases: list[CaseLawRecord] | None = None

    def _load_cases(self) -> list[CaseLawRecord]:
        if self._cases is None:
            self._cases = self._builder.load_all_cases()
        return self._cases

    def _invalidate_cache(self) -> None:
        self._cases = None

    # ------------------------------------------------------------------
    # CorpusLoader contract
    # ------------------------------------------------------------------

    def initialize(self) -> dict[str, int]:
        cases = self._load_cases()
        return {
            "cases_loaded": len(cases),
            "doctrines": len(set(c.doctrine for c in cases if c.doctrine)),
        }

    def resolve_citation(
        self, citation: str, as_of: date | None = None
    ) -> LegalText | None:
        """Resolve a case citation or cluster ID to a LegalText.

        Matching order:
          1. Exact citation match in local cache (e.g. "415 F.3d 1233")
          2. Case name fragment match in local cache
          3. CourtListener API search (with result cached to disk)
        """
        norm = citation.strip()
        for case in self._load_cases():
            if case.citation and case.citation.lower() == norm.lower():
                return self._case_to_legal_text(case, citation)
            if norm.lower() in case.name.lower():
                return self._case_to_legal_text(case, citation)

        # API fallback
        results = self._client.search_opinions(query=norm, max_results=1)
        if not results:
            return None
        hit = results[0]
        cluster_id = hit.get("cluster_id") or hit.get("id")
        if not cluster_id:
            return None
        cluster = self._client.get_cluster(cluster_id)
        if not cluster:
            return None
        record = _cluster_to_case_record(cluster)
        if record:
            self._builder.save_case(record)
            self._invalidate_cache()
            return self._case_to_legal_text(record, citation)
        return None

    def search_text(self, query: str, limit: int = 10) -> list[LegalText]:
        """Search local case law cache, then CourtListener API."""
        query_lower = query.lower()
        local_hits: list[LegalText] = []
        for case in self._load_cases():
            if (
                query_lower in case.name.lower()
                or query_lower in case.summary.lower()
                or query_lower in case.holding.lower()
                or any(query_lower in t.lower() for t in case.issue_tags)
            ):
                local_hits.append(self._case_to_legal_text(case, query))
            if len(local_hits) >= limit:
                return local_hits

        if len(local_hits) < limit:
            api_results = self._client.search_opinions(
                query=query, max_results=limit - len(local_hits)
            )
            for hit in api_results:
                cluster_id = hit.get("cluster_id") or hit.get("id")
                if not cluster_id:
                    continue
                cluster = self._client.get_cluster(cluster_id)
                if not cluster:
                    continue
                record = _cluster_to_case_record(cluster)
                if record:
                    local_hits.append(self._case_to_legal_text(record, query))

        return local_hits[:limit]

    def list_amendments(self, citation: str) -> list[dict]:
        return []

    def statistics(self) -> dict[str, int]:
        cases = self._load_cases()
        return {
            "total_cases": len(cases),
            "with_citations": sum(1 for c in cases if c.citation),
            "with_summaries": sum(1 for c in cases if c.summary),
            "doctrines": len(set(c.doctrine for c in cases if c.doctrine)),
            "courts": len(set(c.court for c in cases if c.court)),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _case_to_legal_text(self, case: CaseLawRecord, citation_raw: str) -> LegalText:
        body_parts = []
        if case.summary:
            body_parts.append(f"Summary: {case.summary}")
        if case.holding:
            body_parts.append(f"Holding: {case.holding}")
        if case.relevance_to_audit:
            body_parts.append(f"Relevance: {case.relevance_to_audit}")
        text = "\n".join(body_parts) or case.name

        return LegalText(
            corpus_id=self.corpus_id,
            citation=case.citation or case.case_id,
            citation_raw=citation_raw,
            title=case.name,
            text=text,
            source_path=f"legal/cases/{case.case_id}.json",
            source_commit=None,
            as_of=date(case.year, 1, 1) if case.year else None,
            url=case.source_url or None,
            notes=f"court={case.court}; doctrine={case.doctrine}",
        )

    # ------------------------------------------------------------------
    # Harvest helper (used by scripts/build_courtlistener_corpus.py)
    # ------------------------------------------------------------------

    def harvest(
        self,
        queries: list[dict] | None = None,
        skip_existing: bool = True,
    ) -> dict[str, int]:
        """Run all ODIA_HARVEST_QUERIES and persist new cases.

        Returns: {total_queries, new_cases, skipped, errors}
        """
        if queries is None:
            queries = ODIA_HARVEST_QUERIES

        existing_ids = {c.case_id for c in self._load_cases()}
        new_cases = 0
        skipped = 0
        errors = 0

        for q in queries:
            query_str = q["query"]
            courts = q.get("courts")
            topic = q.get("topic", "")
            max_r = q.get("max_results", 20)
            logger.info(
                "CourtListener harvest: %r (courts=%s max=%d)", query_str, courts, max_r
            )

            try:
                results = self._client.search_opinions(
                    query=query_str,
                    courts=courts,
                    max_results=max_r,
                )
            except Exception as exc:
                logger.warning("Harvest query failed: %r error: %s", query_str, exc)
                errors += 1
                continue

            for hit in results:
                cluster_id = hit.get("cluster_id") or hit.get("id")
                if not cluster_id:
                    continue
                case_id = f"cl_{cluster_id}"
                if skip_existing and case_id in existing_ids:
                    skipped += 1
                    continue
                try:
                    cluster = self._client.get_cluster(cluster_id)
                    if not cluster:
                        continue
                    opinions = cluster.get("sub_opinions", [])
                    opinion_data = None
                    if opinions:
                        op_id = opinions[0].get("id") or opinions[0]
                        opinion_data = self._client.get_opinion(op_id)
                    record = _cluster_to_case_record(cluster, opinion_data, topic)
                    if record:
                        self._builder.save_case(record)
                        existing_ids.add(case_id)
                        new_cases += 1
                except Exception as exc:
                    logger.warning("Failed to process cluster %s: %s", cluster_id, exc)
                    errors += 1

        self._invalidate_cache()
        return {
            "total_queries": len(queries),
            "new_cases": new_cases,
            "skipped": skipped,
            "errors": errors,
        }
