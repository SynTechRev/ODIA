/**
 * AnalysisSummaryCard — headline statistics across all persisted analyses.
 *
 * v2.7.6 X1: now fetches from `/api/v1/dashboard/summary`. Pre-X1 the
 * card read from a Zustand store that only the legacy paste-text
 * UploadPanel ever wrote to — so audits run through the production
 * `/api/v1/audit/run` flow never showed up here. The DB has been the
 * source of truth since v2.7.3 V1 (init_db at startup); this card is
 * now in lockstep with what the backend has actually persisted.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { AnalysisIcon, UploadIcon } from '@/components/base/Icons';
import { AppLink } from '@/lib/navigation';
import { getAPIClient, type DashboardSummary } from '@/lib/api/client';

const POLL_MS = 30_000;

const EMPTY_SUMMARY: DashboardSummary = {
  available: false,
  analyses: 0,
  documents: 0,
  findings: 0,
  by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
  avg_severity_score: 0,
  last_audit_at: null,
};

export function AnalysisSummaryCard() {
  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY);
  const [loading, setLoading] = useState(true);
  const [reachable, setReachable] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const client = getAPIClient();
    const load = async () => {
      try {
        const data = await client.getDashboardSummary();
        if (!cancelled) {
          setSummary(data);
          setReachable(true);
        }
      } catch {
        if (!cancelled) setReachable(false);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const { analyses, findings, by_severity: sev, avg_severity_score } = summary;
  const totalSev = sev.critical + sev.high + sev.medium + sev.low;

  const subtitle = loading
    ? 'Loading…'
    : !reachable
      ? 'Backend unreachable'
      : analyses === 0
        ? 'No analyses yet'
        : `${analyses} document${analyses === 1 ? '' : 's'} analysed`;

  return (
    <Card
      variant="bordered"
      icon={<AnalysisIcon size={18} />}
      title="Analysis Summary"
      subtitle={subtitle}
    >
      {!reachable ? (
        <DegradedState />
      ) : analyses === 0 && !loading ? (
        <EmptyState />
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-3 gap-4">
            <Metric value={analyses} label="Analyses" />
            <Metric value={findings} label="Findings" />
            <Metric
              value={avg_severity_score.toFixed(2)}
              label="Avg Severity"
              emphasis={avg_severity_score > 0.7 ? 'danger' : undefined}
            />
          </div>

          {totalSev > 0 && (
            <div>
              <div className="flex items-center justify-between text-xs text-zinc-400 mb-2">
                <span>Severity distribution</span>
                <span className="font-mono">{totalSev} total</span>
              </div>
              <div
                className="h-2.5 w-full flex rounded-full overflow-hidden bg-zinc-800/60 ring-1 ring-inset ring-zinc-700/60"
                role="img"
                aria-label={`${sev.critical} critical, ${sev.high} high, ${sev.medium} medium, ${sev.low} low`}
              >
                {sev.critical > 0 && (
                  <span
                    className="bg-rose-600"
                    style={{ width: `${(sev.critical / totalSev) * 100}%` }}
                  />
                )}
                {sev.high > 0 && (
                  <span
                    className="bg-orange-500"
                    style={{ width: `${(sev.high / totalSev) * 100}%` }}
                  />
                )}
                {sev.medium > 0 && (
                  <span
                    className="bg-yellow-500"
                    style={{ width: `${(sev.medium / totalSev) * 100}%` }}
                  />
                )}
                {sev.low > 0 && (
                  <span
                    className="bg-sky-500"
                    style={{ width: `${(sev.low / totalSev) * 100}%` }}
                  />
                )}
              </div>
              <div className="grid grid-cols-4 gap-2 mt-3 text-xs">
                <SeverityLegend color="bg-rose-600" label="Critical" count={sev.critical} />
                <SeverityLegend color="bg-orange-500" label="High" count={sev.high} />
                <SeverityLegend color="bg-yellow-500" label="Medium" count={sev.medium} />
                <SeverityLegend color="bg-sky-500" label="Low" count={sev.low} />
              </div>
            </div>
          )}

          {summary.last_audit_at && (
            <p className="text-xs text-zinc-500 font-mono">
              Last audit: {formatTs(summary.last_audit_at)}
            </p>
          )}
        </div>
      )}
    </Card>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center text-center py-6">
      <div className="w-12 h-12 rounded-full bg-zinc-800/60 text-zinc-300 flex items-center justify-center mb-3 ring-1 ring-zinc-700/60">
        <UploadIcon size={20} />
      </div>
      <p className="text-sm text-zinc-200 font-medium">No analyses yet</p>
      <p className="text-xs text-zinc-500 mt-1 max-w-xs">
        Upload a document to begin forensic analysis. Findings and severity
        breakdowns will appear here.
      </p>
      <AppLink
        href="/upload"
        className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-zinc-200 hover:text-white"
      >
        <UploadIcon size={14} />
        Upload your first document →
      </AppLink>
    </div>
  );
}

function DegradedState() {
  return (
    <div className="flex flex-col items-center text-center py-6">
      <p className="text-sm text-zinc-300 font-medium">Backend unreachable</p>
      <p className="text-xs text-zinc-500 mt-1 max-w-xs">
        The dashboard summary endpoint did not respond. Counters will refresh
        automatically once the backend is back online.
      </p>
    </div>
  );
}

function Metric({
  value,
  label,
  emphasis,
}: {
  value: string | number;
  label: string;
  emphasis?: 'danger';
}) {
  return (
    <div>
      <div
        className={`text-2xl font-bold tabular-nums ${
          emphasis === 'danger' ? 'text-rose-400' : 'text-zinc-100'
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-zinc-400 mt-0.5">{label}</div>
    </div>
  );
}

function SeverityLegend({
  color,
  label,
  count,
}: {
  color: string;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center gap-1.5 min-w-0">
      <span className={`w-2 h-2 rounded-sm flex-shrink-0 ${color}`} />
      <span className="text-zinc-400 truncate">{label}</span>
      <span className="text-zinc-100 font-mono font-medium ml-auto">
        {count}
      </span>
    </div>
  );
}

function formatTs(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}
