'use client';

/**
 * Documents Page (v3.2.0) — lists every Document persisted in the backend DB.
 *
 * Pre-v3.2 this page read from useAuditHistoryStore (browser localStorage)
 * which only captured audits initiated via the UI's drag-and-drop Upload
 * flow. Webhook-driven ingests (the entire scraper pipeline introduced
 * in v3.0.x) persisted directly to the DB without ever touching that
 * store, so the page was empty even when the DB held hundreds of audited
 * documents.
 *
 * v3.2: queries GET /api/v1/documents (paginated, filterable by
 * jurisdiction). Click a row → navigates to /anomalies pre-filtered to
 * that document.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { HeroMetricTile } from '@/components/hero/HeroMetricTile';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';
import { getAPIClient } from '@/lib/api/client';
import type {
  DocumentRow,
  JurisdictionRollup,
  PagedResponse,
} from '@/lib/api/client';

const PAGE_SIZE = 50;

export default function DocumentsPage() {
  const nav = useAppNavigate();
  const client = useMemo(() => getAPIClient(), []);

  const [data, setData] = useState<PagedResponse<DocumentRow> | null>(null);
  const [jurisdictions, setJurisdictions] = useState<JurisdictionRollup[]>([]);
  const [jurisdictionFilter, setJurisdictionFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  // Fetch jurisdictions once for the filter dropdown.
  useEffect(() => {
    let cancelled = false;
    client
      .listJurisdictions()
      .then((r) => {
        if (!cancelled) setJurisdictions(r.items);
      })
      .catch(() => {
        /* fail silently — filter just won't be available */
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  // Fetch documents on mount, filter change, page change, refresh tick.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    client
      .listDocuments({
        page,
        per_page: PAGE_SIZE,
        jurisdiction: jurisdictionFilter || undefined,
      })
      .then((r) => {
        if (!cancelled) {
          setData(r);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message || 'Failed to load documents');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, page, jurisdictionFilter, refreshTick]);

  const handleRefresh = useCallback(async () => {
    setRefreshTick((n) => n + 1);
  }, []);

  // Empty state — DB returned zero rows for the current filter.
  const rows = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasMore = data?.has_more ?? false;
  const totalDocs = jurisdictions.reduce((s, j) => s + j.document_count, 0);
  const totalAnomalies = jurisdictions.reduce((s, j) => s + j.anomaly_count, 0);

  if (loading && rows.length === 0 && page === 1) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <p className="text-gray-600">Loading documents…</p>
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
              Unable to load documents
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

  if (rows.length === 0 && !jurisdictionFilter) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No documents in database yet
            </h3>
            <p className="text-gray-600 mb-6">
              Upload and audit documents — or run the scraper webhook
              pipeline — to populate the persistent document store.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PullToRefresh onRefresh={handleRefresh}>
        <div className="space-y-4">
          {/* Hero — same marble pattern as before */}
          <section className="page-hero-documents hud-brackets p-6 md:p-8 relative overflow-hidden">
            <div className="relative z-10">
              <div className="hud-label-accent hud-amber mb-3">
                [ EVIDENCE LIBRARY · DATABASE-BACKED ]
              </div>
              <h1 className="hud-heading text-2xl md:text-3xl">Documents</h1>
              <p className="hud-subtext mt-3 max-w-3xl">
                Every document persisted in the local backend database. Click a
                row to view its anomalies.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6 max-w-2xl">
                <HeroMetricTile
                  label="Total documents"
                  value={totalDocs}
                  tone="gold"
                />
                <HeroMetricTile
                  label="Jurisdictions"
                  value={jurisdictions.length}
                  tone="emerald"
                />
                <HeroMetricTile
                  label="Total findings"
                  value={totalAnomalies}
                  tone="signal"
                />
              </div>
            </div>
          </section>

          {/* Filter + pagination control bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 px-1">
            <div className="flex items-center gap-2">
              <label className="text-xs uppercase tracking-wider text-gray-400">
                Jurisdiction
              </label>
              <select
                value={jurisdictionFilter}
                onChange={(e) => {
                  setJurisdictionFilter(e.target.value);
                  setPage(1);
                }}
                className="hud-input text-sm px-2 py-1"
              >
                <option value="">All ({totalDocs})</option>
                {jurisdictions.map((j) => (
                  <option key={j.jurisdiction} value={j.jurisdiction}>
                    {j.jurisdiction} ({j.document_count})
                  </option>
                ))}
              </select>
              {jurisdictionFilter && (
                <button
                  type="button"
                  onClick={() => {
                    setJurisdictionFilter('');
                    setPage(1);
                  }}
                  className="text-xs text-gray-500 hover:text-gray-300 underline"
                >
                  clear
                </button>
              )}
            </div>
            <div className="text-xs text-gray-500">
              showing {rows.length ? (page - 1) * PAGE_SIZE + 1 : 0}–
              {(page - 1) * PAGE_SIZE + rows.length} of {total}
              {loading && rows.length > 0 && (
                <span className="ml-2 text-gray-400">refreshing…</span>
              )}
            </div>
          </div>

          {/* Empty-after-filter state */}
          {rows.length === 0 && jurisdictionFilter && (
            <Card variant="bordered">
              <div className="text-center py-8">
                <p className="text-gray-500">
                  No documents in the “{jurisdictionFilter}” jurisdiction yet.
                </p>
              </div>
            </Card>
          )}

          {/* Document rows */}
          <div className="space-y-2">
            {rows.map((r) => (
              <AppLink
                key={r.document_id}
                href={`/anomalies?document_id=${encodeURIComponent(r.document_id)}`}
                className="block hud-panel hud-panel-dense p-4 transition-colors"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-gray-900 text-sm truncate">
                      {r.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      <span className="uppercase">{r.document_type}</span>
                      &nbsp;·&nbsp;
                      <span className="text-gray-400">
                        {r.jurisdiction ?? 'no jurisdiction'}
                      </span>
                      &nbsp;·&nbsp;
                      {r.anomaly_count} finding{r.anomaly_count === 1 ? '' : 's'}
                      {r.scalar_score !== null && (
                        <>
                          &nbsp;·&nbsp;
                          score {(r.scalar_score * 100).toFixed(0)}%
                        </>
                      )}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-0.5 font-mono truncate">
                      sha256: {r.document_id}
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 flex-shrink-0">
                    {r.latest_analysis_at
                      ? r.latest_analysis_at.slice(0, 10)
                      : '—'}
                  </div>
                </div>
              </AppLink>
            ))}
          </div>

          {/* Pagination controls */}
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
