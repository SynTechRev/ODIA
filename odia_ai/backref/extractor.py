"""Alert-to-document back-reference extractor.

Parses the Master Audit Synthesis (MAS) markdown files produced across
the 9-jurisdiction ODIA corpus and extracts structured alert records.

Input: MAS markdown files (e.g., Exeter_MAS_V16_0.md, VPD_V8_0.md)
Output: JSONL lines, one per alert, with:
  - alert_id (e.g. "EXE-138", "VPD-072")
  - jurisdiction (e.g. "Exeter", "VPD")
  - severity (CRITICAL | HIGH | MEDIUM | LOW)
  - category (F-1, F-2, ... F-12 structural finding)
  - title
  - body (full alert text)
  - source_citations (resolution numbers, meeting dates, agenda items, vendors)
  - source_mas_file
  - source_mas_version

This is the ground-truth labeling system for the fine-tuning pipeline.
Each alert becomes a (document, label) training pair once paired with
the primary-source document span it cites.

Author: ODIA AI Team
License: MIT
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Alert ID patterns observed across MAS corpus:
#   VPD-001 through VPD-466
#   PPD-001 through PPD-220
#   TUL-001 through TUL-101
#   LIND-001 through LIND-035
#   FAR-001 through FAR-049
#   WDL-001 through WDL-037
#   DIN-001 through DIN-267
#   EXE-001 through EXE-147
#   TCSO-001 through TCSO-057
ALERT_ID_PATTERN = re.compile(
    r"\b(VPD|PPD|TUL|LIND|FAR|WDL|DIN|EXE|TCSO)[-_]?(\d{3})\b"
)

SEVERITY_PATTERN = re.compile(r"\b(CRITICAL|HIGH|MEDIUM|LOW)\b", re.IGNORECASE)

# Structural finding category (F-1 through F-12)
FINDING_PATTERN = re.compile(r"\bF[-\u2010\u2011]?(\d{1,2})\b")

# Dollar amount extraction
DOLLAR_PATTERN = re.compile(
    r"\$([\d,]+(?:\.\d{2})?)\s*(?:(million|M|thousand|K|billion|B))?",
    re.IGNORECASE,
)

# Resolution / agreement / ordinance number patterns
RESOLUTION_PATTERN = re.compile(
    r"\b(?:Resolution|Res\.?|Ordinance|Ord\.?|Agreement|Agr\.?)"
    r"\s+(?:No\.?\s+)?([0-9]{2,4}[-\u2013][0-9]{2,6}|[0-9]{2,6})\b"
)

# Vendor keywords
VENDOR_KEYWORDS = [
    "Flock Safety",
    "Flock Group",
    "Flock",
    "Flock OS",
    "Flock Nova",
    "Axon Enterprise",
    "Axon",
    "TASER",
    "Evidence.com",
    "Draft One",
    "Fleet 3",
    "Motorola Solutions",
    "Motorola",
    "APX",
    "Spillman",
    "Lexipol",
    "Verkada",
    "BCS Consulting",
    "Spartan Camera",
    "ABH Fox Solutions",
    "SmartWater CSI",
    "Security Lines US",
    "Nexanet",
    "Aerodome",
    "BRINC",
    "DJI",
    "Dell Technologies",
    "T-Mobile",
    "QPCS",
    "Adamson",
    "NEC Corporation",
    "NEC LiveScan",
    "Shotover-Churchill",
    "ActVnet",
    "CML Security",
    "Videray",
    "AMS.NET",
    "Pole Camera",
    "Brief Cam",
    "Avenu",
    "Palantir",
    "Andreessen Horowitz",
    "Founders Fund",
]

STATUTE_KEYWORDS = [
    "SB 524",
    "SB524",
    "AB 481",
    "AB481",
    "SB 978",
    "SB 34",
    "SB 54",
    "Penal Code \u00a713663",
    "Civil Code \u00a71798.90.5",
    "Gov Code \u00a78630",
    "28 CFR Part 23",
    "42 U.S.C. \u00a7 1983",
    "42 U.S.C. \u00a71983",
    "Section 1983",
    "Monell",
    "CJIS",
    "CEQA",
    "Brown Act",
    "CPRA",
    "Government Code \u00a76253",
]


@dataclass
class ExtractedAlert:
    """A single alert extracted from a MAS document."""

    alert_id: str
    jurisdiction: str
    severity: str | None
    finding_category: str | None  # e.g. "F-2"
    title: str
    body: str
    vendors_mentioned: list[str] = field(default_factory=list)
    statutes_mentioned: list[str] = field(default_factory=list)
    resolutions_mentioned: list[str] = field(default_factory=list)
    dollar_amounts: list[str] = field(default_factory=list)
    source_mas_file: str = ""
    source_mas_version: str = ""
    body_char_length: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    def to_jsonl(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# Map alert-ID prefix to canonical jurisdiction name
JURISDICTION_MAP = {
    "VPD": "Visalia",
    "PPD": "Porterville",
    "TUL": "Tulare",
    "LIND": "Lindsay",
    "FAR": "Farmersville",
    "WDL": "Woodlake",
    "DIN": "Dinuba",
    "EXE": "Exeter",
    "TCSO": "TCSO",
}


def extract_vendors(text: str) -> list[str]:
    """Return list of vendor keywords present in text (deduplicated, order-preserving)."""
    hits: list[str] = []
    seen: set[str] = set()
    for vendor in VENDOR_KEYWORDS:
        if vendor.lower() in text.lower() and vendor not in seen:
            hits.append(vendor)
            seen.add(vendor)
    return hits


def extract_statutes(text: str) -> list[str]:
    """Return list of statutory citations present in text (deduplicated)."""
    hits: list[str] = []
    seen: set[str] = set()
    for statute in STATUTE_KEYWORDS:
        if statute.lower() in text.lower() and statute not in seen:
            hits.append(statute)
            seen.add(statute)
    return hits


def extract_resolutions(text: str) -> list[str]:
    """Return all resolution/ordinance/agreement numbers."""
    return list(set(RESOLUTION_PATTERN.findall(text)))


def extract_dollars(text: str) -> list[str]:
    """Return all dollar amounts as raw strings (e.g. '$18,824,577', '$1.556 million')."""
    raw_matches = DOLLAR_PATTERN.findall(text)
    out: list[str] = []
    for amount, scale in raw_matches:
        if scale:
            out.append(f"${amount} {scale}")
        else:
            out.append(f"${amount}")
    return out


def detect_severity(text: str) -> str | None:
    """Return the first severity token found in the text, upper-cased."""
    match = SEVERITY_PATTERN.search(text)
    return match.group(1).upper() if match else None


def detect_finding_category(text: str) -> str | None:
    """Return the first F-N finding category referenced (e.g. 'F-2')."""
    match = FINDING_PATTERN.search(text)
    if not match:
        return None
    num = match.group(1)
    if 1 <= int(num) <= 12:
        return f"F-{num}"
    return None


def _parse_alert_blocks(text: str) -> list[tuple[str, str, str]]:
    """Split MAS text into candidate alert blocks.

    Returns list of (alert_id_string, title_line, body_text) triples.

    A block is the text starting at an alert ID token until the next
    alert ID token (or end of document). The alert-ID search is
    deliberately line-level to tolerate alerts appearing in tables,
    bullet lists, or prose.
    """
    # Find all alert-id match positions
    matches: list[tuple[int, int, str, str]] = []
    for m in ALERT_ID_PATTERN.finditer(text):
        prefix = m.group(1)
        num = m.group(2)
        alert_id = f"{prefix}-{num}"
        matches.append((m.start(), m.end(), alert_id, text[m.start() : m.end()]))

    if not matches:
        return []

    # Deduplicate by alert_id (first occurrence wins); later occurrences are usually cross-refs
    seen_ids: set[str] = set()
    unique: list[tuple[int, int, str]] = []
    for start, end, alert_id, raw in matches:
        if alert_id not in seen_ids:
            unique.append((start, end, alert_id))
            seen_ids.add(alert_id)

    # Build blocks: from each alert position to the next
    blocks: list[tuple[str, str, str]] = []
    for i, (start, _end, alert_id) in enumerate(unique):
        # Expand backward to the line start
        line_start = text.rfind("\n", 0, start) + 1
        # Expand forward to the next alert or end-of-doc
        if i + 1 < len(unique):
            block_end = unique[i + 1][0]
            # Back up to the previous line break
            block_end = text.rfind("\n", 0, block_end)
            if block_end == -1:
                block_end = unique[i + 1][0]
        else:
            block_end = len(text)

        block_text = text[line_start:block_end].strip()
        # Extract title line (first non-empty line)
        lines = [ln for ln in block_text.splitlines() if ln.strip()]
        title_line = lines[0] if lines else alert_id
        # Keep block relatively short: max 2,000 chars per alert
        if len(block_text) > 2000:
            block_text = block_text[:2000]
        blocks.append((alert_id, title_line, block_text))

    return blocks


def extract_alerts_from_file(path: Path) -> list[ExtractedAlert]:
    """Read a MAS markdown file and extract all alerts as ExtractedAlert objects."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    # Determine source MAS version from filename (best-effort)
    version_match = re.search(r"V?(\d+[_\.]\d+)", path.stem)
    version = version_match.group(1).replace("_", ".") if version_match else ""

    results: list[ExtractedAlert] = []
    for alert_id, title, body in _parse_alert_blocks(text):
        prefix = alert_id.split("-")[0]
        jurisdiction = JURISDICTION_MAP.get(prefix, "Unknown")

        alert = ExtractedAlert(
            alert_id=alert_id,
            jurisdiction=jurisdiction,
            severity=detect_severity(body),
            finding_category=detect_finding_category(body),
            title=title[:200],
            body=body,
            vendors_mentioned=extract_vendors(body),
            statutes_mentioned=extract_statutes(body),
            resolutions_mentioned=extract_resolutions(body),
            dollar_amounts=extract_dollars(body),
            source_mas_file=path.name,
            source_mas_version=version,
            body_char_length=len(body),
        )
        results.append(alert)
    return results


def extract_corpus(mas_files: Iterable[Path]) -> list[ExtractedAlert]:
    """Run extraction across a collection of MAS files."""
    all_alerts: list[ExtractedAlert] = []
    for path in mas_files:
        all_alerts.extend(extract_alerts_from_file(path))
    return all_alerts


def write_jsonl(alerts: list[ExtractedAlert], output_path: Path) -> int:
    """Write extracted alerts to a JSONL file. Returns count written."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for alert in alerts:
            f.write(alert.to_jsonl())
            f.write("\n")
    return len(alerts)


def compute_corpus_stats(alerts: list[ExtractedAlert]) -> dict:
    """Summary statistics for an extracted alert corpus."""
    by_jurisdiction: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_finding: dict[str, int] = {}
    vendor_freq: dict[str, int] = {}
    statute_freq: dict[str, int] = {}

    for a in alerts:
        by_jurisdiction[a.jurisdiction] = by_jurisdiction.get(a.jurisdiction, 0) + 1
        if a.severity:
            by_severity[a.severity] = by_severity.get(a.severity, 0) + 1
        if a.finding_category:
            by_finding[a.finding_category] = by_finding.get(a.finding_category, 0) + 1
        for v in a.vendors_mentioned:
            vendor_freq[v] = vendor_freq.get(v, 0) + 1
        for s in a.statutes_mentioned:
            statute_freq[s] = statute_freq.get(s, 0) + 1

    return {
        "total_alerts": len(alerts),
        "by_jurisdiction": by_jurisdiction,
        "by_severity": by_severity,
        "by_finding_category": by_finding,
        "top_vendors": sorted(vendor_freq.items(), key=lambda x: -x[1])[:20],
        "top_statutes": sorted(statute_freq.items(), key=lambda x: -x[1])[:20],
        "avg_body_length": (
            sum(a.body_char_length for a in alerts) // len(alerts) if alerts else 0
        ),
    }
