/**
 * Dashboard — main landing view.
 *
 * Sections:
 *   1. Hero — gem-cut crystallized panel + dual gold/neon-emerald edges
 *   2. Severity strip (live; backed by /api/v1/dashboard/summary)
 *   3. System Status × Analysis Summary cards
 *   4. Jurisdiction × Detectors cards
 *   5. Quick Actions tiles
 *   6. Platform Capabilities (static copy)
 *
 * v2.7.7 Y4 — severity strip now polls the dashboard-summary endpoint
 * instead of reading the dead Zustand store. Hero rewritten to use the
 * .gem-panel-faceted utility (extra mid-side cuts so the silhouette
 * reads as cut quartz). All tiles + features use the gemstone palette.
 */

'use client';

import React, { useEffect, useState } from 'react';
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
  OraculusMarkIcon,
  CheckCircleIcon,
} from '@/components/base/Icons';
import { getAPIClient, type DashboardSummary } from '@/lib/api/client';

const POLL_MS = 30_000;

const EMPTY_SUMMARY: DashboardSummary = {
  available: false,
  analyses: 0,
  documents: 0,
  findings: 0,
  by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
  avg_severity_score: 0,
  last_audit_at: null,
};

function useDashboardSummary(): DashboardSummary {
  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY);
  useEffect(() => {
    let cancelled = false;
    const client = getAPIClient();
    const load = async () => {
      try {
        const data = await client.getDashboardSummary();
        if (!cancelled) setSummary(data);
      } catch {
        /* keep empty */
      }
    };
    load();
    const id = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);
  return summary;
}

export default function Home() {
  const nav = useAppNavigate();
  const summary = useDashboardSummary();
  const sev = summary.by_severity;
  const hasAnomalyData =
    sev.critical + sev.high + sev.medium + sev.low > 0;

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* =============================================================== */}
        {/* 1 · Hero — v2.8.0 C1: malachite texture + crystallized facets   */}
        {/* =============================================================== */}
        {/* The dashboard hero is the platform's primary work surface; per  */}
        {/* BRAND.md §3.2 it gets the malachite texture so it reads as      */}
        {/* polished mineral. Existing gem-panel-faceted geometry stays —   */}
        {/* the texture composes underneath via the gem-hero-malachite      */}
        {/* background-image layer + gradient overlay (preserves text       */}
        {/* contrast).                                                       */}
        <section className="gem-panel gem-panel-faceted gem-hero-malachite relative overflow-hidden">
          <div className="gem-ribbon-top" aria-hidden="true" />
          {/* Emerald bloom upper-right — gem facet catching light */}
          <div
            aria-hidden="true"
            className="absolute -top-32 -right-20 w-96 h-96 rounded-full pointer-events-none blur-3xl"
            style={{ background: 'rgba(0, 255, 157, 0.18)' }}
          />
          {/* Gold bloom lower-left — antique vein depth */}
          <div
            aria-hidden="true"
            className="absolute -bottom-32 -left-32 w-80 h-80 rounded-full pointer-events-none blur-3xl"
            style={{ background: 'rgba(216, 177, 60, 0.12)' }}
          />
          {/* Crystalline diamond-grid hint */}
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-[0.06] pointer-events-none"
            style={{
              backgroundImage:
                'linear-gradient(45deg, var(--gold-300) 1px, transparent 1px), linear-gradient(-45deg, var(--neon-emerald) 1px, transparent 1px)',
              backgroundSize: '32px 32px, 32px 32px',
            }}
          />

          <div className="relative p-8 md:p-10">
            {/* v2.9.2 C2 — canonical bracket-label tag (cyan-bright = live surface) */}
            <div className="hud-label-accent hud-cyan-bright mb-3 relative z-10">
              [ FORENSIC AUDIT PLATFORM · v3.0.2 · LOCAL ]
            </div>

            {/* Brand badge — gem-edged, dual gold/emerald */}
            <div
              className="inline-flex items-center gap-2 px-3 py-1 mb-4 text-[11px] font-medium uppercase tracking-[0.22em] gem-edge"
              style={{
                color: 'var(--smoke-100)',
                background: 'rgba(14, 14, 20, 0.7)',
              }}
            >
              <OraculusMarkIcon size={12} />
              <span
                className="bg-clip-text text-transparent"
                style={{
                  backgroundImage:
                    'linear-gradient(90deg, var(--gold-200), var(--neon-emerald), var(--gold-300))',
                }}
              >
                O.D.I.A. · v3.0.2
              </span>
              <span
                aria-hidden="true"
                className="w-1.5 h-1.5 rounded-full animate-gem-breath"
                style={{
                  background: 'var(--neon-emerald)',
                  boxShadow: '0 0 8px var(--neon-emerald)',
                }}
              />
            </div>

            {/* Heading — gold-vein → neon-emerald gradient */}
            <h1
              className="text-3xl md:text-4xl font-bold tracking-tight mb-3 bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  'linear-gradient(135deg, var(--smoke-100) 0%, var(--gold-200) 35%, var(--neon-emerald) 70%, var(--smoke-100) 100%)',
                filter: 'drop-shadow(0 0 28px rgba(0, 255, 157, 0.20))',
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
              <Button
                variant="accent"
                size="lg"
                onClick={() => nav('/upload')}
                icon={<UploadIcon size={16} />}
              >
                Upload Document
              </Button>
              <Button
                variant="outline"
                size="lg"
                onClick={() => nav('/analysis')}
                icon={<AnalysisIcon size={16} />}
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

          <div className="gem-ribbon-bottom" aria-hidden="true" />
        </section>

        {/* =============================================================== */}
        {/* 2 · Severity strip — live, backed by /api/v1/dashboard/summary  */}
        {/* =============================================================== */}
        {hasAnomalyData && (
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <SeverityTile label="Critical" count={sev.critical} tone="critical" />
            <SeverityTile label="High"     count={sev.high}     tone="high" />
            <SeverityTile label="Medium"   count={sev.medium}   tone="medium" />
            <SeverityTile label="Low"      count={sev.low}      tone="low" />
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
              title="9-Detector Analysis Engine"
              body="Fiscal, constitutional, surveillance, procurement, signature, scope, governance, administrative, and grant-compliance integrity detection — all executed locally."
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
              icon={<OraculusMarkIcon size={18} />}
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
        style={{
          background: 'var(--neon-emerald)',
          boxShadow: '0 0 4px var(--neon-emerald)',
        }}
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
  // v2.7.7 Y4 — gem-cut tile, gold-edged with severity-color crystal accent.
  const toneStyle: Record<typeof tone, { color: string; ring: string }> = {
    critical: { color: 'var(--severity-critical)', ring: 'rgba(244, 63, 94, 0.45)' },
    high:     { color: 'var(--severity-high)',     ring: 'rgba(249, 115, 22, 0.40)' },
    medium:   { color: 'var(--gold-300)',          ring: 'rgba(236, 200, 112, 0.50)' },
    low:      { color: 'var(--neon-emerald)',      ring: 'rgba(0, 255, 157, 0.50)' },
  };
  const t = toneStyle[tone];
  return (
    <div
      className="gem-panel gem-panel-dense p-4 transition-all"
      style={{
        boxShadow:
          `0 0 0 1px var(--gem-edge-gold), inset 0 0 0 1px ${t.ring}, 0 0 24px -10px ${t.ring}`,
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span
          className="w-2 h-2 rounded-full"
          style={{ background: t.color, boxShadow: `0 0 8px ${t.color}` }}
        />
        <span className="hud-metric-label">{label}</span>
      </div>
      <div
        className="hud-metric tabular-nums"
        style={{ color: t.color }}
      >
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
      className="group text-left p-4 transition-all gem-edge focus:outline-none"
      style={{
        background: 'rgba(14, 14, 20, 0.65)',
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center transition-all gem-edge"
          style={{
            background: 'rgba(216, 177, 60, 0.10)',
            color: 'var(--gold-300)',
          }}
        >
          {icon}
        </div>
        <div className="min-w-0">
          <div
            className="font-semibold text-sm mb-0.5 transition-colors group-hover:text-[var(--neon-emerald)]"
            style={{ color: 'var(--smoke-100)' }}
          >
            {title}
          </div>
          <div
            className="text-xs leading-relaxed"
            style={{ color: 'var(--smoke-500)' }}
          >
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
      <div
        className="flex-shrink-0 w-9 h-9 flex items-center justify-center gem-edge"
        style={{
          background: 'rgba(31, 232, 143, 0.10)',
          color: 'var(--neon-emerald)',
        }}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <h4
          className="font-semibold text-sm mb-1"
          style={{ color: 'var(--smoke-100)' }}
        >
          {title}
        </h4>
        <p
          className="text-xs leading-relaxed"
          style={{ color: 'var(--smoke-300)' }}
        >
          {body}
        </p>
      </div>
    </div>
  );
}
