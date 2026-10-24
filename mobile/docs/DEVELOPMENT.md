# ODIA Mobile — Development Guide

## Development Environment Setup

### Required Tools

1. **Node.js 18+**: Download from [nodejs.org](https://nodejs.org/)
2. **Expo CLI**: Included via `npx expo`
3. **TypeScript**: Included in devDependencies
4. **iOS Development** (macOS only):
   - Xcode 15+ from the Mac App Store
   - CocoaPods: `sudo gem install cocoapods`
5. **Android Development**:
   - Android Studio with SDK 34+
   - Android Emulator or physical device

### Project Setup

```bash
# Clone the repository
git clone https://github.com/SynTechRev/ODIA.git
cd ODIA/mobile

# Install dependencies
npm install

# Start development
npx expo start
```

## Project Structure

### Analysis Engine (`lib/analysis/`)

The analysis engine is a complete TypeScript port of the Python detectors in
`src/oraculus_di_auditor/analysis/`. Each detector is a pure function that
takes a normalized document and returns an array of anomaly records.

**Key files:**
- `types.ts` — All TypeScript interfaces and type definitions
- `textUtils.ts` — Text extraction utility (mirrors `text_utils.py`)
- `detectors/*.ts` — Individual detector implementations
- `scalarCore.ts` — Recursive scalar confidence scoring
- `auditEngine.ts` — Unified multi-detector runner
- `pipeline.ts` — Full analysis pipeline with preprocessing

### Storage Layer (`lib/storage/`)

Uses a pluggable storage backend pattern:
- **Production**: Inject `@react-native-async-storage/async-storage`
- **Testing**: Uses built-in `InMemoryStorage`

### OCR Module (`lib/ocr/`)

Provides interfaces for camera capture and text recognition:
- Camera permission management via `expo-camera`
- Extensible OCR provider interface (ready for ML Kit integration)

## Testing

### Running Tests

```bash
# All tests
npm test

# Watch mode
npx jest --watch

# Coverage report
npm run test:coverage

# Single file
npx jest __tests__/detectors/fiscal.test.ts
```

### Test Organization

Tests mirror the source structure:
- `__tests__/detectors/*.test.ts` — Detector unit tests
- `__tests__/storage/*.test.ts` — Storage layer tests
- `__tests__/textUtils.test.ts` — Utility tests

### Writing Tests

Follow existing patterns:
1. Test null/invalid input handling
2. Test positive detection (anomaly present)
3. Test negative detection (no anomaly)
4. Test edge cases (empty text, missing fields)
5. Verify exact field values match Python output

## Code Style

- **TypeScript strict mode** enabled
- **Named exports** preferred over default exports (except screens)
- **Pure functions** for all detectors — no side effects
- **Explicit types** — avoid `any` except in test assertions

## Building for Production

### iOS

```bash
npx expo build:ios
# Or with EAS Build:
npx eas build --platform ios
```

### Android

```bash
npx expo build:android
# Or with EAS Build:
npx eas build --platform android
```

## Troubleshooting

### Common Issues

**Metro bundler errors**: Clear cache with `npx expo start -c`

**TypeScript errors**: Run `npm run typecheck` to see all type issues

**Test failures**: Ensure you're running from the `mobile/` directory

**iOS pod install failures**: Run `cd ios && pod install --repo-update`
