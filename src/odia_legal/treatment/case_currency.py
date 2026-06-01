"""Case-law treatment signal extraction and currency checking.

Maintains a static treatment signal table for cases in the CPRA corpus
and checks whether cases cited in a document are still good law.

Treatment signals:
  GOOD      — still good law; no negative treatment found
  OVERRULED — expressly overruled by subsequent authority
  SUPERSEDED — superseded by statute (e.g. Copley Press by SB 1421)
  DISTINGUISHED — limited by subsequent authority in scope
  LIMITED   — reasoning limited but not overruled
  CRITICIZED — criticized by courts but not overruled

Usage::

    from odia_legal.treatment.case_currency import (
        TreatmentSignal,
        get_treatment,
        check_document_currency,
    )

    result = get_treatment("Copley Press v. Superior Court")
    # → TreatmentSignal(status="SUPERSEDED", ...)

    findings = check_document_currency({"text": "...Copley Press..."})
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from odia_legal.citations.parser import parse_cal_case

# ---------------------------------------------------------------------------
# Treatment signal table
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TreatmentSignal:
    """Treatment status for a case citation."""

    case_id: str
    case_name: str
    citation: str
    status: str
    """GOOD | OVERRULED | SUPERSEDED | DISTINGUISHED | LIMITED | CRITICIZED"""
    superseded_by: str | None = None
    notes: str | None = None
    as_of_year: int | None = None
    doctrinal_weight: float = 1.0


# Static treatment table — updated as authoritative developments occur
_TREATMENT_TABLE: list[TreatmentSignal] = [
    TreatmentSignal(
        case_id="copley_press_v_superior_court_2006",
        case_name="Copley Press",
        citation="39 Cal.4th 1272 (2006)",
        status="SUPERSEDED",
        superseded_by="SB 1421 (Stats. 2018, ch. 988, eff. Jan. 1, 2019)",
        notes="Copley Press held peace officer discipline records categorically confidential. SB 1421 amended Pen. Code § 832.7 to mandate disclosure of use-of-force, sexual assault, and dishonesty records effective January 1, 2019. Copley Press remains good law for records not enumerated in § 832.7(b).",
        as_of_year=2019,
        doctrinal_weight=0.60,
    ),
    TreatmentSignal(
        case_id="chevron_usa_v_nrdc_1984",
        case_name="Chevron U.S.A., Inc. v. Natural Resources Defense Council",
        citation="467 U.S. 837 (1984)",
        status="OVERRULED",
        superseded_by="Loper Bright Enterprises v. Raimondo, 603 U.S. ___ (2024)",
        notes="Loper Bright (2024) expressly overruled Chevron deference. Courts no longer defer to agency interpretations of ambiguous statutes. Administrative law analysis must now apply de novo statutory interpretation.",
        as_of_year=2024,
        doctrinal_weight=0.0,
    ),
    TreatmentSignal(
        case_id="auer_v_robbins_1997",
        case_name="Auer v. Robbins",
        citation="519 U.S. 452 (1997)",
        status="LIMITED",
        superseded_by="Kisor v. Wilkie, 588 U.S. 558 (2019)",
        notes="Kisor substantially narrowed Auer deference. Agency interpretations of their own regulations are entitled to deference only when the regulation is genuinely ambiguous, the interpretation is reasonable, and the interpretation is the agency's authoritative or considered view.",
        as_of_year=2019,
        doctrinal_weight=0.50,
    ),
    TreatmentSignal(
        case_id="cbs_inc_v_block_1986",
        case_name="CBS, Inc. v. Block",
        citation="42 Cal.3d 646 (1986)",
        status="GOOD",
        notes="Still good law; foundational CPRA access case establishing liberal construction and burden on agency.",
        as_of_year=2024,
        doctrinal_weight=0.92,
    ),
    TreatmentSignal(
        case_id="times_mirror_co_v_superior_court_1991",
        case_name="Times Mirror Co. v. Superior Court",
        citation="53 Cal.3d 1325 (1991)",
        status="GOOD",
        notes="Still good law for the § 6255 / § 7922.000 balancing test and deliberative process protection.",
        as_of_year=2024,
        doctrinal_weight=0.91,
    ),
    TreatmentSignal(
        case_id="carpenter_v_united_states_2018",
        case_name="Carpenter v. United States",
        citation="585 U.S. 296 (2018)",
        status="GOOD",
        notes="Still good law; leading digital-privacy precedent; applied to ALPR and tower dump cases.",
        as_of_year=2024,
        doctrinal_weight=0.95,
    ),
    TreatmentSignal(
        case_id="aclu_v_superior_court_2011_alpr",
        case_name="ACLU v. Superior Court (ALPR)",
        citation="202 Cal.App.4th 55 (2011)",
        status="GOOD",
        notes="Still good law for the proposition that § 6254(f) requires particularized showing for bulk surveillance data.",
        as_of_year=2024,
        doctrinal_weight=0.82,
    ),
    TreatmentSignal(
        case_id="los_angeles_county_board_v_superior_court_2016",
        case_name="LA County Board of Supervisors v. Superior Court",
        citation="2 Cal.5th 282 (2016)",
        status="GOOD",
        notes="Still good law for attorney-client privilege scope under CPRA.",
        as_of_year=2024,
        doctrinal_weight=0.93,
    ),
    TreatmentSignal(
        case_id="city_of_san_jose_v_superior_court_2017",
        case_name="City of San Jose v. Superior Court (personal devices)",
        citation="2 Cal.5th 608 (2017)",
        status="GOOD",
        notes="Still good law; personal-device rule for CPRA.",
        as_of_year=2024,
        doctrinal_weight=0.94,
    ),
]

# Build lookup index by case name fragment
_TREATMENT_INDEX: dict[str, TreatmentSignal] = {}
for _t in _TREATMENT_TABLE:
    # Index by case_id
    _TREATMENT_INDEX[_t.case_id] = _t
    # Index by lowercased name fragment
    for _part in _t.case_name.lower().split(" v. "):
        _key = _part.strip().split("(")[0].strip()
        if len(_key) >= 5:
            _TREATMENT_INDEX[_key] = _t


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_treatment(name_or_id: str) -> TreatmentSignal | None:
    """Look up the treatment signal for a case by name fragment or case_id."""
    key = name_or_id.strip().lower()
    # Exact case_id match
    if key in _TREATMENT_INDEX:
        return _TREATMENT_INDEX[key]
    # Partial name match
    for k, signal in _TREATMENT_INDEX.items():
        if key in k or k in key:
            return signal
    return None


def is_good_law(name_or_id: str) -> bool:
    """Return True if the case is still good law (status == GOOD)."""
    signal = get_treatment(name_or_id)
    return signal is None or signal.status == "GOOD"


def treatment_table() -> list[TreatmentSignal]:
    """Return the full treatment signal table."""
    return list(_TREATMENT_TABLE)


def check_document_currency(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """L-8: Scan a document for stale case citations.

    Returns anomaly dicts for any cited cases that are no longer good law.
    """
    text = _get_text(doc)
    if not text:
        return []

    findings: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Parse California case citations
    for cite in parse_cal_case(text):
        party_key = (cite.parties or "").lower().split(" v. ")[0].strip()
        if party_key in seen:
            continue
        seen.add(party_key)

        signal = get_treatment(party_key)
        if signal is None or signal.status == "GOOD":
            continue

        findings.append(
            {
                "id": f"legal:l8:case_currency:{signal.case_id}",
                "issue": f"Cited case {signal.case_name!r} is no longer good law — status: {signal.status}",
                "severity": "high" if signal.status == "OVERRULED" else "medium",
                "layer": "l8_case_currency",
                "details": {
                    "case_name": signal.case_name,
                    "citation": signal.citation,
                    "status": signal.status,
                    "superseded_by": signal.superseded_by,
                    "notes": signal.notes,
                    "doctrinal_weight": signal.doctrinal_weight,
                },
            }
        )

    # Also check for named cases via distinctive-keyword scan
    # Use first word of the plaintiff name (>= 5 chars) as the key trigger
    text_lower = text.lower()
    for signal in _TREATMENT_TABLE:
        if signal.status == "GOOD":
            continue
        if signal.case_id in seen:
            continue
        # Extract a distinctive keyword from the case name (first significant word)
        first_party = signal.case_name.lower().split(" v. ")[0].split(",")[0].strip()
        words = [
            w
            for w in first_party.split()
            if len(w) >= 4 and w not in ("corp", "inc.", "the")
        ]
        distinctive = words[0] if words else first_party
        if distinctive and distinctive in text_lower:
            seen.add(signal.case_id)
            findings.append(
                {
                    "id": f"legal:l8:case_currency:{signal.case_id}",
                    "issue": f"Cited case {signal.case_name!r} is no longer good law — status: {signal.status}",
                    "severity": "high" if signal.status == "OVERRULED" else "medium",
                    "layer": "l8_case_currency",
                    "details": {
                        "case_name": signal.case_name,
                        "citation": signal.citation,
                        "status": signal.status,
                        "superseded_by": signal.superseded_by,
                        "notes": signal.notes,
                        "doctrinal_weight": signal.doctrinal_weight,
                    },
                }
            )

    return findings


def _get_text(doc: dict[str, Any]) -> str:
    for key in ("text", "content", "body", "raw_text"):
        val = doc.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""
