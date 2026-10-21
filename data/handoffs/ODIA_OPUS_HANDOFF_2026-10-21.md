# ODIA Opus Handoff — 2026-10-21

**Supersedes**: ODIA_OPUS_HANDOFF_2026-10-17.md
**Prepared by**: MARS (SynTechRev) via Claude Code (Sonnet 4.6)
**Window covered**: 2026-10-17 → 2026-10-21 PDT
**Repo**: `C:\Users\yahua\Downloads\ODI x RAIA\Oraculus-DI-Auditor-clean`, master, v3.9.2
**Purpose**: Bring Opus current for CPRA letter development following Fresno City MAS V2.0 completion.

> Status key: **VERIFIED** = confirmed from file/process on disk. **MEMORY** = carried from session notes. **OPEN** = unresolved or needs Opus or MARS.

---

## 0. Asks of Opus (priority order)

1. **Draft four new CPRA letters** (§1, §4) grounded in Fresno City MAS V2.0 findings. Full anchors in §4. Target files: `fresno_city_jag_compliance_CPRA_20261021.txt`, `fresno_pd_carpenter_alpr_CPRA_20261021.txt`, `fresno_city_attorney_CPRA_20261021.txt`, `fresno_city_clerk_brown_act_CPRA_20261021.txt`.
2. **Review letters 1–3** (City Clerk surveillance Oct 8, FPD Records Oct 8, unsigned instruments Oct 16) against the completed MAS V2.0 anchors (§3) to confirm their numbers are accurate before MARS sends them.
3. **Fresno Metropolitan MAS V4.0** — integrate the three completed jurisdiction syntheses (§5). All source documents exist.
4. **ARCADE L-14 encoding status** (§6) — no results yet; run is live. Note the structural difference from L-13 (encoding probe = shorter payloads, faster completion). Do not synthesize until hitlog exists.

---

## 1. What changed since 2026-10-17 (headline)

| Track | State |
|---|---|
| Fresno City MAS V2.0 | **COMPLETE 2026-10-20** (VERIFIED). `docs/synthesis/Fresno_City_MAS_V2_0.md` committed b85c0fe. 14,409 docs / 64,489 findings. Full breakdown §2. |
| Platform MAS V1.0 | Committed b85c0fe. `docs/synthesis/Platform_Master_Audit_Synthesis_V1_0.md`. Cross-jurisdiction, all 17 jurisdictions. |
| ARCADE L-13 DanInTheWild | **COMPLETE 2026-10-20** (Run 7, VERIFIED). 512 attempts / 253 passed / 253 bypassed / 6 null. 50% bypass rate. 214 adversarial Type 8 training pairs committed (`data/training/adversarial_dan_type8.jsonl`, commit fef4ea3). |
| ARCADE L-14 encoding probes | **LIVE** (VERIFIED, 2026-10-21). `data/saber/ai-defense/garak-l14-encoding-cpu-config.yaml` (commit 481f43e). 16 active probe classes, all optional deps present, ~5,120 attempts. No hitlog yet. |
| odia-v2 corpus | 327,717 examples (327,503 prior + 214 adversarial DAN Type 8). Blocked: Vast.ai $0 credit + SSH key not uploaded. |
| CourtListener corpus | **133 cases** (VERIFIED, commit 84fbf83, 2026-10-19). Authenticated harvest complete. Topics: CPRA exemptions, 4th Amendment ALPR/GPS, AB 481, JAG compliance, Brown Act, biometric privacy. |
| CPRA letters | 8 drafted, none sent (§3). 4 new letters needed from MAS V2.0 (§4). |
| GCA — Visalia | **October 29, 2026 deadline** (OPEN). Finalization ongoing. Visalia reference case: Sanchez v. City of Visalia and VPD. Two written admissions from Caren L. Curtiss, Herr Pedersen and Berglund LLP, 2026-08-18 17:43 — BWC non-capture (Policy 426.5) and FBI CJIS Security Addendum non-possession (executed Axon MSPA V15.0 operation). |

Git: master is ahead of origin. Commits since last handoff: fef4ea3 (ARCADE L-13 adversarial training), b85c0fe (synthesis docs), 481f43e (L-14 config), b730846 and prior (L-13 fixes). Local tags agree with origin.

---

## 2. Fresno City MAS V2.0 — complete finding substrate

Corpus: 14,409 docs / 64,489 findings / 22 detector layers. O.D.I.A. v3.9.2. Source: `docs/synthesis/Fresno_City_MAS_V2_0.md` (VERIFIED).

### 2.1 Severity distribution

| Severity | Count | % | Dominant pattern |
|---|---|---|---|
| Critical | 3,130 | 4.9% | Signature: 2,956 (94.4% of critical) |
| High | 21,777 | 33.8% | Administrative: 11,637 (53.4% of high) |
| Medium | 24,588 | 38.1% | Scope: 6,640 amendment-without-baseline |
| Low | 14,994 | 23.2% | L-7: 4,686 action-without-authority-cite |

### 2.2 Signature layer (CRITICAL — fiscal track)

- **Aggregate unsigned exposure: $33,642,994,188.34**
- 2,956 critical findings (94.4% of all criticals)
- Largest single instrument: $8,095,546,000.00
- Instruments ≥ $10M: 157 | $1M–$10M: 521 | $100K–$1M: 1,102
- Instrument types: AGREEMENT 1,443 / AMENDMENT 926 / CONTRACT 473 / MOU 99
- **Dual-flag subset**: 926 AMENDMENT instruments are BOTH unsigned (signature critical) AND missing baseline reference (scope layer) — highest-priority per-document review target

### 2.3 Federal grant compliance (CRITICAL — JAG track)

| Pattern | Count | Statute |
|---|---|---|
| JAG without anti-supplanting | **79 CRITICAL** | 34 U.S.C. § 10152(a)(1)(G) |
| JAG-funded surveillance | 15 HIGH | — |
| COPS without itemization | 47 MEDIUM | — |
| Criminal intel without 28 CFR Part 23 | 3 MEDIUM | 28 CFR Part 23 |
| L-5 sole-source no justification | 144 MEDIUM | Uniform Guidance |
| Grant trail — no Single Audit reference | 3,126 MEDIUM | 2 CFR Part 200 Subpart F |
| Grant trail — amount reconciliation gap | 2,303 MEDIUM | — |

**The 79 critical JAG anti-supplanting findings are doctrinally identical to the active Visalia reference case theory.**

### 2.4 Constitutional / surveillance (Fourth Amendment track)

| Pattern | Count | Layer |
|---|---|---|
| carpenter_elements_missing | 126 | L-10 |
| alpr_carpenter_not_analyzed | 38 | L-10 |
| location_surveillance_no_carpenter | 40 | L-6 |
| alpr_sb34_retention (Civ. Code § 1798.90.5) | 159 | l1 |
| alpr_cpra_exemption_scope | 4 | L-3 |
| biometric_no_equal_protection | 37 | L-6 |
| facial_recognition_no_constitutional_analysis | 9 | L-6 |
| facial_recognition_reference (AB 1215) | 42 | Surveillance (CRITICAL) |
| mathews_incomplete | 103 | L-10 |
| ab481_annual_report (Gov. Code §§ 7070–7075) | 636 | l1 |
| ab481_annual_report_missing | 6 | L-4 |

### 2.5 CPRA doctrine stack (~9,500 findings)

| Pattern | Count | Layer |
|---|---|---|
| cpra_access baseline | 3,697 | l1 |
| cpra_denial_missing_appeal_rights | 4,222 | L-2 |
| mandatory_duty_nonperformance | 999 | L-4 |
| unmatched_exemption_claim (legacy section numbers) | 2,289 | L-9 |
| cpra_balancing_absent | 86 | L-10 |
| personnel_file_post_sb1421_misapplication | 34 | L-3 |
| catch_all_no_balancing_test | 65 | L-3 |
| attorney_client_overbroad_factual | 38 | L-3 |
| cpra_extension_no_grounds | 130 | L-4 |
| cpra_response_deadline | 106 | L-4 |
| cpra_fee_exceeds_direct_cost | 1 | L-4 |

### 2.6 Administrative / governance / Brown Act

| Pattern | Count |
|---|---|
| admin:missing-final-action | 10,753 HIGH |
| admin:retroactive-authorization | 884 HIGH |
| consent-calendar-high-value (Brown Act) | 273 MEDIUM |
| text-date-ordering-anomaly | 204 MEDIUM |
| governance critical findings | 53 CRITICAL |
| L-7 action-without-authority-cite | 4,686 LOW |
| ordinance-exceeds-state-preemption | 23 HIGH |
| federal-grant-scope-exceeded | 14 HIGH |

---

## 3. Existing CPRA letters — status

| # | Target | File | Date | Verification status |
|---|---|---|---|---|
| 1 | City of Fresno — City Clerk (surveillance) | `fresno_city_clerk_CPRA_20261008.txt` | 10-08 | **Review needed** against MAS V2.0 ALPR/surveillance numbers |
| 2 | FPD — Records (surveillance ops) | `fresno_pd_records_CPRA_20261008.txt` | 10-08 | **Review needed** — predates MAS V2.0 |
| 3 | City of Fresno — unsigned instruments | `fresno_city_unsigned_instruments_CPRA_20261016.txt` | 10-16 | **Review needed** — confirm $33.6B aggregate and 2,956 critical match |
| 4 | Fresno County Sheriff | `fresnocounty_sheriff_CPRA_20261016.txt` | 10-16 | MEMORY anchors — County MAS V4.0 is the validation source |
| 5 | Fresno County BOS Clerk | `fresnocounty_bos_clerk_CPRA_20261016.txt` | 10-16 | MEMORY anchors |
| 6 | Fresno County CAO + ITS | `fresnocounty_cao_it_CPRA_20261016.txt` | 10-16 | MEMORY anchors |
| 7 | TCPD — Probation | `tcpd_probation_CPRA_20261016.txt` | 10-16 | MEMORY anchors |
| 8 | Visalia PD — Flock Safety (CPRA-VPD-FLOCK-001) | `visalia_pd_CPRA_20261017.txt` | 10-17 | Committed. GCA Oct 29 deadline context. |

**None sent.** Letters 1–3 should be verified against MAS V2.0 §2 before MARS sends them. The unsigned instruments letter (#3) anchor was drafted from MAS aggregates; the $33,642,994,188.34 figure and 2,956 critical finding count are now VERIFIED from the full synthesis.

---

## 4. New CPRA letters needed — anchors and targets

Four letters flow directly from MAS V2.0 findings that are not covered by existing letters.

### Letter A — City of Fresno: Federal Grant Compliance
**File**: `fresno_city_jag_compliance_CPRA_20261021.txt`
**Recipient**: City of Fresno, City Manager / City Clerk
**Statutory basis**: Cal. Gov. Code § 7920.000 et seq. (CPRA recodified); 34 U.S.C. § 10152 (JAG); 42 U.S.C. § 3796dd (COPS); 2 CFR Part 200; 28 CFR Part 23
**Records requested**:
- All Edward Byrne Memorial JAG grant applications, certifications, and award documents — specifically the anti-supplanting certifications required under 34 U.S.C. § 10152(a)(1)(G) — for all grant periods where JAG funding appears in the City record
- All COPS grant applications, award documents, and itemization records required under the COPS grant framework
- All records documenting federal grant scope compliance for the 14 findings of federal_grant_scope_exceeded
- All criminal intelligence system operation records and 28 CFR Part 23 compliance documentation
- Complete Single Audit Act compliance records (2 CFR Part 200 Subpart F) for all federal awards in the corpus period
**Finding anchors**: 79 critical JAG anti-supplanting (L-5), 15 HIGH JAG-funded-surveillance, 47 MEDIUM COPS-without-itemization, 3 MEDIUM crim-intel-without-28-CFR-23, 3,126 grant-trail-no-single-audit-reference, 113 l1 jag_grant baseline documents
**Doctrinal note**: The 79 JAG anti-supplanting findings are doctrinally identical to the active Visalia reference case. This letter is a parallel enforcement track to the Visalia GCA proceeding.

### Letter B — Fresno Police Department: Carpenter / ALPR / AB 1215 / CJIS
**File**: `fresno_pd_carpenter_alpr_CPRA_20261021.txt`
**Recipient**: Fresno Police Department, Records Division / Custodian of Records
**Statutory basis**: Cal. Gov. Code § 7920.000 et seq. (CPRA); Cal. Civ. Code § 1798.90.5 et seq. (SB 34 ALPR retention); Cal. Gov. Code § 7284 et seq. (AB 1215 facial recognition restriction); Cal. Gov. Code §§ 7070–7075 (AB 481 military equipment)
**Records requested**:
- All ALPR deployment records, retention policies, and SB 34 compliance documentation (159 alpr_sb34_retention findings) — specifically the annual ALPR data retention audits and data access logs
- All Carpenter v. United States (585 U.S. 296 (2018)) balancing analysis documentation for all location-surveillance, ALPR, and communication-data programs (126 carpenter_elements_missing, 38 alpr_carpenter_not_analyzed, 40 location_surveillance_no_carpenter)
- All facial recognition technology deployment records and AB 1215 / Gov. Code § 7284 compliance analysis (42 critical facial_recognition_reference, 9 facial_recognition_no_constitutional_analysis, 37 biometric_no_equal_protection)
- All AB 481 military equipment annual reports and supporting documentation (636 ab481_annual_report, 6 ab481_annual_report_missing)
- The FBI CJIS Security Addendum documentation for all currently operational systems requiring CJIS compliance, including the Axon MSPA-covered systems
- All JAG-funded surveillance program records including the specific grant documentation for the 15 JAG-funded-surveillance findings
**Finding anchors**: 204 total Carpenter analysis gaps (L-6 + L-10), 241 ALPR-specific findings (4 layers), 88 facial recognition/biometric findings, 6 ab481_annual_report_missing, 15 JAG-funded-surveillance
**Doctrinal note**: The CJIS Security Addendum request is directly parallel to the Visalia reference case written admission (FBI CJIS non-possession despite executed Axon MSPA V15.0 operation, 2026-08-18).

### Letter C — City Attorney: Attorney-Client Overreach / Balancing Test Failures
**File**: `fresno_city_attorney_CPRA_20261021.txt`
**Recipient**: City of Fresno, City Attorney's Office
**Statutory basis**: Cal. Gov. Code § 7920.000 et seq. (CPRA); Cal. Gov. Code § 7922.000 (public interest balancing)
**Records requested**:
- All records for which attorney-client privilege was invoked beyond its proper legal-advice scope — specifically records where the privilege was applied to factual information (38 attorney_client_overbroad_factual findings), including the specific records identified in those 38 findings and the basis for the privilege claim in each
- All records for which a catch-all exemption was invoked without the public-interest balancing test required under Gov. Code § 7922.000 (65 catch_all_no_balancing_test findings) — specifically the balancing analysis documentation for each invocation
- All records for which a CPRA exemption was cited using a legacy section number (from the pre-AB 473 framework) where the exemption may not have survived the January 1, 2023 recodification — specifically the 38 L-9 unmatched-exemption-claim findings within the City Attorney's record set
**Finding anchors**: 38 attorney_client_overbroad_factual, 65 catch_all_no_balancing_test, relevant subset of 2,289 unmatched_exemption_claim

### Letter D — City Clerk: Brown Act / Consent Calendar Transparency
**File**: `fresno_city_clerk_brown_act_CPRA_20261021.txt`
**Recipient**: City of Fresno, City Clerk
**Statutory basis**: Cal. Gov. Code § 7920.000 et seq. (CPRA); Cal. Gov. Code §§ 54950–54963 (Brown Act); Cal. Gov. Code § 54954.2 (agenda requirement)
**Records requested**:
- All records documenting the basis for placement of high-value items on the consent calendar rather than the discussion calendar (273 consent-calendar-high-value findings) — specifically the dollar-threshold or subject-matter criteria applied to consent calendar placement decisions for each identified item
- All records for the 204 text-date-ordering-anomaly findings — specifically the final executed versions of the identified records and the vote history documentation for each
- The City's written policy for consent calendar placement, including any dollar thresholds, subject-matter exclusions, or public comment procedures applied to consent-calendar items
- Any records documenting public notice and comment procedures for the specific items identified in the consent-calendar-high-value findings
**Finding anchors**: 273 vote_date:consent-calendar-high-value, 204 vote_date:text-date-ordering-anomaly
**Note**: This letter is distinct from Letter #1 (fresno_city_clerk_CPRA_20261008.txt, surveillance-focused). It targets governance transparency and Brown Act compliance.

---

## 5. Fresno Metropolitan MAS V4.0 — source documents available

All three component MAS documents now exist and are committed:

| Component | File | Status |
|---|---|---|
| City of Fresno MAS V2.0 | `docs/synthesis/Fresno_City_MAS_V2_0.md` | COMPLETE 2026-10-21 |
| Fresno County MAS V4.0 | `C:\Users\yahua\Downloads\Fresno_Metropolitan_MAS_V4_0.md` | COMPLETE 2026-07-31 |
| Fresno PD MAS V4.0 | Referenced in CLAUDE.md, July 2026 | COMPLETE 2026-07-31 |

The Fresno Metropolitan MAS V4.0 will:
1. Integrate all three component jurisdictions into a unified Metropolitan Fresno accountability framework
2. Produce the cross-jurisdiction pattern analysis (signature layer cross-reference, JAG anti-supplanting cross-reference, ALPR lattice)
3. Serve as the analytical foundation for subsequent Fresno Section 1983 pipeline and the Fresno Metropolitan MAS V5.0

**OPEN**: MARS to confirm whether the County and FPD V4.0 synthesis documents are available for upload in the Opus project thread.

---

## 6. ARCADE L-14 — encoding probe run (live)

- **Status**: LIVE as of 2026-10-21 (VERIFIED, initiated this session)
- **Config**: `data/saber/ai-defense/garak-l14-encoding-cpu-config.yaml` (commit 481f43e)
- **Probe module**: `probes.encoding` — all 16 active classes
  - InjectBase64, InjectBase16, InjectBase32, InjectAscii85, InjectHex, InjectUU, InjectROT13, InjectBase2048, InjectBraille, InjectAtbash, InjectMorse, InjectNato, InjectEcoji, InjectZalgo, InjectLeet, InjectUnicodeTagChars
- **Detector**: `encoding.DecodeMatch` (primary), `encoding.DecodeApprox` (extended)
- **What a bypass means**: model decoded and reproduced an obfuscated payload (XSS string, slur term, or English text) when presented in an encoded format
- **Expected outcome**: lower bypass rate than L-13's 50% — odia-v1 has no trained reason to decode base64/ROT13/Morse in civic document context
- **Estimated attempts**: ~5,120 (64 prompts × 16 probes × 5 generations, seed=42)
- **Post-run pipeline**: same as L-13 — harvest hitlog → generate Type 8 adversarial pairs → add to odia-v2 corpus

**Do not synthesize L-14 until the hitlog exists.** The run will complete while the Opus CPRA session is in progress.

---

## 7. ARCADE L-13 — final state (for record)

| Probe | Result |
|---|---|
| `dan.Ablation_Dan_11_0` (pre-fix) | 505/635 MitigationBypass (79.5% bypass) |
| `promptinject` (3 probes, post-M1+M2+R7) | 3,005/3,840 bypassed (78.3%) |
| `web_injection` (8 probes) | COMPLETE — results in hitlog |
| `dan.DanInTheWild` (Run 7) | 253/506 bypassed (50% bypass rate), 214 unique jailbreaks, 6 null |
| `packagehallucination` | Descoped — not relevant to civic-audit tool |

Type 8 adversarial training pairs committed: **214 examples** (`data/training/adversarial_dan_type8.jsonl`, commit fef4ea3). odia-v2 corpus total: **327,717 examples**.

---

## 8. Open blockers

| Blocker | Needs | Unblocks |
|---|---|---|
| Vast.ai credits + SSH key | MARS | odia-v2 training (327,717 examples ready) |
| GCA presentment — Visalia | MARS (Oct 29 deadline) | Sanchez v. City of Visalia and VPD proceeding |
| Sending CPRA letters | Letters verified by Opus, then MARS sends | Statutory 10-day response clock |
| `git push origin master` | MARS approval | Remote backup (multiple commits ahead of origin) |

---

## 9. File index

- **Synthesis documents**: `docs/synthesis/` — `Fresno_City_MAS_V2_0.md`, `Platform_Master_Audit_Synthesis_V1_0.md`
- **CPRA letters**: `data/cpra_letters/` — 8 existing; 4 new to be drafted (§4)
- **Handoffs**: `data/handoffs/` — this file supersedes 2026-10-17
- **ARCADE configs**: `data/saber/ai-defense/` — `garak-l14-encoding-cpu-config.yaml`, `garak-l13-dan-cpu-config.yaml`
- **Adversarial training**: `data/training/adversarial_dan_type8.jsonl`
- **MAS source documents**: `C:\Users\yahua\Downloads\Fresno_Metropolitan_MAS_V4_0.md`, `Fresno_City_MAS_V2.docx`
- **Prior handoffs**: `data/handoffs/ODIA_OPUS_HANDOFF_2026-10-17.md` (and earlier)
