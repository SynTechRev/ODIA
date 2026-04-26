# O.D.I.A. — Automation Setup Guide

This guide walks an individual user through configuring O.D.I.A.'s
automation surface, from the simplest setup (no extra software) to a
full automated-ingestion stack with scheduled workflows.

> **Audience:** civic-accountability operators, journalists,
> independent researchers, oversight committee staff. Not
> developer-focused — if you've never used a terminal, you can still
> get to **Level 0** and run real audits today.

---

## Quick reference: which level do you need?

| You want to... | You need | Setup time | Maintenance |
|---|---|---|---|
| Audit documents you upload by hand. Run RAIA cross-jurisdictional synthesis on demand. Check CPRA deadlines for requests you've logged. | **Level 0** | 0 min — already works on the desktop install | None |
| Automatically ingest documents from CivicPlus / Legistar on a schedule (e.g. nightly). Get alerts when CPRA deadlines approach. Trigger workflows from external systems (Zapier, your own scripts, etc.). | **Level 1** | 15–30 min one-time | Docker container management |
| Watch live workflow executions inside the O.D.I.A. UI. Trigger n8n flows from inside O.D.I.A. instead of going to the n8n editor. | **Level 2** | +5 min on top of Level 1 | Same as Level 1 |

**Recommendation for most individuals:** start at Level 0. Move to
Level 1 only if your audit cadence is high enough that manually
clicking "Upload Document" + "Run Audit" feels repetitive. Level 2 is
a UX nicety, not a capability — it doesn't unlock anything new.

---

## Level 0 — Use what's already installed

Nothing to install beyond the O.D.I.A. desktop app itself.

### Step 1 — Install the desktop app

1. Go to https://github.com/SynTechRev/ODIA/releases
2. Download the installer for your platform:
   - **Windows:** `ODIA-Setup-2.7.8.exe`
   - **macOS Intel:** `ODIA-2.7.8-x64.dmg`
   - **macOS Apple Silicon:** `ODIA-2.7.8-arm64.dmg`
   - **Linux:** `ODIA-2.7.8.AppImage`
3. Run the installer. On Windows, expect Defender to scan the
   PyInstaller bundle for ~30–90 seconds before the app launches the
   first time — this is normal.

### Step 2 — Open the app and seed example jurisdictions

1. Launch O.D.I.A. The Dashboard tab opens.
2. Wait for the **Backend online** pill in the bottom-left to turn
   neon-emerald (can take up to 2 minutes on first launch while
   antivirus finishes scanning the bundled Python).
3. Open the **Automation** tab.
4. Scroll to the **Manual Triggers** panel (bottom of the page).
5. Click **Seed Example Jurisdictions**. You should see:
   `Seeded 3 jurisdiction(s). RAIA Synthesis can now run.`

This copies three example jurisdiction configurations into your
user-writable config directory:

| Platform | Where the jurisdictions live |
|---|---|
| Windows | `%APPDATA%\ODIA\config\multi_jurisdiction\` |
| macOS | `~/Library/Application Support/ODIA/config/multi_jurisdiction/` |
| Linux | `~/.local/share/odia/config/multi_jurisdiction/` |

You can edit those JSON files in any text editor to add your own
jurisdictions later — see the "Adding your own jurisdiction" section
below.

### Step 3 — Run your first audit

1. Open the **Upload** tab.
2. Drag a PDF / TXT / JSON / XML document into the drop zone, or
   click to browse. (Want to try without your own files? Bookmark a
   PDF from any city's Legistar portal and download it first.)
3. Click **Run Audit on N file(s)**.
4. Watch the progress bar; on completion you're auto-redirected to
   the **Results** page with the findings.

### Step 4 — Run RAIA Synthesis (cross-jurisdictional)

Back on the **Automation** tab → **Manual Triggers** panel:

- **Run RAIA Synthesis** — runs the cross-jurisdictional pattern
  detection across every jurisdiction in your config dir. Returns
  patterns + a rendered markdown report.
- **Check CPRA Deadlines** — queries any California Public Records
  Act requests you've logged into the local DB and returns those
  closing within the next 72 hours.
- **Export Provenance Chain** — stub at Level 0 (returns 501 with a
  helpful error). Needs Level 1.

That's the whole Level 0 workflow. Day-to-day audit work doesn't
require anything beyond this.

### What Level 0 does NOT do

- ❌ Watch a city's Legistar portal and pull new documents automatically
- ❌ Send you an email/Slack alert when a CPRA deadline approaches
- ❌ Run nightly scrapes
- ❌ Accept webhook calls from external systems
- ❌ Litigation-grade Provenance Chain Export

For any of those, you need **Level 1**.

---

## Level 1 — Add scheduled automation (n8n + Postgres)

This level adds two background services to your machine: **n8n**
(workflow automation engine) and **Postgres** (database that backs
both n8n's execution history and an optional O.D.I.A. provenance
store). Both run inside Docker containers so they don't touch your
Windows/macOS/Linux installation.

### What Docker is and why we use it

A **container** is a sealed bubble that holds an app and everything
it needs to run — its own Python version, its own libraries, its own
config files. The bubble runs on your machine but doesn't share
anything with your normal install.

Why this matters:

- You don't have to install Postgres + n8n + Node.js + their
  dependencies on your computer
- Stopping/uninstalling is one command — nothing left behind
- Updates are clean (`docker compose pull` then restart)
- The same setup works identically on Windows, macOS, and Linux

**Docker Desktop** is the GUI app that runs containers on Windows
and macOS. **Docker Engine** is the same thing on Linux without the
GUI.

### Is Docker free?

Yes, for individuals and small teams.

- **Docker Desktop** is free for personal use, education,
  non-commercial open source, and small businesses (under ~250
  employees / under $10M annual revenue).
- **Docker Engine** (Linux) is fully open source, no license at all.

If you're a single person doing civic-accountability work, you
qualify for the free tier without question.

### Step 1 — Install Docker Desktop

**Windows / macOS:**

1. Go to https://www.docker.com/products/docker-desktop/
2. Click **Download for Windows** or **Download for Mac**
3. Run the installer (~600MB)
4. **Windows only:** the installer will set up WSL2 (Windows
   Subsystem for Linux) automatically if it isn't installed already
   — you may need to restart your computer once
5. After install, launch Docker Desktop. Wait ~30 seconds for the
   "Docker Desktop is running" indicator in the system tray
6. Open a terminal (PowerShell on Windows, Terminal on macOS) and
   verify:
   ```bash
   docker --version
   docker compose version
   ```
   Both should print version numbers.

**Linux:**

Use your distro's package manager. On Ubuntu / Debian:
```bash
sudo apt update
sudo apt install docker.io docker-compose-plugin
sudo usermod -aG docker $USER     # log out + back in for this to take effect
docker --version
```

### Step 2 — Get the docker-compose files

The desktop installer doesn't ship the compose files (the n8n stack
is optional infrastructure). You need the source repo for those:

```bash
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA
```

Don't have `git`? Download the source as a ZIP:
https://github.com/SynTechRev/ODIA/archive/refs/heads/master.zip
and unzip it.

You only need three files from the repo:
- `docker-compose.yml` (base stack)
- `docker-compose.n8n.yml` (n8n + Postgres overlay)
- `data/n8n-workflows/` (seed workflow definitions)

You can copy them somewhere convenient (e.g. `~/odia-stack/`).

### Step 3 — Generate secrets and create your `.env` file

In the directory containing the compose files, generate two random
tokens. Each command prints one line — copy each output to the
matching variable below.

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# → use this for ODIA_WEBHOOK_TOKEN

python -c "import secrets; print(secrets.token_urlsafe(32))"
# → use this for N8N_ENCRYPTION_KEY
```

(Don't have Python? Use https://www.random.org/passwords/?num=2&len=32&format=plain
for two strong random strings — same security.)

Create a file named `.env` (note the leading dot) with this content,
substituting your generated values + your own passwords:

```
ODIA_WEBHOOK_TOKEN=<paste first generated token here>
N8N_ENCRYPTION_KEY=<paste second generated token here>
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=<choose a strong password — you'll log in with this>
POSTGRES_PASSWORD=<choose another strong password>
N8N_HOST=localhost
TZ=America/Los_Angeles
```

> **Important:** the `.env` file contains secrets. Never commit it
> to git, never share it. The `.gitignore` in the repo already
> excludes it.

### Step 4 — Bring up the stack

From the directory containing the compose files + your `.env`:

```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d
```

This downloads the n8n + Postgres + ODIA backend images (~1GB
first-time, then cached) and starts them in the background. The
`-d` flag means "detached" — you get your terminal back.

Watch progress:

```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml ps
```

All three services (`postgres`, `n8n`, `backend`) should show
**healthy** within ~60 seconds.

### Step 5 — Verify n8n is reachable

Open in browser: http://localhost:5678

You should see the n8n login page. Log in with the
`N8N_BASIC_AUTH_USER` (default `admin`) and `N8N_BASIC_AUTH_PASSWORD`
you set in `.env`.

On first login, n8n imports the seed workflows from
`data/n8n-workflows/`. You should see them in the workflow list.

### Step 6 — Verify the O.D.I.A. backend picked up the token

```bash
curl http://localhost:8000/api/v1/webhook/health
```

Should return:
```json
{"status":"ok","tier1_ready":true,"tier2_ready":true,"webhook_token_configured":true}
```

If `webhook_token_configured` is `false`, the backend container
didn't see your `ODIA_WEBHOOK_TOKEN` — restart with:
```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml restart backend
```

### Step 7 — Connect the desktop app to the docker stack

This is the trickiest step. The desktop app's Python backend runs
inside the desktop bundle (port 18741), but the n8n container talks
to the docker stack's backend (port 8000). You have two options:

**Option A (recommended): keep them separate.**
- Desktop app stays at port 18741 (manual audits via the UI)
- Docker stack runs in parallel for n8n's scheduled / webhook flows
- Both write to the same shared database if you point the desktop
  app at the docker Postgres

To make the desktop app use the docker Postgres, set this env var
before launching the app:

```
ODIA_DB_URL=postgresql+psycopg://odia:<POSTGRES_PASSWORD>@localhost:5432/odia
```

On Windows, set it in System → Environment Variables.
On macOS / Linux, add to your shell profile (`~/.zshrc` or
`~/.bashrc`).

**Option B: skip the desktop app, use only the docker stack.**
- Open the docker backend's frontend at http://localhost:3000
  (served by nginx in the base compose stack)
- Same UI, same features — just runs in the browser instead of
  Electron

### Done — what works now

The webhook tile family on the Automation page should now show
**READY** (neon-emerald) instead of NOT CONFIGURED. The following
flows are now active:

- **WF-001 — CivicPlus Auto-Ingest:** detects new agendas / minutes
  on configured city Legistar portals and runs the audit pipeline
  automatically
- **WF-005 — CPRA Deadline Watcher:** runs daily; if any tracked
  CPRA request is within 72h of its statutory deadline, fires the
  alert action you configured (email, Slack, etc.)
- **WF-007 — Mesh Sync Hub:** orchestrates the multi-agent
  Phase-5 pipeline across documents
- **WF-010 — RAIA Synthesis Distributor:** ships the rendered DOCX
  from RAIA Synthesis to wherever you configured (Google Drive,
  Dropbox, S3)
- **WF-014 — Provenance Chain Export:** the previously-stub trigger
  on the Automation page now actually works (joins ODIA's
  WebhookAuditLog with n8n's execution history → litigation-grade
  DOCX)

You configure each workflow's destination (where to send alerts /
exports) by editing the workflow in the n8n editor at
http://localhost:5678 — point-and-click, no code required.

---

## Level 2 — Let the Automation page drive n8n directly

By default the Automation page can show the **n8n: OFFLINE** status
even when n8n is running, because the page proxies to n8n via an
API key it doesn't have yet.

### Step 1 — Get an n8n API key

1. In n8n at http://localhost:5678, go to **Settings** (bottom
   left) → **API**
2. Click **Create an API key**
3. Give it a label like "ODIA Desktop"
4. Copy the key — you won't see it again after closing the dialog

### Step 2 — Add it to your environment

Add to `.env`:

```
N8N_API_KEY=<paste the API key>
N8N_BASE_URL=http://localhost:5678
```

Restart the backend container so it picks up the new env vars:

```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml restart backend
```

### Step 3 — Verify

Reload the Automation page. The **n8n: OFFLINE** tiles should turn
**READY**, and the **Workflows** + **Recent Executions** panels
should populate with live data.

You can now click "Run" on any workflow tile from inside O.D.I.A.
without going to the n8n editor.

---

## Adding your own jurisdiction

Whether you're at Level 0, 1, or 2, you can add your own
jurisdiction by dropping a new subdirectory into your user-writable
config dir.

```
%APPDATA%\ODIA\config\multi_jurisdiction\           ← Windows
~/Library/Application Support/ODIA/config/multi_jurisdiction/   ← macOS
~/.local/share/odia/config/multi_jurisdiction/      ← Linux
```

Inside that dir, create a folder named after your jurisdiction
(e.g. `my_city`) containing at minimum a `jurisdiction.json`:

```json
{
  "name": "My City",
  "state": "CA",
  "country": "US",
  "legistar_base_url": "https://mycity.legistar.com",
  "meeting_type": "city-council"
}
```

Optionally add `agencies.json`, `corpus_manifest.json`, and
`source_urls.json` (see the `example_city_a` directory the Seed
button created for the schemas).

Restart the desktop app or the docker backend, and the new
jurisdiction shows up in RAIA Synthesis runs immediately.

---

## Privacy and data flow

O.D.I.A. is built for civic accountability work, which means
operators are often handling sensitive documents (whistleblower
submissions, draft FOIA requests, surveillance contracts) — so the
data flow matters.

| Setup | Where your documents go |
|---|---|
| **Level 0** | Documents stay on your machine. The Python backend is bundled inside the desktop app and runs locally — no documents leave your computer at any point. |
| **Level 1** | Same — the docker stack runs entirely on your machine. n8n is local. Postgres is local. The only outbound network calls are the ones you explicitly configure inside an n8n workflow (e.g. "send this CPRA alert to my email"). |
| **Level 2** | Same as Level 1 — Level 2 is purely a UI bridge. |

What ODIA never does, regardless of level:

- ❌ Send your documents to any cloud service
- ❌ Phone home with telemetry
- ❌ Require an API key to OpenAI / Anthropic / any LLM
- ❌ Require an internet connection after install (except for the
  optional Legistar fetch + any n8n actions you configure)

The only network calls the desktop app makes by default are:

- The frontend → backend on `127.0.0.1:18741` (localhost loopback)
- Optional: the Legistar fetch in the Upload tab → the public
  Legistar API (`webapi.legistar.com`)

You can audit the network behavior with any HTTP proxy or
`netstat` — there's nothing hidden.

---

## Troubleshooting

### Desktop app says "Backend offline" forever

The bundled Python backend takes 30–120 seconds to start on first
launch (antivirus scans every extracted Python module). If it's
been more than 2 minutes:

1. Check that no other ODIA instance is running (port 18741 conflict)
2. Quit ODIA completely (system-tray → quit)
3. Re-launch and wait 2 minutes

If it still fails: open the app logs.
- **Windows:** `%APPDATA%\ODIA\logs\backend.log`
- **macOS:** `~/Library/Logs/ODIA/backend.log`
- **Linux:** `~/.local/state/odia/logs/backend.log`

### "No jurisdictions" warning on RAIA Synthesis

The Seed button hasn't been clicked yet, or the user-writable
config dir is empty. Open the Automation tab → Manual Triggers →
**Seed Example Jurisdictions**. Then re-run RAIA Synthesis.

### Legistar retrieval downloads but files don't appear in the upload list

This was a v2.7.5 bug fixed in v2.7.6 (X3). If you're on v2.7.5 or
earlier, upgrade to v2.7.8+. If on v2.7.8 and still seeing it, check
the backend log for the line `Cannot register Legistar files into
upload store` — it'll tell you which file failed and why.

### Docker: `permission denied` on Linux

You need to be in the `docker` group:
```bash
sudo usermod -aG docker $USER
# log out + back in for this to take effect
```

### Docker: containers start but the n8n UI shows "Connection refused"

Probably a port conflict with another service on port 5678. Stop
the conflict or change n8n's port in `docker-compose.n8n.yml`
(`ports: - "8080:5678"` would put it at `http://localhost:8080`).

### `webhook_token_configured` is false even though I set the env var

The backend container needs a restart after env changes:
```bash
docker compose -f docker-compose.yml -f docker-compose.n8n.yml restart backend
```

### My antivirus quarantined the ODIA installer

False positive — PyInstaller bundles trip a lot of heuristic
scanners. The installer is unsigned (signing certs cost money). You
have two options:
1. Add an exception for `ODIA-Setup-2.7.8.exe` and
   `%LOCALAPPDATA%\Programs\ODIA\` in your antivirus
2. Build from source — `pip install -e .` then `python scripts/
   run_audit.py` for the CLI workflow, or `cd frontend && npm run
   dev` for the web UI

---

## Where to go from here

- **Day-to-day audit workflow:** see [QUICKSTART.md](../QUICKSTART.md)
  for the CLI commands and document layout
- **Compliance framework details:** see [COMPLIANCE_FRAMEWORK.md](COMPLIANCE_FRAMEWORK.md)
  for the 11 ACLU CCOPS mandate mappings
- **Multi-jurisdiction analysis:** see [MULTI_JURISDICTION.md](MULTI_JURISDICTION.md)
- **Legal reference dataset:** see [LEGAL_REFERENCE.md](LEGAL_REFERENCE.md)
- **Data provenance + chain of custody:** see [DATA_PROVENANCE.md](DATA_PROVENANCE.md)

If something in this guide is unclear or wrong, open an issue:
https://github.com/SynTechRev/ODIA/issues
