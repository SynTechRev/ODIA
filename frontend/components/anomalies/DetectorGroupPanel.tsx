/**
 * DetectorGroupPanel - Displays anomalies from /analyze/detailed grouped by detector.
 *
 * Each detector gets its own collapsible section. Anomalies are color-coded
 * by severity. Clicking an anomaly expands an evidence panel showing details.
 */

'use client';

import React, { useState } from 'react';
import type { Anomaly, DetailedAnalysisResult } from '@/lib/types/api';

// ---------------------------------------------------------------------------
// Severity helpers
// ---------------------------------------------------------------------------

const SEVERITY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-gray-100 text-gray-800',
};

const SEVERITY_BORDER: Record<string, string> = {
  critical: 'border-red-400',
  high: 'border-orange-400',
  medium: 'border-yellow-400',
  low: 'border-gray-300',
};

const DETECTOR_LABELS: Record<string, string> = {
  fiscal: 'Fiscal',
  constitutional: 'Constitutional',
  surveillance: 'Surveillance',
  procurement_timeline: 'Procurement Timeline',
  signature_chain: 'Signature Chain',
  scope_expansion: 'Scope Expansion',
  governance_gap: 'Governance Gap',
  administrative_integrity: 'Administrative Integrity',
};

const DETECTOR_ICONS: Record<string, string> = {
  fiscal: '💰',
  constitutional: '⚖️',
  surveillance: '👁️',
  procurement_timeline: '📅',
  signature_chain: '✍️',
  scope_expansion: '📈',
  governance_gap: '🏛️',
  administrative_integrity: '📋',
};

// ---------------------------------------------------------------------------
// AnomalyRow — single expandable anomaly entry
// ---------------------------------------------------------------------------

function AnomalyRow({ anomaly }: { anomaly: Anomaly }) {
  const [expanded, setExpanded] = useState(false);

  const evidenceEntries = Object.entries(anomaly.details ?? {});

  return (
    <div
      className={`border-l-4 rounded-r-lg mb-2 ${SEVERITY_BORDER[anomaly.severity] ?? 'border-gray-300'}`}
    >
      <button
        className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors rounded-r-lg"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <span className="font-mono text-xs text-gray-500 block mb-0.5">
              {anomaly.id}
            </span>
            <span className="text-sm font-medium text-gray-900">
              {anomaly.issue}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span
              className={`px-2 py-0.5 rounded text-xs font-medium ${SEVERITY_BADGE[anomaly.severity] ?? 'bg-gray-100 text-gray-800'}`}
            >
              {anomaly.severity}
            </span>
            <span className="text-gray-400 text-xs">{expanded ? '▲' : '▼'}</span>
          </div>
        </div>
      </button>

      {expanded && (
        <div className="px-4 pb-4">
          {evidenceEntries.length > 0 ? (
            <div className="bg-gray-50 rounded-lg p-3 space-y-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Evidence
              </div>
              {evidenceEntries.map(([key, value]) => (
                <div key={key} className="flex gap-2 text-sm">
                  <span className="text-gray-500 font-medium min-w-[130px] flex-shrink-0 capitalize">
                    {key.replace(/_/g, ' ')}:
                  </span>
                  <span className="text-gray-800 font-mono text-xs break-all">
                    {Array.isArray(value)
                      ? value.join(', ')
                      : typeof value === 'object' && value !== null
                        ? JSON.stringify(value)
                        : String(value ?? '')}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-gray-400 italic">No additional details.</div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DetectorSection — collapsible section for one detector
// ---------------------------------------------------------------------------

function DetectorSection({
  name,
  anomalies,
}: {
  name: string;
  anomalies: Anomaly[];
}) {
  const [open, setOpen] = useState(anomalies.length > 0);

  const label = DETECTOR_LABELS[name] ?? name.replace(/_/g, ' ');
  const icon = DETECTOR_ICONS[name] ?? '🔍';
  const hasCritical = anomalies.some((a) => a.severity === 'critical');
  const hasHigh = anomalies.some((a) => a.severity === 'high');

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        className={`w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 transition-colors ${
          anomalies.length === 0 ? 'opacity-60' : ''
        }`}
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">{icon}</span>
          <span className="font-medium text-gray-900">{label}</span>
          {hasCritical && (
            <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium">
              critical
            </span>
          )}
          {!hasCritical && hasHigh && (
            <span className="px-1.5 py-0.5 bg-orange-100 text-orange-700 text-xs rounded font-medium">
              high
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`text-sm font-semibold ${
              anomalies.length === 0
                ? 'text-gray-400'
                : hasCritical
                  ? 'text-red-600'
                  : hasHigh
                    ? 'text-orange-600'
                    : 'text-gray-700'
            }`}
          >
            {anomalies.length}{' '}
            {anomalies.length === 1 ? 'finding' : 'findings'}
          </span>
          <span className="text-gray-400 text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {open && (
        <div className="px-4 py-3 border-t border-gray-100 bg-white">
          {anomalies.length === 0 ? (
            <p className="text-sm text-gray-400 italic text-center py-2">
              No anomalies detected by this detector.
            </p>
          ) : (
            anomalies.map((anomaly, i) => (
              <AnomalyRow key={`${anomaly.id}-${i}`} anomaly={anomaly} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DetectorGroupPanel — public export
// ---------------------------------------------------------------------------

interface DetectorGroupPanelProps {
  result: DetailedAnalysisResult;
}

const DETECTOR_ORDER = [
  'fiscal',
  'constitutional',
  'surveillance',
  'procurement_timeline',
  'signature_chain',
  'scope_expansion',
  'governance_gap',
  'administrative_integrity',
] as const;

export function DetectorGroupPanel({ result }: DetectorGroupPanelProps) {
  return (
    <div className="space-y-3">
      {DETECTOR_ORDER.map((name) => (
        <DetectorSection
          key={name}
          name={name}
          anomalies={result.detectors[name] ?? []}
        />
      ))}
    </div>
  );
}
