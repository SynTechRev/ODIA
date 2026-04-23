/**
 * Orchestrator — Phase 5/8 Multi-Agent Pipeline
 *
 * Renders the live state of the O.D.I.A. orchestration layer:
 *   • Task-graph SVG (6 agents: Ingestion → Analysis → Anomaly →
 *     Synthesis → Database → Interface) with idle/active edge states.
 *   • Agent execution timeline (last N MeshExecutionJob rows, newest
 *     first) — each row shows job_id, type, status pill, agent count,
 *     task count, and ISO timestamps.
 *   • Orchestration dashboard (three live counters: agents online,
 *     tasks queued, tasks completed in last 24h).
 *
 * Backend contract
 * ----------------
 *   GET /api/v1/orchestrator/task-graph   → static {nodes, edges}
 *   GET /api/v1/orchestrator/executions?limit=20
 *                                        → {available, count, items}
 *   GET /api/v1/orchestrator/status      → {agents_online, tasks_queued,
 *                                           tasks_completed_today,
 *                                           available}
 *
 * Graceful degradation: when any endpoint returns 404/500/network error,
 * the affected panel still renders in an "unavailable" state.
 */

'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { getAPIClient } from '@/lib/api/client';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GraphNode {
  id: string;
  label: string;
  x: number;
  y: number;
  phase: string;
}

interface GraphEdge {
  source: string;
  target: string;
}

interface TaskGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface ExecutionRow {
  job_id: string;
  job_type: string;
  status: string;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  agent_count: number;
  task_count: number;
  gcn_validated: boolean;
  governor_approved: boolean;
}

interface OrchestratorStatus {
  agents_online: number;
  tasks_queued: number;
  tasks_completed_today: number;
  available: boolean;
}

// Fallback graph matches the backend static layout — lets the page
// render even when the backend is unreachable so operators still see
// the architecture at a glance.
const FALLBACK_GRAPH: TaskGraph = {
  nodes: [
    { id: 'ingest',    label: 'Ingestion',  x: 80,  y: 200, phase: 'intake'  },
    { id: 'analysis',  label: 'Analysis',   x: 220, y: 120, phase: 'compute' },
    { id: 'anomaly',   label: 'Anomaly',    x: 380, y: 120, phase: 'compute' },
    { id: 'synthesis', label: 'Synthesis',  x: 540, y: 200, phase: 'compute' },
    { id: 'database',  label: 'Database',   x: 680, y: 120, phase: 'persist' },
    { id: 'interface', label: 'Interface',  x: 680, y: 280, phase: 'emit'    },
  ],
  edges: [
    { source: 'ingest',    target: 'analysis' },
    { source: 'analysis',  target: 'anomaly' },
    { source: 'anomaly',   target: 'synthesis' },
    { source: 'synthesis', target: 'database' },
    { source: 'synthesis', target: 'interface' },
    { source: 'database',  target: 'interface' },
  ],
};

const POLL_EXECUTIONS_MS = 8000;
const POLL_STATUS_MS = 10000;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function OrchestratorPage() {
  const [graph, setGraph] = useState<TaskGraph>(FALLBACK_GRAPH);
  const [graphAvailable, setGraphAvailable] = useState(false);
  const [executions, setExecutions] = useState<ExecutionRow[]>([]);
  const [executionsAvailable, setExecutionsAvailable] = useState(false);
  const [status, setStatus] = useState<OrchestratorStatus>({
    agents_online: 6,
    tasks_queued: 0,
    tasks_completed_today: 0,
    available: false,
  });

  const api = useMemo(() => getAPIClient(), []);

  // Task graph — load once (it's static).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${api.baseURL}/api/v1/orchestrator/task-graph`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled && data?.nodes?.length) {
          setGraph({ nodes: data.nodes, edges: data.edges || [] });
          setGraphAvailable(true);
        }
      } catch {
        if (!cancelled) setGraphAvailable(false);
      }
    })();
    return () => { cancelled = true; };
  }, [api.baseURL]);

  // Executions — poll.
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch(
          `${api.baseURL}/api/v1/orchestrator/executions?limit=20`
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled) {
          setExecutions(data?.items || []);
          setExecutionsAvailable(!!data?.available);
        }
      } catch {
        if (!cancelled) setExecutionsAvailable(false);
      }
    };
    load();
    const id = setInterval(load, POLL_EXECUTIONS_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [api.baseURL]);

  // Status — poll.
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const res = await fetch(`${api.baseURL}/api/v1/orchestrator/status`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!cancelled && data) setStatus(data);
      } catch {
        if (!cancelled) {
          setStatus((s) => ({ ...s, available: false }));
        }
      }
    };
    load();
    const id = setInterval(load, POLL_STATUS_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, [api.baseURL]);

  const totalTasks = executions.reduce((a, r) => a + (r.task_count || 0), 0);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* ===== Hero ===== */}
        <section className="hud-panel hud-panel-data hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10">
            <div className="hud-label-accent mb-3 hud-cyan-bright">
              <span>[ PHASE 5 ORCHESTRATOR ]</span>
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Multi-Agent Task Coordination
            </h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              Six specialised agents execute the ODIA analysis pipeline
              deterministically under governor + GCN validation. The
              graph below is the static topology; the timeline and
              counters track live mesh execution jobs.
            </p>
            <div className="grid grid-cols-3 gap-4 mt-6 max-w-2xl">
              <OrchestratorMetric
                label="Agents online"
                value={status.agents_online}
              />
              <OrchestratorMetric
                label="Tasks queued"
                value={status.tasks_queued}
              />
              <OrchestratorMetric
                label="Completed / 24h"
                value={status.tasks_completed_today}
              />
            </div>
          </div>
        </section>

        {/* ===== Task graph ===== */}
        <section className="hud-panel hud-panel-inset p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="hud-label-accent hud-cyan-bright">
                [ TASK GRAPH ]
              </div>
              <h2 className="hud-heading text-lg md:text-xl mt-1">
                Agent Pipeline Topology
              </h2>
            </div>
            <span
              className={`hud-sev ${
                graphAvailable ? 'hud-sev-healthy' : 'hud-sev-info'
              }`}
            >
              {graphAvailable ? 'live' : 'static'}
            </span>
          </div>
          <div className="hud-panel hud-panel-dense p-4 overflow-x-auto">
            <TaskGraphSvg graph={graph} />
          </div>
        </section>

        {/* ===== Execution timeline ===== */}
        <section className="hud-panel hud-panel-inset p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="hud-label-accent hud-cyan-bright">
                [ EXECUTION TIMELINE ]
              </div>
              <h2 className="hud-heading text-lg md:text-xl mt-1">
                Recent Mesh Jobs ({executions.length})
                {totalTasks > 0 && (
                  <span className="hud-subtext ml-2">
                    · {totalTasks} task(s) total
                  </span>
                )}
              </h2>
            </div>
            <span
              className={`hud-sev ${
                executionsAvailable ? 'hud-sev-healthy' : 'hud-sev-info'
              }`}
            >
              {executionsAvailable ? 'live' : 'unavailable'}
            </span>
          </div>
          {executions.length === 0 ? (
            <div className="hud-panel hud-panel-dense p-6 text-center">
              <p className="hud-subtext">
                {executionsAvailable
                  ? 'No mesh execution jobs yet.'
                  : 'Backend /executions endpoint unreachable.'}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {executions.map((e) => (
                <ExecutionRowTile key={e.job_id} row={e} />
              ))}
            </div>
          )}
        </section>
      </div>
    </DashboardLayout>
  );
}

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function OrchestratorMetric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="hud-panel-inset px-4 py-3">
      <div className="hud-metric-label">{label}</div>
      <div className="hud-metric mt-1 hud-cyan-bright">{value}</div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const norm = (status || '').toLowerCase();
  let cls = 'hud-sev-info';
  if (norm === 'completed') cls = 'hud-sev-healthy';
  else if (norm === 'failed' || norm === 'interrupted') cls = 'hud-sev-critical';
  else if (['queued', 'routing', 'executing', 'synthesizing'].includes(norm)) {
    cls = 'hud-sev-medium';
  }
  return <span className={`hud-sev ${cls}`}>{norm || 'unknown'}</span>;
}

function ExecutionRowTile({ row }: { row: ExecutionRow }) {
  const ts = row.completed_at || row.started_at || row.created_at || '';
  return (
    <div className="hud-panel hud-panel-dense p-3 flex items-center gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="hud-label hud-flow">{row.job_id}</span>
          <StatusPill status={row.status} />
          <span className="hud-subtext text-xs">{row.job_type}</span>
        </div>
        <div className="mt-1 flex gap-4 hud-subtext text-xs">
          <span>
            <span className="hud-metric-label">agents</span>{' '}
            <span className="hud-num">{row.agent_count}</span>
          </span>
          <span>
            <span className="hud-metric-label">tasks</span>{' '}
            <span className="hud-num">{row.task_count}</span>
          </span>
          <span>
            <span className="hud-metric-label">gcn</span>{' '}
            <span className={row.gcn_validated ? 'text-emerald-400' : 'text-zinc-500'}>
              {row.gcn_validated ? '✓' : '·'}
            </span>
          </span>
          <span>
            <span className="hud-metric-label">governor</span>{' '}
            <span className={row.governor_approved ? 'text-emerald-400' : 'text-zinc-500'}>
              {row.governor_approved ? '✓' : '·'}
            </span>
          </span>
        </div>
      </div>
      {ts && (
        <div className="hud-num text-xs hud-subtext whitespace-nowrap">
          {formatTs(ts)}
        </div>
      )}
    </div>
  );
}

function TaskGraphSvg({ graph }: { graph: TaskGraph }) {
  const nodeById = useMemo(() => {
    const m = new Map<string, GraphNode>();
    for (const n of graph.nodes) m.set(n.id, n);
    return m;
  }, [graph]);

  return (
    <svg
      viewBox="0 0 800 400"
      className="w-full max-w-4xl mx-auto"
      style={{ height: 'auto' }}
    >
      {/* Edges */}
      {graph.edges.map((e, i) => {
        const src = nodeById.get(e.source);
        const dst = nodeById.get(e.target);
        if (!src || !dst) return null;
        return (
          <line
            key={`${e.source}-${e.target}-${i}`}
            x1={src.x}
            y1={src.y}
            x2={dst.x}
            y2={dst.y}
            stroke="currentColor"
            className="text-cyan-500/40"
            strokeWidth="1.5"
            strokeDasharray="4 4"
          />
        );
      })}
      {/* Nodes */}
      {graph.nodes.map((n) => (
        <g key={n.id}>
          <circle
            cx={n.x}
            cy={n.y}
            r="38"
            fill="rgb(15 23 42 / 0.9)"
            stroke="currentColor"
            className="text-cyan-400"
            strokeWidth="2"
          />
          <text
            x={n.x}
            y={n.y - 2}
            textAnchor="middle"
            fontSize="13"
            fontFamily="ui-monospace, monospace"
            fill="currentColor"
            className="text-cyan-100"
          >
            {n.label}
          </text>
          <text
            x={n.x}
            y={n.y + 14}
            textAnchor="middle"
            fontSize="9"
            fontFamily="ui-monospace, monospace"
            fill="currentColor"
            className="text-cyan-500/70"
          >
            {n.phase}
          </text>
        </g>
      ))}
    </svg>
  );
}

function formatTs(iso: string): string {
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toISOString().slice(11, 19) + 'Z';
  } catch {
    return iso;
  }
}
