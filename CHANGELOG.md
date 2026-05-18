# Changelog

## [3.1.1] - 2026-05-17 — HTML ingest support (unblocks WordPress / press-release jurisdictions)

Surfaced while bringing up the Tulare County DA (TCDA) scrape — their portal is a WordPress site exposing 667 press releases as HTML pages, not PDFs. The v3.0.x pipeline had two blockers that would have silently failed:

1. **`_run_scrape_job_background` force-appended `.pdf`** to any filename not ending in `.pdf`. HTML bytes from an HTML URL got tempfile'd with `.pdf` suffix, routed through the PDF parser, returned an error string, and the audit ran on near-empty text → ~0 anomalies (silent failure).
2. **`ingest_uploaded_file` had no `.html`/`.htm` branch.** Even if the suffix were preserved, the ingestion engine would fall through every if/elif without populating `text`, leaving `text=""` for the audit. Same silent failure mode.

### Added — HTML branch in `ingest_uploaded_file`

[src/oraculus_di_auditor/interface/routes/upload.py](src/oraculus_di_auditor/interface/routes/upload.py): when extension is `.html` or `.htm`, parse with BeautifulSoup (already in deps), strip `script`/`style`/`noscript`/`nav`/`footer`/`aside` tags wholesale, then extract text via `soup.get_text(separator="\n", strip=True)`. Falls back to raw text read on parse failure so the audit always gets *some* signal. Keeps detector input focused on the actual article body / press-release prose, not navigation chrome or inline JS.

### Refactor — smarter filename-suffix logic in async worker

[src/oraculus_di_auditor/interface/routes/webhook.py](src/oraculus_di_auditor/interface/routes/webhook.py) `_run_scrape_job_background`:

- If `filename_hint` already has a recognised extension (`.pdf`, `.json`, `.xml`, `.txt`, `.html`, `.htm`), preserve it
- Otherwise, sniff the first 16 bytes of the downloaded body and pick the right extension:
  - `%PDF-` → `.pdf`
  - `<!doctype` / `<html` → `.html`
  - `<?xml` → `.xml`
  - `{` / `[` → `.json`
  - fallback → `.pdf` (conservative, preserves v3.0.x scraping-PDFs behaviour)

Means TCDA-style HTML URLs work without any per-caller extension handling, AND v3.0.x PDF-scraping behaviour is preserved exactly when callers don't pass a filename_hint.

### Tests

Three new tests in [tests/test_webhook_scrape_async.py](tests/test_webhook_scrape_async.py):
- `test_worker_handles_html_with_html_filename_hint` — primary v3.1.1 regression guard. Feeds a tiny HTML payload (with `<nav>` and `<footer>` cruft that must be stripped) through the worker, asserts the audit runs end-to-end AND produces > 0 findings (proves text extraction reached the detectors).
- `test_worker_sniffs_html_bytes_without_filename_hint` — magic-byte sniffer picks `.html` from `<!DOCTYPE` opener with no filename hint.
- `test_worker_sniffs_pdf_bytes_without_filename_hint` — backward-compat: `%PDF-` opener still resolves to `.pdf`.

### Version sync

`pyproject.toml` `version = "3.1.1"` (was 3.1.0). `desktop/package.json` `"version": "3.1.1"`. `api.py` + `webhook.py` `ODIA_VERSION` fallbacks → 3.1.1. Three frontend version strings → v3.1.1.

### Notes

- BeautifulSoup4 was already a dep (added for Sprint F Legistar adapter), no new pip install needed for operators.
- HTML ingest unblocks not just TCDA but ANY WordPress / Drupal / static-site-rendered government portal where press releases or notices are HTML pages rather than PDFs.
- Detector profile on HTML content differs from PDF contracts — expect more `governance:*` / `admin:*` / `surveillance:*` findings, fewer `signature:*` / `procurement:*` ones (prosecutors announce charges/policies; they don't sign contracts).

## [3.1.0] - 2026-05-17 — Fingerprint-resistant fetcher (defeats Akamai / Cloudflare bot blocks)

First minor-version bump in the v3.x line. Adds a two-tier HTTP fetcher to the async scraper so backend-side ingest works against Akamai-protected and similarly hardened municipal sites that pre-v3.1.0 returned HTTP 403 to Python's `urllib` because of TLS/JA3 + HTTP/2 fingerprint inspection. Observed live during v3.0.x bring-up against `tulare.ca.gov` (AkamaiGHost — blocked bare `curl`, browser-UA `curl`, AND browser-UA+Referer `curl` all returned 403 because the gate is at the handshake layer, not the header layer).

### Added — two-tier `_fetch_url(url, *, timeout=120)` helper

New module-level function in [src/oraculus_di_auditor/interface/routes/webhook.py](src/oraculus_di_auditor/interface/routes/webhook.py). Behaviour:

- **Tier 1 — `urllib.request.urlopen` + Chrome-like headers.** Fast, dep-free, succeeds against ~80% of public-records sites (Revize, basic CivicPlus, sites without aggressive bot mitigation). This is the v3.0.x default path, retained as Tier 1 so the common case pays zero overhead.
- **Tier 2 — `curl_cffi` with `impersonate="chrome131"`.** Activated automatically when Tier 1 returns HTTP 403 or 429 (`_TIER1_FALLBACK_HTTP_CODES`), OR fails with a connection-class `OSError` (TLS reset, `RemoteDisconnected`, DNS, timeout). `curl_cffi` ships libcurl-impersonate which replicates Chrome's exact TLS+HTTP2 fingerprint, defeating JA3/JA4 inspection + HTTP/2 frame-order inspection used by Akamai Bot Manager and hardened Cloudflare configurations.
- **Real upstream errors propagate unchanged.** A genuine 404 / 401 / 500 from Tier 1 is NOT a bot block — it propagates immediately without wasting a Tier 2 attempt.
- **Graceful degrade when `curl_cffi` is absent.** Lazy import inside the helper; on ImportError the original Tier 1 exception is re-raised so the operator sees the real underlying problem.

### Added — `curl-cffi>=0.7.0` dependency

Pip-installable, no system binary required (bundles its own `libcurl-impersonate`). Adds ~25 MB to the wheel. Loaded lazily inside `_fetch_url` so non-scraping deployments pay no import-time cost.

### Refactor — `_run_scrape_job_background` worker simplified

The async worker now calls `_fetch_url(url)` instead of inlining the `urllib.request.urlopen` block. Same `_DOWNLOAD_SEMAPHORE` wraps the whole fetch attempt (concurrency throttle covers both tiers). Browser headers lifted to module-level `_BROWSER_HEADERS` constant so tests + future fetchers share one source of truth.

### Tests

Seven new tests in [tests/test_webhook_scrape_async.py](tests/test_webhook_scrape_async.py) covering the fetcher tier logic:

1. `test_fetch_url_tier1_happy_returns_bytes` — Tier 1 success short-circuits before Tier 2
2. `test_fetch_url_tier1_403_falls_through_to_tier2_success` — primary Akamai-bypass scenario
3. `test_fetch_url_tier1_429_falls_through_to_tier2` — rate-limit fallback
4. `test_fetch_url_tier1_404_does_not_fall_through` — real upstream errors propagate immediately
5. `test_fetch_url_tier1_oserror_falls_through_to_tier2` — connection-class failures
6. `test_fetch_url_both_tiers_fail_raises_oserror_with_context` — error message names both failures
7. `test_fetch_url_no_curl_cffi_reraises_tier1_error` — graceful degrade without the dep

Three existing v3.0.4 worker failure-path tests updated to patch `_fetch_url` directly (cleaner separation: those tests exercise worker behaviour, not fetcher internals). All other tests unchanged.

### Version sync

`pyproject.toml` `version = "3.1.0"` (was 3.0.5). `desktop/package.json` `"version": "3.1.0"`. `api.py` + `webhook.py` `ODIA_VERSION` fallbacks → 3.1.0. Three frontend version strings → v3.1.0.

### Notes for operators

- Existing deployments need `pip install curl-cffi>=0.7.0` to enable Tier 2. Without it, behaviour is identical to v3.0.5 (urllib only). The release workflow rebuilds the PyInstaller wheel with the new dep; manual upgrades from source need the pip install.
- The semaphore (`Semaphore(4)`) cap applies to the WHOLE fetch attempt — switching tiers does not multiply effective concurrency.
- Tier-2 is gated to 403/429/OSError specifically because those are the bot-mitigation signatures observed in v3.0.x bring-up. Sites with other rejection patterns can be added by widening `_TIER1_FALLBACK_HTTP_CODES`.
- For Playwright/headless-browser Tier 3 (defeats remaining JS-execution-gate scrapers like some Granicus deployments), see future v3.2+ work — requires ~250 MB Chromium download and OS-level deps, so not bundled by default.

## [3.0.5] - 2026-05-17 — RAIA pattern detection completeness + synthesis_id consistency

Two minor polish items surfaced during the first real RAIA cross-jurisdiction synthesis run (Visalia + Porterville, 2026-05-17 ~16:53 UTC). Neither blocks functionality but both made the cross-jurisdiction report less informative than the underlying data warranted.

### Fixed — pattern detection iterated capped `top_anomalies`, missed shared finding IDs
- `_shared_anomaly_ids` and `_vendor_convergences` in [src/oraculus_di_auditor/raia/patterns.py](src/oraculus_di_auditor/raia/patterns.py) iterated each jurisdiction's `top_anomalies` (default cap: 10). Any finding ID outside that window was invisible to cross-jurisdiction matching. **Observed live**: raw SQL on the Visalia+Porterville DB showed 8 detector IDs firing in both jurisdictions, but the v3.0.4 RAIA report surfaced only 2 of them. The other 6 (`procurement:auto-renewal-clause`, `governance:auto-renewal-clause`, four `sole-source-*` variants, `scope:significant-expansion`, `scope:sole-source-expansion`) all sat past Visalia's top-10 cut-off because that cut-off was dominated by CRITICAL `signature:unsigned-instrument` entries plus high-frequency `admin:missing-final-action` ones.
- Fix: added `all_anomalies: list[AnomalyRow]` field to `JurisdictionSummary` in [src/oraculus_di_auditor/raia/schemas.py](src/oraculus_di_auditor/raia/schemas.py). `RAIAService._build_summary` now populates this with the full unsliced anomaly list. Pattern detectors iterate `all_anomalies` (falling back to `top_anomalies` for backward compat with hand-built test summaries). `top_anomalies` remains as-is for display rendering — only pattern matching widens its window.
- The new field is deliberately excluded from `JurisdictionSummary.to_dict()` so the webhook JSON response stays compact (otherwise a 1000-anomaly jurisdiction would multiply the response payload).
- Same fix applied to vendor convergence: vendor mentions like `surveillance:vendor-detected:axon-enterprise` typically sit at LOW severity (below CRITICAL/HIGH structural defects) and were invisible to vendor-convergence detection pre-v3.0.5.

### Fixed — `synthesis_id` mismatch between webhook JSON and rendered markdown
- The `/api/v1/webhook/synthesize` route generated a `synthesis_id` (`secrets.token_hex(8)`) and called `_run_raia_synthesis` to render the markdown. The route then overrode `result_dict["synthesis_id"] = synthesis_id` AFTER the markdown was already rendered. Result: the JSON response carried the route's ID while the rendered `.md` embedded `RAIAService`'s internally-generated one. Cosmetic but operators correlating webhook responses to downloaded reports would see two different IDs.
- Fix: `_run_raia_synthesis` gains an optional `synthesis_id_override: str | None = None` parameter. When provided, it's applied to the `RAIAResult` BEFORE `render_markdown_template()` is called. The route now passes its synthesis_id into the helper rather than overriding after the fact.

### Tests
- 3 new tests in [tests/test_raia_service.py](tests/test_raia_service.py):
  - `test_shared_anomaly_surfaces_outside_top_n_via_all_anomalies` — primary regression guard for the pattern-detection bug
  - `test_vendor_convergence_surfaces_outside_top_n_via_all_anomalies` — same for vendor convergence
  - `test_pattern_detection_falls_back_to_top_anomalies_when_all_empty` — backward-compat with legacy test fixtures
- 1 new test in [tests/test_webhook_ingest.py](tests/test_webhook_ingest.py): `test_synthesize_markdown_embeds_route_synthesis_id_not_internal_one` — regression guard for the synthesis_id reorder.
- All existing RAIA + synthesize tests untouched and still passing.

### Version sync
- `pyproject.toml` `version = "3.0.5"` (was 3.0.4). `desktop/package.json` `"version": "3.0.5"`. `api.py` + `webhook.py` `ODIA_VERSION` fallbacks → 3.0.5. Three frontend version strings → v3.0.5.

### Notes
- This polish unblocks meaningful cross-jurisdiction synthesis at any scale. With 2 jurisdictions the v3.0.4 RAIA missed 75% of shared finding IDs; with 3+ jurisdictions the proportion missed would have grown as more long-tail detectors became "shared". v3.0.5 makes RAIA scale linearly with jurisdiction count instead of being capped by per-jurisdiction display ranking.
- v3.1.0 (next) introduces a fingerprint-resistant fetcher (`curl_cffi` as Tier 2 behind the current `urllib` Tier 1) to make backend-side scraping work against Akamai/Cloudflare-protected municipal sites that currently 403 our Python urllib requests (observed against Tulare CA earlier in v3.0.x bring-up).

## [3.0.4] - 2026-05-17 — Async worker hardening (RemoteDisconnected catch + download throttle)

Polish release on v3.0.3 driven by a defect surfaced during v3.0.3 first-light validation. Firing 84 parallel scrape jobs at Visalia exposed two real-world failure modes that the unit tests hadn't covered.

### Fixed — `_run_scrape_job_background` exception handler too narrow
- The v3.0.3 catch was `(urllib.error.URLError, urllib.error.HTTPError, TimeoutError)`. `http.client.RemoteDisconnected` is a `ConnectionResetError` → `OSError`, **not** a `URLError` — when Cloudflare TCP-reset some connections under parallel load the exception escaped the worker, crashed the daemon thread, and left the job stuck at `status="downloading"` in the in-memory registry forever (no `failed` transition, no poll signal). The widened catch is now `except OSError` — `URLError`, `HTTPError`, `TimeoutError`, `RemoteDisconnected`, `ConnectionResetError`, DNS errors, etc. all funnel through the same `state["status"] = "failed"` path.
- New regression tests in `tests/test_webhook_scrape_async.py`:
  - `test_worker_marks_failed_on_remote_disconnected` — raises `http.client.RemoteDisconnected` from the mocked `urlopen`; asserts the worker does NOT propagate the exception and that `state["status"] == "failed"` with the error captured.
  - `test_worker_marks_failed_on_generic_oserror` — belt-and-braces with a bare `OSError` to cover DNS / broken-pipe / connection-refused variants.

### Added — `_DOWNLOAD_SEMAPHORE = threading.Semaphore(4)`
- Module-level throttle in `src/oraculus_di_auditor/interface/routes/webhook.py`. The `urllib.request.urlopen` call in `_run_scrape_job_background` is wrapped with `with _DOWNLOAD_SEMAPHORE:`, capping concurrent outbound downloads at 4 regardless of how fast n8n enqueues. Audit work happens **after** the `with` block, so multi-doc audits still run in parallel — only the network read is throttled.
- The cap is a soft etiquette signal toward upstream (CivicPlus / Cloudflare-fronted public-records sites observably rate-limit at higher concurrency). Matches the v3.0.2 shell script's polite pacing without needing the script's per-call `sleep 1`.
- The constant `_DOWNLOAD_CONCURRENCY = 4` is module-level so future jurisdictions with different upstream tolerance can override it via a single edit.
- `test_download_semaphore_is_module_level_and_sized` smoke-tests both invariants.

### Tidy
- `import threading` lifted to module top alongside the other stdlib imports; the lazy `import threading` inside `_enqueue_scrape_job` is now redundant and removed.
- `import urllib.error` inside `_run_scrape_job_background` removed (unused after the catch widened to `OSError`).

### Tests
- 15 tests in `tests/test_webhook_scrape_async.py` (12 from v3.0.3 + 3 new). All 15 green. Sync `/scrape-and-ingest` tests untouched and still 10/10. Ruff clean.

### Version sync
- `pyproject.toml` `version = "3.0.4"`. `desktop/package.json` `"version": "3.0.4"`. `api.py` + `webhook.py` ODIA_VERSION fallbacks → 3.0.4. Three frontend version strings → v3.0.4.

### Notes
- The sync `/scrape-and-ingest` endpoint at v3.0.2 has the same narrow exception handler, but its failure mode is benign — a `RemoteDisconnected` there raises a 500 the caller sees immediately rather than leaking a zombie job. Deliberately not patched here to keep the v3.0.x sync interface stable.
- The semaphore is process-local. A multi-worker `uvicorn --workers N` deployment effectively gets `N × 4` outbound slots, which is fine — the etiquette goal is "don't blast 84 at once from one process", not "global rate limit".

## [3.0.3] - 2026-05-16 — Async Scrape Endpoint (n8n never times out on large PDFs)

Follow-up to v3.0.2's backend-side scraping. The synchronous `/webhook/scrape-and-ingest` blocks the HTTP connection for the full download + audit duration; large agenda packets (Visalia item 12 was an 18 MB PDF) push past n8n's 180 s HTTP node timeout and the request dies even though the backend was still working. v3.0.3 adds a fire-and-forget variant that hands the caller a job ID immediately and runs the work on a daemon thread.

### Added — `POST /api/v1/webhook/scrape-and-ingest-async`
- New endpoint at `src/oraculus_di_auditor/interface/routes/webhook.py`. Body is identical to `/scrape-and-ingest`: `{"url": "...", "jurisdiction_id": "...", "filename_hint": "..."}`. Returns HTTP 202 with `{"status": "accepted", "job_id": "...", "url": "...", "poll_url": "/api/v1/webhook/status/{job_id}"}` in well under 100 ms — n8n's HTTP node sees its response and moves on regardless of how big the upstream PDF is.
- Backend work runs on a `threading.Thread(daemon=True)` worker (`_run_scrape_job_background`) that walks the same `_dedup_check` → `_run_tier1_pipeline` → `_record_seen_hash` → `_persist_tier1_result` chain as the sync endpoint, updating `_BATCH_JOBS[job_id]["status"]` through `queued → downloading → auditing → completed | failed` so polls can observe progress.
- Reuses the existing `GET /api/v1/webhook/status/{job_id}` endpoint — no separate scrape-status route. Returns the full job state (job_id, type=scrape, status, url, jurisdiction_id, sha256, filename, result, error, already_seen) on demand; 404 on unknown ID.
- **Threading note**: `db/session.py` already opens SQLite with `connect_args={"check_same_thread": False}` for tests, so the worker can use the same `get_db()` context manager from a non-request thread. The job registry is process-local (in-memory `_BATCH_JOBS`); a multi-worker deployment would back this with Redis or a jobs table.

### Added — `data/n8n-workflows/wf-001-visalia-url-async.json`
- New WF-001 variant. Identical to the v3.0.2 URL variant except:
  - POSTs `/webhook/scrape-and-ingest-async` instead of `/scrape-and-ingest`
  - HTTP node timeout dropped 180 s → 10 s (the call resolves in ~30 ms)
  - Batching loosened: 5 per second instead of 3 per 2 s (no per-call audit wait)
- Does NOT include a poll/notify branch. For first-light, "enqueue 84 jobs in under 30 s and let the backend chew" is the goal; per-doc completion visibility can be added as a separate workflow if needed.
- Both URL variants are kept in-repo (per the `data/n8n-workflows/` operator-state policy these are `.gitignored` and only ship in `bundle.json`, but the source-of-truth JSON lives here for reference).

### Tests — `tests/test_webhook_scrape_async.py`
- 12 new tests across four sections: endpoint accept-and-dispatch (5 — happy path returns 202 + job_id, auth/validation rejections), background worker behaviour driven synchronously for determinism (4 — happy path, urlopen failure, empty body, dedup short-circuit), status polling (2 — 404 for unknown job, state passthrough for seeded job), end-to-end through the real thread with bounded poll loop (1).
- **12/12 green.** Mocks `urllib.request.urlopen` so tests never hit the network; clears `_BATCH_JOBS` between tests via an autouse fixture.

### Version sync
- `pyproject.toml` `version = "3.0.3"` (was 3.0.2).
- `desktop/package.json` `"version": "3.0.3"`.
- Hardcoded fallbacks updated to 3.0.3: `api.py` `_resolve_odia_version()` (×2), `webhook.py` ODIA_VERSION defaults (×2), `frontend/components/dashboard/DashboardLayout.tsx` `ODIA_VERSION_FALLBACK`, `frontend/app/settings/page.tsx` System Information card, `frontend/app/page.tsx` hero strings (×2).

### Notes
- The sync `/scrape-and-ingest` endpoint stays in place. It's the right call when the audit fits comfortably inside the caller's request budget (small PDFs, retry-on-timeout orchestrators, manual `curl` from the terminal). For n8n in production, prefer the async variant.
- v3.0.3 is the foundation for any future scraper that talks to large public-records PDFs — the same pattern can wrap Granicus / Legistar / TCDAO endpoints without re-solving the timeout problem.

## [3.0.2] - 2026-05-15 — Backend-Side Scraping + Real-World First Ingest

Productionised the v3.0 autonomous-ingest thesis after a real first-light run against Visalia, CA's CivicPlus AgendaCenter surfaced one architectural gap (Cloudflare TLS-fingerprint blocking n8n's Node.js HTTP node) and one packaging gap (n8n's hardened Docker image strips Execute Command + curl, removing the natural workaround). Adds a backend-side download endpoint that routes around both, plus a simplified WF-001 that uses it.

### Added — `POST /api/v1/webhook/scrape-and-ingest`
- New endpoint at `src/oraculus_di_auditor/interface/routes/webhook.py`. Body: `{"url": "...", "jurisdiction_id": "...", "filename_hint": "..."}` (filename_hint optional). Downloads the URL server-side via Python's `urllib.request` with browser-like headers, computes SHA-256, dedups via `_dedup_check`, runs the Tier 1 audit pipeline, persists the Document/Analysis/Anomaly rows, and returns the same payload shape as `/webhook/ingest-and-analyze` so callers can treat them interchangeably.
- **Why**: Cloudflare-fronted public-records sites (CivicPlus / Granicus / Legistar) inspect the JA3 TLS fingerprint of the client and block Node.js's well-known hash. Python's OpenSSL stack has a different fingerprint that's accepted. This endpoint moves the download into the backend so the orchestrator (n8n) only needs to POST URLs.
- **Why now**: n8n's recent shift to hardened distroless-style images strips out the Execute Command node type AND the `curl` binary that were the natural workarounds for the Cloudflare block. Architectural fix beats trying to inject tools into a security-locked container.
- 502 returned on upstream download failure with descriptive detail; 400 on missing/non-http(s) URL or missing jurisdiction; 401 on invalid token (same as other endpoints).

### Added — `data/n8n-workflows/wf-001-visalia-url.json`
- Simplified 5-node WF-001 variant that uses the new URL endpoint:
  1. Daily 06:00 cron trigger
  2. Jurisdiction Config (Visalia, search URL pre-set)
  3. Fetch Portal HTML (with Cloudflare-bypass headers from v3.0.x)
  4. Extract PDF Links (regex from v3.0.x)
  5. POST `/webhook/scrape-and-ingest` with `{url, jurisdiction_id, filename_hint}` JSON body — batched 3 at a time with 2s interval
- No Execute Command, no Read Binary File, no shell-out — works on n8n's hardened image. Replaces both the original `wf-001-visalia.json` (which hit Cloudflare on download) and the `wf-001-visalia-shellexec.json` shim (which hit the missing-Execute-Command-node block).

### Added — `scripts/visalia_ingest.sh`
- Standalone Ubuntu shell script that does the whole Visalia ingest in 10 lines of bash — useful for non-Docker environments or scripted bulk runs. Curls the AgendaCenter search page, greps for `/AgendaCenter/ViewFile/` links, loops with wget download → curl POST per URL. Includes 20 MB cap (skips agenda packets) and dedup via the webhook's `already_seen:true` short-circuit.
- Used for tonight's first-light validation: **84 Visalia documents ingested, 85 total documents in DB, 80 anomalies persisted, 5 CRITICAL / 35 HIGH / 40 MEDIUM**. Pipeline integrity 100% (85/85 successful audits).

### Tests
- `tests/test_webhook_scrape_and_ingest.py` (new) — 10 tests covering happy path, filename-hint optional, missing/wrong token (401), missing URL / non-http URL / missing jurisdiction (400), dedup short-circuit, upstream `URLError` / empty-body (502). Mocks `urllib.request.urlopen` so tests never hit the network.
- 35/35 webhook + config-routes + scrape-and-ingest tests green; black + ruff clean.

### Notes for v3.0.x sub-cycle
- WF-001 now has three importable variants in `data/n8n-workflows/`: original (`wf-001-visalia.json`), shellexec attempt (`wf-001-visalia-shellexec.json`), and URL-endpoint version (`wf-001-visalia-url.json` — recommended). Future v3.0.x may consolidate.
- The `scrape-and-ingest` endpoint is the foundation for the Cross-Entity Tracks D/E/F deferred from v2.10.0 — future scrapers can reuse this path for Granicus / Legistar / TCDAO / etc. without re-solving the TLS-fingerprint problem.

## [3.0.0] - 2026-05-13 — Live Automation Goes Online

Marks the v2.x → v3.x cut. v3.0 is the operational-readiness release: the desktop installer now ships with everything needed to run n8n end-to-end against ODIA without manual env-var configuration. Three runtime bugs that survived v2.10.x are fixed, the brand mark is replaced with the geometric O.D.I.A. monogram crosshair, and the per-page hero treatment is unified across primary surfaces.

### Brand — O.D.I.A. monogram crosshair + unified malachite hero
- **New brand mark** (`frontend/components/base/icons/OraculusMarkIcon.tsx`). Geometric overlay of all four letters: O = outer gold ring, D = left tangent stem inside the O so the ring reads as both, A = inscribed equilateral triangle, I = centre vertical stem with double top crossbar. Triangle interior split into four facets — upper pair tinted gold, lower pair tinted emerald — by the I's stem + crossbar. Centre catch-light at (12,12) anchors the crosshair sighting point. Replaces the v2.7.9 gold-swirl mark.
- **Standalone 512×512 SVG** (`frontend/public/icons/oraculus-mark.svg`) rebuilt with the same construction plus gem-glow filters, gradient fills, and the v2.8 hex-mesh underlay. Picked up automatically by the sharp-based installer rasteriser to regenerate `icon-192.png`, `icon-512.png`, and `desktop/resources/icon.{png,ico,icns}`.
- **Unified hero** across Settings / Upload / Automation. The three pages previously used gold-flux / amber backgrounds (page-hero-settings / -upload / -automation) and now share Dashboard's `gem-panel gem-panel-faceted gem-hero-malachite` chain. Bracket-label tone bumped from amber/flow to cyan-bright to match. Note: this loses the v2.9.2 §8.5 differentiation (amber = library, cyan = live, flow = automation); intentional per user direction.

### Fixed — RAIA synthesis report rendering
- **Missing newline** between "Jurisdictions analysed" and "Missing (no persisted data)" in the rendered markdown. Root cause: Jinja's `trim_blocks=True` was stripping the newline after `{% endif %}` on the line ending the analysed list. Fixed by replacing the conditional with an explicit blank line + `{%- ... -%}` whitespace control.
- **Em-dash rendering as `â`** in downloaded `.md` files opened in Windows Notepad. Backend correctly emits UTF-8; the issue is legacy Windows editors defaulting to Windows-1252 without BOM detection. Fixed by prepending UTF-8 BOM (`0xEF 0xBB 0xBF`) to the modal's download blob. Modern editors (VSCode, Notepad++, macOS TextEdit) ignore the BOM; Notepad now auto-detects UTF-8.

### Fixed — Mesh-job lifecycle zombies
- `MeshExecutionJob` rows previously stayed at `status="executing"` forever when the backend process was killed mid-audit (uvicorn restart, Electron quit, SIGTERM during installer upgrade). The transition to `completed` / `failed` lived in the in-process audit thread; when the thread died the row was orphaned.
- New `_reconcile_stale_mesh_jobs()` in `src/oraculus_di_auditor/db/session.py` runs at `init_db()` boot, sweeps any `executing` row, marks it `failed` with a `reconciliation: "marked failed at startup..."` note in `metadata_json`, and commits. Conservative — no time window needed because a row claiming "executing" at boot is structurally orphaned (the process wasn't here when it started).
- Result: Orchestrator's "Recent Mesh Jobs" panel now reports accurate state across restarts.

### Fixed — PyInstaller installer bundle completeness
- Four module trees were missing from `desktop/odia-backend.spec` `hiddenimports`, causing them to fail to import at runtime in the bundled `.exe` / `.dmg` / `.AppImage`. Symptoms: Tier 2 webhook tile showing OFFLINE, Settings → Automation Webhook card non-functional, RAIA Synthesis trigger 500-ing.
- Added:
  - `oraculus_di_auditor.interface.routes.config_routes` (v2.10.1 runtime config — the entire webhook-token Settings UI was unreachable on the v2.10.1 installer)
  - `oraculus_di_auditor.mesh` + `oraculus_di_auditor.mesh.mesh_coordinator` (Tier 2 readiness)
  - `oraculus_di_auditor.self_healing` + `oraculus_di_auditor.self_healing.self_healing_service` (Tier 2 readiness)
  - `oraculus_di_auditor.raia` + `raia.raia_service` + `raia.synthesis_report` + `raia.schemas` + `raia.patterns` (Run RAIA Synthesis trigger)

### Version sync
- `pyproject.toml` `version = "3.0.0"` (was 2.10.1).
- `desktop/package.json` `"version": "3.0.0"`.
- Hardcoded fallbacks updated: `webhook.py` ODIA_VERSION defaults, `api.py` _resolve_odia_version() fallbacks, `frontend/components/dashboard/DashboardLayout.tsx` `ODIA_VERSION_FALLBACK`, `frontend/app/settings/page.tsx` System Information card, `frontend/app/page.tsx` hero strings (×2).

### Deferred to v3.x sub-cycle
- **Cross-Entity Tracks D / E / F** from v2.10.0 remain outstanding (14 entity-specific sub-detectors, XREF register persistence, frontend XREF page). Significant scope; will be the v3.1 / v3.2 themes.
- **n8n + WF-001 end-to-end scraper baseline test** is the operational validation of v3.0's infrastructure; happens against the v3.0 binary in a follow-on session.

## [2.10.1] - 2026-05-12 — Post-install UX patch (RAIA viewer + webhook token UI)

Closes three gaps a fresh v2.10.0 desktop install surfaced for the first user. Scope is deliberately narrow — UX wiring and runtime-mutable config — and is independent of v2.10.0's deferred Track D / Track E / Track F items, which remain on the v2.10.x sub-cycle roadmap.

### Fixed — RAIA Synthesis result viewer
- Previously, clicking **Run RAIA Synthesis** on the Automation page produced a green success toast and silently dropped the rendered markdown report (`body.markdown` from `/api/v1/triggers/raia-synthesize-all`). Users had no way to see what RAIA actually found.
- `frontend/app/automation/page.tsx`:
  - `TriggerNotification` interface extended with optional `report?: RaiaReport` payload.
  - `triggerRaiaSynthesis()` now captures the markdown and metadata, persists to `localStorage` under key `odia.lastRaiaReport` so the most recent report survives reloads.
  - New `RaiaReportModal` component renders the markdown verbatim in a scrollable monospace `<pre>` with **copy** and **download .md** actions. Escape key + backdrop click close it.
  - The success banner gains a "view report →" action whenever a notice carries a report.
  - The "Run RAIA Synthesis" trigger tile gains a permanent **VIEW LAST REPORT →** footer link whenever a stored report exists.

### Added — Runtime-mutable webhook token (Settings UI)
- Pre-patch, `ODIA_WEBHOOK_TOKEN` could only be set as a process environment variable, which is impractical on the Electron desktop install where the host has no shell. The `register_webhook_routes` registration gate also REFUSED to register webhook routes when the env var was unset — so a Settings-page UI for the token was structurally impossible.
- `src/oraculus_di_auditor/interface/routes/webhook.py`:
  - New `_user_token_path()` returns `<user_data_root>/webhook_token` (uses `config.jurisdiction_loader._user_data_root()`).
  - New `_resolve_webhook_token()` returns `(token, source)`, reading env first then file fallback. `_verify_token`, `_token_configured`, and the registration check all route through this resolver.
  - **Registration gate softened**: webhook routes now register unconditionally. The per-request `_require_token` dependency remains the security wall. This makes the Settings-UI token effective without a backend restart.
- `src/oraculus_di_auditor/interface/routes/config_routes.py` (new):
  - `GET /api/v1/config/webhook-token` → `{configured, source: "env"|"file"|null, file_path, env_var}`. Never returns the token value.
  - `POST /api/v1/config/webhook-token` → writes / clears the file, sets POSIX `0o600` perms where supported, surfaces env-shadows-file conflicts.
- `src/oraculus_di_auditor/interface/api.py`: wires `register_config_routes` after the dashboard routes.
- `frontend/lib/api/client.ts`: new `getWebhookTokenStatus()` + `setWebhookToken(value)` methods + `WebhookTokenStatus` / `WebhookTokenSetResult` interfaces.
- `frontend/app/settings/page.tsx`: new `WebhookTokenCard` (status pill: `env var` / `on disk` / `not configured`; masked input with Show / Hide / 32-byte-hex Generate; Save / Clear; amber inline warning when env shadows the file).

### Changed — Webhook contract on unconfigured installs (breaking for internal probes)
- Pre-patch: `GET /api/v1/webhook/health` returned **404** when no token was configured (registration gate refused).
- Post-patch: returns **200** with `webhook_token_configured: false`. Authenticated webhook endpoints still return 401 in that state.
- Rationale: the 404-when-unset contract made the Settings UI structurally impossible and forced misconfigured installs to fail with an opaque 404 instead of a structured "not configured" boolean.
- **Migration**: any external monitoring asserting on 404-when-unset should switch to checking `webhook_token_configured`. No external consumers known at release time; internal `test_webhook_health.py` updated to assert the new contract.

### Fixed — Version strings that drifted at v2.10.0
- `pyproject.toml` (was 2.9.3 — never bumped at v2.10.0).
- `src/oraculus_di_auditor/interface/api.py` `_resolve_odia_version()` fallbacks (2x).
- `src/oraculus_di_auditor/interface/routes/webhook.py` `ODIA_VERSION` defaults (2x).
- `frontend/app/settings/page.tsx` hardcoded "odia 2.9.3" in the System Information card.
- `desktop/package.json` (was 2.10.0 → 2.10.1 for the installer-naming match).

### Tests
- `tests/test_webhook_health.py`: rewritten for the v2.10.1 contract. New autouse `_isolate_token_file` fixture redirects `_user_token_path` to `tmp_path` so the suite never reads or writes the developer's real `%APPDATA%\ODIA\webhook_token`. Old "404 when unset" test became "200 with `webhook_token_configured: false`"; new test covers the file-fallback path.
- `tests/test_config_routes.py` (new): 5 tests covering GET status (none / env), POST persist-and-activate without restart, POST empty-string clear, env-shadows-file conflict reporting.
- **32/32 green** across the webhook + config-routes surface (test_webhook_health 7, test_webhook_ingest 16, test_webhook_models 4, test_config_routes 5). tsc clean on touched frontend files.

### Operational notes
- The bundled compose's `ODIA_BASE_URL=http://backend:8000` only works when the ODIA backend is the `backend` compose service. Desktop installs run the backend outside compose, so users running n8n alongside a desktop install **must** override to `ODIA_BASE_URL=http://host.docker.internal:8000` in their `.env`. This is now called out in the Automation page's offline-help block.

## [2.10.0] - 2026-05-12 — Cross-Entity Analysis Protocol V1.0

Formalises two years of "accidental find" forensic work into deterministic architecture. Every document entering O.D.I.A. is now classifiable against the full Cross-Entity Registry, not just the jurisdiction under primary analysis. The protocol's governing principle — *"the audit that documents the machine that serves itself must operate across those same boundaries — systematically, not accidentally"* — operates at ingestion time, not at R.A.I.A. discovery time.

This is a scoped first slice of the protocol: registry foundation, D-13 detector with seven finding types (A–G), TCDAO press-release archive scraper (yearly + monthly-archive-widget discovery + 2022 path-variant handling + gap-band absence-record emission). The 14 entity-specific sub-detectors (Track D), XREF register persistence (Track E), and frontend XREF page (Track F) defer to v2.10.1+.

### Added — Track A · Cross-Entity Registry foundation
- **`src/oraculus_di_auditor/registry/` package** — canonical Sunshine Dragnet entity catalogue per Cross-Entity Analysis Protocol V1.0 (May 2026).
  - `entities.yml`: 12 Tier-1 primary jurisdictions (VPD/PPD/TPD/LDPS/FPD/WPD/DPD/EPD/TCSO/TCPD/TCDAO/DMV) + 8 Tier-2 governance bodies (BOS/Grand Jury/Courts/Public Defender/CAO/CCP/VEDC) + 10 Tier-3 vendors (Axon/Flock/Motorola/Lexipol/BCS/BRINC/NEC/Tyler/BI Inc/Loops Marketing) + 6 Tier-4 external intelligence sources + 13 personnel + 7 finding-type rules + 11 "Leave No Stone Unturned" non-standard record categories.
  - `loader.py` (`EntityRegistry`): typed accessors for tier-filtered iteration, alias index (case-insensitive), sub-detector activation lookup, finding-type severity defaults, non-standard category sweep precedents.
  - `types.py`: frozen `@dataclass` definitions (`Entity`, `Personnel`, `PersonnelHistoryEntry`, `FindingType`, `NonStandardCategory`).
  - 21 tests in `tests/registry/test_loader.py` covering tier counts, personnel records, Axon's 9-jurisdiction presence footprint, Fahoum personnel-migration precedent (E-001 → E-011), dataclass immutability.

### Added — Track B · D-13 Cross-Entity Detector
- **`src/oraculus_di_auditor/analysis/cross_entity.py`** — function-style detector matching the project's `(doc) -> list[dict]` contract. Sweeps every document against the full registry; emits one finding per `(primary, target)` pair, classified into one of seven types:
  - **A** Budget/Fiscal cross-reference (HIGH; CRITICAL on new vendor presence)
  - **B** Personnel migration (HIGH; CRITICAL on procurement-authority-to-prosecution-subject migration — the Fahoum precedent)
  - **C** Vendor cross-contamination (always CRITICAL — Farmersville/Woodlake/Visalia Axon Outpost precedents)
  - **D** Operational intersection (HIGH; default for unsignalled hits)
  - **E** Governance chain (HIGH; CRITICAL when governance action creates an unmet obligation)
  - **F** Grant/Funding pipeline (HIGH)
  - **G** Data/Evidence pipeline (HIGH; CRITICAL on undisclosed access)
- Confidence scoring with multi-signal co-occurrence bonus, dollar-amount-in-excerpt boost, repeated-mention reinforcement, and < 0.40 demotion-to-low-severity floor for analyst review.
- Registry + alias-pattern caches are module-level lazy singletons; first call hydrates, subsequent calls reuse (one YAML load per process).
- 11 fixture tests in `tests/analysis/test_cross_entity.py` covering activation gates, self-reference suppression, all five protocol-precedent finding types, low-confidence demotion, and the output-shape contract.
- D-13 wired into `analysis/pipeline.run_full_analysis` alongside the existing detectors; `"cross_entity"` joins the findings dict. The pipeline's severity-weights map gains `"critical": 1.0` so CRITICAL findings correctly dominate aggregate severity; flag extraction and summary lines updated to surface critical alongside high.

### Added — Track C · TCDAO press-release archive scraper
- **`src/oraculus_di_auditor/scrapers/tcdao_archive.py`** — v1 scraper for tulareda.org press release category archives. Polite by design: `robots.txt`-aware, identifying User-Agent (`O.D.I.A.-Forensic-Audit-Scraper/1.0`), default 2-second rate limit, exponential backoff on 429/503, `Retry-After` honoured, manifest-driven dedup, dry-run mode for discovery-only previews.
- Yearly category archive discovery 2020–2026, paginated walk, WordPress-standard HTML parsing (title / publish date / body / inbound links / embedded images / SHA-256).
- CLI: `python -m oraculus_di_auditor.scrapers.tcdao_archive --start-year 2020 --end-year 2026 --out data/tcdao_archive`.
- 11 parser tests in `tests/scrapers/test_tcdao_archive.py`.

### Added — Track D · v2 gap-band absence-record emission
- **`src/oraculus_di_auditor/scrapers/tcdao_archive_v2.py`** — extends v1 with three enhancements from the May 11, 2026 baseline diagnostic:
  - **Monthly-archive-dropdown discovery** (`parse_archive_widget`): the WordPress sidebar widget is the authoritative surviving-months index. Recovers sparse historical entries (2006-03, 2006-04, 2006-05, 2006-10, 2011-03, 2015-05) that no yearly category page lists.
  - **Gap-band detection + synthetic absence records** (`KNOWN_GAPS`, `classify_coverage`, `AbsenceRecord`, `emit_gap_absence_records`): three known multi-year gaps (GAP-A 2006-11→2011-02 / GAP-B 2011-04→2015-04 / GAP-C 2015-06→2017-12) materialise as `primary_entity=E-011` documents at finding ID `archival:coverage-gap`. The absence-record text deliberately includes governance vocabulary so D-13 round-trips it as a **Type E governance-chain cross-reference to BOS (E-020) regarding records-retention obligation** — locked by an integration test.
  - **2022 path-variant handling**: the canonical category slug was renamed and now requires the doubled `2022-press-releases-press-releases/` form; discovery tries both before falling back to monthly enumeration.
- 21 tests in `tests/scrapers/test_tcdao_archive_v2.py` including the C1+D1+B1+B2 end-to-end integration test.

### Added — Dependencies
- `beautifulsoup4>=4.12.0` (runtime). Used by the TCDAO scrapers; tests gracefully skip via `pytest.importorskip("bs4")` on minimal dev installs.

### Changed
- `analysis/pipeline.py`: pipeline `findings` dict now includes `"cross_entity"`; `severity_weights` includes `"critical": 1.0`; flag extractor and summary line surface critical alongside high. Existing detector behaviour unchanged.
- `analysis/__init__.py`: exports `detect_cross_entity_anomalies` alongside the existing detector exports.

### Fixed
- Function-style adaptation of the supplied D-13 corrected a Type B (Personnel Migration) classification bug in the upstream protocol bundle: `is_personnel` was derived from `target_entity_id.startswith("P-")` after personnel hits had been re-keyed under entity targets (E-NNN / V-NNN), so the test always returned False and Type B never fired. Now carried as a `kind` field on `AliasHit` and read at classify time.

### Notes for the v2.10.x sub-cycle
- Track A2 (PersonnelRegistry mutable extension via SQLAlchemy)
- Track A3 (Document schema additions: `primary_entity`, `secondary_entities`, `vendors_detected`, `personnel_detected`, `xref_notes`, `confidence_status` columns + migration)
- Track A4 (`CrossEntityReference` model + XrefRegister service)
- Track D1–D3 (14 entity-specific sub-detectors for TCPD/TCDAO/DMV)
- Track E2/E3 (Targeted R.A.I.A. + Entity-Opening R.A.I.A.)
- Track F1–F3 (Evidence packet XREF integration, frontend XREF/Personnel pages)
- Track C3 (IngestionBridge wiring scraped press releases into the standard pipeline)
- The two n8n workflows WF-015 (TCDAO archive monthly refresh) and WF-016 (Targeted R.A.I.A. daily trigger) defer to v2.10.x.

---

## [2.9.3] - 2026-04-28 — Detector Calibration Sweep + OCR Coverage

The Run-12 evidence packet (70 Visalia documents, 415 findings) revealed a P0 silent-failure mode: 8 of 38 unique SHAs (the actual Flock contracts, the Axon staff report, the JAG allocations PDF) emitted ONLY noise-floor findings because their text-extraction returned near-empty content and the audit pipeline did not flag the gap. v2.9.3 ships five tracks addressing that, plus a detector-completeness fix, MAS aggregation correctness, noise-floor suppression, and vendor-registry expansion.

### Added — Track A · OCR coverage (P0)
- **`scripts/diagnose_text_extraction.py`** — one-shot diagnostic. Run against any PDF corpus to identify silent-failure candidates (documents where pypdf returns < 500 chars and OCR fallback is needed). Supports `--use-ocr` to exercise the full pipeline + `--threshold` override.
- **`TextExtractionResult` dataclass + `extract_text_from_pdf_with_metadata()`** in `oraculus_di_auditor.ingestion.engine` — sibling of the existing `extract_text_from_pdf()` that returns the extraction `method` (`pypdf` / `tesseract_ocr` / `ocr_unavailable` / `failed`) + `char_count` alongside the text. Old function kept as a backwards-compatible wrapper.
- **`SeenHash.text_extraction_method` + `SeenHash.text_char_count`** columns persist the extraction provenance per document. New idempotent `_migrate_seen_hash_extraction_columns()` runs at `init_db()` to ALTER TABLE-ADD the columns on existing SQLite installs (no Alembic in this codebase).
- **Evidence packet manifest carries `text_extraction` block per document**: `{method, char_count, ocr_used}`. The executive summary now renders a corpus-level WARNING when documents required OCR — and an even louder warning when OCR was *needed* but unavailable (the silent-failure mode from Run-12).

### Fixed — Track B · Detector emission completeness (P0)
- **`grant:cops-without-itemisation` populates its evidence dict** (`grant_compliance.py`). The pre-2.9.3 emission passed `details={}`, leaving 10/10 sheets in Run-12 rendered with "(no structured details recorded)" and no Technical Evidence JSON block. Now emits `grant_program`, `statute` citation, `trigger_excerpts`, `itemisation_markers_searched`, `anti_supplant_referenced`.
- **Renderer-level invariant**: `evidence_packet._build_finding_sheet` now WARNs when a finding emits with empty `details`, so this regression cannot recur silently for any future detector.

### Changed — Track C · MAS aggregation correctness (P0)
- **Synthesis page top-findings table** — `Docs / Occurrences` columns replaced with `Unique SHAs / Total Emissions`. The pre-2.9.3 columns were ambiguous and duplicate uploads of the same SHA inflated both equally, producing nonsense like "50 docs / 50 occurrences". Now uses the `document_id → sha256` map from each audit's `document_manifest` to dedupe.
- **Synthesis page vendor table** — split detection-emission count from related-findings severity histogram. Pre-2.9.3 the severity histogram showed only `vendor-detected:*` emissions (uniformly LOW because that finding ID IS LOW), giving the misleading impression that Axon-related risk is uniformly LOW. Now `Detections` (vendor-tagged emissions) and `Related` (all findings on docs where the vendor was detected) are distinct, and the C/H/M/L histogram covers the related set.
- Both Markdown and DOCX exports updated; on-page rendering updated to surface unique-SHA counts and the related-severity strip.

### Changed — Track D · Noise-floor suppression (P1)
- **`fiscal:missing-provenance-hash` gated behind `ODIA_INCLUDE_PIPELINE_CHECKS=1`**. Fired on 100% of Run-11 + Run-12 corpora because it measures pipeline state, not document content. Default behaviour: silent. Diagnostic operators can opt in.
- **`admin:blank-required-fields` rolled up to corpus scope**. Per-document emission gated behind `ODIA_PER_DOC_BLANK_FIELDS=1`; default emission is now a single corpus-level `admin:blank-required-fields-corpus` finding with `scope: "corpus"` listing every affected document. Run-12 produced 70 echoes for one underlying observation; v2.9.3 produces 1 finding with the full per-document detail nested in `evidence.affected_documents`.
- **Tests for both detectors** updated to opt-in via `monkeypatch.setenv()`; new tests pin the default-OFF behaviour.

### Added — Track E · Detector coverage + vendor expansion (P1)
- **`scripts/detector_coverage.py`** — empirical coverage diagnostic. Exercises every detector against a stress corpus and reports detector module / finding ID / severity / details-populated / plain-language-template / statute citation per emitted finding. Answers "what does ODIA actually look for?" without a 9-module refactor. Verified output: 21 distinct finding IDs across 7 detector modules, all with populated `details` post-2.9.3.
- **Vendor catalogue expanded**: added `Verkada` (video / cloud surveillance, governance gates required) and `T-Mobile` (telecom backhaul). Pre-2.9.3 catalogue already covered Lexipol, Spartan Camera, ABH Fox Solutions, SmartWater CSI, Nexanet, Security Lines US, BCS Consulting, QPCS LLC — handoff list of 9 was based on a stale view; only these 2 were genuinely missing.

### Added — Documentation
- **`docs/EVIDENCE_PACKET_RUN12_EVALUATION.md`** — the run-12 quality audit that motivated v2.9.3. Documents the silent-failure observation, the detector emission gap, the MAS aggregation issues, and the noise-floor patterns.

### Engineering
- 229 backend tests pass on touched modules (`test_fiscal_detector` + `test_administrative_integrity` + `test_audit_engine` + `test_evidence_packet` + `test_ingestion_engine` + `test_plain_language` + `test_upload_routes` + `test_audit_records_mesh_job` + `test_audit_workflow_integration` + `test_orchestrator_dashboard`).
- `npx tsc --noEmit` clean across all production sources.
- `next build` passes for all 15 routes; Synthesis bundle ↑ 6.01kB → 6.33kB (new aggregation logic).

### Out of scope (deferred)
- Near-duplicate detection above SHA layer (the 4-byte Measure N variant) → v2.9.4.
- Image-extraction from PDFs (signature stamps, table images) → v2.10.0.
- Multi-language OCR (`tesseract-ocr-spa`) → activated when first Spanish corpus arrives.
- Cumulative-state R.A.I.A. recursion → separate analysis phase, not a code change.

---

## [2.9.2] - 2026-04-27 — Hero Pattern Convergence

The user named three pages (Dashboard, Anomalies, Orchestrator) as the design target and asked every other page to match. v2.9.2 ships the unification: a single shared `HeroMetricTile` component, the four-element canonical hero structure (bracket-label / heading / subtext / metric grid) on every surface, and tonal coherence across the navigation.

### Added
- **`HeroMetricTile` component** (`frontend/components/hero/HeroMetricTile.tsx`) — the canonical metric tile for hero readouts. One component, ten tones (`critical/high/medium/low/info/gold/emerald/signal/flow/neutral`), optional active state with 3-layer glow ring, optional onClick that renders as a keyboard-accessible button. Replaces three previously-divergent implementations (Dashboard `SeverityTile`, Anomalies inline filter buttons, Orchestrator `OrchestratorMetric`).
- **18 jest assertions** covering every tone, active/inactive states, button vs div rendering, sublabel handling, icon slot, and aria-pressed reflection.
- **`page-hero-synthesis` CSS class** — marble texture for the Synthesis cross-jurisdictional aggregation surface (mobile fallback included in the `@media (max-width: 768px)` block).
- **`docs/EVIDENCE_PACKET_RUN11_EVALUATION.md`** — quality audit of the run-11 evidence packet. 122 findings sampled across 7 detector modules; verdict is "factually correct, no detector regressions" with recommendations for v2.10.x calibration sprint.
- **`docs/BRAND.md` §8.5** — documents the canonical four-element hero pattern with bracket-label tone discipline (cyan-bright = live; amber = static/library; flow = automation).

### Changed
- **Anomalies hero** — added `[ ANOMALY EXPLORER · CROSS-AUDIT ]` bracket label + canonical heading + subtext; severity tiles now use `HeroMetricTile` with `active` glow ring on filter selection (behaviour identical, implementation shared).
- **Orchestrator hero** — three metrics migrated to `HeroMetricTile` with tonal colouring (`signal` for agents online, `emerald`/`neutral` for tasks queued, `gold` for completed/24h).
- **Synthesis hero** — flat severity-number strip + bare gem-panel hero replaced with the canonical pattern (marble texture, amber bracket label, severity tiles inside the hero with sublabel percentages, export buttons moved into the hero).
- **Documents hero** — added evidence-library bracket label + 3-tile metric grid (unique documents / total audits / findings emitted).
- **Analysis hero** — added aggregate-analytics bracket label + severity tile grid with percentage sublabels. Severity-distribution bars now colour by severity CSS vars (was uniform light-blue); detector bars fade `gold-300` → `gold-500` → `smoke-500` by rank.
- **Results hero** — flat severity strip with custom inline tones replaced with the canonical `HeroMetricTile` pattern. Bracket label includes the truncated job ID for context. Active-filter glow now matches Anomalies exactly.
- **Automation hero** — four `HealthTile` instances migrated to a `WebhookMetric` wrapper that maps webhook tri-state to `HeroMetricTile` flow/critical/medium tones; active-workflows tile uses `signal` (live state) instead of amber (config state).
- **Settings hero** — added `[ APPLICATION CONFIG · USER SCOPE ]` bracket label + canonical heading/subtext (no metric tiles — config page).
- **Upload hero** — added evidence-intake bracket label + 3-tile context strip (audits run / findings emitted / detector modules) so users see audit-history depth before they intake new documents.
- **Dashboard hero** — added `[ FORENSIC AUDIT PLATFORM · v2.9.2 · LOCAL ]` bracket label per BRAND.md §8.5; brand badge bumped to v2.9.2.

### Engineering
- **Zero type errors** in production code (`npx tsc --noEmit` clean across all `app/` + `components/` non-test sources).
- **Next.js build** passes for all 15 routes; bundle deltas are minor (each metric-tile-using page picks up ~0.3 kB for the shared `HeroMetricTile` chunk).

---

## [2.9.1] - 2026-04-27 — Mineral Polish + Maturity Pass

Five tracks of finish work on top of v2.9.0. Track A fixes the intro's premature exit, Track B propagates mineral textures across every page, Track C completes the light-theme leak sweep, Track D finally swaps the legacy octopus desktop icon, Track E lands the maturity roadmap.

### Fixed
- **Intro played past final frame** (Track A) — `IntroFrame.tsx` fallback timeout bumped 30s → 35s. The intro `run()` function takes ~31.4 seconds end-to-end (3 phases + 7.6s typeCode + 2.4s final hold + postMessage); the previous 30s fallback fired BEFORE the intro's postMessage, cutting off the "We the People" + brand-tag phase. 35s gives ~4s cushion past genuine completion so postMessage always wins under normal conditions; the fallback only fires if the intro JS errors mid-sequence.
- **Desktop icon still showed legacy octopus** (Track D, **CRITICAL**) — `desktop/resources/icon.png` was 2,757,125 bytes at v2.8.1, **identical to v2.7.10**. Despite the v2.7.10 / v2.8.0 / v2.8.1 release notes claiming the icon had been updated, the file on disk had never actually been replaced. Fixed by copying the v2.8.2 raster bundle (1,299,046-byte composite of the gold-swirl source painting in a circular frame with gold ring) into `desktop/resources/icon.png` + new `icon.ico` for Windows multi-size, plus three PWA rasters (192/512/maskable-512). Windows title bar finally renders the brand mark.

### Added
- **Per-page mineral hero textures** (Track B) — eight new `.page-hero-*` utility classes wired into Upload, Results, Anomalies, Documents, Analysis, Settings, Orchestrator, Automation. Each page reads as a distinct location in the same mineral-photographic visual world: Upload + Settings + Automation get gold-flux, Results gets emerald malachite, Anomalies + Orchestrator get malachite-flux (active surfaces), Documents + Analysis get marble.
- **Comprehensive light-theme override sweep** in `globals.css` — every `bg-{color}-50/100`, `text-{color}-700/800`, `border-{color}-200/300` Tailwind class now resolves to mineral-palette CSS vars at runtime. Form inputs (select / input / textarea) get mineral styling. Severity stripe primitive (`.severity-stripe.s-{level}`) for finding cards.
- **Two new secondary surface classes** — `.gem-card-marble`, `.gem-card-malachite` for body-level cards (more dimmed than hero variants).
- **`docs/MATURITY_REPORT.md`** (Track E) — 289-line project status document covering the six dimensions of "outstanding performance" (visual identity, forensic depth, operational reliability, data governance, distribution, community), what's complete, and a 90-day sprint roadmap from v2.9.x to v2.10.0.

### Changed
- **Results page severity table** — emoji icons (🔴🟠🟡🔵) removed per `BRAND.md` §9 (no emoji in chrome). Replaced with `hud-sev hud-sev-{level}` pill primitives + `severity-stripe` left-edge accents on finding cards.
- **Anomalies page severity filter tiles** — pastel `bg-red-50/orange-50/yellow-50/blue-50` rectangles replaced with `hud-panel hud-panel-inset` cards + colored dot + glow shadow when active. Matches the Dashboard's SeverityTile pattern.
- **Settings — Theme dropdown removed** — the app is dark-only per `BRAND.md` §9; the "Light / Dark / System" options were misleading and the user confirmed the setting didn't actually work. Replaced with a read-only "Mineral (locked at v2.8.0)" indicator.
- **Settings — auth buttons** — `bg-blue-600 text-white` and `border-gray-300 text-gray-700` replaced with `hud-btn hud-btn-emerald` / `hud-btn hud-btn-ghost`.
- **Upload page drag-drop zone** — pale gray rectangle replaced with `hud-panel hud-panel-inset` + emerald glow when armed.
- **Upload "From Gallery" / "Use Camera" buttons** — light gray border buttons replaced with `hud-btn hud-btn-ghost` at 44 px touch-target minimum.

---

## [2.9.0] - 2026-04-27 — Mobile-First PWA Polish

The platform's first dedicated mobile pass. Tracks A (documentation) and B (PWA polish) ship; Track C (Capacitor native wrapper) is deferred pending Apple Developer Program / Google Play Console account decisions. Web/PWA installs work on iOS Safari and Android Chrome today.

### Added
- **`docs/MOBILE.md`** — comprehensive PWA platform guide. Platform-support matrix (iOS Safari ≥16.4, Android Chrome ≥110, desktop Chromium), install instructions for both flavors, service-worker behavior, troubleshooting, and a deferred-work reference for the Capacitor native track.
- **README — Mobile (PWA) section** — points users at `docs/MOBILE.md` and summarises which surfaces are mobile-optimized vs. desktop-first.
- **`PullToRefresh` component** (`frontend/components/mobile/PullToRefresh.tsx`) — touch-driven pull-to-refresh wrapper with damped pull curve, threshold arming, and `--signal-neon` spinner glow. Active only on `<md:` viewports (desktop has its own polling). Wired into `/documents`, `/anomalies`, and `/results`.
- **`InstallPrompt` component** (`frontend/components/pwa/InstallPrompt.tsx`) — mobile-only install banner. Captures Android `beforeinstallprompt` for one-tap install, falls back to an iOS Safari "Tap Share → Add to Home Screen" hint. Auto-suppresses in standalone mode, under file:// (Electron), and for 14 days after dismissal. Mounted in `DashboardLayout` above the bottom tab bar.
- **Upload page mobile card layout** — file table replaced with a stacked card list on `<md:`. Each card surfaces filename, format pill, size, truncated SHA, and a full-width Remove button at the 44 px touch-target minimum. The desktop table is preserved verbatim at `md+`.

### Changed
- **`Button` size scale formalized as touch-target policy** — `xs (32 px)`, `sm (40 px)`, `md (44 px)`, `lg (52 px)` minimum heights. `md` is the iOS HIG / Material Design default (44 pt / 48 dp). Documented inline at `frontend/components/base/Button.tsx`.
- **Mobile bottom tab bar `min-h-[56px]`** — gives every tab the full Material Design tap surface.
- **Service worker — split caching** (`frontend/public/sw.js`): app shell pre-cached in `odia-shell-v5` (bumped from `odia-shell-v4`); new `odia-static-v1` runtime cache holds `/_next/static/*`, `/icons/*`, `/textures/*` under a stale-while-revalidate strategy. `/api/*` (including `/api/uploads/*`) is still never cached. Splitting the caches keeps the shell small and lets us evict the two independently.

### Fixed
- **`/documents` page broken `useMemo` opener** — the row-aggregation memo was missing its `const rows = useMemo(() => {` declaration after the v2.9.0 B3 edit, leaving floating code and an undefined `rows` reference. Restored.

### Notes
- **Capacitor native track deferred** — full handoff staged in `C:\Users\yahua\Downloads\v2.8.1_Updates\CLAUDE_CODE_HANDOFF_v2_9_0_mobile.md` for when Apple Developer Program ($99/yr) and Google Play Console ($25 one-time) accounts are decided. The PWA covers the install path until then.

---

## [2.8.1] - 2026-04-26 — Mineral Calibration Bug-Fix Patch

Five surgical fixes addressing user-flagged bugs in the v2.8.0 install.

### Fixed
- **Texture overlay too dark** (Fix #1) — `.gem-hero-*` overlay opacities reduced from 0.50–0.95 to 0.30–0.72 so the underlying marble veining / malachite striations / gold flux from the reference photos actually read through. Previous opacities drowned the texture so the hero panels showed flat tinted rectangles. New range still meets 4.5:1 text contrast on the composite.
- **Textures don't load under Electron file://** (Fix #2, **CRITICAL**) — CSS `url('/textures/...')` resolved to filesystem root under `file://` (same bug class as the v2.7.10 IntroFrame fix). New `TextureResolver` client component uses `useLayoutEffect` to overwrite the `--texture-*` CSS variables with `publicAssetURL()`-resolved absolute URLs before browser paint. Mounted in `app/layout.tsx` between `ServiceWorkerRegistration` and `IntroGate`. Mobile breakpoint substitutes `-mobile.webp` variants. SSR-safe (short-circuits when `typeof window === 'undefined'`).
- **Intro replay button visible from start** (Fix #3) — `#replay` button now ships with `opacity: 0` and `pointer-events: none`. Reveals only after the run() function adds `.completed` class to `#seq` (post brand-tag fade-in).
- **Intro click-dismiss too eager** (Fix #4) — added 4-second minimum-duration guard on `$('seq').addEventListener('click', ...)`. Clicks before the guard expires are absorbed; clicks after dismiss as before. The parent IntroFrame's Skip button (3-second appearance delay, upper-right corner) is unaffected — it still dismisses immediately. Final-frame hold bumped from 1.4s → 2.4s so users see "We the People" + brand tag before the dashboard fade-in.

### Added
- **`scripts/build-icons.sh`** — rsvg-convert + ImageMagick reference rasterizer documented in handoff §6 Option B. The existing `frontend/scripts/build-icons.mjs` (sharp-based) remains the default — both produce equivalent SVG-fidelity output. Shell script is preserved for users who prefer rsvg-convert.
- **`frontend/components/__tests__/TextureResolver.test.tsx`** — 4 smoke tests pinning the texture-variable rewrite behaviour.

### Notes
- **Fix #5 deferred — no new icon raster commit needed.** The v2.8.0 commit `D2` already regenerated the icons via sharp from the new measured-color SVG, and sharp's libvips renderer with `density: 384` produces SVG-fidelity output equivalent to rsvg-convert. The supplied PIL approximations in the v2.8.1 bundle are visibly worse than the already-committed sharp output, so they're skipped. The user's "still shows octopus" diagnostic likely came from a stale install of v2.7.x.

---

## [2.8.0] - 2026-04-26 — Mineral Calibration

### Changed
- **Palette** — every smoke / gold / emerald token recalibrated to colors literally measured from the reference photography in `docs/brand/reference/`. Primary brand gold shifts from `#d8b13c` (saturated yellow) to `#997545` (mineral tan-gold); primary emerald shifts from `#1fe88f` (digital neon) to `#0f6546` (real malachite). The neon emeralds are preserved under a new `--signal-*` namespace reserved for live-state UI only (running workflow, healthy backend, active mobile tab).
- **Intro** — plays on every app launch (was: first launch only). Per-session dedup via `sessionStorage` means navigating between pages within a session does not replay it. Settings replay button now writes a one-shot `localStorage` flag for cross-session force-replay.
- **Oraculus mark SVG** — rebuilt with measured colors from the source painting. Every gradient stop is a real pixel sampled from `reference_5_gold-swirl-icon-source.png`.
- **`OctopusMarkIcon` → `OraculusMarkIcon`** — call sites in `app/page.tsx` and `components/dashboard/DashboardLayout.tsx` migrated to the canonical name. The deprecated alias re-export stays in `components/base/Icons.tsx` so any third-party import keeps working.
- **Service worker** — cache key `odia-shell-v3` → `odia-shell-v4` to evict v2.7.x caches on the new mineral palette.

### Added
- **Texture system** — four reference photos exposed as CSS variables (`--texture-marble`, `--texture-malachite`, `--texture-malachite-flux`, `--texture-gold-flux`), each in four pre-dimmed WebP variants (bg, hero, tile, mobile). Total ~530 KB across 16 files at `frontend/public/textures/`.
- **Gem-hero utility classes** — `.gem-hero-marble`, `.gem-hero-malachite`, `.gem-hero-malachite-flux`, `.gem-hero-gold-flux`, `.gem-splash`. Hero/splash/cover surfaces only — body content panels stay flat per BRAND.md §3.2.
- **Dashboard hero gets `.gem-hero-malachite`** (C1) and **Synthesis hero gets `.gem-hero-marble`** (C3) — texture composes underneath the existing chamfer + bracket geometry.
- **`docs/brand/measured_palette.json`** — machine-readable palette reference with L\* values + source-image anchoring for every token.

### Fixed
- **CHANGELOG** — reconstructed continuity from v2.1.1 forward (all v2.2 through v2.7.10 entries reconstructed from git tag history + memory artifacts).

---

## [2.7.10] - 2026-04-26 — Sign-off Pass on v2.7.9 Install

### Fixed
- **Intro black-screen bug** — `<iframe src="/intro/index.html">` resolved to filesystem root under Electron `file://` (became `file:///intro/index.html` — doesn't exist). New `publicAssetURL()` helper in `frontend/lib/navigation.tsx` anchors against the runtime app root via `getAppRootURL()`. IntroFrame computes the iframe src via this helper at mount.
- **Application icon** — swapped from procedural SVG approximation (read as a stylized "C/E" curve) to a pixel-faithful raster of `docs/brand/reference/reference_5_gold-swirl-icon-source.png` via `sharp` lanczos3 upscale. Maskable variant gets 12% inner padding so Android adaptive-icon mask doesn't crop the artwork.
- **DOCX export now works on the desktop install** — was pandoc-only since Sprint 6 (silently disabled in PyInstaller bundle). Added `python-docx` fallback in `format_converters.markdown_to_docx` handling the audit-report Markdown subset directly. `python-docx` added to runtime deps + PyInstaller spec hiddenimports.

### Changed
- **Contrast + gold pass** — body bg switched from flat near-black to a 4-stop linear gradient (smoke-950 → #0c1011 → #0d1310 → smoke-900) with a faint jade undertone. Edge tokens bumped: `--gem-edge-gold` 55%→80%, `--gem-edge-emerald` 45%→70%. `.hud-panel` and `.gem-panel` lifted off pure black with jade undertone, dual gold + emerald halo on hover.

### Added
- **3 DOCX-fallback regression tests** in `tests/test_docx_export_fallback.py`.

---

## [2.7.9] - 2026-04-25 — Brand Refresh & Cinematic Intro

### Added
- **`docs/BRAND.md`** — 323-line visual identity reference document. Palette tokens, glyph geometry, typography stack, motion conventions, surface treatments, do/don't list. Locked at v2.7.9.
- **`OraculusMarkIcon`** — gold paint-swirl React component replacing the v2.6-era `OctopusMarkIcon` (headphones-and-tentacles silhouette). Three deprecated aliases (`OctopusMarkIcon`, `StrategyMarkIcon`, `OdiaMarkIcon`) repointed to the new component so every existing call site keeps compiling.
- **Cinematic Oraculus intro** — 25-second self-contained HTML+CSS+JS boot animation at `frontend/public/intro/index.html`. Five phases: deep grid → boot text → glyph assembly → equation/code → declaration. Plays on first launch (changed to every launch in v2.8.0).
- **`IntroGate` + `IntroFrame` + intro Zustand store** — orchestration. SSR-safe, respects `prefers-reduced-motion`, autofocused Skip button at 3s, Escape exits, 30s fallback timer.
- **Settings → Presentation card** with "Show on next launch" replay button.
- **`scripts/build-icons.mjs`** — sharp-based PNG rasterizer (no pandoc/rsvg-convert needed). `electron-builder` auto-derives `.ico` + `.icns` from the master `icon.png`.
- **5 vetted reference images** in `docs/brand/reference/`.

### Changed
- **`manifest.json` + `layout.tsx` theme color** → `#07070A` (`--smoke-950`); `appleWebApp.statusBarStyle` → `"black-translucent"`.
- **Service worker** cache `odia-shell-v1` → `odia-shell-v3`.

---

## [2.7.7] – [2.7.8] - 2026-04-25 — Gemstone Propagation + AppLink Hotfix

### Added
- **Gemstone palette propagation** (Y1–Y5) — vibrant neon emerald + matte gold dual-edge tokens propagated platform-wide. Crystallized facet panel utility (`.gem-panel-faceted` — 12-vertex quartz silhouette via clip-path). Sidebar, topbar, mobile bottom-tab bar, base components, every Dashboard card restyled. Severity strip on Dashboard rewired to the live `/api/v1/dashboard/summary` endpoint.

### Fixed
- **v2.7.8** — `<AppLink>` and SVG `IconProps` interfaces now declare `style?: React.CSSProperties` so the gem-palette inline-style approach used in DashboardLayout passes the Next.js typecheck. v2.7.7's tag failed CI at the typecheck step; v2.7.8 supersedes it.

---

## [2.7.6] - 2026-04-25 — X1–X5 Functional Pass

### Added
- **`/api/v1/dashboard/summary`** endpoint backing the Analysis Summary card on the home page (was previously reading from a Zustand store that production audits never wrote to).
- **Frozen-aware jurisdiction discovery** + `POST /api/v1/dashboard/seed-jurisdictions` endpoint + "Seed Example Jurisdictions" trigger so RAIA Synthesis works on a fresh desktop install.
- **Legistar retrieval bridges into the upload-staging store** — downloads now appear in the Upload page's "files ready" table.
- **Audit pipeline records `MeshExecutionJob` rows** so the Orchestrator timeline reflects actual work.
- **Initial gemstone hero POC** on `frontend/app/page.tsx` (replaced the v2.7.5 W4 purple/platinum POC).

---

## [2.7.5] - 2026-04-25 — Manual Triggers Wired

### Added
- **ODIA-native `/api/v1/triggers/*` route family** bypasses the n8n token gate so the Manual Triggers panel works out of the box.
- **CCOPS Compliance scorecard** on HUD primitives.

### Changed
- **Ingest tab consolidated into Upload** (legacy redirect preserved at `/ingest`).

---

## [2.7.4] - 2026-04-24 — Quality Polish

### Fixed
- **Database initialization at startup** — closes silent-degrade gap where `get_db()` raised "DB not initialised".
- **Dynamic version pill** on the sidebar (was hardcoded literal).
- **Tri-state UX on Orchestrator executions** — distinguishes "loading" from "unavailable".
- **Three-state automation tile** (`READY` / `OFFLINE` / `NOT CONFIGURED`).

---

## [2.7.3] - 2026-04-23 — Audit-Fix Sprint (D1–D8)

### Added
- **MAS narrative templates** — plain-language audit-report narrative with statute citations.
- **Orchestrator page** — full task graph + execution timeline + agent status panels.
- **Electron window icon** — desktop title-bar icon now uses the bundled SVG/PNG.
- **`/api/v1/automation/*`** n8n proxy + n8n editor health gate on the Automation page.

### Fixed
- **General-path SeenHash deduplication** — desktop audits now skip duplicates on the SHA-256 hash, matching the n8n webhook flow.
- **Fail-loud PDF extraction** — silent text-extraction failures now emit `ingestion:extraction-failure` HIGH-severity findings.
- **Tile contrast** — severity tiles redrawn to HUD primitives (was unreadable on dark theme).

---

## [2.7.2] - 2026-04-23 — Desktop Build Stabilization

### Fixed
- **PyInstaller cold-start** — uvicorn switched to `create_app` factory pattern (was bare `app` object); main.js startup timeout 30s → 60s.
- **n8n integration** — desktop builds now ship the `automation`/`cpra`/`field`/`webhook`/`triggers` route modules in PyInstaller hiddenimports.

---

## [2.7.1] - 2026-04-23 — HUD Design System Upgrade

### Added
- **Design token system** — `globals.css` rewritten with full token hierarchy. `slate-950 / amber-500 / cyan-400` palette. Five panel variants (`hud-panel`, `-data`, `-flow`, `-critical`, `-inset`). Severity pills, metric readouts, workflow nodes, dividers, HUD buttons, HUD tables. Print mode flattens to litigation-grade B&W.
- **Violet automation channel** — workflow state distinct from audit data.
- **Motion system** — `odia-pulse`, `odia-fade`, `odia-sheen`, `odia-scan`, `odia-tick`, `odia-breath`, `hud-bracket-pulse`. All respect `prefers-reduced-motion: reduce`.

---

## [2.7.0] - 2026-04-23 — n8n Integration

### Added
- **Token-gated webhook surface** — 5 endpoints under `/api/v1/webhook/*` (ingest-and-analyze, batch-ingest, status, synthesize, health). Token validated against `ODIA_WEBHOOK_TOKEN` via constant-time comparison. Refuses to register if the env var is unset.
- **`docker-compose.n8n.yml`** — one-command stack for backend + Postgres + n8n with shared inbox volume.
- **DB models** — `SeenHash`, `WebhookAuditLog`, `CPRARequest`, `FieldObservation`.
- **RAIA service package** — Recursion Analysis Investigative Audit cross-jurisdictional pattern detection.
- **CPRA + field-verification routes** — `/api/v1/cpra/deadlines-within/{72h,7d,30d}`, field observations under `/api/v1/field/*`.
- **Automation page** — first-class n8n workflow + execution viewer.

---

## [2.5.x] – [2.6.x] - 2026-04-22 to 2026-04-23 — Architectural Tier Boundary + Octopus Mark Era

### Added
- **Three-tier architecture analysis** — Tier 1 forensic, Tier 2 extended, Tier 3 recursive synthesis boundary documented.
- **Jurisdiction auto-loader** (`config.jurisdiction_loader.discover_jurisdictions`) — scans `config/multi_jurisdiction/` for per-jurisdiction subdirectories.
- **Octopus mark** introduced as the v2.6 brand glyph (later replaced at v2.7.9 with the Oraculus gold-swirl).
- **Synthesis page** — cross-audit aggregation report, DOCX export.
- **Platform-aware OCR fallback** — Tesseract bundled on Windows; macOS/Linux use system-installed binaries via PATH.

### Fixed
- **Fiscal regex** — appropriation-trail detector tightened to reduce false positives on routine encumbrance language.

---

## [2.4.0] - 2026-04-22 — 4-Platform Installer Release

### Added
- **OCR-bundled Windows installer** — Tesseract + Poppler binaries shipped inside the PyInstaller bundle so scanned PDFs work out of the box.
- **macOS arm64 + x64 installers** built on separate runners.
- **Linux AppImage** with libfuse2 dependency documented.

---

## [2.3.0] - 2026-04-21 — Detector Pipeline Expansion

### Added
- **Vendor catalogue + grant-compliance detector** — JAG/COPS anti-supplanting, vendor-statutory-trigger mapping (Flock/Axon/Lexipol), 9th detector added to the audit pipeline.
- **Governance gap detector** rewritten with 7 distinct finding IDs (capability-without-council-approval, data-retention-gap, lexipol-boilerplate, consent-calendar-placement, sole-source-without-justification, auto-renewal-clause, transparency-portal-absence).
- **Surveillance detector** rewritten with vendor-specific statutory gap detection (ALPR/SB524, ALPR Privacy Act, BWC/CJIS, facial recognition, drone/AB481, AI report writing).

---

## [2.2.x] - 2026-04-18 — Detector Refinement

### Fixed
- **`_flatten_findings`** — was reading `result["findings"]` but `analyze_document` returns `result["anomalies"]` (caused 0 findings since v2.0).
- **Upload error messages** — show actual FastAPI `detail` / HTTP status instead of generic "Check that the server is running".
- **CI workflow hardening** — graceful npm fallback when `package-lock.json` absent.

### Added
- **8-detector analysis pipeline** restored and wired through `audit_engine.analyze_document`.
- **React error boundaries** (`frontend/app/error.tsx`, `global-error.tsx`).

---

## [2.1.x] - 2026-04-16 to 2026-04-17 — UI Patch Set + CI Heredoc Fix

### Fixed
- **CI hang on indented PYEOF** — extracted inline Python heredoc to standalone `scripts/fix_electron_paths.py`.
- **Electron `routeToFileURL` subpage navigation** — base URL now strips known route segments before computing root.
- **PyInstaller hiddenimports** — 21 modules added (route modules, auth stack, SQLAlchemy SQLite dialect, sklearn C extensions).

### Added
- **`OctopusMarkIcon` etc.** — self-contained inline SVG icon set (critical for Electron file:// rendering).
- **Dashboard cards** — `SystemStatusCard`, `AnalysisSummaryCard`, `DetectorStatusCard`, `JurisdictionCard`.
- **`navigation.tsx`** — `useAppNavigate`, `AppLink`, `isFileProtocol`, `routeToFileURL` Electron file:// helpers.

---

## [2.1.1] - 2026-04-13 — Desktop App Icons & macOS Multi-Arch Build Fix

Patch release fixing desktop application packaging and CI workflows introduced in v2.1.

### Fixed
- macOS desktop build now correctly produces separate x64 (macos-13) and arm64 (macos-latest) artifacts instead of a single hardcoded arch
- `release-desktop.yml` upgraded to `action-gh-release@v2`; per-platform build commands use the correct Electron targets
- `desktop-build.yml` split macOS job into separate x64 and arm64 runners
- `desktop/package.json` sets per-platform `artifactName` and removes hardcoded `mac.arch`

### Added
- `desktop/resources/icon.png` (512×512), `icon.ico` (multi-size), `icon.icns` (multi-size) — desktop application icons for all three platforms

### Docs
- README download table updated to reflect 4 platform entries (Windows, Linux, macOS arm64, macOS x64)
- `desktop/README.md` updated with separate macOS arm64/x64 entries and per-arch build commands

---

## [2.0.0] - 2026-03-13 — Platform Generalization Release

This release transforms ODIA from a jurisdiction-specific audit tool into a
general-purpose legal document ingestion, normalization, and anomaly auditing platform.
All jurisdiction-specific data has been removed; the platform is now configured via
`config/jurisdiction.json` and `config/corpus_manifest.json`.

### Breaking Changes
- `src/oraculus/` is now a thin backward-compatibility wrapper only; all new code lives
  in `src/oraculus_di_auditor/`
- Anomaly detector return shape changed: `{id, issue, severity, layer, details}` replaces
  the previous `{type, description, severity, evidence}` shape
- `config/jurisdiction.json` must be present for jurisdiction-aware analysis (optional;
  system degrades gracefully when absent)

### Added

#### Anomaly Detectors (5 new)
- `procurement_timeline` — detects contracts executed before governing-body authorization date
- `signature_chain` — detects unsigned, partially signed, or placeholder-signed documents
- `scope_expansion` — detects amendment-as-procurement pattern (significant scope creep)
- `governance_gap` — detects surveillance capabilities deployed without governance documentation
- `administrative_integrity` — detects missing final actions, blank required fields, retroactive authorizations

#### API Endpoints (3 new)
- `POST /analyze/detailed` — per-detector anomaly breakdown with severity summary and weighted score
- `GET /detectors` — registry of all 8 detectors with descriptions and anomaly types
- `POST /analyze/batch` — multi-document analysis with cross-document procurement timeline patterns

#### Jurisdiction & Configuration System
- `src/oraculus_di_auditor/config/jurisdiction_loader.py` — `JurisdictionConfig` dataclass,
  `load_jurisdiction_config()`, `get_config()` singleton, `clear_config_cache()`
- `config/jurisdiction.json` (gitignored) — active jurisdiction config
- `config/corpus_manifest.example.json` — template for corpus configuration
- `config/corpus_manifest.json` — maps corpus IDs to meeting dates

#### Audit CLI
- `scripts/run_audit.py` — end-to-end audit CLI: ingest → analyze → report (JSON + Markdown)

#### Frontend (Next.js 14 dashboard)
- `frontend/lib/types/api.ts` — canonical `Anomaly`, `DetailedAnalysisResult`, `DetectorInfo`,
  `JurisdictionInfo` TypeScript types
- `frontend/lib/api/client.ts` — `APIClient` singleton covering all backend endpoints
- `frontend/lib/stores/analysis.ts` — Zustand store with `detailedAnalyses` state
- `frontend/components/anomalies/DetectorGroupPanel.tsx` — collapsible per-detector panels
  with severity color-coding and expandable evidence
- `frontend/components/analysis/SeverityChart.tsx` — recharts donut chart
- `frontend/components/dashboard/JurisdictionCard.tsx` — live jurisdiction config display
- `frontend/components/dashboard/DetectorStatusCard.tsx` — live detector registry display
- Dashboard severity count cards; anomalies page document selector and severity filter;
  analysis page top-10 findings panel

#### Documentation
- `CONTRIBUTING.md` — contributor guide with branch, commit, and test conventions
- `docs/PHASES.md` — phase-by-phase engine reference (Phases 5–20)
- `docs/phases/` — 25 phase overview and implementation files (relocated from repo root)
- `README.md` — full rewrite (~167 lines, clean public-facing structure)

### Changed
- Unified package structure: `src/oraculus/` reduced to thin wrapper; `src/oraculus_di_auditor/`
  is the sole authoritative package
- Higher-phase naming: abstract/mythological names replaced with plain engineering terms
  (rec17, rgk18, aei19, aer20, mesh, otge15, qdcl, scalar_convergence)
- `scripts/corpus_manager.py` now loads from `config/corpus_manifest.json`
- `datetime.utcnow()` replaced with `datetime.now(UTC)` throughout (deprecation fix)
- All `open()` calls use `encoding="utf-8"` for Windows cp1252 compatibility
- Unicode `✓`/`✗` in scripts replaced with `[OK]`/`[FAIL]`
- Phase documentation files moved from repo root into `docs/phases/`

### Removed
- All jurisdiction-specific data (city names, Legistar URLs, personnel names,
  dollar amounts from any specific audit)
- Jurisdiction-specific hardcoded configurations

### Tests
- **2275 passing, 9 skipped, 0 failing**
- New test files: `tests/test_jurisdiction_config.py`, `tests/test_pipeline_jurisdiction.py`,
  `tests/test_run_audit.py`, `tests/test_api_detectors.py` (21 tests for new API endpoints)
- 9 skipped tests are data-dependent corpus/transparency tests with explicit skip markers

---

## 2024-12-29 - Audit Triage & Reporting Pipeline Scaffolding

### Added - Audit Triage & Reporting Infrastructure

**Complete audit workflow scaffolding for manual auditing, legally-defensible reports, and small-model evaluations on lightweight hardware.**

#### Core Files
- **`audit_manifest.schema.json`** - JSON Schema for document manifest validation with fields for document metadata, extraction info, forensics, flags, citations, notes, redaction status, and chain-of-custody
- **`config/defaults.yaml`** - Repository-level configuration for manifests, extraction, PDFs (external storage by default), Ollama, RAG/retrieval, redaction (manual review required), OCR, reports, security, and evaluation
- **`config/ollama_config.yaml`** - Ollama-specific configuration with model settings, generation parameters, system prompts per category, and response validation

#### Scripts
- **`scripts/triage.py`** - Executable CLI tool for creating/updating manifests with SHA-256 checksums, flags (severity: low/medium/high/critical), notes, and chain-of-custody tracking
- **`scripts/ocr_sample.py`** - Lightweight OCR runner using Pillow + pytesseract with optional deskewing via opencv-python; extracts text to `extraction/` and updates manifest metadata
- **`scripts/render_report.py`** - Report renderer using Jinja2 templates; generates Markdown reports with optional HTML/PDF via pandoc or wkhtmltopdf
- **`scripts/eval_harness.py`** - Ollama evaluation harness with TF-IDF-based retrieval (scikit-learn) or naive substring fallback; records model responses, latency, context, and stores logs under `reports/eval/`
- **`scripts/auto_issue_generator.py`** - GitHub issue draft generator for high-severity findings; creates markdown files in `reports/issues/` with pre-filled audit finding templates

#### Templates & Queries
- **`templates/report_template.md`** - Jinja2 Markdown template for executive summary, findings list, evidence manifest table, methodology, legal checks, recommendations, and appendices
- **`queries/sample_queries.json`** - 20 sample audit queries across 6 categories: factual_retrieval, contradiction_detection, irb_consent_check, infrastructure_concern, grant_incentive_detection, executive_summary

#### Compliance & Governance
- **`compliance_checklist.md`** - Four fault-line compliance framework with detailed checklists for DOJ certification, IRB consent (28 C.F.R. Part 46), infrastructure policy, and federal grant incentives; includes red flags, immediate actions, and per-document assessment forms

#### GitHub Integration
- **`.github/ISSUE_TEMPLATE/audit_finding.md`** - Issue template for reporting audit findings with fields for document ID, manifest path, severity, fault-line category, evidence, impact assessment, recommended actions, and chain-of-custody

#### Directory Structure
- **`manifests/`** - Document manifest storage with README
- **`extraction/`** - Extracted text storage with README
- **`reports/eval/`** - Evaluation results directory
- **`reports/issues/`** - Generated issue drafts directory

#### Tests
- **`tests/test_triage_basic.py`** - Unit tests for triage.py covering manifest creation, flag addition, note addition, updates, checksum calculation, and validation

### Documentation
- **README.md** - Added comprehensive "Audit Triage & Report Scaffolding" section with quick start guide, configuration instructions, security/legal warnings, compliance checklist overview, files added, requirements, and next steps for repo owner
- All scripts include detailed docstrings and command-line help with usage examples

### Features
- **Manual Audit Workflow**: Triage script for creating manifests with flags and notes; no heavy dependencies (stdlib + hashlib)
- **OCR Integration**: Pytesseract-based text extraction with confidence scoring and optional deskewing
- **Report Generation**: Jinja2-based Markdown reports with fallback support for missing pandoc/wkhtmltopdf
- **Ollama Evaluation**: Small model evaluation with local inference, TF-IDF retrieval, latency tracking, and structured logging
- **Compliance Framework**: Four fault-line checklist covering DOJ, IRB, Infrastructure, and Grant compliance
- **Security-First**: External PDF storage by default, manual redaction review required, no automatic uploads, chain-of-custody tracking
- **Low-Compute Design**: Runs on lightweight hardware (HP notebook); all processing local; no cloud dependencies

### Security & Legal
- No automated external uploads of PDFs or manifests
- Default configuration stores PDFs externally (configurable via `config/defaults.yaml`)
- Redaction placeholders only; manual review required before disclosure
- Chain-of-custody tracking with SHA-256 checksums and timestamps
- Explicit warning: tooling does not constitute legal advice; consult counsel

### Requirements
- Core: Jinja2, pytesseract, Pillow, pdf2image, scikit-learn (optional but recommended)
- Optional: opencv-python (deskewing), pandoc (reports), wkhtmltopdf (PDF fallback), requests (Ollama HTTP)
- System: tesseract-ocr, Ollama (optional for evaluation)

### Next Steps for Repo Owner
1. Confirm manifest storage location (in-repo vs. external)
2. Confirm redaction policy (placeholders only vs. enabled)
3. Confirm Ollama model names for testing

---

## 2025-12-04
- Trigger CI for PR #37 by adding a small doc change to ensure GitHub Actions picks up the latest push to `copilot/initiate-full-ingestion`.

All notable changes to the Oraculus Decimus Intellect Analyst project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - November 17, 2025
- **Documentation** (40.6 KB total):
  - `docs/audit-methodology.md` - Multi-layered anomaly detection framework
  - `docs/recursive-scalar-model.md` - Mathematical framework for pattern lattice analysis
  - `docs/developer-setup.md` - Comprehensive developer onboarding guide
  - `docs/database-design.md` - Database architecture and implementation plan
  - `VALIDATION_REPORT.md` - Project completion assessment (48% complete toward v1.0)
- **API Interface**:
  - `src/oraculus_di_auditor/interface/api.py` - FastAPI REST API stub
  - Endpoints: `/api/v1/health`, `/api/v1/analyze`, `/api/v1/info`
- **Test Coverage** (11 new tests):
  - `tests/test_constitutional_detector.py` - Constitutional anomaly tests
  - `tests/test_surveillance_detector.py` - Surveillance outsourcing tests
  - Enhanced `tests/test_fiscal_detector.py` - Appropriation trail tests

### Enhanced - November 17, 2025
- **Fiscal Detector** (`fiscal.py`):
  - Appropriation trail detection (fiscal amounts without appropriation keywords)
  - Fiscal amount pattern matching ($1,000,000, $1M formats)
  - New anomaly: `fiscal:amount-without-appropriation` (medium severity)
- **Constitutional Detector** (`constitutional.py`):
  - Broad delegation pattern detection (Secretary may determine, as deemed necessary)
  - Intelligible principle checking (limiting standards detection)
  - New anomaly: `constitutional:broad-delegation` (medium severity)
- **Surveillance Detector** (`surveillance.py`):
  - Surveillance keyword detection (biometric, facial recognition, monitoring, tracking)
  - Contractor involvement detection (contractor, vendor, third party)
  - Privacy safeguard checking (warrant, court order, minimization)
  - New anomalies: `surveillance:outsourced-without-safeguards` (high), `surveillance:outsourced-with-safeguards` (low)
- **Scalar Core** (`scalar_core.py`):
  - Weighted scoring by severity (low: 0.02, medium: 0.05, high: 0.10)
  - Pattern lattice coherence bonus (up to 0.02 for strong provenance)
  - More nuanced confidence scoring

### Validated
- ✅ 143/143 tests passing (100% pass rate)
- ✅ All ruff checks passing (zero linting errors)
- ✅ CodeQL security scan: 0 vulnerabilities
- ✅ Pre-commit hooks functional
- ✅ CI/CD pipeline operational

### Added - Earlier
- Complete foundational scaffold implementation per specification
- Core modules: `cli.py`, `config.py`, `ingest.py`, `normalize.py`, `embeddings.py`, `retriever.py`, `analyzer.py`, `reporter.py`, `utils.py`
- Documentation: `ARCHITECTURE.md`, `PHASE_PLAN.md`, `DATA_POLICY.md`, `PROVENANCE.md`
- Data directories: `cases/`, `statutes/`, `vectors/` with proper gitignore
- Test suite for all new modules
- Tool scripts: `import_examples.sh`, `make_local_env.ps1`
- Requirements files: `requirements.txt`, `dev-requirements.txt`
- CLI interface for document ingestion

### Features
- Multi-format document ingestion (TXT, JSON, PDF, XML)
- Text normalization with configurable chunking (2000 chars, 200 overlap)
- TF-IDF based deterministic embeddings (sklearn)
- Vector storage and cosine similarity search
- Advanced anomaly detection:
  - Fiscal: Appropriation trail analysis
  - Constitutional: Broad delegation detection
  - Surveillance: Outsourcing and safeguard validation
  - Long sentence detector (>1000 chars)
  - Cross-reference mismatch detector
  - Contradictory date detector
- Recursive scalar scoring with weighted severity penalties
- JSON and CSV report generation with provenance
- REST API interface (FastAPI)
- Full test coverage for core modules

### Infrastructure
- Parallel module structure: `src/oraculus_di_auditor/` alongside existing `src/oraculus/`
- Backward compatible with existing legislative ingestion system
- Privacy-first data policy with gitignored sensitive directories
- Comprehensive architecture documentation
- Database design ready for implementation

## [0.1.0] - 2025-11-12

### Added
- Initial project structure from PR #7
- Legislative document loader with JSON, TXT, PDF support
- Provenance tracking system with reference graph
- Anomaly detection for missing fields and broken references
- Confidence scoring system
- GitHub Actions CI workflow
- Basic test infrastructure

### Infrastructure  
- Package structure under `src/oraculus/`
- JSON Schema validation
- SHA-256 hashing for document integrity
- Test fixtures and comprehensive test suite
