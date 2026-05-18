'use client';

/**
 * Anomalies Page (v3.2.0) — DB-backed cross-jurisdiction findings explorer.
 *
 * Pre-v3.2 this page read findings from useAuditHistoryStore (browser
 * localStorage), which only captured UI-triggered audits and missed
 * everything ingested via the webhook scraper pipeline.
 *
 * v3.2: queries GET /api/v1/anomalies (paginated, filterable by severity,
 * layer, jurisdiction, document_id). Top severity-tile totals are pulled
 * from /api/v1/synthesis/aggregates so they reflect the full corpus, not
 * just the current page.
 *
 * Pre-population: deep-linked URL params (`?document_id=…`, `?jurisdiction=…`,
 * `?severity=…`, `?layer=…`) seed the initial filters so the Documents
 * page can jump straight to a single doc's anomalies and the Dashboard
 * jurisdiction tiles can drill in.
 */

import React, {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useSearchParams } from 'next/navigation';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { HeroMetricTile } from '@/components/hero/HeroMetricTile';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';
import { getAPIClient } from '@/lib/api/client';
import type {
  AnomalyRow,
  JurisdictionRollup,
  PagedResponse,
  SynthesisAggregatesResponse,
} from '@/lib/api/client';

type Severity = 'critical' | 'high' | 'medium' | 'low';
type SeverityFilter = 'all' | Severity;

const PAGE_SIZE = 50;

const SEV_BADGE: Record<Severity, string> = {
  critical: 'hud-sev hud-sev-critical',
  high: 'hud-sev hud-sev-high',
  medium: 'hud-sev hud-sev-medium',
  low: 'hud-sev hud-sev-low',
};

function AnomaliesPageContent() {
  const client = useMemo(() => getAPIClient(), []);
  const searchParams = useSearchParams();

  // Initial filter state seeded from URL query params (deep-link entry).
  const initialSeverity =
    (searchParams.get('severity') as SeverityFilter | null) ?? 'all';
  const initialLayer = searchParams.get('layer') ?? '';
  const initialJurisdiction = searchParams.get('jurisdiction') ?? '';
  const initialDocumentId = searchParams.get('document_id') ?? '';

  const [filterSeverity, setFilterSeverity] = useState<SeverityFilter>(initialSeverity);
  const [filterLayer, setFilterLayer] = useState<string>(initialLayer);
  const [filterJurisdiction, setFilterJurisdiction] =
    useState<string>(initialJurisdiction);
  const [filterDocumentId] = useState<string>(initialDocumentId);
  const [page, setPage] = useState(1);
  const [refreshTick, setRefreshTick] = useState(0);

  const [data, setData] = useState<PagedResponse<AnomalyRow> | null>(null);
  const [aggregates, setAggregates] = useState<SynthesisAggregatesResponse | null>(
    null,
  );
  const [jurisdictions, setJurisdictions] = useState<JurisdictionRollup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleRefresh = useCallback(async () => {
    setRefreshTick((n) => n + 1);
  }, []);

  // Load aggregates + jurisdictions once on mount + on manual refresh.
  useEffect(() => {
    let cancelled = false;
    Promise.all([client.getSynthesisAggregates(), client.listJurisdictions()])
      .then(([agg, jur]) => {
        if (!cancelled) {
          setAggregates(agg);
          setJurisdictions(jur.items);
        }
      })
      .catch(() => {
        /* aggregates are nice-to-have for tile totals; not blocking */
      });
    return () => {
      cancelled = true;
    };
  }, [client, refreshTick]);

  // Load anomaly page on every filter / page / refresh change.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    client
      .listAnomalies({
        page,
        per_page: PAGE_SIZE,
        severity: filterSeverity === 'all' ? undefined : filterSeverity,
        layer: filterLayer || undefined,
        jurisdiction: filterJurisdiction || undefined,
        document_id: filterDocumentId || undefined,
      })
      .then((r) => {
        if (!cancelled) {
          setData(r);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message || 'Failed to load anomalies');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [
    client,
    page,
    filterSeverity,
    filterLayer,
    filterJurisdiction,
    filterDocumentId,
    refreshTick,
  ]);

  // Totals across the whole corpus (not just current filter / page).
  const totals = aggregates?.by_severity ?? {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const totalAllSeverities = totals.critical + totals.high + totals.medium + totals.low;

  // Layer options come from aggregates (full corpus, not current page).
  const layerOptions = aggregates?.by_layer ?? [];

  const rows = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasMore = data?.has_more ?? false;

  // Group current page by layer for display.
  const grouped = useMemo(() => {
    const g = new Map<string, AnomalyRow[]>();
    for (const r of rows) {
      if (!g.has(r.layer)) g.set(r.layer, []);
      g.get(r.layer)!.push(r);
    }
    return [...g.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [rows]);

  const setSeverityFilter = (next: Severity) => {
    setFilterSeverity(filterSeverity === next ? 'all' : next);
    setPage(1);
  };

  if (loading && rows.length === 0 && page === 1 && !aggregates) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <p className="text-gray-600">Loading anomalies…</p>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Unable to load anomalies
            </h3>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button variant="primary" onClick={handleRefresh}>
              Retry
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  if (totalAllSeverities === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No anomalies in database yet
            </h3>
            <p className="text-gray-600 mb-6">
              Run an audit — via the Upload page or the scraper webhook
              pipeline — to populate the persistent anomaly store.
            </p>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PullToRefresh onRefresh={handleRefresh}>
        <div className="space-y-6">
          {/* Hero — full-corpus severity tiles (click to filter) */}
          <section className="page-hero-anomalies hud-brackets p-6 md:p-8 relative overflow-hidden">
            <div className="relative z-10">
              <div className="hud-label-accent hud-cyan-bright mb-3">
                [ ANOMALY EXPLORER · DATABASE-BACKED ]
              </div>
              <h1 className="hud-heading text-2xl md:text-3xl">Anomalies</h1>
              <p className="hud-subtext mt-3 max-w-3xl">
                Every detector finding in the persistent backend database.
                Click a severity tile to filter; click again to clear.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                {(['critical', 'high', 'medium', 'low'] as const).map((k) => (
                  <HeroMetricTile
                    key={k}
                    label={k}
                    value={totals[k]}
                    tone={k}
                    active={filterSeverity === k}
                    onClick={() => setSeverityFilter(k)}
                  />
                ))}
              </div>
            </div>
          </section>

          {/* Filters bar */}
          <Card variant="bordered">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">
                  Jurisdiction:
                </label>
                <select
                  value={filterJurisdiction}
                  onChange={(e) => {
                    setFilterJurisdiction(e.target.value);
                    setPage(1);
                  }}
                  className="hud-input text-sm px-2 py-1"
                >
                  <option value="">All</option>
                  {jurisdictions.map((j) => (
                    <option key={j.jurisdiction} value={j.jurisdiction}>
                      {j.jurisdiction} ({j.anomaly_count})
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">
                  Detector:
                </label>
                <select
                  value={filterLayer}
                  onChange={(e) => {
                    setFilterLayer(e.target.value);
                    setPage(1);
                  }}
                  className="hud-input text-sm px-2 py-1"
                >
                  <option value="">All</option>
                  {layerOptions.map((l) => (
                    <option key={l.layer} value={l.layer}>
                      {l.layer} ({l.count})
                    </option>
                  ))}
                </select>
              </div>
              {filterDocumentId && (
                <div className="text-xs text-gray-500 font-mono">
                  doc: {filterDocumentId.slice(0, 12)}…
                </div>
              )}
              <div className="ml-auto text-sm text-gray-500">
                showing {rows.length ? (page - 1) * PAGE_SIZE + 1 : 0}–
                {(page - 1) * PAGE_SIZE + rows.length} of {total}
                {loading && rows.length > 0 && (
                  <span className="ml-2 text-gray-400">refreshing…</span>
                )}
              </div>
            </div>
          </Card>

          {/* Empty-after-filter */}
          {rows.length === 0 && (
            <Card variant="bordered">
              <div className="text-center py-8">
                <p className="text-gray-500">No anomalies match the current filters.</p>
              </div>
            </Card>
          )}

          {/* Grouped by layer */}
          {grouped.map(([layer, items]) => (
            <div key={layer}>
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                {layer}
                <span className="ml-2 text-sm font-normal text-gray-500">
                  — {items.length} on this page
                </span>
              </h2>
              <div className="space-y-2">
                {items.map((f) => (
                  <div
                    key={f.id}
                    className={`block hud-panel hud-panel-dense severity-stripe s-${f.severity} relative pl-5 p-3`}
                  >
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span
                        className={`${SEV_BADGE[f.severity as Severity] ?? 'hud-sev'} uppercase`}
                      >
                        {f.severity}
                      </span>
                      <span className="hud-finding-id">{f.anomaly_id}</span>
                      {f.jurisdiction && (
                        <span className="text-xs px-2 py-0.5 rounded bg-black/30 text-gray-300 uppercase">
                          {f.jurisdiction}
                        </span>
                      )}
                      <span className="hud-finding-doc truncate max-w-xs">
                        {f.document_title}
                      </span>
                      <span
                        className="text-xs ml-auto"
                        style={{ color: 'var(--smoke-400)' }}
                      >
                        {f.analysis_timestamp?.slice(0, 10) ?? '—'}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-900">{f.issue}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Pagination */}
          {(page > 1 || hasMore) && (
            <div className="flex items-center justify-center gap-3 pt-4">
              <Button
                variant="secondary"
                disabled={page <= 1 || loading}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                ← Prev
              </Button>
              <span className="text-sm text-gray-400">page {page}</span>
              <Button
                variant="secondary"
                disabled={!hasMore || loading}
                onClick={() => setPage((p) => p + 1)}
              >
                Next →
              </Button>
            </div>
          )}
        </div>
      </PullToRefresh>
    </DashboardLayout>
  );
}

/**
 * Next.js 15 static export requires every page that calls
 * useSearchParams() to be wrapped in a Suspense boundary; otherwise
 * `next build` fails the /anomalies prerender step (CSR bailout
 * detection). The Electron desktop build runs `next build` against the
 * exported static bundle so this matters for desktop installer
 * generation even though the dev server tolerates the bare hook.
 */
export default function AnomaliesPage() {
  return (
    <Suspense
      fallback={
        <DashboardLayout>
          <div className="text-center py-12 text-gray-600">
            Loading anomalies…
          </div>
        </DashboardLayout>
      }
    >
      <AnomaliesPageContent />
    </Suspense>
  );
}
