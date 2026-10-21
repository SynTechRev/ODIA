# ODIA / C.O.N.T.R.A. Opus Handoff — 2026-10-01

**Supersedes**: CONTRA_OPUS_HANDOFF_2026-08-23.md  
**Prepared by**: MARS (SynTechRev) via Claude Code (Sonnet 4.6)  
**Session scope**: CIFU v2 implementation, gig economy corpus expansion (DoorDash + Instacart), Uber entity deduplication, training dataset expansion to 6,672 examples across 6 types, odia_legal Phase 1 foundation (CPRACorpusLoader + CalCitation parser + LegalResolver integration)  
**Framework version**: C.O.N.T.R.A. V1.0 / CASI v1.1 / CIFU v2.0  
**Chains at handoff**: **8 chains — all Foreclosure Regime**  
**Training dataset**: 6,672 examples (`data/contra_training_v1.jsonl`, 11.6 MB)  
**Test suite**: 4,378 passed / 15 skipped / 0 failures  
**ODIA DB**: 50,699 documents / 148,349 findings (16 jurisdictions — unchanged)

---

## Section 1 — What Happened Since Last Handoff (2026-08-23)

### 1.1 CIFU v2 Implementation

The CIFU v2 formula was implemented in response to Opus's specification from the prior session. CIFU v1 used binary entity presence (entity either has findings on an axis or doesn't). CIFU v2 adds a severity-weighted correction.

**Formula:**
```
cifu_v1 = round((breadth_pct × 50) + (depth_pct × 50), 1)
cifu_v2 = min(100, cifu_v1 + 10 × mean_sev_ratio)

where:
  mean_sev_ratio = mean((critical_count + 0.6 × high_count) / total_findings)
  computed per entity across the chain
```

Both v1 and v2 scores are now emitted by `scripts/compute_cifu.py` for all chains. The v2 score is in `data/cifu_report.json` as `cifu_v2_score`.

**Current chain table (all Foreclosure Regime):**

| Chain | CIFU v1 | CIFU v2 | N Entities | Docs |
|---|---|---|---|---|
| AT&T / Cricket Wireless | 100.0 | 100.0 | 2 | 86 |
| Telecom Carrier Full | 97.5 | 99.6 | 4 | 150 |
| **Gig Economy Competitive** | **97.1** | **100.0** | **7** | **131** |
| Uber Worker Full | 94.6 | 98.4 | 13 | 108 |
| Uber Consumer Full | 92.4 | 95.9 | 21 | 620 |
| Behavioral Advertising Surveillance | 90.0 | 93.5 | 12 | 729 |
| Financial Instrument Worker Payment | 90.0 | 92.7 | 5 | 55 |
| Identity Resolution & Data Broker | 85.0 | 88.6 | 10 | 305 |

The Gig Economy chain is now the joint #1 chain by CIFU v2 (tied with AT&T at ceiling 100.0) and #3 by v1. Every axis at 100% entity saturation on DED/MC/PA across all 7 platforms.

### 1.2 Gig Economy Corpus Expansion — DoorDash and Instacart

Two new entities added to the Gig Economy Competitive chain, completing its 7-platform structure.

**DoorDash Inc. — 3 documents ingested:**
- `doordash_terms_2026-09-30.txt` — CASI **82** (Foreclosure Regime). Main ToS. Full 5-axis activation. DED/MC/PA/RF/ECA all present.
- `doordash_privacy_2026-09-30.txt` — CASI **26** (Elevated). Privacy policy only.
- Combined: avg CASI 44.7 (Substantial band)

**Maplebear Inc. (Instacart) — 2 documents ingested:**
- `instacart_terms_2026-09-30.txt` — CASI **77** (Severe). ToS with full arbitration architecture.
- `instacart_privacy_2026-09-30.txt` — CASI **24** (Elevated). Privacy policy only.
- Combined: avg CASI 50.5 (Substantial band)

**Targeted harvest tool created** — `scripts/contra_targeted_harvest.py`:
- Fetches known canonical URLs directly (no CDX/Wayback needed for primary documents)
- HTML→txt via BeautifulSoup, minimum 500-char gate rejects shell-only pages
- Wrote `data/manifests/gig_targeted_2026-09-30.json` (3 entries after cleaning 6 failed JS-rendered help articles)
- Note: help.doordash.com articles are Salesforce Experience Cloud — JS-rendered, BeautifulSoup returns only ~936 chars of navigation shell; confirmed useless and purged

### 1.3 Uber Entity Deduplication

Two `commercial_entities` records existed for Uber: `"contra:uber_technologies_inc."` (with period, 8 docs at time of fix) and `"contra:uber_technologies_inc"` (no period, 4 docs). These were two separate DB rows for the same entity due to manifest inconsistency.

**Fix applied** — `scripts/fix_uber_entity_merge.py`:
- Migrated all 4 documents from the no-period ID to the canonical with-period ID
- Registered `"Uber Technologies Inc"` (no period) as alias in `commercial_entity_aliases`
- Deleted the duplicate entity record
- Result: **12 Uber Technologies Inc. documents** unified under canonical ID
- Worker chain anchor in `compute_cifu.py` also corrected from `"Uber Technologies Inc"` → `"Uber Technologies Inc."` to prevent future mis-resolution (worker chain CIFU corrected: 90.8 → **94.6/98.4**)

### 1.4 Training Dataset Expansion — 6 Types, 6,672 Examples

Training dataset grew from 3,538 to **6,672 examples** (`data/contra_training_v1.jsonl`, 11.6 MB).

**Six training types:**

| Type | Description | Count |
|---|---|---|
| 1 | Finding Explanation — excerpt → legal analysis | ~2,000 |
| 2 | Axis Classification — clause → axis + severity label | ~1,500 |
| 3 | Entity Audit — entity → full CASI axis profile | ~30 |
| 4 | Chain Audit — chain → CIFU analysis narrative | 8 |
| 5 | Doctrine Application — anchor ID → statutory text + analysis | 21 |
| 6 | Cross-Chain Comparison — chain pair → comparative analysis | 12 |

**Type 5 — Doctrine Application** is notable: it uses the live CPRACorpusLoader (see Section 1.5) to embed real CPRA/CCPA statutory text directly in each example. When the anchor is e.g. `CCPA_121`, the training prompt includes the full text of Cal. Civ. Code § 1798.121. This makes odia-v2 capable of reasoning from first-principles statute text, not just pattern-match from labeled corpora.

**Type 6 — Cross-Chain Comparison** produces pairwise comparisons of the top 4 chains versus all remaining chains (up to 12 pairs). Each example includes CIFU v1/v2, axis breakdown, entity count, and an analytical narrative explaining what structural differences drive score divergence.

### 1.5 odia_legal Phase 1 Foundation

Three new source files and two modified files implementing the California statutory citation infrastructure for the L-detectors.

**New files:**

1. **`src/oraculus_di_auditor/legal/cpra_corpus.py`** — `CPRACorpusLoader`
   - Implements `CorpusLoader` interface; no external submodule required (embedded corpus)
   - 13 embedded CPRA/CCPA provisions: `1798.100`, `1798.110`, `1798.115`, `1798.120`, `1798.121`, `1798.125`, `1798.135`, `1798.150`, `CCP_1281.97`, `CCP_1281.98`, `CCP_1670.5`, `Lab_2699`, `GovCode_12953`
   - Resolves by: CONTRA anchor ID (`CCPA_121` → section `1798.121`), formal citation (`Cal. Civ. Code § 1798.121`), bare section (`§ 1798.120`)
   - 19/19 tests passing (`tests/legal/test_cpra_corpus.py`)

2. **`src/oraculus_di_auditor/legal/statute_citation.py`** (extended)
   - Added `CalCitation` dataclass: `code`, `section`, `subsection_path`, `raw`, `canonical`
   - `cpra_loader_key` property: maps `CalCitation` to `CPRACorpusLoader._PROVISIONS` key
   - Added `parse_cal_citations(text)` and `parse_cal_single(text)` functions
   - Handles: `Cal. Civ. Code § 1798.121(a)`, `CCP § 1281.97`, `§ 1798.121`, `Labor Code § 2699(f)`, etc.
   - 18/18 tests passing (`tests/legal/test_cal_citation_parser.py`)

3. **`config/legal_corpora.yml`** (extended)
   - Added CPRA corpus entry: `id: cpra`, `submodule_path: null`, citation patterns for `§ 1798.*`, `CCPA`, `CPRA`, `CCP §`, `Lab. Code §`
   - `LegalResolver` now loads 4 corpora at startup: us-code, cal_codes, cpra, cfr

**Modified files:**

4. **`src/oraculus_di_auditor/legal/legal_resolver.py`** — Fixed `_instantiate_loader` to handle `submodule_path: null` in YAML (previously raised `TypeError: Path(None)`)

5. **`src/oraculus_di_auditor/contra/_utils.py`** — Added `extract_cal_citations(text)` helper enabling L-detectors to surface California citations found embedded in scanned contract text

### 1.6 Bug Fixes

| Fix | File | Description |
|---|---|---|
| `fdr = None` when agg=0 | `ingest/commercial.py:218` | Zero-aggregate documents now get `fdr = 0.0`, not NULL |
| L-17:C test text | `tests/contra/test_detectors_l16_l20.py` | `test_l17c_broad_modality_scope` updated to include explicit ML training context (the `has_train` gate is intentional — the test was wrong, not the gate) |
| LegalResolver null path | `legal/legal_resolver.py` | `_instantiate_loader` now handles `submodule_path: null` before calling `Path()` |
| Worker chain anchor period | `scripts/compute_cifu.py` | Worker chain anchor corrected from `"Uber Technologies Inc"` to `"Uber Technologies Inc."` |

---

## Section 2 — Platform State at Handoff

| Component | State |
|---|---|
| ODIA platform version | 3.9.2 (master branch) |
| CONTRA framework version | V1.0 / CASI v1.1 / CIFU v2.0 |
| DB | `D:\CONTRA Contract Corpus\contra_corpus.db` |
| Total chains | **8** (all Foreclosure Regime) |
| Gig economy chain | **7 entities / 131 docs / CIFU 97.1 v1 / 100.0 v2** |
| Uber Consumer Full | 21 entities / 620 docs / CIFU 92.4 v1 / 95.9 v2 |
| Training dataset | 6,672 examples in `data/contra_training_v1.jsonl` (11.6 MB) |
| odia_legal Phase 1 | Foundation complete — CPRACorpusLoader + CalCitation parser live |
| Test suite | **4,378 passed / 15 skipped / 0 failures** (488s) |
| ODIA DB | 50,699 docs / 148,349 findings / 16 jurisdictions (unchanged) |
| odia-v1 | LIVE — Ollama, default RAG LLM |
| odia-v2 dataset | Active development — not yet trained |
| `s1281_96_cases` rows | 0 (still empty — §1281.96 pipeline not yet wired) |
| Dasher/driver agreements | Not yet ingested — JS-rendered, require alternate approach |
| City of Fresno Legistar | NOT YET INGESTED (P0 — blocked on prior work) |

---

## Section 3 — Gig Economy Chain Analysis

### 3.1 Chain Entity Breakdown

| Entity | Docs | Avg CASI | Max CASI | Band | Axes Active | Role |
|---|---|---|---|---|---|---|
| Lyft Inc. | 49 | 24.8 | 88 | Severe | 5/5 | Anchor |
| DoorDash Inc. | 3 | 44.7 | 82 | Severe | 5/5 (ToS doc) | Competitive peer |
| Maplebear Inc. (Instacart) | 2 | 50.5 | 77 | Severe | 5/5 (ToS doc) | Competitive peer |
| Grubhub Holdings LLC | 6 | ~35 | 66 | Severe | 5/5 | Competitive peer |
| Uber Technologies Inc. | 12 | 44.1 | 71 | Severe | 5/5 | Competitive peer |
| Plaid Inc. | 3+ | — | — | — | 3/5 | Payment sub-processor |
| Jumio Inc. | 10 | 32.6 | 60 | Substantial | 5/5 | Biometric sub-processor |

### 3.2 Structural Finding: Multi-App Foreclosure

A gig worker who multi-apps across Lyft + DoorDash + Instacart + Grubhub + Uber is simultaneously bound to five independently structured arbitration agreements — each requiring individual arbitration, naming AAA or JAMS, with shortened statutes of limitations, and each containing DED/MC/PA/RF/ECA axis activations. There is no cross-platform opt-out mechanism. The platforms share sub-processors (Plaid for payments, Jumio/similar for biometric onboarding) that appear in multiple chains simultaneously.

This is distinct from the Uber Consumer Full chain (which models a consumer bound to Uber's full vendor ecosystem). The Gig Economy chain models competitive market foreclosure: the instruments are not from one ecosystem but from competitors, yet they are structurally identical in their rights-foreclosure architecture. This is the strongest evidence in the corpus for coordination thesis vs. independent convergence.

### 3.3 Known Chain Gaps

| Missing Item | Blocking Reason | Priority |
|---|---|---|
| Dasher agreement (DoorDash worker) | Salesforce Experience Cloud — JS-rendered | P1 |
| Lyft driver agreement | Lyft serves driver docs via JS-gated portal | P1 |
| Instacart Shopper Terms | 404 at instacart.com/shopper-terms | P1 |
| Uber Eats / Postmates worker terms | Overlap with Uber Worker chain | P2 |

DoorDash currently has 3 consumer docs but no Dasher-specific agreement. Until Dasher agreement is ingested, the "worker chain" sub-component of gig economy is undercounted — consumer CASI 82 may not reflect the full worker exposure.

---

## Section 4 — odia_legal Phase 1: State and Remaining Work

### 4.1 What Is Built

The Phase 1 objective is a citation infrastructure layer that:
1. Resolves CONTRA doctrinal anchor IDs (e.g. `CCPA_121`) to full statutory text
2. Parses California statutory citations embedded in scanned contract text
3. Routes those citations to the correct corpus loader for full-text retrieval

All three are now functional. The integration point between the CONTRA L-detectors and the legal corpus layer is `extract_cal_citations()` in `contra/_utils.py`, and the Type 5 training examples demonstrate the pattern: anchor → live statute text → analysis.

**ANCHOR_TO_SECTION mapping (current):**

| CONTRA Anchor | Cal. Code Section | Provision |
|---|---|---|
| `CCPA_121` | `1798.121` | Right to opt out of sale of sensitive PI |
| `CCP_1281_97` | `CCP_1281.97` | Arbitration — company failure to pay fees |
| `CCP_1281_98` | `CCP_1281.98` | Arbitration — material breach |
| `CAL_LABOR_2699` | `Lab_2699` | PAGA — civil penalties |
| `AB_51` | `GovCode_12953` | Prohibition on mandatory arbitration as condition of employment |
| `CCPA_100` | `1798.100` | Right to know / access |
| `CCPA_110` | `1798.110` | Right to know categories |
| `CCPA_120` | `1798.120` | Right to opt out |
| `CCPA_125` | `1798.125` | Right to non-discrimination |
| `CCPA_135` | `1798.135` | Privacy notice requirements |

### 4.2 Remaining Phase 1 Work

**L-9 recodification** — The existing L-9 detector uses informal anchor strings. These need updating to use `CalCitation`-compatible keys so `extract_cal_citations()` and `CPRACorpusLoader.resolve_anchor()` can route them. This is a mechanical sweep of `anchors.py` — no logic changes, only key format updates.

**CPRA crosswalk auto-enrichment** — When a CONTRA finding has a `doctrinal_anchor` (e.g. `CCPA_121`), the system should automatically resolve that anchor via `CPRACorpusLoader.resolve_anchor()` and embed the statutory text in the finding's `notes` field at ingest time. Integration point: `make_finding()` in `contra/_utils.py` or the CASI batch loop in `ingest/commercial.py`. This would make every finding self-documenting and significantly improve Type 1/Type 5 training quality. The `CPRACorpusLoader.resolve_anchor()` method is already live and tested — the integration is a ~10-line addition.

**L-detectors → statute citation extraction** — After ingesting a document, `extract_cal_citations(text)` should be called and the results stored (probably as a JSONB column or separate table in `contra_corpus.db`). This surfaces clauses where the company itself cites the statute it is waiving, which is a distinct and analytically important finding class.

---

## Section 5 — Pending Work (Priority Order)

### P0 — ODIA Main Corpus

1. **City of Fresno NSU ingest** — Delete `cache\fresno_legistar\progress.json`, then:
   ```
   python scripts/ingest_legistar.py --client fresno
   ```
   City of Fresno Legistar is **not yet in the corpus at all** (0 documents). Confirmed artifacts include a $1.5M Flock Safety contract, TASER sole-source, JAG grant instruments. This is a known P0 gap since v3.9.2.

2. **Fresno MAS V2.0 via Opus** — After city ingest is complete. MAS V1.0 was Fresno County only; V2.0 should incorporate City of Fresno data and update the cross-jurisdiction Flock lattice analysis.

3. **TCPD Questys harvest** — TCPD operational presence is confirmed (April 29, 2026 SEU field action) but absent from all 161 current TCPD corpus documents. Questys system holds the records.
   ```
   python scripts/ingest_tcpd.py --dry-run
   python scripts/ingest_tcpd.py
   ```

### P1 — CONTRA Corpus

4. **Gig worker agreements** — Dasher, Lyft driver, Instacart shopper agreements. All three are JS-rendered or portal-gated. Approaches:
   - Wayback Machine CDX snapshots: `python scripts/wayback_backfill.py --entity doordash --doc-type dasher_agreement`
   - Direct PDF download: Some platforms provide PDF copies on request pages that bypass JS rendering
   - Manual download from authenticated portal session

5. **§1281.96 arbitration data pipeline** — `s1281_96_cases` table still has 0 rows. `D:\CONTRA Contract Corpus\AAA\` is still empty. Without real arbitration award data, `enforcement_cost_asymmetry` is theoretically capped at ~80 per instrument. The practical CASI ceiling will remain below Foreclosure Regime for individual instruments until this data is populated. Potential source: AAA case search, JAMS case registry, or court filing scrapers for California arbitration motions filed under CCP § 1281.97/98.

6. **CPRA letters** — Target entities: Fresno County Sheriff, BOS Clerk, IT/CEO; City of Fresno/FPD. These are CPRA requests for records pertaining to surveillance technology contracts, not legal filings.

### P1 — odia_legal

7. **CPRA crosswalk auto-enrichment** — Integration of `CPRACorpusLoader.resolve_anchor()` into the finding creation pipeline. See Section 4.2. This is a ~10-line change with high training data quality impact.

8. **L-9 recodification** — Update `anchors.py` doctrinal anchor keys to `CalCitation`-compatible format. Mechanical sweep; no logic changes.

### P2 — Training Pipeline

9. **odia-v2 training** — The dataset is at 6,672 examples. The original odia-v1 trained on 87,618 examples. For odia-v2 to be a meaningful upgrade, the target is at least 20,000 CONTRA examples + TCPD data + Fresno city ingest. Current bottleneck: training data is blocked on (a) TCPD ingest, (b) City of Fresno ingest, (c) §1281.96 pipeline for enforcement asymmetry examples.

10. **Type 7: Legal Citation Annotation** — Once CPRA crosswalk is live, a new training type is available: given a finding's `notes` field (which will contain the resolved statute text), produce an annotation explaining why the contract clause is in tension with that specific statutory provision. This is the highest-value training type for legal reasoning capability.

### P3 — Infrastructure

11. **Flock Safety cross-jurisdiction lattice** — VPD has 75 Flock detections vs Fresno County's 1 (hex-named PDF). This asymmetry is analytically significant and needs a JIM collection document explaining the cross-jurisdiction interoperability implications. Write to `jim_collection`.

12. **Multi-index RAG routing** — `ace_collection` and `jim_collection` are built but not exposed via `corpus_filter` in the API. Documents like the Flock lattice analysis are in JIM but unreachable via the frontend query interface.

---

## Section 6 — Files to Upload to Opus Project Folder

| File | Location | Purpose |
|---|---|---|
| This handoff | `data/handoffs/ODIA_OPUS_HANDOFF_2026-10-01.md` | Primary briefing |
| CIFU report (gig chain) | `data/cifu_report.json` | Gig Economy chain — current last-computed chain |
| Gap report | `data/gap_report_2026-09-30.json` | Uber Consumer Full axis coverage and gap analysis |
| Chain comparison | `data/chain_comparison.json` | All 8 chains side by side |
| Training dataset stats | Run: `python scripts/contra_training_exporter.py --stats` | Current example counts by type |
| CPRACorpusLoader source | `src/oraculus_di_auditor/legal/cpra_corpus.py` | For Request B analysis |
| CalCitation parser source | `src/oraculus_di_auditor/legal/statute_citation.py` | For Request B analysis |
| CONTRA detectors directory | `src/oraculus_di_auditor/contra/` (all l1x_ files) | For Request C detector audit |
| Legal corpora config | `config/legal_corpora.yml` | For Request B integration review |
| Previous handoff | `data/handoffs/CONTRA_OPUS_HANDOFF_2026-08-23.md` | Historical context — Opus's prior assessment and CIFU v2 spec |

---

## Section 7 — Requests for Opus This Session

### Request A — Overall Project Velocity Assessment

Provide an honest assessment of odia-v2 readiness given the current state:

1. **Training data adequacy**: Is 6,672 examples sufficient for a meaningful odia-v2 fine-tune, or is the corpus too small? The 6 training types cover finding explanation, axis classification, entity audit, chain audit, doctrine application, and cross-chain comparison. What training types are missing for the model to develop genuine commercial contract legal reasoning?

2. **Coverage gaps**: The current CONTRA corpus focuses heavily on gig economy and Uber ecosystem. What sectors are absent that would materially improve odia-v2's generalization? Candidates: healthcare (HIPAA BAAs), financial (TILA/EFTA), telecom (CPNI), employment (NLRA), housing (FCRA).

3. **odia_legal Phase 1 completeness**: The CPRACorpusLoader has 13 provisions embedded. Is this sufficient for the L-detectors' doctrinal anchors, or are there anchor IDs being fired without a corresponding provision? Recommend running `grep -rn "doctrinal_anchor" src/oraculus_di_auditor/contra/` and cross-referencing against `_ANCHOR_TO_SECTION` in `cpra_corpus.py`.

4. **Critical path to first odia-v2 training run**: Given current blockers, what is the minimum viable dataset state to justify a fine-tuning run? Is there value in a partial odia-v2 run now (6,672 examples) vs. waiting for TCPD + Fresno city ingest?

### Request B — CPRA Crosswalk Integration Design

Design the full implementation for CPRA crosswalk auto-enrichment — the integration that embeds resolved statutory text directly into CONTRA findings at ingest time.

Context:
- `CPRACorpusLoader.resolve_anchor(anchor_id)` is live and returns a `LegalText` object with `.title`, `.text`, `.citation`
- `make_finding()` in `contra/_utils.py` accepts a `notes: str | None` parameter
- The batch ingest pipeline runs in `src/oraculus_di_auditor/ingest/commercial.py`
- L-detector `scan_pattern()` calls `make_finding()` internally for each match

Produce:
1. The exact code change to `make_finding()` or the batch ingest pipeline to auto-resolve `anchor` → `notes` when `notes` is None and `anchor` has a CPRACorpusLoader mapping
2. How to handle the case where `CPRACorpusLoader` is not initialized (graceful fallback — don't block ingest on legal corpus availability)
3. Whether the statute text excerpt should be stored in `notes` (VARCHAR in DB) or a separate `doctrinal_text` column (would require a schema migration)
4. The Type 7 training prompt format: given a finding enriched with statutory text, what instruction/response structure produces the highest-value legal reasoning training example?

### Request C — Gig Economy Chain: Coordination Thesis Evaluation

The gig economy chain's CIFU 97.1/100.0 arises from 7 independent companies deploying structurally identical arbitration architectures. Evaluate whether this represents:

**(A) Independent convergence** — Each platform independently arrived at the same optimal risk-allocation structure under California/federal arbitration law, driven by cost minimization and precedent (AT&T Mobility LLC v. Concepcion, 2011; Epic Systems Corp. v. Lewis, 2018).

**(B) Coordination** — The structural identity across platforms (same venues AAA/JAMS, same modality-strip in L-17, same SOL truncation in L-12) suggests either template adoption (platforms using the same legal vendors) or explicit coordination.

**(C) Structural inevitability** — Under current US arbitration law, any company operating at gig economy scale with consumer/worker contracts faces a legal architecture funnel. The same law that permits these clauses also narrows the design space to near-identical structures.

Provide:
1. A framework for distinguishing A/B/C using only the instrument text (no external evidence of coordination needed)
2. Which specific L-detector sub-detectors would produce different scores under A vs. B (e.g., if arbitration clause language is copy-pasted, L-11:G's `_P_TEMPLATE_MARKER` should fire; if independently drafted, it may not)
3. What additional corpus documents would allow ODIA to definitively distinguish A from B (suggested: legal vendor disclosure sections in each platform's ToS, attorney fee disclosures in arbitration clauses, AAA/JAMS case number formats)
4. Whether "structural inevitability" (C) has legal relevance — does a court or regulator view identical consumer harm differently when it arises from industry convergence vs. coordination?

### Request D — §1281.96 Pipeline Architecture

Design the full data pipeline for ingesting California arbitration award data into `s1281_96_cases`. This table has 0 rows and a 30-column schema. Until it is populated, `enforcement_cost_asymmetry` is theoretically starved — no individual instrument can reach Foreclosure Regime.

Context:
- California SB 762 (2021) and AB 1286 (2022) require AAA and JAMS to publish consumer and employment arbitration case statistics
- AAA Consumer Case Filings are published quarterly at adr.org
- JAMS publishes annual employment/consumer case statistics
- CCP § 1281.96(a) requires businesses to publish arbitration results on their websites when they are the drafting party

Produce:
1. Data source mapping: for each of the 7 gig economy entities + 21 Uber Consumer chain entities, where is §1281.96 disclosure data available (company website, AAA, JAMS, or court docket)?
2. Ingestion script architecture for `scripts/ingest_s128196_cases.py` — schema mapping from AAA/JAMS published format to `s1281_96_cases` 30-column schema
3. How to connect `s1281_96_cases` data back to CIFU: should enforcement cost asymmetry depth increase when a chain entity has a high ratio of consumer losses in published arbitration results?
4. First target entity for a pilot ingest (recommendation: Uber Technologies Inc., which publishes §1281.96 disclosures annually on their legal page)

### Request E — odia-v2 Training Type Design: Types 7–10

The current 6 training types cover the detection and classification layer. Types 7–10 should advance the model toward legal reasoning and consumer-rights analysis. Propose 4 additional training types, each with:
- Type ID and name
- Input prompt structure
- Expected output structure
- Data source (which CONTRA tables and fields provide the training examples)
- Estimated example count achievable from current corpus

Constraints:
- Type 7 should use the CPRA crosswalk enrichment (statutory text embedded in finding) — this is the highest priority capability gap
- At least one type should involve multi-document analysis (reasoning across multiple instruments for the same entity)
- At least one type should involve temporal reasoning (comparing a 2022 ToS to a 2024 ToS for the same entity using `commercial_document_version_chain`)
- The total new example count from Types 7–10 should be achievable from the current corpus state (~57 entities, ~15,000 findings) without additional ingestion

---

## Section 8 — Technical Reference

### 8.1 Key Files Modified or Created This Session

```
CREATED:
  src/oraculus_di_auditor/legal/cpra_corpus.py       — CPRACorpusLoader (embedded CPRA corpus)
  scripts/fix_uber_entity_merge.py                   — One-time Uber entity deduplication
  scripts/contra_targeted_harvest.py                 — Direct URL harvest, HTML→txt
  tests/legal/test_cpra_corpus.py                    — 19 tests
  tests/legal/test_cal_citation_parser.py            — 18 tests
  data/manifests/gig_targeted_2026-09-30.json        — 3-entry cleaned manifest

MODIFIED:
  src/oraculus_di_auditor/legal/statute_citation.py  — Added CalCitation + parsers
  src/oraculus_di_auditor/legal/legal_resolver.py    — Fixed null submodule_path
  src/oraculus_di_auditor/legal/__init__.py           — Added 4 new exports
  src/oraculus_di_auditor/contra/_utils.py            — Added extract_cal_citations()
  src/oraculus_di_auditor/ingest/commercial.py        — fdr=0.0 fix
  scripts/compute_cifu.py                            — CIFU v2 formula + Uber anchor fix
  scripts/contra_training_exporter.py                — Types 5 + 6 generators + default --types 1,2,3,4,5,6
  config/legal_corpora.yml                           — CPRA corpus entry added
  tests/contra/test_detectors_l16_l20.py             — L-17 test text corrected
```

### 8.2 DB Schema — Key Tables (`contra_corpus.db`)

```sql
commercial_entities:
  entity_id (UUID PK), canonical_name, jurisdiction_code, corporate_family,
  entity_type, created_at

commercial_entity_aliases:
  alias_name, entity_id (FK)  -- canonical_name variants, trade names

commercial_documents:
  document_hash (SHA-256 PK), entity_id (FK), doc_type, file_name, file_path,
  source_url, ingested_at, framework_version

contra_findings:
  id, document_hash (FK), layer, sub_detector, severity, axis, delta,
  anchor_citation, remedy_channels, match_start, match_end, notes

casi_scores:
  document_hash (FK), remedy_foreclosure, data_extraction_depth,
  modification_and_consent, procedural_adhesion, enforcement_cost_asymmetry,
  aggregate, band, framework_version, computed_at,
  finding_density_ratio, regulated_content_delta

s1281_96_cases:
  (30 columns — 0 rows — §1281.96 disclosure data, NOT YET POPULATED)

commercial_document_version_chain:
  (exists — 0 rows — version diffing, NOT YET POPULATED)
```

### 8.3 CASI Axis Definitions

| Axis | Max Score | Key Detectors | Activation Threshold |
|---|---|---|---|
| `data_extraction_depth` (DED) | 20 | L-14, L-15, L-16, L-17 | CCPA cats A–K; biometric SPI; training grants |
| `modification_and_consent` (MC) | 20 | L-13 | Unilateral modification; retroactivity; notice method |
| `procedural_adhesion` (PA) | 20 | L-11, L-12, L-20 | Arbitration architecture; choice of law; dark patterns |
| `remedy_foreclosure` (RF) | 20 | L-11, L-12, L-18 | Damages caps; class waivers; injunctive relief waivers |
| `enforcement_cost_asymmetry` (ECA) | 20 | L-11, L-19 | Fee-shifting; CCP §1281.97/98; gag clauses; discovery limits |

### 8.4 CIFU Formulas (v1 and v2)

```python
# v1
breadth = len([ax for ax in axes if any(e has findings on ax for e in chain)])
depth_pct = mean(entities_with_findings_on_axis / total_entities for active axes)
cifu_v1 = round((breadth / 5 * 50) + (depth_pct * 50), 1)

# v2 (severity-weighted)
mean_sev_ratio = mean(
    (critical_count + 0.6 * high_count) / total_findings
    for each entity in chain
)
cifu_v2 = min(100, round(cifu_v1 + 10 * mean_sev_ratio, 1))

# Bands (same for both)
# Baseline 0–20 | Elevated 21–40 | Substantial 41–60 | Severe 61–80 | Foreclosure Regime 81–100
```

### 8.5 Key Scripts

| Script | Purpose |
|---|---|
| `scripts/contra_batch_ingest.py` | Batch ingest from manifest JSON |
| `scripts/compute_cifu.py` | All-chain CIFU computation (v1 + v2) |
| `scripts/contra_training_exporter.py` | Export training JSONL (types 1–6) |
| `scripts/contra_targeted_harvest.py` | Direct URL harvest, HTML→txt |
| `scripts/fix_uber_entity_merge.py` | One-time entity deduplication (run --dry-run first) |
| `scripts/rescore_commercial.py` | Discovery-by-hash rescore with checkpoint |
| `scripts/contra_query.py` | Corpus-level summary stats |
| `scripts/contra_chain_compare.py` | Multi-chain CIFU comparison table |
| `scripts/contra_corpus_gap.py` | Gap analysis: which entities are missing axis coverage |

### 8.6 Detector Module Map

```
src/oraculus_di_auditor/contra/
├── l11_arbitration_architecture.py   CLEAN
├── l12_choice_of_law_forum.py        WATCH (_P_C "action/suit" broad gap)
├── l13_unilateral_modification.py    FIXED 2026-08-23 (L-13:A)
├── l14_data_collection_depth.py      CLEAN
├── l15_data_retention.py             WATCH (_P_COLLECT "use" alternative)
├── l16_onward_transfer.py            WATCH (_P_G_BROAD no "we" prefix)
├── l17_ml_ai_training.py             FIXED 2026-08-23 (L-17:C) / post-fix L-17:C still #1
├── l18_remedy_foreclosure.py         CLEAN
├── l19_enforcement_asymmetry.py      CLEAN (starved: s1281_96_cases=0 rows)
├── l20_dark_pattern.py               CLEAN (L-20 / L-13 intentional axis overlap)
├── casi.py                           CASI aggregator
├── anchors.py                        Doctrinal anchor constants → needs L-9 recodification
└── _utils.py                         scan_pattern / make_finding / extract_cal_citations
```

### 8.7 odia_legal Legal Corpus Loader Map

```
src/oraculus_di_auditor/legal/
├── corpus_base.py           CorpusLoader ABC + LegalText dataclass
├── cpra_corpus.py           CPRACorpusLoader — 13 provisions, no submodule (COMPLETE)
├── us_code_loader.py        USC loader (submodule-dependent)
├── legal_resolver.py        LegalResolver singleton — routes all resolve() calls
├── statute_citation.py      CalCitation dataclass + parse_cal_citations() (COMPLETE)
├── reference_service.py     Legacy reference lookup (pre-Phase 1)
└── __init__.py              Exports: CPRACorpusLoader, CalCitation, parse_cal_citations, parse_cal_single

config/legal_corpora.yml:
  - id: us-code    (submodule: odia_legal/us_code)
  - id: cal_codes  (submodule: odia_legal/cal_codes)
  - id: cpra       (submodule_path: null — embedded, always available)  ← ADDED THIS SESSION
  - id: cfr        (submodule: odia_legal/cfr)
```

### 8.8 Training Types — Prompt/Response Format

All examples in `contra_training_v1.jsonl` follow the Alpaca/Llama-3 instruction format:

```json
{
  "instruction": "<task description>",
  "input": "<context — excerpt, finding data, chain data>",
  "output": "<expected model response>",
  "type": "type1_finding_explanation | type2_axis_classification | ...",
  "source": "contra_corpus"
}
```

Type 5 (Doctrine Application) includes the full statutory text (up to 1,200 chars) in the `input` field, making the model reason from statute text directly:

```json
{
  "instruction": "Apply California consumer protection law to analyze the following contract clause...",
  "input": "ANCHOR: Right to Opt Out of Sale of Sensitive Personal Information\n\nSTATUTORY TEXT:\nCal. Civ. Code § 1798.121 ...\n\nCONTRACT EXCERPT: ...",
  "output": "This clause implicates Cal. Civ. Code § 1798.121(a)..."
}
```

---

## Section 9 — Analytical Context for Opus

### 9.1 CIFU v2 at 100.0: What the Ceiling Means

The Gig Economy chain and AT&T/Cricket chain both hit CIFU v2 = 100.0. This is the mathematical ceiling of `min(100, cifu_v1 + 10 × mean_sev_ratio)`. It does not mean the analysis is saturated — it means the formula's current severity bonus term is not differentiating enough at the high end.

Before concluding these chains are equivalent, Opus should evaluate whether CIFU v2 needs a differentiation component above 90:
- Concentration term (Shannon entropy) — proposed in the 2026-08-23 Opus session but not yet implemented
- `N_disclosed` denominator — AT&T/Cricket has 2 entities vs. Gig Economy's 7; the formula currently ignores that breadth difference once both reach 5/5 axes
- Inter-instrument dependency density — a single consumer may be bound to both DoorDash and Lyft simultaneously; this is structurally different from AT&T/Cricket where no consumer signs both independently

### 9.2 The §1281.96 Paradox

All 8 chains are Foreclosure Regime by CIFU. But no single instrument reaches Foreclosure Regime individually (highest individual CASI: Lyft at 88, Foreclosure Regime threshold at 81 — so Lyft does reach it, but most don't). The §1281.96 data pipeline, once populated, could push more individual instruments into Foreclosure Regime by activating the `enforcement_cost_asymmetry` axis at its full depth. This matters for the training data: current Type 1/2 examples almost never describe enforcement_cost_asymmetry findings from §1281.96 (because there are none). odia-v2 will be systematically weak on the enforcement cost reasoning pathway.

### 9.3 What Should NOT Change

The following are validated and should not be questioned:
- L-13:A fix (bare `we may` alternative removed) — validated 2026-08-23
- L-17:C fix (bare modalities removed + has_train gate) — validated 2026-08-23; `has_train` gate is correct, L-17:C test was wrong
- CIFU v2 formula — implemented per Opus's 2026-08-23 specification
- Uber entity canonical form: `"Uber Technologies Inc."` (with period) is canonical
- CPRACorpusLoader embedded approach — no submodule required; 13 provisions are sufficient for current anchor set
- Training type formats — do not change prompt/response structure without re-exporting the full dataset

### 9.4 Open Questions for Opus

1. Is the Type 5 training format (statute text in input) the right way to build statutory reasoning capability, or would it be better to train the model to retrieve the statute text via tool use rather than embedding it in every prompt? (Relevant to odia-v2 architecture decision: RAG-augmented vs. fine-tuned memory)

2. The `commercial_document_version_chain` table is empty. Version diffing (comparing a 2022 Uber ToS to a 2024 Uber ToS) could be a high-value training type. Is it worth building the version-chain ingestion infrastructure now, or should CIFU chain expansion come first?

3. DoorDash CASI 82 on the main ToS — this is the first platform-competitive document to reach Foreclosure Regime individually (not just via CIFU). Does this change the analytical conclusion from "CIFU is needed because no single instrument reaches FR" to "competitive market convergence is producing individual Foreclosure Regime instruments"?

4. The training dataset has 8 Type 4 examples (one per chain) and 12 Type 6 examples (pairwise chain comparison). Is this sufficient for the model to learn chain-level analysis, or is this undercounted relative to the ~2,000 Type 1 finding explanation examples?

---

*End of ODIA / C.O.N.T.R.A. Opus Handoff — 2026-10-01*  
*Prior handoff: `data/handoffs/CONTRA_OPUS_HANDOFF_2026-08-23.md`*  
*Next handoff target: after §1281.96 pilot ingest + CPRA crosswalk auto-enrichment + City of Fresno Legistar ingest*
