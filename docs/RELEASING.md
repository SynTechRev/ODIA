# Release Process

## Automated Desktop Releases

Desktop application releases are automated via GitHub Actions
(`.github/workflows/release-desktop.yml`).

### Creating a New Release

1. **Update version** in relevant package files:

   ```bash
   # Update desktop/package.json version field to X.Y.Z
   # Update pyproject.toml version field to X.Y.Z
   ```

2. **Commit version bump:**

   ```bash
   git add desktop/package.json pyproject.toml
   git commit -m "chore: bump version to X.Y.Z"
   git push
   ```

3. **Create and push tag:**

   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

4. **GitHub Actions automatically:**
   - Builds desktop installers for Windows, macOS, and Linux
   - Creates a GitHub Release
   - Uploads installers as release assets
   - Generates release notes

5. **Verify release:**
   - Check <https://github.com/SynTechRev/ODIA/releases>
   - Test download links work
   - Download and test installers on each platform

### Manual Release (Fallback)

If the automated release fails:

```bash
# Build locally for your platform
cd desktop
npm run build:win     # Windows
npm run build:mac     # macOS
npm run build:linux   # Linux

# Manually create a release on GitHub and upload installers from desktop/dist/
```

## Release Checklist

- [ ] Version bumped in `desktop/package.json`
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG updated (if maintained)
- [ ] All tests passing (`pytest` and `cd desktop && npm test`)
- [ ] Desktop app builds successfully locally
- [ ] Tag created and pushed (`git tag vX.Y.Z && git push origin vX.Y.Z`)
- [ ] GitHub Actions workflow completes without errors
- [ ] Release appears on <https://github.com/SynTechRev/ODIA/releases>
- [ ] Download links tested
- [ ] Installers tested on target platforms (Windows, macOS, Linux)

## Workflow Overview

The release workflow (`.github/workflows/release-desktop.yml`) runs on:

- **Version tags** matching `v*.*.*` (e.g., `v2.1.0`) — full build + release
- **Manual dispatch** — full build + artifact upload (no release created unless on a tag)

The existing CI workflow (`.github/workflows/desktop-build.yml`) handles
continuous integration builds for pull requests and branch pushes.
