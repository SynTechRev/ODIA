/**
 * Dashboard Page
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

        {/* Hero */}
        <div
          className="relative rounded-xl overflow-hidden p-8"
          style={{
            background: 'linear-gradient(135deg, #071526 0%, #0a1f3a 40%, #0d2b4e 100%)',
            border: '1px solid var(--border)',
          }}
        >
          {/* Decorative grid overlay */}
          <div
            className="absolute inset-0 opacity-5 pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(var(--accent) 1px, transparent 1px), linear-gradient(90deg, var(--accent) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
            }}
          />
          {/* Gold top-left accent bar */}
          <div
            className="absolute top-0 left-0 h-1 w-32 rounded-br"
            style={{ background: 'linear-gradient(90deg, var(--gold), transparent)' }}
          />

          <div className="relative">
            <div className="flex items-center gap-3 mb-3">
              <span
                className="text-xs font-black tracking-[0.3em] px-2.5 py-1 rounded"
                style={{
                  background: 'rgba(212,160,23,0.15)',
                  color: 'var(--gold)',
                  border: '1px solid rgba(212,160,23,0.3)',
                }}
              >
                O.D.I.A.
              </span>
              <span
                className="text-xs font-medium"
                style={{ color: 'var(--muted)' }}
              >
                v2.1.2
              </span>
            </div>

            <h1
              className="text-3xl font-black mb-1 tracking-tight"
              style={{ color: 'var(--foreground)' }}
            >
              Oraculus Decimus Intellect Analyst
            </h1>
            <p className="text-sm mb-6 max-w-xl" style={{ color: 'var(--muted)' }}>
              Civic accountability intelligence — forensic anomaly detection, cross-jurisdiction
              procurement analysis, and CCOPS compliance assessment for legal documents.
            </p>

            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => router.push('/ingest')}
                className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 hover:opacity-90 active:scale-95"
                style={{ background: 'var(--accent)', color: '#fff' }}
              >
                Upload Document
              </button>
              <button
                onClick={() => router.push('/analysis')}
                className="px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-150 hover:bg-white/10 active:scale-95"
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  color: 'var(--foreground)',
                  border: '1px solid var(--border)',
                }}
              >
                View Analyses
              </button>
            </div>
          </div>
        </div>

        {/* Severity counters */}
        {hasAnomalyData && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Critical', value: severityTotals.critical, color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
              { label: 'High',     value: severityTotals.high,     color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
              { label: 'Medium',   value: severityTotals.medium,   color: '#eab308', bg: 'rgba(234,179,8,0.1)' },
              { label: 'Low',      value: severityTotals.low,      color: 'var(--muted)', bg: 'rgba(122,154,184,0.1)' },
            ].map(({ label, value, color, bg }) => (
              <div
                key={label}
                className="rounded-lg p-4 text-center"
                style={{ background: bg, border: `1px solid ${color}30` }}
              >
                <div className="text-3xl font-black mb-0.5" style={{ color }}>{value}</div>
                <div className="text-xs font-semibold tracking-wide uppercase" style={{ color: 'var(--muted)' }}>
                  {label}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Status cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemStatusCard />
          <AnalysisSummaryCard />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <JurisdictionCard />
          <DetectorStatusCard />
        </div>

        {/* Quick actions */}
        <div
          className="rounded-xl p-6"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3
            className="text-xs font-bold tracking-widest uppercase mb-4"
            style={{ color: 'var(--muted)' }}
          >
            Quick Actions
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { href: '/ingest',    icon: '▤', label: 'Ingest Document',  sub: 'Upload and analyze new documents' },
              { href: '/documents', icon: '▣', label: 'Browse Documents', sub: 'View all ingested documents' },
              { href: '/anomalies', icon: '△', label: 'Explore Anomalies',sub: 'Review detected anomalies by detector' },
            ].map(({ href, icon, label, sub }) => (
              <button
                key={href}
                onClick={() => router.push(href)}
                className="p-4 rounded-lg text-left transition-all duration-150 hover:scale-[1.01] active:scale-95"
                style={{
                  background: 'var(--surface-2)',
                  border: '1px solid var(--border)',
                }}
                onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--accent)')}
                onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
              >
                <div
                  className="text-2xl mb-2 font-mono"
                  style={{ color: 'var(--accent)' }}
                >
                  {icon}
                </div>
                <div className="text-sm font-semibold mb-0.5" style={{ color: 'var(--foreground)' }}>
                  {label}
                </div>
                <div className="text-xs" style={{ color: 'var(--muted)' }}>{sub}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Feature overview */}
        <div
          className="rounded-xl p-6"
          style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
          <h3
            className="text-xs font-bold tracking-widest uppercase mb-4"
            style={{ color: 'var(--muted)' }}
          >
            Platform Capabilities
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {[
              {
                icon: '◎', color: 'var(--accent)',
                title: '12-Detector Analysis Engine',
                body: 'Fiscal, constitutional, surveillance, procurement, signature, scope, governance, and administrative integrity detection.',
              },
              {
                icon: '⊛', color: 'var(--gold)',
                title: 'Phase 5–9 Orchestration',
                body: 'Multi-agent autonomous task graph with dependency resolution and parallel execution.',
              },
              {
                icon: '⬡', color: '#a78bfa',
                title: 'CCOPS Compliance Engine',
                body: '11 ACLU mandate checks mapped to detector findings with automated scorecard generation.',
              },
              {
                icon: '▤', color: '#34d399',
                title: 'Full Provenance Tracking',
                body: 'SHA-256 hashing, contract lineage reconstruction, and cryptographic chain-of-custody.',
              },
            ].map(({ icon, color, title, body }) => (
              <div key={title} className="flex gap-3">
                <div
                  className="w-8 h-8 rounded-md flex items-center justify-center text-sm flex-shrink-0 font-mono"
                  style={{ background: `${color}18`, color }}
                >
                  {icon}
                </div>
                <div>
                  <div className="text-sm font-semibold mb-0.5" style={{ color: 'var(--foreground)' }}>
                    {title}
                  </div>
                  <div className="text-xs leading-relaxed" style={{ color: 'var(--muted)' }}>
                    {body}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </DashboardLayout>
  );
}
