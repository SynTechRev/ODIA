/**
 * Analysis Page - View analysis results
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useAnalysisStore } from '@/lib/stores/analysis';
import { AnalysisPanel } from '@/components/analysis/AnalysisPanel';
import { Card } from '@/components/base/Card';

export default function AnalysisPage() {
  const analyses = useAnalysisStore((state) => state.analyses);
  const currentAnalysis = useAnalysisStore((state) => state.currentAnalysis);
  const setCurrentAnalysis = useAnalysisStore((state) => state.setCurrentAnalysis);

  const analysisArray = Object.values(analyses);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {analysisArray.length === 0 ? (
          <Card variant="bordered">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Analyses Yet
              </h3>
              <p className="text-gray-600">
                Upload and analyze documents to see results here.
              </p>
            </div>
          </Card>
        ) : (
          <>
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
                      {analysis.metadata.title || 'Untitled'}
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
                        {analysis.findings.fiscal.length +
                          analysis.findings.constitutional.length +
                          analysis.findings.surveillance.length +
                          analysis.findings.anomalies.length}
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
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
