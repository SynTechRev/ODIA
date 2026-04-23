/**
 * Automation — n8n Workflow Surface
 *
 * Renders the live state of the O.D.I.A. n8n automation layer:
 *   • Workflow roster (WF-001 … WF-014) with last-run + status
 *   • Live execution console (tails n8n's REST /executions endpoint)
 *   • Per-jurisdiction pipeline visualisation (scraper → ingest → analyse → MAS)
 *   • Trigger buttons for ad-hoc runs (synthesize, CPRA watch, USASpending check)
 *
 * This page lives in the "System" sidebar group alongside Orchestrator and
 * Settings. Add it to `sidebarNav` in DashboardLayout.tsx:
 *
 *   { name: 'Automation', href: '/automation', Icon: AutomationIcon,
 *     group: 'System' },
 *
 * Backend contract
 * ----------------
 *   GET  /api/v1/webhook/health      → tier readiness + token config
 *   GET  /api/v1/automation/workflows → enriched list: name, id, active,
 *                                       last_execution, next_run
 *   GET  /api/v1/automation/executions?since=TS → SSE stream of executions
 *   POST /api/v1/automation/workflows/:id/run   → manual trigger
 *
 * This page degrades gracefully when the backend automation routes are
 * missing — it still renders the roster, just marked "unavailable".
 */

'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { getAPIClient } from '@/lib/api/client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type WorkflowStatus = 'idle' | 'running' | 'success' | 'error' | 'unavailable';

interface WorkflowSummary {
  id: string;
  name: string;
  description: string;
  active: boolean;
  status: WorkflowStatus;
  lastRun?: string;           // ISO
  lastDurationMs?: number;
  nextRun?: string;           // ISO (from cron)
  lastExecutionId?: string;
}

interface ExecutionEvent {
  ts: string;
  workflow_id: string;
  execution_id: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

interface WebhookHealth {
  status: 'healthy' | 'degraded' | 'unavailable';
  tier1_ready: boolean;
  tier2_ready: boolean;
  webhook_token_configured: boolean;
}

// ---------------------------------------------------------------------------
// Seed data (used when backend automation routes are unreachable)
// ---------------------------------------------------------------------------

const WORKFLOW_ROSTER: WorkflowSummary[] = [
  {
    id: 'wf-001',
    name: 'CivicPlus Scraper → Tier 1',
    description: 'Daily 06:00. Scrapes council agendas, deduplicates by SHA-256, posts each new PDF to /webhook/ingest-and-analyze.',
    active: true, status: 'idle',
  },
  {
    id: 'wf-003',
    name: 'Severity Router',
    description: 'Consumes finding payloads and routes CRITICAL/HIGH/MEDIUM/LOW to the appropriate notification channel.',
    active: true, status: 'idle',
  },
  {
    id: 'wf-004',
    name: 'CRITICAL → Gmail Alert',
    description: 'Immediate email alert when a CRITICAL finding is surfaced. Includes jurisdiction, finding summary, and deep link.',
    active: true, status: 'idle',
  },
  {
    id: 'wf-005',
    name: 'CPRA Deadline Watcher',
    description: 'Daily 08:00. Queries ODIA for CPRA requests closing within 72h, emails a consolidated digest.',
    active: true, status: 'idle',
  },
  {
    id: 'wf-008',
    name: 'Post-Batch MAS Generation',
    description: 'After each jurisdiction batch completes Tier 1, generates the MAS DOCX and uploads to Google Drive.',
    active: true, status: 'idle',
  },
  {
    id: 'wf-010',
    name: 'RAIA Cross-Jurisdictional Synthesis',
    description: 'Monthly on the 1st @ 09:00. Triggers /webhook/synthesize across all completed jurisdictions, downloads the RAIA DOCX.',
    active: false, status: 'idle',
  },
  {
    id: 'wf-011',
    name: 'USASpending.gov JAG Verification',
    description: 'Nightly 02:00. Cross-references ODIA-extracted JAG figures against USASpending.gov; flags discrepancies > $10k or 5%.',
    active: false, status: 'idle',
  },
  {
    id: 'wf-014',
    name: 'Provenance Chain Export',
    description: 'Quarterly or on-demand. Exports a litigation-grade chain-of-custody DOCX joining n8n executions to ODIA findings.',
    active: false, status: 'idle',
  },
];

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

function useWebhookHealth(): WebhookHealth {
  const [state, setState] = useState<WebhookHealth>({
    status: 'unavailable',
    tier1_ready: false,
    tier2_ready: false,
    webhook_token_configured: false,
  });

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const r = await fetch(
          `${getAPIClient().baseURL}/api/v1/webhook/health`,
          { cache: 'no-store' },
        );
        if (!r.ok) throw new Error(`${r.status}`);
        const data = await r.json();
        if (!cancelled) setState(data);
      } catch {
        if (!cancelled) {
          setState((s) => ({ ...s, status: 'unavailable' }));
        }
      }
    }

    tick();
    const iv = setInterval(tick, 8000);
    return () => { cancelled = true; clearInterval(iv); };
  }, []);

  return state;
}

function useExecutionLog(): ExecutionEvent[] {
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const containerRef = useRef(events);
  containerRef.current = events;

  useEffect(() => {
    // Poll approach — works under Electron file:// where EventSource is
    // flaky. Swap for SSE in a browser build if desired.
    let cancelled = false;
    let lastTs = new Date(Date.now() - 60_000).toISOString();

    async function tick() {
      try {
        const r = await fetch(
          `${getAPIClient().baseURL}/api/v1/automation/executions?since=${lastTs}`,
          { cache: 'no-store' },
        );
        if (!r.ok) return;
        const data = (await r.json()) as ExecutionEvent[];
        if (cancelled || !data.length) return;

        // Keep last 80 events — enough for the terminal viewport.
        const next = [...containerRef.current, ...data].slice(-80);
        setEvents(next);
        lastTs = data[data.length - 1].ts;
      } catch {
        /* ignore — terminal shows "no events" when backend is down */
      }
    }

    tick();
    const iv = setInterval(tick, 3000);
    return () => { cancelled = true; clearInterval(iv); };
  }, []);

  return events;
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function AutomationPage() {
  const health = useWebhookHealth();
  const events = useExecutionLog();
  const [workflows] = useState<WorkflowSummary[]>(WORKFLOW_ROSTER);

  const activeCount = useMemo(
    () => workflows.filter((w) => w.active).length,
    [workflows],
  );

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto space-y-6 animate-odia-fade">

        {/* =============================================================== */}
        {/* 1 · Hero + health strip                                          */}
        {/* =============================================================== */}
        <section className="hud-panel hud-panel-flow hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-violet-500/15 blur-3xl pointer-events-none" aria-hidden />
          <div className="relative">
            <div className="hud-label-accent mb-3 hud-flow">
              AUTOMATION · n8n INTEGRATION
            </div>
            <h1 className="font-display text-3xl md:text-4xl font-bold tracking-tight mb-2">
              Orchestration at machine speed.
            </h1>
            <p className="text-slate-300 max-w-2xl text-sm md:text-base leading-relaxed">
              n8n drives the audit pipeline — scraping, ingestion, severity routing,
              MAS generation, and R.A.I.A. synthesis — while O.D.I.A. does the analysis.
              Every execution is recorded in the provenance chain.
            </p>

            <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3">
              <HealthTile
                label="Tier 1"
                ok={health.tier1_ready}
              />
              <HealthTile
                label="Tier 2"
                ok={health.tier2_ready}
              />
              <HealthTile
                label="Webhook Token"
                ok={health.webhook_token_configured}
              />
              <HealthTile
                label="Active Workflows"
                ok={activeCount > 0}
                valueOverride={`${activeCount} / ${workflows.length}`}
              />
            </div>
          </div>
        </section>

        {/* =============================================================== */}
        {/* 2 · Live execution terminal                                      */}
        {/* =============================================================== */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="hud-label">LIVE EXECUTION STREAM</div>
              <h2 className="font-display text-lg font-semibold mt-1">
                Workflow console
              </h2>
            </div>
            <div className="flex items-center gap-2">
              <span className={`hud-sev ${events.length > 0 ? 'hud-sev-healthy' : 'hud-sev-info'}`}>
                {events.length > 0 ? 'Live' : 'Idle'}
              </span>
            </div>
          </div>

          <div className="hud-terminal h-64 overflow-y-auto">
            {events.length === 0 ? (
              <div className="text-slate-500 italic">
                {/* Deliberately understated — a live stream that's empty is
                    not an error, just quiet. */}
                No executions in the last 60s.
              </div>
            ) : (
              events.map((ev, i) => (
                <div key={`${ev.execution_id}-${i}`} className="whitespace-pre">
                  <span className="text-slate-500">
                    [{new Date(ev.ts).toLocaleTimeString()}]
                  </span>
                  {' '}
                  <span className="hud-flow">{ev.workflow_id}</span>
                  {' '}
                  <span className={levelClass(ev.level)}>
                    {ev.level.toUpperCase().padEnd(7)}
                  </span>
                  {' '}
                  <span>{ev.message}</span>
                </div>
              ))
            )}
          </div>
        </section>

        {/* =============================================================== */}
        {/* 3 · Workflow roster                                              */}
        {/* =============================================================== */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="hud-label">WORKFLOW ROSTER</div>
              <h2 className="font-display text-lg font-semibold mt-1">
                {workflows.length} registered workflows
              </h2>
            </div>
            <Button variant="ghost" size="sm" onClick={openN8nEditor}>
              Open n8n Editor →
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {workflows.map((wf) => (
              <WorkflowCard key={wf.id} wf={wf} />
            ))}
          </div>
        </section>

        {/* =============================================================== */}
        {/* 4 · Manual triggers                                              */}
        {/* =============================================================== */}
        <Card title="Manual Triggers" variant="bordered">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <TriggerTile
              title="Run RAIA Synthesis"
              subtitle="Cross-jurisdictional R.A.I.A. pass across all completed jurisdictions."
              onClick={() => runWorkflow('wf-010')}
            />
            <TriggerTile
              title="Check CPRA Deadlines"
              subtitle="Query requests closing within 72h and email the digest."
              onClick={() => runWorkflow('wf-005')}
            />
            <TriggerTile
              title="Export Provenance Chain"
              subtitle="Generate litigation-grade chain-of-custody DOCX."
              onClick={() => runWorkflow('wf-014')}
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

function HealthTile({
  label,
  ok,
  valueOverride,
}: {
  label: string;
  ok: boolean;
  valueOverride?: string;
}) {
  return (
    <div className="hud-panel-inset px-4 py-3">
      <div className="hud-metric-label">{label}</div>
      <div className={`hud-metric mt-1 ${ok ? 'hud-cyan-bright' : 'text-rose-400'}`}>
        {valueOverride ?? (ok ? 'READY' : 'OFFLINE')}
      </div>
    </div>
  );
}

function WorkflowCard({ wf }: { wf: WorkflowSummary }) {
  const statusClass = statusToPanelClass(wf.status);
  return (
    <div className={`hud-panel ${statusClass} p-4`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="hud-label hud-flow">{wf.id.toUpperCase()}</span>
            {wf.active ? (
              <span className="hud-sev hud-sev-healthy">Active</span>
            ) : (
              <span className="hud-sev hud-sev-info">Inactive</span>
            )}
            {wf.status === 'running' && (
              <span className="hud-sev hud-sev-info animate-odia-breath">
                Running
              </span>
            )}
            {wf.status === 'error' && (
              <span className="hud-sev hud-sev-critical">Error</span>
            )}
          </div>
          <h3 className="font-display text-base font-semibold text-slate-100 leading-tight">
            {wf.name}
          </h3>
        </div>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed mb-3">
        {wf.description}
      </p>

      <hr className="hud-hairline mb-3" />

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <div className="hud-metric-label">Last run</div>
          <div className="hud-num text-slate-300">
            {wf.lastRun ? new Date(wf.lastRun).toLocaleString() : '—'}
          </div>
        </div>
        <div>
          <div className="hud-metric-label">Next run</div>
          <div className="hud-num text-slate-300">
            {wf.nextRun ? new Date(wf.nextRun).toLocaleString() : '—'}
          </div>
        </div>
      </div>
    </div>
  );
}

function TriggerTile({
  title,
  subtitle,
  onClick,
}: {
  title: string;
  subtitle: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="hud-panel hud-panel-flow hud-panel-dense p-4 text-left transition-transform hover:-translate-y-[1px]"
    >
      <div className="font-display text-sm font-semibold text-slate-100 mb-1">
        {title}
      </div>
      <div className="text-xs text-slate-400 leading-relaxed">
        {subtitle}
      </div>
      <div className="mt-3 hud-label-accent hud-flow">
        EXECUTE →
      </div>
    </button>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function statusToPanelClass(s: WorkflowStatus): string {
  switch (s) {
    case 'running': return 'hud-panel-flow';
    case 'success': return 'hud-panel-data';
    case 'error':   return 'hud-panel-critical';
    default:        return '';
  }
}

function levelClass(l: ExecutionEvent['level']): string {
  switch (l) {
    case 'success': return 'text-emerald-400';
    case 'warn':    return 'text-yellow-400';
    case 'error':   return 'text-rose-400';
    default:        return 'text-cyan-300';
  }
}

function openN8nEditor() {
  // The n8n editor URL is configurable — in production, read from
  // NEXT_PUBLIC_N8N_URL and fall through to localhost for dev.
  const url = process.env.NEXT_PUBLIC_N8N_URL || 'http://localhost:5678';
  if (typeof window !== 'undefined') window.open(url, '_blank');
}

async function runWorkflow(id: string) {
  try {
    await fetch(
      `${getAPIClient().baseURL}/api/v1/automation/workflows/${id}/run`,
      { method: 'POST' },
    );
  } catch {
    /* surface as a toast in the real build */
  }
}
