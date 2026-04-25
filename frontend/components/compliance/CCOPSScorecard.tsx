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

// v2.7.4 W3: HUD primitive tones for the four mandate states.
// Replaces the pre-W3 light-theme bg-green-50 / bg-red-50 / etc. that
// rendered as pale pastels on slate-950. Each entry maps to:
//   - tone:    text colour for the title + status icon ring
//   - sevPill: hud-sev-* class for the right-side state pill
//   - icon:    glyph rendered in the circle on the left
const STATUS_STYLES: Record<
  string,
  { tone: string; sevPill: string; icon: string; label: string }
> = {
  pass:    { tone: 'text-emerald-400', sevPill: 'hud-sev-healthy',  icon: '✓', label: 'No issues' },
  fail:    { tone: 'text-rose-400',    sevPill: 'hud-sev-critical', icon: '✗', label: 'Findings' },
  warn:    { tone: 'text-yellow-400',  sevPill: 'hud-sev-medium',   icon: '!', label: 'Warnings' },
  unknown: { tone: 'text-zinc-500',    sevPill: 'hud-sev-info',     icon: '?', label: 'No data' },
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

  const noData = mandates.filter((m) => m.status === 'unknown').length;

  return (
    <div className="space-y-4">
      {/* v2.7.4 W3: summary row uses HUD primitive panel + counter
          tones matching the scorecard mandate tiles. */}
      <div className="hud-panel hud-panel-inset p-4 flex flex-wrap gap-6">
        <ScorecardCounter value={passed} label="No issues" tone="text-emerald-400" />
        <ScorecardCounter value={warned} label="Warnings" tone="text-yellow-400" />
        <ScorecardCounter value={failed} label="Findings" tone="text-rose-400" />
        <ScorecardCounter value={noData} label="No data" tone="text-zinc-500" />
        <div className="ml-auto flex items-center">
          <p className="hud-metric-label">11 ACLU CCOPS mandates</p>
        </div>
      </div>

      {/* Mandate list */}
      <div className="space-y-2">
        {mandates.map((mandate) => {
          const styles = STATUS_STYLES[mandate.status];
          return (
            <div
              key={mandate.id}
              className="hud-panel hud-panel-dense p-3"
            >
              <div className="flex items-start gap-3">
                <span
                  className={`
                    flex-shrink-0 w-6 h-6 rounded-full flex items-center
                    justify-center text-sm font-bold border ${styles.tone}
                    border-current bg-slate-900/60
                  `}
                  aria-label={styles.label}
                >
                  {styles.icon}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className={`text-sm font-semibold ${styles.tone}`}>
                      {mandate.title}
                    </p>
                    <span className={`hud-sev ${styles.sevPill}`}>
                      {styles.label.toLowerCase()}
                    </span>
                  </div>
                  <p className="hud-subtext text-xs mt-1">{mandate.description}</p>
                  {mandate.evidence.length > 0 && (
                    <ul className="mt-2 space-y-0.5">
                      {mandate.evidence.map((e, i) => (
                        <li
                          key={i}
                          className="text-xs text-slate-400 flex gap-1.5"
                        >
                          <span aria-hidden="true" className="text-slate-600">
                            ›
                          </span>
                          <span className="break-words">{e}</span>
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

function ScorecardCounter({
  value,
  label,
  tone,
}: {
  value: number;
  label: string;
  tone: string;
}) {
  return (
    <div className="text-center">
      <div className={`hud-metric tabular-nums ${tone}`}>{value}</div>
      <div className="hud-metric-label">{label}</div>
    </div>
  );
}
