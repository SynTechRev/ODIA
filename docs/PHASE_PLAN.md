# ODIA Development Roadmap

**Version**: 3.9.2 | **Test suite**: 4,378 passed, 15 skipped | **Last updated**: 2026-10-04

| Corpus stat | Value |
|---|---|
| Total documents | 50,699 |
| Total findings | 148,349 |
| Jurisdictions | 16 |
| odia-v1 | LIVE (Ollama, Q4_K_M GGUF) |
| Sunshine Dragnet deadline | **2028-07-02** |

---

## Track 1 -- Core Platform

| Item | Status |
|---|---|
| Multi-format ingestion (PDF, XML, JSON, TXT) | DONE |
| 20+ detector layers (fiscal, surveillance, procurement, etc.) | DONE |
| FastAPI backend + modular route system | DONE |
| Next.js 14 frontend (8 pages) | DONE |
| Electron desktop app (v3.9.1 -- Win/Mac/Linux) | DONE |
| SQLite corpus (50,699 docs / 148,349 findings) | DONE |
| TF-IDF RAG pipeline (corpus + ACE + JIM collections) | DONE |
| JWT auth, governance, scalar scoring | DONE |
| CI/CD (GitHub Actions -- 4 platform builds) | DONE |

---

## Track 2 -- odia-v1 LLM

| Item | Status |
|---|---|
| 87,618 training examples (13,498 reports + 74,120 explanations) | DONE |
| QLoRA fine-tune on Llama-3.1-8B (r=16, alpha=32, 2 epochs) | DONE |
| Q4_K_M GGUF quantization (4.92 GB) | DONE |
| Registered in Ollama as `odia-v1` | DONE |
| Wired as default RAG LLM (rag_config.py + ollama_config.yaml) | DONE |
| HuggingFace upload (SynTechRev/odia-v1, private) | DONE |

---

## Track 3 -- Corpus Ingest

### Tulare County jurisdictions (complete)

| Jurisdiction | Docs | Findings | MAS |
|---|---|---|---|
| visalia | 7,928 | 20,824 | DONE 2026-06-16 |
| tulare | 3,062 | 10,750 | DONE |
| tcso | 573 | 4,474 | DONE 2026-06-16 |
| tcda | 660 | 102 | DONE 2026-06-16 |
| visalia-pd | 340 | 4,571 | DONE |
| farmersville | 1,643 | 7,525 | DONE |
| exeter | 1,396 | 4,838 | DONE |
| dinuba | 1,105 | 13,506 | DONE |
| lindsay | 805 | 4,799 | DONE |
| porterville | 350 | 1,756 | DONE |
| woodlake | 103 | 773 | DONE |
| tulare-county | 95 | 119 | DONE |
| tcpd | 161 | 132 | PARTIAL -- public records only |
| multi-jurisdiction | 12 | 107 | DONE |

### Fresno County jurisdictions

| Jurisdiction | Docs | Findings | MAS | Notes |
|---|---|---|---|---|
| fresnocounty | 32,340 | 73,547 | V4.0 DONE 2026-07-31 | NSU complete. $14.97B unsigned instruments. |
| fresno-pd | 126 | 526 | V4.0 DONE 2026-07-31 | 3 Flock detections. |
| **fresno (city)** | **0** | **0** | **PENDING** | **NSU currently running** (`ingest_legistar.py --client fresno`). $1.5M Flock contract + TASER sole-source + JAG not yet in corpus. |

### Pending

- [ ] City of Fresno NSU ingest -- in progress (15,044 matters est.)
- [ ] Fresno MAS V2.0 via Opus -- after city ingest + CPRA returns
- [ ] TCPD PrimeGov harvest -- `python scripts/ingest_tcpd.py --dry-run` then full run
  - **2026-10-05: Portal migration confirmed.** Questys CMX at `publicdocs.co.tulare.ca.us` is dead (Drupal 10 redirect). New system: PrimeGov at `tularecounty.primegov.com` (Granicus). BOS committee ID = 25. API: `/api/v2/PublicPortal/ListArchivedMeetingsByCommitteeId?year=N&committeeId=25` returns meeting list with compiled file IDs. `/api/Meeting/getcompiledfiledownloadurl?compiledFileId=N` returns signed Azure Blob SAS URL. PDF download confirmed (228KB, Oct 6 2026 BOS agenda). Archives go back to 2006 (21 years, ~700+ meetings est.). `primegov_adapter.py` written and `ingest_tcpd.py` updated.

---

## Track 4 -- CPRA Letters

| Target | Status |
|---|---|
| Fresno County Sheriff | PENDING |
| Fresno County BOS Clerk | PENDING |
| Fresno County IT/CEO | PENDING |
| City of Fresno | PENDING |
| Fresno Police Department | PENDING |
| TCPD (CPRA-004) | PENDING |

- [ ] Send letters after City of Fresno ingest is complete
- [ ] Target date: after Fresno MAS V2.0

---

## Track 5 -- C.O.N.T.R.A. (Commercial Contract Reasoning)

| Item | Status |
|---|---|
| 10 detectors (L-11 through L-20) | DONE |
| CASI + CIFU scoring engine | DONE |
| Entity registry (57+ entities) | DONE |
| Gig Economy chain (7 entities, CIFU v2 100.0) | DONE |
| AT&T / Cricket Wireless chain (CIFU v2 100.0) | DONE |
| Telecom Carrier Full (CIFU v2 99.6) | DONE |
| Uber Worker + Consumer chains | DONE |
| Behavioral Advertising Surveillance chain | DONE |
| Financial Instrument Worker Payment chain | DONE |
| Identity Resolution & Data Broker chain | DONE |
| Frontend /contra tab | DONE |
| 6,672 CONTRA training examples (odia-v2 Types 1-6) | DONE |
| **Lyft worker/driver agreement harvest** | **PENDING** |
| **DoorDash Dasher agreement (JS-rendered)** | **PENDING** |
| **§1281.96 arbitration data pipeline** | **PENDING -- blocks odia-v2 Type 7** |

---

## Track 6 -- S.A.B.E.R. (Security Asymmetry Balance Equalization Record)

| Item | Status |
|---|---|
| Pillar 4: Signing (Ed25519, HybridSignature) | DONE |
| Pillar 1: Content Store (SHA-256 blob store + lookup table) | DONE |
| Pillar 3: Audit Log (Merkle chain, verify_chain, checkpoints) | DONE |
| Pillar 2: Manifest (signed loader manifests) | DONE |
| Phase 1 migration -- 13 CPRA provisions | DONE 2026-10-04 |
| Architect signing key generated (SABER_SIGNING_KEY_PATH) | DONE |
| Root hash at Phase 1: `00b16be764a7...` | DONE 2026-10-04 |
| GitHub repo saber-audit-log created | DONE 2026-10-04 |
| First checkpoint committed (saber-audit-20261004T210456Z.json) | DONE 2026-10-04 |
| Daily checkpoint workflow (.github/workflows/daily-checkpoint.yml) | DONE 2026-10-04 |
| Apache 2.0 license elected for saber/ subpackage | DONE 2026-10-04 |
| ML-DSA-65 post-quantum signing | DONE 2026-10-05 (scripts/saber_upgrade_key.py; signing.py _ml_pub fix; hybrid checkpoint saber-audit-20261005T023831Z.json) |

---

## Track 7 -- A.R.C.A.D.E. (Security Layers)

### Layer 2 -- Supply Chain Security

- [x] .github/workflows/supply_chain.yml (gitleaks + osv-scanner + Syft SBOM + cosign)
- [x] .pre-commit-config.yaml (gitleaks + ruff + detect-private-key)
- [x] Install: gitleaks v8.30.1 + osv-scanner v2.6.0 -- 2026-10-04
- [x] Install pre-commit hooks: `pre-commit install` -- 2026-10-04
- [ ] Activate: push ODIA repo to GitHub remote

### Layer 13 -- AI Defense (garak 0.17.0)

- [x] scripts/arcade_l13_garak.py written
- [x] garak 0.17.0 installed in venv
- [x] Probe names corrected to 0.17.0 API (promptinject, latentinjection, leakreplay, packagehallucination, web_injection, dan)
- [x] Run launched 2026-10-04 14:39 UTC -- 32 DAN attempts, 160 generations
- [x] Results analysis -- data/saber/ai-defense/arcade-l13-analysis-20261004.md -- 2026-10-04
  - **CRITICAL FINDING**: odia-v1 100% susceptible to DAN 11.0 jailbreak (160/160 generations)
  - `detector_results: {}` -- scoring phase incomplete; 5 of 6 probe sets did not run
- [x] M-1: SECURITY_GUARD_SYSTEM_PROMPT injected as system-role message on every Ollama call -- 2026-10-04
  - security/jailbreak_filter.py (7 pattern categories), llm_providers.py updated
- [x] M-2: Output filter in OracRAG.query() -- blocks DAN compliance post-generation -- 2026-10-04
  - 53/53 tests passing (test_jailbreak_filter.py + test_orac_rag_security.py)
- [ ] M-3: Adversarial refusal examples for odia-v2 training (pending Vast.ai credits)
- [x] Re-run promptinject (3 probes, 256×5=1280 evals/probe) -- DONE 2026-10-05
  - **CRITICAL**: 77–80% vulnerable to data-embedded injection; M-1/M-2 holds for DAN but not promptinject
  - M-1 enhanced 2026-10-05: rule 7 added to SECURITY_GUARD_SYSTEM_PROMPT (data injection defense); 53/53 tests
  - **M-1 R7 re-run result 2026-10-05: 77.1% vulnerable (HijackHateHumans, 170 outputs) — no significant improvement**
  - Conclusion: promptinject is a training-time gap; system prompt cannot fix base model behavior
  - Analysis: data/saber/ai-defense/arcade-l13-analysis-promptinject-20261005.md
  - M-3 (adversarial training for odia-v2) is the required fix -- pending Vast.ai credits

### Layer 14 -- Backup and Recovery (restic 3-2-1-1-0)

- [x] scripts/arcade_l14_backup.py written (updated to resolve restic via WinGet fallback)
- [x] Install: restic v0.19.1 -- 2026-10-04
- [x] RESTIC_PASSWORD set at user environment level -- 2026-10-04
- [x] Init repo: `python scripts/arcade_l14_backup.py --init` -- 2026-10-04
- [x] First backup (snapshot e0ac15b7): `--backup` -- 2026-10-04 17:36 UTC (43.682 MiB)
- [x] Second backup (snapshot 0540340f): `--backup` -- 2026-10-04 18:57 UTC (45.791 MiB, +36.2 MiB delta)
- [x] Verify: `--verify` -- no errors, 2 snapshots, integrity passed -- 2026-10-04
- [x] Schedule daily backup: Windows Task Scheduler `ODIA-ARCADE-L14-Backup` at 02:00 AM -- DONE 2026-10-05

---

## Track 8 -- odia_legal (Legal Reasoning Engine)

**Deadline: 2028-07-02 (Sunshine Dragnet Phase Zero)**

### Phase 1 -- Citation Infrastructure (DONE)

- [x] CPRACorpusLoader -- 13 embedded provisions, no submodule required
- [x] CalCitation + parse_cal_citations() -- California Code citation parser
- [x] L-9 recodification -- 18 Cal. statute strings updated to § symbol
- [x] CPRA crosswalk -- auto-enriches doctrinal_anchor in contra/_utils.py
- [x] 234/234 contra + cpra tests passing

### Phase 2 -- L-Detector Reasoning Engine (DONE)

| Detector | Rules | Tests | Status |
|---|---|---|---|
| _base.py (DocContext, LegalFinding, LegalDetector, Severity) | -- | -- | DONE 2026-10-04 |
| L-1 Statutory Applicability | 3 tiers (CPRA baseline + doc-type + content signals) | 22/22 | DONE 2026-10-04 |
| L-2 Procedural Compliance | PC-1 through PC-4 | 14/14 | DONE 2026-10-04 |
| L-3 Exemption Misapplication | EX-1 through EX-5 | 18/18 | DONE 2026-10-04 |
| L-4 Ministerial Duty | MD-1 through MD-5 | 17/17 | DONE 2026-10-04 |
| L-5 Federal Grant Compliance | GC-1 through GC-5 | 21/21 | DONE 2026-10-04 |
| L-6 Constitutional Implication | CI-1 through CI-5 | 21/21 | DONE 2026-10-04 |
| L-10 Balancing Test Analyzer | BT-1 through BT-5 | 32/32 | DONE 2026-10-04 |
| L-7 Regulatory Authority | RA-1 through RA-5 | 26/26 | DONE 2026-10-04 |
| L-8 Case Law Currency | CC-1 through CC-5 | 32/32 | DONE 2026-10-04 |
| L-9 Statute Citation Auditor | SA-1 through SA-5 | 30/30 | DONE 2026-10-04 |
| PHASE2_DETECTORS registry | 10 detectors (L-1 through L-10, complete) | -- | DONE 2026-10-04 |
| run_legal_detectors.py (batch pipeline) | -- | -- | DONE 2026-10-04 |
| POST /api/v1/legal/detect (API route) | -- | 12/12 | DONE 2026-10-04 |

**Legal module total: 373/373 tests passing**

**odia_legal Phase 2 COMPLETE -- all 10 detectors live (L-1 through L-10)**

### Phases 3-6 -- Not started

| Phase | Scope |
|---|---|
| Phase 3 | Case law corpus integration (Westlaw / CourtListener pipeline) |
| Phase 4 | LLM-augmented legal reasoning (odia-v2 legal fine-tune) |
| Phase 5 | Cross-jurisdiction precedent mapping |
| Phase 6 | Litigation-grade output (memoranda, demand letters, TOA) |

---

## Track 9 -- odia-v2 LLM

| Item | Status |
|---|---|
| Types 1-6 training examples (6,672 CONTRA-derived) | DONE |
| Vast.ai account created | DONE |
| Vast.ai credits | PENDING -- $0 balance |
| SSH key uploaded to Vast.ai | PENDING |
| Type 7 -- §1281.96 arbitration data pipeline | BLOCKED -- 0 rows in DB |
| Type 8 -- Gig worker agreement harvest (Playwright) | BLOCKED -- JS-rendered |
| Types 9-10 design | PENDING |
| Training run (RTX 4090, Unsloth Studio) | PENDING |

---

## Milestone Summary

| Milestone | Target | Status |
|---|---|---|
| Core platform + RAG + odia-v1 | 2026-08 | COMPLETE |
| Tulare County full corpus + MAS | 2026-06 | COMPLETE |
| Fresno County + FPD corpus + MAS V4.0 | 2026-07 | COMPLETE |
| C.O.N.T.R.A. Phase A-G | 2026-08 | COMPLETE |
| S.A.B.E.R. Phase 1 + ML-DSA-65 hybrid signing | 2026-10 | COMPLETE (2026-10-05) |
| odia_legal Phase 2 (L-1 through L-10) | 2026-10 | COMPLETE |
| A.R.C.A.D.E. L-13 garak run + analysis | 2026-10 | COMPLETE (CRITICAL finding: DAN) |
| A.R.C.A.D.E. L-2 tools installed + hooks active | 2026-10 | COMPLETE |
| A.R.C.A.D.E. L-14 restic backup + daily scheduler | 2026-10 | COMPLETE (daily 02:00, Task Scheduler ODIA-ARCADE-L14-Backup) |
| City of Fresno NSU ingest | 2026-10 | IN PROGRESS |
| CPRA letters (6 targets) | 2026-11 | PENDING |
| Fresno MAS V2.0 | 2026-11 | PENDING |
| odia_legal Phase 2 (L-1 through L-10) | 2026-10 | **COMPLETE** |
| odia-v2 training (87,618+ examples) | 2027-Q2 | PENDING |
| odia_legal Phases 3-6 | 2027-2028 | PENDING |
| **Sunshine Dragnet Phase Zero** | **2028-07-02** | **TARGET** |
