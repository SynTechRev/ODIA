# Day 05 -- Document AI Bakeoff

**Date**: 2026-10-31
**Branch**: learning/10-day-challenge
**Operator**: M. Sanchez (SynTechRev)
**Status**: COMPLETE

---

## Pre-flight

**Day 4 prerequisite gate verified**: Commit f618f50 ("day04: COMPLETE -- 4/5 verify_passed
with real citations (run 3)") confirms the raia trace rerun completed after citation prompt
fixes in commit 7e5b840. Run 3 results:

| query_id | category | halt | conf | citation_validity |
|---|---|---|---|---|
| q020 | instrument_type | verify_passed | 1.0 | 1 doc_id verified |
| q040 | dollar_range | verify_passed | 1.0 | 1 doc_id verified |
| q060 | severity_critical | max_iterations | 0.0 | 0 (persistent gap) |
| q080 | gap_pattern | verify_passed | 1.0 | 1 doc_id verified |
| q100 | combined | verify_passed | 1.0 | 14 doc_ids verified |

4/5 verify_passed with real citations. severity_critical is the documented persistent zero-citation
failure; endpoint stays internal through Day 11 consolidation review. Gate satisfied.

**Pre-flight deviations from handoff**:
- ColPali deferred: CPU-only torch; GTX 1650 has 4GB VRAM, ColPali requires 6-8GB minimum
- Nougat deferred: not installed; CPU-only; arXiv academic-paper domain mismatch for BOS docs
- marker-pdf deferred: pillow<11 incompatible with Python 3.14 (B-11 pattern)
- Original target (20-doc Fresno sample) substituted with TCPD PrimeGov corpus (see CP4)

---

## Bakeoff: pymupdf vs pdfplumber vs pypdf

**Corpus**: 1,107 TCPD PrimeGov PDFs in cache/tcpd_primegov/ (307 MB total)
**Sample**: 60 files (20 per category, SEED=42)
**Libraries**: pymupdf 1.27.2.3 (fitz, AGPL), pdfplumber 0.11.10 (MIT), pypdf 6.12.2 (BSD)

### Category Definitions

Derived from corpus probe (all 1,107 files categorized via fitz scan):

| Cat | Description | Count | Method |
|---|---|---|---|
| A | Short notices/agendas (<100KB, 1-4 pages) | 338 | size-based |
| B | Standard BOS agendas (100-500KB, 5-10 pages) | 619 | size-based |
| C | Staff reports with attachments (>500KB, 10+ pages) | 150 | size-based |
| D | Encoding-problematic (U+FFFD / bullet artifacts) | 0 | artifact probe |

Category D yielded zero files: the TCPD corpus is entirely digitally-born with clean encoding.

### Speed Results

| Library | Cat A median | Cat B median | Cat C median | ALL median | All 20-file total |
|---|---|---|---|---|---|
| pymupdf | 0.014s | 0.017s | 0.073s | **0.019s** | 2.6s |
| pypdf | 0.418s | 0.202s | 0.579s | 0.392s | 34.2s |
| pdfplumber | 1.103s | 0.628s | 3.783s | 1.330s | 184.2s |

Projected full corpus (1,107 files): pymupdf 21s, pypdf 7.2 min, pdfplumber 24.5 min.

### Critical Finding: Content Duplication in Cat C

Cat C median char counts:
- pymupdf: 15,191 chars (correct -- per-page isolation)
- pypdf: 104,750 chars (7x inflation)
- pdfplumber: 104,460 chars (7x inflation)

Investigation of worst-case file (tcpd_2295_24819.pdf, 15 pages):
- pymupdf: 36,027 chars total (1,316-3,547 chars per page, correct variation)
- pypdf: 541,095 chars = 36,073 chars x 15 pages (full document returned once per page)
- pdfplumber: identical duplication pattern

Root cause: these Cat C PDFs store their text as a document-level stream rather than per-page
streams. pymupdf correctly isolates per-page content; pypdf and pdfplumber return the full
document stream for each page reference.

Consequence for ODIA RAG: ingesting Cat C with pypdf/pdfplumber would inject 7-15 duplicate
copies of each agenda into the vector store, corrupting similarity search for 13.5% of corpus.

### Encoding Quality

All three libraries: zero replacement chars (U+FFFD), zero bullet artifacts across all 60 files.
The encoding artifacts visible in early probes (bullet-space substitution in BOS header lines)
are cosmetic Unicode normalization issues that do not affect extraction completeness.

---

## B-6 Checkpoint Session A

### CP1: Per-category Extraction Recommendation

**VERDICT: pymupdf exclusively for all TCPD PrimeGov corpus extraction**

- Cat A, B: pymupdf correct, 21x faster than pypdf, 71x faster than pdfplumber
- Cat C: pymupdf is the ONLY correct choice (pypdf/pdfplumber content duplication bug)
- No per-category split needed

### CP2: Day 11 Hardware-Gated Items Plan

**Vast.ai session signed off.** Credits confirmed sufficient.

**Session spec** (single ~2h RTX 4090 session):

Target instance: RTX 4090 (24GB VRAM), Vast.ai on-demand. Ubuntu 22.04.

Tasks in order:
1. ColPali (google/paligemma-3b-mix-448): generate visual embeddings for all 1,107 TCPD PDFs.
   VRAM: ~5GB. Purpose: visual understanding of layout and embedded images that pymupdf text
   extraction cannot describe -- contracts with signature blocks, tables with dollar amounts.
   Output: data/vectors/tcpd_colpali_embeddings.npy (to be copied to Roaming/ODIA/data/vectors)

2. Nougat (facebook/nougat-base): OCR pass on any pages where pymupdf extraction falls below
   a quality threshold (defined as <50 chars extracted from a non-blank page, or page flagged
   as image-only by fitz). VRAM: ~2GB. Output: augments cache/tcpd_primegov/*.txt sidecars.

3. severity_critical citation discipline: R.A.I.A. endpoint promotion gate. After ColPali
   embeddings extend the retrieval pool for severity_critical queries, re-run the Day 4
   five-query eval. Target: severity_critical achieve at least 1 verified doc_id citation
   per finding. If achieved: /api/v1/raia/analyze moves to allowlist-gated production.

Session protocol:
- Provision instance -> upload SSH key (not yet uploaded; see odia-vastai-finetuning-state memory)
- Install: torch 2.4 (CUDA 12.1), transformers, Unsloth (for odia-v3 M-3 if session permits)
- Run scripts/day11_colpali_nougat.py (to be written in Day 11 prep)
- Download outputs to local -> destroy instance immediately after download confirmed
- Do NOT leave instance running between steps; destroy and re-provision if resuming

**odia-v3 M-3 adversarial training**: if session time permits after ColPali+Nougat, run
the M-3 adversarial example generation (L-13 AI defense). This is opportunistic -- Day 11
core tasks take priority.

### CP3: marker-pdf Gap Documentation

**Failure**: pillow<11 has no Python 3.14 wheel (B-11 pattern). marker-pdf 0.x requires
pillow<11. Python 3.14 ships with incompatible C-extension ABI.

**Gap**: marker-pdf uses a vision transformer pipeline (document layout segmentation -> text
block extraction -> column resequencing) that handles genuinely complex layouts better than
heuristic text extraction. Specific benefits foregone:
- Multi-column staff report resequencing (text flows across columns correctly)
- Table structure preservation as markdown
- Figure/caption association

**Gap assessment for current corpus**: MINIMAL. All 1,107 TCPD PDFs are digitally-born BOS
meeting documents. The bakeoff showed zero encoding artifacts and correct per-page isolation
with pymupdf. No multi-column resequencing failures were detected across 60 sampled files.

**Resolution options ranked by immediate applicability**:

| Option | Mechanism | When to use | Cost |
|---|---|---|---|
| A (Day 11, GPU) | ColPali + Nougat on Vast.ai RTX 4090 | Visual layout understanding at scale | ~$2 Vast.ai credits |
| B (immediate) | pymupdf get_text("blocks") + coordinate sort | If multi-column mis-sequencing is detected in a specific file | 0 -- pure Python |
| C (subprocess) | Python 3.12 venv for marker-pdf only | If marker-pdf's table markdown output is needed before Day 11 | ~30 min setup |
| D (accepted gap) | pymupdf as-is for current TCPD corpus | BOS meeting docs, no complex multi-column detected | 0 |

**Signed-off resolution**: Option D (accept gap for current TCPD corpus) + Option A at Day 11.
Option B available as immediate fallback if a specific file is found to mis-sequence.
Option C deferred indefinitely -- ColPali supersedes marker-pdf for the use cases ODIA needs.

### CP4: TCPD PrimeGov Substitution Acceptance

**Substitution**: original Day 5 handoff spec called for a 20-doc Fresno sample.
Actual run: 1,107 TCPD PrimeGov PDFs across 3 size categories, 60-file sample, 180 extractions.

Rationale for substitution: D-07 corpus gap urgency (TCPD is the Section 1983 pattern-and-practice
anchor for the April 29, 2027 filing); PrimeGov adapter already implemented; TCPD ingest already
complete (1,080 docs in DB as of 2026-10-31 query).

**Performance evaluation**:
- Extraction speed: 21s for full 1,107 files with pymupdf (acceptable for ingestion pipeline)
- Extraction quality: zero encoding artifacts, zero empty pages (Cat A/B), 1 empty page total (Cat C)
- Yield: 1,080 of 1,107 cached PDFs ingested to DB (97.5% success rate)

**Functional incorporation**:
- Adapter: src/oraculus_di_auditor/adapters/primegov_adapter.py -- fully implemented
  - Public API (no auth), CSRF token, Azure Blob SAS URL download
  - Politeness controls: 1.5s pause between requests, 10s pause every 20 requests
  - Retry logic: 3 retries with 30s backoff
  - Cache layer: cache/tcpd_primegov/ prevents re-downloading
- Ingest script: scripts/ingest_tcpd.py -- posts to ODIA webhook with jurisdiction_id="tcpd"
- DB record: jurisdiction "tcpd" with 1,080 documents confirmed via live DB query

**Integration gap identified**:
- PrimeGovAdapter is NOT exported in adapters/__init__.py (only LegistarAdapter is)
- No TCPD entry in config/legistar_cities.json (correct -- PrimeGov is a separate portal)
- These gaps are acceptable for current single-jurisdiction TCPD ingest (script instantiates
  adapter directly). Resolution needed before a generalized multi-jurisdiction PrimeGov harvest.

**Substitution accepted**. TCPD PrimeGov corpus is the Day 5 target of record. The bakeoff
on TCPD PDFs is more operationally relevant than the original 20-doc Fresno sample because
TCPD documents are the active gap being closed for Section 1983 preparation.

**Integration gap action item (not Day 5 blocker)**:
Add PrimeGovAdapter to adapters/__init__.py and add a tcpd entry to a new
config/primegov_portals.json for multi-jurisdiction PrimeGov support.

---

## D-05 Resolution (bonus -- live DB queried 2026-10-31)

Authoritative corpus counts from live oraculus_audit.db:

| Metric | Authoritative (live DB) |
|---|---|
| Documents | 81,309 |
| Findings (anomalies) | 271,245 |
| Jurisdictions | 16 |

All three prior figures reconciled:
- GCA Handoff doc (38,950): pre-ingest snapshot, written before Fresno City NSU + TCPD harvest
- Day 5 Roadmap V1.0 (65,108 / 17 jurisd.): intermediate snapshot, methodology unclear; 17th
  jurisdiction does not exist in live DB
- Memory checkpoint (81,309): confirmed correct -- matches live DB exactly

D-05 is resolved. All future legal filings and the CA AG referral letter may cite:
**81,309 documents / 271,245 findings / 16 jurisdictions (verified 2026-10-31)**.

TCPD corpus status update: D-07 urgency revised. TCPD is at 1,080 docs (not 63 as the
2026-10-08 pre-ingest export showed). The PrimeGov harvest ran to completion. Target of 500+
docs for Section 1983 pattern-and-practice is already met.

---

## Severity breakdown (live DB, 2026-10-31)

| Severity | Count |
|---|---|
| MEDIUM | 100,143 |
| HIGH | 96,111 |
| LOW | 63,355 |
| CRITICAL | 11,636 |

---

## Open items passed to Day 6

- PrimeGovAdapter not exported in adapters/__init__.py (non-blocker for Day 6)
- severity_critical citation failure: persistent zero-citation across all runs; targeted
  for Day 11 ColPali retrieval expansion + RAIA endpoint promotion review
- B-10 blocker: contra_training_v1.jsonl does not exist; Day 6 preference extraction
  baseline must be resolved before Day 6 build starts

## Next: Day 6 (B-6 Session B + Preference Optimization)

B-6 Session B at start of Day 6 (45-60 min):
- CP5: L-11 Healthcare District scoping decision (operator sign-off required)
- CP6: L-12 Civic Ritual scoping decision (operator sign-off required)
- CP7: L-13 Scenographic Compilation disposition (recommended: absorb into L-10)
- D-02 / D-05 resolution sequencing (D-05 now resolved; D-02 Week 1 target)

Day 6 build: data/preferences_v1.jsonl, DPO config, 10-step smoke test.
Recommended preference strategy: generate chosen/rejected pairs from live RAIA traces
(run 3 citation-grounded responses = chosen; pre-7e5b840 vacuous responses = rejected).
