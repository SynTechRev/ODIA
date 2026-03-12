/**
 * Analysis Panel Component - Main analysis results display
 */

'use client';

import React, { useState } from 'react';
import { Card } from '../base/Card';
import { Button } from '../base/Button';
import type { AnalysisResult } from '@/lib/types/api';
import { FiscalFindingsView } from './FiscalFindingsView';

interface AnalysisPanelProps {
  result: AnalysisResult;
  onRefresh?: () => void;
  loading?: boolean;
}

export function AnalysisPanel({ result, onRefresh, loading }: AnalysisPanelProps) {
  const [activeTab, setActiveTab] = useState<'fiscal' | 'constitutional' | 'surveillance' | 'anomalies'>('fiscal');

  const tabs = [
    { id: 'fiscal' as const, label: 'Fiscal', count: result.findings.fiscal.length },
    { id: 'constitutional' as const, label: 'Constitutional', count: result.findings.constitutional.length },
    { id: 'surveillance' as const, label: 'Surveillance', count: result.findings.surveillance.length },
    { id: 'anomalies' as const, label: 'Anomalies', count: result.findings.anomalies.length },
  ];

  return (
    <div className="space-y-6">
      {/* Header with Scores */}
      <Card variant="bordered">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="text-sm text-gray-600 mb-1">Severity Score</div>
            <div className="flex items-baseline gap-2">
              <div className="text-3xl font-bold text-gray-900">
                {result.severity_score.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">/ 1.0</div>
            </div>
          </div>
          
          <div>
            <div className="text-sm text-gray-600 mb-1">Lattice Score</div>
            <div className="flex items-baseline gap-2">
              <div className="text-3xl font-bold text-gray-900">
                {result.lattice_score.toFixed(2)}
              </div>
              <div className="text-sm text-gray-500">/ 1.0</div>
            </div>
          </div>

          <div>
            <div className="text-sm text-gray-600 mb-1">Total Findings</div>
            <div className="text-3xl font-bold text-gray-900">
              {result.findings.fiscal.length +
                result.findings.constitutional.length +
                result.findings.surveillance.length +
                result.findings.anomalies.length}
            </div>
          </div>
        </div>

        {result.flags.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Flags:</div>
            <div className="flex flex-wrap gap-2">
              {result.flags.map((flag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium"
                >
                  {flag}
                </span>
              ))}
            </div>
          </div>
        )}
      </Card>

      {/* Summary */}
      {result.summary && (
        <Card title="Summary" variant="bordered">
          <p className="text-gray-700">{result.summary}</p>
        </Card>
      )}

      {/* Findings Tabs */}
      <Card variant="bordered">
        <div className="border-b border-gray-200 mb-4">
          <nav className="flex gap-4" aria-label="Findings categories">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-4 py-2 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300'
                  }
                `}
                aria-current={activeTab === tab.id ? 'page' : undefined}
              >
                {tab.label}
                <span className="ml-2 px-2 py-0.5 bg-gray-100 rounded-full text-xs">
                  {tab.count}
                </span>
              </button>
            ))}
          </nav>
        </div>

        {/* Findings Content */}
        <div>
          {activeTab === 'fiscal' && (
            <FiscalFindingsView findings={result.findings.fiscal} />
          )}
          {activeTab === 'constitutional' && (
            <div className="text-gray-500 text-center py-8">
              Constitutional findings view (component to be implemented)
            </div>
          )}
          {activeTab === 'surveillance' && (
            <div className="text-gray-500 text-center py-8">
              Surveillance findings view (component to be implemented)
            </div>
          )}
          {activeTab === 'anomalies' && (
            <div className="text-gray-500 text-center py-8">
              Anomalies view (component to be implemented)
            </div>
          )}
        </div>
      </Card>

      {/* Provenance */}
      <Card title="Provenance" variant="bordered">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Pipeline Version:</span>
            <span className="font-mono text-gray-900">
              {result.provenance.pipeline_version}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Analysis Timestamp:</span>
            <span className="font-mono text-gray-900">
              {new Date(result.provenance.analysis_timestamp).toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Confidence:</span>
            <span className="font-mono text-gray-900">
              {(result.confidence * 100).toFixed(1)}%
            </span>
          </div>
          {result.provenance.document_hash && (
            <div className="flex justify-between">
              <span className="text-gray-600">Document Hash:</span>
              <span className="font-mono text-xs text-gray-900">
                {result.provenance.document_hash}
              </span>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
