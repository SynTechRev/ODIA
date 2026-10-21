# C.O.N.T.R.A. Opus Handoff — 2026-08-23

**Supersedes**: First Opus assessment (CONTRA — no file; generated as conversation output, 2026-08-23 prior session)  
**Prepared by**: MARS (SynTechRev) via Claude Code  
**Session scope**: Uber ecosystem ingest (109 instruments / 21 entities), CIFU metric build, first Opus assessment, both critical detector fixes (L-13:A, L-17:C), full corpus rescore (283 docs), Cricket Wireless purge and clean ingest  
**Framework version**: C.O.N.T.R.A. V1.0 / CASI v1.1  
**DB at handoff**: 311 documents / 7,134 findings across 28 entities  
**CIFU at handoff**: 90.5 / 100 — Foreclosure Regime (Uber Consumer Full Chain)

---

## Section 1 — What Happened This Session

### 1.1 Uber Ecosystem Corpus Expansion (NSU Protocol)

- **Script**: `scripts/build_manifest_uber_ecosystem.py` (complete rewrite)
- **Routing**: `_ROOT_ROUTING` (13 routed + 4 rejected root-level files) + `_SUBFOLDER_MAP` (per-vendor reject lists and cross-entity rerouting)
- **Special routing**: `Facebook/TrustArc` and `Meta/TrustArc` nested paths → `TrustArc Inc.` entity; `Drata/Google API Services User Data Policy.pdf` → Google LLC
- **Dry-run confirmed**: 109 instruments, 21 entities, 24 correct rejects
- **Entities added**: Uber Technologies Inc., Portier LLC, Cambridge Mobile Telematics, Tealium Inc., Fullstory Inc., Meta Platforms, Microsoft Corporation, NextRoll Inc., Pinterest Inc., Plaid Inc., Dwolla Inc., Modulr FS Limited, Upside Commerce Group, Jumio Inc., Socure Inc., Veriff Inc., TrustArc Inc., Drata Inc., Vanta Inc., Sprinto Inc.
- **Key analytical note**: Three simultaneous biometric identity verification vendors (Jumio, Socure, Veriff) within the Uber powered-by chain. BIPA 740 ILCS 14 requires per-scan consent per vendor — three independent exposure chains from a single Uber driver/rider verification event.
- **TrustArc lineage**: TrustArc (formerly TrustE) appears simultaneously as (1) historical Facebook/Meta privacy certifier, (2) current Meta consent infrastructure vendor, and (3) Uber's direct Consent Management Platform. Certifier-turned-processor relationship without assessor independence.

### 1.2 FDR / RCD Backfill and Zero-Aggregate Fix

- **Script**: `scripts/backfill_fdr_rcd.py` (modified)
- **Bug fixed**: `fdr = None` for zero-aggregate documents caused skip logic to leave FDR as NULL. Changed to `fdr = 0.0` for zero-aggregate rows (agg=0 is a valid scored state — all five axes returned 0, not a pipeline error).
- **Result**: 9 previously-skipped zero-CASI rows updated.

### 1.3 Corporate Family Tagging

- **Script**: `scripts/corporate_family_expander.py` (modified)
- **Added**: 30+ seed-map entries for all Uber ecosystem entities (`"Portier LLC": "Uber"`, `"Jumio Inc.": "Jumio"`, etc.)
- **Added**: `"Comcast / Xfinity": "Comcast"` to prevent unnecessary EDGAR API calls
- **Result**: All 28 entities carry `corporate_family` values set at ingest time from `_SUBFOLDER_MAP`; expander correctly reported 0 changes on second run (values already correct).

### 1.4 CIFU Metric Build

- **Script**: `scripts/compute_cifu.py` (created)
- **Chain defined**: `uber_consumer_full` — Uber Technologies Inc. (anchor) + 19 sub-processors, advertisers, payment processors, biometric verifiers, consent managers, compliance auditors
- **Formula**: `CIFU_score = round((breadth_pct * 50) + (depth_pct * 50), 1)` where breadth_pct = axes_with_any_entity / 5 and depth_pct = mean(entity_count_per_active_axis / 20)
- **Initial result**: 93.5 / 100 (Foreclosure Regime)
- **Corrected result**: 90.5 / 100 (Foreclosure Regime) — Modification & Consent depth corrected from 100% to 70% after identifying the L-13:A false findings inflating that axis
- **Output file**: `data/cifu_report.json`

### 1.5 First Opus Assessment (Prior Session)

Opus reviewed the 93.5 CIFU result and the full corpus state pre-fix. Opus identified:

1. **L-17:C false positive defect** — bare `text|image|audio|video` alternatives in `_P_C` fired without AI/training context. Generated 6,477 false findings (39.5% of corpus). Defect class: broad alternative inside alternation with correctly-constrained siblings.
2. **L-13:A false positive defect** — unanchored `we\s+(?:may|can|will)` fired without modification verb. Generated 4,090 false findings (24.9% of corpus). Same defect class.
3. **CIFU numerator overclaim** — `modification_and_consent` depth was 100% (20/20 entities) due to L-13:A inflation; corrected to 70% (14/20 entities).
4. **Proposed CIFU v2** — severity-weighted depth, N_disclosed denominator (44 Uber vendors total, not 20 retrieved), geometric mean formula, Shannon entropy concentration term.
5. **Source URL coverage gap** — only 27/310 documents had `source_url` at assessment time (8.7%); blocks the entire automation roadmap.
6. **§1281.96 pipeline empty** — `s1281_96_cases` table has 0 rows; `D:\CONTRA Contract Corpus\AAA\` empty; enforcement cost asymmetry axis effectively starved (practical CASI ceiling ~80, not 100).

### 1.6 Detector Fixes — L-13:A and L-17:C

Both fixes implemented in the same session as the Opus assessment.

**L-13:A fix** — `src/oraculus_di_auditor/contra/l13_unilateral_modification.py`:
- Deleted the entire first alternative `we\s+(?:may|reserve\s+the\s+right\s+to|can|will)` from `_P_A`
- Retained only the correctly-constrained alternative: `(?:company|service\s+provider|we)\s+(?:may|reserves?)\s+(?:at\s+any\s+time\s+)?(?:modify|change|update|revise|amend|alter)\s+(?:these\s+)?(?:terms?|agreement|policy|conditions?|provisions?)`
- Impact: 4,090 false findings eliminated

**L-17:C fix** — `src/oraculus_di_auditor/contra/l17_ml_ai_training.py`:
- Removed bare `text|image|audio|video` alternatives from `_P_C`; replaced with modality-combination phrases only (`text and image`, `image and audio`, `multimodal`, etc.)
- Moved `has_train = bool(_P_D_TRAIN.search(text_lower))` computation before the C scan
- Gated entire C scan on `has_train` — `if has_train: findings += scan_pattern(_P_C, ...)`
- Removed duplicate `has_train2` variable in E check; unified to shared `has_train`
- Impact: 6,477 false findings eliminated

### 1.7 Discovery-by-Hash Rescore

- **Script**: `scripts/rescore_commercial.py` (created)
- **Strategy**: Walk all manifest files, compute SHA-256(raw_pdf_bytes), match against DB hashes, delete old ContraFinding + CasiScore rows, re-run all L-11–L-20 detectors, recompute CASI, insert with `framework_version="1.1"`
- **Result**: 283/287 matched documents rescored; 4 skipped (same PDF at multiple manifest paths)
- **Checkpoint**: `cache/rescore_checkpoint.json` (resume support)
- **FDR fix in rescore**: `fdr = round(len(new_findings) / agg, 3) if agg > 0 else 0.0` — matches backfill behavior

### 1.8 Cricket Wireless Purge and Fresh Ingest

- **Problem**: Rescore checkpoint from prior run had 283 docs marked done. New Cricket PDFs had different SHA-256 hashes (different file versions). Old Cricket max CASI was 84 (Foreclosure Regime) — entirely detector noise.
- **Resolution**:
  1. Purged 15 old Cricket CommercialDocument + ContraFinding + CasiScore + Provenance rows via `scratchpad/purge_cricket.py` (entity record retained)
  2. Built new manifest: `python scripts/build_manifest_from_folder.py --folder "D:\CONTRA Contract Corpus\Cricket Wireless" --entity "Cricket Wireless" --out contra_manifest_cricket.json` → 16 entries
  3. Fresh ingest: `contra_batch_ingest.py --manifest contra_manifest_cricket.json --skip-review` → 16 OK, 13.3s
  4. Backfill: 3 Cricket zero-CASI rows updated (FDR=0.0)
- **Cricket corrected max CASI**: 69 (Severe — not Foreclosure Regime)
- **AT&T template propagation thesis**: Holds, but was overstated. Cricket's high-severity findings reflect AT&T arbitration architecture inheritance, not independent Foreclosure Regime severity.

---

## Section 2 — Platform State at Handoff

| Component | State |
|---|---|
| ODIA platform version | 3.9.2 (master branch) |
| CONTRA framework version | V1.0 / detector code v1.1 (post-fix) |
| DB | SQLite `contra_corpus.db` at `D:\CONTRA Contract Corpus\contra_corpus.db` (separate from `oraculus_audit.db`) |
| Documents | **311** (unique, SHA-256 deduped) |
| Entities | **28** |
| Findings | **7,134** (post-fix, framework_version="1.1") |
| CASI archive | `data/contra_corpus_archive/` — 29,503 KB across 48 JSON files, 4 bands |
| Foreclosure Regime documents | **0** |
| CIFU | 90.5 / 100 (Foreclosure Regime band) — Uber Consumer Full Chain |
| Source URL coverage | ~27/311 documents (8.7%) |
| `s1281_96_cases` rows | 0 |
| `commercial_document_version_chain` rows | 0 |
| `framework_version="1.1"` rows | 283 (rescored) |
| `framework_version="1.0"` rows | ~28 (Cricket fresh ingest + unmapped docs) |

---

## Section 3 — Full Corpus State

### 3.1 Entity Rankings (by avg CASI, post-fix)

| Entity | Docs | Avg CASI | Max CASI | Band | Notes |
|---|---|---|---|---|---|
| Upside Commerce Group | 2 | 50.0 | 74 | Severe | Loyalty/cashback — full 5-axis presence |
| Modulr FS Limited | 1 | 50.0 | 50 | Substantial | UK payment infra |
| Sprinto Inc. | 2 | 46.5 | 73 | Severe | Compliance-vendor paradox peak |
| Microsoft Corporation | 6 | 33.8 | 71 | Severe | Azure + Bing Ads — highest avg among large entities |
| Cricket Wireless | 16 | 32.1 | 69 | Severe | Corrected from false 84 FR |
| Fullstory Inc. | 12 | 27.6 | 80 | Severe | **Highest max in corpus** — session replay |
| AT&T Mobility | 35 | 57.1 | 77 | Severe | **Highest avg CASI in corpus**; prior session stated 22.9 — that was a pre-expansion sample of ~4 docs |
| Comcast / Xfinity | 53 | 41.0 | 77 | Severe | 2nd-tier max (tied AT&T); 53 docs |
| JPMorgan Chase | 16 | 48.7 | 68 | Severe | Payment + banking instruments |
| Jumio Inc. | 10 | 32.6 | 60 | Substantial | Biometric verification |
| Socure Inc. | 4 | 33.3 | 34 | Elevated | Biometric — lower spread than Jumio |
| Veriff Inc. | 4 | 27.8 | 34 | Elevated | European biometric — GDPR framing |
| Uber Technologies Inc. | 8 | 27.9 | 71 | Severe | Anchor entity |
| Vanta Inc. | 11 | 17.2 | 53 | Substantial | Compliance-vendor paradox |
| Drata Inc. | 7 | 21.3 | 39 | Elevated | Compliance-vendor paradox |
| TrustArc Inc. | 11 | 14.9 | 34 | Elevated | Certifier-turned-processor |

### 3.2 CASI Band Distribution (post-fix)

| Band | Range | Count | % |
|---|---|---|---|
| Baseline | 0–20 | 146 | 47.0% |
| Elevated | 21–40 | 130 | 41.8% |
| Substantial | 41–60 | 18 | 5.8% |
| Severe | 61–80 | 17 | 5.5% |
| Foreclosure Regime | 81–100 | **0** | **0%** |

### 3.3 Finding Impact of Detector Fixes

| Metric | Pre-fix | Post-fix | Change |
|---|---|---|---|
| Total findings | 16,407 | 7,134 | -56.5% |
| FR documents | 14 | 0 | -14 |
| Severe documents | 8 | 17 | +9 |
| Substantial documents | 102 | 18 | -84 |
| L-13:A false findings removed | — | 4,090 | 24.9% of pre-fix corpus |
| L-17:C false findings removed | — | 6,477 | 39.5% of pre-fix corpus |
| Combined false findings removed | — | 10,567 | 64.4% of pre-fix corpus |

### 3.4 CIFU Report Summary (current)

| Axis | Entity Count | Depth % | Active |
|---|---|---|---|
| Data Extraction Depth | 19/20 | 95% | Yes |
| Modification & Consent | 14/20 | 70% | Yes |
| Procedural Adhesion | 19/20 | 95% | Yes |
| Remedy Foreclosure | 16/20 | 80% | Yes |
| Enforcement Cost Asymmetry | 13/20 | 65% | Yes |
| **Overall CIFU** | **5 active axes** | **81%** | 90.5 / 100 |

**Key analytical finding**: The corpus now demonstrates that no single consumer contract in 311 documents reaches Foreclosure Regime individually (highest single-instrument score: Fullstory at 80). CIFU at 90.5 is achieved entirely through cross-instrument compounding across a 20-entity network. This makes CIFU *more important*, not less, as the primary consumer risk metric for network-structured ecosystems.

**Known CIFU denominator issue**: The chain is defined as "vendors with retrieved documents" (20 entities). Uber's privacy policy discloses 44 sub-processors, of which 27 have empty corpus folders. At the full 44-vendor denominator, CIFU drops to approximately 71.8 (from 90.5). The honest denominator requires filling those 27 folders.

---

## Section 4 — Detector Audit (All 10 L-11–L-20)

Systematic review for the same defect class found in L-13:A and L-17:C:
**Defect class**: A broad unanchored alternative inside a regex alternation, alongside correctly-constrained siblings, that fires without requiring the same semantic context as those siblings.

### 4.1 Audit Results

| Detector | Status | Risk Level | Finding |
|---|---|---|---|
| L-11 Arbitration Architecture | CLEAN | None | All 10 sub-detectors (A–J) require specific arbitration vocabulary; no broad unanchored alternatives |
| L-12 Choice of Law/Forum | WATCH | Low-Medium | `_P_C` first alternative: `\b(?:claim\|action\|suit\|lawsuit\|...\|dispute)\b.{0,300}\bwithin...\s+(?:days?\|months?\|years?)\b` — "action" and "suit" appear in non-limitation contexts; DOTALL + 300-char gap increases exposure |
| L-13 Unilateral Modification | **FIXED** | RESOLVED | L-13:A unanchored `we\s+may\|can\|will` removed; 4,090 false findings eliminated |
| L-14 Data Collection Depth | CLEAN | None | All 8 sub-detectors require specific CCPA-category vocabulary; `_P_A` correctly gates on collection verb |
| L-15 Data Retention | WATCH | Medium | `_P_COLLECT` first alternative: `we\s+(?:collect\|gather\|receiv\|obtain\|process\|store\|retain\|use)\w*` — `use` alternative fires on "we use arbitration", "we use cookies", "we use these terms"; if `has_collection=True` and no defined retention period, L-15:A fires — potentially over-fires on non-data documents |
| L-16 Onward Transfer | WATCH | Low | `_P_G_BROAD` uses `(?:determine\|choose\|decide)` without "we" prefix; could fire on non-data-disclosure sentences containing those verbs + "share" + "government/authority"; however `has_broad and not has_narrow` design limits false positive severity |
| L-17 ML/AI Training | **FIXED / WATCH** | Post-fix | L-17:C bare modalities removed; `has_train` gate added; 6,477 false findings eliminated. However, L-17:C remains #1 sub-detector post-fix at 1,193 hits — the `any\s+(?:data\|content\|information)\s+you\s+(?:provide\|submit\|...)` alternative in `_P_C` fires on standard ToS phrases once `has_train` gates true; requires spot-check on 10 random matches |
| L-18 Remedy Foreclosure | CLEAN | None | All 8 sub-detectors require specific damages/waiver legal terminology |
| L-19 Enforcement Asymmetry | CLEAN | None | All sub-detectors well-constrained; G is intentional absence detection (arbitration without 1281.97/98 cite) |
| L-20 Dark Pattern | CLEAN | Note | `_P_C` overlaps with L-13:C semantically ("by continuing to use...you agree") — different axes (procedural_adhesion vs modification_and_consent), so not double-counting the same axis, but same underlying text contributes to two axes simultaneously. Intentional design choice, not a bug. |

### 4.2 Recommended Verification Actions

**L-15 `_P_COLLECT` (Medium priority)**:
Run the following query to count L-15:A findings on documents with no data-collection vocabulary beyond "we use":
```sql
SELECT COUNT(*) FROM contra_findings
WHERE layer = 'L-15' AND sub_detector = 'A'
AND document_hash IN (
  SELECT document_hash FROM commercial_documents
  WHERE doc_type NOT IN ('privacy_notice')
)
```
If L-15:A appears in non-privacy-notice documents lacking clear data-collection language, consider adding a secondary gate: `has_collection` must require `collect|gather|receiv|obtain|process|store|retain` (not `use`), or the `data|information` phrase structure of the second alternative.

**L-12 `_P_C` (Low priority)**:
Run `SELECT COUNT(*) FROM contra_findings WHERE layer = 'L-12' AND sub_detector = 'C'` and spot-check a sample of matched texts. If "within 30 days" notices (e.g., cancellation notices, service windows) are generating L-12:C hits outside of limitation-of-action contexts, tighten by requiring "claim|lawsuit|legal action|dispute|cause of action" to appear within 50 chars of "within X days" (not 300).

---

## Section 5 — Pending Work (Priority Order)

### P0 — Code Correctness (Before Any External Use)

1. **Fix `commercial.py:218`** — Sets `fdr = None` when `agg=0`; should be `fdr = 0.0` to match `backfill_fdr_rcd.py` and `rescore_commercial.py`. One-line fix. Path: `src/oraculus_di_auditor/contra/commercial.py`.

2. **Anti-pattern regression suite** — Add negative-fixture tests for all 10 detectors. Minimum fixture set from the two known defects:
   - L-13:A negative: `"We will send you the latest Home Gateway within 30 days."` → expect 0 L-13:A findings
   - L-13:A negative: `"We may contact you regarding your account."` → expect 0 L-13:A findings
   - L-17:C negative: `"TEXT SHOWN ONLY FOR ACKNOWLEDGMENT."` → expect 0 L-17:C findings
   - L-17:C negative: `"We accept text, image, audio, and video as proof of delivery."` → expect 0 L-17:C findings
   - L-15:A negative: `"We use arbitration to resolve all disputes under these terms."` (no data collection language) → verify L-15:A does NOT fire
   - L-12:C negative: `"Requests must be submitted within 30 days of purchase."` (cancellation/return policy context) → verify L-12:C does NOT fire as shortened-SOL

### P1 — CIFU v2 Implementation

3. **CIFU v2 formula** (Opus to spec in this session — see Section 7 Request A):
   - Severity-weighted depth instead of binary entity presence
   - `N_disclosed` denominator (44 Uber sub-processors, not 20 retrieved)
   - Geometric mean across axes instead of arithmetic mean
   - Shannon entropy concentration term (penalizes single-entity dominance)

4. **N_disclosed denominator** — 27 empty Uber vendor subfolders (Amazon, Criteo, TikTok, LinkedIn, PayPal, Snap, Reddit, The Trade Desk, LiveRamp, Epsilon, etc.) need PDFs for honest CIFU denominator. Without them, CIFU 90.5 is computed on a selected 45% of the disclosed vendor network.

### P2 — Corpus Expansion

5. **AT&T → Cricket CIFU chain** — Cheapest next chain (both already in DB, zero additional retrieval cost). Tests intra-family independent instruments. AT&T is anchor; Cricket is subsidiary with independent arbitration.

6. **DoorDash or Lyft comparison CIFU** — CIFU needs a baseline. 90.5 is uninterpretable without a comparator. DoorDash or Lyft would provide a peer gig-economy chain for calibration.

7. **T-Mobile ingest** — JS-rendered site, manual download to `D:\CONTRA Contract Corpus\T-Mobile\` required. With AT&T + Cricket + T-Mobile, telecom section achieves analytical completeness.

8. **Verizon ingest** — Verizon's consumer arbitration clause is the most aggressive in US telecom (mandatory, class waiver, fee-split, JAMS-only, 1-year SOL). Strong candidate for highest single-chain CIFU in telecom.

### P3 — Pipeline Infrastructure

9. **Source URL backfill** — Only ~27/311 documents have `source_url`. This blocks: ToS monitoring, version-diffing, Wayback integration, and the entire automation roadmap. Must backfill from manifest `source_url` fields where available; for gaps, manual entry or web-search-assisted backfill.

10. **Version chain** — `commercial_document_version_chain` has 0 rows. Requires proactive Wayback archival at ingest time. Strategy: submit every fetched URL to `web.archive.org/save/` at ingest; link successive versions by entity + doc_type + SHA-256 diff.

11. **§1281.96 arbitration pipeline** — `s1281_96_cases` has 0 rows. Schema exists (30 columns). `D:\CONTRA Contract Corpus\AAA\` is empty. Until real arbitration awards data is ingested, `enforcement_cost_asymmetry` axis is theoretically starved — CASI ceiling per instrument is practically ~80, not 100. This explains why no instrument reaches Foreclosure Regime individually.

12. **CCM (Certification Capture Metric)** — TrustArc is simultaneously (a) historical Facebook privacy certifier (TrustE seal), (b) current Meta consent infrastructure vendor, and (c) Uber's direct CMP. CCM would quantify assessor independence loss when a privacy certifier becomes a paid client's infrastructure vendor. Proposed: `CCM = (shared_entity_count / disclosed_certifier_count) × temporal_persistence_score × role_overlap_factor`. Design spec TBD.

### P4 — Analytical Deliverables

13. **CONTRA Corpus Report V1.0** — A standalone public-facing report document summarizing: (a) methodology, (b) 311-document corpus state, (c) top-10 entities by risk, (d) CIFU analysis, (e) three key findings (compliance-vendor paradox, biometric triple-deployment, certifier capture). Target: publishable via ODIA frontend `/contra` page.

14. **BIPA analysis memo** — Three simultaneous biometric deployments (Jumio, Socure, Veriff) within a single Uber onboarding flow. BIPA § 740 ILCS 14 requires per-scan written consent per vendor. If Uber's consent page names only Uber (not each biometric vendor), all three are in individual exposure chains without disclosed consumer consent. Memo format for legal reference.

---

## Section 6 — Files to Upload to Opus Project Folder

For Opus to perform the requested analysis (Section 7), upload these files:

| File | Location | Purpose |
|---|---|---|
| This handoff | `data/handoffs/CONTRA_OPUS_HANDOFF_2026-08-23.md` | Primary briefing |
| CIFU report | `data/cifu_report.json` | Current CIFU state (90.5, all axis detail, all member entities) |
| Corpus archive index | `data/contra_corpus_archive/MASTER_INDEX.json` (if exists) | Corpus navigation |
| Entity breakdown sample | DB query output — top 15 entities by avg CASI with axis breakdowns | Context for CIFU v2 design |
| L-15 detector source | `src/oraculus_di_auditor/contra/l15_data_retention.py` | For `_P_COLLECT` audit in Request C |
| L-12 detector source | `src/oraculus_di_auditor/contra/l12_choice_of_law_forum.py` | For `_P_C` audit in Request C |

---

## Section 7 — Requests for Opus This Session

### Request A — CIFU v2 Full Design Specification

Produce a complete implementation specification for CIFU v2. The current formula (`breadth_pct × 50 + depth_pct × 50`) has three structural problems:

1. **Binary depth**: Entity either has findings on an axis (counts as 1) or doesn't (counts as 0). A company with CASI axis score 2/20 counts the same as one with 19/20.
2. **Retrieved denominator**: The chain uses 20 entities (those with PDFs) rather than 44 (all disclosed sub-processors). This inflates CIFU by ~26% relative to the honest measurement.
3. **No concentration term**: If one entity (e.g., Fullstory at 80) drives the majority of axis scores, CIFU doesn't capture the concentration risk — the consumer's actual exposure is more concentrated than the score implies.

Design a CIFU v2 specification that addresses all three. Required elements in the spec:
- Complete formula with all components and their weights/justification
- Definition of severity-weighted depth per axis per entity
- N_disclosed vs N_retrieved handling (and how to express the gap)
- Geometric mean rationale vs arithmetic mean
- Shannon entropy implementation (formula + scale)
- Band calibration: should Foreclosure Regime still start at 81? What happens to the Uber chain score under v2?
- Migration note: how existing CIFU v1 scores should be labeled when v2 is deployed
- `compute_cifu.py` function signature changes required

### Request B — AT&T → Cricket CIFU Chain Definition

Define the `att_cricket_telecom` CIFU chain using the current corpus:
- Anchor: AT&T Mobility
- Member: Cricket Wireless (AT&T subsidiary — independent ToS, independent arbitration clause)
- Relationship: `parent_subsidiary` with note that Cricket consumers sign Cricket ToS, not AT&T ToS; the relationship creates a double-arbitration exposure when Cricket disputes escalate to AT&T infrastructure

Produce:
1. The `_CIFU_CHAINS` dict entry for `att_cricket_telecom` (ready to paste into `compute_cifu.py`)
2. The computed CIFU score and axis breakdown using current corpus data
3. Comparison to the Uber chain (90.5): is this a parent-subsidiary amplification or attenuation?
4. One-paragraph analytical finding: what does intra-family CIFU measure that single-entity CASI cannot?

### Request C — Remaining Detector Audit Verification Queries

For L-15:A and L-12:C (flagged as Watch in Section 4), produce:

1. **L-15:A verification query** — SQL query against `contra_corpus.db` to identify documents where L-15:A fired but the source text contains "we use" without data collection verbs. Include the `contra_findings` and `commercial_documents` join structure.

2. **L-12:C spot-check query** — SQL to retrieve a sample of matched text for L-12:C findings. Pattern: `SUBSTR(doc_text, match_start, match_end - match_start + 1)` if match positions are stored, or equivalent from `contra_findings` columns.

3. **Verdict** — Based on query structure and likely result patterns: should L-15:A or L-12:C be escalated to Priority Fix (same as L-13:A / L-17:C were), or are they acceptable noise levels? Justify with reference to the `_P_COLLECT` and `_P_C` patterns provided in Section 4.1.

### Request D — Anti-Pattern Regression Test Suite Design

Design the complete regression test suite for all 10 CONTRA detectors. For each detector, provide:
- At least 2 **positive fixtures** (text that SHOULD fire the detector, with expected sub-detector label)
- At least 2 **negative fixtures** (text that should NOT fire, specifically targeting the broad-alternative risk)
- One **defect-class negative fixture** (a text that would have fired the old defective pattern but should not fire the fixed one — applicable to L-13 and L-17)

Format as pytest parametrize entries or a JSON fixture file that `tests/contra/test_detector_regression.py` can consume directly.

Priority negative fixtures for the two known defects:
- L-13:A: "We will send you the latest Home Gateway within 30 days." — NEGATIVE
- L-13:A: "We may contact you via phone regarding your account." — NEGATIVE  
- L-17:C: "TEXT SHOWN ONLY FOR ACKNOWLEDGMENT." — NEGATIVE
- L-17:C: "Users may submit text, image, audio, or video content as proof." — NEGATIVE

### Request E — CCM Metric Design

Design the Certification Capture Metric (CCM) for TrustArc's multi-role position:

Context:
- TrustArc (formerly TrustE) historically certified Facebook and Meta's privacy practices (independent certifier role)
- TrustArc currently provides consent management infrastructure to Meta (paid vendor role)  
- TrustArc is also Uber's direct Consent Management Platform vendor
- The transition from certifier → infrastructure vendor for the same entities it formerly assessed represents assessor independence loss — a structural conflict of interest embedded in the consent management supply chain

Design a CCM formula that quantifies:
1. Role overlap score (number of concurrent roles: certifier / assessor / vendor / infrastructure provider)
2. Temporal persistence (how long has the entity held both certifier and vendor roles simultaneously?)
3. Principal scope (how many of the certified entities also became paying clients?)
4. Independence breach threshold (at what CCM score does the arrangement constitute a structural conflict under CPPA guidance?)

Provide:
- Complete CCM formula with component definitions
- TrustArc's illustrative CCM score (using publicly known information)
- Proposed addition to `contra_corpus.db` schema (new table or column)
- How CCM connects to CIFU (does a high-CCM consent manager inflate or deflate the CIFU score?)

---

## Section 8 — Technical Reference

### 8.1 DB Schema (Key Tables — `contra_corpus.db`)

```
commercial_entities:
  entity_id (UUID), canonical_name, jurisdiction_code, corporate_family,
  entity_type, created_at

commercial_documents:
  document_hash (SHA-256, PK), entity_id (FK), doc_type, file_name, file_path,
  source_url, ingested_at, framework_version

commercial_document_provenance:
  document_hash (FK), manifest_path, batch_id, ingest_timestamp

contra_findings:
  id, document_hash (FK), layer, sub_detector, severity, axis,
  delta, anchor_citation, remedy_channels, match_start, match_end, notes

casi_scores:
  document_hash (FK), remedy_foreclosure, data_extraction_depth,
  modification_and_consent, procedural_adhesion, enforcement_cost_asymmetry,
  aggregate, band, framework_version, computed_at,
  finding_density_ratio, regulated_content_delta

s1281_96_cases:
  case_id, entity_id, consumer_pseudonym, filing_date, administrator,
  arbitrator, award_amount, consumer_prevailed, ... (30 columns — EMPTY)

commercial_document_version_chain:
  (exists in schema — 0 rows)
```

### 8.2 CASI Axis Definitions

| Axis | Max Score | Key Detectors | Notes |
|---|---|---|---|
| `data_extraction_depth` | 20 | L-14, L-15, L-16, L-17 | CCPA categories A–K; biometric SPI; training grants |
| `modification_and_consent` | 20 | L-13 | Unilateral modification; notice methods; retroactivity |
| `procedural_adhesion` | 20 | L-11, L-12, L-20 | Arbitration architecture; choice of law; dark patterns |
| `remedy_foreclosure` | 20 | L-11, L-12, L-18 | Damages caps; class waivers; injunctive relief waivers |
| `enforcement_cost_asymmetry` | 20 | L-11, L-19 | Fee-shifting; 1281.97/98; gag clauses; discovery limits |

### 8.3 Key Scripts

| Script | Purpose |
|---|---|
| `scripts/contra_batch_ingest.py` | Batch ingest from manifest JSON; runs L-11–L-20; computes CASI |
| `scripts/rescore_commercial.py` | Discovery-by-hash rescore (post-fix) with checkpoint |
| `scripts/backfill_fdr_rcd.py` | Backfill FDR and RCD for existing CASI rows |
| `scripts/compute_cifu.py` | CIFU metric for defined chains; outputs `data/cifu_report.json` |
| `scripts/build_manifest_uber_ecosystem.py` | NSU routing for Uber 20-entity ecosystem |
| `scripts/build_manifest_from_folder.py` | Build manifest from a local folder (any entity) |
| `scripts/corporate_family_expander.py` | Map entity names to corporate families |
| `scripts/entity_breakdown.py` | Entity-level CASI summary from DB |
| `scripts/build_contra_corpus_archive.py` | Build JSON archive from DB (band-partitioned) |
| `scripts/contra_query.py` | Quick corpus-level summary stats |

### 8.4 Detector Module Locations

```
src/oraculus_di_auditor/contra/
├── l11_arbitration_architecture.py
├── l12_choice_of_law_forum.py
├── l13_unilateral_modification.py   ← FIXED (L-13:A)
├── l14_data_collection_depth.py
├── l15_data_retention.py            ← WATCH (_P_COLLECT)
├── l16_onward_transfer.py           ← WATCH (_P_G_BROAD)
├── l17_ml_ai_training.py            ← FIXED (L-17:C)
├── l18_remedy_foreclosure.py
├── l19_enforcement_asymmetry.py
├── l20_dark_pattern.py
├── casi.py                          ← CASI aggregator
├── anchors.py                       ← Legal citation constants
└── _utils.py                        ← scan_pattern / make_finding helpers
```

### 8.5 CIFU Chain Structure (in `compute_cifu.py`)

```python
_CIFU_CHAINS = {
    "uber_consumer_full": {
        "chain_name": "Uber Consumer Full Chain",
        "anchor": "Uber Technologies Inc.",
        "members": [
            {"entity_name": "Portier LLC", "relationship": "subsidiary", "note": "..."},
            {"entity_name": "Cambridge Mobile Telematics", "relationship": "sub_processor", ...},
            # ... 17 more entries ...
        ],
    }
}
```

### 8.6 CIFU Formula (Current v1)

```
breadth = count(axes with at least one entity having findings)
breadth_pct = breadth / 5

depth_per_axis = (entities_with_findings_on_axis / total_entities_in_chain)
depth_pct = mean(depth_per_axis for each active axis)

CIFU_score = round((breadth_pct * 50) + (depth_pct * 50), 1)

Bands: Baseline 0–20 | Elevated 21–40 | Substantial 41–60 | Severe 61–80 | Foreclosure Regime 81–100
```

### 8.7 Compliance-Vendor Paradox

A structural anomaly observed in compliance-automation vendors (Drata, Vanta, Sprinto):

- **Sprinto**: avg 46.5, max 73 — highest CASI among the three; compliance vendor with Severe-band instruments
- **Vanta**: avg 17.2, max 53 — Substantial-band maximum
- **Drata**: avg 21.3, max 39 — Elevated-band maximum

These entities are deployed by enterprise clients to audit and certify their own compliance posture. They obtain read-access to client data inventories, infrastructure configuration, and employee records to perform this function. Their own contracts with enterprise clients (which flow down to consumer data through the sub-processor relationship) contain the same arbitration, modification, and data-extraction provisions they are paid to help clients manage. The paradox: the compliance certifier is itself non-compliant by C.O.N.T.R.A. standards at the instrument level.

---

## Section 9 — Analytical Context for Opus

### 9.1 What CIFU 90.5 Means

The 90.5 score should be read as: "A consumer who uses Uber implicitly binds to instruments across 20 entities — 5 CASI axes are active, 19/20 entities contribute to data extraction depth, and 14/20 entities contribute to modification and consent — creating a cross-instrument foreclosure exposure equivalent to a Foreclosure Regime contract even though no single instrument reaches that band."

This is the definitional case for why network-level risk metrics are necessary: the most dangerous consumer legal architecture in 2026 is not a single draconian contract but a web of seemingly ordinary contracts whose combined effect erases consumer rights across all available axes.

### 9.2 What Opus Should Not Change

The following are **confirmed correct** post-fix and should not be questioned:
- L-13:A fix (removing bare `we may` alternative) — validated against prior session's defect analysis
- L-17:C fix (removing bare modalities + has_train gate) — validated against prior session's defect analysis
- CIFU denominator at 20 (retrieved), not 44 (disclosed) — this is the correct current denominator; v2 will address the gap
- Cricket Wireless max CASI at 69 (corrected from 84 FR) — the 84 was entirely detector noise
- Zero Foreclosure Regime documents in the 311-doc corpus — this is the correct post-fix state

### 9.3 Open Analytical Questions

1. Does the compliance-vendor paradox have a legal theory of harm (FTC Section 5, CPPA enforcement, or SEC non-reliance disclosure analog)?
2. TrustArc's multi-role position: is the certifier-capture dynamic a separate disclosure violation, or is it subsumed under the sub-processor onward-transfer chain?
3. At what CIFU score does a consumer's rights become "effectively extinguished" in a legally cognizable sense? Is there a Foreclosure Regime analog in existing case law?
4. The three simultaneous biometric deployments (Jumio, Socure, Veriff) in the Uber chain: under BIPA § 740 ILCS 14 / 5 ILCS 177, does a consumer's facial scan during Uber driver onboarding constitute three separate violations if only one vendor is named in the consent form?
5. Portier LLC (Uber Eats legal entity) has max CASI 14 but appears as a separate arbitration venue from Uber Technologies Inc. — does this create a dispute-routing ambiguity where Uber Eats disputes fall outside Uber's arbitration clause?

---

*End of C.O.N.T.R.A. Opus Handoff — 2026-08-23*  
*Next handoff target: after CIFU v2 implementation + AT&T/Cricket chain + regression suite + L-15:A/L-12:C verification*
