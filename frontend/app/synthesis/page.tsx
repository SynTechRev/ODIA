'use client';

/**
 * Master Audit Synthesis — cross-audit aggregation report.
 *
 * Takes every audit in local history (useAuditHistoryStore) and produces:
 *   - Severity totals across all audits
 *   - Top finding IDs by cross-document prevalence
 *   - Vendor aggregation (findings with `vendor` in details)
 *   - Statute aggregation (findings with `statute` in details)
 *   - Markdown + DOCX exports
 *
 * Purely client-side. No backend endpoint required. The `docx` library is
 * imported dynamically inside the export handler so it doesn't inflate
 * the initial page bundle for users who never export.
 */

import React, { useCallback, useMemo } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { HeroMetricTile } from '@/components/hero/HeroMetricTile';
import { AppLink, useAppNavigate } from '@/lib/navigation';
import { useAuditHistoryStore } from '@/lib/stores/audit-history';
import type { AuditFinding } from '@/lib/types/api';
// Type-only imports from `docx` so we can annotate the DOCX builder's
// intermediate variables. The actual classes are loaded at runtime via
// a dynamic `await import('docx')` inside the export handler — these
// type references are erased at compile time and don't bloat the bundle.
import type {
  Paragraph as DocxParagraph,
  Table as DocxTable,
  TableRow as DocxTableRow,
} from 'docx';

type Severity = 'critical' | 'high' | 'medium' | 'low';

const SEV_ORDER: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

interface FindingGroup {
  id: string;
  issue: string;
  layer: string;
  severity: string;
  document_ids: Set<string>; // distinct AuditFinding.document_id values
  unique_shas: Set<string>;  // v2.9.3 C.1 — distinct SHA-256s (deduped)
  job_ids: Set<string>;
  count: number;             // raw emission count across all audits
}

interface VendorGroup {
  vendor: string;
  count: number;                              // vendor-tagged finding count
  severities: Record<Severity, number>;       // severity histogram of vendor-tagged findings
  document_ids: Set<string>;                  // doc_ids carrying this vendor
  unique_shas: Set<string>;                   // v2.9.3 C.2 — SHAs carrying this vendor
  related_count: number;                      // v2.9.3 C.2 — total findings on those docs
  related_severities: Record<Severity, number>; // v2.9.3 C.2 — full severity histogram
}

interface StatuteGroup {
  statute: string;
  count: number;
  document_ids: Set<string>;
  unique_shas: Set<string>;
}

function pctOf(part: number, whole: number): string {
  if (whole <= 0) return '0%';
  return `${Math.round((part / whole) * 1000) / 10}%`;
}

function triggerMarkdownDownload(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function SynthesisPage() {
  const nav = useAppNavigate();
  const entries = useAuditHistoryStore((s) => s.entries);

  const aggregates = useMemo(() => {
    const severity = { critical: 0, high: 0, medium: 0, low: 0 };
    const uniqueDocs = new Set<string>();
    const byFindingId = new Map<string, FindingGroup>();
    const byVendor = new Map<string, VendorGroup>();
    const byStatute = new Map<string, StatuteGroup>();

    // v2.9.3 C.1 — `document_id` on AuditFinding is the per-audit
    // document handle, not the SHA-256. Building a job-scoped doc_id →
    // sha256 map lets the aggregations report unique-SHA counts that
    // don't double-count the same bytes uploaded under different
    // filenames. Without this, the MAS top-findings table reports
    // "50 docs / 50 occurrences" because doc_id IS the per-upload
    // handle (the run-12 silent-failure motivating example).
    const docIdToSha = new Map<string, string>(); // key: `${job_id}::${document_id}`
    // v2.9.3 C.2 — also build a vendor-per-document index so the vendor
    // aggregation can produce a related-findings severity histogram
    // (covering ALL findings on docs where the vendor was detected,
    // not just the LOW-severity vendor-detected:* emissions).
    const docVendors = new Map<string, Set<string>>(); // key: `${job_id}::${document_id}`

    for (const entry of entries) {
      for (const doc of entry.results.document_manifest ?? []) {
        uniqueDocs.add(doc.sha256);
        docIdToSha.set(`${entry.job_id}::${doc.document_id}`, doc.sha256);
      }
      // First pass: index vendors by document so the second pass can
      // attribute every finding on a vendor-tagged document.
      for (const f of entry.results.findings ?? []) {
        const vendor = (f.details as Record<string, unknown>)?.vendor;
        if (typeof vendor === 'string' && vendor.length > 0) {
          const k = `${entry.job_id}::${f.document_id}`;
          if (!docVendors.has(k)) docVendors.set(k, new Set<string>());
          docVendors.get(k)!.add(vendor);
        }
      }

      for (const f of entry.results.findings ?? []) {
        if (f.severity in severity) severity[f.severity as Severity] += 1;
        const docKey = `${entry.job_id}::${f.document_id}`;
        const sha = docIdToSha.get(docKey) ?? f.document_id;

        // Group by finding id
        const fg = byFindingId.get(f.id);
        if (!fg) {
          byFindingId.set(f.id, {
            id: f.id,
            issue: f.issue,
            layer: f.layer,
            severity: f.severity,
            document_ids: new Set([f.document_id]),
            unique_shas: new Set([sha]),
            job_ids: new Set([entry.job_id]),
            count: 1,
          });
        } else {
          fg.document_ids.add(f.document_id);
          fg.unique_shas.add(sha);
          fg.job_ids.add(entry.job_id);
          fg.count += 1;
        }

        // Group by vendor (surveillance detector — vendor-tagged emissions)
        const vendor = (f.details as Record<string, unknown>)?.vendor;
        if (typeof vendor === 'string' && vendor.length > 0) {
          let vg = byVendor.get(vendor);
          if (!vg) {
            vg = {
              vendor,
              count: 0,
              severities: { critical: 0, high: 0, medium: 0, low: 0 },
              document_ids: new Set<string>(),
              unique_shas: new Set<string>(),
              related_count: 0,
              related_severities: { critical: 0, high: 0, medium: 0, low: 0 },
            };
            byVendor.set(vendor, vg);
          }
          vg.count += 1;
          if (f.severity in vg.severities) {
            vg.severities[f.severity as Severity] += 1;
          }
          vg.document_ids.add(f.document_id);
          vg.unique_shas.add(sha);
        }

        // v2.9.3 C.2 — related-findings tally: every finding on a
        // vendor-tagged document, regardless of which detector emitted
        // it, contributes to the vendor's related-severity histogram.
        // This is what answers "Axon-related risk profile" (mixed
        // severities) instead of "vendor-detection emissions" (all LOW).
        const vendorsOnDoc = docVendors.get(docKey);
        if (vendorsOnDoc) {
          for (const vName of vendorsOnDoc) {
            const vg = byVendor.get(vName);
            if (vg) {
              vg.related_count += 1;
              if (f.severity in vg.related_severities) {
                vg.related_severities[f.severity as Severity] += 1;
              }
            }
          }
        }

        // Group by statute
        const statute = (f.details as Record<string, unknown>)?.statute;
        if (typeof statute === 'string' && statute.length > 0) {
          const sg = byStatute.get(statute);
          if (!sg) {
            byStatute.set(statute, {
              statute,
              count: 1,
              document_ids: new Set([f.document_id]),
              unique_shas: new Set([sha]),
            });
          } else {
            sg.count += 1;
            sg.document_ids.add(f.document_id);
            sg.unique_shas.add(sha);
          }
        }
      }
    }

    const byFindingArr = [...byFindingId.values()].sort((a, b) => {
      const sevDiff =
        (SEV_ORDER[a.severity] ?? 99) - (SEV_ORDER[b.severity] ?? 99);
      if (sevDiff !== 0) return sevDiff;
      return b.unique_shas.size - a.unique_shas.size;
    });

    const byVendorArr = [...byVendor.values()].sort((a, b) => b.count - a.count);
    const byStatuteArr = [...byStatute.values()].sort((a, b) => b.count - a.count);

    return {
      severity,
      uniqueDocCount: uniqueDocs.size,
      totalFindings:
        severity.critical + severity.high + severity.medium + severity.low,
      byFinding: byFindingArr,
      byVendor: byVendorArr,
      byStatute: byStatuteArr,
    };
  }, [entries]);

  const handleExportMarkdown = useCallback(() => {
    const { severity, uniqueDocCount, totalFindings, byFinding, byVendor, byStatute } =
      aggregates;
    const now = new Date().toISOString();

    const lines: string[] = [];
    lines.push(`# O.D.I.A. Master Audit Synthesis`);
    lines.push('');
    lines.push(`Generated ${now.slice(0, 19).replace('T', ' ')} UTC`);
    lines.push('');
    lines.push(`## Scope`);
    lines.push('');
    lines.push(`- **Audits analyzed**: ${entries.length}`);
    lines.push(`- **Unique documents** (by SHA-256): ${uniqueDocCount}`);
    lines.push(`- **Total findings**: ${totalFindings}`);
    lines.push('');
    lines.push(`## Severity distribution`);
    lines.push('');
    lines.push(`| Severity | Count |`);
    lines.push(`|----------|------:|`);
    lines.push(`| Critical | ${severity.critical} |`);
    lines.push(`| High     | ${severity.high} |`);
    lines.push(`| Medium   | ${severity.medium} |`);
    lines.push(`| Low      | ${severity.low} |`);
    lines.push('');

    lines.push(`## Top findings by severity and cross-document prevalence`);
    lines.push('');
    if (byFinding.length === 0) {
      lines.push(`_No findings._`);
    } else {
      // v2.9.3 C.1 — "Unique SHAs" replaces "Docs" so duplicate uploads
      // of the same bytes don't inflate the prevalence count. "Total
      // Emissions" replaces the ambiguous "Occurrences".
      lines.push(`| Finding ID | Detector | Severity | Unique SHAs | Total Emissions | Issue |`);
      lines.push(`|-----------|---------|----------|-----:|-----:|-------|`);
      for (const f of byFinding.slice(0, 25)) {
        const issueEscaped = f.issue.replace(/\|/g, '\\|');
        lines.push(
          `| \`${f.id}\` | ${f.layer} | ${f.severity} | ${f.unique_shas.size} | ${f.count} | ${issueEscaped} |`,
        );
      }
    }
    lines.push('');

    if (byVendor.length > 0) {
      // v2.9.3 C.2 — split detection emissions from related-findings
      // severity histogram. The pre-2.9.3 column reported the severity
      // of `vendor-detected:*` emissions only (uniformly LOW, which is
      // misleading). "Related findings C/H/M/L" reflects every finding
      // on documents where the vendor was detected, regardless of which
      // detector emitted it — that's the column that answers "what's
      // this vendor's actual risk surface?"
      lines.push(`## Vendor aggregation`);
      lines.push('');
      lines.push(
        `| Vendor | Detections | Unique SHAs | Related Findings | C/H/M/L (related) |`,
      );
      lines.push(
        `|--------|-----------:|------------:|-----------------:|-------------------|`,
      );
      for (const v of byVendor) {
        const sev = v.related_severities;
        const breakdown = `${sev.critical}/${sev.high}/${sev.medium}/${sev.low}`;
        lines.push(
          `| ${v.vendor} | ${v.count} | ${v.unique_shas.size} | ${v.related_count} | ${breakdown} |`,
        );
      }
      lines.push('');
    }

    if (byStatute.length > 0) {
      lines.push(`## Statute aggregation`);
      lines.push('');
      lines.push(`| Statute | Findings | Documents |`);
      lines.push(`|---------|---------:|----------:|`);
      for (const s of byStatute) {
        lines.push(
          `| ${s.statute} | ${s.count} | ${s.document_ids.size} |`,
        );
      }
      lines.push('');
    }

    lines.push(`## Audit history`);
    lines.push('');
    lines.push(`| Generated | Job ID | Document(s) | Findings |`);
    lines.push(`|-----------|--------|-------------|---------:|`);
    for (const e of entries) {
      const first = e.results.document_manifest?.[0]?.filename ?? 'Audit';
      const more =
        e.results.document_count > 1
          ? ` +${e.results.document_count - 1} more`
          : '';
      const name = (first + more).replace(/\|/g, '\\|');
      lines.push(
        `| ${e.results.generated_at.slice(0, 16).replace('T', ' ')} | \`${e.job_id.slice(0, 8)}\` | ${name} | ${e.results.finding_count} |`,
      );
    }
    lines.push('');

    triggerMarkdownDownload(
      lines.join('\n'),
      `odia_master_audit_synthesis_${now.slice(0, 10)}.md`,
    );
  }, [aggregates, entries]);

  const handleExportDocx = useCallback(async () => {
    const {
      severity,
      uniqueDocCount,
      totalFindings,
      byFinding,
      byVendor,
      byStatute,
    } = aggregates;
    const now = new Date().toISOString();

    // Dynamic import so the ~400KB docx bundle only loads when the user
    // clicks Export — not on every Synthesis page view.
    const {
      Document,
      Packer,
      Paragraph,
      HeadingLevel,
      TextRun,
      Table,
      TableRow,
      TableCell,
      WidthType,
      AlignmentType,
    } = await import('docx');

    const heading = (text: string, level: (typeof HeadingLevel)[keyof typeof HeadingLevel]) =>
      new Paragraph({ text, heading: level, spacing: { before: 240, after: 120 } });

    const para = (text: string, bold = false) =>
      new Paragraph({
        children: [new TextRun({ text, bold })],
        spacing: { after: 80 },
      });

    const cell = (text: string, opts: { bold?: boolean; width?: number } = {}) =>
      new TableCell({
        width: opts.width
          ? { size: opts.width, type: WidthType.PERCENTAGE }
          : undefined,
        children: [
          new Paragraph({
            children: [new TextRun({ text, bold: opts.bold })],
          }),
        ],
      });

    const headerRow = (labels: string[]) =>
      new TableRow({
        tableHeader: true,
        children: labels.map((l) => cell(l, { bold: true })),
      });

    const dataRow = (values: string[]) =>
      new TableRow({ children: values.map((v) => cell(v)) });

    // Column widths are given in DXA (twentieths of a point; 1440 DXA = 1 inch).
    // Without explicit per-column widths, WordPad (and some older DOCX
    // renderers) collapse every cell to minimum width and wrap text
    // character-by-character. Total should sit around the usable page width,
    // roughly 9360 DXA for letter-size paper with 1-inch margins.
    const table = (rows: DocxTableRow[], columnWidths: number[]) =>
      new Table({
        rows,
        width: { size: 100, type: WidthType.PERCENTAGE },
        columnWidths,
      });

    const children: (DocxParagraph | DocxTable)[] = [];

    children.push(
      new Paragraph({
        alignment: AlignmentType.LEFT,
        heading: HeadingLevel.TITLE,
        children: [new TextRun({ text: 'O.D.I.A. Master Audit Synthesis' })],
      }),
      para(`Generated ${now.slice(0, 19).replace('T', ' ')} UTC`),
    );

    children.push(heading('Scope', HeadingLevel.HEADING_1));
    children.push(para(`Audits analyzed: ${entries.length}`));
    children.push(para(`Unique documents (by SHA-256): ${uniqueDocCount}`));
    children.push(para(`Total findings: ${totalFindings}`));

    children.push(heading('Severity distribution', HeadingLevel.HEADING_1));
    children.push(
      table(
        [
          headerRow(['Severity', 'Count']),
          dataRow(['Critical', String(severity.critical)]),
          dataRow(['High', String(severity.high)]),
          dataRow(['Medium', String(severity.medium)]),
          dataRow(['Low', String(severity.low)]),
        ],
        [4680, 4680], // 3.25" + 3.25"
      ),
    );

    children.push(
      heading(
        'Top findings by severity and cross-document prevalence',
        HeadingLevel.HEADING_1,
      ),
    );
    if (byFinding.length === 0) {
      children.push(para('No findings.'));
    } else {
      children.push(
        table(
          [
            headerRow([
              'Finding ID',
              'Detector',
              'Severity',
              'Unique SHAs',
              'Total Emissions',
              'Issue',
            ]),
            ...byFinding
              .slice(0, 25)
              .map((f) =>
                dataRow([
                  f.id,
                  f.layer,
                  f.severity,
                  String(f.unique_shas.size),
                  String(f.count),
                  f.issue,
                ]),
              ),
          ],
          [2200, 1400, 1000, 700, 1060, 3000], // 6 cols, Issue widest
        ),
      );
    }

    if (byVendor.length > 0) {
      children.push(heading('Vendor aggregation', HeadingLevel.HEADING_1));
      children.push(
        table(
          [
            headerRow([
              'Vendor',
              'Detections',
              'Unique SHAs',
              'Related',
              'Critical',
              'High',
              'Medium',
              'Low',
            ]),
            ...byVendor.map((v) =>
              dataRow([
                v.vendor,
                String(v.count),
                String(v.unique_shas.size),
                String(v.related_count),
                String(v.related_severities.critical),
                String(v.related_severities.high),
                String(v.related_severities.medium),
                String(v.related_severities.low),
              ]),
            ),
          ],
          [2400, 900, 900, 900, 900, 900, 900, 900], // 8 cols, Vendor widest
        ),
      );
    }

    if (byStatute.length > 0) {
      children.push(heading('Statute aggregation', HeadingLevel.HEADING_1));
      children.push(
        table(
          [
            headerRow(['Statute', 'Findings', 'Documents']),
            ...byStatute.map((s) =>
              dataRow([
                s.statute,
                String(s.count),
                String(s.document_ids.size),
              ]),
            ),
          ],
          [5560, 1900, 1900], // 3 cols, Statute widest
        ),
      );
    }

    children.push(heading('Audit history', HeadingLevel.HEADING_1));
    children.push(
      table(
        [
          headerRow(['Generated', 'Job ID', 'Document(s)', 'Findings']),
          ...entries.map((e) => {
            const first =
              e.results.document_manifest?.[0]?.filename ?? 'Audit';
            const more =
              e.results.document_count > 1
                ? ` +${e.results.document_count - 1} more`
                : '';
            return dataRow([
              e.results.generated_at.slice(0, 16).replace('T', ' '),
              e.job_id.slice(0, 8),
              first + more,
              String(e.results.finding_count),
            ]);
          }),
        ],
        [2200, 1400, 4700, 1060], // 4 cols, Document(s) widest
      ),
    );

    const doc = new Document({
      creator: 'O.D.I.A.',
      title: 'Master Audit Synthesis',
      description: 'Cross-audit findings synthesis report',
      sections: [{ children }],
    });

    const blob = await Packer.toBlob(doc);
    triggerBlobDownload(
      blob,
      `odia_master_audit_synthesis_${now.slice(0, 10)}.docx`,
    );
  }, [aggregates, entries]);

  if (entries.length === 0) {
    return (
      <DashboardLayout>
        <Card variant="bordered">
          <div className="text-center py-12">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No audits to synthesize
            </h3>
            <p className="text-gray-600 mb-6">
              Run one or more audits first. Synthesis aggregates findings across
              all local audit history to surface cross-document patterns.
            </p>
            <Button variant="primary" onClick={() => nav('/upload')}>
              Go to Upload
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  const { severity, uniqueDocCount, totalFindings, byFinding, byVendor, byStatute } =
    aggregates;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* v2.9.2 — canonical hero pattern with marble texture */}
        <section className="page-hero-synthesis hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10">
            <div className="hud-label-accent hud-amber mb-3">
              [ MASTER AUDIT SYNTHESIS · CROSS-JURISDICTIONAL ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Master Audit Synthesis
            </h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              {entries.length} audit{entries.length === 1 ? '' : 's'} ·{' '}
              {uniqueDocCount} unique document{uniqueDocCount === 1 ? '' : 's'}{' '}
              · {totalFindings} findings — cumulative across all local audit
              history.
            </p>

            <div className="flex items-center gap-3 mt-6 flex-wrap">
              <Button variant="secondary" onClick={handleExportMarkdown}>
                ↓ Markdown
              </Button>
              <Button variant="primary" onClick={handleExportDocx}>
                ↓ DOCX
              </Button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <HeroMetricTile
                label="Critical"
                value={severity.critical}
                sublabel={pctOf(severity.critical, totalFindings)}
                tone="critical"
              />
              <HeroMetricTile
                label="High"
                value={severity.high}
                sublabel={pctOf(severity.high, totalFindings)}
                tone="high"
              />
              <HeroMetricTile
                label="Medium"
                value={severity.medium}
                sublabel={pctOf(severity.medium, totalFindings)}
                tone="medium"
              />
              <HeroMetricTile
                label="Low"
                value={severity.low}
                sublabel={pctOf(severity.low, totalFindings)}
                tone="low"
              />
            </div>
          </div>
        </section>

        {/* Top findings by prevalence */}
        <Card title="Top findings by cross-document prevalence" variant="bordered">
          {byFinding.length === 0 ? (
            <div className="text-center py-8 text-gray-400 text-sm">
              No findings to rank
            </div>
          ) : (
            <div className="space-y-2">
              {byFinding.slice(0, 15).map((f) => (
                <div
                  key={f.id}
                  className="flex items-start gap-3 py-2 border-b border-gray-100 last:border-0"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="px-2 py-0.5 rounded text-xs font-semibold uppercase bg-gray-100 text-gray-800">
                        {f.severity}
                      </span>
                      <span className="text-xs font-mono text-gray-500">
                        {f.id}
                      </span>
                      <span className="text-xs text-gray-400">
                        {f.layer}
                      </span>
                    </div>
                    <div className="text-sm text-gray-900">{f.issue}</div>
                  </div>
                  <div className="text-right text-xs text-gray-600 flex-shrink-0">
                    <div>
                      <span className="font-semibold">{f.unique_shas.size}</span>{' '}
                      SHA{f.unique_shas.size === 1 ? '' : 's'}
                    </div>
                    <div>
                      <span className="font-semibold">{f.count}</span> emission
                      {f.count === 1 ? '' : 's'}
                    </div>
                  </div>
                </div>
              ))}
              {byFinding.length > 15 && (
                <div className="text-xs text-gray-500 pt-2">
                  …and {byFinding.length - 15} more (included in Markdown export)
                </div>
              )}
            </div>
          )}
        </Card>

        {/* Vendor + statute side-by-side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Vendors flagged" variant="bordered">
            {byVendor.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No vendor-specific findings detected
              </div>
            ) : (
              <div className="space-y-2">
                {byVendor.map((v) => (
                  <div
                    key={v.vendor}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 gap-3"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-gray-900">{v.vendor}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {v.unique_shas.size} SHA{v.unique_shas.size === 1 ? '' : 's'} ·{' '}
                        {v.count} detection{v.count === 1 ? '' : 's'}
                      </div>
                    </div>
                    {/* v2.9.3 C.2 — related-findings severity histogram */}
                    {v.related_count > 0 && (
                      <div className="text-xs text-gray-600 flex-shrink-0 text-right">
                        <div className="font-mono">
                          {v.related_severities.critical}/
                          {v.related_severities.high}/
                          {v.related_severities.medium}/
                          {v.related_severities.low}
                        </div>
                        <div className="text-[10px] text-gray-400">C/H/M/L related</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Statutes referenced" variant="bordered">
            {byStatute.length === 0 ? (
              <div className="text-center py-8 text-gray-400 text-sm">
                No statute-specific findings detected
              </div>
            ) : (
              <div className="space-y-2">
                {byStatute.map((s) => (
                  <div
                    key={s.statute}
                    className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0"
                  >
                    <div className="font-medium text-gray-900">{s.statute}</div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-gray-500">
                        {s.document_ids.size} doc{s.document_ids.size === 1 ? '' : 's'}
                      </span>
                      <span className="text-gray-500">· {s.count} findings</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Audit timeline */}
        <Card title="Audits in this synthesis" variant="bordered">
          <div className="space-y-2">
            {entries.map((e) => (
              <AppLink
                key={e.job_id}
                href={`/results?job_id=${e.job_id}`}
                className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 -mx-2 px-2 rounded"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-sm text-gray-900 truncate">
                    {e.results.document_manifest?.[0]?.filename ?? 'Audit'}
                    {e.results.document_count > 1 &&
                      ` +${e.results.document_count - 1} more`}
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    {e.job_id.slice(0, 8)} ·{' '}
                    {e.results.generated_at.slice(0, 16).replace('T', ' ')}
                  </div>
                </div>
                <div className="text-sm text-gray-700 flex-shrink-0">
                  {e.results.finding_count} findings
                </div>
              </AppLink>
            ))}
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
