'use client';

import React from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { ContraIcon } from '@/components/base/Icons';

// ---------------------------------------------------------------------------
// Pre-seeded commercial entity registry (mirrors DB seed data)
// ---------------------------------------------------------------------------
const SEEDED_ENTITIES = [
  'AT&T Mobility', 'Verizon Wireless', 'T-Mobile USA', 'Comcast / Xfinity',
  'Charter / Spectrum', 'Cox Communications', 'Google / Alphabet', 'Apple Inc.',
  'Microsoft Corporation', 'Amazon / AWS', 'Meta Platforms', 'Axon Enterprise',
  'Flock Safety', 'Motorola Solutions', 'Tyler Technologies', 'Thomson Reuters',
  'LexisNexis', 'Palantir Technologies', 'Cellebrite', 'ShotSpotter / SoundThinking',
  'Vigilant Solutions', 'Fusus', 'Clearview AI', 'JPMorgan Chase', 'Wells Fargo',
  'Bank of America', 'US Bank', 'Citibank', 'Capital One', 'American Express',
  'Discover Financial', 'PayPal',
];

const DETECTORS = [
  { id: 'L-11', name: 'Adhesion Clause', desc: 'One-sided modification rights, no-negotiation clauses' },
  { id: 'L-12', name: 'Liability Waiver', desc: 'Broad indemnification and limitation of liability' },
  { id: 'L-13', name: 'Arbitration Mandate', desc: '§ 1281.96 forced arbitration + class action waiver' },
  { id: 'L-14', name: 'Data Monetization', desc: 'Third-party data sale, behavioral profiling rights' },
  { id: 'L-15', name: 'Surveillance Enablement', desc: 'Location tracking, biometric collection, monitoring' },
  { id: 'L-16', name: 'Auto-Renewal Trap', desc: 'Silent renewal, cancellation barrier patterns' },
  { id: 'L-17', name: 'Unilateral Amendment', desc: 'Terms changeable without user consent or notice' },
  { id: 'L-18', name: 'Jurisdiction Override', desc: 'Foreign venue selection, choice-of-law stripping' },
  { id: 'L-19', name: 'Price Escalation', desc: 'Hidden fee structures, non-transparent billing' },
  { id: 'L-20', name: 'IP Overreach', desc: 'Broad user content / data ownership claims' },
];

// ---------------------------------------------------------------------------

function DetectorBadge({ id, name, desc }: { id: string; name: string; desc: string }) {
  return (
    <div
      className="p-3 gem-edge"
      style={{ background: 'rgba(216, 177, 60, 0.04)' }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span
          className="font-mono text-[10px] px-1.5 py-0.5"
          style={{
            color: 'var(--gold-300)',
            background: 'rgba(216, 177, 60, 0.12)',
            border: '1px solid rgba(216, 177, 60, 0.2)',
          }}
        >
          {id}
        </span>
        <span className="text-sm font-medium" style={{ color: 'var(--smoke-100)' }}>
          {name}
        </span>
      </div>
      <p className="text-xs" style={{ color: 'var(--smoke-400)' }}>{desc}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------

export default function ContraPage() {
  return (
    <DashboardLayout>
      <div className="p-6 md:p-8 space-y-6 max-w-5xl">

        {/* Header */}
        <div>
          <div className="hud-label-accent hud-cyan-bright mb-3">
            [ COMMERCIAL CONTRACT ANALYSIS · C.O.N.T.R.A. ]
          </div>
          <h1
            className="text-2xl font-bold mb-2"
            style={{ color: 'var(--smoke-50)' }}
          >
            C.O.N.T.R.A.
          </h1>
          <p className="text-sm max-w-2xl" style={{ color: 'var(--smoke-300)' }}>
            Commercial Obligation and Non-Transparent Rights Analysis — 10 detectors (L-11–L-20)
            scoring adhesion severity via CASI (Consumer Adhesion Severity Index) across
            five axes: Modification, Liability, Arbitration, Surveillance, and Data.
          </p>
        </div>

        {/* Status tiles */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Detectors', value: '10', sub: 'L-11 through L-20' },
            { label: 'Entities Seeded', value: '32', sub: 'in registry' },
            { label: 'Docs Ingested', value: '0', sub: 'run contra-ingest to populate' },
            { label: 'CASI Scored', value: '0', sub: 'no data yet' },
          ].map(({ label, value, sub }) => (
            <div
              key={label}
              className="p-4 gem-edge"
              style={{ background: 'rgba(14, 14, 20, 0.6)' }}
            >
              <div
                className="text-2xl font-bold font-mono mb-0.5"
                style={{ color: 'var(--gold-200)' }}
              >
                {value}
              </div>
              <div className="text-xs font-medium uppercase tracking-wider mb-0.5" style={{ color: 'var(--smoke-200)' }}>
                {label}
              </div>
              <div className="text-[11px]" style={{ color: 'var(--smoke-500)' }}>{sub}</div>
            </div>
          ))}
        </div>

        {/* Empty state / CLI instruction */}
        <Card
          variant="bordered"
          icon={<ContraIcon size={18} />}
          title="No Commercial Data Ingested"
          subtitle="Run odia contra-ingest to begin analysis"
        >
          <div className="space-y-4">
            <p className="text-sm" style={{ color: 'var(--smoke-300)' }}>
              C.O.N.T.R.A. requires commercial contract PDFs to be ingested via the CLI.
              Point <code className="font-mono text-xs px-1" style={{ color: 'var(--gold-300)' }}>--source</code> at
              any Terms of Service, user agreement, or service contract PDF on your system.
            </p>
            <div
              className="p-4 font-mono text-xs space-y-1 gem-edge overflow-x-auto"
              style={{ background: 'rgba(0,0,0,0.4)', color: 'var(--neon-emerald)' }}
            >
              <div><span style={{ color: 'var(--smoke-500)' }}># Single document</span></div>
              <div>odia contra-ingest --source &quot;path\to\att_tos.pdf&quot; --entity &quot;AT&amp;T Mobility&quot; --doc-type tos --output .\cards\</div>
              <div className="mt-2"><span style={{ color: 'var(--smoke-500)' }}># Batch (run in waves of 3)</span></div>
              <div>odia contra-ingest --source &quot;path\to\chase_agreement.pdf&quot; --entity &quot;JPMorgan Chase&quot; --doc-type cardmember_agreement --output .\cards\</div>
            </div>
            <p className="text-xs" style={{ color: 'var(--smoke-500)' }}>
              Supported doc types: <code className="font-mono" style={{ color: 'var(--gold-400)' }}>tos · eula · msa · cardmember_agreement · privacy_policy · arbitration_agreement</code>
            </p>
          </div>
        </Card>

        {/* Detector registry */}
        <Card
          variant="bordered"
          title="Active Detectors"
          subtitle="L-11–L-20 commercial pattern library"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {DETECTORS.map((d) => (
              <DetectorBadge key={d.id} {...d} />
            ))}
          </div>
        </Card>

        {/* Entity registry */}
        <Card
          variant="bordered"
          title="Entity Registry"
          subtitle={`${SEEDED_ENTITIES.length} pre-seeded entities — fuzzy-match threshold 0.88`}
        >
          <div className="flex flex-wrap gap-2">
            {SEEDED_ENTITIES.map((e) => (
              <span
                key={e}
                className="text-xs px-2 py-1 gem-edge"
                style={{
                  color: 'var(--smoke-200)',
                  background: 'rgba(216, 177, 60, 0.06)',
                }}
              >
                {e}
              </span>
            ))}
          </div>
          <p className="text-xs mt-3" style={{ color: 'var(--smoke-500)' }}>
            Entities not in this list are auto-created on first ingest with a warning.
            Match threshold 0.88 — &quot;AT&amp;T&quot; and &quot;AT&amp;T Mobility&quot; resolve to the same record.
          </p>
        </Card>

      </div>
    </DashboardLayout>
  );
}
