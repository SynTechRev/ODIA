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
  OctopusMarkIcon,
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
        {/* 1 · Hero — v2.7.6 X5 POC: gemstone (smoke / gold / emerald)     */}
        {/* =============================================================== */}
        {/* Cut-gemstone aesthetic, replacing the v2.7.5 W4 purple POC:     */}
        {/*   a) smoke base — vertical gradient near-black → smoke-900       */}
        {/*      → smoke-800 (the polished obsidian body)                    */}
        {/*   b) gold hairline border + brighter inner stroke (the "cut      */}
        {/*      edge" of the gem — antique gold, not chrome)                */}
        {/*   c) emerald bloom upper-right (the gem facet catching light)    */}
        {/*   d) gold-vein gradient text + emerald CTA + gold-outline CTA   */}
        <section
          className="
            relative overflow-hidden
            rounded-2xl
          "
          style={{
            background:
              'linear-gradient(160deg, var(--smoke-950) 0%, var(--smoke-900) 45%, var(--smoke-800) 75%, var(--smoke-900) 100%)',
            boxShadow:
              '0 0 0 1px var(--gem-edge-gold), 0 0 0 2px rgba(0,0,0,0.45) inset, 0 0 60px -16px var(--gem-edge-emerald)',
          }}
        >
          {/* Inner gold stroke — the second cut of the gem edge */}
          <div
            aria-hidden="true"
            className="absolute inset-[2px] rounded-[14px] pointer-events-none"
            style={{ boxShadow: 'inset 0 0 0 1px rgba(232, 201, 113, 0.18)' }}
          />
          {/* Top gold hairline ribbon — animated catch-light */}
          <div
            aria-hidden="true"
            className="absolute inset-x-0 top-0 h-px"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, var(--gold-400) 30%, var(--gold-300) 50%, var(--gold-400) 70%, transparent 100%)',
            }}
          />
          {/* Emerald bloom upper-right — gem facet */}
          <div
            aria-hidden="true"
            className="absolute -top-32 -right-20 w-96 h-96 rounded-full pointer-events-none blur-3xl"
            style={{ background: 'rgba(16, 185, 129, 0.22)' }}
          />
          {/* Gold bloom lower-left — antique vein depth */}
          <div
            aria-hidden="true"
            className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full pointer-events-none blur-3xl"
            style={{ background: 'rgba(212, 175, 55, 0.10)' }}
          />
          {/* Faceted grid pattern — subtle gemstone facet hint */}
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-[0.04] pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(rgba(232,201,113,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(232,201,113,0.6) 1px, transparent 1px)',
              backgroundSize: '28px 28px',
            }}
          />

          <div className="relative p-8 md:p-10">
            {/* Brand badge — gold ring, smoke fill, emerald accent dot */}
            <div
              className="
                inline-flex items-center gap-2 px-3 py-1 mb-4
                text-[11px] font-medium uppercase tracking-[0.22em]
              "
              style={{
                color: 'var(--smoke-100)',
                background: 'rgba(20, 20, 26, 0.6)',
                boxShadow:
                  '0 0 0 1px var(--gem-edge-gold), 0 0 18px -6px rgba(212, 175, 55, 0.55)',
              }}
            >
              <OctopusMarkIcon size={12} />
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage:
                    'linear-gradient(90deg, var(--gold-300), var(--smoke-100), var(--gold-400))',
                }}
              >
                O.D.I.A. · v2.7.6
              </span>
              <span
                aria-hidden="true"
                className="w-1.5 h-1.5 rounded-full"
                style={{
                  background: 'var(--emerald-300)',
                  boxShadow: '0 0 6px var(--emerald-500)',
                }}
              />
            </div>

            {/* Heading — gold-vein gradient text */}
            <h1
              className="text-3xl md:text-4xl font-bold tracking-tight mb-3 bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  'linear-gradient(135deg, var(--smoke-100) 0%, var(--gold-300) 50%, var(--smoke-200) 100%)',
                filter: 'drop-shadow(0 0 28px rgba(212, 175, 55, 0.18))',
              }}
            >
              Civic accountability,
              <br className="hidden md:block" />
              at forensic resolution.
            </h1>

            <p
              className="max-w-2xl mb-6 text-sm md:text-base leading-relaxed"
              style={{ color: 'var(--smoke-300)' }}
            >
              Ingest legal and government documents. Surface fiscal anomalies,
              constitutional concerns, surveillance outsourcing, and procurement
              irregularities — all locally, all private, all auditable.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              {/* Primary CTA — emerald body, gold inner highlight ring */}
              <Button
                variant="accent"
                size="lg"
                onClick={() => nav('/upload')}
                icon={<UploadIcon size={16} />}
                className="!text-white !border-0"
                style={{
                  background:
                    'linear-gradient(135deg, var(--emerald-500) 0%, var(--emerald-700) 100%)',
                  boxShadow:
                    '0 0 24px -6px rgba(16, 185, 129, 0.55), inset 0 1px 0 rgba(232, 201, 113, 0.35)',
                }}
              >
                Upload Document
              </Button>
              {/* Secondary CTA — gold-outline platinum text */}
              <Button
                variant="ghost"
                size="lg"
                onClick={() => nav('/analysis')}
                icon={<AnalysisIcon size={16} />}
                className="hover:!bg-white/[0.04]"
                style={{
                  color: 'var(--smoke-100)',
                  border: '1px solid var(--gem-edge-gold)',
                  boxShadow: 'inset 0 1px 0 rgba(232, 201, 113, 0.10)',
                }}
              >
                View Analyses
              </Button>
            </div>

            <div
              className="mt-6 flex flex-wrap gap-4 text-xs"
              style={{ color: 'var(--smoke-300)' }}
            >
              <InlineFeature label="100% local processing" />
              <InlineFeature label="SHA-256 provenance" />
              <InlineFeature label="9-detector pipeline" />
              <InlineFeature label="No outbound network" />
            </div>
          </div>

          {/* Bottom gold hairline ribbon — mirror of the top cut */}
          <div
            aria-hidden="true"
            className="absolute inset-x-0 bottom-0 h-px"
            style={{
              background:
                'linear-gradient(90deg, transparent 0%, var(--gold-500) 30%, var(--gold-400) 50%, var(--gold-500) 70%, transparent 100%)',
              opacity: 0.6,
            }}
          />
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
              onClick={() => nav('/upload')}
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
              icon={<OctopusMarkIcon size={18} />}
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
      <span
        className="w-1 h-1 rounded-full"
        style={{ background: 'var(--gold-400)' }}
      />
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
  // v2.7.3 D6: replaced bg-white + ring-red-* + text-red-700 chain
  // (pale-pastel on slate-950, unreadable per post-v2.7.2 screenshots)
  // with the HUD primitive stack shared across Automation and
  // Orchestrator pages.
  const toneClassMap: Record<typeof tone, string> = {
    critical: 'text-rose-400',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    low: 'text-blue-400',
  };
  const dotClassMap: Record<typeof tone, string> = {
    critical: 'bg-rose-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-500',
  };
  return (
    <div className="hud-panel hud-panel-inset p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-2 h-2 rounded-full ${dotClassMap[tone]}`} />
        <span className="hud-metric-label">{label}</span>
      </div>
      <div className={`hud-metric tabular-nums ${toneClassMap[tone]}`}>
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
