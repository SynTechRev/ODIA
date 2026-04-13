# Release Notes Template

Use this template when creating release tags:

## Version X.Y.Z

### New Features
- List new features here
- Be specific about user-facing improvements

### Improvements
- Performance enhancements
- UI/UX improvements
- Documentation updates

### Bug Fixes
- List bugs fixed in this release
- Reference issue numbers when applicable

### Breaking Changes
- Document any breaking changes
- Provide migration instructions

### Known Issues
- List any known issues
- Provide workarounds if available

### Technical Details
- Dependencies updated
- Build system changes
- Internal refactoring

### Downloads

| Platform | File | Size |
|----------|------|------|
| Windows (x64) | ODIA-Setup-X.Y.Z.exe | ~XXX MB |
| macOS (Intel) | ODIA-X.Y.Z-x64.dmg | ~XXX MB |
| macOS (Apple Silicon) | ODIA-X.Y.Z-arm64.dmg | ~XXX MB |
| Linux (x64) | ODIA-X.Y.Z.AppImage | ~XXX MB |

### Installation Instructions

See [desktop/README.md](../desktop/README.md) for platform-specific installation instructions.

### Verification

All installers are signed with SHA-256 checksums. Verify downloads:

```bash
sha256sum ODIA-*
```
