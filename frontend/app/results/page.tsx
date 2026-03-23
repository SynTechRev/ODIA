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

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { TemporalTimeline } from '@/components/timeline/TemporalTimeline';
import { CCOPSScorecard } from '@/components/compliance/CCOPSScorecard';
import { getAPIClient } from '@/lib/api/client';
import type { AuditFinding, AuditResults, TimelineEvent } from '@/lib/types/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SEVERITY_STYLES: Record<string, { badge: string; border: string; icon: string }> = {
  critical: { badge: 'bg-red-100 text-red-800', border: 'border-l-red-500', icon: '🔴' },
  high:     { badge: 'bg-orange-100 text-orange-800', border: 'border-l-orange-500', icon: '🟠' },
  medium:   { badge: 'bg-yellow-100 text-yellow-800', border: 'border-l-yellow-500', icon: '🟡' },
  low:      { badge: 'bg-blue-100 text-blue-700', border: 'border-l-blue-400', icon: '🔵' },
};

function SeverityBadge({ severity }: { severity: string }) {
  const styles = SEVERITY_STYLES[severity] ?? {
    badge: 'bg-gray-100 text-gray-700',
    border: '',
    icon: '⚪',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${styles.badge}`}>
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
      className={`bg-white rounded-lg border border-gray-200 border-l-4 ${styles.border} shadow-sm`}
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
        <div className="border-t border-gray-100 px-4 pb-4 pt-3 space-y-3 bg-gray-50 rounded-b-lg">
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
              <pre className="text-xs bg-white border border-gray-200 rounded p-3 overflow-auto max-h-40 text-gray-600">
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

  // Fetch results on mount
  useEffect(() => {
    if (!jobId) {
      setError('No job ID provided. Return to Upload and run an audit.');
      setLoading(false);
      return;
    }

    const fetchResults = async () => {
      try {
        const response = await client.getAuditResults(jobId);
        if (response.results) {
          setResults(response.results);
        } else {
          setError(`Job is not complete yet (status: ${response.status}). Please wait and refresh.`);
        }
      } catch {
        setError('Failed to load audit results. Check that the server is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
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

  if (error || !results) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <div className="text-5xl mb-4">⚠️</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Unable to load results</h3>
            <p className="text-gray-600 mb-6">{error ?? 'No results found.'}</p>
            <Link
              href="/upload"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Back to Upload
            </Link>
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
      <div className="space-y-6">
        {/* Severity summary banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {(
            [
              { key: 'critical', label: 'Critical', color: 'text-red-600', bg: 'bg-red-50' },
              { key: 'high', label: 'High', color: 'text-orange-600', bg: 'bg-orange-50' },
              { key: 'medium', label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-50' },
              { key: 'low', label: 'Low', color: 'text-blue-600', bg: 'bg-blue-50' },
            ] as const
          ).map(({ key, label, color, bg }) => (
            <button
              key={key}
              onClick={() => setFilterSeverity(filterSeverity === key ? 'all' : key)}
              className={`rounded-lg p-4 text-center border-2 transition-colors ${
                filterSeverity === key ? 'border-current' : 'border-transparent'
              } ${bg}`}
            >
              <div className={`text-3xl font-bold ${color}`}>{sev[key]}</div>
              <div className={`text-sm font-medium ${color}`}>{label}</div>
            </button>
          ))}
        </div>

        {/* Meta + export */}
        <Card variant="bordered">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="text-sm text-gray-600">
              <span className="font-medium text-gray-900">{results.document_count}</span> documents
              &nbsp;·&nbsp;
              <span className="font-medium text-gray-900">{results.finding_count}</span> total findings
              &nbsp;·&nbsp;
              {results.generated_at?.slice(0, 10)}
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
                    className="text-sm text-blue-600 hover:text-blue-800"
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
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
