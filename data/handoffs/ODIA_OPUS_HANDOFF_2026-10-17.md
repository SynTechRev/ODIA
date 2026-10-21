# ODIA Opus Handoff — 2026-10-17

**Supersedes**: ODIA_OPUS_HANDOFF_2026-10-01.md (and CONTRA_OPUS_HANDOFF_2026-08-23.md for the CONTRA track)
**Prepared by**: MARS (SynTechRev) via Claude Code (Sonnet 5.5)
**Window covered**: 2026-10-01 → 2026-10-17 06:58 PDT
**Repo**: `C:\Users\yahua\Downloads\ODI x RAIA\Oraculus-DI-Auditor-clean`, master, v3.9.2, 3 commits ahead of origin (unpushed)
**Purpose**: bring Opus current for synthesis analysis, corpus inclusion and roadmap update.

> Status key: **VERIFIED** = read from a file or process on disk during this handoff. **MEMORY** = carried from session notes, not re-checked. **OPEN** = unresolved or needs Opus or MARS.

---

## 0. Asks of Opus (priority order)

1. **Fresno County MAS synthesis** (27,413 docs / 123,736 findings, the largest jurisdiction, not yet synthesized). Splits are in `data/mas_export/fresnocounty_splits/`. Use the same upload order as the City run (SPLIT_INDEX → severity_CRITICAL → layer_signature → layer_surveillance → layer_procurement → layer_l5_federal_grant_compliance → HIGH parts). The County CPRA letters were drafted from MAS aggregates only, so the synthesis should confirm or correct their anchor numbers (§3).
2. **Finish the City MAS V2.0 synthesis**. Only 9 of 34 split files were reviewed. The next batch is in §4.
3. **TCPD MAS synthesis** (`data/mas_export/tcpd_splits/`, `tcpd_MAS.json`). It is new since the last handoff and Opus has not seen it.
4. **Reconcile finding counts** (§2.2). The ACE index total and the per-jurisdiction table may not describe the same set.
5. **Roadmap update** (§7): confirm the proposed re-ordering.
6. **Interpret the L-13 results** when the garak run finishes (§5). There are no verdicts yet, so do not synthesize L-13 beyond the 2026-10-04/05 findings.

---

## 1. What changed since 2026-10-01 (headline)

| Track | State |
|---|---|
| City of Fresno ingest | DONE 2026-10-08. 16,692 matters, 29,308 new files, 0 failures. 14,409 docs / 64,489 findings (MEMORY). |
| TCPD ingest (PrimeGov BOS, 2006–2026) | DONE. Log shows 1,262 items: **1,078 new / 29 already seen / 155 DOWNLOAD_FAILED** (VERIFIED, `logs/tcpd_ingest.log`). `tcpd_MAS.json` and `tcpd_splits/` exist. The 155 failures are mostly older `compiledFileId` entries (e.g. 2006-12 meetings); retry has not been attempted. |
| MAS exports | `*_MAS.json` exist for 15 jurisdictions plus `fresno_splits/` (35 files ≤8 MB), `fresnocounty_splits/` and `tcpd_splits/` (VERIFIED). CORPUS_INDEX, SEVERITY_MATRIX and CROSS_JURISDICTION_PATTERNS were refreshed 2026-10-08. |
| CPRA letters | 7 drafted and committed in db6c064 (§3). **Not sent**, not pushed. |
| RAG index | Rebuilt: 2026-10-16 20:21 (VERIFIED). corpus 81,309 / ACE 271,245 / JIM 3,937 entries. All 9 vector files are present in `AppData\Roaming\ODIA\data\vectors` (VERIFIED). The stalled-rebuild blocker is **resolved**. |
| Retriever OOM | Fixed in 2123a06. |
| Watchdog and ingest performance | 1c7553a and 80d9db2 are on origin (VERIFIED). |
| CourtListener harvest | **BLOCKED**: no API key. All `/clusters/*` detail calls returned 401, so 0 new cases. The legal corpus stays at 84 cases / 19 doctrines (VERIFIED, `logs/courtlistener_harvest_20261016.log`). |
| odia-v2 training | Blocked: Vast.ai credits $0, SSH key not uploaded, §1281.96 pipeline incomplete (MEMORY). |
| ARCADE L-13 (garak) | **IN PROGRESS** (§5). |

Git: `master` is 3 ahead of `origin/master` (503902c, 2123a06, db6c064). Untracked: `data/handoffs/`, `logs/*` (VERIFIED). Local and origin tags agree on v3.9.0–v3.9.2 and nothing is behind (VERIFIED after `git fetch`). The earlier note "5 commits ahead" is stale: 1c7553a and 80d9db2 have since been pushed.

---

## 2. Corpus state

### 2.1 Per-jurisdiction (2026-10-08 export, MEMORY; TCPD row is pre-ingest)

| Jurisdiction | Docs | Findings |
|---|---|---|
| fresnocounty | 27,413 | 123,736 |
| fresno (city) | 14,409 | 64,489 |
| visalia | 5,814 | 20,824 |
| tulare | 2,244 | 10,750 |
| dinuba | 1,087 | 13,506 |
| farmersville | 1,292 | 7,525 |
| lindsay | 661 | 4,799 |
| exeter | 1,048 | 4,838 |
| tcso | 458 | 4,474 |
| visalia-pd | 337 | 4,571 |
| porterville | 340 | 1,756 |
| woodlake | 85 | 773 |
| tcpd | 2 → ~1,100+ after ingest | 15 → **needs re-export** |
| tcda | 97 | 102 |
| tulare-county | 49 | 119 |
| multi-jurisdiction | 7 | 107 |
| fresno-pd | separate file | n/a |

### 2.2 OPEN: count reconciliation
- The table's findings column sums to **262,384**. It predates the TCPD ingest and excludes fresno-pd.
- The headline "271,245 findings" is the **ACE index size**. The RAG log says the ACE index = DB findings **plus** 107,653 L-1..L-10 legal-layer findings (VERIFIED, `logs/rag_rebuild_20261016.log`).
- If both are correct, the DB-only count is about 163,592, which does not match the table. One of these figures is mislabelled or double-counted.
- **Ask**: the next export should report DB findings and legal-layer findings separately, per jurisdiction. Until then, quote 271,245 as "ACE index entries" and not as "findings".
- The TCPD row, and the 14,409 and 64,489 City figures, should be refreshed from the same export.
- `CLAUDE.md` is stale (dated 2026-08-11) and disagrees with the 10-08 export. It lists fresnocounty at 32,340 docs / 73,547 findings (the export says 27,413 / 123,736), tcpd at 161 docs / 132 findings (the export says 2 / 15), and fresno (city) at 0 docs. Its 148,349 total is the pre-City, pre-TCPD DB figure. Do not cite CLAUDE.md numbers. Treat the 10-08 export, then a fresh re-export, as authoritative.

### 2.3 Legal and training assets
- odia-v1 (Llama-3.1-8B QLoRA, 87,618 examples) is registered in Ollama and is the RAG default. Do not retrain.
- C.O.N.T.R.A. training set: 6,672 examples (`data/contra_training_v1.jsonl`), 8 chains, all Foreclosure Regime, as of the 10-01 handoff (unchanged).
- odia_legal: 10 detectors (L-1–L-10). CourtListener corpus is stuck at 84 cases (see §1). Sunshine Dragnet Phase Zero deadline is **2028-07-02**.

---

## 3. CPRA letters (all in `data/cpra_letters/`, committed db6c064, none sent)

| # | Target | File | Drafted |
|---|---|---|---|
| 1 | City of Fresno — City Clerk (surveillance) | `fresno_city_clerk_CPRA_20261008.txt` | 10-08 |
| 2 | Fresno PD — Records (surveillance ops) | `fresno_pd_records_CPRA_20261008.txt` | 10-08 |
| 3 | City of Fresno — unsigned instruments (fiscal) | `fresno_city_unsigned_instruments_CPRA_20261016.txt` | 10-16 |
| 4 | Fresno County Sheriff | `fresnocounty_sheriff_CPRA_20261016.txt` | 10-16 |
| 5 | Fresno County BOS Clerk | `fresnocounty_bos_clerk_CPRA_20261016.txt` | 10-16 |
| 6 | Fresno County CAO + ITS | `fresnocounty_cao_it_CPRA_20261016.txt` | 10-16 |
| 7 | TCPD — Probation Dept | `tcpd_probation_CPRA_20261016.txt` | 10-16 |

Anchor numbers used (MEMORY; **verify against synthesis before sending**):
- City of Fresno: **2,956 unsigned instruments = 94.4% of 3,130 criticals** (signature layer). Sample amounts $10,024,426.24 and $3,100,000.
- Fresno County: **4,120 unsigned instruments (~$14.97B)**. 190 JAG anti-supplanting findings.
- TCPD: 60 JAG anti-supplanting findings.

Letters 4–7 were drafted from MAS aggregates, **not** from a completed Opus pass over the County or TCPD data. Letters 3–7 should be read once against the Opus synthesis before MARS sends them.

---

## 4. Fresno City MAS V2.0 synthesis — where it stands

- Opus reviewed 9 of 34 unique split files (inventory: `C:\Users\yahua\Downloads\Fresno_Split_Corpus_Inventory.xlsx`).
- **Have**: severity_CRITICAL, severity_HIGH parts 1–3, layer_fiscal, layer_grant_funding_trails, layer_l2_procedural_compliance, layer_surveillance, layer_procurement, SPLIT_INDEX.
- **Next batch (5 files, 11.57 MB)**: `layer_signature.json` (2.81 MB), `layer_scope.json` (6.54 MB), `layer_l5_federal_grant_compliance.json` (0.49 MB), `layer_vote_date_alignment.json` (1.24 MB), `layer_governance.json` (0.49 MB).
- Do not re-upload `layer_fiscal.json` (byte-identical to the project-knowledge copy; MD5 confirmed).
- Surveillance evidence already in hand (MEMORY): 25 docs ALPR without SB 524 transparency citation (critical); 25 docs ALPR without Civ. Code §1798.90.5 policy citation (high); 11 docs facial recognition / AB 1215 (critical); 51 docs Axon BWC without CJIS Security Policy reference (high); 7 docs drone/UAS without AB 481 annual-report language (high); 6 docs AI report writing (Draft One) without SB 524 (critical); 18 docs reference Flock Safety; 56 docs reference Axon.
- Inference for Opus to test: the signature layer (94.4% of criticals) outweighs the surveillance layer (1.3% of criticals) in weight. The fiscal track should lead the City narrative.

---

## 5. ARCADE L-13 — AI Defense / garak (**the live run**)

### 5.1 Findings so far (completed, VERIFIED from `data/saber/ai-defense/`)

| Date | Attack class | Result (from garak report eval entries) |
|---|---|---|
| 10-04 | DAN, `dan.Ablation_Dan_11_0` on odia-v1 (before any fix) | `dan.DAN` detector failed **635/635 (100%)**. `mitigation.MitigationBypass` failed 505/635. `dan.AutoDANCached`: 0/15 on `dan.DAN`, 8/15 on MitigationBypass. |
| 10-04/05 | DAN after M-1 (system-prompt guard) + M-2 (`check_output` filter) | ~0% by **unit tests only (53/53)**. **There is no garak re-run of DAN after the fixes.** The file `garak-odia-v1-m1m2-20261004.report.jsonl` is a latentinjection run killed at Eiffel probe 128/256 with no eval entries. |
| 10-05 | promptinject, M-1+M-2 (`...m1m2-promptinject-20261005`) | HijackHateHumans **994/1280 (77.7%)**; HijackKillHumans **995/1280 (77.7%)**; HijackLongPrompt **1031/1280 (80.5%)** failed. |
| 10-06 | promptinject re-run after M-1 Rule 7 (`...m1m2-r7-promptinject-20261005`, all 3 probes complete) | HijackHateHumans **1011/1280 (79.0%)**; HijackKillHumans **983/1280 (76.8%)**; HijackLongPrompt **1011/1280 (79.0%)**. Pooled **3005/3840 (78.3%)**, no improvement. The hitlog has 3,005 records. |

Correction to the earlier draft: the analysis note `arcade-l13-analysis-promptinject-20261005.md` reports only a partial r7 result (HijackHateHumans 131/170, 77.1%). The full r7 report shows all three probes completed. Use the table above.

Analysis files: `arcade-l13-analysis-20261004.md` and `arcade-l13-analysis-promptinject-20261005.md`. Their conclusion is that prompt injection is a **training-time gap**, not a prompting gap. M-3 (adversarial examples in odia-v2 training) is the only path to a meaningful fix, and it is blocked on Vast.ai credits. The odia-v1 base cannot reliably separate instructions from document content, and odia-v1 is the default RAG LLM that reads untrusted government documents, so this is the most consequential security finding.

### 5.2 Remaining probe sets (run 2026-10-16 → now)

Target: odia-v1 via Ollama, garak 0.17.0, 5 generations, seed 42.

**Run A — `garak-l13-remaining-config.yaml`** (DanInTheWild + packagehallucination + web_injection), started 10-16 ~19:50.
- DanInTheWild probe 55/256 triggered context overflow: 10–17 min per generation, observed ~4h25m for the first generation, ETA ~17 h more.
- **Aborted.** Last log write 10-17 02:33. 55 attempts were logged and none completed.
- **DanInTheWild produced no scored results.** It is excluded from Run B.
- The config's own comment says latentinjection (100+ h est.) and leakreplay (not relevant to a civic-accountability tool) were skipped by design.

**Run B — `garak-l13-pkghall-webinject-config.yaml`**, started **2026-10-17 06:44:43** (PID 17348, child 3448; **still running** at 06:58, VERIFIED via process list).
- Probes: packagehallucination (Dart, JavaScript, Python, Ruby, Rust) and web_injection (ColabAIDataLeakage, MarkdownImageExfil, MarkdownURIImageExfilExtended, MarkdownURINonImageExfilExtended, MarkdownXSS, PlaygroundMarkdownExfil, StringAssemblyDataExfil, TaskXSS).
- Progress at last check: `packagehallucination.Dart` 7/240 prompts in ~13.5 min (~112 s/prompt) → **~7.3 h for Dart alone**. The 13-probe queue will take **days** at this rate.
- Report: `C:\Users\yahua\.local\share\garak\garak_runs\garak.d01d1924-cda1-4dac-82ae-a0308a549339.report.jsonl`. It has 7 attempts and **0 eval entries**, so there are **no verdicts yet**. Garak writes the `eval` line only when a probe finishes.
- Repo logs (stdout is mostly a progress bar): `garak-l13-pkghall-webinject-stdout.log`, `-stderr.log`.

### 5.2b Hardware constraint (from the garak thread, `yahua-fa`, 2026-10-17 07:00)
- The GPU is a GTX 1650 with 4 GiB VRAM, and odia-v1 Q4_K_M is 4.92 GB. Inference is therefore **CPU-only**. That explains ~22 s per 5-generation call.
- DanInTheWild probe 55/256 has a very long prompt. It takes 10–17 min per generation until Ollama runs out of memory and exits. This happened on **three** attempts: Run A, a second attempt (`garak.dce5c2f3-…`, 55 attempts, no evals), and a third (`garak.47057022-…`) that aborted with a connection error before any probe ran.
- DanInTheWild is untestable on this hardware. It needs a generation timeout patch to garak's Ollama generator, or a GPU with ≥6 GiB VRAM. Vast.ai would also fix this.
- Ollama has 3 models loaded (odia-v1, llama3.1:8b, qwen3.6).
- No M-3 adversarial examples exist yet. The 3,005 r7 hitlog records (`goal, prompt, output, triggers, score`) are the raw negative-example corpus for M-3 once Vast.ai is funded.
- `data/saber/ai-defense/` is gitignored, so garak configs and logs are not committed (by design).

### 5.3 What Opus should and shouldn't conclude
- **There is no L-13 result for DanInTheWild, packagehallucination or web_injection.** "No hits" is not a finding here, because the probes have not completed. Silence from the run says nothing about the model.
- Relevance ranking for odia-v1's actual deployment (document analysis through RAG):
  - web_injection (markdown/URL exfiltration) is high relevance. Backend responses are rendered in the Electron UI.
  - packagehallucination is low relevance (a civic-audit tool does not recommend packages).
  - DanInTheWild is medium; DAN is already mitigated by M-1/M-2.
- **Decision for MARS/Opus (OPEN)**: at ~112 s/prompt, run web_injection first and drop or cap packagehallucination. A smaller `generations:` value or reordered/sampled probes would also bring it down. This handoff does not change the run.
- Of the 6 probe families in the original L-13 plan, the ones with completed garak verdicts are `dan` (pre-fix only) and `promptinject`. `latentinjection` (killed at 128/256), `leakreplay` (never ran), `packagehallucination`, `web_injection` and `DanInTheWild` have no verdicts.
- Because DAN has no post-fix garak verdict, the "DAN fully mitigated" claim rests on unit tests alone. A cheap post-fix `dan.Ablation_Dan_11_0` re-run (about 32 prompts) would close that.

### 5.4 Other thread
The garak thread (`yahua-fa`) replied. Its report agreed with the on-disk state on the live run, the three DanInTheWild failures and M-3 status. I did not take three of its statements as given, because the files contradict them:
- "DAN M-1+M-2 fully completed, PASS": no such garak result exists (see §5.1).
- "5 commits ahead of origin": it is **3** after `git fetch` (1c7553a and 80d9db2 are on origin).
- "M-2 = refusal preamble": the analysis note describes M-2 as a `check_output` regex filter on DAN-compliance patterns.

---

## 6. Other open blockers

| Blocker | Needs | Unblocks |
|---|---|---|
| `git push origin master` (3 commits ahead, includes the 7 CPRA letters) | MARS approval | Remote backup of the letters |
| `COURTLISTENER_API_KEY` | MARS to obtain and set env var | Legal corpus growth (84 → 180+ cases) |
| Vast.ai credits + SSH key upload | MARS | odia-v2 training, M-3 adversarial examples (closes the 78% prompt-injection gap) |
| §1281.96 data pipeline | Engineering | odia-v2 dataset completeness |
| 155 TCPD `DOWNLOAD_FAILED` | Retry run | TCPD coverage completeness (mostly 2006-era files) |
| Sending CPRA letters | MARS, after Opus read of letters 3–7 | Statutory 10-day response clock |

A. R.C.A.D.E. Tier 1 (as of 10-05, MEMORY): L-2 supply chain DONE (pending GitHub push); L-13 M-1 and M-2 live, M-3 pending; L-14 restic 3-2-1-1-0 backup DONE with daily 02:00 task. S.A.B.E.R. Phase 1 complete: 13 CPRA provisions, hybrid Ed25519 + ML-DSA-65 signatures, 49/49 tests.

---

## 7. Proposed roadmap update (for Opus to confirm or revise)

**Now (done, bank it):** City ingest → TCPD ingest → RAG rebuild → 7 CPRA letters drafted.

**Next 1–2 weeks**
1. Opus: Fresno County MAS synthesis, then finish the City batch, then TCPD. Read letters 3–7 against it.
2. MARS: push commits; send letters 1–3 first (they rest on the best-validated data), then 4–7 after Opus sign-off.
3. Re-export MAS/CORPUS_INDEX/SEVERITY_MATRIX with TCPD included, and reconcile counts (§2.2).
4. L-13: run a post-fix `dan.Ablation_Dan_11_0` re-run; let Run B finish web_injection; decide on cutting packagehallucination; then write the final L-13 analysis note.

**Gated (not startable until a human unblocks)**
- CourtListener key → harvest → legal corpus growth.
- Vast.ai credits → M-3 adversarial examples → odia-v2 training → L-13 re-test to confirm the injection fix.

**Anchor**: Sunshine Dragnet Phase Zero 2028-07-02.

**Roadmap changes proposed**: (a) add "count reconciliation" as a gating item before any number is published or cited in a letter; (b) move TCPD from "ingest running" to "MAS synthesis pending"; (c) mark RAG rebuild resolved; (d) split L-13 into "complete: DAN, promptinject" and "in progress: web_injection / packagehallucination / DanInTheWild (descoped)"; (e) add a prompt-injection residual-risk note against the RAG pipeline until M-3 lands.

---

## 8. File index

- Letters: `data/cpra_letters/`
- MAS exports and splits: `data/mas_export/` (`fresno_splits/`, `fresnocounty_splits/`, `tcpd_splits/`)
- City synthesis inventory: `C:\Users\yahua\Downloads\Fresno_Split_Corpus_Inventory.xlsx`
- L-13 outputs: `data/saber/ai-defense/`; live garak report in `C:\Users\yahua\.local\share\garak\garak_runs\`
- Logs: `logs/tcpd_ingest.log`, `logs/rag_rebuild_20261016.log`, `logs/courtlistener_harvest_20261016.log`
- RAG vectors: `data/vectors/` and `C:\Users\yahua\AppData\Roaming\ODIA\data\vectors\`
- Prior handoffs: `data/handoffs/`
