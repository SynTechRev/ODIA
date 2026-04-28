'use client';

/**
 * Documents Page — lists unique documents across all audits in local history.
 *
 * Reads from useAuditHistoryStore (localStorage-persisted) rather than the
 * legacy useDocumentStore, which was populated by the deprecated /ingest
 * and /analyze flows that the current Upload → Run Audit path doesn't use.
 * Each unique SHA-256 hash is one row; click → Results page for the latest
 * audit containing that document.
 */

import React, { useCallback, useMemo, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { useAuditHistoryStore } from '@/lib/stores/audit-history';
import { PullToRefresh } from '@/components/mobile/PullToRefresh';

interface DocumentRow {
  sha256: string;
  filename: string;
  size: number;
  format: string;
  latest_job_id: string;
  latest_generated_at: string;
  audit_count: number;
  total_findings: number;
}

function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(1)} MB`;
}

export default function DocumentsPage() {
  const nav = useAppNavigate();
  const entries = useAuditHistoryStore((s) => s.entries);
  // v2.9.0 B3 — bumping a refresh tick forces useMemo re-evaluation,
  // gives the user visible feedback that the pull was honored even
  // though the audit-history store is in-memory (no backend roundtrip).
  const [, setRefreshTick] = useState(0);
  const handleRefresh = useCallback(async () => {
    setRefreshTick((n) => n + 1);
  }, []);

  const rows = useMemo(() => {
    const bySha = new Map<string, DocumentRow>();
    for (const entry of entries) {
      for (const doc of entry.results.document_manifest ?? []) {
        const existing = bySha.get(doc.sha256);
        if (!existing) {
          bySha.set(doc.sha256, {
            sha256: doc.sha256,
            filename: doc.filename,
            size: doc.size,
            format: doc.format,
            latest_job_id: entry.job_id,
            latest_generated_at: entry.results.generated_at,
            audit_count: 1,
            total_findings: doc.finding_count,
          });
        } else {
          existing.audit_count += 1;
          existing.total_findings += doc.finding_count;
          if (
            new Date(entry.results.generated_at) >
            new Date(existing.latest_generated_at)
          ) {
            existing.latest_job_id = entry.job_id;
            existing.latest_generated_at = entry.results.generated_at;
          }
        }
      }
    }
    return [...bySha.values()].sort(
      (a, b) =>
        new Date(b.latest_generated_at).getTime() -
        new Date(a.latest_generated_at).getTime(),
    );
  }, [entries]);

  if (rows.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No documents analyzed yet
            </h3>
            <p className="text-gray-600 mb-6">
              Upload and audit documents to see them here. Documents are indexed
              by SHA-256 across all local audit history.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PullToRefresh onRefresh={handleRefresh}>
      <div className="space-y-4">
        {/* v2.9.1 — page hero with marble mineral texture */}
        <section className="page-hero-documents p-6 mb-6 hud-brackets">
          <h1 className="text-2xl font-semibold" style={{ color: 'var(--smoke-50)' }}>
            Documents
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--smoke-300)' }}>
            Unique documents across all local audits ({rows.length} total). Click
            a row to open the most recent audit containing that document.
          </p>
        </section>
        <div className="space-y-2">
          {rows.map((r) => (
            <AppLink
              key={r.sha256}
              href={`/results?job_id=${r.latest_job_id}`}
              className="block hud-panel hud-panel-dense p-4 transition-colors"
            >
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <p className="font-medium text-gray-900 text-sm truncate">
                    {r.filename}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatBytes(r.size)}
                    &nbsp;·&nbsp;
                    <span className="uppercase">{r.format}</span>
                    &nbsp;·&nbsp;
                    {r.audit_count} audit{r.audit_count === 1 ? '' : 's'}
                    &nbsp;·&nbsp;
                    {r.total_findings} total findings
                  </p>
                  <p className="text-[10px] text-gray-400 mt-0.5 font-mono truncate">
                    sha256: {r.sha256}
                  </p>
                </div>
                <div className="text-xs text-gray-500 flex-shrink-0">
                  last audit {r.latest_generated_at.slice(0, 10)}
                </div>
              </div>
            </AppLink>
          ))}
        </div>
      </div>
      </PullToRefresh>
    </DashboardLayout>
  );
}
