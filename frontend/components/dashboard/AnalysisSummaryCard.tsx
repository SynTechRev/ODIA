/**
 * AnalysisSummaryCard — headline statistics across all local analyses.
 *
 * Replaces the bare-numbers grid with a horizontal severity bar so the
 * user can see the relative distribution of findings at a glance.
 */

'use client';

import React from 'react';
import { Card } from '../base/Card';
import { useAnalysisStore } from '@/lib/stores/analysis';
import { AnalysisIcon, UploadIcon } from '@/components/base/Icons';
import Link from 'next/link';

export function AnalysisSummaryCard() {
  const analyses = useAnalysisStore((s) => s.analyses);
  const detailedAnalyses = useAnalysisStore((s) => s.detailedAnalyses);

  const analysisCount = Object.keys(analyses).length;

  const totalFindings = Object.values(analyses).reduce(
    (sum, a) =>
      sum +
      (a.findings.fiscal?.length ?? 0) +
      (a.findings.constitutional?.length ?? 0) +
      (a.findings.surveillance?.length ?? 0) +
      (a.findings.anomalies?.length ?? 0),
    0,
  );

  const avgSeverity =
    analysisCount > 0
      ? Object.values(analyses).reduce((sum, a) => sum + a.severity_score, 0) /
        analysisCount
      : 0;

  // Aggregate severity counts from detailed analyses
  const severity = Object.values(detailedAnalyses).reduce(
    (acc, a) => {
      acc.critical += a.summary.by_severity.critical;
      acc.high     += a.summary.by_severity.high;
      acc.medium   += a.summary.by_severity.medium;
      acc.low      += a.summary.by_severity.low;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  );
  const totalSeverity =
    severity.critical + severity.high + severity.medium + severity.low;

  return (
    <Card
      variant="bordered"
      icon={<AnalysisIcon size={18} />}
      title="Analysis Summary"
      subtitle={
        analysisCount === 0
          ? 'No analyses yet'
          : `${analysisCount} document${analysisCount === 1 ? '' : 's'} analysed`
      }
    >
      {analysisCount === 0 ? (
        <div className="flex flex-col items-center text-center py-6">
          <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mb-3 ring-1 ring-amber-200">
            <UploadIcon size={20} />
          </div>
          <p className="text-sm text-slate-700 font-medium">
            No analyses yet
          </p>
          <p className="text-xs text-slate-500 mt-1 max-w-xs">
            Upload a document to begin forensic analysis. Findings and
            severity breakdowns will appear here.
          </p>
          <Link
            href="/upload"
            className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-amber-700 hover:text-amber-800"
          >
            <UploadIcon size={14} />
            Upload your first document →
          </Link>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Headline metrics */}
          <div className="grid grid-cols-3 gap-4">
            <Metric value={analysisCount}          label="Analyses"     />
            <Metric value={totalFindings}          label="Findings"     />
            <Metric
              value={avgSeverity.toFixed(2)}
              label="Avg Severity"
              emphasis={avgSeverity > 0.7 ? 'danger' : undefined}
            />
          </div>

          {/* Severity stack bar */}
          {totalSeverity > 0 && (
            <div>
              <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                <span>Severity distribution</span>
                <span className="font-mono">{totalSeverity} total</span>
              </div>
              <div
                className="h-2.5 w-full flex rounded-full overflow-hidden bg-slate-100 ring-1 ring-inset ring-slate-200"
                role="img"
                aria-label={`${severity.critical} critical, ${severity.high} high, ${severity.medium} medium, ${severity.low} low`}
              >
                {severity.critical > 0 && (
                  <span className="bg-red-700" style={{ width: `${(severity.critical / totalSeverity) * 100}%` }} />
                )}
                {severity.high > 0 && (
                  <span className="bg-red-500" style={{ width: `${(severity.high / totalSeverity) * 100}%` }} />
                )}
                {severity.medium > 0 && (
                  <span className="bg-orange-500" style={{ width: `${(severity.medium / totalSeverity) * 100}%` }} />
                )}
                {severity.low > 0 && (
                  <span className="bg-yellow-500" style={{ width: `${(severity.low / totalSeverity) * 100}%` }} />
                )}
              </div>
              <div className="grid grid-cols-4 gap-2 mt-3 text-xs">
                <SeverityLegend color="bg-red-700"     label="Critical" count={severity.critical} />
                <SeverityLegend color="bg-red-500"     label="High"     count={severity.high} />
                <SeverityLegend color="bg-orange-500"  label="Medium"   count={severity.medium} />
                <SeverityLegend color="bg-yellow-500"  label="Low"      count={severity.low} />
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
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
          emphasis === 'danger' ? 'text-red-600' : 'text-slate-900'
        }`}
      >
        {value}
      </div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
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
      <span className="text-slate-600 truncate">{label}</span>
      <span className="text-slate-900 font-mono font-medium ml-auto">
        {count}
      </span>
    </div>
  );
}
