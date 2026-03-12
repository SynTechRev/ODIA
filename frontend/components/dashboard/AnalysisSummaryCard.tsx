/**
 * AnalysisSummaryCard - Displays analysis summary statistics
 */

'use client';

import React from 'react';
import { Card } from '../base/Card';
import { useAnalysisStore } from '@/lib/stores/analysis';

export function AnalysisSummaryCard() {
  const analyses = useAnalysisStore((state) => state.analyses);

  const analysisCount = Object.keys(analyses).length;
  
  const totalFindings = Object.values(analyses).reduce((sum, analysis) => {
    return sum + 
      analysis.findings.fiscal.length +
      analysis.findings.constitutional.length +
      analysis.findings.surveillance.length +
      analysis.findings.anomalies.length;
  }, 0);

  const avgSeverity = analysisCount > 0
    ? Object.values(analyses).reduce((sum, a) => sum + a.severity_score, 0) / analysisCount
    : 0;

  const highSeverityCount = Object.values(analyses).filter(
    (a) => a.severity_score > 0.7
  ).length;

  return (
    <Card title="Analysis Summary" variant="bordered">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-3xl font-bold text-gray-900">{analysisCount}</div>
            <div className="text-sm text-gray-600">Total Analyses</div>
          </div>

          <div>
            <div className="text-3xl font-bold text-gray-900">{totalFindings}</div>
            <div className="text-sm text-gray-600">Total Findings</div>
          </div>

          <div>
            <div className="text-3xl font-bold text-gray-900">
              {avgSeverity.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">Avg Severity</div>
          </div>

          <div>
            <div className="text-3xl font-bold text-red-600">
              {highSeverityCount}
            </div>
            <div className="text-sm text-gray-600">High Severity</div>
          </div>
        </div>

        {analysisCount === 0 && (
          <div className="text-center py-4 text-gray-500">
            No analyses yet. Upload and analyze documents to see statistics.
          </div>
        )}
      </div>
    </Card>
  );
}
