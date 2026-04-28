'use client';

/**
 * Anomalies Page — cross-audit findings explorer.
 *
 * Reads all findings across all local audits from useAuditHistoryStore,
 * groups them by detector layer, and offers severity / detector / document
 * filters. Replaces the legacy per-doc /analyze/detailed view.
 */

import React, { useCallback, useMemo, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { useAuditHistoryStore } from '@/lib/stores/audit-history';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';
import type { AuditFinding } from '@/lib/types/api';

type Severity = 'critical' | 'high' | 'medium' | 'low';
type SeverityFilter = 'all' | Severity;

interface EnrichedFinding extends AuditFinding {
  job_id: string;
  generated_at: string;
}

// v2.9.1 — HUD severity primitives (no pastel pills, severity-stripe handles edge)
const SEV_BADGE: Record<Severity, string> = {
  critical: 'hud-sev hud-sev-critical',
  high: 'hud-sev hud-sev-high',
  medium: 'hud-sev hud-sev-medium',
  low: 'hud-sev hud-sev-low',
};

export default function AnomaliesPage() {
  const nav = useAppNavigate();
  const entries = useAuditHistoryStore((s) => s.entries);

  const [filterSeverity, setFilterSeverity] = useState<SeverityFilter>('all');
  const [filterDetector, setFilterDetector] = useState<string>('all');
  const [filterDocument, setFilterDocument] = useState<string>('all');
  // v2.9.0 B3 — pull-to-refresh tick (forces useMemo re-evaluation).
  const [, setRefreshTick] = useState(0);
  const handleRefresh = useCallback(async () => {
    setRefreshTick((n) => n + 1);
  }, []);

  // Flatten findings across every audit, enriched with job_id + generated_at.
  const allFindings: EnrichedFinding[] = useMemo(() => {
    const out: EnrichedFinding[] = [];
    for (const entry of entries) {
      for (const f of entry.results.findings ?? []) {
        out.push({
          ...f,
          job_id: entry.job_id,
          generated_at: entry.results.generated_at,
        });
      }
    }
    return out;
  }, [entries]);

  const detectors = useMemo(
    () => [...new Set(allFindings.map((f) => f.layer))].sort(),
    [allFindings],
  );
  const documents = useMemo(
    () => [...new Set(allFindings.map((f) => f.document_id))].sort(),
    [allFindings],
  );

  const totals = useMemo(() => {
    const t = { critical: 0, high: 0, medium: 0, low: 0 };
    for (const f of allFindings) {
      if (f.severity in t) t[f.severity as Severity] += 1;
    }
    return t;
  }, [allFindings]);

  const filtered = useMemo(
    () =>
      allFindings.filter((f) => {
        if (filterSeverity !== 'all' && f.severity !== filterSeverity) return false;
        if (filterDetector !== 'all' && f.layer !== filterDetector) return false;
        if (filterDocument !== 'all' && f.document_id !== filterDocument) return false;
        return true;
      }),
    [allFindings, filterSeverity, filterDetector, filterDocument],
  );

  const grouped = useMemo(() => {
    const g = new Map<string, EnrichedFinding[]>();
    for (const f of filtered) {
      if (!g.has(f.layer)) g.set(f.layer, []);
      g.get(f.layer)!.push(f);
    }
    return [...g.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [filtered]);

  if (allFindings.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No anomalies yet
            </h3>
            <p className="text-gray-600 mb-6">
              Run an audit to see detector findings grouped here across all
              your local audit history.
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
      <div className="space-y-6">
        {/* v2.9.1 — page hero with malachite-flux mineral texture */}
        <section className="page-hero-anomalies p-6 mb-6 hud-brackets">
          <h1 className="text-2xl font-semibold mb-4" style={{ color: 'var(--smoke-50)' }}>
            Anomalies
          </h1>
          {/* Severity summary — HUD primitives, semantic colors */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {(['critical', 'high', 'medium', 'low'] as const).map((k) => {
              const colorVar = `var(--severity-${k})`;
              const active = filterSeverity === k;
              return (
                <button
                  key={k}
                  onClick={() =>
                    setFilterSeverity(active ? 'all' : k)
                  }
                  className="hud-panel hud-panel-inset p-4 text-center transition-all"
                  style={{
                    boxShadow: active
                      ? `0 0 0 1.5px ${colorVar}, inset 0 0 0 1px ${colorVar}, 0 0 32px -8px ${colorVar}`
                      : undefined,
                  }}
                >
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{
                        background: colorVar,
                        boxShadow: `0 0 8px ${colorVar}`,
                      }}
                    />
                    <span className="hud-metric-label capitalize">{k}</span>
                  </div>
                  <div
                    className="hud-metric tabular-nums"
                    style={{ color: colorVar }}
                  >
                    {totals[k]}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Filters */}
        <Card variant="bordered">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                Detector:
              </label>
              <select
                value={filterDetector}
                onChange={(e) => setFilterDetector(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm"
              >
                <option value="all">All</option>
                {detectors.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                Document:
              </label>
              <select
                value={filterDocument}
                onChange={(e) => setFilterDocument(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm max-w-xs truncate"
              >
                <option value="all">All</option>
                {documents.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>
            <div className="ml-auto text-sm text-gray-500">
              {filtered.length} of {allFindings.length} findings shown
            </div>
          </div>
        </Card>

        {/* Grouped by detector */}
        {grouped.map(([layer, findings]) => (
          <div key={layer}>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              {layer}
              <span className="ml-2 text-sm font-normal text-gray-500">
                — {findings.length} finding{findings.length === 1 ? '' : 's'}
              </span>
            </h2>
            <div className="space-y-2">
              {findings.map((f, i) => (
                <AppLink
                  key={`${f.job_id}-${f.id}-${i}`}
                  href={`/results?job_id=${f.job_id}`}
                  className={`block hud-panel hud-panel-dense severity-stripe s-${f.severity} relative pl-5 transition-colors p-3`}
                >
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span
                      className={`${SEV_BADGE[f.severity as Severity] ?? 'hud-sev'} uppercase`}
                    >
                      {f.severity}
                    </span>
                    <span className="hud-finding-id">{f.id}</span>
                    <span className="hud-finding-doc truncate max-w-xs">
                      {f.document_id}
                    </span>
                    <span className="text-xs ml-auto" style={{ color: 'var(--smoke-400)' }}>
                      {f.generated_at.slice(0, 10)}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">{f.issue}</p>
                </AppLink>
              ))}
            </div>
          </div>
        ))}
      </div>
      </PullToRefresh>
    </DashboardLayout>
  );
}
