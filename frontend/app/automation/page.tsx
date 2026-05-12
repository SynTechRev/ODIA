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
import { HeroMetricTile, type HeroMetricTone } from '@/components/hero/HeroMetricTile';
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

interface N8nHealth {
  online: boolean;
  checking: boolean;
  base_url: string;
  api_key_configured: boolean;
}

/**
 * v2.7.3 D8 — polls /api/v1/automation/health to gate the "Open n8n
 * Editor" button. Without this gate, clicking the button when the
 * container is down lands the user on ERR_CONNECTION_REFUSED with
 * no explanation.
 */
function useN8nHealth(): N8nHealth {
  const [state, setState] = useState<N8nHealth>({
    online: false,
    checking: true,
    base_url: 'http://localhost:5678',
    api_key_configured: false,
  });

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      try {
        const r = await fetch(
          `${getAPIClient().baseURL}/api/v1/automation/health`,
          { cache: 'no-store' },
        );
        if (!r.ok) throw new Error(`${r.status}`);
        const data = await r.json();
        if (!cancelled) {
          setState({
            online: !!data.n8n_online,
            checking: false,
            base_url: data.n8n_base_url || 'http://localhost:5678',
            api_key_configured: !!data.api_key_configured,
          });
        }
      } catch {
        if (!cancelled) {
          setState((s) => ({ ...s, online: false, checking: false }));
        }
      }
    }

    tick();
    const iv = setInterval(tick, 10_000);
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
  const n8nHealth = useN8nHealth();
  const events = useExecutionLog();
  const [workflows] = useState<WorkflowSummary[]>(WORKFLOW_ROSTER);
  // v2.7.4 W1 — last manual-trigger result, rendered inline above the panel.
  const [triggerNotice, setTriggerNotice] = useState<TriggerNotification | null>(null);
  const [triggerBusy, setTriggerBusy] = useState<string | null>(null);
  // v2.10.x — keep the most recent RAIA report viewable across sessions.
  // Hydrated from localStorage on mount; updated whenever Run RAIA Synthesis
  // succeeds. Opening the modal pulls from this state.
  const [lastRaiaReport, setLastRaiaReport] = useState<RaiaReport | null>(null);
  const [raiaModalOpen, setRaiaModalOpen] = useState(false);

  useEffect(() => {
    setLastRaiaReport(loadLastRaiaReport());
  }, []);

  const handleTrigger = async (
    label: string,
    fn: () => Promise<TriggerNotification>,
  ) => {
    setTriggerBusy(label);
    setTriggerNotice(null);
    try {
      const note = await fn();
      setTriggerNotice(note);
      if (note.report) {
        setLastRaiaReport(note.report);
      }
    } finally {
      setTriggerBusy(null);
    }
  };

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
        {/* v2.9.2 — canonical hero pattern with gold-flux + violet flow accents */}
        <section className="page-hero-automation hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-violet-500/15 blur-3xl pointer-events-none" aria-hidden />
          <div className="relative z-10">
            <div className="hud-label-accent hud-flow mb-3">
              [ AUTOMATION · n8n INTEGRATION ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Orchestration at machine speed.
            </h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              n8n drives the audit pipeline — scraping, ingestion, severity routing,
              MAS generation, and R.A.I.A. synthesis — while O.D.I.A. does the analysis.
              Every execution is recorded in the provenance chain.
            </p>

            {/* v2.9.2 — webhook health surfaced through the canonical
                HeroMetricTile (flow tone for "configured", medium for
                "not configured"). Active workflows reads in signal-green
                so it pops as live state, not configuration state. */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <WebhookMetric
                label="Tier 1 webhook"
                state={webhookTileState(health, 'tier1')}
              />
              <WebhookMetric
                label="Tier 2 webhook"
                state={webhookTileState(health, 'tier2')}
              />
              <WebhookMetric
                label="Webhook token"
                state={webhookTileState(health, 'token')}
              />
              <HeroMetricTile
                label="Active workflows"
                value={`${activeCount} / ${workflows.length}`}
                tone="signal"
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
            {/* v2.7.3 D8 — gate the editor button on container health */}
            <div className="flex items-center gap-2">
              <N8nHealthPill health={n8nHealth} />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openN8nEditor(n8nHealth.base_url)}
                disabled={!n8nHealth.online}
                title={
                  n8nHealth.checking
                    ? 'Checking n8n status…'
                    : n8nHealth.online
                      ? `Open ${n8nHealth.base_url}`
                      : 'n8n container is offline — bring it up with docker compose'
                }
              >
                {n8nHealth.checking
                  ? 'Checking n8n…'
                  : n8nHealth.online
                    ? 'Open n8n Editor →'
                    : 'n8n Editor (container offline)'}
              </Button>
            </div>
          </div>

          {!n8nHealth.online && !n8nHealth.checking && (
            <N8nOfflineHelp baseUrl={n8nHealth.base_url} />
          )}

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
          {triggerNotice && (
            <TriggerNoticeBanner
              notice={triggerNotice}
              onDismiss={() => setTriggerNotice(null)}
              onViewReport={
                triggerNotice.report
                  ? () => setRaiaModalOpen(true)
                  : undefined
              }
            />
          )}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <TriggerTile
              title="Run RAIA Synthesis"
              subtitle="Cross-jurisdictional R.A.I.A. pass across all configured jurisdictions."
              busy={triggerBusy === 'RAIA'}
              onClick={() =>
                handleTrigger('RAIA', triggerRaiaSynthesis)
              }
              footer={
                lastRaiaReport ? (
                  <button
                    type="button"
                    className="hud-label text-[11px] text-cyan-300 hover:text-amber-300"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRaiaModalOpen(true);
                    }}
                  >
                    VIEW LAST REPORT →
                  </button>
                ) : undefined
              }
            />
            <TriggerTile
              title="Check CPRA Deadlines"
              subtitle="Query CPRA requests closing within 72h."
              busy={triggerBusy === 'CPRA'}
              onClick={() =>
                handleTrigger('CPRA', triggerCpraDeadlines)
              }
            />
            <TriggerTile
              title="Export Provenance Chain"
              subtitle="Generate litigation-grade chain-of-custody DOCX (requires n8n)."
              busy={triggerBusy === 'PROV'}
              onClick={() =>
                handleTrigger('PROV', triggerProvenanceExport)
              }
            />
            <TriggerTile
              title="Seed Example Jurisdictions"
              subtitle="Copy bundled example_city_a/b/c into the user-writable config dir so RAIA Synthesis has something to run against."
              busy={triggerBusy === 'SEED'}
              onClick={() =>
                handleTrigger('SEED', triggerSeedJurisdictions)
              }
            />
          </div>
        </Card>

      </div>

      {raiaModalOpen && lastRaiaReport && (
        <RaiaReportModal
          report={lastRaiaReport}
          onClose={() => setRaiaModalOpen(false)}
        />
      )}
    </DashboardLayout>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

type HealthTileState = 'ready' | 'offline' | 'not_configured';

/**
 * v2.7.3 V5 — tri-state tile. 'offline' (red) means the n8n webhook
 * surface returned an error. 'not_configured' (amber) means it
 * returned 404 because ODIA_WEBHOOK_TOKEN is unset — expected on a
 * fresh install without n8n. 'ready' (cyan) is the happy path.
 */
function webhookTileState(
  health: WebhookHealth,
  which: 'tier1' | 'tier2' | 'token',
): HealthTileState {
  if (health.status === 'unavailable') return 'not_configured';
  if (which === 'tier1') return health.tier1_ready ? 'ready' : 'offline';
  if (which === 'tier2') return health.tier2_ready ? 'ready' : 'offline';
  return health.webhook_token_configured ? 'ready' : 'not_configured';
}

/**
 * v2.9.2 — webhook-state → HeroMetricTile mapper. Keeps the tri-state
 * vocabulary (ready / offline / not_configured) but renders through
 * the canonical tile so Automation reads as part of the same family
 * as Anomalies, Results, etc.
 */
function WebhookMetric({
  label,
  state,
}: {
  label: string;
  state: HealthTileState;
}) {
  const tone: HeroMetricTone =
    state === 'ready' ? 'flow' : state === 'offline' ? 'critical' : 'medium';
  const value =
    state === 'ready' ? 'READY' : state === 'offline' ? 'OFFLINE' : 'NOT CONFIGURED';
  return <HeroMetricTile label={label} value={value} tone={tone} />;
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
  busy = false,
  footer,
}: {
  title: string;
  subtitle: string;
  onClick: () => void;
  busy?: boolean;
  footer?: React.ReactNode;
}) {
  return (
    <div
      className={`
        hud-panel hud-panel-flow hud-panel-dense p-4 text-left
        transition-transform hover:-translate-y-[1px]
        ${busy ? 'opacity-60 cursor-wait translate-y-0' : ''}
      `}
    >
      <button
        type="button"
        onClick={onClick}
        disabled={busy}
        className="block w-full text-left disabled:cursor-wait"
      >
        <div className="font-display text-sm font-semibold text-slate-100 mb-1">
          {title}
        </div>
        <div className="text-xs text-slate-400 leading-relaxed">
          {subtitle}
        </div>
        <div
          className={`mt-3 hud-label-accent hud-flow ${
            busy ? 'animate-odia-breath' : ''
          }`}
        >
          {busy ? 'EXECUTING…' : 'EXECUTE →'}
        </div>
      </button>
      {footer && (
        <div className="mt-2 pt-2 border-t border-slate-800/50">
          {footer}
        </div>
      )}
    </div>
  );
}

/**
 * v2.7.4 W1 — inline notification rendered above the Manual Triggers
 * grid after a button has been clicked. We keep this in-page rather
 * than introducing a global toast library; the surface is small,
 * dismissible, and reads at the same scan-line as the buttons it
 * describes.
 */
function TriggerNoticeBanner({
  notice,
  onDismiss,
  onViewReport,
}: {
  notice: TriggerNotification;
  onDismiss: () => void;
  onViewReport?: () => void;
}) {
  const toneClass =
    notice.level === 'success'
      ? 'hud-sev-healthy'
      : notice.level === 'warn'
        ? 'hud-sev-medium'
        : notice.level === 'error'
          ? 'hud-sev-critical'
          : 'hud-sev-info';
  return (
    <div className="hud-panel hud-panel-dense p-3 mb-3 flex items-start gap-3">
      <span className={`hud-sev ${toneClass} mt-0.5 shrink-0`}>
        {notice.level}
      </span>
      <div className="flex-1 min-w-0">
        <div className="font-display text-sm font-semibold text-slate-100">
          {notice.title}
        </div>
        {notice.detail && (
          <div className="text-xs text-slate-400 mt-1 leading-relaxed break-words">
            {notice.detail}
          </div>
        )}
      </div>
      {onViewReport && (
        <button
          type="button"
          className="hud-label text-xs px-2 py-1 text-cyan-300 hover:text-amber-300 shrink-0"
          onClick={onViewReport}
          aria-label="View report"
        >
          view report →
        </button>
      )}
      <button
        type="button"
        className="hud-label text-xs px-2 py-1 hover:text-amber-300 shrink-0"
        onClick={onDismiss}
        aria-label="Dismiss notification"
      >
        dismiss
      </button>
    </div>
  );
}

/**
 * v2.10.x — RAIA Synthesis report viewer.
 *
 * The trigger response carries `body.markdown` (rendered server-side
 * via `render_markdown_template(result)`).  Pre-v2.10.x the frontend
 * dropped that field on the floor, leaving users with only a toast.
 * This modal renders the markdown verbatim (monospace, scrollable)
 * with download + copy-to-clipboard affordances so the report can
 * leave the app for evidence packets.
 */
function RaiaReportModal({
  report,
  onClose,
}: {
  report: RaiaReport;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const handleDownload = () => {
    const blob = new Blob([report.markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `raia_synthesis_${report.synthesisId}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopy = async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(report.markdown);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }
    } catch {
      /* clipboard blocked */
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="raia-report-title"
    >
      <div
        className="hud-panel hud-panel-flow w-full max-w-4xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 p-4 border-b border-slate-800">
          <div className="min-w-0">
            <div className="hud-label-accent hud-flow mb-1">
              [ RAIA SYNTHESIS REPORT ]
            </div>
            <h2
              id="raia-report-title"
              className="font-display text-lg font-semibold text-slate-100 truncate"
            >
              {report.jurisdictions.length} jurisdiction(s) · {report.patternCount} pattern(s)
            </h2>
            <div className="text-xs text-slate-400 mt-1 font-mono truncate">
              {report.synthesisId} · {new Date(report.generatedAt).toLocaleString()}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              className="hud-label text-xs px-2 py-1 text-cyan-300 hover:text-amber-300"
              onClick={handleCopy}
            >
              {copied ? 'copied ✓' : 'copy'}
            </button>
            <button
              type="button"
              className="hud-label text-xs px-2 py-1 text-cyan-300 hover:text-amber-300"
              onClick={handleDownload}
            >
              download .md
            </button>
            <button
              type="button"
              className="hud-label text-xs px-2 py-1 hover:text-amber-300"
              onClick={onClose}
              aria-label="Close report"
            >
              close ✕
            </button>
          </div>
        </div>

        <div className="hud-terminal flex-1 overflow-y-auto p-4 m-3 mt-3">
          <pre className="text-xs text-slate-200 leading-relaxed whitespace-pre-wrap font-mono">
            {report.markdown}
          </pre>
        </div>
      </div>
    </div>
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

function openN8nEditor(baseUrl?: string) {
  // Priority: live n8n_base_url from /health → NEXT_PUBLIC_N8N_URL →
  // localhost. The health-endpoint value wins because it reflects how
  // the backend is configured right now, not what was baked into the
  // build.
  const url =
    baseUrl ||
    process.env.NEXT_PUBLIC_N8N_URL ||
    'http://localhost:5678';
  if (typeof window !== 'undefined') window.open(url, '_blank');
}

// ---------------------------------------------------------------------------
// v2.7.3 D8 — n8n offline UX
// ---------------------------------------------------------------------------

function N8nHealthPill({ health }: { health: N8nHealth }) {
  if (health.checking) {
    return (
      <span className="hud-sev hud-sev-info animate-odia-breath">
        checking
      </span>
    );
  }
  if (health.online) {
    return <span className="hud-sev hud-sev-healthy">n8n online</span>;
  }
  return <span className="hud-sev hud-sev-medium">n8n offline</span>;
}

function N8nOfflineHelp({ baseUrl }: { baseUrl: string }) {
  const commands = [
    'docker compose -f docker-compose.yml -f docker-compose.n8n.yml up -d n8n',
    'docker compose -f docker-compose.yml -f docker-compose.n8n.yml logs -f n8n',
    `curl -sf ${baseUrl}/healthz`,
  ];
  return (
    <div className="hud-panel hud-panel-dense p-4 mb-4">
      <div className="hud-label-accent hud-flow mb-2">
        [ n8n container is offline ]
      </div>
      <p className="hud-subtext text-sm mb-3">
        The n8n automation container is not responding at{' '}
        <code className="hud-flow">{baseUrl}</code>. Bring it up locally
        with one of the commands below, or reach out to whoever manages
        the shared automation host.
      </p>
      <div className="space-y-2">
        {commands.map((cmd) => (
          <N8nCommandLine key={cmd} cmd={cmd} />
        ))}
      </div>
    </div>
  );
}

function N8nCommandLine({ cmd }: { cmd: string }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(cmd);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }
    } catch {
      /* clipboard blocked — silently ignore */
    }
  };
  return (
    <div className="hud-terminal flex items-center gap-2 px-3 py-2">
      <code className="flex-1 text-xs text-cyan-200 font-mono truncate">
        $ {cmd}
      </code>
      <button
        type="button"
        className="hud-label text-xs px-2 py-1 hover:text-amber-300"
        onClick={handleCopy}
        aria-label={`Copy ${cmd}`}
      >
        {copied ? 'copied ✓' : 'copy'}
      </button>
    </div>
  );
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

// ---------------------------------------------------------------------------
// v2.7.4 W1 — Manual Trigger handlers
//
// Each button in the "Manual Triggers" panel invokes one of these. They
// hit ODIA-native endpoints under /api/v1/triggers/* (added in v2.7.4)
// rather than the n8n proxy, so the buttons work even when the n8n
// container is offline (the default for fresh installs).
// ---------------------------------------------------------------------------

export type TriggerLevel = 'info' | 'success' | 'warn' | 'error';

export interface TriggerNotification {
  level: TriggerLevel;
  title: string;
  detail?: string;
  /**
   * Optional viewable payload — if present, the banner renders an
   * extra "View report →" action that opens a modal.  Used by RAIA
   * Synthesis so the markdown report from the trigger response is
   * not silently dropped on the floor.
   */
  report?: RaiaReport;
}

export interface RaiaReport {
  synthesisId: string;
  jurisdictions: string[];
  patternCount: number;
  generatedAt: string;        // ISO
  markdown: string;
  raw: Record<string, unknown>;
}

const RAIA_REPORT_STORAGE_KEY = 'odia.lastRaiaReport';

function loadLastRaiaReport(): RaiaReport | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(RAIA_REPORT_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as RaiaReport;
  } catch {
    return null;
  }
}

function saveLastRaiaReport(report: RaiaReport): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(RAIA_REPORT_STORAGE_KEY, JSON.stringify(report));
  } catch {
    /* quota exceeded — non-fatal */
  }
}

async function triggerCpraDeadlines(): Promise<TriggerNotification> {
  try {
    const r = await fetch(
      `${getAPIClient().baseURL}/api/v1/triggers/cpra-deadlines/72h`,
      { cache: 'no-store' },
    );
    if (!r.ok) {
      return {
        level: 'error',
        title: 'CPRA deadlines',
        detail: `HTTP ${r.status}`,
      };
    }
    const body = await r.json();
    const count = body?.count ?? 0;
    return {
      level: count > 0 ? 'warn' : 'success',
      title: `CPRA deadlines (72h): ${count} request(s)`,
      detail:
        count === 0
          ? 'No requests in the next 72 hours.'
          : (body.items as { jurisdiction_id: string; statutory_deadline: string }[])
              .slice(0, 3)
              .map((it) => `${it.jurisdiction_id} · ${it.statutory_deadline}`)
              .join(' / '),
    };
  } catch (err) {
    return {
      level: 'error',
      title: 'CPRA deadlines',
      detail: 'Network error — backend unreachable.',
    };
  }
}

async function triggerRaiaSynthesis(): Promise<TriggerNotification> {
  try {
    const r = await fetch(
      `${getAPIClient().baseURL}/api/v1/triggers/raia-synthesize-all`,
      { method: 'POST', cache: 'no-store' },
    );
    if (!r.ok) {
      return {
        level: 'error',
        title: 'RAIA synthesis',
        detail: `HTTP ${r.status}`,
      };
    }
    const body = await r.json();
    if (body?.status === 'no_jurisdictions') {
      return {
        level: 'warn',
        title: 'RAIA synthesis: no jurisdictions',
        detail: body.message,
      };
    }
    const result = body?.result ?? {};
    const jurisdictionCount = result?.jurisdictions?.length ?? 0;
    const patternCount = result?.patterns?.length ?? 0;
    const synthesisId = result?.synthesis_id ?? '(none)';
    const markdown: string = body?.markdown ?? '';

    let report: RaiaReport | undefined;
    if (markdown) {
      report = {
        synthesisId,
        jurisdictions: Array.isArray(body?.jurisdictions) ? body.jurisdictions : [],
        patternCount,
        generatedAt: new Date().toISOString(),
        markdown,
        raw: result,
      };
      saveLastRaiaReport(report);
    }

    return {
      level: 'success',
      title: `RAIA synthesis: ${jurisdictionCount} jurisdiction(s), ${patternCount} pattern(s)`,
      detail: `Synthesis ID: ${synthesisId}`,
      report,
    };
  } catch (err) {
    return {
      level: 'error',
      title: 'RAIA synthesis',
      detail: 'Network error — backend unreachable.',
    };
  }
}

async function triggerSeedJurisdictions(): Promise<TriggerNotification> {
  // v2.7.6 X2 — copy bundled example jurisdictions into the user-writable
  // dir so the RAIA Synthesis trigger has something to load. Idempotent;
  // skips entries already present in the target.
  try {
    const result = await getAPIClient().seedJurisdictions(false);
    if (result.status === 'no_bundle') {
      return {
        level: 'error',
        title: 'Seed jurisdictions: no bundle found',
        detail: result.message ?? 'Reinstall the desktop app.',
      };
    }
    const copied = result.copied.length;
    const skipped = result.skipped.length;
    if (copied === 0 && skipped > 0) {
      return {
        level: 'success',
        title: `Already seeded: ${skipped} jurisdiction(s)`,
        detail: result.target ? `Target: ${result.target}` : '',
      };
    }
    return {
      level: 'success',
      title: `Seeded ${copied} jurisdiction(s)${skipped ? ` · ${skipped} already present` : ''}`,
      detail: result.target
        ? `Target: ${result.target}. RAIA Synthesis can now run.`
        : 'RAIA Synthesis can now run.',
    };
  } catch {
    return {
      level: 'error',
      title: 'Seed jurisdictions',
      detail: 'Network error — backend unreachable.',
    };
  }
}

async function triggerProvenanceExport(): Promise<TriggerNotification> {
  try {
    const r = await fetch(
      `${getAPIClient().baseURL}/api/v1/triggers/provenance-chain-export`,
      { method: 'POST', cache: 'no-store' },
    );
    if (r.status === 501) {
      const body = await r.json().catch(() => ({}));
      return {
        level: 'warn',
        title: 'Provenance Chain Export: not available',
        detail: body?.detail ?? 'Requires the n8n container (workflow WF-014).',
      };
    }
    if (!r.ok) {
      return {
        level: 'error',
        title: 'Provenance Chain Export',
        detail: `HTTP ${r.status}`,
      };
    }
    const body = await r.json();
    return {
      level: 'success',
      title: 'Provenance Chain Export: triggered',
      detail: JSON.stringify(body),
    };
  } catch (err) {
    return {
      level: 'error',
      title: 'Provenance Chain Export',
      detail: 'Network error — backend unreachable.',
    };
  }
}
