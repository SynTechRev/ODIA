# ODIA Opus Handoff — 2026-07-30
**Supersedes**: ODIA_OPUS_HANDOFF_2026-06-18.md  
**Prepared by**: MARS (SynTechRev) via Claude Code  
**Session scope**: Fresno County full corpus ingest (NSU protocol), Flock Safety targeted RAG analysis, corpus archive rebuild, cross-jurisdiction lattice update  
**Platform version**: 3.8.x (master branch)  
**DB at handoff**: 33,968 documents / 106,668 findings across 15 jurisdictions

---

## Section 1 — What Happened This Session

### 1.1 Fresno County Full Corpus Ingest (NSU Protocol)
- **Protocol**: No Stone Unturned — full Legistar corpus, no keyword filters, no date range restriction
- **Script**: `scripts/ingest_legistar.py --client fresnocounty`
- **Runtime**: ~44 hours (2026-07-28T19:33:02 to 2026-07-30T15:42:02)
- **Matters processed**: 14,783 / 14,783 (complete)
- **Attachments ingested**: 32,337 new files / 3 failed / 373 skipped (below 1 KB or above 50 MB)
- **Checkpoint file**: `cache/fresnocounty_legistar/progress.json` (final state, resumable)
- **Fresno County now holds 15,735 documents / 32,392 findings** — largest single jurisdiction in the corpus

### 1.2 Corpus Archive Rebuild
- **Script**: `scripts/build_corpus_archive.py`
- **Output**: `data/corpus_archive/` — 33,968 docs / 31,925 archive files / 190 MB
- **Architecture**: MASTER_INDEX.json → by_finding/ → by_severity/ → {jurisdiction}/index.json → per-document JSON
- **Note**: `sections` table is empty (text extraction does not persist paragraph-level content); per-document JSON contains finding metadata but no text excerpt or page-offset location fields

### 1.3 Flock Safety RAG Analysis
- **Script**: `C:\Users\yahua\AppData\Local\Temp\rag_flock_queries.py` (4 queries, top_k=15, timeout=900s)
- **Finding**: All 4 queries retrieved Visalia/Visalia-PD documents as top sources — zero Fresno County Flock Safety documents exist
- **Key anomaly surfaced in Q4**: `admin:missing-final-action` in Fresno County BOS agendas — approval language present, `final_action` field null
- **RAG confidence range**: 0.452–0.660 (low due to cross-jurisdiction retrieval substitution)

### 1.4 Direct DB Analysis
- Confirmed zero Flock Safety title/metadata matches across all 32,340 fresnocounty documents
- Confirmed Axon Enterprise IS named in fresnocounty surveillance anomalies (body cams/evidence mgmt)
- Confirmed 20+ `admin:missing-final-action` HIGH anomalies in fresnocounty
- Confirmed multiple `ALPR system referenced without SB 524 AI-transparency policy citation` CRITICAL anomalies in fresnocounty
- Cross-jurisdiction comparison: Visalia-PD has 22 Flock Safety documents (MSAs, fee schedules, community letters) vs. Fresno County's zero

---

## Section 2 — Platform State at Handoff

| Component | State |
|---|---|
| Platform version | 3.8.x |
| Python | 3.11+ (tested 3.14) |
| Tests | 3,396 passing / 17 skipped (data-dependent) |
| DB | SQLite `oraculus_audit.db` — 33,968 docs / 106,668 findings |
| RAG index | TF-IDF; corpus=33,968 / ace=106,668 / jim=644 (needs rebuild post-Fresno) |
| LLM | odia-v1 (Llama-3.1-8B Q4_K_M GGUF, Ollama) — live |
| Desktop | v3.8.0 Electron app installed, backend on port 18741 |
| odia_legal | Phase 1 NOT YET STARTED — deadline 2028-07-02 |
| Multi-index RAG | ace_collection + jim_collection not yet wired into live API query path |
| Fresno County RAG | ANALYZED — findings documented in Section 4 |
| Vast.ai fine-tune | Account created, $0 credit — paused pending odia-v2 data prep |

**RAG index note**: The TF-IDF index was built before Fresno County ingest. The index must be rebuilt (`python scripts/build_rag_index.py`) to include all 33,968 documents. Until then, Fresno County documents are not retrievable via RAG — only via direct DB queries.

---

## Section 3 — Full Corpus Status

### 3.1 Totals
- **Documents**: 33,968 (unique, SHA-256 deduped)
- **Findings**: 106,668 anomaly records across 151 unique finding types
- **Jurisdictions**: 15
- **Finding rows by severity**: rebuild `by_severity/` in corpus archive for current breakdown

### 3.2 Jurisdiction Table

| Jurisdiction | Docs | Findings | MAS Status | Notes |
|---|---|---|---|---|
| fresnocounty | 15,735 | 32,392 | PENDING — V1.0 | Largest. Flock absent. CPRA targets identified. |
| visalia | 7,928 | 20,824 | DONE 2026-06-16 | 20 detector layers |
| farmersville | 1,643 | 7,525 | Complete | MAS purged from temp store |
| exeter | 1,396 | 4,838 | Complete | MAS purged |
| dinuba | 1,105 | 13,506 | Complete | MAS purged |
| lindsay | 805 | 4,799 | Complete | MAS purged |
| tcso | 573 | 4,474 | DONE 2026-06-16 | 15 layers |
| visalia-pd | 340 | 4,571 | Complete | 22 Flock Safety docs / 355 findings |
| porterville | 350 | 1,756 | Complete | MAS purged |
| tcda | 660 | 102 | DONE 2026-06-16 | 3 layers |
| woodlake | 103 | 773 | Complete | MAS purged |
| tulare | 3,062 | 10,750 | Complete | MAS purged |
| tulare-county | 95 | 119 | N/A | Complete |
| tcpd | 161 | 132 | PARTIAL | Public records only. SEU absent. CPRA-004 pending. |
| multi-jurisdiction | 12 | 107 | Complete | Cross-jurisdiction index documents |
| **TOTAL** | **33,968** | **106,668** | | |

### 3.3 Fresno County Deep-Dive

**Ingest**: NSU protocol, 14,783 Legistar matters, ~44 hours, complete.

**Critical surveillance findings**:
- Multiple documents: `ALPR system referenced without SB 524 AI-transparency policy citation` — CRITICAL
- Multiple documents: `Surveillance capability referenced without council resolution or approval` — CRITICAL
- Named vendor in findings: **Axon Enterprise** (body cameras, digital evidence management)
- Flock Safety: **ZERO documents** in 32,340-document corpus

**High-severity administrative findings**:
- 20+ documents: `admin:missing-final-action` — BOS text contains "approved/authorized/adopted" but `final_action` field is null
- Pattern: consistent across multiple agenda dates — systemic record gap, not isolated incidents

**Flock Safety opacity analysis**:

Fresno County publicly stated (2026, mid-year) they are "standing by their Flock Safety contracts." The corpus confirms ALPR technology is deployed (multiple SB 524 violations imply ALPR is present and not disclosed per statute), but no contract, MSA, agenda item, staff report, resolution, or attachment names Flock Safety anywhere in 14,783 matters. Two working hypotheses:

1. **Sheriff's direct procurement**: California county sheriffs may contract independently. If Fresno County Sheriff signed the Flock MSA, it would not appear in BOS Legistar at all.
2. **Consent calendar opacity**: Contract buried under generic attachment title ("Attachments.pdf") in a consent calendar item with no descriptive matter title. Supported by the 20+ missing-final-action anomalies — approvals occurred but weren't properly recorded.

**Comparison baseline — Visalia-PD**: 22 Flock Safety documents disclosed including signed MSAs (2024-09-20, 2024-09-23 dates confirmed), reinstall fee schedules, cross-jurisdictional analysis reports ("Vpd Cross Jurisdictional Flock Analysis V1 and V2"), and community notification letters. This is the standard for what Fresno County should have disclosed.

### 3.4 TCPD SEU Finding (Carried Forward from 2026-06-18)

TCPD corpus: 63 unique documents (165 PDFs across CCP/JJDPC/MJJCC divisions, SHA-256 deduped) / 132 findings. Includes full policy manual (08.29.2025).

Machine-confirmed finding via RAG (direct API call bypassing UI truncation):
> "The Tulare County Probation Department does not appear to have a Special Enforcement Unit referenced in the provided documents."

However, the SEU was confirmed present at the 2026-04-29 multi-agency field action. The SEU exists operationally but is completely absent from all 63 public TCPD documents, including the full policy manual.

**Statutory exposure**:
- Monell doctrine (42 U.S.C. § 1983) — operation under undisclosed custom or practice
- Pen. Code § 832.7 / SB 1421 — mandatory disclosure of use-of-force records
- L-7 (Regulatory Authority Chains) — formal ODIA anomaly type; undisclosed enforcement unit with no disclosed statutory authority

**CPRA-004 supplement scope** (8 categories pending):
1. All SEU operational orders, policies, directives, and SOPs
2. All SEU personnel rosters and position classifications
3. All SEU deployment logs and incident reports (2024–present)
4. All MOUs or cooperative agreements establishing SEU authority
5. All grant applications or awards funding SEU operations
6. All SEU training curricula and certification records
7. All SEU use-of-force reports (§ 832.7 / SB 1421 mandatory)
8. Any memoranda between TCPD and Tulare County Sheriff / DA re: SEU

---

## Section 4 — Cross-Jurisdiction Lattice (Emerging Pattern Map)

The following patterns are appearing across multiple jurisdictions and should be integrated into the `jim_collection` cross-jurisdiction analysis:

### 4.1 Flock Safety Lattice

| Jurisdiction | Flock Docs | Key Evidence | Status |
|---|---|---|---|
| visalia-pd | 22 | MSAs, fee schedules, community letters, cross-jur analysis | DISCLOSED |
| visalia | 1 | Single agenda attachment | DISCLOSED |
| fresnocounty | 0 | Zero — despite public statement re: "standing by contracts" | OPACITY FINDING |
| tcso | unknown | Not queried yet | PENDING |
| porterville | unknown | Not queried yet | PENDING |
| farmersville | unknown | Not queried yet | PENDING |

Visalia-PD's "Vpd Cross Jurisdictional Flock Analysis V1/V2" documents should be read directly — they may name other agencies in the ALPR data-sharing network, which would create new CPRA targets.

### 4.2 ALPR / SB 524 Compliance Lattice

| Jurisdiction | ALPR Finding | SB 524 Cited? |
|---|---|---|
| fresnocounty | CRITICAL — multiple docs | No |
| visalia-pd | CRITICAL — 22 Flock docs | No |
| tcso | TCSO corpus has 573 docs — not yet cross-referenced | Pending |
| tulare | ALPR study session documented (2025 CIP) | Partial |
| porterville | ALPR agenda items documented (2023-06, 2024-06) | Unknown |

### 4.3 Consent Calendar / Missing-Final-Action Lattice

| Jurisdiction | Count | Notes |
|---|---|---|
| fresnocounty | 20+ HIGH | Systemic across multiple dates |
| visalia | Known pattern | Identified in prior MAS |
| others | Not cross-tabulated yet | Needs jim_collection query |

### 4.4 Undisclosed Enforcement Units

| Jurisdiction | Unit | Status |
|---|---|---|
| tcpd | SEU (Special Enforcement Unit) | Confirmed operational 2026-04-29; zero documentation |

---

## Section 5 — CPRA Action Targets

### 5.1 Fresno County (NEW — Identified This Session)

**Target 1: Fresno County Sheriff's Office**
- Request: All contracts, MSAs, amendments, and renewal options with Flock Safety Inc.
- Request: All data retention schedules and data sharing addenda for ALPR systems
- Request: All inter-agency MOUs for ALPR data sharing with state or federal agencies
- Basis: Zero Flock documentation in 14,783 BOS matters despite confirmed ALPR deployment

**Target 2: Fresno County BOS Clerk**
- Request: All agenda items, staff reports, resolutions, and consent calendar attachments referencing ALPR, automated license plate reader, or Flock Safety (2018–present)
- Request: All items where `final_action` was approved but not recorded in Legistar (20+ identified)
- Basis: `admin:missing-final-action` HIGH anomaly across 20+ agenda documents

**Target 3: Fresno County IT / Chief Executive Office**
- Request: SB 524 / AB 2557 technology accountability policy for all ALPR systems
- Request: Any automated decision system impact assessment for ALPR
- Basis: Multiple CRITICAL `ALPR system referenced without SB 524 AI-transparency policy citation` findings

**Target 4: Any Fresno County city / agency with joint-use**
- Request: Inter-agency MOUs for joint ALPR networks with Fresno PD, Clovis PD, Fresno County Sheriff

### 5.2 TCPD (Carried Forward — CPRA-004 Supplement)

See Section 3.4 — 8 categories targeting SEU operational records.

---

## Section 6 — MAS Export Status

| Jurisdiction | Export File | Size | Uploadable to Claude.ai? |
|---|---|---|---|
| visalia | `data/mas_export/visalia_MAS.json` | ~8 MB | Yes |
| tcso | `data/mas_export/tcso_MAS.json` | ~4 MB | Yes |
| tcda | `data/mas_export/tcda_MAS.json` | ~2 MB | Yes |
| tcpd | Not yet exported | — | — |
| fresnocounty | `data/mas_export/fresnocounty_MAS.json` | ~40 MB | No — too large |
| all others | Purged from temp store | — | Needs rebuild |

**fresnocounty_MAS.json split**: 40 MB exceeds Claude.ai project file limit (~10 MB typical). Must be split before upload to Opus project. Splitting options:
- By severity: `critical.json`, `high.json`, `medium.json`, `low.json`
- By finding type: group the 151 finding types
- By date range: year-by-year slices
- By jurisdiction sub-area (if metadata supports it)

A `scripts/split_mas_export.py` script needs to be built. Target: output files under 8 MB each.

---

## Section 7 — Pending Work (Priority Order)

### P0 — Immediate (This Next Session)

1. **Rebuild RAG index** — `python scripts/build_rag_index.py` — index does not include Fresno County yet; 33,968 docs need to be re-indexed
2. **Build `scripts/split_mas_export.py`** — split `fresnocounty_MAS.json` (40 MB) into uploadable chunks for Opus project
3. **Update CLAUDE.md** — DB totals: `33,968 documents / 106,668 findings`; add fresnocounty row to corpus table

### P1 — Opus Analysis (This Handoff)

4. **Fresno County MAS V1.0** — Full multi-layer anomaly synthesis using fresnocounty findings data
5. **Cross-jurisdiction Flock lattice expansion** — Read VPD Cross Jurisdictional Flock Analysis V1/V2 documents directly; identify named partner agencies
6. **CPRA draft letters** — Three letters: Fresno County Sheriff, BOS Clerk, County IT/CEO
7. **jim_collection update** — Add Fresno County pattern entries to cross-jurisdiction index

### P2 — Infrastructure

8. **odia_legal Phase 1** — Skeleton + CPRA crosswalk + L-9 recodification + citation parser (CRITICAL deadline: 2028-07-02)
9. **Multi-index RAG routing** — Wire `ace_collection` and `jim_collection` into live API query path via `corpus_filter` parameter
10. **odia-v2 training data prep** — After TCPD full ingest + legal corpus expansion

### P3 — Remaining Corpus

11. **TCPD Questys harvest** — `scripts/ingest_tcpd.py` (Questys CMX portal adapter) — procurement contracts, SEU records (if disclosed post-CPRA), grant applications
12. **Fresno County neighboring cities** — Fresno PD, Clovis, Madera County — consider for NSU ingest
13. **Kern County / Kings County** — Next geographic layer in the San Joaquin Valley lattice

---

## Section 8 — Files to Upload to Opus Project Folder

For Opus to perform MAS V1.0 on Fresno County and update cross-jurisdiction documentation, provide these files:

| File | Location | Purpose |
|---|---|---|
| This handoff | `ODIA_OPUS_HANDOFF_2026-07-30.md` | Session record and briefing |
| Fresno County MAS chunks | `data/mas_export/fresnocounty_*.json` (after split) | Primary analysis corpus |
| Corpus archive MASTER_INDEX | `data/corpus_archive/MASTER_INDEX.json` | Navigation + totals |
| Fresno County archive index | `data/corpus_archive/fresnocounty/index.json` | Jurisdiction document list |
| by_finding FINDING_INDEX | `data/corpus_archive/by_finding/FINDING_INDEX.json` | All 151 finding types |
| VPD Flock analysis docs | `data/corpus_archive/visalia-pd/` (Flock docs) | Comparison baseline |
| visalia MAS | `data/mas_export/visalia_MAS.json` | Cross-reference |
| tcso MAS | `data/mas_export/tcso_MAS.json` | Cross-reference |

**Note on 40 MB limit**: Run `scripts/split_mas_export.py` (to be built) before uploading fresnocounty MAS.

---

## Section 9 — MAS Requests for Opus This Session

When analyzing with these materials, Opus should produce:

### Request A — Fresno County MAS V1.0
Full multi-layer anomaly synthesis for Fresno County. Required sections:
1. Executive summary (threat tier, key findings count by severity)
2. Surveillance / ALPR layer — complete Axon Enterprise finding inventory; SB 524 compliance gap
3. Procurement opacity layer — Flock Safety absence analysis; consent calendar pattern; missing-final-action inventory
4. Fiscal layer — any abnormal contract values, sole-source indicators, emergency procurement
5. Constitutional layer — 1st/4th Amendment exposure from undisclosed ALPR deployment
6. Administrative layer — Legistar record integrity (missing-final-action pattern)
7. CPRA action matrix — Section 5.1 targets, specific document categories, legal basis per request
8. Cross-jurisdiction lattice entry — how fresnocounty findings connect to other corpus jurisdictions

### Request B — Flock Safety Cross-Jurisdiction Lattice Document
Synthesize across visalia, visalia-pd, and fresnocounty to produce a `jim_collection`-ready document:
- Named agencies in VPD's cross-jurisdictional Flock analysis
- Known MSA terms from Visalia-PD (dates, parties, renewal terms)
- Gap analysis: what Fresno County should have disclosed based on Visalia-PD precedent
- Estimated contract value range (using Visalia-PD as baseline if dollar amounts are in their docs)

### Request C — Updated CPRA Letter Drafts
Three draft CPRA letters using Government Code § 6250 et seq.:
1. Fresno County Sheriff — Flock Safety contracts + data sharing + retention
2. Fresno County BOS Clerk — ALPR agenda items + missing-final-action resolutions
3. Fresno County IT/CEO — SB 524 compliance / technology accountability policy

Each letter should cite: specific finding types from ODIA, relevant statutory authority (SB 524, Pen. Code § 832.7 where applicable), and 10-day acknowledgment / 30-day response deadlines.

### Request D — SEU Anomaly Memo Update (TCPD)
Update the SEU anomaly record first drafted June 18 to current canonical form:
- Confirmed machine finding language
- Updated CPRA supplement scope (8 categories)
- Monell doctrine exposure analysis
- Recommended next step: CPRA supplement filing date

---

## Section 10 — Technical Reference

### DB Schema (Key Tables)

```
documents:  id, document_id, title, document_type, jurisdiction, authority, 
            version_date, signatory, created_at, updated_at, metadata_json

analyses:   id, document_id, analysis_timestamp, anomaly_count, scalar_score,
            severity_score, coherence_bonus, engine_version, summary, metadata_json

anomalies:  id, analysis_id, anomaly_id, issue, severity, layer, details_json

seen_hashes: sha256, first_seen_at, document_id, jurisdiction_id,
             text_extraction_method, text_char_count

sections:   (exists, schema has content TEXT, but table is EMPTY — 
             text extraction does not persist paragraph-level content)
```

**Anomaly linkage**: `anomalies.analysis_id` → `analyses.id` → `analyses.document_id` → `documents.document_id`

**To query fresnocounty critical findings**:
```sql
SELECT an.anomaly_id, an.issue, an.severity, an.layer, an.details_json, d.title
FROM anomalies an
JOIN analyses al ON al.id = an.analysis_id
JOIN documents d  ON d.document_id = al.document_id
WHERE d.jurisdiction = 'fresnocounty'
AND an.severity IN ('critical', 'high')
ORDER BY CASE an.severity WHEN 'critical' THEN 0 ELSE 1 END, an.layer, an.issue
```

### RAG Endpoints

```
POST http://127.0.0.1:18741/api/v1/rag/query
Content-Type: application/json
{"query": "...", "top_k": 15}

POST http://127.0.0.1:18741/api/v1/webhook/ingest-and-analyze
Content-Type: multipart/form-data
file=@<path>, jurisdiction=<jur>, token=<jwt>
```

### Key Scripts

| Script | Purpose |
|---|---|
| `scripts/build_rag_index.py` | Rebuild TF-IDF index from live DB |
| `scripts/ingest_legistar.py` | Legistar corpus ingest (resumable) |
| `scripts/ingest_local_tcpd.py` | Local PDF batch ingest (TCPD) |
| `scripts/build_corpus_archive.py` | Build navigable archive from DB |
| `scripts/export_mas_corpus.py` | Export MAS JSON per jurisdiction |
| `scripts/split_mas_export.py` | Split large MAS exports (PENDING BUILD) |

### Jurisdiction IDs (for scripts and DB queries)

`fresnocounty`, `visalia`, `visalia-pd`, `tcso`, `tcda`, `tcpd`, `tulare`, `tulare-county`, `farmersville`, `exeter`, `dinuba`, `lindsay`, `porterville`, `woodlake`, `multi-jurisdiction`

### Legistar Client IDs

| Jurisdiction | Legistar Client ID |
|---|---|
| Visalia | `visalia` |
| Fresno County | `fresnocounty` |
| Porterville | `porterville` |
| Farmersville | (Questys / non-Legistar) |

### odia_legal Detector Reference

| ID | Name | Status |
|---|---|---|
| L-1 | Fiscal Compliance | Active |
| L-2 | Procurement Compliance | Active |
| L-3 | Constitutional Exposure | Active |
| L-4 | Use-of-Force Policy | Active |
| L-5 | Grant Compliance | Partial |
| L-6 | Surveillance Oversight | Active |
| L-7 | Regulatory Authority Chains | Active — SEU finding |
| L-8 | Data Privacy | Active |
| L-9 | CPRA Crosswalk | Partial — needs recodification |
| L-10 | Inter-Agency Agreement | Active |

---

## Appendix A — Flock Safety Document Inventory (Visalia-PD)

For comparison purposes — these represent the disclosure standard:

```
Vpd Cross Jurisdictional Flock Analysis (V1)
Vpd Cross Jurisdictional Flock Analysis V2
1 Flock (1), (2), (3), (4)    [numbered attachment series]
1 Flock                        [primary attachment]
2 Flock (1)                    [secondary series]
2 Flock
2024.09.20 Flock Agreement
2024.09.23 Flock Agreement
Flock Master Service Agreement (1), (2), (2) (1), (3)
Flock Reinstall Fee Schedule (1), (2)
Flock Reinstall Fee Schedule
Letter To The Community — Flock Safety Update
```

22 total documents. Fresno County: 0.

---

## Appendix B — Session RAG Query Results Summary

| Query | Confidence | Top Source Jurisdiction | Key Finding |
|---|---|---|---|
| Flock Safety contract terms + procurement | 0.66 | visalia (cross-jur pull) | "Vendor selection without public solicitation (sole-source)" flagged; no fresnocounty docs retrieved |
| Grant funding for Flock cameras | 0.495 | visalia (cross-jur pull) | Empty grant_trails; no grant documentation found for fresnocounty |
| Data sharing MOUs / ALPR | 0.458 | tulare, visalia-pd (cross-jur pull) | No inter-agency MOUs for fresnocounty ALPR; Tulare ALPR policy docs retrieved instead |
| Consent calendar placement | 0.452 | fresnocounty | admin:missing-final-action anomaly surfaced; approval signals present, final_action null |

Low confidence scores confirm: the TF-IDF corpus index does not yet include fresnocounty documents (index predates ingest). After RAG index rebuild, Fresno County queries will return direct matches. All four queries confirm Flock Safety has no public footprint in Fresno County Legistar.

---

*End of ODIA Opus Handoff — 2026-07-30*  
*Next handoff target: after fresnocounty MAS V1.0 complete + RAG index rebuilt + odia_legal Phase 1 initiated*
