/**
 * Analysis Page - View analysis results with severity chart and top findings.
 */

'use client';

import React from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useAnalysisStore } from '@/lib/stores/analysis';
import { AnalysisPanel } from '@/components/analysis/AnalysisPanel';
import { SeverityChart } from '@/components/analysis/SeverityChart';
import { Card } from '@/components/base/Card';
import type { Anomaly } from '@/lib/types/api';
import { useRouter } from 'next/navigation';

const SEVERITY_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export default function AnalysisPage() {
  const router = useRouter();
  const analyses = useAnalysisStore((state) => state.analyses);
  const detailedAnalyses = useAnalysisStore((state) => state.detailedAnalyses);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);
  const setCurrentAnalysis = useAnalysisStore((state) => state.setCurrentAnalysis);

  const analysisArray = Object.values(analyses);

  // --- Aggregate severity data for the chart across all detailed analyses ---
  const aggregatedBySeverity = Object.values(detailedAnalyses).reduce(
    (acc, a) => {
      acc.critical += a.summary.by_severity.critical;
      acc.high += a.summary.by_severity.high;
      acc.medium += a.summary.by_severity.medium;
      acc.low += a.summary.by_severity.low;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  );

  // --- Top findings: collect all anomalies from all detailed analyses, sort by severity ---
  const topFindings: Array<Anomaly & { document_id: string }> = [];
  Object.values(detailedAnalyses).forEach((da) => {
    Object.values(da.detectors).forEach((anomalies) => {
      anomalies.forEach((a) => topFindings.push({ ...a, document_id: da.document_id }));
    });
  });
  topFindings.sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99),
  );
  const top10 = topFindings.slice(0, 10);

  const SEVERITY_BADGE: Record<string, string> = {
    critical: 'bg-red-100 text-red-800',
    high: 'bg-orange-100 text-orange-800',
    medium: 'bg-yellow-100 text-yellow-800',
    low: 'bg-gray-100 text-gray-800',
  };

  if (analysisArray.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Analyses Yet</h3>
            <p className="text-gray-600 mb-6">
              Upload and analyze documents to see results here.
            </p>
            <button
              onClick={() => router.push('/ingest')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload Document
            </button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Severity distribution chart + top findings — shown when detailed data exists */}
        {Object.keys(detailedAnalyses).length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Severity chart */}
            <Card title="Severity Distribution" variant="bordered">
              <SeverityChart bySeverity={aggregatedBySeverity} />
            </Card>

            {/* Top findings */}
            <Card title="Top Findings" variant="bordered">
              {top10.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-3xl mb-2">✓</div>
                  <div className="text-sm">No findings across analyzed documents</div>
                </div>
              ) : (
                <div className="space-y-2 max-h-[280px] overflow-y-auto">
                  {top10.map((finding, i) => (
                    <div
                      key={`${finding.id}-${i}`}
                      className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0"
                    >
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 mt-0.5 ${SEVERITY_BADGE[finding.severity] ?? 'bg-gray-100 text-gray-800'}`}
                      >
                        {finding.severity}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900 truncate">
                          {finding.issue}
                        </div>
                        <div className="text-xs text-gray-500 truncate">
                          {finding.layer} &middot; {finding.document_id}
                        </div>
                      </div>
                      <button
                        className="text-xs text-blue-600 hover:underline flex-shrink-0"
                        onClick={() => router.push('/anomalies')}
                      >
                        View
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}

        {/* Analysis Selector */}
        <Card title="Select Analysis" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {analysisArray.map((analysis) => (
              <button
                key={analysis.document_id}
                onClick={() => setCurrentAnalysis(analysis)}
                className={`
                  p-4 border-2 rounded-lg text-left transition-colors
                  ${currentAnalysis?.document_id === analysis.document_id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300'
                  }
                `}
              >
                <div className="font-medium text-gray-900 mb-1">
                  {String(analysis.metadata?.title ?? 'Untitled')}
                </div>
                <div className="text-sm text-gray-600 mb-2">
                  {new Date(analysis.timestamp).toLocaleDateString()}
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <span className="text-gray-500">
                    Severity: {analysis.severity_score.toFixed(2)}
                  </span>
                  <span className="text-gray-500">
                    Findings:{' '}
                    {(analysis.findings.fiscal?.length ?? 0) +
                      (analysis.findings.constitutional?.length ?? 0) +
                      (analysis.findings.surveillance?.length ?? 0) +
                      (analysis.findings.anomalies?.length ?? 0)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        </Card>

        {/* Analysis Results */}
        {currentAnalysis ? (
          <AnalysisPanel result={currentAnalysis} />
        ) : (
          <Card variant="bordered">
            <p className="text-center py-8 text-gray-500">
              Select an analysis above to view details
            </p>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
