# ODIA Mobile

Native mobile application for the ODIA (Oraculus DI Auditor) legal document analysis platform, built with React Native and Expo.

## Overview

ODIA Mobile provides **complete on-device** legal document analysis. All nine Python analysis detectors have been ported to TypeScript and run entirely on the device — no network connection or server required.

### Key Features

- **Offline-first**: All analysis runs on-device with zero network requirements
- **Full detector suite**: All 9 Python detectors ported to TypeScript with identical behavior
- **Camera capture**: Document capture with OCR support (extensible)
- **Secure storage**: All data stored locally using AsyncStorage + FileSystem
- **Dark mode**: Full dark/light theme support following platform guidelines
- **Accessibility**: VoiceOver/TalkBack support, proper ARIA labels

### Analysis Detectors

| Detector | Layer | Description |
|----------|-------|-------------|
| Fiscal Trail | `fiscal` | Gaps in appropriation and fiscal lineage |
| Constitutional Conformity | `constitutional` | Unconstitutional delegation patterns |
| Surveillance Outsourcing | `surveillance` | Private vendor surveillance risks |
| Procurement Timeline | `procurement` | Contracts executed before authorization |
| Governance Gap | `governance` | Capabilities without governance docs |
| Signature Chain | `signature` | Unsigned or placeholder-signed documents |
| Administrative Integrity | `administrative` | Missing actions, blank fields, misfiling |
| Scope Expansion | `scope` | Amendment-as-procurement patterns |
| Cross-Reference | `cross-ref` | Cross-jurisdiction legal conflicts |

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Expo CLI (`npx expo`)
- For iOS: Xcode 15+ and CocoaPods
- For Android: Android Studio with SDK 34+

### Installation

```bash
cd mobile
npm install
```

### Development

```bash
# Start Expo dev server
npx expo start

# Run on iOS simulator
npx expo start --ios

# Run on Android emulator
npx expo start --android
```

### Testing

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run specific detector tests
npx jest __tests__/detectors/fiscal.test.ts
```

### Type Checking

```bash
npm run typecheck
```

## Architecture

```
mobile/
├── app/                    # Expo Router screens
│   ├── _layout.tsx         # Root navigation layout
│   ├── index.tsx           # Home (document list)
│   ├── analyze.tsx         # Document input + analysis
│   ├── results.tsx         # Analysis results display
│   └── settings.tsx        # App settings
├── components/             # Shared UI components
│   ├── AnomalyCard.tsx     # Anomaly finding display
│   ├── LoadingOverlay.tsx  # Loading indicator
│   └── EmptyState.tsx      # Empty state placeholder
├── lib/                    # Core logic
│   ├── analysis/           # Analysis engine (Python port)
│   │   ├── types.ts        # TypeScript type definitions
│   │   ├── textUtils.ts    # Text extraction utility
│   │   ├── scalarCore.ts   # Recursive scalar scoring
│   │   ├── auditEngine.ts  # Unified analysis entry point
│   │   ├── pipeline.ts     # Full analysis pipeline
│   │   └── detectors/      # Individual detector ports
│   ├── storage/            # Offline storage layer
│   └── ocr/                # Camera + OCR module
├── __tests__/              # Test suite
│   ├── detectors/          # Detector unit tests
│   ├── storage/            # Storage tests
│   └── textUtils.test.ts   # Utility tests
└── docs/                   # Documentation
```

## Performance

| Metric | Target | Notes |
|--------|--------|-------|
| Document analysis | <5s for 10-page | On-device processing |
| App launch | <3s cold start | Optimized bundle |
| Memory usage | <150MB | Analysis on-demand |
| Battery impact | Minimal | No background processing |

## License

MIT — see [LICENSE](../LICENSE) in the repository root.
