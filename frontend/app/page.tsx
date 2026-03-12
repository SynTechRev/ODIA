/**
 * Dashboard Page - Main overview of Oraculus-DI-Auditor
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SystemStatusCard } from '@/components/dashboard/SystemStatusCard';
import { AnalysisSummaryCard } from '@/components/dashboard/AnalysisSummaryCard';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-8 text-white">
          <h1 className="text-3xl font-bold mb-2">
            Welcome to Oraculus DI Auditor
          </h1>
          <p className="text-blue-100 mb-4">
            Comprehensive legal document ingestion, analysis, and anomaly detection platform
          </p>
          <div className="flex gap-4">
            <Button 
              variant="secondary" 
              onClick={() => router.push('/ingest')}
            >
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

        {/* Status Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemStatusCard />
          <AnalysisSummaryCard />
        </div>

        {/* Quick Actions */}
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
              <div className="text-sm text-gray-600">Review detected anomalies</div>
            </button>
          </div>
        </Card>

        {/* Features Overview */}
        <Card title="Features" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">🔍 Multi-Layered Analysis</h4>
              <p className="text-sm text-gray-600">
                Fiscal, constitutional, and surveillance anomaly detection with recursive scalar scoring
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
                All processing is local with no external API calls - your data stays secure
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
