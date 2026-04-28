'use client';

/**
 * Results Page — displays audit findings with plain-language explanations.
 *
 * Reads job_id from ?job_id=… URL param and fetches results from
 * GET /api/v1/audit/results/{job_id}.
 *
 * Features:
 *  - Severity summary banner (critical / high / medium / low counts)
 *  - Filter by severity, detector type, or document
 *  - Finding cards with plain-language summary + expandable technical detail
 *  - Download buttons: Markdown, HTML, Evidence Packet (ZIP)
 */

import React, { Suspense, useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { AppLink } from '@/lib/navigation';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { TemporalTimeline } from '@/components/timeline/TemporalTimeline';
import { CCOPSScorecard } from '@/components/compliance/CCOPSScorecard';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';
import { getAPIClient } from '@/lib/api/client';
import { useAuditHistoryStore } from '@/lib/stores/audit-history';
import type { AuditFinding, AuditResults, TimelineEvent } from '@/lib/types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// v2.9.1 — HUD severity primitives (no emoji per BRAND.md §9; severity-stripe for left edge)
const SEVERITY_STYLES: Record<string, { badge: string; border: string }> = {
  critical: { badge: 'hud-sev hud-sev-critical', border: 'severity-stripe s-critical' },
  high:     { badge: 'hud-sev hud-sev-high',     border: 'severity-stripe s-high' },
  medium:   { badge: 'hud-sev hud-sev-medium',   border: 'severity-stripe s-medium' },
  low:      { badge: 'hud-sev hud-sev-low',      border: 'severity-stripe s-low' },
};

function SeverityBadge({ severity }: { severity: string }) {
  const styles = SEVERITY_STYLES[severity] ?? { badge: 'hud-sev', border: '' };
  return (
    <span className={`${styles.badge} uppercase`}>
      {severity}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Finding card
// ---------------------------------------------------------------------------

function FindingCard({ finding, index }: { finding: AuditFinding; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const styles = SEVERITY_STYLES[finding.severity] ?? SEVERITY_STYLES.low;

  return (
    <div
      className={`hud-panel hud-panel-dense ${styles.border} relative pl-5`}
    >
      {/* Card header */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="text-xs font-mono text-gray-400">F-{String(index).padStart(3, '0')}</span>
              <SeverityBadge severity={finding.severity} />
              <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-mono text-gray-600">
                {finding.layer}
              </span>
              <span className="text-xs text-gray-500">
                {finding.document_id}
              </span>
            </div>
            <p className="font-medium text-gray-900 text-sm">{finding.issue}</p>
          </div>
          <button
            onClick={() => setExpanded((v) => !v)}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>

        {/* Plain-language summary (always visible) */}
        {finding.plain_summary && (
          <p className="mt-2 text-sm text-gray-700 leading-relaxed">
            {finding.plain_summary}
          </p>
        )}
      </div>

      {/* Expandable detail */}
      {expanded && (
        <div
          className="border-t px-4 pb-4 pt-3 space-y-3"
          style={{
            borderColor: 'rgba(45, 45, 44, 0.6)',
            background: 'rgba(5, 5, 5, 0.5)',
          }}
        >
          {finding.plain_impact && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Why it matters
              </p>
              <p className="text-sm text-gray-700">{finding.plain_impact}</p>
            </div>
          )}
          {finding.plain_action && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Recommended action
              </p>
              <p className="text-sm text-gray-700">{finding.plain_action}</p>
            </div>
          )}
          {Object.keys(finding.details ?? {}).length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                Technical evidence
              </p>
              <pre className="text-xs hud-terminal max-h-40 overflow-auto">
                {JSON.stringify(finding.details, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Download helper
// ---------------------------------------------------------------------------

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Sharing helpers
// ---------------------------------------------------------------------------

async function shareOrCopy(title: string, text: string, url?: string): Promise<'shared' | 'copied' | 'failed'> {
  if (typeof navigator === 'undefined') return 'failed';
  if (navigator.share) {
    try {
      await navigator.share({ title, text, url: url ?? window.location.href });
      return 'shared';
    } catch {
      // User cancelled or not allowed — fall through to clipboard
    }
  }
  try {
    await navigator.clipboard.writeText(text);
    return 'copied';
  } catch {
    return 'failed';
  }
}

// ---------------------------------------------------------------------------
// Build timeline events from findings + document manifest
// ---------------------------------------------------------------------------

function buildTimelineEvents(results: AuditResults): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  // Add document ingestion events from manifest
  results.document_manifest?.forEach((doc, i) => {
    events.push({
      id: `doc-${doc.document_id}-${i}`,
      date: results.generated_at,
      label: `Ingested: ${doc.filename}`,
      description: `${doc.finding_count} finding${doc.finding_count !== 1 ? 's' : ''} detected. SHA-256: ${doc.sha256.slice(0, 12)}…`,
      category: 'document',
      document_id: doc.document_id,
    });
  });

  // Add critical/high findings as events (with synthetic offset for display order)
  results.findings
    .filter((f) => f.severity === 'critical' || f.severity === 'high')
    .forEach((f, i) => {
      // Use generated_at as base date; offset by index for visual spread
      const base = new Date(results.generated_at);
      base.setMinutes(base.getMinutes() - (results.findings.length - i) * 2);
      events.push({
        id: `finding-${f.id}-${i}`,
        date: base.toISOString(),
        label: f.issue,
        description: f.plain_summary ?? f.issue,
        category: 'finding',
        severity: f.severity,
        document_id: f.document_id,
      });
    });

  // Add a completion milestone
  events.push({
    id: 'audit-complete',
    date: results.generated_at,
    label: 'Audit complete',
    description: `${results.document_count} documents, ${results.finding_count} findings`,
    category: 'milestone',
  });

  return events;
}

function buildCriticalSummary(results: AuditResults): string {
  const critical = results.findings.filter(
    (f) => f.severity === 'critical' || f.severity === 'high',
  );
  const lines = [
    `O.D.I.A. Audit Summary`,
    `${results.document_count} documents · ${results.finding_count} findings`,
    `Critical: ${results.severity_summary.critical} | High: ${results.severity_summary.high}`,
    '',
    ...critical.slice(0, 5).map((f) => `• [${f.severity.toUpperCase()}] ${f.issue}`),
  ];
  if (critical.length > 5) lines.push(`…and ${critical.length - 5} more`);
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center py-24"><div className="text-gray-600">Loading…</div></div>}>
      <ResultsPageInner />
    </Suspense>
  );
}

function ResultsPageInner() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get('job_id');

  const [results, setResults] = useState<AuditResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [shareStatus, setShareStatus] = useState<'idle' | 'shared' | 'copied' | 'failed'>('idle');
  const [activeTab, setActiveTab] = useState<'findings' | 'timeline' | 'compliance'>('findings');

  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterDetector, setFilterDetector] = useState<string>('all');
  const [filterDocument, setFilterDocument] = useState<string>('all');

  const client = getAPIClient();
  const historyEntries = useAuditHistoryStore((s) => s.entries);
  const addAuditToHistory = useAuditHistoryStore((s) => s.addAudit);
  const getAuditFromHistory = useAuditHistoryStore((s) => s.getAudit);

  // v2.9.0 B3 — extracted fetch so PullToRefresh can re-invoke it.
  // Pull-to-refresh BYPASSES the cache (the user is asking for fresh
  // data). Mount-time fetch keeps the cache-first behaviour.
  const fetchFromBackend = useCallback(async () => {
    if (!jobId) return;
    try {
      const response = await client.getAuditResults(jobId);
      if (response.results) {
        setResults(response.results);
        setError(null);
        addAuditToHistory(jobId, response.results);
      } else {
        setError(`Job is not complete yet (status: ${response.status}). Please wait and refresh.`);
      }
    } catch {
      setError('Failed to load audit results. Check that the server is running.');
    }
  }, [jobId, client, addAuditToHistory]);

  // Fetch results on mount — cache-first, then backend fallback.
  // When no jobId is present we render a history list view instead of an error.
  useEffect(() => {
    if (!jobId) {
      setLoading(false);
      return;
    }

    const cached = getAuditFromHistory(jobId);
    if (cached) {
      setResults(cached.results);
      setLoading(false);
      return;
    }

    (async () => {
      await fetchFromBackend();
      setLoading(false);
    })();
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Download handlers
  const handleDownload = useCallback(
    async (format: string) => {
      if (!jobId) return;
      setDownloading(format);
      try {
        const blob = await client.exportAudit(jobId, format);
        const ext = format === 'markdown' ? 'md' : format;
        triggerDownload(blob, `audit_report_${jobId.slice(0, 8)}.${ext}`);
      } catch {
        setError(`Failed to download ${format} report.`);
      } finally {
        setDownloading(null);
      }
    },
    [client, jobId],
  );

  const handleEvidencePacket = useCallback(async () => {
    if (!jobId) return;
    setDownloading('zip');
    try {
      const blob = await client.downloadEvidencePacket(jobId);
      triggerDownload(blob, `evidence_packet_${jobId.slice(0, 8)}.zip`);
    } catch {
      setError('Failed to download evidence packet.');
    } finally {
      setDownloading(null);
    }
  }, [client, jobId]);

  const handleShare = useCallback(async () => {
    if (!results) return;
    const summary = buildCriticalSummary(results);
    const status = await shareOrCopy('O.D.I.A. Audit Report', summary);
    setShareStatus(status);
    if (status !== 'failed') setTimeout(() => setShareStatus('idle'), 3000);
  }, [results]);

  // -------------------------------------------------------------------------
  // Loading / error states
  // -------------------------------------------------------------------------

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-24">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading audit results…</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // No jobId in URL → render history list (or empty state if no past audits).
  if (!jobId) {
    if (historyEntries.length === 0) {
      return (
        <DashboardLayout>
          <Card variant="bordered">
            <div className="text-center py-12">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No audit history yet</h3>
              <p className="text-gray-600 mb-6">
                Run an audit to see its report here. Past audits are saved locally on this machine.
              </p>
              <AppLink
                href="/upload"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Go to Upload
              </AppLink>
            </div>
          </Card>
        </DashboardLayout>
      );
    }
    return (
      <DashboardLayout>
        <div className="space-y-4">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">Audit history</h2>
            <p className="text-gray-600 text-sm">
              Past audits from this machine. Click a row to reopen its report.
            </p>
          </div>
          <div className="space-y-2">
            {historyEntries.map((entry) => {
              const r = entry.results;
              const sev = r.severity_summary;
              const firstDoc = r.document_manifest?.[0]?.filename ?? 'Unnamed';
              const more = r.document_count > 1 ? ` +${r.document_count - 1} more` : '';
              return (
                <AppLink
                  key={entry.job_id}
                  href={`/results?job_id=${entry.job_id}`}
                  className="block hud-panel hud-panel-dense p-4 transition-colors"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 text-sm truncate">
                        {firstDoc}{more}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {r.generated_at?.slice(0, 16).replace('T', ' ')}
                        &nbsp;·&nbsp;
                        {r.finding_count} finding{r.finding_count === 1 ? '' : 's'}
                        &nbsp;·&nbsp;
                        <span className="font-mono">{entry.job_id.slice(0, 8)}</span>
                      </p>
                    </div>
                    <div className="flex gap-1 text-xs flex-shrink-0">
                      {sev.critical > 0 && (
                        <span className="hud-sev hud-sev-critical">C {sev.critical}</span>
                      )}
                      {sev.high > 0 && (
                        <span className="hud-sev hud-sev-high">H {sev.high}</span>
                      )}
                      {sev.medium > 0 && (
                        <span className="hud-sev hud-sev-medium">M {sev.medium}</span>
                      )}
                      {sev.low > 0 && (
                        <span className="hud-sev hud-sev-low">L {sev.low}</span>
                      )}
                    </div>
                  </div>
                </AppLink>
              );
            })}
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !results) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <div className="text-5xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to load results</h3>
            <p className="text-gray-600 mb-6">{error ?? 'No results found.'}</p>
            <AppLink
              href="/upload"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Upload
            </AppLink>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  // -------------------------------------------------------------------------
  // Filter findings
  // -------------------------------------------------------------------------

  const detectors = [...new Set(results.findings.map((f) => f.layer))].sort();
  const documents = [...new Set(results.findings.map((f) => f.document_id))].sort();

  const filtered = results.findings.filter((f) => {
    if (filterSeverity !== 'all' && f.severity !== filterSeverity) return false;
    if (filterDetector !== 'all' && f.layer !== filterDetector) return false;
    if (filterDocument !== 'all' && f.document_id !== filterDocument) return false;
    return true;
  });

  const sev = results.severity_summary;

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <DashboardLayout>
      <PullToRefresh onRefresh={fetchFromBackend}>
      <div className="space-y-6">
        {/* v2.9.1 — page hero with malachite mineral texture */}
        <section className="page-hero-results p-6 mb-6 hud-brackets">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <h1 className="text-2xl font-semibold" style={{ color: 'var(--smoke-50)' }}>
              Audit Results
            </h1>
            <div className="text-sm" style={{ color: 'var(--smoke-300)' }}>
              <span className="font-medium" style={{ color: 'var(--smoke-100)' }}>
                {results.document_count}
              </span>{' '}
              docs ·{' '}
              <span className="font-medium" style={{ color: 'var(--smoke-100)' }}>
                {results.finding_count}
              </span>{' '}
              findings · {results.generated_at?.slice(0, 10)}
            </div>
          </div>
        {/* v2.7.3 V3: severity summary banner — HUD primitives match
            the Dashboard's SeverityTile (D6). The pre-v2.7.3 version
            rendered pale bg-red-50/orange-50/yellow-50/blue-50 on
            slate-950 which was effectively invisible. */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(
            [
              { key: 'critical', label: 'Critical', tone: 'text-rose-400', dot: 'bg-rose-500' },
              { key: 'high', label: 'High', tone: 'text-orange-400', dot: 'bg-orange-500' },
              { key: 'medium', label: 'Medium', tone: 'text-yellow-400', dot: 'bg-yellow-500' },
              { key: 'low', label: 'Low', tone: 'text-blue-400', dot: 'bg-blue-500' },
            ] as const
          ).map(({ key, label, tone, dot }) => {
            const active = filterSeverity === key;
            return (
              <button
                key={key}
                onClick={() => setFilterSeverity(active ? 'all' : key)}
                className={`
                  hud-panel hud-panel-inset p-4 text-center transition-colors
                  ${active ? 'ring-2 ring-current' : ''}
                `}
              >
                <div className="flex items-center justify-center gap-2 mb-2">
                  <span className={`w-2 h-2 rounded-full ${dot}`} />
                  <span className="hud-metric-label">{label}</span>
                </div>
                <div className={`hud-metric tabular-nums ${tone}`}>
                  {sev[key]}
                </div>
              </button>
            );
          })}
        </div>
        </section>

        {/* Export controls (meta moved into the hero) */}
        <Card variant="bordered">
          <div className="flex flex-wrap items-center justify-end gap-4">
            <div className="text-xs" style={{ color: 'var(--smoke-400)' }}>
              Export this audit:
            </div>

            <div className="flex flex-wrap gap-2">
              {(['markdown', 'html'] as const).map((fmt) => (
                <button
                  key={fmt}
                  onClick={() => handleDownload(fmt)}
                  disabled={!!downloading}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                >
                  {downloading === fmt ? '…' : `↓ ${fmt.toUpperCase()}`}
                </button>
              ))}
              <button
                onClick={handleEvidencePacket}
                disabled={!!downloading}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {downloading === 'zip' ? '…' : '↓ Evidence Packet (ZIP)'}
              </button>
              <button
                onClick={handleShare}
                className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                title="Share critical findings summary"
              >
                {shareStatus === 'shared' ? '✓ Shared' : shareStatus === 'copied' ? '✓ Copied' : shareStatus === 'failed' ? '✗ Failed' : '↗ Share'}
              </button>
            </div>
          </div>
        </Card>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex gap-0 -mb-px" role="tablist">
            {(
              [
                { id: 'findings', label: 'Findings', count: results.finding_count },
                { id: 'timeline', label: 'Timeline', count: null },
                { id: 'compliance', label: 'Compliance', count: null },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  px-4 py-3 text-sm font-medium border-b-2 transition-colors
                  ${activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                {tab.label}
                {tab.count !== null && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-gray-100 rounded-full text-gray-600">
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab panels */}
        {activeTab === 'findings' && (
          <>
            {/* Filters */}
            <Card variant="bordered">
              <div className="flex flex-wrap gap-4 items-center">
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Severity:</label>
                  <select
                    value={filterSeverity}
                    onChange={(e) => setFilterSeverity(e.target.value)}
                    className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-gray-700">Detector:</label>
                  <select
                    value={filterDetector}
                    onChange={(e) => setFilterDetector(e.target.value)}
                    className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All</option>
                    {detectors.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>

                {documents.length > 1 && (
                  <div className="flex items-center gap-2">
                    <label className="text-sm font-medium text-gray-700">Document:</label>
                    <select
                      value={filterDocument}
                      onChange={(e) => setFilterDocument(e.target.value)}
                      className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All</option>
                      {documents.map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="ml-auto text-sm text-gray-500">
                  {filtered.length} finding{filtered.length !== 1 ? 's' : ''} shown
                </div>

                {(filterSeverity !== 'all' || filterDetector !== 'all' || filterDocument !== 'all') && (
                  <button
                    onClick={() => { setFilterSeverity('all'); setFilterDetector('all'); setFilterDocument('all'); }}
                    className="text-sm transition-colors"
                    style={{ color: 'var(--signal-400)' }}
                  >
                    Clear filters
                  </button>
                )}
              </div>
            </Card>

            {filtered.length === 0 ? (
              <Card variant="bordered">
                <div className="text-center py-10 text-gray-500">
                  No findings match the current filters.
                </div>
              </Card>
            ) : (
              <div className="space-y-3">
                {filtered.map((finding, i) => (
                  <FindingCard
                    key={`${finding.id}-${finding.document_id}-${i}`}
                    finding={finding}
                    index={i + 1}
                  />
                ))}
              </div>
            )}
          </>
        )}

        {activeTab === 'timeline' && (
          <Card variant="bordered">
            <TemporalTimeline events={buildTimelineEvents(results)} />
          </Card>
        )}

        {activeTab === 'compliance' && (
          <Card variant="bordered">
            <CCOPSScorecard findings={results.findings} />
          </Card>
        )}

        {error && (
          <div className="hud-panel hud-panel-critical p-3 text-sm">
            {error}
          </div>
        )}
      </div>
      </PullToRefresh>
    </DashboardLayout>
  );
}
