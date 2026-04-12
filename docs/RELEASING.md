# ODIA Release Process

## Overview

ODIA uses automated GitHub Actions workflows to build and publish desktop application releases. This document describes the release process and troubleshooting steps.

## Automated Release Process

### Prerequisites

- [ ] All tests passing on `master` branch
- [ ] Desktop app builds successfully locally (optional verification)
- [ ] Version numbers updated in:
  - `pyproject.toml` (line 7)
  - `desktop/package.json` (line 3)
- [ ] CHANGELOG.md updated (if exists) or release notes prepared
- [ ] README.md download links point to correct version

### Creating a Release

1. **Ensure you're on the latest master:**
   ```bash
   git checkout master
   git pull origin master
   ```

2. **Create and push the version tag:**
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

3. **Monitor the build:**
   - Go to: https://github.com/SynTechRev/ODIA/actions
   - Watch the "Build and Release Desktop Apps" workflow
   - Expected duration: 15-20 minutes
   - Three jobs run in parallel (Windows, macOS, Linux)

4. **Verify the release:**
   - Check: https://github.com/SynTechRev/ODIA/releases
   - Verify three installers are attached:
     - `ODIA-Setup-X.Y.Z.exe` (Windows)
     - `ODIA-X.Y.Z.dmg` (macOS)
     - `ODIA-X.Y.Z.AppImage` (Linux)
   - Test download links work
   - Download and test installers (recommended)

### What the Workflow Does

The `.github/workflows/release-desktop.yml` workflow:

1. **Builds Python backend** using PyInstaller
2. **Builds frontend** as static export for Electron
3. **Creates native installers** using electron-builder:
   - **Windows:** NSIS installer (`.exe`)
   - **macOS:** DMG disk image (`.dmg`) - Universal binary (x64 + arm64)
   - **Linux:** AppImage (`.AppImage`)
4. **Creates GitHub Release** with auto-generated release notes
5. **Uploads installers** as release assets

### Version Numbering

Follow Semantic Versioning (semver): `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes, incompatible API changes
- **MINOR:** New features, backwards-compatible
- **PATCH:** Bug fixes, backwards-compatible

Examples:
- `v2.1.0` → `v2.1.1` (bug fix)
- `v2.1.0` → `v2.2.0` (new feature)
- `v2.1.0` → `v3.0.0` (breaking change)

---

## Manual Release (Fallback)

If the automated workflow fails, you can build and release manually.

### Local Build Requirements

**All Platforms:**
- Node.js 20+
- Python 3.11+
- Git

**Platform-Specific:**
- **Windows:** Windows 10+ (for Windows builds)
- **macOS:** macOS 10.15+ with Xcode Command Line Tools (for macOS builds)
- **Linux:** Ubuntu 18.04+ with build-essential, fakeroot, rpm, libfuse2

### Manual Build Steps

```bash
# 1. Install Python dependencies
pip install -e ".[dev]"
pip install pyinstaller

# 2. Build Python backend
cd desktop
npm ci
npm run build:backend

# 3. Build frontend for Electron
cd ../frontend
npm ci
ELECTRON_BUILD=1 npm run build

# 4. Copy frontend to desktop build directory
cd ..
mkdir -p desktop/build/frontend
cp -r frontend/out/. desktop/build/frontend/

# 5. Build installer for your platform
cd desktop
npm run build:win     # Windows
npm run build:mac     # macOS
npm run build:linux   # Linux

# Installers output to: desktop/dist/
```

### Manual Release Creation

1. Go to: https://github.com/SynTechRev/ODIA/releases/new
2. **Tag:** `v2.1.0` (create new tag)
3. **Title:** `ODIA v2.1.0 - Desktop Release`
4. **Description:** Add release notes (see template below)
5. **Attach files:** Upload installers from `desktop/dist/`
6. **Publish release**

---

## Release Notes Template

```markdown
## ODIA v2.1.0

### 🎉 First Official Release

This is the first official release of ODIA (Oraculus DI Auditor) featuring desktop applications for Windows, macOS, and Linux.

### 📱 New Features

- **Desktop Application:** Standalone Electron app for offline document analysis
  - Native file dialogs
  - Automatic Python backend management
  - Cross-platform support (Windows, macOS, Linux)

- **Mobile Application:** React Native/Expo mobile app (source available)
  - 9 TypeScript-ported analysis detectors
  - Offline-first architecture
  - 118 tests at 97% coverage

### 🔍 Analysis Capabilities

- Fiscal anomaly detection
- Constitutional issues analysis
- Surveillance concerns identification
- Procurement timeline analysis
- Cross-jurisdiction boundary detection

### 📥 Downloads

| Platform | File | Size |
|----------|------|------|
| Windows (x64) | ODIA-Setup-2.1.0.exe | ~XXX MB |
| macOS (Universal) | ODIA-2.1.0.dmg | ~XXX MB |
| Linux (x64) | ODIA-2.1.0.AppImage | ~XXX MB |

### 📚 Documentation

- [Desktop App README](https://github.com/SynTechRev/ODIA/blob/master/desktop/README.md)
- [Quick Start Guide](https://github.com/SynTechRev/ODIA/blob/master/QUICKSTART.md)
- [Architecture Overview](https://github.com/SynTechRev/ODIA/blob/master/docs/ARCHITECTURE.md)

### 🐛 Known Issues

None reported yet. Please report issues at https://github.com/SynTechRev/ODIA/issues

### 🙏 Acknowledgments

Built with contributions from the Copilot coding agent and the open-source community.

---

**Full Changelog**: https://github.com/SynTechRev/ODIA/commits/v2.1.0
```

---

## Troubleshooting

### Build Fails on GitHub Actions

**Check the logs:**
1. Go to https://github.com/SynTechRev/ODIA/actions
2. Click on the failed workflow run
3. Expand the failed job
4. Review error messages

**Common issues:**

| Error | Cause | Fix |
|-------|-------|-----|
| `frontend/out not found` | Frontend build failed | Check ELECTRON_BUILD env var is set |
| `PyInstaller failed` | Python dependencies missing | Verify requirements.txt complete |
| `electron-builder failed` | Missing native dependencies | Check platform-specific dependencies |
| `Permission denied` | File permissions issue | Check file modes in repo |

### Release Not Created

**Verify:**
- Tag was pushed: `git ls-remote --tags origin`
- Tag format is correct: `v*.*.*` (e.g., `v2.1.0`, not `2.1.0`)
- Workflow has `contents: write` permission (already configured)
- Workflow completed successfully without errors

### Download Links Return 404

**Possible causes:**
1. Release not published yet (still draft)
2. Asset file names don't match links
3. Using `/latest/` before any release exists

**Fix:**
- Use specific version in URLs: `/download/v2.1.0/filename`
- Verify exact filenames in release assets
- Ensure release is published (not draft)

### Installer Doesn't Run

**Windows:**
- "Windows protected your PC" → Click "More info" → "Run anyway"
- SmartScreen warning expected for unsigned executables

**macOS:**
- "Cannot be opened because it is from an unidentified developer"
- Right-click → Open → Confirm
- Or: System Preferences → Security & Privacy → "Open Anyway"

**Linux:**
- Make executable: `chmod +x ODIA-*.AppImage`
- Install FUSE: `sudo apt install libfuse2`

---

## Release Checklist

Use this checklist for each release:

### Pre-Release
- [ ] All tests passing on master
- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `desktop/package.json`
- [ ] README.md download links updated
- [ ] Release notes prepared

### Release
- [ ] Tag created and pushed
- [ ] GitHub Actions workflow triggered
- [ ] All three builds completed successfully
- [ ] Release created automatically
- [ ] Installers attached to release

### Post-Release
- [ ] Download links tested (no 404s)
- [ ] Windows installer tested
- [ ] macOS installer tested
- [ ] Linux AppImage tested
- [ ] GitHub Release marked as "Latest release"

---

## Future Automation Ideas

- **Automated version bumping** via conventional commits
- **Changelog generation** from commit messages
- **Pre-release builds** for testing
- **Code signing** for Windows/macOS installers
- **Auto-update mechanism** in desktop app
- **Homebrew formula** for macOS installation
- **Snap/Flatpak packages** for Linux

---

## Resources

- [Electron Builder Docs](https://www.electron.build/)
- [GitHub Actions - Creating Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
