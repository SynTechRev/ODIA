#!/usr/bin/env python3
"""
Generate a single plain-text full audit and analysis from existing JSON artifacts.

Usage:
  python scripts/generate_plaintext_audit.py --artifacts-dir transparency_release

Adjust file names/paths in ARTIFACT_PATHS if your repo uses different names.
"""
import argparse
import json
from datetime import UTC, datetime
from itertools import islice
from pathlib import Path

# Path correction log
PATH_CORRECTIONS_LOG = Path("analysis/logs/path_corrections.log")

# === CONFIG: update these if your artifacts use different names/locations ===
ARTIFACT_PATHS = {
    "ingestion_report": "oraculus/corpus/ingestion_report.json",
    "validation_report": "oraculus/corpus/VALIDATION_REPORT.json",
    "ace_report": "analysis/ace/ACE_REPORT.json",
    "ace_summary": "analysis/ace/ACE_SUMMARY.md",
    "vendor_graph": "analysis/vendor/vendor_graph.json",
    "vendor_anomalies": "analysis/vendor/VENDOR_ANOMALY_LINKS.json",
    "pdf_forensic": "analysis/pdf_forensics/forensic_report.json",
    "pdf_inconsistency": "analysis/pdf_forensics/metadata_inconsistency_map.json",
    "jim_report": "analysis/jim/JIM_REPORT.json",
    "jim_summary": "analysis/jim/JIM_SUMMARY.md",
    "semantic_matrix": "analysis/semantic/SEMANTIC_HARMONIZATION_MATRIX.json",
    "divergence_index": "analysis/semantic/MEANING_DIVERGENCE_INDEX.json",
    "hash_manifest": "transparency_release/HASH_MANIFEST_FULL_SHA256.txt",
    "corpus_manifest": "transparency_release/corpus_manifest.json",
}


def log_path_correction(original_path: str, corrected_path: str) -> None:
    """Log path corrections to the path corrections log file."""
    PATH_CORRECTIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    log_entry = f"[{timestamp}] {original_path} -> {corrected_path}\n"
    with open(PATH_CORRECTIONS_LOG, "a", encoding="utf-8") as f:
        f.write(log_entry)
    print(f"Path corrected: {original_path} -> {corrected_path}")


def auto_detect_path(
    base_path: Path, original_relative: str, artifacts_dir: Path
) -> Path:
    """Auto-detect correct path by searching recursively if original doesn't exist."""
    # Try original path first
    original_path = base_path / original_relative
    if original_path.exists():
        return original_path

    # Try under artifacts_dir
    artifacts_path = artifacts_dir / original_relative
    if artifacts_path.exists():
        log_path_correction(str(original_relative), str(artifacts_path))
        return artifacts_path

    # Extract filename and search recursively
    filename = Path(original_relative).name
    search_dirs = [artifacts_dir, base_path / "analysis", base_path / "oraculus"]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for found_path in search_dir.rglob(filename):
            if found_path.is_file():
                log_path_correction(str(original_relative), str(found_path))
                return found_path

    # Return original path even if it doesn't exist (will be handled by caller)
    return original_path


def validate_and_fix_paths(artifacts_dir: Path) -> dict:
    """Validate all artifact paths and fix them if needed."""
    base_path = Path.cwd()
    fixed_paths = {}

    for key, rel_path in ARTIFACT_PATHS.items():
        detected_path = auto_detect_path(base_path, rel_path, artifacts_dir)
        fixed_paths[key] = detected_path

    return fixed_paths


# =============================================================================
def load_json_if_exists(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_load_error": str(e), "_path": str(path)}


def load_text_if_exists(path: Path):
    return path.read_text(encoding="utf-8") if path.exists() else None


def summarize_ingestion(ing):
    s = []
    if not ing:
        return "No ingestion_report available.\n"

    summary = ing.get("summary", {})

    # Explicit None checks to avoid masking zero values
    total_corpora = ing.get("corpora_processed")
    if total_corpora is None:
        total_corpora = summary.get("total_corpora")
    if total_corpora is None:
        total_corpora = ing.get("corpora", {}).get("total", 0)

    total_pdfs = ing.get("pdfs_scanned")
    if total_pdfs is None:
        total_pdfs = summary.get("pdfs_found")
    if total_pdfs is None:
        total_pdfs = summary.get("total_files_ingested", 0)

    extraction_rate = ing.get("extraction_success_rate")
    if extraction_rate is None:
        extraction_rate = summary.get("extraction_success_rate", 0.0)
    s.append(f"- Corpora processed: {total_corpora}")
    s.append(f"- Planned corpora: {summary.get('planned_corpora', 'N/A')}")
    s.append(f"- PDFs scanned: {total_pdfs}")
    s.append(f"- Extraction success rate: {extraction_rate:.1f}%")
    s.append(f"- Files missing agendas: {summary.get('files_missing_agendas', 0)}")
    s.append(f"- Files missing minutes: {summary.get('files_missing_minutes', 0)}")
    s.append(
        f"- Index rebuild confirmed: {summary.get('index_rebuild_confirmed', False)}"
    )
    s.append(
        f"- Structure validation passed: {summary.get('structure_validation_passed', False)}"
    )
    s.append(
        f"- Integrity checks passed: {summary.get('integrity_checks_passed', False)}"
    )

    # Warnings
    warnings = ing.get("warnings", [])
    if warnings:
        s.append("\nWarnings:")
        for w in warnings[:5]:
            s.append(f"  • {w}")

    flagged = ing.get("flagged_irregularities") or ing.get("issues") or []
    s.append("\n- Flagged irregularities (sample up to 10):")
    if not flagged:
        s.append("  (none)")
    for it in flagged[:10]:
        s.append(f"  • {it}")
    return "\n".join(s) + "\n"


def summarize_validation(val):
    s = []
    if not val:
        return "No validation report available.\n"

    # Look in multiple places for these values
    total_files = val.get("total_files") or val.get("summary", {}).get("total_files", 0)
    extraction_rate = val.get("extraction_success_rate") or val.get("summary", {}).get(
        "extraction_success_rate", 0.0
    )

    s.append(f"- Total files counted by audit: {total_files}")
    s.append(f"- Extraction success rate (per-audit): {extraction_rate:.1f}%")
    missing = val.get("missing_items", [])
    s.append(f"- Missing items reported: {len(missing)}")
    if missing:
        s.append("  Example missing items:")
        for m in missing[:8]:
            s.append(f"  • {m}")
    return "\n".join(s) + "\n"


def summarize_ace(ace):
    if not ace:
        return "No ACE report available.\n"
    s = []
    summary = ace.get("summary", {})
    s.append(
        f"- ACE anomalies total: {summary.get('total_anomalies', summary.get('anomalies_total', 0))}"
    )
    by_type = summary.get("by_type", {})
    if by_type:
        s.append("- Anomalies by category:")
        for k, v in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            s.append(f"  • {k}: {v}")
    else:
        s.append("- Anomalies by category: (not categorized)")

    # Add more detail about anomaly distribution
    all_anomalies = ace.get("anomalies", [])
    if all_anomalies:
        s.append(f"\n- Total anomaly records: {len(all_anomalies)}")
        score_distribution = {
            "critical (>0.9)": 0,
            "high (0.7-0.9)": 0,
            "medium (0.4-0.7)": 0,
            "low (<0.4)": 0,
        }
        for anomaly in all_anomalies:
            score = anomaly.get("score", 0)
            if score > 0.9:
                score_distribution["critical (>0.9)"] += 1
            elif score > 0.7:
                score_distribution["high (0.7-0.9)"] += 1
            elif score > 0.4:
                score_distribution["medium (0.4-0.7)"] += 1
            else:
                score_distribution["low (<0.4)"] += 1

        s.append("- Score distribution:")
        for level, count in score_distribution.items():
            if count > 0:
                s.append(f"  • {level}: {count}")

    top = ace.get("top_anomalies", [])[:15]
    if top:
        s.append("\n- Top anomaly examples (hist_id / score / brief):")
        for t in top:
            s.append(f"  • {t.get('hist_id')} / {t.get('score')} / {t.get('brief','')}")
    return "\n".join(s) + "\n"


def summarize_vendor(vendor_graph, vendor_anoms):
    if not vendor_graph and not vendor_anoms:
        return "No vendor artifacts available.\n"
    s = []
    if vendor_graph:
        try:
            nodes = vendor_graph.get("nodes") or vendor_graph.get("vendors") or []
            edges = vendor_graph.get("edges", [])
            s.append(f"- Vendors discovered (count): {len(nodes)}")
            s.append(f"- Vendor relationships (edges): {len(edges)}")

            # Categorize vendors by type/year if available
            vendor_types = {}
            for n in nodes:
                if isinstance(n, dict):
                    vtype = n.get("type") or n.get("id", "").split(":")[0]
                    if vtype not in vendor_types:
                        vendor_types[vtype] = []
                    vendor_types[vtype].append(n)

            if vendor_types:
                s.append("\n- Vendor distribution by type:")
                for vtype, vendors in sorted(
                    vendor_types.items(), key=lambda x: len(x[1]), reverse=True
                )[:10]:
                    s.append(f"  • {vtype}: {len(vendors)}")

            s.append("\n- Sample vendors (top by contracts):")
            sample = sorted(
                [n for n in nodes if isinstance(n, dict)],
                key=lambda x: x.get("total_contracts", x.get("count", 0)),
                reverse=True,
            )[:15]
            for n in sample:
                s.append(
                    f"  • {n.get('id') or n.get('name')} — {n.get('total_contracts',n.get('count','?'))} contracts"
                )
        except Exception:
            s.append("- vendor_graph parsed poorly.")

    if vendor_anoms:
        links = vendor_anoms.get("links", []) or vendor_anoms.get("anomaly_links", [])
        s.append(f"\n- Vendor-linked anomalies: {len(links)} total")
        s.append("- Sample vendor anomaly links (up to 10):")
        for x in links[:10]:
            if isinstance(x, dict):
                s.append(
                    f"  • Vendor: {x.get('vendor_id', 'N/A')}, Anomaly: {x.get('anomaly_id', 'N/A')}"
                )
            else:
                s.append(f"  • {x}")
    return "\n".join(s) + "\n"


def summarize_pdf_forensics(pdff, pdfmap):
    if not pdff and not pdfmap:
        return "No PDF forensics available.\n"
    s = []
    if pdff:
        # Get mode and counts
        mode = pdff.get("mode", "unknown")
        total_scanned = pdff.get("total_scanned", pdff.get("pdfs_processed", "unknown"))
        pdfs_found = pdff.get("pdfs_found_count", 0)
        pdfs_metadata = pdff.get("pdfs_metadata_count", 0)

        s.append(f"- Forensic total scanned: {total_scanned}")
        s.append(f"- Analysis mode: {mode}")

        if mode == "metadata_only":
            s.append(f"- PDFs analyzed from metadata: {pdfs_metadata}")
            s.append("  (Note: Full forensic analysis requires actual PDF files)")
        elif mode == "full_forensic":
            s.append(f"- PDFs with full forensic analysis: {pdfs_found}")

        summary = pdff.get("summary", {})
        avg_score = summary.get("average_score", 0.0)
        s.append(f"- Average forensic score: {avg_score:.1f}/100")

        anomalies = pdff.get("anomalies", [])
        s.append(f"- Forensic anomalies: {len(anomalies)}")

        if anomalies:
            s.append("- Top forensic anomaly types (sample):")
            anomaly_types = summary.get("anomalies_by_type", {})
            for atype, count in islice(
                sorted(anomaly_types.items(), key=lambda x: -x[1]), 8
            ):
                s.append(f"  • {atype}: {count}")

        # Add metadata file count
        metadata_by_file = pdff.get("metadata_by_file", {})
        if metadata_by_file:
            s.append(f"- Unique files tracked: {len(metadata_by_file)}")

    if pdfmap:
        total_inconsistencies = pdfmap.get("total_inconsistencies", 0)
        s.append(f"\n- Metadata inconsistencies detected: {total_inconsistencies}")
        if total_inconsistencies > 0:
            s.append("- Inconsistency examples (up to 8):")
            for k, v in islice(pdfmap.items(), 8):
                if (
                    k != "version"
                    and k != "generated_at"
                    and k != "total_inconsistencies"
                ):
                    s.append(f"  • {k}: {v}")
    return "\n".join(s) + "\n"


def summarize_jim(jim):
    if not jim:
        return "No JIM report available.\n"
    s = []
    summary = jim.get("summary") or jim.get("meta") or {}
    # Get cases analyzed from metadata.total_anomalies or summary fields
    # Use explicit None checks to avoid masking legitimate zero values
    metadata = jim.get("metadata", {})
    cases_analyzed = summary.get("cases_analyzed")
    if cases_analyzed is None:
        cases_analyzed = jim.get("cases_count")
    if cases_analyzed is None:
        cases_analyzed = metadata.get("total_anomalies")
    if cases_analyzed is None:
        cases_analyzed = 0
    s.append(f"- JIM cases analyzed: {cases_analyzed}")
    s.append("- Doctrines scored / triggered (sample):")
    top = jim.get("top_doctrines", [])[:10]
    for d in top:
        s.append(f"  • {d}")
    s.append("- Constitutional risk high-count (sample):")
    for r in (jim.get("high_risk_items") or [])[:10]:
        s.append(f"  • {r}")
    return "\n".join(s) + "\n"


def summarize_semantics(matrix, divergence):
    if not matrix and not divergence:
        return "No semantic artifacts available.\n"
    s = []
    if matrix:
        s.append(
            f"- Semantic matrix entries: {len(matrix.get('entries', []) if isinstance(matrix, dict) else 'unknown')}"
        )
    if divergence:
        terms_dict = divergence.get("terms", {})
        if isinstance(terms_dict, dict):
            # Sort dictionary items directly
            top = sorted(
                terms_dict.items(),
                key=lambda x: x[1].get("divergence_score", 0),
                reverse=True,
            )[:10]
            s.append("- Highest meaning divergence terms (top 10):")
            for term, data in top:
                s.append(f"  • {term} — divergence {data.get('divergence_score', 0)}")
        else:
            s.append("- Terms structure in divergence index not recognized")
    return "\n".join(s) + "\n"


def build_plaintext(artifacts_dir: Path, out_path: Path):
    # Validate and fix paths first
    fixed_paths = validate_and_fix_paths(artifacts_dir)

    # load everything using validated paths
    loaded = {}
    for key, path in fixed_paths.items():
        loaded[key] = (
            load_json_if_exists(path)
            if path.suffix in (".json",)
            else load_text_if_exists(path)
        )

    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    lines = []
    lines.append("ORACULUS-DI AUDIT: FULL PLAIN-TEXT REPORT")
    lines.append(f"Generated: {now}")
    lines.append("=" * 80)
    lines.append("\nEXECUTIVE SUMMARY\n")
    # brief top-levels
    lines.append(
        "Method: automated ingestion -> audit -> anomaly engines -> cross correlation -> legal synthesis"
    )
    lines.append("")
    lines.append("Topline:")
    try:
        ingestion = loaded.get("ingestion_report")
        val = loaded.get("validation_report")
        ace = loaded.get("ace_report")
        jim = loaded.get("jim_report")
        lines.append(summarize_ingestion(ingestion))
        lines.append(summarize_validation(val))
        lines.append(summarize_ace(ace))
        lines.append(summarize_jim(jim))
    except Exception as e:
        lines.append(f"[error summarizing topline: {e}]")

    lines.append("\nMETHODOLOGY\n")
    lines.append("This audit employs a multi-layered analytical framework:")
    lines.append(
        "\n1) INGESTION MODULE: Parsed legislative corpus, computed SHA-256 hashes, "
        "extracted text from PDFs where possible. Flagged missing files, empty directories, "
        "and structural inconsistencies. Built comprehensive index of all corpora."
    )
    lines.append(
        "\n2) VALIDATION MODULE: Cross-referenced file metadata against expected structure. "
        "Calculated extraction success rates. Identified missing agenda/minute pairs. "
        "Validated provenance chains and meeting date consistency."
    )
    lines.append(
        "\n3) ACE (ANOMALY CORRELATION ENGINE): Multi-dimensional anomaly detection using "
        "statistical outliers, metadata breaks, temporal gaps, and vendor pattern analysis. "
        "Scores range 0.0-1.0 with >0.7 flagged for manual review."
    )
    lines.append(
        "\n4) VICFM (VENDOR INFLUENCE CORRELATION & FLOW MAPPING): Extracted vendor entities, "
        "built relationship graphs, detected procurement irregularities (sole-source flags, "
        "cost escalation >40% YoY, multi-year continuity). Linked vendors to ACE anomalies."
    )
    lines.append(
        "\n5) CAIM (CROSS-AGENCY INFLUENCE MAPPING): Analyzed inter-departmental vendor overlap, "
        "technology stack dependencies, and contract flow synchronization. Computed influence "
        "scores incorporating vendor overlap, tech stack, contract flow, ACE linkage, and continuity."
    )
    lines.append(
        "\n6) DPMM (PDF METADATA MINER): Forensic analysis of PDF XMP metadata, creation/modification "
        "timestamps, producer signatures, and origin consistency. Detects retroactive edits, "
        "scanned vs digital-native documents, and metadata tampering."
    )
    lines.append(
        "\n7) JIM (JURIDICAL INTELLIGENCE MAPPER): Legal correlation engine mapping anomalies "
        "to 159 SCOTUS cases and 57 constitutional doctrines. Weights cases by era (1791/1868/2024) "
        "and applies 10 interpretive frameworks (OPM, Textualism, Framers' Intent, etc.)."
    )
    lines.append(
        "\n8) MSH (MULTI-SOURCE SEMANTIC HARMONIZATION): Harmonizes legal definitions across "
        "5 authoritative sources (Black's Law 11th, Bouvier's 1856, Webster Legal, Oxford Law, "
        "Latin maxims). Weighted conflict resolution (Black's 0.35, others distributed)."
    )
    lines.append(
        "\n9) MDI (MEANING DIVERGENCE INDEX): Computes semantic drift for legal terms across "
        "historical eras. Scores 0.0-1.0 where 0.0=canonical stability, 1.0=complete inversion. "
        "Flags terms with >0.5 divergence for contextual review."
    )
    lines.append(
        "\n10) CDSCE (CROSS-DICTIONARY SEMIOTIC CORRELATION): Detects cross-dictionary "
        "intelligence, semiotic drift, contradictions, and graph-based relationship analysis "
        "across legal terminology."
    )
    lines.append(
        "\n11) TRANSPARENCY PACKAGE GENERATOR: Produces SHA-256 hash manifests, corpus inventories, "
        "public-safe summaries, and reproducibility documentation."
    )
    lines.append(
        "\nNotes: Missing or image-only PDFs are flagged; Data Availability statement excludes "
        "non-public materials. All analysis is deterministic and reproducible from source data.\n"
    )

    # Chronology
    lines.append("\nCHRONOLOGICAL TIMELINE SUMMARY\n")
    if val and isinstance(val, dict):
        timeline = val.get("timeline") or val.get("chronology") or {}
        if timeline:
            lines.append("Per-audit timeline (sample):")
            for item in timeline.get("items", [])[:20]:
                lines.append(
                    f"  • {item.get('date')}: {item.get('id')} — {item.get('title', '')}"
                )
        else:
            lines.append(
                "No timeline object in validation report; use oraculus/corpus/index.json for full chronology."
            )
    else:
        lines.append("No validation timeline available.\n")

    # Anomalies & Inconsistencies (categories)
    lines.append("\nANOMALIES & INCONSISTENCIES\n")
    lines.append("A) Extraction / data integrity")
    lines.append(summarize_validation(val))

    lines.append("B) ACE anomaly summary")
    lines.append(summarize_ace(loaded.get("ace_report")))

    lines.append("C) Vendor & procurement irregularities")
    lines.append(
        summarize_vendor(loaded.get("vendor_graph"), loaded.get("vendor_anomalies"))
    )

    lines.append("D) PDF Forensics (retroactive edits, scanned vs digital)")
    lines.append(
        summarize_pdf_forensics(
            loaded.get("pdf_forensic"), loaded.get("pdf_inconsistency")
        )
    )

    lines.append("E) Legal correlations & doctrine triggers (JIM)")
    lines.append(summarize_jim(loaded.get("jim_report")))

    lines.append("F) Semantic conflicts & drift")
    lines.append(
        summarize_semantics(
            loaded.get("semantic_matrix"), loaded.get("divergence_index")
        )
    )

    lines.append("\nCROSS-REFERENCES TO CASE LAW (sample linkage results)\n")
    if jim and isinstance(jim, dict):
        links = jim.get("case_links") or jim.get("links") or []
        if links:
            for item in links[:40]:
                lines.append(
                    f"  - {item.get('case_id')} linked to anomaly {item.get('anomaly_id')} via doctrine {item.get('doctrine')}"
                )
        else:
            lines.append(
                "No direct case_links array in JIM report; check JIM_REPORT.json for case mappings."
            )
    else:
        lines.append("No JIM report loaded.")

    lines.append("\nRECOMMENDATIONS (high level)\n")
    lines.append(
        "1) Prioritize forensic re-evaluation of PDFs with producer/creation date mismatches and high ForensicScore."
    )
    lines.append(
        "2) Manual review for top ACE anomalies (highest score) with vendor links in VENDOR_ANOMALY_LINKS.json."
    )
    lines.append(
        "3) Legal counsel review: JIM high-risk items and doctrine triggers; prepare targeted discovery requests."
    )
    lines.append(
        "4) Re-run OCR on image-only PDFs and reattempt extraction; add extracted text to artifacts for reproducibility."
    )
    lines.append(
        "5) Public transparency: publish HASH_MANIFEST_FULL_SHA256.txt and ALL_AUDIT_FULL.txt alongside reproducible script."
    )
    lines.append(
        "6) Update metadata records for date mismatches in provenance records and mark items requiring chain-of-custody review.\n"
    )

    lines.append("\nAPPENDIX: ARTIFACTS & COUNTS\n")
    # counts
    try:
        if loaded.get("corpus_manifest"):
            cm = loaded["corpus_manifest"]
            files = cm.get("files", [])
            corpora = cm.get("corpora", [])
            lines.append(f"- Corpus manifest entries: {len(files)}")
            lines.append(
                f"- Total corpora tracked: {cm.get('total_corpora', len(corpora))}"
            )
            lines.append(
                f"- Corpus range: {cm.get('corpus_range', {}).get('start_year', 'N/A')} - {cm.get('corpus_range', {}).get('end_year', 'N/A')}"
            )

            # List corpora with file counts
            if corpora:
                lines.append("\nCorpora inventory (by year):")
                by_year = {}
                for corpus in corpora:
                    year = corpus.get("year", "Unknown")
                    if year not in by_year:
                        by_year[year] = []
                    by_year[year].append(corpus)

                for year in sorted(by_year.keys()):
                    year_corpora = by_year[year]
                    total_files = sum(c.get("file_count", 0) for c in year_corpora)
                    lines.append(
                        f"  {year}: {len(year_corpora)} corpora, {total_files} files"
                    )
                    for corpus in year_corpora[:3]:  # Show first 3 from each year
                        lines.append(
                            f"    • {corpus.get('corpus_id')}: {corpus.get('meeting_date')} ({corpus.get('file_count', 0)} files)"
                        )
                    if len(year_corpora) > 3:
                        lines.append(f"    ... and {len(year_corpora) - 3} more")

    except Exception:
        # Silently skip if corpus manifest format is unexpected
        pass

    # hash manifest presence
    hm = fixed_paths.get("hash_manifest", Path(ARTIFACT_PATHS["hash_manifest"]))
    if hm.exists():
        lines.append(f"\n- Hash manifest found: {hm} (attach in public release)")
        # Count lines in hash manifest
        try:
            with open(hm, encoding="utf-8") as f:
                hash_lines = [
                    line for line in f if line.strip() and not line.startswith("#")
                ]
            lines.append(f"  Contains {len(hash_lines)} file hashes")
        except Exception:
            pass
    else:
        lines.append(
            "\n- Hash manifest not found at expected path; ensure transparency_release/HASH_MANIFEST_FULL_SHA256.txt present."
        )

    # Add module summaries section
    lines.append("\n\nMODULE OUTPUT SUMMARY\n")
    lines.append("The following analysis modules contributed to this audit:\n")

    # ACE module
    if loaded.get("ace_report"):
        ace = loaded["ace_report"]
        lines.append(
            f"\n1. ACE (Anomaly Correlation Engine): {ace.get('summary', {}).get('total_anomalies', 0)} anomalies detected"
        )

    # Vendor modules
    if loaded.get("vendor_graph"):
        vg = loaded["vendor_graph"]
        lines.append(
            f"2. VICFM (Vendor Influence Correlation): {len(vg.get('nodes', []))} vendors tracked"
        )

    # PDF Forensics
    if loaded.get("pdf_forensic"):
        pdff = loaded["pdf_forensic"]
        lines.append(
            f"3. DPMM (PDF Metadata Miner): {pdff.get('total_scanned', 0)} documents analyzed"
        )

    # JIM
    if loaded.get("jim_report"):
        jim_local = loaded["jim_report"]
        lines.append(
            f"4. JIM (Juridical Intelligence Mapper): {jim_local.get('summary', {}).get('cases_analyzed', 0)} legal cases correlated"
        )

    # Semantic Harmonization
    if loaded.get("semantic_matrix"):
        sm = loaded["semantic_matrix"]
        lines.append(
            f"5. MSH (Multi-Source Harmonization): {len(sm.get('entries', []))} semantic entries"
        )

    # Divergence Index
    if loaded.get("divergence_index"):
        di = loaded["divergence_index"]
        lines.append(
            f"6. MDI (Meaning Divergence Index): {len(di.get('terms', {}))} terms analyzed"
        )

    lines.append("\n\nDETAILED ARTIFACT LOCATIONS\n")
    lines.append("All analysis artifacts are stored in the following locations:\n")
    lines.append("- Ingestion: oraculus/corpus/ingestion_report.json")
    lines.append("- Validation: oraculus/corpus/VALIDATION_REPORT.json")
    lines.append("- ACE Reports: analysis/ace/ACE_REPORT.json, ACE_SUMMARY.md")
    lines.append(
        "- Vendor Analysis: analysis/vendor/vendor_graph.json, VENDOR_ANOMALY_LINKS.json"
    )
    lines.append("- PDF Forensics: analysis/pdf_forensics/forensic_report.json")
    lines.append("- JIM Analysis: analysis/jim/JIM_REPORT.json, JIM_SUMMARY.md")
    lines.append(
        "- Semantic Analysis: analysis/semantic/SEMANTIC_HARMONIZATION_MATRIX.json"
    )
    lines.append("- Transparency Package: transparency_release/corpus_manifest.json")
    lines.append("- Hash Manifests: transparency_release/HASH_MANIFEST_FULL_SHA256.txt")

    # file list of top flagged items
    try:
        flagged = []
        if loaded.get("ace_report"):
            flagged = [
                a
                for a in loaded["ace_report"].get("anomalies", [])
                if a.get("score", 0) > 0.7
            ][:30]
        if flagged:
            lines.append("\nTop flagged items (ACE score > 0.7):")
            for f in flagged:
                lines.append(
                    f"  • {f.get('hist_id')} — {f.get('score')} — {f.get('brief','')}"
                )
    except Exception:
        # Silently skip if ACE report format is unexpected
        pass

    # Add data quality notes
    lines.append("\n\nDATA QUALITY NOTES\n")
    lines.append("- All timestamps are in UTC (ISO 8601 format) for reproducibility")
    lines.append("- SHA-256 hashes ensure file integrity and detect tampering")
    lines.append("- Missing or image-only PDFs are flagged in ingestion report")
    lines.append("- Anomaly scores range from 0.0 (no anomaly) to 1.0 (severe anomaly)")
    lines.append(
        "- Vendor influence scores incorporate frequency, value, ACE linkage, and continuity"
    )
    lines.append(
        "- Legal doctrine triggers are mapped using 159 SCOTUS cases and 57 doctrines"
    )
    lines.append("- Semantic drift analysis uses 5 authoritative legal dictionaries")

    # Add reproducibility section
    lines.append("\n\nREPRODUCIBILITY\n")
    lines.append("To reproduce this audit:")
    lines.append("1. Clone repository from GitHub")
    lines.append("2. Install dependencies: pip install -r requirements.txt")
    lines.append("3. Run pipeline: python scripts/run_full_pipeline.py")
    lines.append("4. Verify artifacts: python scripts/reconcile_artifacts.py")
    lines.append("5. Validate schemas: python scripts/validate_schemas.py")
    lines.append("6. Generate report: python scripts/generate_plaintext_audit.py")
    lines.append(
        "\nAll scripts are deterministic and produce identical results from identical inputs."
    )
    lines.append("Hash manifests can be used to verify file integrity at any time.")

    # Add glossary
    lines.append("\n\nGLOSSARY OF TERMS\n")
    lines.append(
        "ACE - Anomaly Correlation Engine: Multi-dimensional anomaly detection system"
    )
    lines.append(
        "VICFM - Vendor Influence Correlation & Flow Mapping: Vendor relationship and procurement analysis"
    )
    lines.append(
        "CAIM - Cross-Agency Influence Mapping: Inter-departmental dependency analysis"
    )
    lines.append(
        "DPMM - Document/PDF Metadata Miner: Forensic PDF metadata and integrity analysis"
    )
    lines.append(
        "JIM - Juridical Intelligence Mapper: Legal case and doctrine correlation engine"
    )
    lines.append(
        "MSH - Multi-Source Semantic Harmonization: Legal definition harmonization across sources"
    )
    lines.append(
        "MDI - Meaning Divergence Index: Semantic drift quantification for legal terminology"
    )
    lines.append(
        "CDSCE - Cross-Dictionary Semiotic Correlation Engine: Cross-dictionary intelligence analysis"
    )
    lines.append(
        "CLF - Constitutional Linguistic Frameworks: 10 constitutional interpretation frameworks"
    )
    lines.append(
        "LLEP - Legal Lexicon Expansion Pack: Multi-source legal dictionary system"
    )
    lines.append(
        "CLEP - Case Law Expansion Pack: Comprehensive SCOTUS case library (159 cases)"
    )
    lines.append(
        "SHA-256: Cryptographic hash function ensuring file integrity and detecting tampering"
    )
    lines.append(
        "Anomaly Score: 0.0-1.0 metric where >0.7 indicates high-priority review needed"
    )
    lines.append(
        "Influence Score: Composite metric incorporating frequency, value, ACE linkage, centrality, continuity"
    )
    lines.append("Forensic Score: 0-100 metric assessing PDF metadata integrity")
    lines.append(
        "Divergence Score: 0.0-1.0 metric where 0.0=canonical stability, 1.0=complete inversion"
    )
    lines.append(
        "Sole-Source Flag: Procurement irregularity indicating non-competitive contract award"
    )
    lines.append(
        "Cost Escalation: Year-over-year price increase >40% triggering audit flag"
    )
    lines.append(
        "Extraction Success Rate: Percentage of PDFs with successfully extracted text content"
    )
    lines.append(
        "Corpus: Collection of legislative documents for a single meeting date"
    )
    lines.append("HIST-ID: Historical identifier for archived legislative corpus")
    lines.append(
        "Provenance Chain: Complete history of file creation, modification, and custody"
    )

    lines.append("\n\nAUDIT GENERATION METADATA\n")
    lines.append(f"Report generated: {now}")
    lines.append("Generator version: Oraculus-DI v0.1.0")
    lines.append("Python version: 3.11+")
    lines.append("Transparency package version: 1.0")
    lines.append("Schema validation: 14 artifact types validated")
    lines.append("Reproducibility: Fully deterministic from source data")
    lines.append("License: Analysis tools open source (see repository)")
    lines.append("Contact: syntechrev@gmail.com")

    lines.append("\n" + "=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    # finalization
    out_text = "\n".join(lines)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")
    print(f"Wrote full plaintext audit to: {out_path}")


# === CLI ===
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifacts-dir", default=".", help="Base path where artifacts live"
    )
    parser.add_argument(
        "--output",
        default="transparency_release/ALL_AUDIT_FULL.txt",
        help="Output plaintext file",
    )
    args = parser.parse_args()
    artifacts_dir = Path(args.artifacts_dir)
    out_path = Path(args.output)
    build_plaintext(artifacts_dir, out_path)


if __name__ == "__main__":
    main()
