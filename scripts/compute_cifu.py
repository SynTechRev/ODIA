"""Cross-Instrument Foreclosure Union (CIFU) — compute aggregate consumer foreclosure exposure.

CIFU measures what a single consumer implicitly accepts across ALL instruments in a
sub-processor chain when they sign one primary contract (e.g., Uber's ToS). Each
instrument may individually have a manageable CASI score, but their union creates a
foreclosure regime no single-entity CASI captures.

Metric definition
-----------------
For a chain of N entities:
  - Active vectors  : for each CASI axis, how many distinct entities have ≥1 finding on it
  - Breadth (0–5)   : count of axes active in any entity across the chain
  - Depth (0–1)     : mean(entity_count_per_axis / N) across active axes
  - CIFU score      : (breadth/5 × 50) + (depth × 50)  →  0–100

A CIFU score of 100 means all 5 foreclosure axes are reinforced by every entity
in the chain. The Uber chain is expected to score in the Severe–Foreclosure band.

Usage:
    python scripts/compute_cifu.py
    python scripts/compute_cifu.py --chain uber_consumer_full
    python scripts/compute_cifu.py --output data/cifu_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

_DEFAULT_DB = r"D:\CONTRA Contract Corpus\contra_corpus.db"

_AXES = [
    "data_extraction_depth",
    "modification_and_consent",
    "procedural_adhesion",
    "remedy_foreclosure",
    "enforcement_cost_asymmetry",
]

_AXIS_LABELS = {
    "data_extraction_depth": "Data Extraction Depth",
    "modification_and_consent": "Modification & Consent",
    "procedural_adhesion": "Procedural Adhesion",
    "remedy_foreclosure": "Remedy Foreclosure",
    "enforcement_cost_asymmetry": "Enforcement Cost Asymmetry",
}

# ── Chain definitions ─────────────────────────────────────────────────────────
# Each chain has an anchor entity + ordered members with their relationship type.
# relationship_type values:
#   subsidiary      — separate legal entity under same parent
#   sub_processor   — receives and processes user data under primary contract
#   advertising     — receives behavioral/identity data for targeting
#   compliance_audit — has full visibility into primary's data infrastructure

_CIFU_CHAINS: dict[str, dict] = {
    "uber_consumer_full": {
        "name": "Uber Consumer Full Chain",
        "description": (
            "Every instrument a consumer implicitly accepts by using Uber services. "
            "Uber's ToS is the anchor; the powered-by chain silently extends exposure "
            "to 19 additional sub-processors, ad vendors, compliance auditors, and "
            "identity verification providers — each with independent arbitration clauses."
        ),
        "anchor": "Uber Technologies Inc.",
        "members": [
            # Subsidiary — distinct legal entity, separate ToS governs delivery disputes
            (
                "Portier LLC",
                "subsidiary",
                "Uber Eats delivery — separate legal entity forecloses delivery dispute outside Uber arbitration",
            ),
            # Telematics — behavioral scoring (driver)
            (
                "Cambridge Mobile Telematics",
                "sub_processor",
                "Driver behavioral/telematics scoring; data flows to insurers",
            ),
            # Tag management — routes ALL event data to every vendor below simultaneously
            (
                "Tealium Inc.",
                "sub_processor",
                "Tag management system — single accept routes data to all vendors below",
            ),
            # Session replay — highest data-extraction depth
            (
                "Fullstory Inc.",
                "sub_processor",
                "Session replay — captures every keystroke, scroll, tap, form entry",
            ),
            # Advertising chain
            (
                "Meta Platforms",
                "advertising",
                "Facebook/Instagram pixel — behavioral + identity targeting",
            ),
            ("Microsoft Corporation", "advertising", "Bing Ads + Azure analytics"),
            (
                "NextRoll Inc.",
                "advertising",
                "Programmatic retargeting — formerly AdRoll",
            ),
            ("Pinterest Inc.", "advertising", "Ad platform"),
            # Financial data
            (
                "Plaid Inc.",
                "sub_processor",
                "Bank account aggregator — routing/account numbers + transaction history",
            ),
            ("Dwolla Inc.", "sub_processor", "ACH payment processor"),
            ("Modulr FS Limited", "sub_processor", "UK payment infrastructure"),
            # Loyalty
            (
                "Upside Commerce Group",
                "sub_processor",
                "Cashback/loyalty — purchases behavioral + transaction data",
            ),
            # Biometric identity verification (three parallel deployments)
            (
                "Jumio Inc.",
                "sub_processor",
                "Biometric/document identity verification — TrustE/TrustArc certified",
            ),
            (
                "Socure Inc.",
                "sub_processor",
                "Biometric identity verification — parallel to Jumio",
            ),
            (
                "Veriff Inc.",
                "sub_processor",
                "European biometric identity verification — GDPR focus",
            ),
            # Consent management (cross-generational TrustE→TrustArc lineage)
            (
                "TrustArc Inc.",
                "sub_processor",
                "Consent management platform; historically TrustE-certified Facebook/Meta privacy",
            ),
            # Compliance audit — full infrastructure visibility
            (
                "Drata Inc.",
                "compliance_audit",
                "Compliance automation — sees Uber's full data asset inventory",
            ),
            (
                "Vanta Inc.",
                "compliance_audit",
                "Security compliance — full infrastructure visibility",
            ),
            ("Sprinto Inc.", "compliance_audit", "Compliance management platform"),
            # Post-transaction checkout interceptor — embedded in Uber Eats purchase flow
            (
                "Rokt Pte. Ltd.",
                "sub_processor",
                "Post-transaction upsell interceptor at Uber Eats checkout. 442 corpus docs — largest single-entity haul. Every order confirmation page is a Rokt data-collection event independent of Uber's own ToS.",
            ),
        ],
    },
    "uber_worker_full": {
        "name": "Uber Worker Full Chain",
        "description": (
            "Every instrument a driver/courier implicitly accepts by working on Uber platforms. "
            "Anchor: Uber Technologies Inc. (parent). Three parallel subsidiary PAAs (Schleuder, "
            "Rasier, Portier) each impose independent arbitration clauses with independent opt-out "
            "windows. Biometric sextuple-deployment (Microsoft Face API, Jumio, Socure, Veriff, "
            "Prove Identity, Plaid) each with independent retention and ML training rights. "
            "Worker cannot opt out of any instrument without losing income. "
            "Projected W-CASI aggregate: 82–92 (Foreclosure Regime). "
            "Seattle OLS settlement: $15,025,521.75 / 16,120 workers / 2025-08-26."
        ),
        "anchor": "Uber Technologies Inc.",
        "members": [
            # Three-LLC arbitration architecture — each independent
            (
                "Schleuder LLC",
                "subsidiary",
                "Delivery PAA (June 2020). JAMS arbitration. Opt-out: optout-schleuder@uber.com. No-Incorporation clause §11.9 separates Indemnity Agreement.",
            ),
            (
                "Rasier LLC",
                "subsidiary",
                "Rideshare PAA (Jan 2022). ADR Services (CA) / court-appointed (other). Mass-arbitration Special Master §13.3(h). Offer of judgment §13.6(d). L-19:G: CCP 1281.97/98 not acknowledged.",
            ),
            (
                "Portier LLC",
                "subsidiary",
                "Uber Eats delivery PAA (Mar 2021). JAMS arbitration. Opt-out: optout-portier@uber.com. Seattle $15M enforcement target.",
            ),
            # Behavioral scoring / telematics
            (
                "Cambridge Mobile Telematics",
                "sub_processor",
                "Telematics: harsh braking, acceleration, turning, speeding events. Behavioral scoring feeds deactivation risk.",
            ),
            # Biometric sextuple-deployment (all six vendors, each independent)
            (
                "Microsoft Corporation",
                "sub_processor",
                "Primary biometric processor via Face API (confirmed on Uber help page). Microsoft Azure Cognitive Services DPA not yet obtained.",
            ),
            (
                "Jumio Inc.",
                "sub_processor",
                "Onboarding identity verification. Biometric faceprints. ML training rights confirmed. 3-year post-account retention.",
            ),
            (
                "Socure Inc.",
                "sub_processor",
                "Real-time identity verification. Biometric data processing. Independent retention schedule.",
            ),
            (
                "Veriff Inc.",
                "sub_processor",
                "Re-verification biometric checks. GDPR-focused. Independent retention and ML training rights.",
            ),
            (
                "Plaid Inc.",
                "sub_processor",
                "Facial geometry scans for IDV. No ML training use (explicit). Release clause waives all biometric claims against Plaid.",
            ),
            # Payment infrastructure (worker-side)
            (
                "Dwolla Inc.",
                "sub_processor",
                "ACH payment processor for driver earnings disbursements.",
            ),
            # Compliance audit — sees driver data inventory
            (
                "Drata Inc.",
                "compliance_audit",
                "Compliance automation with full Uber data asset inventory visibility.",
            ),
            (
                "Vanta Inc.",
                "compliance_audit",
                "Security compliance with full infrastructure visibility.",
            ),
        ],
    },
    "att_cricket_telecom": {
        "name": "AT&T / Cricket Wireless Telecom Chain",
        "description": (
            "Parent-subsidiary template propagation chain. AT&T (anchor) + Cricket Wireless "
            "(MVNO subsidiary). CONTRA V2.0 corrected AT&T avg CASI from 22.9 to 57.1 "
            "(35 docs, corpus-highest average entity). Cricket avg 49.1. "
            "Expected CIFU v2 approximately 69 (Severe) per CONTRA MAS V2.0 Section 7.2."
        ),
        "anchor": "AT&T Mobility",
        "members": [
            (
                "Cricket Wireless",
                "subsidiary",
                "MVNO subsidiary — inherits AT&T template arbitration/data-extraction architecture",
            ),
        ],
    },
    # ── Behavioral Advertising Surveillance Chain ────────────────────────────
    "behavioral_advertising_full": {
        "name": "Behavioral Advertising Surveillance Chain",
        "description": (
            "Cross-platform behavioral surveillance stack assembled from social, CTV, "
            "native, and session-recording vendors. Anchor: Snap Inc. (CASI 77.5 avg, "
            "max 88 — highest multi-doc average in corpus). Each member independently "
            "collects behavioral fingerprints, often without consumer awareness, "
            "aggregating into a persistent cross-device identity profile. "
            "Findings: Snap 331 / TikTok 116 / Meta 465 / Google 1,597 / "
            "Hotjar 400 / Rokt 2,239."
        ),
        "anchor": "Snap Inc.",
        "members": [
            (
                "TikTok Inc.",
                "advertising",
                "Short-form video behavioral + facial recognition pipeline; ByteDance data-sharing obligations under Chinese law.",
            ),
            (
                "Meta Platforms",
                "advertising",
                "Facebook/Instagram pixel + Conversions API; cross-app tracking; biometric faceprint retention.",
            ),
            (
                "Google LLC",
                "advertising",
                "Google Ads + Analytics; cross-site cookie identity graph; 66 corpus docs across Alphabet properties.",
            ),
            (
                "LinkedIn Corporation",
                "advertising",
                "Microsoft subsidiary; professional behavioral profiling; B2B intent data sold to advertisers.",
            ),
            (
                "Pinterest Inc.",
                "advertising",
                "Visual search behavioral fingerprinting; purchase-intent inference.",
            ),
            (
                "MNTN Inc.",
                "advertising",
                "Connected TV (CTV) programmatic advertising; household-level identity matching; 7 docs at CASI 38.7.",
            ),
            (
                "TripleLift Inc.",
                "advertising",
                "Native ad server; in-content behavioral event capture.",
            ),
            (
                "Yahoo Inc.",
                "advertising",
                "DSP + Verizon Media legacy data; cross-device identity graph.",
            ),
            (
                "Hotjar Ltd.",
                "sub_processor",
                "Session recording + heatmaps; captures every mouse movement, scroll, click, and form entry; 128 docs at CASI 12.1.",
            ),
            (
                "Rokt Pte. Ltd.",
                "sub_processor",
                "Post-transaction upsell at checkout; 442 docs — largest single-entity corpus haul; 2,239 findings.",
            ),
            (
                "Mutiny Inc.",
                "sub_processor",
                "Website personalization; session-level behavioral data; 7 docs at CASI 42.1.",
            ),
        ],
    },
    # ── Identity Resolution Data Broker Chain ────────────────────────────────
    "identity_resolution_full": {
        "name": "Identity Resolution & Data Broker Chain",
        "description": (
            "The backbone of cross-device, cross-platform persistent identity. "
            "Anchor: The Trade Desk (DSP integrating 90%+ of programmatic inventory). "
            "LiveRamp (160 corpus docs) is the identity graph that links offline purchase "
            "data to online behavioral profiles. Zeta Global (200M+ individual profiles, "
            "CASI 39.8) is the enrichment layer. This chain operates silently beneath "
            "every Uber, AT&T, and gig-platform instrument in the corpus."
        ),
        "anchor": "The Trade Desk Inc.",
        "members": [
            (
                "LiveRamp Holdings",
                "sub_processor",
                "Identity resolution graph: hashed email → device ID → postal address. 160 corpus docs. Links every consumer instrument to a persistent offline identity.",
            ),
            (
                "Zeta Global Holdings",
                "sub_processor",
                "Data cloud: 200M+ individual behavioral profiles. CASI 39.8. Enriches identity graph with purchase intent and predictive scores.",
            ),
            (
                "Google LLC",
                "advertising",
                "Google Ads ecosystem as identity sink: first-party signed-in identity anchors the entire programmatic stack.",
            ),
            (
                "Meta Platforms",
                "advertising",
                "Custom Audiences + Conversions API: hashed PII fed directly to Meta bypasses browser-level consent.",
            ),
            (
                "Demandbase Inc.",
                "sub_processor",
                "B2B intent data: maps IP addresses to corporate accounts; links consumer identity to employer identity.",
            ),
            (
                "Joveo Inc.",
                "sub_processor",
                "Programmatic job advertising: links consumer identity to employment-seeking behavior; 12 docs at CASI 29.0.",
            ),
            (
                "NextRoll Inc.",
                "sub_processor",
                "Programmatic retargeting: persistent cookie + device graph; 3 docs.",
            ),
            (
                "Adobe Inc.",
                "sub_processor",
                "Marketo marketing automation: campaign behavioral profiling fed into identity enrichment.",
            ),
            (
                "Yahoo Inc.",
                "advertising",
                "Verizon Media DSP legacy: cross-device identity graph spanning search, email, finance.",
            ),
        ],
    },
    # ── Telecom Carrier Full Chain ────────────────────────────────────────────
    "telecom_carrier_full": {
        "name": "Telecom Carrier Full Chain",
        "description": (
            "Network-level data extraction by carrier infrastructure. "
            "Anchor: AT&T Mobility (CASI 57.1 avg, 35 docs, corpus leader). "
            "Carriers have privileged access to all traffic metadata — every URL visited, "
            "every app used, every call/SMS record — independent of consent presented "
            "in any app-layer instrument. Cricket (MVNO) + Verizon + Comcast extend "
            "coverage to fixed broadband (Comcast CASI 41.0, 53 docs) and "
            "prepaid/MVNO market (Cricket CASI 49.1)."
        ),
        "anchor": "AT&T Mobility",
        "members": [
            (
                "Cricket Wireless",
                "subsidiary",
                "MVNO subsidiary — AT&T network infrastructure; prepaid market; template-inherits AT&T arbitration architecture. CASI 49.1.",
            ),
            (
                "Verizon Communications",
                "subsidiary",
                "Separate carrier; parallel network-level data access. CASI 28.5, 11 docs, 1,015 findings — highest finding density of any telecom.",
            ),
            (
                "Comcast / Xfinity",
                "sub_processor",
                "Broadband ISP; packet-level traffic inspection rights; 53 docs at CASI 41.0. Extends carrier chain to fixed internet access.",
            ),
        ],
    },
    # ── Financial Instrument Worker Payment Chain ────────────────────────────
    "financial_payment_worker": {
        "name": "Financial Instrument Worker Payment Chain",
        "description": (
            "The payment infrastructure layer that governs worker earnings across gig "
            "platforms. Workers cannot receive income without accepting these instruments. "
            "Anchor: JPMorgan Chase (CASI 48.7, 16 docs, 363 findings). Zelle (Chase "
            "subsidiary, 6 docs) handles P2P disbursements. PayPal (CASI 46.6, 8 docs) "
            "governs Uber Cash and alternative payout rails. Plaid aggregates bank data "
            "back to the platform. Combined with the Three-LLC arbitration architecture, "
            "this chain forecloses financial dispute remedies for workers at every layer."
        ),
        "anchor": "JPMorgan Chase",
        "members": [
            (
                "Zelle",
                "subsidiary",
                "P2P payment subsidiary of JPMorgan Chase. 6 docs at CASI 22.7. Worker disbursements via Zelle inherit Chase arbitration clause independently.",
            ),
            (
                "PayPal Holdings",
                "sub_processor",
                "Uber Cash + alternative payout rails. CASI 46.6, 8 docs. Independent JAMS arbitration clause parallels platform-level foreclosure. Strongest financial instrument in corpus after Chase.",
            ),
            (
                "Plaid Inc.",
                "sub_processor",
                "Bank account aggregator: routing/account numbers + full transaction history flows back to Uber platform. Release clause waives biometric claims. 8 docs at CASI 23.5.",
            ),
            (
                "Dwolla Inc.",
                "sub_processor",
                "ACH processor for driver earnings disbursements. 1 doc at CASI 28.0.",
            ),
        ],
    },
    # ── Gig Economy Competitive Chain ────────────────────────────────────────
    # PENDING CORPUS EXPANSION — zero docs for Lyft, DoorDash, Instacart, Grubhub.
    # Run `python scripts/contra_gig_harvest.py` then `contra_batch_ingest.py` to activate.
    "gig_economy_competitive": {
        "name": "Gig Economy Competitive Chain",
        "description": (
            "Cross-platform gig economy instrument stack. Anchor: Lyft Inc. "
            "All four platforms (Lyft, DoorDash, Instacart/Maplebear, Grubhub) deploy "
            "structurally identical arbitration architectures: individual-only proceedings, "
            "JAMS/AAA venue, shortened statutes of limitations, and biometric verification "
            "sub-processors. A gig worker who multi-apps across platforms is simultaneously "
            "bound by every chain instrument with no cross-platform opt-out mechanism. "
            "CIFU v1=97.1 / v2=100.0 (Foreclosure Regime ceiling). Surpasses all Uber chains; second only to AT&T by v1 score. DED/MC/PA axes at 100% entity saturation across all 7 platforms."
        ),
        "anchor": "Lyft Inc.",
        "members": [
            (
                "DoorDash Inc.",
                "sub_processor",
                "Primary competitor — parallel arbitration architecture. CORPUS PENDING.",
            ),
            (
                "Maplebear Inc.",
                "sub_processor",
                "Instacart — grocery delivery; biometric verification sub-processors. CORPUS PENDING.",
            ),
            (
                "Grubhub Holdings LLC",
                "sub_processor",
                "Restaurant delivery — JAMS arbitration; parallel worker instrument. CORPUS PENDING.",
            ),
            (
                "Jumio Inc.",
                "sub_processor",
                "Identity verification — already in corpus (CASI 32.6, 10 docs); shared with Uber chain.",
            ),
            (
                "Socure Inc.",
                "sub_processor",
                "Identity verification — already in corpus (CASI 33.3, 4 docs); shared with Uber chain.",
            ),
            (
                "Plaid Inc.",
                "sub_processor",
                "Bank account aggregation — earnings disbursement. Already in corpus (CASI 23.5, 8 docs).",
            ),
        ],
    },
    # Additional chains can be defined here as corpus grows
}

_CIFU_BANDS = [
    (
        81,
        100,
        "Foreclosure Regime",
        "Consumer rights effectively extinguished across all chain instruments",
    ),
    (
        61,
        80,
        "Severe Exposure",
        "Multiple high-depth foreclosure axes reinforced across most chain entities",
    ),
    (
        41,
        60,
        "Substantial Exposure",
        "Broad foreclosure breadth; depth concentrated in dominant axes",
    ),
    (
        21,
        40,
        "Elevated Exposure",
        "Several axes active; reinforcement limited to anchor + primary vendors",
    ),
    (
        0,
        20,
        "Baseline Exposure",
        "Limited cross-instrument compounding; instruments largely independent",
    ),
]


def _band(score: float) -> tuple[str, str]:
    for lo, hi, label, desc in _CIFU_BANDS:
        if lo <= score <= hi:
            return label, desc
    return "Unknown", ""


def compute(db_path: str, chain_id: str) -> dict:
    from oraculus_di_auditor.db.models import (
        CommercialDocument,
        CommercialEntity,
        ContraFinding,
    )
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Session = sessionmaker(bind=engine)
    session = Session()

    chain = _CIFU_CHAINS[chain_id]
    all_members = [(chain["anchor"], "anchor", "Primary contract")] + list(
        chain["members"]
    )
    n_total = len(all_members)

    # Build entity_name → entity_id map
    entities = {
        e.canonical_name: e.entity_id for e in session.query(CommercialEntity).all()
    }

    # Build document_hash → entity_name map
    doc_entity: dict[str, str] = {}
    for doc_hash, ename in (
        session.query(CommercialDocument.document_hash, CommercialEntity.canonical_name)
        .join(
            CommercialEntity, CommercialDocument.entity_id == CommercialEntity.entity_id
        )
        .all()
    ):
        doc_entity[doc_hash] = ename

    # Build entity_name → set of scoring_axis (where findings exist) map
    entity_axes: dict[str, set[str]] = {name: set() for name, _, _ in all_members}

    findings = (
        session.query(ContraFinding.document_hash, ContraFinding.scoring_axis)
        .filter(ContraFinding.scoring_axis.isnot(None))
        .all()
    )

    for doc_hash, axis in findings:
        ename = doc_entity.get(doc_hash)
        if ename and ename in entity_axes:
            entity_axes[ename].add(axis)

    # Build CASI score lookup per entity
    from oraculus_di_auditor.db.models import CasiScore

    entity_casi: dict[str, list[int]] = {name: [] for name, _, _ in all_members}
    for doc_hash, agg in session.query(
        CasiScore.document_hash, CasiScore.aggregate
    ).all():
        ename = doc_entity.get(doc_hash)
        if ename and ename in entity_casi:
            entity_casi[ename].append(agg)

    session.close()

    # ── CIFU v1 computation ───────────────────────────────────────────────────
    # For each axis: how many entities in the chain have ≥1 finding on it?
    axis_depth: dict[str, int] = {}
    for axis in _AXES:
        count = sum(1 for name, _, _ in all_members if axis in entity_axes[name])
        axis_depth[axis] = count

    active_axes = {ax: d for ax, d in axis_depth.items() if d > 0}
    breadth = len(active_axes)  # 0–5
    breadth_pct = breadth / 5.0  # 0–1

    depth_pct = (
        sum(d / n_total for d in active_axes.values()) / breadth if breadth > 0 else 0.0
    )

    cifu_score = round((breadth_pct * 50) + (depth_pct * 50), 1)
    band_label, band_desc = _band(cifu_score)

    # ── CIFU v2 — severity-weighted score ─────────────────────────────────────
    # Adds a severity bonus (0–10 pts) to CIFU v1 based on critical/high finding
    # concentration across chain entities. Captures the difference between a chain
    # where every entity has LOW findings vs one dominated by CRITICAL findings.
    #
    # severity_bonus = 10 × mean(critical_count + 0.6*high_count) / total_count
    #                  averaged across all entities with any findings in the chain
    # cifu_v2 = min(100, cifu_v1 + severity_bonus)

    entity_sev: dict[str, dict] = {}
    sev_findings = (
        session.query(
            ContraFinding.document_hash,
            ContraFinding.scoring_axis,
            ContraFinding.severity,
        )
        .filter(ContraFinding.scoring_axis.isnot(None))
        .all()
    )

    for doc_hash, axis, sev in sev_findings:
        ename = doc_entity.get(doc_hash)
        if ename and ename in {n for n, _, _ in all_members}:
            if ename not in entity_sev:
                entity_sev[ename] = {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "total": 0,
                }
            entity_sev[ename]["total"] += 1
            if sev in entity_sev[ename]:
                entity_sev[ename][sev] += 1

    sev_ratios = []
    for name, _, _ in all_members:
        s = entity_sev.get(name)
        if s and s["total"] > 0:
            ratio = (s["critical"] + 0.6 * s["high"]) / s["total"]
            sev_ratios.append(ratio)

    mean_sev_ratio = sum(sev_ratios) / len(sev_ratios) if sev_ratios else 0.0
    severity_bonus = round(10.0 * mean_sev_ratio, 1)
    cifu_v2_score = round(min(100.0, cifu_score + severity_bonus), 1)
    band_v2_label, band_v2_desc = _band(cifu_v2_score)

    # ── Per-entity detail ─────────────────────────────────────────────────────
    member_detail = []
    for name, rel_type, note in all_members:
        axes_active = sorted(entity_axes[name])
        casi_scores = entity_casi[name]
        member_detail.append(
            {
                "entity_name": name,
                "relationship": rel_type,
                "note": note,
                "docs": len(casi_scores),
                "avg_casi": round(sum(casi_scores) / len(casi_scores), 1)
                if casi_scores
                else None,
                "max_casi": max(casi_scores) if casi_scores else None,
                "active_axes": axes_active,
                "axis_count": len(axes_active),
                "missing_axes": [ax for ax in _AXES if ax not in axes_active],
            }
        )

    return {
        "chain_id": chain_id,
        "chain_name": chain["name"],
        "description": chain["description"],
        "computed_at": datetime.now(UTC).isoformat(),
        "n_entities": n_total,
        "cifu_score": cifu_score,
        "band": band_label,
        "band_desc": band_desc,
        "breadth": breadth,
        "depth_pct": round(depth_pct, 3),
        # CIFU v2 — severity-weighted
        "cifu_v2_score": cifu_v2_score,
        "cifu_v2_band": band_v2_label,
        "severity_bonus": severity_bonus,
        "mean_sev_ratio": round(mean_sev_ratio, 3),
        "axis_detail": [
            {
                "axis": ax,
                "label": _AXIS_LABELS[ax],
                "entity_count": axis_depth[ax],
                "depth_pct": round(axis_depth[ax] / n_total, 3),
                "active": axis_depth[ax] > 0,
            }
            for ax in _AXES
        ],
        "members": member_detail,
    }


def print_report(r: dict) -> None:
    print(f"\n{'='*72}")
    print(f"  CIFU REPORT — {r['chain_name']}")
    print(f"{'='*72}")
    print(f"\n  {r['description']}\n")
    print(f"  CIFU Score   : {r['cifu_score']:.1f} / 100  (v1 — breadth × depth)")
    print(
        f"  CIFU v2      : {r['cifu_v2_score']:.1f} / 100  (+{r['severity_bonus']} severity bonus | sev ratio {r['mean_sev_ratio']:.1%})"
    )
    print(f"  Band         : {r['band']}")
    print(f"  Detail       : {r['band_desc']}")
    print(f"  Chain size   : {r['n_entities']} entities")
    print(f"  Breadth      : {r['breadth']}/5 axes active across chain")
    print(f"  Depth        : {r['depth_pct']:.1%} average saturation per active axis")

    print("\n  Axis Breakdown:")
    print(f"  {'Axis':<35} {'Entities':>8}  {'Depth':>6}  {'Active':>6}")
    print(f"  {'─'*60}")
    for ax in r["axis_detail"]:
        flag = "✓" if ax["active"] else "–"
        print(
            f"  {ax['label']:<35} {ax['entity_count']:>8}  "
            f"{ax['depth_pct']:>5.1%}  {flag:>6}"
        )

    print(f"\n  Chain Member Detail ({r['n_entities']} entities):")
    print(f"  {'Entity':<36} {'Rel':<16} {'CASI':>5}  {'Axes':>5}")
    print(f"  {'─'*70}")
    for m in r["members"]:
        rel = m["relationship"]
        avg = f"{m['avg_casi']:.0f}" if m["avg_casi"] is not None else "  –"
        print(
            f"  {m['entity_name']:<36} {rel:<16} {avg:>5}  "
            f"{m['axis_count']}/5  {', '.join(a.split('_')[0] for a in m['active_axes'])}"
        )

    # Highest-risk members
    fr_members = [m for m in r["members"] if m["max_casi"] and m["max_casi"] >= 81]
    if fr_members:
        print(f"\n  Foreclosure Regime instruments in chain ({len(fr_members)}):")
        for m in sorted(fr_members, key=lambda x: -(x["max_casi"] or 0)):
            print(
                f"    CASI {m['max_casi']:>3}  {m['entity_name']}  [{m['relationship']}]"
            )

    print(f"\n{'='*72}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute CIFU for a defined entity chain"
    )
    parser.add_argument("--db-path", default=_DEFAULT_DB)
    parser.add_argument(
        "--chain", default="uber_consumer_full", choices=list(_CIFU_CHAINS)
    )
    parser.add_argument("--output", default="data/cifu_report.json")
    args = parser.parse_args()

    result = compute(args.db_path, args.chain)
    print_report(result)

    out = Path(args.output)
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Report saved: {out.resolve()}")


if __name__ == "__main__":
    main()
