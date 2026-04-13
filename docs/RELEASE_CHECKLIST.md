# ODIA Release Checklist

## Pre-Release Validation

- [ ] All tests passing on master
- [ ] Version numbers synchronized:
  - [ ] `pyproject.toml` version matches
  - [ ] `desktop/package.json` version matches
- [ ] CHANGELOG.md updated (if exists)
- [ ] Desktop app icons present in `desktop/resources/`
- [ ] README.md download links point to correct version

## Release Process

### 1. Create Release Tag

```bash
git checkout master
git pull origin master
git tag -a v2.1.0 -m "Release message here"
git push origin v2.1.0
```

### 2. Monitor Automated Build

- Go to: https://github.com/SynTechRev/ODIA/actions
- Watch "Build and Release Desktop Apps" workflow
- Expected duration: ~20 minutes
- 4 parallel jobs should complete successfully

### 3. Verify Release Artifacts

Release should be created at: https://github.com/SynTechRev/ODIA/releases/tag/v2.1.0

Expected artifacts:
- [ ] ODIA-Setup-2.1.0.exe (~180 MB)
- [ ] ODIA-2.1.0-x64.dmg (~200 MB)
- [ ] ODIA-2.1.0-arm64.dmg (~195 MB)
- [ ] ODIA-2.1.0.AppImage (~175 MB)

### 4. Test Download Links

Verify these URLs return actual files:
- https://github.com/SynTechRev/ODIA/releases/download/v2.1.0/ODIA-Setup-2.1.0.exe
- https://github.com/SynTechRev/ODIA/releases/download/v2.1.0/ODIA-2.1.0-x64.dmg
- https://github.com/SynTechRev/ODIA/releases/download/v2.1.0/ODIA-2.1.0-arm64.dmg
- https://github.com/SynTechRev/ODIA/releases/download/v2.1.0/ODIA-2.1.0.AppImage

### 5. Manual Testing (Recommended)

- [ ] Download Windows installer and verify it installs
- [ ] Download macOS DMG and verify it opens
- [ ] Download Linux AppImage and verify it executes
- [ ] Test app launches on each platform
- [ ] Verify analysis functionality works offline

### 6. Post-Release

- [ ] Mark release as "Latest release" (usually automatic)
- [ ] Announce release (optional)
- [ ] Close related issues/PRs
- [ ] Plan next version features

## Troubleshooting

### Build Fails

1. Check workflow logs: https://github.com/SynTechRev/ODIA/actions
2. Common issues:
   - npm ci errors → verify package-lock.json exists
   - Python dependencies → check requirements.txt
   - Platform-specific errors → review runner logs

### Release Not Created

- Verify tag was pushed: `git ls-remote --tags origin`
- Check tag format matches `v*.*.*` pattern
- Ensure workflow has `contents: write` permission

### Installers Missing

- Check if workflow completed all 4 jobs
- Verify artifact upload succeeded
- Check file patterns in release-desktop.yml match actual output
