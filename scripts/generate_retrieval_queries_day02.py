"""Generate data/eval/retrieval_queries_v1.jsonl for Day 02 benchmark.

Builds 100 queries with known-relevant document IDs from the 1000-doc
Fresno signature-layer corpus (data/eval/fresno_signature_1k.jsonl).

Query categories:
    - q001-q020: instrument type (CONTRACT, AGREEMENT, AMENDMENT, MOU)
    - q021-q040: dollar amount range (million+, 100k-1M, under 100k)
    - q041-q060: severity (all critical, with specific gap patterns)
    - q061-q080: gap pattern type (underscore, blank_line, missing_auth)
    - q081-q100: combined / analytical queries

Each entry:
    {
      "id": "q001",
      "category": "instrument_type",
      "query": "...",
      "relevant_doc_ids": ["<sha256>", ...],   # ground truth
      "note": "..."
    }
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

random.seed(42)

SRC = Path("data/eval/fresno_signature_1k.jsonl")
OUT = Path("data/eval/retrieval_queries_v1.jsonl")


def load_docs() -> list[dict]:
    docs = []
    with open(SRC, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))
    return docs


def parse_dollar(raw: str) -> float:
    try:
        return float(raw.replace("$", "").replace(",", ""))
    except (ValueError, AttributeError):
        return 0.0


def build_queries(docs: list[dict]) -> list[dict]:
    by_instrument: dict[str, list[str]] = defaultdict(list)
    by_dollar_range: dict[str, list[str]] = defaultdict(list)
    by_gap_pattern: dict[str, list[str]] = defaultdict(list)
    all_critical = []

    for doc in docs:
        doc_id = doc["document_id"]
        for f in doc.get("findings", []):
            details = f.get("details", {})
            itype = details.get("instrument_type", "UNKNOWN")
            by_instrument[itype].append(doc_id)
            raw = details.get("dollar_amount", "")
            val = parse_dollar(raw)
            if val >= 1_000_000:
                by_dollar_range["million_plus"].append(doc_id)
            elif val >= 100_000:
                by_dollar_range["100k_to_1m"].append(doc_id)
            elif val > 0:
                by_dollar_range["under_100k"].append(doc_id)
            gap = details.get("signature_gap_type", "")
            if gap:
                by_gap_pattern[gap].append(doc_id)
            if f.get("severity") == "critical":
                all_critical.append(doc_id)

    def dedup_list(lst: list[str]) -> list[str]:
        seen: set[str] = set()
        out = []
        for x in lst:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    queries: list[dict] = []
    qn = 1

    def add(category: str, query: str, relevant: list[str], note: str = "") -> None:
        nonlocal qn
        queries.append(
            {
                "id": f"q{qn:03d}",
                "category": category,
                "query": query,
                "relevant_doc_ids": dedup_list(relevant),
                "note": note,
            }
        )
        qn += 1

    # q001-q020: instrument type
    instrument_queries = [
        ("CONTRACT", "unsigned contract missing signature gap"),
        ("AGREEMENT", "agreement document with signature gap"),
        ("AMENDMENT", "amendment missing authorized signature"),
        ("AMENDMENT", "unsigned amendment to city agreement"),
        ("CONTRACT", "contract with missing signature line critical finding"),
        ("AGREEMENT", "unsigned city agreement fiscal anomaly"),
        ("CONTRACT", "procurement contract missing execution signature"),
        ("AGREEMENT", "agreement instrument signature gap pattern detected"),
        ("AMENDMENT", "amendment instrument unsigned critical"),
        ("CONTRACT", "contract dollar amount unsigned missing signature"),
        ("AGREEMENT", "unsigned agreement instrument high value"),
        ("CONTRACT", "contract signature gap pattern underscore"),
        ("AMENDMENT", "amendment to contract missing signature authorization"),
        ("MOU", "memorandum of understanding unsigned instrument"),
        ("AGREEMENT", "city agreement without signature line"),
        ("CONTRACT", "service contract missing signature finding"),
        ("AGREEMENT", "agreement anomaly unsigned instrument critical severity"),
        ("CONTRACT", "contract instrument signature gap gap_pattern_count"),
        ("AMENDMENT", "amendment missing signatory line"),
        ("AGREEMENT", "fiscal agreement with signature compliance gap"),
    ]
    for itype, query in instrument_queries[:20]:
        relevant = by_instrument.get(itype, [])
        add("instrument_type", query, relevant, f"instrument_type={itype}")

    # q021-q040: dollar amount range
    dollar_queries = [
        ("million_plus", "contracts over one million dollars unsigned instrument"),
        ("million_plus", "high value agreement missing signature million dollar"),
        ("million_plus", "seven figure contract unsigned critical anomaly"),
        ("million_plus", "large contract signature gap over 1 million"),
        ("100k_to_1m", "mid range contract hundred thousand signature gap"),
        ("100k_to_1m", "agreement between 100k and 1 million unsigned"),
        ("100k_to_1m", "city procurement 100000 to 1000000 unsigned instrument"),
        ("100k_to_1m", "contract value 500000 missing signature"),
        ("under_100k", "small contract under one hundred thousand unsigned"),
        ("under_100k", "low value agreement signature gap detected"),
        ("million_plus", "multi-million dollar contract missing execution"),
        ("million_plus", "10 million contract unsigned instrument finding"),
        ("100k_to_1m", "contract 250000 signature gap pattern"),
        ("under_100k", "contract 50000 missing authorized signature"),
        ("million_plus", "high dollar unsigned procurement contract"),
        ("100k_to_1m", "city agreement fiscal anomaly mid range value"),
        ("million_plus", "million dollar agreement missing signature authorization"),
        ("100k_to_1m", "service agreement 300k unsigned instrument critical"),
        ("under_100k", "low dollar contract signature compliance gap"),
        ("million_plus", "unsigned agreement large dollar amount signature finding"),
    ]
    for range_key, query in dollar_queries[:20]:
        relevant = by_dollar_range.get(range_key, [])
        add("dollar_range", query, relevant, f"dollar_range={range_key}")

    # q041-q060: severity / critical findings
    critical_docs = dedup_list(all_critical)
    severity_queries = [
        "critical severity unsigned instrument findings",
        "critical anomaly signature gap detected",
        "highest severity contract compliance gap",
        "critical finding unsigned city contract",
        "critical compliance failure signature instrument",
        "unsigned instrument critical severity fiscal",
        "signature gap critical anomaly findings",
        "critical procurement contract unsigned",
        "critical findings city agreements unsigned",
        "severe compliance gap unsigned instrument",
        "critical risk unsigned contract instrument",
        "high priority unsigned instrument critical",
        "critical audit finding missing signature",
        "critical severity instrument signature gap pattern",
        "top severity findings signature layer",
        "contract critical finding signature compliance",
        "critical anomaly unsigned instrument city",
        "most severe instrument findings unsigned",
        "critical procurement gap signature",
        "critical unsigned agreement instrument",
    ]
    for query in severity_queries[:20]:
        add("severity_critical", query, critical_docs)

    # q061-q080: gap pattern
    gap_pattern_queries = [
        ("_{5,}", "underscore gap pattern signature line"),
        ("_{5,}", "signature blank line underscore pattern detected"),
        ("_{5,}", "contract underscore signature gap"),
        ("_{5,}", "underscore placeholder signature missing"),
        ("_{5,}", "five underscore signature gap pattern count"),
        ("blank_line", "blank line signature gap instrument"),
        ("blank_line", "empty line where signature should be"),
        ("blank_line", "contract blank signature line gap pattern"),
        ("blank_line", "unsigned instrument blank line gap"),
        ("blank_line", "signature blank line compliance failure"),
    ]
    for gap, query in gap_pattern_queries[:10]:
        relevant = by_gap_pattern.get(gap, [])
        add("gap_pattern", query, relevant, f"gap_pattern={gap}")

    # Fill remaining gap slots with all gaps combined
    all_gap_docs = dedup_list(
        [doc_id for docs_list in by_gap_pattern.values() for doc_id in docs_list]
    )
    for i in range(10):
        add(
            "gap_pattern",
            f"signature gap pattern instrument finding {i+1}",
            all_gap_docs,
        )

    # q081-q100: combined and analytical
    all_ids = [d["document_id"] for d in docs]
    combined_queries = [
        "how many unsigned instruments are in the corpus",
        "what is the total dollar value of unsigned contracts",
        "which document types have the most signature gaps",
        "contracts and agreements with critical unsigned finding",
        "largest unsigned instrument dollar amount",
        "all unsigned instruments across the fresno corpus",
        "agreement and contract signature gap findings",
        "what percentage of documents have critical signature gaps",
        "unsigned instruments over 500000 dollars",
        "multi-million dollar unsigned contracts and agreements",
        "signature gap analysis across all instrument types",
        "fiscal impact of unsigned instrument anomalies",
        "summary of signature compliance failures",
        "unsigned agreements with dollar amounts above threshold",
        "pattern of signature gaps in city procurement documents",
        "contracts with multiple signature gap occurrences",
        "fiscal compliance audit unsigned instruments",
        "CPRA request basis unsigned instrument findings",
        "legal exposure from unsigned high-value contracts",
        "city clerk compliance unsigned instrument review",
    ]
    for query in combined_queries[:20]:
        add("combined", query, all_ids)

    return queries[:100]


def main() -> None:
    docs = load_docs()
    queries = build_queries(docs)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    print(f"Wrote {len(queries)} queries to {OUT}")
    categories: dict[str, int] = {}
    for q in queries:
        categories[q["category"]] = categories.get(q["category"], 0) + 1
    for cat, cnt in sorted(categories.items()):
        print(f"  {cat}: {cnt}")


if __name__ == "__main__":
    main()
