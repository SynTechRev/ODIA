/**
 * Anomalies Page - Browse anomalies from /analyze/detailed, grouped by detector.
 */

'use client';

import React, { useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useAnalysisStore } from '@/lib/stores/analysis';
import { DetectorGroupPanel } from '@/components/anomalies/DetectorGroupPanel';
import { Card } from '@/components/base/Card';
import type { DetailedAnalysisResult } from '@/lib/types/api';
import { useRouter } from 'next/navigation';

type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

export default function AnomaliesPage() {
  const router = useRouter();
  const detailedAnalyses = useAnalysisStore((state) => state.detailedAnalyses);
  const [filterSeverity, setFilterSeverity] = useState<SeverityFilter>('all');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const analysisArray = Object.values(detailedAnalyses);

  // Choose which analysis to display
  const activeAnalysis: DetailedAnalysisResult | null =
    selectedDocId
      ? (detailedAnalyses[selectedDocId] ?? null)
      : (analysisArray[0] ?? null);

  // Aggregate by-severity across all analyses
  const totals = analysisArray.reduce(
    (acc, a) => {
      acc.critical += a.summary.by_severity.critical;
      acc.high += a.summary.by_severity.high;
      acc.medium += a.summary.by_severity.medium;
      acc.low += a.summary.by_severity.low;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  );

  // Filter the active analysis by severity when a filter is applied
  const filteredAnalysis: DetailedAnalysisResult | null = activeAnalysis
    ? filterSeverity === 'all'
      ? activeAnalysis
      : {
          ...activeAnalysis,
          detectors: Object.fromEntries(
            Object.entries(activeAnalysis.detectors).map(([name, anomalies]) => [
              name,
              anomalies.filter((a) => a.severity === filterSeverity),
            ]),
          ) as DetailedAnalysisResult['detectors'],
        }
    : null;

  if (analysisArray.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-16">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Analyses Yet</h3>
            <p className="text-gray-600 mb-6">
              Upload and analyze a document to see per-detector anomaly breakdowns here.
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
        {/* Severity summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">{totals.critical}</div>
              <div className="text-sm text-gray-600">Critical</div>
            </div>
          </Card>
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">{totals.high}</div>
              <div className="text-sm text-gray-600">High</div>
            </div>
          </Card>
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">{totals.medium}</div>
              <div className="text-sm text-gray-600">Medium</div>
            </div>
          </Card>
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-600">{totals.low}</div>
              <div className="text-sm text-gray-600">Low</div>
            </div>
          </Card>
        </div>

        {/* Document selector + severity filter */}
        <Card variant="bordered">
          <div className="flex flex-wrap items-center gap-4">
            {analysisArray.length > 1 && (
              <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700">Document:</label>
                <select
                  value={selectedDocId ?? analysisArray[0]?.document_id ?? ''}
                  onChange={(e) => setSelectedDocId(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
                >
                  {analysisArray.map((a) => (
                    <option key={a.document_id} value={a.document_id}>
                      {a.document_id}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">Filter severity:</label>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value as SeverityFilter)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {activeAnalysis && (
              <div className="ml-auto text-sm text-gray-500">
                {activeAnalysis.summary.total_anomalies} total anomaly
                {activeAnalysis.summary.total_anomalies !== 1 ? 'ies' : 'y'} &middot;{' '}
                score{' '}
                <span className="font-medium text-gray-800">
                  {activeAnalysis.summary.score.toFixed(2)}
                </span>
              </div>
            )}
          </div>
        </Card>

        {/* Per-detector grouped view */}
        {filteredAnalysis && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Anomalies by Detector
              {activeAnalysis && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  — {activeAnalysis.document_id}
                  {activeAnalysis.jurisdiction
                    ? ` · ${activeAnalysis.jurisdiction}`
                    : ''}
                </span>
              )}
            </h2>
            <DetectorGroupPanel result={filteredAnalysis} />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
