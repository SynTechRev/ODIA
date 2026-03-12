/**
 * Anomalies Page - Browse and explore anomalies
 */

'use client';

import React, { useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useAnalysisStore } from '@/lib/stores/analysis';
import { useAnomalyStore } from '@/lib/stores/anomaly';
import { Card } from '@/components/base/Card';
import { Panel } from '@/components/base/Panel';
import type { Finding } from '@/lib/types/api';

export default function AnomaliesPage() {
  const analyses = useAnalysisStore((state) => state.analyses);
  const anomalies = useAnomalyStore((state) => state.anomalies);
  const setAnomalies = useAnomalyStore((state) => state.setAnomalies);
  const filterSeverity = useAnomalyStore((state) => state.filterSeverity);
  const setFilterSeverity = useAnomalyStore((state) => state.setFilterSeverity);
  const selectedAnomaly = useAnomalyStore((state) => state.selectedAnomaly);
  const selectAnomaly = useAnomalyStore((state) => state.selectAnomaly);

  // Aggregate anomalies from all analyses
  useEffect(() => {
    const allAnomalies: Finding[] = [];
    
    Object.values(analyses).forEach((analysis) => {
      // Collect all findings as anomalies
      allAnomalies.push(...analysis.findings.fiscal);
      allAnomalies.push(...analysis.findings.constitutional);
      allAnomalies.push(...analysis.findings.surveillance);
      allAnomalies.push(...analysis.findings.anomalies);
    });
    
    setAnomalies(allAnomalies);
  }, [analyses, setAnomalies]);

  // Filter anomalies
  const filteredAnomalies = anomalies.filter((anomaly) => {
    if (filterSeverity !== 'all' && anomaly.severity !== filterSeverity) {
      return false;
    }
    return true;
  });

  // Group by severity
  const bySeverity = {
    critical: filteredAnomalies.filter((a) => a.severity === 'critical'),
    high: filteredAnomalies.filter((a) => a.severity === 'high'),
    medium: filteredAnomalies.filter((a) => a.severity === 'medium'),
    low: filteredAnomalies.filter((a) => a.severity === 'low'),
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">{bySeverity.critical.length}</div>
              <div className="text-sm text-gray-600">Critical</div>
            </div>
          </Card>
          
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">{bySeverity.high.length}</div>
              <div className="text-sm text-gray-600">High</div>
            </div>
          </Card>
          
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-600">{bySeverity.medium.length}</div>
              <div className="text-sm text-gray-600">Medium</div>
            </div>
          </Card>
          
          <Card variant="bordered">
            <div className="text-center">
              <div className="text-3xl font-bold text-gray-600">{bySeverity.low.length}</div>
              <div className="text-sm text-gray-600">Low</div>
            </div>
          </Card>
        </div>

        {/* Filter */}
        <Card variant="bordered">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium text-gray-700">
              Filter by Severity:
            </label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value as any)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </Card>

        {/* Anomalies List */}
        {filteredAnomalies.length === 0 ? (
          <Card variant="bordered">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✓</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Anomalies Found
              </h3>
              <p className="text-gray-600">
                {anomalies.length === 0
                  ? 'Analyze documents to detect anomalies.'
                  : 'No anomalies match the current filter.'}
              </p>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Anomalies List */}
            <div className="lg:col-span-1">
              <Card title={`Anomalies (${filteredAnomalies.length})`} variant="bordered">
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {filteredAnomalies.map((anomaly, index) => (
                    <button
                      key={index}
                      onClick={() => selectAnomaly(anomaly)}
                      className={`
                        w-full text-left p-3 rounded-lg border-2 transition-colors
                        ${selectedAnomaly === anomaly
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <span className="font-medium text-sm text-gray-900">
                          {anomaly.type}
                        </span>
                        <span
                          className={`
                            px-2 py-0.5 rounded text-xs font-medium
                            ${anomaly.severity === 'critical' ? 'bg-red-100 text-red-800' :
                              anomaly.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                              anomaly.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-gray-100 text-gray-800'}
                          `}
                        >
                          {anomaly.severity}
                        </span>
                      </div>
                      <div className="text-xs text-gray-600 line-clamp-2">
                        {anomaly.description}
                      </div>
                    </button>
                  ))}
                </div>
              </Card>
            </div>

            {/* Anomaly Details */}
            <div className="lg:col-span-2">
              {selectedAnomaly ? (
                <Card title="Anomaly Details" variant="bordered">
                  <div className="space-y-4">
                    <div>
                      <div className="text-sm text-gray-600 mb-1">Type</div>
                      <div className="font-medium text-gray-900">{selectedAnomaly.type}</div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Severity</div>
                      <span
                        className={`
                          inline-block px-3 py-1 rounded text-sm font-medium
                          ${selectedAnomaly.severity === 'critical' ? 'bg-red-100 text-red-800' :
                            selectedAnomaly.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                            selectedAnomaly.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-gray-100 text-gray-800'}
                        `}
                      >
                        {selectedAnomaly.severity}
                      </span>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Description</div>
                      <div className="text-gray-900">{selectedAnomaly.description}</div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Detector</div>
                      <div className="font-mono text-sm text-gray-900">
                        {selectedAnomaly.detector}
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-1">Confidence</div>
                      <div className="text-gray-900">
                        {(selectedAnomaly.confidence * 100).toFixed(1)}%
                      </div>
                    </div>

                    <div>
                      <div className="text-sm text-gray-600 mb-2">Text Location</div>
                      <Panel padding="sm">
                        <pre className="text-sm font-mono text-gray-700 whitespace-pre-wrap">
                          {selectedAnomaly.location.text}
                        </pre>
                      </Panel>
                    </div>
                  </div>
                </Card>
              ) : (
                <Card variant="bordered">
                  <div className="text-center py-12 text-gray-500">
                    Select an anomaly to view details
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
