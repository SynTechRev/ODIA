"""CONTRA → odia-v2 training example exporter.

Converts the CONTRA corpus DB (findings + CASI scores + entity/chain context) into
instruction-tuning JSONL examples for odia-v2 fine-tuning. Produces four example types
designed to build commercial contract reasoning capability:

  TYPE 1  — FINDING_EXPLANATION  : "What does this clause mean?" → legal analysis
  TYPE 2  — AXIS_CLASSIFICATION   : "Which CASI axis?" → axis + severity + doctrinal anchor
  TYPE 3  — ENTITY_AUDIT          : "Audit this entity's posture" → CASI profile + risk narrative
  TYPE 4  — CHAIN_AUDIT           : "What foreclosure exposure does this chain create?" → CIFU analysis

Output format: newline-delimited JSON (one example per line), compatible with Unsloth
chat-template fine-tuning (system/user/assistant turns).

Usage:
    python scripts/contra_training_exporter.py
    python scripts/contra_training_exporter.py --out data/contra_training_v1.jsonl
    python scripts/contra_training_exporter.py --types 1,2 --limit 500
    python scripts/contra_training_exporter.py --stats    # count only, no write
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"
_DEFAULT_OUT = _REPO_ROOT / "data" / "contra_training_v1.jsonl"

_SYSTEM_PROMPT = (
    "You are ODIA (Oraculus Decimus Intellect Analyst), a commercial contract auditing "
    "system specializing in California consumer rights, arbitration architecture analysis, "
    "and cross-instrument foreclosure detection. You apply the C.O.N.T.R.A. (Commercial "
    "Obligation & Non-Transparency Risk Analysis) framework using detectors L-11 through "
    "L-20 and the CASI (Commercial Adhesion Severity Index) scoring model. When analyzing "
    "contract clauses, you identify the applicable CASI axis, severity level, doctrinal "
    "authority, and consumer remedies foreclosed. You cite California statutes and case "
    "law precisely. You are precise, analytical, and never speculate beyond the evidence."
)

_AXIS_DESCRIPTIONS = {
    "data_extraction_depth": (
        "Data Extraction Depth (DED) — the breadth and sensitivity of personal data the "
        "instrument authorizes collection of, including biometrics, precise geolocation, "
        "behavioral profiles, and sensitive personal information under CCPA § 1798.121."
    ),
    "modification_and_consent": (
        "Modification & Consent (MC) — unilateral modification rights that allow the "
        "instrument to be changed without meaningful consumer consent, typically through "
        "continued-use acceptance clauses or constructive notice provisions."
    ),
    "procedural_adhesion": (
        "Procedural Adhesion (PA) — take-it-or-leave-it contract conditions, "
        "buried or obscured material terms, and absence of meaningful opt-out "
        "that indicate substantive unconscionability under Armendariz and Sanchez v. Valencia."
    ),
    "remedy_foreclosure": (
        "Remedy Foreclosure (RF) — provisions that eliminate, cap, or procedurally "
        "foreclose the consumer's ability to obtain meaningful relief: jury waivers, "
        "injunctive relief bans, shortened statutes of limitations, damages caps, "
        "PAGA waivers, and biometric data release clauses."
    ),
    "enforcement_cost_asymmetry": (
        "Enforcement Cost Asymmetry (ECA) — clauses that make individual enforcement "
        "prohibitively expensive for consumers: mandatory arbitration at JAMS/AAA, "
        "individual-only proceeding requirements, fee-shifting provisions, and "
        "multi-LLC architecture that multiplies separate arbitration obligations."
    ),
}

_SEVERITY_NARRATIVE = {
    "critical": (
        "CRITICAL severity indicates a per se rights elimination — a clause that "
        "categorically forecloses a California statutory right or constitutes a "
        "pre-dispute waiver that California courts void as against public policy."
    ),
    "high": (
        "HIGH severity indicates substantial rights impairment — terms that "
        "materially disadvantage the consumer but may survive unconscionability "
        "challenge depending on the full contract context."
    ),
    "medium": (
        "MEDIUM severity indicates meaningful rights restriction — provisions that "
        "limit remedies or disclosure obligations but do not categorically eliminate them."
    ),
    "low": (
        "LOW severity indicates standard adhesion language that is procedurally "
        "adhesive but falls within the range of clauses California courts have "
        "not found substantively unconscionable."
    ),
}


def _load_db(db_path: str):
    from sqlalchemy import create_engine

    return create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )


def _generate_type1(engine, limit: int | None) -> list[dict]:
    """Finding explanation: excerpt + axis + anchor → legal analysis."""
    from sqlalchemy import text

    examples = []
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT cf.evidence_excerpt, cf.scoring_axis, cf.severity,
                   cf.doctrinal_anchor, cf.sub_detector, cf.layer, cf.notes,
                   ce.canonical_name, cd.doc_type
            FROM contra_findings cf
            JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
            JOIN commercial_entities ce ON ce.entity_id = cd.entity_id
            WHERE cf.evidence_excerpt IS NOT NULL
              AND length(cf.evidence_excerpt) > 20
              AND cf.scoring_axis IS NOT NULL
              AND cf.severity IN ('critical', 'high')
            ORDER BY RANDOM()
            LIMIT :lim
        """),
            {"lim": limit or 2000},
        ).fetchall()

    for row in rows:
        excerpt, axis, severity, anchor, sub_det, layer, notes, entity, doc_type = row
        axis_desc = _AXIS_DESCRIPTIONS.get(axis, axis)
        sev_narr = _SEVERITY_NARRATIVE.get(severity, severity)

        user_msg = (
            f'Analyze the following clause from a {doc_type or "legal"} document by '
            f'{entity}. Identify the CASI axis, severity level, doctrinal authority, '
            f'and the specific consumer rights at risk.\n\n'
            f'Clause excerpt: "{excerpt}"'
        )

        assistant_msg = (
            f"This clause triggers the **{axis.replace('_', ' ').title()}** CASI axis "
            f"({axis_desc.split(' — ')[0]}).\n\n"
            f"**Severity**: {severity.upper()} — {sev_narr}\n\n"
            f"**Doctrinal authority**: {anchor}\n\n"
            f"**Detector**: {layer}-{sub_det}\n\n"
            f"**Analysis**: {notes or 'This provision operates to restrict consumer rights along the identified axis.'}\n\n"
            f"**Axis definition**: {axis_desc}"
        )

        examples.append(
            {
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ],
                "_meta": {
                    "type": "finding_explanation",
                    "entity": entity,
                    "axis": axis,
                    "severity": severity,
                },
            }
        )
    return examples


def _generate_type2(engine, limit: int | None) -> list[dict]:
    """Axis classification: given clause text → predict axis + severity."""
    from sqlalchemy import text

    examples = []
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
            SELECT cf.evidence_excerpt, cf.scoring_axis, cf.severity, cf.layer, cf.sub_detector
            FROM contra_findings cf
            WHERE cf.evidence_excerpt IS NOT NULL
              AND length(cf.evidence_excerpt) > 30
              AND cf.scoring_axis IS NOT NULL
            ORDER BY RANDOM()
            LIMIT :lim
        """),
            {"lim": limit or 1500},
        ).fetchall()

    for row in rows:
        excerpt, axis, severity, layer, sub_det = row

        user_msg = (
            f"Classify the following contract clause using the CASI framework. "
            f"Identify: (1) the primary CASI axis, (2) severity level, "
            f"(3) which detector sub-type applies.\n\n"
            f'Clause: "{excerpt}"'
        )
        assistant_msg = (
            f"**Primary CASI axis**: {axis.replace('_', ' ').title()} ({axis})\n\n"
            f"**Severity**: {severity.upper()}\n\n"
            f"**Detector**: {layer}, sub-detector {sub_det}\n\n"
            f"**Axis rationale**: {_AXIS_DESCRIPTIONS.get(axis, '').split(' — ')[1] if ' — ' in _AXIS_DESCRIPTIONS.get(axis, '') else _AXIS_DESCRIPTIONS.get(axis, '')}"
        )

        examples.append(
            {
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ],
                "_meta": {
                    "type": "axis_classification",
                    "axis": axis,
                    "severity": severity,
                },
            }
        )
    return examples


def _generate_type3(engine, limit: int | None) -> list[dict]:
    """Entity audit: entity name + corpus stats → CASI profile narrative."""
    from sqlalchemy import text

    examples = []
    with engine.connect() as conn:
        entities = conn.execute(
            text("""
            SELECT ce.canonical_name, ce.corporate_family,
                   COUNT(DISTINCT cd.document_hash) as docs,
                   AVG(cs.aggregate) as avg_casi, MAX(cs.aggregate) as max_casi,
                   COUNT(DISTINCT cf.id) as findings
            FROM commercial_entities ce
            JOIN commercial_documents cd ON cd.entity_id = ce.entity_id
            LEFT JOIN casi_scores cs ON cs.document_hash = cd.document_hash
            LEFT JOIN contra_findings cf ON cf.document_hash = cd.document_hash
            GROUP BY ce.canonical_name, ce.corporate_family
            HAVING docs >= 3 AND avg_casi IS NOT NULL
            ORDER BY avg_casi DESC
            LIMIT :lim
        """),
            {"lim": limit or 30},
        ).fetchall()

        for ent_row in entities:
            name, family, docs, avg_casi, max_casi, findings = ent_row

            # Axis breakdown
            axis_rows = conn.execute(
                text("""
                SELECT cf.scoring_axis, cf.severity, COUNT(*) as cnt
                FROM contra_findings cf
                JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
                JOIN commercial_entities ce ON ce.entity_id = cd.entity_id
                WHERE ce.canonical_name = :name AND cf.scoring_axis IS NOT NULL
                GROUP BY cf.scoring_axis, cf.severity
                ORDER BY cf.scoring_axis, cf.severity
            """),
                {"name": name},
            ).fetchall()

            axis_summary: dict[str, dict] = {}
            for ax, sev, cnt in axis_rows:
                if ax not in axis_summary:
                    axis_summary[ax] = {"total": 0, "critical": 0, "high": 0}
                axis_summary[ax]["total"] += cnt
                if sev in ("critical", "high"):
                    axis_summary[ax][sev] += cnt

            if not axis_summary:
                continue

            axis_lines = "\n".join(
                f"  - {ax.replace('_',' ').title()}: {v['total']} findings "
                f"({v['critical']} critical, {v['high']} high)"
                for ax, v in sorted(axis_summary.items(), key=lambda x: -x[1]["total"])
            )

            band = (
                "Foreclosure Regime"
                if avg_casi >= 81
                else "Severe"
                if avg_casi >= 61
                else "Substantial"
                if avg_casi >= 41
                else "Elevated"
                if avg_casi >= 21
                else "Baseline"
            )

            user_msg = (
                f"Provide a C.O.N.T.R.A. audit profile for {name}"
                + (f" ({family})" if family else "")
                + f". The corpus contains {docs} documents with {findings} findings."
            )

            assistant_msg = (
                f"## C.O.N.T.R.A. Audit Profile: {name}\n\n"
                + (f"**Corporate family**: {family}\n\n" if family else "")
                + f"**Corpus coverage**: {docs} documents | {findings} findings\n\n"
                f"**CASI score**: {avg_casi:.1f} avg / {max_casi} max — **{band}** band\n\n"
                f"**Axis coverage**:\n{axis_lines}\n\n"
                f"**Risk assessment**: "
                + (
                    f"{name} operates in the {band} CASI band, indicating "
                    + (
                        "that consumer rights are effectively extinguished across all five foreclosure axes. "
                        "The multi-document pattern demonstrates systematic deployment of arbitration architecture, "
                        "data extraction clauses, and remedy foreclosure provisions across the entity's full "
                        "instrument suite."
                        if band == "Foreclosure Regime"
                        else "substantial cross-axis exposure requiring priority review of arbitration, "
                        "modification consent, and remedy foreclosure provisions."
                        if band in ("Severe", "Substantial")
                        else "elevated individual-axis exposure that does not yet constitute systematic foreclosure "
                        "but warrants monitoring across the consumer's full instrument portfolio."
                    )
                )
            )

            examples.append(
                {
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": assistant_msg},
                    ],
                    "_meta": {
                        "type": "entity_audit",
                        "entity": name,
                        "avg_casi": round(avg_casi, 1),
                    },
                }
            )

    return examples


def _generate_type4(engine, limit: int | None) -> list[dict]:
    """Chain audit: import chain definitions from compute_cifu and generate CIFU narratives."""
    import importlib.util

    cifu_path = _REPO_ROOT / "scripts" / "compute_cifu.py"
    spec = importlib.util.spec_from_file_location("compute_cifu", cifu_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    examples = []
    db_path = engine.url.database

    for chain_id, chain_def in list(mod._CIFU_CHAINS.items()):
        try:
            r = mod.compute(db_path, chain_id)
        except Exception:
            continue

        anchor = chain_def["anchor"]
        n = r["n_entities"]
        cifu = r["cifu_score"]
        band = r["band"]

        axis_lines = "\n".join(
            f"  - {d['label']}: {d['entity_count']}/{n} entities active "
            f"({d['depth_pct']:.0%} depth)"
            for d in r["axis_detail"]
            if d["active"]
        )

        member_names = ", ".join(m["entity_name"] for m in r["members"][:5])
        if n > 6:
            member_names += f", and {n - 5} others"

        user_msg = (
            f"Analyze the cross-instrument foreclosure exposure for the "
            f"{chain_def['name']}. The anchor entity is {anchor}. "
            f"What CIFU score does this chain produce and what does it mean for consumers?"
        )

        assistant_msg = (
            f"## CIFU Analysis: {chain_def['name']}\n\n"
            f"**Chain description**: {chain_def['description']}\n\n"
            f"**CIFU score**: {cifu}/100 — **{band}**\n\n"
            f"**Chain composition**: {n} entities including {member_names}\n\n"
            f"**Active foreclosure axes**:\n{axis_lines}\n\n"
            f"**Interpretation**: {r['band_desc']} "
            + (
                f"The {n}-entity chain creates compounding exposure: a consumer who "
                f"accepts {anchor}'s primary instrument implicitly accepts the data "
                f"collection, arbitration, and remedy foreclosure provisions of all "
                f"{n - 1} downstream instruments simultaneously — each with independent "
                f"foreclosure architecture. No single CASI score captures this aggregate "
                f"exposure; only cross-instrument CIFU analysis reveals the full foreclosure regime."
                if cifu >= 81
                else f"The chain creates substantial compounding risk across {r['breadth']} "
                f"of 5 possible foreclosure axes."
            )
        )

        examples.append(
            {
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ],
                "_meta": {"type": "chain_audit", "chain_id": chain_id, "cifu": cifu},
            }
        )

    return examples


def _generate_type5(engine, limit: int | None) -> list[dict]:
    """Doctrine Application: doctrinal_anchor + finding excerpt → statutory analysis.

    For each unique anchor with enough findings, generates an example explaining
    exactly how the statute applies to the contract clause — building citation-grounded
    legal reasoning capability.
    """
    from sqlalchemy import text

    # Anchor descriptions mapping anchor ID → human-readable statute text
    _ANCHOR_LABELS = {
        "CCPA_1798_100": "California Civil Code § 1798.100 (CCPA — right to know)",
        "CCPA_1798_110": "California Civil Code § 1798.110 (CCPA — categories of personal information)",
        "CCPA_1798_115": "California Civil Code § 1798.115 (CCPA — sharing of personal information)",
        "CCPA_1798_120": "California Civil Code § 1798.120 (CCPA — right to opt out of sale)",
        "CCPA_121": "California Civil Code § 1798.121 (CPRA — sensitive personal information)",
        "CCPA_125": "California Civil Code § 1798.125 (CCPA — non-discrimination for exercising rights)",
        "CCP_1281_97": "California Code of Civil Procedure § 1281.97 (employer/consumer arbitration deadlines)",
        "CCP_1281_98": "California Code of Civil Procedure § 1281.98 (arbitration fee waiver trigger)",
        "FAA_9": "9 U.S.C. § 2 (Federal Arbitration Act — written arbitration provision)",
        "FAA_3": "9 U.S.C. § 3 (Federal Arbitration Act — stay of proceedings pending arbitration)",
        "BIPA_15": "740 ILCS 14/15 (Biometric Information Privacy Act, section 15 — duties of private entities)",
        "BIPA_20": "740 ILCS 14/20 (Biometric Information Privacy Act, section 20 — private right of action)",
        "FCRA_616": "15 U.S.C. § 1681n (Fair Credit Reporting Act — civil liability for willful noncompliance)",
        "PLAID_FTC": "In re Plaid Inc., FTC File No. 2023169 (Consent Order, Aug. 2022)",
        "CCP_1670_5": "California Code of Civil Procedure § 1670.5 (unconscionable contract provisions)",
        "CAL_LABOR_2699": "California Labor Code § 2699 (Private Attorneys General Act — PAGA civil penalties)",
        "AB_51": "California AB 51 (Gov. Code § 12953 — mandatory arbitration ban for employees)",
    }

    _ANCHOR_ANALYSIS = {
        "CCPA_121": (
            "CCPA § 1798.121 (as amended by CPRA, effective Jan 1, 2023) imposes a heightened opt-in "
            "consent requirement for use of 'sensitive personal information' (SPI), which includes "
            "precise geolocation, racial/ethnic origin, biometric data for identification, and health "
            "information. An instrument that collects SPI without a specific, separate opt-in consent "
            "mechanism violates § 1798.121(a). The provision is self-executing for California residents "
            "and does not require a private right of action — CPPA enforcement is the primary remedy "
            "channel, but consumers may also raise § 1798.121 in conjunction with § 1798.150 (statutory "
            "damages) when a data breach involves SPI."
        ),
        "CCP_1281_97": (
            "CCP § 1281.97 (eff. 2020, amended 2022) requires that the drafting party in an "
            "employment or consumer arbitration pay all arbitration fees and costs within 30 days of "
            "the due date. Failure triggers a material breach of the arbitration agreement, and the "
            "consumer may withdraw the claim from arbitration and proceed in court. Courts have "
            "broadly held that § 1281.97 cannot be waived by contract (Ramirez v. Charter "
            "Communications, 2024). An instrument that attempts to shift fees to the consumer or "
            "that omits the 30-day cure period is facially unconscionable under this section."
        ),
        "CCP_1670_5": (
            "CCP § 1670.5 codifies the common-law doctrine of unconscionability in California. "
            "A court may refuse enforcement of a contract or any clause it finds unconscionable at "
            "the time it was made (§ 1670.5(a)). California courts apply a two-part test: "
            "procedural unconscionability (oppression or surprise) and substantive unconscionability "
            "(overly harsh or one-sided terms). Arbitration clauses in adhesion contracts presumptively "
            "satisfy procedural unconscionability (Armendariz v. Foundation Health Psychcare, 2000); "
            "substantive unconscionability is established by fee-shifting, eliminating discovery, "
            "or stripping public injunctive relief."
        ),
        "CAL_LABOR_2699": (
            "Labor Code § 2699 (PAGA) allows an 'aggrieved employee' to sue on behalf of the state "
            "for civil penalties for Labor Code violations. Unlike class actions, PAGA claims cannot "
            "be waived in arbitration agreements (Viking River Cruises v. Moriana, 2022, as modified "
            "by Adolph v. Uber, Cal. S. Ct. 2023). An instrument that purports to waive PAGA claims "
            "or require individual-only arbitration of PAGA claims is per se unenforceable as to the "
            "representative (non-individual) PAGA claims, even if the individual PAGA claim is "
            "validly arbitrated."
        ),
    }

    examples = []
    with engine.connect() as conn:
        # Get doctrinal anchors with substantial findings
        anchors = conn.execute(
            text("""
            SELECT cf.doctrinal_anchor, cf.scoring_axis,
                   COUNT(*) as cnt,
                   cf.severity
            FROM contra_findings cf
            WHERE cf.doctrinal_anchor IS NOT NULL
              AND cf.evidence_excerpt IS NOT NULL
              AND LENGTH(cf.evidence_excerpt) > 100
            GROUP BY cf.doctrinal_anchor, cf.scoring_axis, cf.severity
            HAVING cnt >= 3
            ORDER BY cnt DESC
        """)
        ).fetchall()

        processed: set[str] = set()
        for anchor, axis, cnt, severity in anchors:
            if anchor in processed:
                continue
            if limit and len(examples) >= limit:
                break

            # Pull representative findings for this anchor
            findings = conn.execute(
                text("""
                SELECT cf.evidence_excerpt, cf.layer, cf.severity,
                       cd.doc_type, ce.canonical_name
                FROM contra_findings cf
                JOIN commercial_documents cd ON cd.document_hash = cf.document_hash
                JOIN commercial_entities ce ON ce.entity_id = cd.entity_id
                WHERE cf.doctrinal_anchor = :anchor
                  AND cf.evidence_excerpt IS NOT NULL
                  AND LENGTH(cf.evidence_excerpt) > 100
                ORDER BY cf.severity DESC, RANDOM()
                LIMIT 3
            """),
                {"anchor": anchor},
            ).fetchall()

            if not findings:
                continue

            processed.add(anchor)
            anchor_label = _ANCHOR_LABELS.get(anchor, anchor)

            # Try to pull live statutory text from CPRACorpusLoader first
            analysis_boilerplate = ""
            try:
                import sys as _sys

                _sys.path.insert(0, str(_REPO_ROOT / "src"))
                from oraculus_di_auditor.legal.cpra_corpus import (
                    CPRACorpusLoader as _CPRALoader,
                )

                _cpra = _CPRALoader()
                _lt = _cpra.resolve_anchor(anchor)
                if _lt:
                    analysis_boilerplate = f"{_lt.title}\n\n{_lt.text[:1200]}"
            except Exception:
                pass
            if not analysis_boilerplate:
                analysis_boilerplate = _ANCHOR_ANALYSIS.get(anchor, "")

            # Use the most severe finding as the example excerpt
            excerpt, layer, sev, doc_type, entity = findings[0]
            excerpt_trunc = excerpt[:600] + ("…" if len(excerpt) > 600 else "")

            user_msg = (
                f"Explain how {anchor_label} applies to the following contract clause:\n\n"
                f"**Entity**: {entity}\n"
                f"**Document type**: {doc_type}\n"
                f"**Detector**: {layer} (severity: {sev})\n\n"
                f"**Clause excerpt**:\n> {excerpt_trunc}"
            )

            other_entities = list({f[4] for f in findings[1:] if f[4] != entity})
            cross_entity_note = (
                f" This pattern appears in {len(findings)} instruments across the corpus "
                f"(also in: {', '.join(other_entities[:2])})."
                if other_entities
                else ""
            )

            assistant_msg = (
                f"## Doctrine Application: {anchor_label}\n\n"
                f"**Statutory text and scope**:\n"
                + (
                    analysis_boilerplate
                    if analysis_boilerplate
                    else f"{anchor_label} establishes obligations applicable to this clause."
                )
                + f"\n\n**Application to this clause**:\n"
                f"The clause excerpt triggers {anchor} because it "
                + (
                    "collects, processes, or shares sensitive personal information as defined by the statute "
                    "without a separate opt-in consent mechanism as required by § 1798.121(a)."
                    if "CCPA_121" in anchor
                    else "imposes a fee-shifting or cost-allocation structure that violates the mandatory 30-day "
                    "fee payment requirement established by § 1281.97."
                    if "1281_97" in anchor
                    else "contains provisions that are procedurally adhesive and substantively one-sided, meeting "
                    "the Armendariz two-prong unconscionability standard under § 1670.5."
                    if "1670_5" in anchor
                    else "attempts to waive the worker's representative PAGA standing in a manner that conflicts "
                    "with the California Supreme Court's holding in Adolph v. Uber (2023)."
                    if "2699" in anchor
                    else "contains terms that directly conflict with the statutory requirements."
                )
                + f"{cross_entity_note}\n\n"
                f"**Consumer remedies**:\n"
                f"A California consumer facing this clause may: (1) file a complaint with the CPPA or "
                f"California AG; (2) raise this provision as a defense in any arbitration proceeding "
                f"citing {anchor}; (3) seek declaratory relief in superior court that the clause is "
                f"unenforceable; (4) in appropriate cases, pursue class relief where the clause is "
                f"systematically deployed across consumer instruments."
            )

            examples.append(
                {
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": assistant_msg},
                    ],
                    "_meta": {
                        "type": "doctrine_application",
                        "anchor": anchor,
                        "axis": axis,
                        "severity": severity,
                        "example_count": cnt,
                    },
                }
            )

    return examples


def _generate_type6(engine, limit: int | None) -> list[dict]:
    """Cross-chain comparison: two chains → compare arbitration architecture, CIFU, shared entities."""
    import importlib
    import sys

    examples = []

    # Load chain definitions and compute scores
    _scripts = Path(__file__).resolve().parents[0]
    sys.path.insert(0, str(_scripts))
    try:
        cifu_mod = importlib.import_module("compute_cifu")
    except ModuleNotFoundError:
        return examples

    chains_raw = cifu_mod._CIFU_CHAINS  # type: ignore[attr-defined]
    compute = cifu_mod.compute  # type: ignore[attr-defined]
    _band = cifu_mod._band  # type: ignore[attr-defined]

    # Compute scores for all chains
    chain_results: dict[str, dict] = {}
    db_path = engine.url.database
    for cid in chains_raw:
        try:
            r = compute(db_path, cid)
            chain_results[cid] = r
        except Exception:
            pass

    if len(chain_results) < 2:
        return examples

    chain_ids = sorted(
        chain_results.keys(), key=lambda c: -chain_results[c]["cifu_score"]
    )

    # Generate pairwise comparisons — focus on highest-CIFU pairs first, then cross-sector
    pairs: list[tuple[str, str]] = []
    # High vs mid
    for i in range(min(4, len(chain_ids))):
        for j in range(i + 1, len(chain_ids)):
            pairs.append((chain_ids[i], chain_ids[j]))
    # Limit to most informative
    pairs = pairs[: limit or 12]

    for cid_a, cid_b in pairs:
        ra = chain_results[cid_a]
        rb = chain_results[cid_b]
        da = chains_raw[cid_a]
        db_ = chains_raw[cid_b]

        # Find shared entities
        members_a = {m[0] for m in da["members"]}
        members_b = {m[0] for m in db_["members"]}
        members_a.add(da["anchor"])
        members_b.add(db_["anchor"])
        shared = members_a & members_b

        name_a = da["name"]
        name_b = db_["name"]
        cifu_a = ra["cifu_score"]
        cifu_b = rb["cifu_score"]
        band_a = ra["band"]
        band_b = rb["band"]

        axes_a = {ax["axis"]: ax["depth_pct"] for ax in ra.get("axis_detail", [])}
        axes_b = {ax["axis"]: ax["depth_pct"] for ax in rb.get("axis_detail", [])}

        axis_cmp = []
        for ax_key in sorted(set(list(axes_a) + list(axes_b))):
            ax_label = ax_key.replace("_", " ").title()
            a_val = round(axes_a.get(ax_key, 0) * 100, 0)
            b_val = round(axes_b.get(ax_key, 0) * 100, 0)
            delta = a_val - b_val
            direction = "higher" if delta > 0 else ("lower" if delta < 0 else "equal")
            axis_cmp.append(
                f"  - {ax_label}: {name_a.split()[0]} {a_val:.0f}% vs {name_b.split()[0]} {b_val:.0f}%"
                + (
                    f" ({abs(delta):.0f}pp {direction} in {name_a.split()[0]})"
                    if delta != 0
                    else ""
                )
            )

        user_msg = (
            f"Compare the foreclosure architecture of the '{name_a}' and the '{name_b}' "
            f"in the C.O.N.T.R.A. corpus. How do their CIFU scores, axis profiles, and "
            f"shared-entity exposure differ?"
        )

        shared_note = (
            f"\n\n**Shared entities** ({len(shared)}): {', '.join(sorted(shared)[:5])}"
            + (" and others." if len(shared) > 5 else ".")
            + " Consumers bound by both chains face compounding exposure through these shared instruments."
            if shared
            else ""
        )

        assistant_msg = (
            f"## Cross-Chain Comparison: {name_a} vs {name_b}\n\n"
            f"**CIFU scores**:\n"
            f"  - {name_a}: {cifu_a}/100 ({band_a})\n"
            f"  - {name_b}: {cifu_b}/100 ({band_b})\n"
            f"  - Delta: {abs(cifu_a - cifu_b):.1f} points — "
            + (
                f"{name_a} is the more severe foreclosure structure."
                if cifu_a > cifu_b
                else f"{name_b} is the more severe foreclosure structure."
                if cifu_b > cifu_a
                else "both chains are equivalently severe."
            )
            + "\n\n**Axis-by-axis comparison**:\n"
            + "\n".join(axis_cmp)
            + shared_note
            + f"\n\n**Structural comparison**:\n"
            f"{name_a} has {ra['n_entities']} entities across {sum(m.get('docs',0) for m in ra.get('members',[]))} documents, "
            f"while {name_b} has {rb['n_entities']} entities across {sum(m.get('docs',0) for m in rb.get('members',[]))} documents. "
            + (
                "Document volume reflects corpus penetration but does not automatically indicate higher severity — "
                "CIFU measures structural breadth and depth, not document volume."
            )
            + "\n\n**Chain-crossing consumer risk**:\n"
            + (
                f"A consumer who uses services from both chains is simultaneously bound by "
                f"{ra['n_entities'] + rb['n_entities'] - len(shared)} independent instruments "
                f"({len(shared)} shared) with independent arbitration architectures, independent "
                f"opt-out windows, and independent data collection rights. No single instrument "
                f"discloses this aggregate exposure."
                if shared
                else "These chains operate independently with no shared entities, but a consumer who "
                "uses services from both faces additive foreclosure exposure with no cross-chain "
                "opt-out mechanism."
            )
        )

        examples.append(
            {
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg},
                ],
                "_meta": {
                    "type": "cross_chain_comparison",
                    "chain_a": cid_a,
                    "chain_b": cid_b,
                    "cifu_a": cifu_a,
                    "cifu_b": cifu_b,
                    "shared_entities": len(shared),
                },
            }
        )

    return examples


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export CONTRA training JSONL for odia-v2"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument("--out", default=str(_DEFAULT_OUT))
    parser.add_argument(
        "--types",
        default="1,2,3,4,5,6",
        help="Comma-separated example types to generate (1-6)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Per-type example limit (default: all)"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Print counts only, do not write file"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing file rather than overwriting (deduplicates by content hash)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    engine = _load_db(args.db_path)
    requested = {int(t.strip()) for t in args.types.split(",")}

    all_examples: list[dict] = []

    generators = {
        1: ("Finding Explanation", _generate_type1),
        2: ("Axis Classification", _generate_type2),
        3: ("Entity Audit", _generate_type3),
        4: ("Chain Audit", _generate_type4),
        5: ("Doctrine Application", _generate_type5),
        6: ("Cross-Chain Comparison", _generate_type6),
    }

    for type_id, (label, gen_fn) in generators.items():
        if type_id not in requested:
            continue
        print(f"  Generating type {type_id} ({label})...", end=" ", flush=True)
        examples = gen_fn(engine, args.limit)
        print(f"{len(examples)} examples")
        all_examples.extend(examples)

    # Strip _meta from output (keep for stats only)
    total = len(all_examples)
    print(f"\nTotal examples: {total}")
    type_counts = {}
    for ex in all_examples:
        t = ex["_meta"]["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    for t, cnt in type_counts.items():
        print(f"  {t:<28} {cnt:>5}")

    if args.stats:
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Dedup by message content hash when appending
    existing_hashes: set[str] = set()
    if args.append and out_path.exists():
        import hashlib

        with out_path.open("r", encoding="utf-8") as f:
            for line in f:
                existing_hashes.add(hashlib.sha256(line.encode()).hexdigest())
        print(f"Existing file: {len(existing_hashes)} examples loaded for dedup")

    mode = "a" if args.append else "w"
    new_count = 0
    with out_path.open(mode, encoding="utf-8") as f:
        for ex in all_examples:
            clean = {k: v for k, v in ex.items() if k != "_meta"}
            line = json.dumps(clean, ensure_ascii=False) + "\n"
            if args.append:
                import hashlib

                h = hashlib.sha256(line.encode()).hexdigest()
                if h in existing_hashes:
                    continue
                existing_hashes.add(h)
            f.write(line)
            new_count += 1

    action = "Appended" if args.append else "Saved"
    print(f"\n{action} {new_count} examples → {out_path}")
    print(f"Timestamp: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    main()
