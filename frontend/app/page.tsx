/**
 * Dashboard Page - Main overview of Oraculus-DI-Auditor
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SystemStatusCard } from '@/components/dashboard/SystemStatusCard';
import { AnalysisSummaryCard } from '@/components/dashboard/AnalysisSummaryCard';
import { JurisdictionCard } from '@/components/dashboard/JurisdictionCard';
import { DetectorStatusCard } from '@/components/dashboard/DetectorStatusCard';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { useRouter } from 'next/navigation';
import { useAnalysisStore } from '@/lib/stores/analysis';

export default function Home() {
  const router = useRouter();
  const detailedAnalyses = useAnalysisStore((state) => state.detailedAnalyses);

  const severityTotals = Object.values(detailedAnalyses).reduce(
    (acc, a) => {
      acc.critical += a.summary.by_severity.critical;
      acc.high += a.summary.by_severity.high;
      acc.medium += a.summary.by_severity.medium;
      acc.low += a.summary.by_severity.low;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  );

  const hasAnomalyData = Object.keys(detailedAnalyses).length > 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-8 text-white">
          <h1 className="text-3xl font-bold mb-2">Welcome to Oraculus DI Auditor</h1>
          <p className="text-blue-100 mb-4">
            Comprehensive legal document ingestion, analysis, and anomaly detection platform
          </p>
          <div className="flex gap-4">
            <Button variant="secondary" onClick={() => router.push('/ingest')}>
              Upload Document
            </Button>
            <Button
              variant="ghost"
              onClick={() => router.push('/analysis')}
              className="border border-white/20 text-white hover:bg-white/10"
            >
              View Analyses
            </Button>
          </div>
        </div>

        {hasAnomalyData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card variant="bordered">
              <div className="text-center">
                <div className="text-3xl font-bold text-red-600">{severityTotals.critical}</div>
                <div className="text-sm text-gray-600">Critical</div>
              </div>
            </Card>
            <Card variant="bordered">
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-600">{severityTotals.high}</div>
                <div className="text-sm text-gray-600">High</div>
              </div>
            </Card>
            <Card variant="bordered">
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">{severityTotals.medium}</div>
                <div className="text-sm text-gray-600">Medium</div>
              </div>
            </Card>
            <Card variant="bordered">
              <div className="text-center">
                <div className="text-3xl font-bold text-gray-600">{severityTotals.low}</div>
                <div className="text-sm text-gray-600">Low</div>
              </div>
            </Card>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemStatusCard />
          <AnalysisSummaryCard />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <JurisdictionCard />
          <DetectorStatusCard />
        </div>

        <Card title="Quick Actions" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => router.push('/ingest')}
              className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="text-3xl mb-2">📄</div>
              <div className="font-medium text-gray-900">Ingest Document</div>
              <div className="text-sm text-gray-600">Upload and analyze new documents</div>
            </button>
            <button
              onClick={() => router.push('/documents')}
              className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="text-3xl mb-2">📚</div>
              <div className="font-medium text-gray-900">Browse Documents</div>
              <div className="text-sm text-gray-600">View all ingested documents</div>
            </button>
            <button
              onClick={() => router.push('/anomalies')}
              className="p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="text-3xl mb-2">⚠️</div>
              <div className="font-medium text-gray-900">Explore Anomalies</div>
              <div className="text-sm text-gray-600">Review detected anomalies by detector</div>
            </button>
          </div>
        </Card>

        <Card title="Features" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🔍 8-Detector Analysis</h4>
              <p className="text-sm text-gray-600">
                Fiscal, constitutional, surveillance, procurement, signature, scope, governance,
                and administrative integrity detection.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🤖 Phase 5 Orchestration</h4>
              <p className="text-sm text-gray-600">
                Multi-agent autonomous coordination with task scheduling and parallel execution
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🔐 Privacy-First</h4>
              <p className="text-sm text-gray-600">
                All processing is local with no external API calls — your data stays secure
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">📊 Full Provenance</h4>
              <p className="text-sm text-gray-600">
                Complete lineage tracking with SHA-256 hashing and cryptographic verification
              </p>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
