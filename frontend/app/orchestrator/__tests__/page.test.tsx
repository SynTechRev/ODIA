/**
 * Orchestrator page — smoke test.
 *
 * The handoff §D4 spec calls for a smoke test that asserts the page
 * renders without crashing when all three backend endpoints return
 * 404. This verifies the graceful-degradation path end-to-end.
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import OrchestratorPage from '../page';

// Stub the API client so we don't need Next.js runtime env. The page
// only reads ``api.baseURL``; the fetch calls below control the rest.
jest.mock('@/lib/api/client', () => ({
  getAPIClient: () => ({ baseURL: 'http://test.local' }),
}));

// Stub the DashboardLayout so the test focuses on OrchestratorPage
// content — we don't need to assert navigation chrome here.
jest.mock('@/components/dashboard/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  ),
}));

describe('OrchestratorPage smoke test', () => {
  let fetchMock: jest.Mock;

  beforeEach(() => {
    fetchMock = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({}),
    });
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders without crashing when all endpoints return 404', async () => {
    render(<OrchestratorPage />);
    // Hero section always renders (no data dependency).
    expect(
      screen.getByText('Multi-Agent Task Coordination')
    ).toBeInTheDocument();
    // Phase label is always present.
    expect(screen.getByText(/PHASE 5 ORCHESTRATOR/i)).toBeInTheDocument();
    // Task graph panel renders with the fallback static graph.
    expect(screen.getByText('Agent Pipeline Topology')).toBeInTheDocument();
    // Timeline panel shows the unavailable state.
    expect(screen.getByText('Recent Mesh Jobs (0)')).toBeInTheDocument();

    // Give the unreachable-fetch effects a tick to settle so the
    // fallback state renders and any state transitions complete.
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
  });

  it('renders the six-agent fallback graph even with no backend', () => {
    render(<OrchestratorPage />);
    // All six agent labels should appear somewhere (SVG <text> nodes).
    const labels = ['Ingestion', 'Analysis', 'Anomaly', 'Synthesis', 'Database', 'Interface'];
    for (const label of labels) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it('shows initial static metric fallbacks before any data loads', () => {
    render(<OrchestratorPage />);
    // Static fallback: 6 agents online, 0 queued, 0 completed today.
    expect(screen.getByText('Agents online')).toBeInTheDocument();
    expect(screen.getByText('Tasks queued')).toBeInTheDocument();
    expect(screen.getByText('Completed / 24h')).toBeInTheDocument();
  });
});
