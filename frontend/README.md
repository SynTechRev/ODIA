# Oraculus-DI-Auditor Frontend

Production-ready Next.js 14 frontend UI for comprehensive legal document analysis and anomaly detection.

## Quick Start

### Prerequisites
- Node.js 20+
- npm 10+

### Installation

```bash
npm install
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Environment Configuration

Create `.env.local` file:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Backend Setup

The frontend requires the Oraculus-DI-Auditor backend to be running:

```bash
# In the parent directory
cd ..
pip install -e .
uvicorn oraculus_di_auditor.interface.api:app --reload

# Configure CORS
export ORACULUS_CORS_ORIGINS="http://localhost:3000"
```

## Features

- 📊 **Dashboard**: System status, analysis summaries, quick actions
- 📄 **Document Ingest**: Upload and analyze documents (TXT, JSON)
- 🔍 **Analysis View**: Detailed findings with fiscal, constitutional, and surveillance detection
- 📚 **Document Browser**: View and manage all documents
- ⚠️ **Anomaly Explorer**: Browse and filter detected anomalies
- 🔀 **Orchestrator**: Multi-agent task coordination (Phase 5)
- ⚙️ **Settings**: UI preferences and configuration

## Architecture

### Technology Stack
- **Framework**: Next.js 14 (App Router, Turbopack)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **State**: Zustand with persistence
- **API**: Axios with custom client
- **Visualization**: Recharts, D3

### Project Structure

```
frontend/
├── app/              # Next.js pages
├── components/       # React components
├── lib/             # API client, stores, types
└── public/          # Static assets
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Key Components

### Pages
- `/` - Dashboard
- `/ingest` - Document uploader
- `/analysis` - Analysis results
- `/documents` - Document browser
- `/anomalies` - Anomaly explorer
- `/orchestrator` - Orchestration viewer
- `/settings` - Settings

### State Stores
- `DocumentStore` - Document management
- `AnalysisStore` - Analysis results
- `AnomalyStore` - Anomaly filtering
- `UISettingsStore` - User preferences

## API Integration

Communicates with backend via RESTful API:

```typescript
import { getAPIClient } from '@/lib/api/client';

const client = getAPIClient();
const result = await client.analyze({
  document_text: "...",
  metadata: { title: "..." }
});
```

## Development Notes

### Type Safety
All API responses are strictly typed to match backend schemas. See `lib/types/api.ts`.

### State Management
Zustand provides lightweight, TypeScript-friendly state management. Stores are located in `lib/stores/`.

### Styling
Tailwind CSS with custom configuration. Component styles use Tailwind utility classes.

## Deployment

### Vercel (Recommended)
```bash
npm install -g vercel
vercel
```

### Docker
```bash
docker build -t oraculus-frontend .
docker run -p 3000:3000 oraculus-frontend
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Documentation

Full documentation available in `../PHASE7_IMPLEMENTATION.md`.

## License

Copyright © 2025 Synthetic Technology Revolution
