'use client';

/**
 * Analysis Page — aggregate stats across all audits in local history.
 *
 * Reads from useAuditHistoryStore rather than the legacy useAnalysisStore.
 * Shows: severity distribution, per-detector finding counts, top findings
 * by severity, and a compact audit timeline.
 */

import React, { useMemo } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { useAuditHistoryStore } from '@/lib/stores/audit-history';
import type { AuditFinding } from '@/lib/types/api';

type Severity = 'critical' | 'high' | 'medium' | 'low';

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

const SEV_BADGE: Record<Severity, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-blue-100 text-blue-700',
};

const SEV_BAR: Record<Severity, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-400',
  low: 'bg-blue-400',
};

interface EnrichedFinding extends AuditFinding {
  job_id: string;
  generated_at: string;
}

export default function AnalysisPage() {
  const nav = useAppNavigate();
  const entries = useAuditHistoryStore((s) => s.entries);

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

  const totals = useMemo(() => {
    const t = { critical: 0, high: 0, medium: 0, low: 0 };
    for (const f of allFindings) {
      if (f.severity in t) t[f.severity as Severity] += 1;
    }
    return t;
  }, [allFindings]);

  const byDetector = useMemo(() => {
    const m = new Map<string, number>();
    for (const f of allFindings) m.set(f.layer, (m.get(f.layer) ?? 0) + 1);
    return [...m.entries()].sort((a, b) => b[1] - a[1]);
  }, [allFindings]);

  const top10 = useMemo(
    () =>
      [...allFindings]
        .sort(
          (a, b) =>
            (SEVERITY_ORDER[a.severity] ?? 99) -
            (SEVERITY_ORDER[b.severity] ?? 99),
        )
        .slice(0, 10),
    [allFindings],
  );

  if (entries.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No analyses yet
            </h3>
            <p className="text-gray-600 mb-6">
              Run an audit to see aggregate severity distribution, detector
              activity, and top findings across all your local audits.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  const totalFindings = allFindings.length;
  const maxDetector = byDetector[0]?.[1] ?? 1;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Analysis</h2>
          <p className="text-gray-600 text-sm">
            Aggregate statistics across {entries.length} audit
            {entries.length === 1 ? '' : 's'} · {totalFindings} total findings
          </p>
        </div>

        {/* Severity distribution */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Severity distribution" variant="bordered">
            <div className="space-y-3">
              {(['critical', 'high', 'medium', 'low'] as const).map((k) => {
                const pct = totalFindings > 0 ? (totals[k] / totalFindings) * 100 : 0;
                return (
                  <div key={k}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="capitalize font-medium text-gray-700">
                        {k}
                      </span>
                      <span className="text-gray-500">
                        {totals[k]} ({pct.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${SEV_BAR[k]}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          <Card title="Findings by detector" variant="bordered">
            {byDetector.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No detector activity
              </div>
            ) : (
              <div className="space-y-2">
                {byDetector.map(([layer, count]) => (
                  <div key={layer}>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="font-mono text-gray-700">{layer}</span>
                      <span className="text-gray-500">{count}</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-slate-500"
                        style={{ width: `${(count / maxDetector) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Top findings */}
        <Card title="Top findings by severity" variant="bordered">
          {top10.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              No findings yet
            </div>
          ) : (
            <div className="space-y-2">
              {top10.map((f, i) => (
                <AppLink
                  key={`${f.job_id}-${f.id}-${i}`}
                  href={`/results?job_id=${f.job_id}`}
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
                      {f.issue}
                    </div>
                    <div className="text-xs text-gray-500 truncate">
                      <span className="font-mono">{f.layer}</span> ·{' '}
                      {f.document_id} · {f.generated_at.slice(0, 10)}
                    </div>
                  </div>
                </AppLink>
              ))}
            </div>
          )}
        </Card>

        {/* Audit timeline */}
        <Card title="Audit timeline" variant="bordered">
          <div className="space-y-2">
            {entries.map((e) => {
              const sev = e.results.severity_summary;
              return (
                <AppLink
                  key={e.job_id}
                  href={`/results?job_id=${e.job_id}`}
                  className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
                >
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {e.results.document_manifest?.[0]?.filename ?? 'Audit'}
                      {e.results.document_count > 1 &&
                        ` +${e.results.document_count - 1} more`}
                    </div>
                    <div className="text-xs text-gray-500">
                      {e.results.generated_at.slice(0, 16).replace('T', ' ')} ·{' '}
                      {e.results.finding_count} finding
                      {e.results.finding_count === 1 ? '' : 's'}
                    </div>
                  </div>
                  <div className="flex gap-1 text-xs flex-shrink-0">
                    {sev.critical > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-red-100 text-red-700">
                        C {sev.critical}
                      </span>
                    )}
                    {sev.high > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-orange-100 text-orange-700">
                        H {sev.high}
                      </span>
                    )}
                    {sev.medium > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700">
                        M {sev.medium}
                      </span>
                    )}
                    {sev.low > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">
                        L {sev.low}
                      </span>
                    )}
                  </div>
                </AppLink>
              );
            })}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
