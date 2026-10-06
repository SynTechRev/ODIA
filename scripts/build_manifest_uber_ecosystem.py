"""Build CONTRA manifests for the full Uber sub-processor + partner ecosystem.

NSU (No Stone Unturned) routing of all 130+ documents across 20 distinct entities.
Handles nested subfolder structure (Facebook/TrustArc, Meta/TrustArc), per-vendor
reject lists, and cross-entity routing (Drata/Google API doc → Google LLC).

Entity graph:
  Uber Technologies Inc. (core)
    ├── Portier LLC               (delivery entity — separate legal person)
    ├── Cambridge Mobile Telematics (driver behavioral scoring)
    │
    ├── Identity verification chain:
    │     Jumio Inc.              (biometrics — TrustE/TrustArc certified)
    │     Socure Inc.             (biometrics — Jumio competitor)
    │     Veriff Inc.             (biometrics — EU/GDPR focus)
    │
    ├── Compliance/audit chain:
    │     Vanta Inc.              (security compliance automation)
    │     Drata Inc.              (compliance automation)
    │     Sprinto Inc.            (compliance automation)
    │
    ├── Data/payment chain:
    │     Plaid Inc.              (financial data aggregator)
    │     Dwolla Inc.             (ACH payments)
    │     Modulr FS Limited       (UK payment infrastructure)
    │     Upside Commerce Group   (loyalty/rewards)
    │
    ├── Data routing / tag management:
    │     Tealium Inc.            (TMS — routes ALL event data to every vendor below)
    │
    ├── Advertising chain:
    │     Meta Platforms          (ad targeting — Facebook/Instagram)
    │     │   └── TrustArc Inc.  (consent mgmt for Meta; historically TrustE-certified)
    │     Microsoft Corporation   (Bing Ads / analytics)
    │     NextRoll Inc.           (programmatic retargeting)
    │     Pinterest Inc.          (ad platform)
    │
    ├── Session replay:
    │     Fullstory Inc.          (behavioral analytics — sees every user interaction)
    │
    ├── Consent management (cross-cutting):
    │     TrustArc Inc.           (TrustE successor; certifies Meta AND manages Uber consent)
    │         ├── deployed at Facebook/TrustArc/ (historical FB privacy certification)
    │         └── deployed at Meta/TrustArc/     (current Meta consent infrastructure)
    │
    └── Google LLC                (supplement to existing corpus entity)

Usage:
    python scripts/build_manifest_uber_ecosystem.py --dry-run
    python scripts/build_manifest_uber_ecosystem.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_UBER_ROOT = Path(r"D:\CONTRA Contract Corpus\Uber Technologies Inc")

# ── Root-level file routing ────────────────────────────────────────────────────
# None = reject (not a consumer-facing legal instrument)

_ROOT_ROUTING: dict[str, dict | None] = {
    "Uber U.S. Terms of Use.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "THE NEW UBER PRO TERMS AND CONDITIONS.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "Uber Pro Terms And Conditions 2026.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
        "version_label": "2026",
    },
    "Uber Cookie Notice (Global).pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver and Delivery Person Privacy Notice.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver and Delivery Person Privacy Notice (1).pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Driver Privacy Notice.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "privacy_notice",
    },
    "Uber Guidelines for Third Party Data Requests and Service of Legal Documents_.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "Uber use of Cambridge Mobile Telematics.pdf": {
        "entity_name": "Uber Technologies Inc.",
        "corporate_family": "Uber",
        "doc_type": "tos",
    },
    "Portier LLC Terms and Conditions.pdf": {
        "entity_name": "Portier LLC",
        "corporate_family": "Uber",
        "doc_type": "tos",
        "note": "Uber Eats delivery operations — separate legal entity from Uber Technologies Inc.",
    },
    "Cambridge Mobile Telematics PRIVACY POLICY.pdf": {
        "entity_name": "Cambridge Mobile Telematics",
        "corporate_family": "Cambridge Mobile Telematics",
        "doc_type": "privacy_notice",
        "note": "Driver behavioral/telematics scoring vendor deployed by Uber",
    },
    "Google Analytics Privacy Notice Safeguarding your data.pdf": {
        "entity_name": "Google LLC",
        "corporate_family": "Alphabet",
        "doc_type": "privacy_notice",
    },
    "How Google uses information from sites or apps that use our services.pdf": {
        "entity_name": "Google LLC",
        "corporate_family": "Alphabet",
        "doc_type": "privacy_notice",
    },
    # ── Rejects ──
    "European Commission Standard Contractual Clauses (SCC).pdf": None,
    "Office of Privacy and Open Government Privacy Laws, Policies and Guidance.pdf": None,
    "Salesloft Cookie Notice.pdf": None,
    "ITA PRIVACY PROGRAM.pdf": None,
}

# ── Subfolder entity map ───────────────────────────────────────────────────────
# key = relative subfolder path from _UBER_ROOT
# value = entity info + per-file reject list

_SUBFOLDER_MAP: dict[str, dict] = {
    # Identity verification chain
    "Jumio": {
        "entity_name": "Jumio Inc.",
        "corporate_family": "Jumio",
        "note": "Biometric/document identity verification. Was TrustE-certified (predecessor to TrustArc) — Jumio/What a TRUSTe badge signifies.pdf confirms the TrustE→TrustArc lineage through the Uber ecosystem.",
        "rejects": set(),  # keep all including TrustE badge doc for analytical value
    },
    "Socure": {
        "entity_name": "Socure Inc.",
        "corporate_family": "Socure",
        "note": "Biometric identity verification — parallel/competing deployment to Jumio within Uber ecosystem",
        "rejects": set(),
    },
    "Veriff": {
        "entity_name": "Veriff Inc.",
        "corporate_family": "Veriff",
        "note": "European identity verification, GDPR-focused. Third identity verification vendor in Uber chain.",
        "rejects": {
            "Veriff Fraud Article.pdf",
            "Veriff product GDPR audit executive summary 2024.pdf",
            "Veriff Security and Compliance.pdf",
            "Veriff Security Whitepaper.pdf",
            "Veriff Trust Center Controls.pdf",
            "Veriff Trust Center Resources.pdf",
            "Veriff Trust Center.pdf",
        },
    },
    # Compliance/audit chain
    "Vanta": {
        "entity_name": "Vanta Inc.",
        "corporate_family": "Vanta",
        "note": "Security compliance automation (SOC2/ISO/FedRAMP). Has full visibility into Uber's data infrastructure.",
        "rejects": {
            "Schellman FedRAMP 20x Assessment Plan & Methodology (Vanta) v1.0.pdf",
            "Vanta - FedRAMP 20x Pilot Final Submission File.pdf",
            "Vanta FedRAMP 20xP1 Authorization Package Overview (Public) .pdf",
            "Vanta FedRAMP 20xP1 Final Authorization Package Overview (Public) .pdf",
            "Vanta - Vanta Web App - ACR - WCAG 2.2 A, WCAG 2.2 AA, EN 301 549, Section 508 - June 2026.pdf",
            "Vanta-Case-Study.pdf",
            "W-9- 2026 updated .pdf",
            "Vanta Code of Conduct.pdf",
            "Secure Implementation Guidelines.pdf",
            "Vanta Continuous Collaboration Report June 2026 (20x Low)_Public.pdf",
        },
    },
    "Drata": {
        "entity_name": "Drata Inc.",
        "corporate_family": "Drata",
        "note": "Compliance automation (SOC2/ISO). Parallel to Vanta in Uber audit chain.",
        "rejects": set(),
        # Google API Services User Data Policy.pdf in this folder → Google LLC
        "reroute": {
            "Google API Services User Data Policy.pdf": {
                "entity_name": "Google LLC",
                "corporate_family": "Alphabet",
                "doc_type": "tos",
            },
        },
    },
    "Sprinto": {
        "entity_name": "Sprinto Inc.",
        "corporate_family": "Sprinto",
        "note": "Compliance automation — third audit vendor in Uber chain alongside Vanta and Drata",
        "rejects": {
            "Sprinto Security starts with us.pdf",
        },
    },
    # Data/payment chain
    "Plaid": {
        "entity_name": "Plaid Inc.",
        "corporate_family": "Plaid",
        "note": "Financial data aggregator — accesses bank accounts for Uber payment processing. Biometric data via Plaid Biometric Policy.",
        "rejects": set(),
    },
    "Dwolla": {
        "entity_name": "Dwolla Inc.",
        "corporate_family": "Dwolla",
        "note": "ACH/bank transfer payment processor",
        "rejects": set(),
    },
    "Modulr": {
        "entity_name": "Modulr FS Limited",
        "corporate_family": "Modulr",
        "note": "UK payment infrastructure — Uber international operations",
        "rejects": set(),
    },
    "Upside": {
        "entity_name": "Upside Commerce Group",
        "corporate_family": "Upside",
        "note": "Cashback/loyalty rewards — purchases behavioral and transaction data",
        "rejects": set(),
    },
    # Tag management / data routing
    "Tealium": {
        "entity_name": "Tealium Inc.",
        "corporate_family": "Tealium",
        "note": "Tag management system — routes ALL Uber user event data to every other vendor simultaneously. Highest-leverage node in the ecosystem.",
        "rejects": set(),
    },
    # Advertising chain
    "Meta": {
        "entity_name": "Meta Platforms",
        "corporate_family": "Meta",
        "note": "Ad targeting — Facebook/Instagram. Merges with existing corpus records.",
        "rejects": set(),
    },
    # TrustArc nested under Facebook — historical TrustE privacy certification of Facebook
    "Facebook/TrustArc": {
        "entity_name": "TrustArc Inc.",
        "corporate_family": "TrustArc",
        "note": "TrustArc (formerly TrustE) deployed as Facebook privacy certifier. TrustE issued the 'TrustE Certified' badge to Facebook before the FTC settlement. Rebranded to TrustArc. Now manages consent infrastructure for both Meta and Uber simultaneously.",
        "rejects": {
            "SOC2 Report Table of Contents_2025.pdf",
            "Sub-processor disclosure.docx.pdf",
        },
    },
    # TrustArc nested under Meta — current consent management deployment
    "Meta/TrustArc": {
        "entity_name": "TrustArc Inc.",
        "corporate_family": "TrustArc",
        "note": "TrustArc as Meta's current consent management platform. Same entity as Facebook/TrustArc — confirms cross-generational continuity from TrustE certification to active consent infrastructure.",
        "rejects": set(),
    },
    "MicrosoftBing": {
        "entity_name": "Microsoft Corporation",
        "corporate_family": "Microsoft",
        "note": "Bing Ads and analytics — advertising vendor in Uber ecosystem",
        "rejects": set(),
    },
    "NextRoll": {
        "entity_name": "NextRoll Inc.",
        "corporate_family": "NextRoll",
        "note": "Programmatic ad retargeting — receives user behavioral data from Tealium",
        "rejects": set(),
    },
    "Pintrest": {
        "entity_name": "Pinterest Inc.",
        "corporate_family": "Pinterest",
        "note": "Ad platform",
        "rejects": set(),
    },
    # Fullstory — session replay
    "Fullstory": {
        "entity_name": "Fullstory Inc.",
        "corporate_family": "Fullstory",
        "note": "Session replay and behavioral analytics — captures and replays every user interaction on Uber app/web. Highest data-extraction depth of all vendors.",
        "rejects": set(),
    },
}

_DOC_TYPE_KEYWORDS: list[tuple[str, str]] = [
    ("arbitrat", "arbitration"),
    ("dispute", "arbitration"),
    ("eula", "eula"),
    ("end user licen", "eula"),
    ("privacy", "privacy_notice"),
    ("cookie", "privacy_notice"),
    ("ccpa", "privacy_notice"),
    ("gdpr", "privacy_notice"),
    ("data polic", "privacy_notice"),
    ("data processing", "privacy_notice"),
    ("sub-processor", "privacy_notice"),
    ("sub processor", "privacy_notice"),
    ("modern slavery", "privacy_notice"),
    ("biometric", "privacy_notice"),
    ("health data", "privacy_notice"),
    ("candidate", "privacy_notice"),
    ("applicant", "privacy_notice"),
    ("recruitment", "privacy_notice"),
    ("terms", "tos"),
    ("conditions", "tos"),
    ("acceptable use", "tos"),
    ("service level", "tos"),
    ("addendum", "tos"),
    ("agreement", "tos"),
    ("partner program", "tos"),
    ("subscription", "tos"),
    ("support policy", "tos"),
    ("services", "tos"),
]


def _infer_doc_type(filename: str) -> str:
    fn = filename.lower()
    for kw, dt in _DOC_TYPE_KEYWORDS:
        if kw in fn:
            return dt
    return "tos"


def _make_entry(
    file_path: Path,
    entity_name: str,
    corporate_family: str,
    doc_type: str,
    version_label: str | None = None,
) -> dict:
    return {
        "file_path": str(file_path.resolve()),
        "entity_name": entity_name,
        "corporate_family": corporate_family,
        "doc_type": doc_type,
        "doc_type_confidence": 0.85,
        "needs_review": False,
        "version_label": version_label,
        "effective_date": None,
        "source_url": None,
    }


def build(dry_run: bool) -> None:
    if not _UBER_ROOT.exists():
        print(f"ERROR: Uber corpus folder not found: {_UBER_ROOT}")
        return

    # ── Root-level routing ──
    by_manifest: dict[str, list[dict]] = {
        "contra_manifest_uber_core.json": [],
        "contra_manifest_portier.json": [],
        "contra_manifest_cmt.json": [],
        "contra_manifest_uber_google.json": [],
        "contra_manifest_uber_vendors.json": [],
    }

    rejected: list[str] = []
    unrouted: list[str] = []
    entity_counts: dict[str, int] = {}

    for pdf in sorted(_UBER_ROOT.glob("*.pdf")):
        routing = _ROOT_ROUTING.get(pdf.name, "UNROUTED")
        if routing == "UNROUTED":
            unrouted.append(pdf.name)
            continue
        if routing is None:
            rejected.append(pdf.name)
            continue

        entry = _make_entry(
            pdf,
            entity_name=routing["entity_name"],
            corporate_family=routing["corporate_family"],
            doc_type=routing["doc_type"],
            version_label=routing.get("version_label"),
        )

        name = routing["entity_name"]
        entity_counts[name] = entity_counts.get(name, 0) + 1

        if name == "Uber Technologies Inc.":
            by_manifest["contra_manifest_uber_core.json"].append(entry)
        elif name == "Portier LLC":
            by_manifest["contra_manifest_portier.json"].append(entry)
        elif name == "Cambridge Mobile Telematics":
            by_manifest["contra_manifest_cmt.json"].append(entry)
        elif name == "Google LLC":
            by_manifest["contra_manifest_uber_google.json"].append(entry)

    # ── Subfolder routing ──
    subfolder_rejects: list[str] = []

    for subfolder_rel, entity_info in _SUBFOLDER_MAP.items():
        subfolder = _UBER_ROOT / subfolder_rel.replace("/", "\\")
        if not subfolder.exists():
            continue

        pdfs = sorted(subfolder.glob("*.pdf"))
        if not pdfs:
            continue

        rejects = entity_info.get("rejects", set())
        reroute = entity_info.get("reroute", {})

        for pdf in pdfs:
            if pdf.name in rejects:
                subfolder_rejects.append(f"{subfolder_rel}/{pdf.name}")
                continue

            # Check for reroute
            if pdf.name in reroute:
                r = reroute[pdf.name]
                entry = _make_entry(
                    pdf,
                    entity_name=r["entity_name"],
                    corporate_family=r["corporate_family"],
                    doc_type=r["doc_type"],
                )
                by_manifest["contra_manifest_uber_google.json"].append(entry)
                entity_counts["Google LLC"] = entity_counts.get("Google LLC", 0) + 1
                continue

            entry = _make_entry(
                pdf,
                entity_name=entity_info["entity_name"],
                corporate_family=entity_info["corporate_family"],
                doc_type=_infer_doc_type(pdf.name),
            )
            by_manifest["contra_manifest_uber_vendors.json"].append(entry)
            name = entity_info["entity_name"]
            entity_counts[name] = entity_counts.get(name, 0) + 1

    # ── Print plan ──
    total_ingest = sum(len(v) for v in by_manifest.values())
    total_reject = len(rejected) + len(subfolder_rejects)

    print("\n== UBER ECOSYSTEM MANIFEST BUILD (NSU) ==\n")

    # Show by manifest
    for manifest, entries in by_manifest.items():
        if entries:
            names = sorted(set(e["entity_name"] for e in entries))
            print(f"  {manifest:<45} {len(entries):>3} docs | {', '.join(names)}")

    print(f"\n  {'─'*75}")
    print(f"  TOTAL to ingest : {total_ingest}")
    print(f"  REJECTED        : {total_reject}")

    print(f"\n  Entity breakdown ({len(entity_counts)} entities):")
    for name, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
        note = ""
        for _, info in _SUBFOLDER_MAP.items():
            if info["entity_name"] == name and info.get("note"):
                note = "  # " + info["note"][:80]
                break
        print(f"    {name:<40} {count:>3} docs{note}")

    print(f"\n  Rejected ({total_reject}):")
    for r in rejected:
        print(f"    ROOT: {r}")
    for r in subfolder_rejects:
        print(f"    SUB:  {r}")

    if unrouted:
        print(f"\n  UNROUTED (add to _ROOT_ROUTING): {len(unrouted)}")
        for u in unrouted:
            print(f"    ? {u}")

    if dry_run:
        print("\n  (dry run — manifests not written)")
        return

    # ── Write manifests ──
    print("\nWriting manifests...")
    written = []
    for manifest_path, entries in by_manifest.items():
        if not entries:
            continue
        out = Path(manifest_path)
        out.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  {out} — {len(entries)} entries")
        written.append(out)

    print("\nIngest order:")
    for out in written:
        print(f"  python scripts/contra_batch_ingest.py --manifest {out} --skip-review")
    print("  python scripts/build_contra_corpus_archive.py")
    print("  python scripts/contra_query.py")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NSU manifest build for full Uber sub-processor + partner ecosystem"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
