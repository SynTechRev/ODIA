/**
 * Fiscal Findings View Component
 *
 * Displays fiscal anomalies from the /analyze endpoint.
 * Uses the Anomaly type (id, issue, severity, layer, details) matching
 * the actual backend response shape.
 */

'use client';

import React from 'react';
import { Panel } from '../base/Panel';
import type { Anomaly } from '@/lib/types/api';

interface FiscalFindingsViewProps {
  findings: Anomaly[];
}

export function FiscalFindingsView({ findings }: FiscalFindingsViewProps) {
  if (findings.length === 0) {
    return (
      <Panel>
        <p className="text-gray-500 text-center py-4">No fiscal findings detected</p>
      </Panel>
    );
  }

  return (
    <Panel>
      <div className="space-y-4">
        {findings.map((finding, index) => {
          const details = finding.details ?? {};
          const sampleAmounts = Array.isArray(details.sample_amounts)
            ? (details.sample_amounts as string[]).join(', ')
            : null;

          return (
            <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-mono text-xs text-gray-500">{finding.id}</h4>
                <span
                  className={`
                    px-2 py-1 rounded text-xs font-medium flex-shrink-0 ml-2
                    ${finding.severity === 'critical' ? 'bg-red-100 text-red-800' :
                      finding.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                      finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'}
                  `}
                >
                  {finding.severity}
                </span>
              </div>

              <p className="text-sm font-medium text-gray-900 mb-2">{finding.issue}</p>

              {sampleAmounts && (
                <p className="text-sm text-gray-600 mb-2">
                  <span className="font-medium">Amounts:</span> {sampleAmounts}
                </p>
              )}

              {Object.keys(details).length > 0 && (
                <div className="bg-gray-50 p-2 rounded text-xs font-mono text-gray-600 mt-2 space-y-1">
                  {Object.entries(details).map(([key, value]) => (
                    <div key={key}>
                      <span className="text-gray-500">{key}: </span>
                      <span>
                        {Array.isArray(value) ? value.join(', ') : String(value ?? '')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Panel>
  );
}
