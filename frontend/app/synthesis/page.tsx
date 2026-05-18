'use client';

/**
 * Master Audit Synthesis Page (v3.2.0) — DB-backed cross-jurisdiction
 * aggregates from /api/v1/synthesis/aggregates.
 *
 * Pre-v3.2 this page computed all aggregates client-side from
 * useAuditHistoryStore (browser localStorage), which only captured
 * UI-triggered audits. v3.2 pulls real cross-corpus aggregates from
 * the backend — the same query path RAIA uses internally — so the
 * numbers reflect the full persisted DB regardless of how audits
 * arrived (UI, webhook, direct curl).
 *
 * The legacy client-side Markdown/DOCX export logic has been replaced
 * by a link to the Automation page's "Run RAIA Synthesis" trigger,
 * which hits the backend's full RAIA pipeline (DB → patterns →
 * Jinja2 markdown render) and returns a litigation-grade report.
 *
 * Jurisdiction filter: optional `?jurisdictions=a,b,c` URL param scopes
 * the aggregation. Default is "all jurisdictions in the DB".
 */

import React, { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { HeroMetricTile } from '@/components/hero/HeroMetricTile';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { getAPIClient } from '@/lib/api/client';
import type {
  JurisdictionRollup,
  SynthesisAggregatesResponse,
} from '@/lib/api/client';

type Severity = 'critical' | 'high' | 'medium' | 'low';

const SEV_BADGE: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-blue-100 text-blue-700',
};

function SynthesisPageContent() {
  const nav = useAppNavigate();
  const client = useMemo(() => getAPIClient(), []);
  const searchParams = useSearchParams();

  // Optional jurisdiction filter from URL: ?jurisdictions=visalia,tcda
  const urlJurisdictions = (searchParams.get('jurisdictions') ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  const [aggregates, setAggregates] = useState<SynthesisAggregatesResponse | null>(
    null,
  );
  const [jurisdictions, setJurisdictions] = useState<JurisdictionRollup[]>([]);
  const [selectedJurisdictions, setSelectedJurisdictions] =
    useState<string[]>(urlJurisdictions);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Available jurisdictions for the multi-select filter (loaded once).
  useEffect(() => {
    let cancelled = false;
    client
      .listJurisdictions()
      .then((r) => {
        if (!cancelled) setJurisdictions(r.items);
      })
      .catch(() => {
        /* filter just won't be available */
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  // Reload aggregates when scope changes.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const scope = selectedJurisdictions.length ? selectedJurisdictions : undefined;
    client
      .getSynthesisAggregates(scope)
      .then((r) => {
        if (!cancelled) {
          setAggregates(r);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message || 'Failed to load synthesis aggregates');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, selectedJurisdictions]);

  if (loading && !aggregates) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <p className="text-gray-600">Loading synthesis aggregates…</p>
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
              Unable to load synthesis
            </h3>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button variant="primary" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  const severity = aggregates?.by_severity ?? {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const totalFindings = aggregates?.total_anomalies ?? 0;
  const totalDocs = aggregates?.total_documents ?? 0;
  const byFinding = aggregates?.by_finding_id ?? [];
  const byVendor = aggregates?.by_vendor ?? [];
  const byLayer = aggregates?.by_layer ?? [];
  const scope = aggregates?.jurisdictions_scope ?? [];

  if (totalFindings === 0 && totalDocs === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No audits to synthesize
            </h3>
            <p className="text-gray-600 mb-6">
              Run one or more audits first. Synthesis aggregates findings
              across all local audit history to surface cross-document
              patterns.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  const pctOf = (n: number, total: number): string =>
    total > 0 ? `${Math.round((n / total) * 1000) / 10}%` : '0%';

  const toggleJurisdiction = (jur: string) => {
    setSelectedJurisdictions((prev) =>
      prev.includes(jur) ? prev.filter((j) => j !== jur) : [...prev, jur],
    );
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Hero — full-corpus or filtered aggregate */}
        <section className="page-hero-synthesis hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10">
            <div className="hud-label-accent hud-amber mb-3">
              [ MASTER AUDIT SYNTHESIS · DATABASE-BACKED ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Master Audit Synthesis
            </h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              {totalDocs} document{totalDocs === 1 ? '' : 's'} · {totalFindings}{' '}
              finding{totalFindings === 1 ? '' : 's'} ·{' '}
              {scope.length === 0
                ? 'all jurisdictions'
                : `scope: ${scope.join(', ')}`}
              .
            </p>

            <div className="flex items-center gap-3 mt-6 flex-wrap">
              <Button variant="primary" onClick={() => nav('/automation')}>
                ↗ Run RAIA Synthesis (Markdown / DOCX)
              </Button>
              <span className="text-xs text-gray-500">
                Full cross-jurisdiction RAIA report lives on the Automation page.
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <HeroMetricTile
                label="Critical"
                value={severity.critical}
                sublabel={pctOf(severity.critical, totalFindings)}
                tone="critical"
              />
              <HeroMetricTile
                label="High"
                value={severity.high}
                sublabel={pctOf(severity.high, totalFindings)}
                tone="high"
              />
              <HeroMetricTile
                label="Medium"
                value={severity.medium}
                sublabel={pctOf(severity.medium, totalFindings)}
                tone="medium"
              />
              <HeroMetricTile
                label="Low"
                value={severity.low}
                sublabel={pctOf(severity.low, totalFindings)}
                tone="low"
              />
            </div>
          </div>
        </section>

        {/* Jurisdiction scope picker (multi-select pills) */}
        {jurisdictions.length > 0 && (
          <Card variant="bordered">
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-sm font-medium text-gray-700">
                Scope:
              </span>
              <button
                type="button"
                onClick={() => setSelectedJurisdictions([])}
                className={`px-3 py-1 rounded text-xs font-medium ${
                  selectedJurisdictions.length === 0
                    ? 'bg-emerald-600 text-white'
                    : 'bg-black/30 text-gray-300 hover:bg-black/40'
                }`}
              >
                All ({jurisdictions.length})
              </button>
              {jurisdictions.map((j) => (
                <button
                  key={j.jurisdiction}
                  type="button"
                  onClick={() => toggleJurisdiction(j.jurisdiction)}
                  className={`px-3 py-1 rounded text-xs font-medium ${
                    selectedJurisdictions.includes(j.jurisdiction)
                      ? 'bg-emerald-600 text-white'
                      : 'bg-black/30 text-gray-300 hover:bg-black/40'
                  }`}
                >
                  {j.jurisdiction} ({j.anomaly_count})
                </button>
              ))}
              {loading && (
                <span className="text-xs text-gray-400 ml-auto">refreshing…</span>
              )}
            </div>
          </Card>
        )}

        {/* Top finding IDs by cross-document prevalence */}
        <Card title="Top findings by cross-document prevalence" variant="bordered">
          {byFinding.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              No findings in this scope
            </div>
          ) : (
            <div className="space-y-2">
              {byFinding.slice(0, 20).map((f) => (
                <AppLink
                  key={f.anomaly_id}
                  href={`/anomalies?layer=${encodeURIComponent(f.layer)}`}
                  className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                          SEV_BADGE[f.severity as Severity] ??
                          'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {f.severity}
                      </span>
                      <span className="text-xs font-mono text-gray-500">
                        {f.anomaly_id}
                      </span>
                      <span className="text-xs text-gray-400">{f.layer}</span>
                    </div>
                    <div className="text-sm text-gray-900 truncate">
                      {f.example_issue}
                    </div>
                  </div>
                  <div className="text-right text-xs text-gray-600 flex-shrink-0">
                    <div>
                      <span className="font-semibold">{f.count}</span> total
                    </div>
                    <div>
                      <span className="font-semibold">{f.jurisdiction_count}</span>{' '}
                      jurisdiction{f.jurisdiction_count === 1 ? '' : 's'}
                    </div>
                  </div>
                </AppLink>
              ))}
              {byFinding.length > 20 && (
                <div className="text-xs text-gray-500 pt-2">
                  …and {byFinding.length - 20} more (full list available via
                  RAIA Synthesis export).
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Vendor + layer side-by-side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Vendors flagged" variant="bordered">
            {byVendor.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No vendor-specific findings detected
              </div>
            ) : (
              <div className="space-y-2">
                {byVendor.map((v) => (
                  <div
                    key={v.vendor}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 gap-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-gray-900">{v.vendor}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {v.count} detection{v.count === 1 ? '' : 's'} across{' '}
                        {v.jurisdiction_count} jurisdiction
                        {v.jurisdiction_count === 1 ? '' : 's'}
                        {v.jurisdictions.length > 0 && (
                          <span className="ml-1 text-gray-400">
                            ({v.jurisdictions.join(', ')})
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Detector layer activity" variant="bordered">
            {byLayer.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No detector activity in this scope
              </div>
            ) : (
              <div className="space-y-2">
                {byLayer.map((l) => (
                  <AppLink
                    key={l.layer}
                    href={`/anomalies?layer=${encodeURIComponent(l.layer)}`}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
                  >
                    <div className="font-mono text-sm text-gray-700">{l.layer}</div>
                    <div className="text-sm text-gray-500">
                      {l.count} finding{l.count === 1 ? '' : 's'}
                    </div>
                  </AppLink>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

/**
 * Suspense wrapper required by Next.js 15 static export when the page
 * calls useSearchParams(). Without this the desktop Electron build's
 * `next build` step bails the /synthesis prerender (CSR detection).
 */
export default function SynthesisPage() {
  return (
    <Suspense
      fallback={
        <DashboardLayout>
          <div className="text-center py-12 text-gray-600">
            Loading synthesis…
          </div>
        </DashboardLayout>
      }
    >
      <SynthesisPageContent />
    </Suspense>
  );
}
