# ODIA Desktop Application

A standalone desktop application for ODIA that enables non-technical users to
run document analysis locally — no Python, Docker, or command-line knowledge
required.

## Features

- **Fully offline** — All document analysis runs on your machine. No data is
  sent to external servers.
- **Native file dialogs** — Select documents using your operating system's
  standard file picker.
- **Automatic backend** — The Python analysis engine starts and stops
  automatically with the application.
- **Cross-platform** — Available for Windows, macOS, and Linux.

## Quick Start

### Download

Download the latest installer for your platform from the
[Releases](https://github.com/SynTechRev/ODIA/releases) page:

| Platform | File |
|----------|------|
| Windows  | `ODIA-Setup-x.x.x.exe` |
| macOS    | `ODIA-x.x.x.dmg` |
| Linux    | `ODIA-x.x.x.AppImage` |

### Install and Run

1. **Windows**: Run the `.exe` installer and follow the prompts.
2. **macOS**: Open the `.dmg` and drag ODIA to your Applications folder.
3. **Linux**: Make the `.AppImage` executable (`chmod +x`) and run it.

The application will launch with the ODIA dashboard. The analysis backend
starts automatically in the background.

## Usage

### Analyzing Documents

1. Click **"Select Documents"** or use **File → Open** to choose documents.
2. Supported formats: PDF, TXT, JSON, XML (up to 50 MB each).
3. The analysis runs locally and results appear in the dashboard.
4. Export reports as Markdown, JSON, or plain text using **File → Save Report**.

### What Gets Analyzed

The desktop application uses the same analysis pipeline as the ODIA web
version:

- **Fiscal anomalies** — Missing provenance, appropriation trail gaps
- **Constitutional issues** — Broad delegation, due process concerns
- **Surveillance concerns** — Outsourcing patterns, privacy impacts
- **Procurement timeline** — Sole-source irregularities, timeline anomalies
- **Cross-jurisdiction** — Federal/state boundary violations

## Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- npm

### Install Dependencies

```bash
# From the repository root
pip install -e ".[dev]"

# Install desktop dependencies
cd desktop
npm install
```

### Run in Development Mode

```bash
# Terminal 1: Start the Next.js frontend in export mode
cd frontend
npm run build
# The static export goes to frontend/out/

# Terminal 2: Start the desktop app
cd desktop
npm run dev
```

In development mode, the app launches uvicorn directly using your local Python
installation instead of the bundled PyInstaller binary.

### Run Tests

```bash
cd desktop
npm test
```

### Build Installers

Building a distributable installer requires building both the Python backend
and the Next.js frontend first:

```bash
# 1. Build the Python backend (PyInstaller)
cd desktop
npm run build:backend

# 2. Build the frontend (Next.js static export)
cd ../frontend
npm run build

# 3. Copy frontend output
mkdir -p ../desktop/build/frontend
cp -r out/* ../desktop/build/frontend/

# 4. Build the installer for your platform
cd ../desktop
npm run build:win    # Windows
npm run build:mac    # macOS
npm run build:linux  # Linux
```

Installers are output to `desktop/dist/`.

## Architecture

```
desktop/
├── src/
│   ├── main.js        # Electron main process entry point
│   ├── preload.js     # Context bridge (renderer ↔ main IPC)
│   ├── backend.js     # Python backend lifecycle management
│   └── ipc.js         # IPC handler registration
├── test/
│   ├── ipc.test.js    # IPC handler unit tests
│   ├── backend.test.js # Backend lifecycle tests
│   └── preload.test.js # Preload API surface tests
├── scripts/
│   └── backend_entry.py  # PyInstaller entry point
├── resources/         # App icons and assets
├── odia-backend.spec  # PyInstaller build spec
├── package.json       # Electron + electron-builder config
└── jest.config.js     # Test configuration
```

### Security Model

- **Context isolation** enabled — renderer cannot access Node.js APIs directly.
- **Node integration** disabled — no `require()` in renderer code.
- **Sandbox** enabled — renderer process runs in a sandboxed environment.
- **Allowlisted IPC** — only specific channels are exposed via `contextBridge`.
- **URL validation** — external links only open http/https URLs.
- **File size limits** — documents over 50 MB are rejected.
- **Local-only backend** — backend binds to `127.0.0.1` only.

### Backend Lifecycle

1. On app start: `main.js` calls `startBackend()` which spawns the Python process.
2. Health polling: `waitForBackend()` polls `/api/v1/health` every second (30s timeout).
3. On app quit: `stopBackend()` sends SIGTERM, then SIGKILL after 5 seconds.

## Troubleshooting

### Backend fails to start

- **Check logs**: Open the developer console (View → Toggle Developer Tools)
  and check for error messages.
- **Port conflict**: The backend uses port 18741. If another process is using
  this port, close it and restart ODIA.
- **Antivirus**: Some antivirus software may block the backend executable.
  Add an exception for the ODIA application directory.

### "Frontend failed to load" error

- This usually means the frontend assets were not bundled correctly.
- Try reinstalling the application from a fresh download.

### Application is slow to start

- The first launch may take 10-15 seconds while the Python backend initializes.
- Subsequent launches are typically faster.
- If startup takes more than 30 seconds, check the logs for errors.

### Documents not loading

- Verify the document is in a supported format (PDF, TXT, JSON, XML).
- Check that the file is not larger than 50 MB.
- For PDF files, ensure they contain extractable text (not scanned images
  without OCR).

### macOS: "ODIA can't be opened because it is from an unidentified developer"

- Right-click the app and select "Open" from the context menu.
- Alternatively, go to System Preferences → Security & Privacy and click
  "Open Anyway".

### Linux: AppImage doesn't run

- Make sure the file is executable: `chmod +x ODIA-*.AppImage`
- You may need FUSE installed: `sudo apt install libfuse2`

## License

MIT — Copyright © 2025 Synthetic Technology Revolution
