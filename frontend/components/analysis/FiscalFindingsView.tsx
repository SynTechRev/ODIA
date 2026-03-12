/**
 * Fiscal Findings View Component
 */

'use client';

import React from 'react';
import { Panel } from '../base/Panel';
import type { FiscalFinding } from '@/lib/types/api';

interface FiscalFindingsViewProps {
  findings: FiscalFinding[];
}

export function FiscalFindingsView({ findings }: FiscalFindingsViewProps) {
  if (findings.length === 0) {
    return (
      <Panel>
        <p className="text-gray-500 text-center py-4">
          No fiscal findings detected
        </p>
      </Panel>
    );
  }

  return (
    <Panel>
      <div className="space-y-4">
        {findings.map((finding, index) => (
          <div
            key={index}
            className="border-l-4 border-blue-500 pl-4 py-2"
          >
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-medium text-gray-900">{finding.type}</h4>
              <span
                className={`
                  px-2 py-1 rounded text-xs font-medium
                  ${finding.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    finding.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    finding.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'}
                `}
              >
                {finding.severity}
              </span>
            </div>
            
            <p className="text-sm text-gray-700 mb-2">{finding.description}</p>
            
            {finding.fiscal_amount && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Amount:</span> {finding.fiscal_amount}
              </p>
            )}

            {finding.appropriation_status && (
              <p className="text-sm text-gray-600 mb-2">
                <span className="font-medium">Status:</span>{' '}
                {finding.appropriation_status.replace(/_/g, ' ')}
              </p>
            )}
            
            <div className="bg-gray-50 p-2 rounded text-xs font-mono text-gray-600 mt-2">
              {finding.location.text}
            </div>
            
            <div className="mt-2 text-xs text-gray-500">
              Confidence: {(finding.confidence * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
