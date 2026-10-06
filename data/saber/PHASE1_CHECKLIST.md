# S.A.B.E.R. Phase 1 Development Checklist
## Security Asymmetry Balance Equalization Record
### Version 1.0 | October 2026

---

## 0. ELECTIONS (Complete)

- [x] ELECT-1: Working name confirmed -- S.A.B.E.R. (Security Asymmetry Balance Equalization Record)
- [x] ELECT-2: Namespace confirmed -- src/oraculus_di_auditor/legal/saber/
- [x] ELECT-3: Key custody confirmed -- Architect sole control, SABER_SIGNING_KEY_PATH env var
- [x] ELECT-4: Audit publication confirmed -- Public Git under SynTechRev
- [x] ELECT-5: Migration sequence confirmed -- all four corpora in parallel
- [x] ELECT-6: License confirmed -- MIT current; Apache 2.0 for saber/ deferred to Phase 1 delivery
- [x] ELECT-7: Agent numbering confirmed -- C-series by tier (C-1 through C-100+)
- [x] elections.yaml written at repo root

---

## 1. INFRASTRUCTURE (Written -- Pending Tests)

### Pillar 4 -- Signing (signing.py)
- [x] signing.py written
- [x] tests/legal/saber/test_signing.py passing
- [x] Ed25519 verified working
- [ ] ML-DSA-65 verified working (requires: `pip install liboqs-python`)

### Pillar 1 -- Content Store (content_store.py)
- [x] content_store.py written
- [x] tests/legal/saber/test_content_store.py passing
- [x] ContentStore.put() / .get() / .verify_blob() verified
- [x] ContentStore.resolve_citation() with as_of= verified
- [x] Lookup table signing verified

### Pillar 3 -- Audit Log (audit_log.py)
- [x] audit_log.py written
- [x] tests/legal/saber/test_audit_log.py passing
- [x] AuditLog.verify_chain() detects tampering
- [x] AuditLog.root_hash() is stable on identical content
- [x] AuditLog.write_checkpoint() writes publishable JSON

### Pillar 2 -- Manifest (manifest.py)
- [x] manifest.py written
- [x] tests/legal/saber/test_manifest.py passing
- [x] LoaderManifest round-trips through save/load
- [x] Signed manifest verifies with VerifyKey

### Module Init
- [x] saber/__init__.py written with all exports

---

## 2. KEY GENERATION (Pre-flight)

- [x] Generate Architect signing key: `python scripts/saber_keygen.py`
- [x] SABER_SIGNING_KEY_PATH set in environment (permanent Windows user env var)
- [x] public.json held for solo Phase 1

---

## 3. PHASE 1 MIGRATION (All Four Corpora in Parallel)

- [x] Dry run passes: `python scripts/saber_migrate_phase1.py --dry-run`
- [x] Full migration: `python scripts/saber_migrate_phase1.py` -- 2026-10-04

### CPRA Corpus (Priority 1 -- 13 embedded provisions)
- [x] 13/13 provisions migrated
- [x] Lookup table signed -- Architect Ed25519 signature verified 2026-10-04
- [x] Manifest written: manifests/cpra-*.json

### Cal Codes Corpus (Priority 2)
- [x] 0/0 provisions migrated (loader module absent -- valid zero-provision manifest)
- [x] Manifest written

### US Code Corpus (Priority 3)
- [x] 0/0 provisions migrated (submodule absent -- valid zero-provision manifest)
- [x] Manifest written

### CFR Corpus (Priority 4)
- [x] 0/0 provisions migrated (submodule absent -- valid zero-provision manifest)
- [x] Manifest written

---

## 4. POST-MIGRATION VERIFICATION

- [x] Audit chain verified: `python scripts/saber_verify.py` -- 2026-10-04
- [x] All 13 blob hashes verified
- [x] Root hash recorded:
  - Root hash at Phase 1 completion: `00b16be764a7b9d94e9216fafb46be90d624912338d41b8f2ae7b7fdd7ffbe4c`
  - Date: `2026-10-04`
  - Audit entries: 54 (includes initial failed run, signed re-run, verification passes)

---

## 5. PUBLICATION (ELECT-4)

- [x] GitHub repo `SynTechRev/saber-audit-log` created -- https://github.com/SynTechRev/saber-audit-log
- [x] First checkpoint JSON committed -- saber-audit-20261004T210456Z.json (root hash 00b16be7...)
- [x] Daily checkpoint workflow configured -- .github/workflows/daily-checkpoint.yml (06:00 UTC)

---

## 6. TIER 1 ARCADE LAYERS (Can run in parallel with migration)

### A.R.C.A.D.E. Layer 2 -- Supply Chain Security
- [x] .github/workflows/supply_chain.yml written (gitleaks + osv-scanner + Syft SBOM + cosign)
- [x] .pre-commit-config.yaml written (gitleaks + ruff + detect-private-key)
- [x] Install tools: gitleaks v8.30.1 + osv-scanner v2.6.0 -- 2026-10-04
- [x] Install pre-commit hooks: `pre-commit install` -- 2026-10-04
- [ ] Activate workflow: push ODIA repo to GitHub remote

### A.R.C.A.D.E. Layer 13 -- AI Defense
- [x] scripts/arcade_l13_garak.py written (6 OWASP LLM Top 10 probe sets)
- [x] garak 0.17.0 installed in venv -- 2026-10-04
- [x] Probe names corrected to garak 0.17.0 API (promptinject, latentinjection, leakreplay, packagehallucination, web_injection, dan) -- 2026-10-04
- [x] Run launched: `python scripts/arcade_l13_garak.py` -- 2026-10-04 14:39 UTC
      32 DAN attempts, 160 generations -- all returned "DAN Mode enabled" (100% susceptibility)
      5 of 6 probe sets did not run (run terminated after DAN)
- [x] Results analysis written: data/saber/ai-defense/arcade-l13-analysis-20261004.md -- 2026-10-04
      CRITICAL FINDING: ARCADE-L13-001 -- odia-v1 100% susceptible to DAN 11.0 jailbreak
- [ ] Mitigations: system-prompt hardening + output filter in OracRAG + adversarial training for odia-v2
- [ ] Re-run: probes.promptinject, latentinjection, leakreplay, packagehallucination, web_injection

### A.R.C.A.D.E. Layer 14 -- Backup and Recovery
- [x] scripts/arcade_l14_backup.py written (restic wrapper, 3-2-1-1-0 config)
      Updated 2026-10-04: _find_restic() fallback resolves WinGet install path
- [x] Install restic: restic v0.19.1 -- 2026-10-04
- [ ] Set RESTIC_PASSWORD: `[System.Environment]::SetEnvironmentVariable("RESTIC_PASSWORD","YOUR-PASSPHRASE","User")`
- [ ] Init repo: `python scripts/arcade_l14_backup.py --init`
- [ ] First backup: `python scripts/arcade_l14_backup.py --backup`
- [ ] Verify: `python scripts/arcade_l14_backup.py --verify`

---

## 7. ELECT-6 LICENSE FINAL ELECTION

- [x] Phase 1 delivery complete
- [x] Review Apache 2.0 vs MIT for saber/ subpackage
- [x] Final election confirmed: Apache-2.0 for saber/ (elected 2026-10-04)
- [x] saber/__init__.py header updated with SPDX-License-Identifier: Apache-2.0
- [x] saber/LICENSE-Apache-2.0 written
- [x] elections.yaml ELECT_6 finalized

---

## 8. ODIA_LEGAL PHASE 1 REMAINING (Complete)

- [x] L-9 recodification: updated anchors.py -- all 18 Cal. statute strings now use § symbol, CalCitation-compatible -- 2026-10-04
- [x] CPRA crosswalk auto-enrichment: CPRACorpusLoader.resolve_citation() integrated into make_finding() in contra/_utils.py -- 2026-10-04
      234/234 contra + cpra tests passing

---

## 9. ODIA_LEGAL PHASE 2 -- Reasoning Engine (Active)

### L-Detectors Package (src/oraculus_di_auditor/legal/detectors/)

- [x] _base.py: DocContext, LegalFinding, LegalDetector protocol, Severity -- 2026-10-04
- [x] L-1 Statutory Applicability (l1_statutory_applicability.py) -- 2026-10-04
      Tier 1: CPRA baseline. Tier 2: doc-type triggers. Tier 3: content signals (ALPR, FRT, BWC, arbitration, AI).
      22/22 tests passing.
- [x] L-2 Procedural Compliance (l2_procedural_compliance.py) -- 2026-10-04
      PC-1: CPRA 10-day response. PC-2: extension without production date. PC-3: Brown Act 72-hour posting. PC-4: AB 481 annual report.
      14/14 tests passing.
- [x] L-3 Exemption Misapplication (l3_exemption_misapplication.py) -- 2026-10-04
      EX-1: § 7923.600 (law enforcement). EX-2: § 7922.000 (catch-all). EX-3: § 1798.90.55 (FRT). EX-4: § 7927.705 (deliberative). EX-5: A/C privilege.
      18/18 tests passing.
- [x] __init__.py: PHASE2_DETECTORS registry + all exports -- 2026-10-04
- [x] legal/__init__.py updated to re-export Phase 2 detectors -- 2026-10-04
- [x] 188/188 legal module tests passing (all phases) -- 2026-10-04
- [x] L-4: Ministerial Duty Analysis (Cal. Gov. § 815.6, mandatory duty doctrine, ALPR, MRAP, § 832.7) -- 2026-10-04
      MD-1 through MD-5 -- 17/17 tests passing.
- [x] L-5: Federal Grant Compliance (34 USC § 10152/10381, 2 CFR § 200.320, 42 USC § 1983) -- 2026-10-04
      GC-1 through GC-5 -- 21/21 tests passing.
- [x] 221/221 legal module tests passing (all phases) -- 2026-10-04
- [x] L-6: Constitutional Implication (Carpenter mosaic, Fourth/First/14th Amend., Cal. Const.) -- 2026-10-04
      CI-1 through CI-5 -- 21/21 tests passing.
- [x] 242/242 legal module tests passing (L-1 through L-6 + all Phase 1) -- 2026-10-04
- [x] scripts/run_legal_detectors.py written (batch pipeline: --dry-run, --jurisdiction, --limit) -- 2026-10-04
- [x] L-10: Balancing Test Analyzer (Mathews v. Eldridge, CPRA public interest, Carpenter, AB 481) -- 2026-10-04
      BT-1 through BT-5 -- 32/32 tests passing. 274/274 legal module tests total.
- [x] Phase 2 API route: POST /api/v1/legal/detect (single-document L-detector pass) -- 2026-10-04
      Wired directly to PHASE2_DETECTORS. DetectRequest schema: text, document_id, document_hash,
      document_type, jurisdiction, authority, detectors (allow-list). Returns findings sorted by
      severity, counts dict, errors list, detectors_run list. 12/12 route tests passing.

---

## Notes

- The S.A.B.E.R. store lives at: data/saber/store/
- Audit log: data/saber/audit/saber.log
- Manifests: data/saber/manifests/
- Checkpoints: data/saber/checkpoints/
- All paths are relative to repo root
- data/saber/ should be added to .gitignore (runtime artifacts)
  EXCEPT: data/saber/PHASE1_CHECKLIST.md (this file -- tracked in git)
