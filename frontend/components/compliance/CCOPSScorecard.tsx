/**
 * CCOPS Scorecard — displays the 11 ACLU Community Control Over Police Surveillance
 * mandates and their compliance status derived from audit findings.
 */

'use client';

import React from 'react';
import type { AuditFinding, CCOPSMandate } from '@/lib/types/api';

// The 11 CCOPS mandates (titles from the ACLU model ordinance)
const MANDATE_DEFINITIONS = [
  {
    id: 'surveillance-use-policy',
    title: 'Surveillance Use Policy',
    description: 'Each surveillance technology must have a written use policy limiting how it may be used.',
    detectors: ['surveillance', 'governance_gap'],
  },
  {
    id: 'data-minimization',
    title: 'Data Minimization',
    description: 'Surveillance data must only be collected to the extent necessary and must not be retained longer than required.',
    detectors: ['surveillance', 'administrative_integrity'],
  },
  {
    id: 'data-security',
    title: 'Data Security',
    description: 'Surveillance data must be protected from unauthorised access and use.',
    detectors: ['surveillance', 'administrative_integrity'],
  },
  {
    id: 'prohibitions',
    title: 'Prohibitions on Use',
    description: 'Surveillance technology must not be used to track protected activities or to discriminate.',
    detectors: ['surveillance', 'constitutional'],
  },
  {
    id: 'data-sharing',
    title: 'Data Sharing Restrictions',
    description: 'Data obtained from surveillance technology must not be shared without community approval.',
    detectors: ['cross_reference', 'surveillance'],
  },
  {
    id: 'accountability',
    title: 'Public Accountability',
    description: 'Governing body must approve acquisition and use policy in a public meeting.',
    detectors: ['governance_gap', 'procurement_timeline'],
  },
  {
    id: 'auditing',
    title: 'Annual Reporting & Auditing',
    description: 'Annual report on use, effectiveness, complaints, and costs must be submitted to the governing body.',
    detectors: ['governance_gap', 'administrative_integrity'],
  },
  {
    id: 'civil-rights-assessment',
    title: 'Civil Rights Impact Assessment',
    description: 'A civil rights impact assessment must be conducted before technology is acquired.',
    detectors: ['constitutional', 'governance_gap'],
  },
  {
    id: 'community-process',
    title: 'Community Input Process',
    description: 'Community input must be solicited and considered before acquisition or material changes.',
    detectors: ['governance_gap', 'scope_expansion'],
  },
  {
    id: 'cost-reporting',
    title: 'Cost Reporting',
    description: 'Complete procurement costs including ongoing expenses must be publicly reported.',
    detectors: ['fiscal', 'procurement_timeline'],
  },
  {
    id: 'enforcement',
    title: 'Enforcement & Remedy',
    description: 'Violations of the use policy must result in consequences including suppression of evidence.',
    detectors: ['governance_gap', 'administrative_integrity'],
  },
];

const STATUS_STYLES: Record<string, { bg: string; text: string; icon: string; label: string }> = {
  pass:    { bg: 'bg-green-50',  text: 'text-green-700',  icon: '✓', label: 'No issues' },
  fail:    { bg: 'bg-red-50',    text: 'text-red-700',    icon: '✗', label: 'Findings' },
  warn:    { bg: 'bg-yellow-50', text: 'text-yellow-700', icon: '!', label: 'Warnings' },
  unknown: { bg: 'bg-gray-50',   text: 'text-gray-500',   icon: '?', label: 'No data' },
};

export function buildCCOPSMandates(findings: AuditFinding[]): CCOPSMandate[] {
  return MANDATE_DEFINITIONS.map((def) => {
    const relevant = findings.filter(
      (f) => def.detectors.includes(f.layer) || def.detectors.some((d) => f.id?.startsWith(d)),
    );
    const hasCriticalHigh = relevant.some(
      (f) => f.severity === 'critical' || f.severity === 'high',
    );
    const hasMediumLow = relevant.some(
      (f) => f.severity === 'medium' || f.severity === 'low',
    );

    const status: CCOPSMandate['status'] = hasCriticalHigh
      ? 'fail'
      : hasMediumLow
        ? 'warn'
        : relevant.length === 0
          ? 'unknown'
          : 'pass';

    return {
      id: def.id,
      title: def.title,
      description: def.description,
      status,
      evidence: relevant.map((f) => f.issue).slice(0, 3),
    };
  });
}

interface CCOPSScorecardProps {
  findings: AuditFinding[];
}

export function CCOPSScorecard({ findings }: CCOPSScorecardProps) {
  const mandates = buildCCOPSMandates(findings);
  const passed = mandates.filter((m) => m.status === 'pass').length;
  const failed = mandates.filter((m) => m.status === 'fail').length;
  const warned = mandates.filter((m) => m.status === 'warn').length;

  return (
    <div className="space-y-4">
      {/* Summary row */}
      <div className="flex flex-wrap gap-4 p-4 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{passed}</div>
          <div className="text-xs text-gray-500">No issues</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{warned}</div>
          <div className="text-xs text-gray-500">Warnings</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{failed}</div>
          <div className="text-xs text-gray-500">Findings</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-400">
            {mandates.filter((m) => m.status === 'unknown').length}
          </div>
          <div className="text-xs text-gray-500">No data</div>
        </div>
        <div className="ml-auto flex items-center">
          <p className="text-xs text-gray-400">11 ACLU CCOPS mandates</p>
        </div>
      </div>

      {/* Mandate list */}
      <div className="space-y-2">
        {mandates.map((mandate) => {
          const styles = STATUS_STYLES[mandate.status];
          return (
            <div
              key={mandate.id}
              className={`rounded-lg border border-gray-100 p-3 ${styles.bg}`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold ${styles.bg} ${styles.text} border border-current`}
                  aria-label={styles.label}
                >
                  {styles.icon}
                </span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${styles.text}`}>{mandate.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{mandate.description}</p>
                  {mandate.evidence.length > 0 && (
                    <ul className="mt-1 space-y-0.5">
                      {mandate.evidence.map((e, i) => (
                        <li key={i} className="text-xs text-gray-600 flex gap-1">
                          <span aria-hidden="true">›</span> {e}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
