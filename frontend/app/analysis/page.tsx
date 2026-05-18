'use client';

/**
 * Analysis Page (v3.2.0) — DB-backed aggregate stats across the corpus.
 *
 * Pre-v3.2 this page read from useAuditHistoryStore (browser localStorage)
 * and only counted UI-triggered audits. v3.2 pulls real aggregates from
 * GET /api/v1/synthesis/aggregates (severity totals + by-layer + top
 * findings by count) and a slice of GET /api/v1/analyses for the audit
 * timeline. Numbers now reflect the full backend corpus regardless of
 * how audits arrived (UI upload, webhook, direct curl, etc.).
 */

import React, { useEffect, useMemo, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { HeroMetricTile } from '@/components/hero/HeroMetricTile';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { getAPIClient } from '@/lib/api/client';
import type {
  AnalysisRow,
  PagedResponse,
  SynthesisAggregatesResponse,
} from '@/lib/api/client';

type Severity = 'critical' | 'high' | 'medium' | 'low';

const SEV_BADGE: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-blue-100 text-blue-700',
};

const SEV_BAR_VAR: Record<Severity, string> = {
  critical: 'var(--severity-critical)',
  high: 'var(--severity-high)',
  medium: 'var(--severity-medium)',
  low: 'var(--severity-low)',
};

const TIMELINE_LIMIT = 20;

export default function AnalysisPage() {
  const nav = useAppNavigate();
  const client = useMemo(() => getAPIClient(), []);

  const [aggregates, setAggregates] = useState<SynthesisAggregatesResponse | null>(
    null,
  );
  const [analyses, setAnalyses] = useState<PagedResponse<AnalysisRow> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      client.getSynthesisAggregates(),
      client.listAnalyses({ per_page: TIMELINE_LIMIT }),
    ])
      .then(([agg, an]) => {
        if (!cancelled) {
          setAggregates(agg);
          setAnalyses(an);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e?.message || 'Failed to load analysis aggregates');
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  if (loading) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <p className="text-gray-600">Loading aggregates…</p>
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
              Unable to load analyses
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

  const totals = aggregates?.by_severity ?? {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
  };
  const totalFindings = aggregates?.total_anomalies ?? 0;
  const totalAnalyses = analyses?.total ?? 0;
  const byLayer = aggregates?.by_layer ?? [];
  const topFindings = (aggregates?.by_finding_id ?? []).slice(0, 10);
  const timeline = analyses?.items ?? [];
  const detectorCount = byLayer.length;
  const maxLayerCount = byLayer[0]?.count ?? 1;

  if (totalAnalyses === 0 && totalFindings === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No analyses in database yet
            </h3>
            <p className="text-gray-600 mb-6">
              Run an audit — via the Upload page or the scraper webhook
              pipeline — to populate the analysis store.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  const pct = (n: number, total: number): string =>
    total > 0 ? `${Math.round((n / total) * 1000) / 10}%` : '0%';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Hero — full-corpus aggregate */}
        <section className="page-hero-analysis hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10">
            <div className="hud-label-accent hud-amber mb-3">
              [ AGGREGATE ANALYTICS · DATABASE-BACKED ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">Analysis</h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              Aggregate statistics across {totalAnalyses} analysis
              {totalAnalyses === 1 ? '' : 'es'} · {totalFindings} total
              finding{totalFindings === 1 ? '' : 's'} · {detectorCount}{' '}
              detector module{detectorCount === 1 ? '' : 's'} active.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <HeroMetricTile
                label="Critical"
                value={totals.critical}
                sublabel={pct(totals.critical, totalFindings)}
                tone="critical"
              />
              <HeroMetricTile
                label="High"
                value={totals.high}
                sublabel={pct(totals.high, totalFindings)}
                tone="high"
              />
              <HeroMetricTile
                label="Medium"
                value={totals.medium}
                sublabel={pct(totals.medium, totalFindings)}
                tone="medium"
              />
              <HeroMetricTile
                label="Low"
                value={totals.low}
                sublabel={pct(totals.low, totalFindings)}
                tone="low"
              />
            </div>
          </div>
        </section>

        {/* Severity distribution + by-detector bars */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Severity distribution" variant="bordered">
            <div className="space-y-3">
              {(['critical', 'high', 'medium', 'low'] as const).map((k) => {
                const pctVal =
                  totalFindings > 0 ? (totals[k] / totalFindings) * 100 : 0;
                return (
                  <div key={k}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="capitalize font-medium text-gray-700">
                        {k}
                      </span>
                      <span className="text-gray-500">
                        {totals[k]} ({pctVal.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full"
                        style={{
                          width: `${pctVal}%`,
                          background: SEV_BAR_VAR[k],
                          boxShadow: `0 0 8px ${SEV_BAR_VAR[k]}`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card title="Findings by detector" variant="bordered">
            {byLayer.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No detector activity
              </div>
            ) : (
              <div className="space-y-2">
                {byLayer.map((row, i) => {
                  const fade =
                    byLayer.length > 1 ? i / (byLayer.length - 1) : 0;
                  const fill =
                    fade < 0.34
                      ? 'var(--gold-300)'
                      : fade < 0.67
                        ? 'var(--gold-500)'
                        : 'var(--smoke-500)';
                  return (
                    <AppLink
                      key={row.layer}
                      href={`/anomalies?layer=${encodeURIComponent(row.layer)}`}
                      className="block hover:bg-black/20 rounded -mx-1 px-1 py-0.5"
                    >
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="font-mono text-gray-700">{row.layer}</span>
                        <span className="text-gray-500">{row.count}</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full"
                          style={{
                            width: `${(row.count / maxLayerCount) * 100}%`,
                            background: fill,
                            boxShadow: fade < 0.34 ? `0 0 8px ${fill}` : 'none',
                          }}
                        />
                      </div>
                    </AppLink>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Top finding IDs by count (more informative than top-10-by-severity) */}
        <Card title="Top finding types (by occurrence count)" variant="bordered">
          {topFindings.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              No findings yet
            </div>
          ) : (
            <div className="space-y-2">
              {topFindings.map((f) => (
                <AppLink
                  key={f.anomaly_id}
                  href={`/anomalies?layer=${encodeURIComponent(f.layer)}`}
                  className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
                >
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-semibold uppercase flex-shrink-0 mt-0.5 ${
                      SEV_BADGE[f.severity as Severity] ??
                      'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {f.severity}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      <span className="font-mono">{f.anomaly_id}</span>
                      <span className="ml-2 text-gray-500">
                        × {f.count}
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      <span className="font-mono">{f.layer}</span>
                      &nbsp;·&nbsp;
                      jurisdictions: {f.jurisdictions.join(', ') || '—'}
                    </div>
                  </div>
                </AppLink>
              ))}
            </div>
          )}
        </Card>

        {/* Recent analyses timeline */}
        <Card
          title={`Recent analyses (${timeline.length} of ${totalAnalyses})`}
          variant="bordered"
        >
          <div className="space-y-2">
            {timeline.map((a) => (
              <AppLink
                key={a.id}
                href={`/anomalies?document_id=${encodeURIComponent(a.document_id)}`}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-900 truncate">
                    {a.document_title}
                  </div>
                  <div className="text-xs text-gray-500">
                    {a.analysis_timestamp?.slice(0, 16).replace('T', ' ') ?? '—'}
                    &nbsp;·&nbsp;
                    {a.anomaly_count} finding{a.anomaly_count === 1 ? '' : 's'}
                    &nbsp;·&nbsp;
                    <span className="text-gray-400">
                      {a.jurisdiction ?? 'no jurisdiction'}
                    </span>
                  </div>
                </div>
                {a.scalar_score !== null && (
                  <div className="text-xs flex-shrink-0 text-gray-500">
                    score {(a.scalar_score * 100).toFixed(0)}%
                  </div>
                )}
              </AppLink>
            ))}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
