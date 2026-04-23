/**
 * Dashboard — main landing view.
 *
 * Sections:
 *   1. Hero — brand statement + primary CTAs
 *   2. Severity strip (conditional — only when analyses exist)
 *   3. System Status × Analysis Summary cards
 *   4. Jurisdiction × Detectors cards
 *   5. Quick Actions tiles
 *   6. Platform Capabilities (static copy)
 */

'use client';

import React from 'react';
import { useAppNavigate } from '@/lib/navigation';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { SystemStatusCard } from '@/components/dashboard/SystemStatusCard';
import { AnalysisSummaryCard } from '@/components/dashboard/AnalysisSummaryCard';
import { JurisdictionCard } from '@/components/dashboard/JurisdictionCard';
import { DetectorStatusCard } from '@/components/dashboard/DetectorStatusCard';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import {
  UploadIcon,
  AnalysisIcon,
  IngestIcon,
  DocumentsIcon,
  AnomaliesIcon,
  OrchestratorIcon,
  StrategyMarkIcon,
  CheckCircleIcon,
} from '@/components/base/Icons';
import { useAnalysisStore } from '@/lib/stores/analysis';

export default function Home() {
  const nav = useAppNavigate();
  const detailedAnalyses = useAnalysisStore((state) => state.detailedAnalyses);

  const severityTotals = Object.values(detailedAnalyses).reduce(
    (acc, a) => {
      acc.critical += a.summary.by_severity.critical;
      acc.high     += a.summary.by_severity.high;
      acc.medium   += a.summary.by_severity.medium;
      acc.low      += a.summary.by_severity.low;
      return acc;
    },
    { critical: 0, high: 0, medium: 0, low: 0 },
  );

  const hasAnomalyData = Object.keys(detailedAnalyses).length > 0;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* =============================================================== */}
        {/* 1 · Hero                                                         */}
        {/* =============================================================== */}
        <section
          className="
            relative overflow-hidden rounded-md text-white odia-targets
            bg-gradient-to-br from-slate-950 via-slate-900 to-slate-800
            ring-1 ring-amber-500/30
            shadow-[0_0_24px_-6px_rgba(245,158,11,0.35),0_1px_0_rgba(255,255,255,0.04)_inset]
          "
        >
          {/* Decorative grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.06] pointer-events-none"
            aria-hidden="true"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
              backgroundSize: '24px 24px',
            }}
          />
          {/* Accent glow */}
          <div
            className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-amber-500/20 blur-3xl pointer-events-none"
            aria-hidden="true"
          />
          <div className="relative p-8 md:p-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-amber-500/10 text-amber-300 text-xs font-medium ring-1 ring-amber-500/40 mb-4 shadow-[0_0_8px_-2px_rgba(245,158,11,0.5)]">
              <StrategyMarkIcon size={12} />
              Oraculus Decimus Intellect Analyst · v2.6.0
            </div>
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight mb-3">
              Civic accountability,
              <br className="hidden md:block" />
              at forensic resolution.
            </h1>
            <p className="text-slate-300 max-w-2xl mb-6 text-sm md:text-base leading-relaxed">
              Ingest legal and government documents. Surface fiscal anomalies,
              constitutional concerns, surveillance outsourcing, and procurement
              irregularities — all locally, all private, all auditable.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Button
                variant="accent"
                size="lg"
                onClick={() => nav('/upload')}
                icon={<UploadIcon size={16} />}
              >
                Upload Document
              </Button>
              <Button
                variant="ghost"
                size="lg"
                onClick={() => nav('/analysis')}
                className="text-white hover:bg-white/10 border border-white/20"
                icon={<AnalysisIcon size={16} />}
              >
                View Analyses
              </Button>
            </div>
            <div className="mt-6 flex flex-wrap gap-4 text-xs text-slate-400">
              <InlineFeature label="100% local processing" />
              <InlineFeature label="SHA-256 provenance" />
              <InlineFeature label="8-detector pipeline" />
              <InlineFeature label="No outbound network" />
            </div>
          </div>
        </section>

        {/* =============================================================== */}
        {/* 2 · Severity strip (conditional)                                 */}
        {/* =============================================================== */}
        {hasAnomalyData && (
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <SeverityTile label="Critical" count={severityTotals.critical} tone="critical" />
            <SeverityTile label="High"     count={severityTotals.high}     tone="high" />
            <SeverityTile label="Medium"   count={severityTotals.medium}   tone="medium" />
            <SeverityTile label="Low"      count={severityTotals.low}      tone="low" />
          </section>
        )}

        {/* =============================================================== */}
        {/* 3 · System × Analysis cards                                      */}
        {/* =============================================================== */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <SystemStatusCard />
          <AnalysisSummaryCard />
        </section>

        {/* =============================================================== */}
        {/* 4 · Jurisdiction × Detectors                                     */}
        {/* =============================================================== */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <JurisdictionCard />
          <DetectorStatusCard />
        </section>

        {/* =============================================================== */}
        {/* 5 · Quick Actions                                                */}
        {/* =============================================================== */}
        <Card title="Quick Actions" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <ActionTile
              onClick={() => nav('/ingest')}
              icon={<IngestIcon size={22} />}
              title="Ingest Document"
              subtitle="Upload and analyse new documents"
            />
            <ActionTile
              onClick={() => nav('/documents')}
              icon={<DocumentsIcon size={22} />}
              title="Browse Documents"
              subtitle="View all ingested documents"
            />
            <ActionTile
              onClick={() => nav('/anomalies')}
              icon={<AnomaliesIcon size={22} />}
              title="Explore Anomalies"
              subtitle="Review findings by detector"
            />
          </div>
        </Card>

        {/* =============================================================== */}
        {/* 6 · Platform Capabilities                                        */}
        {/* =============================================================== */}
        <Card title="Platform Capabilities" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Feature
              icon={<AnalysisIcon size={18} />}
              title="8-Detector Analysis Engine"
              body="Fiscal, constitutional, surveillance, procurement, signature, scope, governance, and administrative integrity detection — all executed locally."
            />
            <Feature
              icon={<OrchestratorIcon size={18} />}
              title="Phase 5–9 Orchestration"
              body="Multi-agent autonomous task graph with dependency resolution and parallel execution across the detector registry."
            />
            <Feature
              icon={<CheckCircleIcon size={18} />}
              title="CCOPS Compliance Engine"
              body="11 ACLU mandate checks mapped to detector findings with automated scorecard generation for oversight review."
            />
            <Feature
              icon={<StrategyMarkIcon size={18} />}
              title="Full Provenance Tracking"
              body="SHA-256 hashing, contract lineage reconstruction, and cryptographic chain-of-custody for every analysed document."
            />
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function InlineFeature({ label }: { label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="w-1 h-1 rounded-full bg-amber-400" />
      {label}
    </span>
  );
}

function SeverityTile({
  label,
  count,
  tone,
}: {
  label: string;
  count: number;
  tone: 'critical' | 'high' | 'medium' | 'low';
}) {
  const toneMap = {
    critical: { text: 'text-red-700',    dot: 'bg-red-700',     ring: 'ring-red-200' },
    high:     { text: 'text-red-600',    dot: 'bg-red-500',     ring: 'ring-red-100' },
    medium:   { text: 'text-orange-600', dot: 'bg-orange-500',  ring: 'ring-orange-100' },
    low:      { text: 'text-yellow-700', dot: 'bg-yellow-500',  ring: 'ring-yellow-100' },
  };
  const t = toneMap[tone];
  return (
    <div className={`bg-white border border-slate-200 rounded-xl p-4 ring-1 ${t.ring}`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${t.dot}`} />
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">
          {label}
        </span>
      </div>
      <div className={`text-2xl font-bold tabular-nums ${t.text}`}>
        {count}
      </div>
    </div>
  );
}

function ActionTile({
  onClick,
  icon,
  title,
  subtitle,
}: {
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <button
      onClick={onClick}
      className="
        group text-left p-4 rounded-lg
        border border-slate-200 bg-white
        hover:border-amber-400 hover:shadow-md hover:shadow-amber-500/5
        transition-all duration-150
        focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2
      "
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-md bg-slate-100 text-slate-600 group-hover:bg-amber-50 group-hover:text-amber-600 flex items-center justify-center transition-colors">
          {icon}
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-slate-900 text-sm mb-0.5">
            {title}
          </div>
          <div className="text-xs text-slate-500 leading-relaxed">
            {subtitle}
          </div>
        </div>
      </div>
    </button>
  );
}

function Feature({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0 w-9 h-9 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center ring-1 ring-amber-200">
        {icon}
      </div>
      <div className="min-w-0">
        <h4 className="font-semibold text-slate-900 text-sm mb-1">{title}</h4>
        <p className="text-xs text-slate-600 leading-relaxed">{body}</p>
      </div>
    </div>
  );
}
