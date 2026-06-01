'use client';

import React, { useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { getAPIClient } from '@/lib/api/client';
import type {
  LegalAnalyzeResponse,
  LegalExplainResponse,
  LegalFinding,
  LegalMemorandumResponse,
} from '@/lib/api/client';

// ---------------------------------------------------------------------------
// Types / constants
// ---------------------------------------------------------------------------

type OutputMode = 'findings' | 'memorandum' | 'explainer';
type Audience = 'community' | 'council' | 'media';

const SEVERITY_COLORS: Record<string, string> = {
  high: 'var(--severity-critical)',
  medium: 'var(--severity-high)',
  low: 'var(--severity-medium)',
};

const AUDIENCE_LABELS: Record<Audience, string> = {
  community: 'Community (plain language)',
  council: 'Council / elected officials',
  media: 'Media / press',
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-mono font-bold uppercase"
      style={{
        color: SEVERITY_COLORS[severity] ?? 'var(--smoke-300)',
        border: `1px solid ${SEVERITY_COLORS[severity] ?? 'var(--smoke-600)'}`,
        background: 'rgba(0,0,0,0.3)',
      }}
    >
      {severity}
    </span>
  );
}

function FindingCard({ finding }: { finding: LegalFinding }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className="rounded p-3 mb-2 cursor-pointer"
      style={{
        background: 'rgba(14,14,20,0.6)',
        border: `1px solid ${SEVERITY_COLORS[finding.severity] ?? 'var(--gem-edge-gold)'}22`,
      }}
      onClick={() => setOpen((v) => !v)}
    >
      <div className="flex items-start gap-3">
        <SeverityBadge severity={finding.severity} />
        <div className="flex-1 min-w-0">
          <p className="text-sm" style={{ color: 'var(--smoke-100)' }}>
            {finding.issue}
          </p>
          <p className="text-xs mt-1 font-mono" style={{ color: 'var(--smoke-500)' }}>
            {finding.layer} · {finding.id}
          </p>
        </div>
        <span style={{ color: 'var(--smoke-500)' }} className="text-xs mt-0.5">
          {open ? '▲' : '▼'}
        </span>
      </div>
      {open && Object.keys(finding.details).length > 0 && (
        <div
          className="mt-3 p-2 rounded text-xs font-mono"
          style={{
            background: 'rgba(0,0,0,0.4)',
            color: 'var(--smoke-300)',
            borderTop: '1px solid var(--gem-edge-gold)22',
          }}
        >
          {Object.entries(finding.details).map(([k, v]) =>
            v ? (
              <div key={k} className="mb-1">
                <span style={{ color: 'var(--gold-400)' }}>{k}: </span>
                {String(v)}
              </div>
            ) : null,
          )}
        </div>
      )}
    </div>
  );
}

function CountsBar({ counts }: { counts: LegalAnalyzeResponse['counts'] }) {
  const items = [
    { label: 'HIGH', value: counts.high, color: 'var(--severity-critical)' },
    { label: 'MEDIUM', value: counts.medium, color: 'var(--severity-high)' },
    { label: 'LOW', value: counts.low, color: 'var(--severity-medium)' },
    { label: 'TOTAL', value: counts.total, color: 'var(--neon-emerald)' },
  ];
  return (
    <div className="flex gap-4 flex-wrap mb-4">
      {items.map(({ label, value, color }) => (
        <div
          key={label}
          className="flex flex-col items-center px-3 py-1 rounded"
          style={{ background: 'rgba(0,0,0,0.3)', border: `1px solid ${color}33` }}
        >
          <span className="text-xl font-bold font-mono" style={{ color }}>
            {value}
          </span>
          <span className="text-xs font-mono" style={{ color: 'var(--smoke-500)' }}>
            {label}
          </span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function LegalPage() {
  const [text, setText] = useState('');
  const [mode, setMode] = useState<OutputMode>('findings');
  const [audience, setAudience] = useState<Audience>('community');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [analyzeResult, setAnalyzeResult] = useState<LegalAnalyzeResponse | null>(null);
  const [memoResult, setMemoResult] = useState<LegalMemorandumResponse | null>(null);
  const [explainResult, setExplainResult] = useState<LegalExplainResponse | null>(null);

  const canRun = text.trim().length > 20;

  async function runAnalysis() {
    if (!canRun) return;
    setLoading(true);
    setError(null);
    setAnalyzeResult(null);
    setMemoResult(null);
    setExplainResult(null);

    try {
      const api = getAPIClient();

      // Step 1: always run the detector pass
      const analyzeResp = await api.legalAnalyze(text);
      setAnalyzeResult(analyzeResp);

      // Step 2: generate the requested output format
      if (mode === 'memorandum' && analyzeResp.findings.length > 0) {
        const memoResp = await api.legalMemorandum(text, analyzeResp.findings, {
          format: 'markdown',
        });
        setMemoResult(memoResp);
      } else if (mode === 'explainer' && analyzeResp.findings.length > 0) {
        const explainResp = await api.legalExplain(analyzeResp.findings, {
          audience,
          format: 'text',
        });
        setExplainResult(explainResp);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Header */}
        <div>
          <h1
            className="text-2xl font-bold font-mono mb-1"
            style={{ color: 'var(--gold-400)' }}
          >
            Legal Analysis
          </h1>
          <p className="text-sm" style={{ color: 'var(--smoke-400)' }}>
            Run L-1 through L-10 legal detectors on any document text. Generate
            litigation-grade memoranda or plain-language explainers.
          </p>
        </div>

        {/* Input card */}
        <Card>
          <div className="space-y-4">
            <label
              className="block text-xs font-mono uppercase tracking-wider"
              style={{ color: 'var(--smoke-400)' }}
            >
              Document text
            </label>
            <textarea
              className="w-full rounded p-3 text-sm font-mono resize-y"
              rows={8}
              placeholder="Paste government document text here (CPRA response, policy, MOU, budget, etc.)…"
              value={text}
              onChange={(e) => setText(e.target.value)}
              style={{
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid var(--gem-edge-gold)44',
                color: 'var(--smoke-100)',
                minHeight: '160px',
              }}
            />

            {/* Mode selector */}
            <div className="flex flex-wrap gap-3 items-center">
              <span className="text-xs font-mono" style={{ color: 'var(--smoke-500)' }}>
                OUTPUT:
              </span>
              {(['findings', 'memorandum', 'explainer'] as OutputMode[]).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className="px-3 py-1 rounded text-xs font-mono uppercase"
                  style={{
                    background: mode === m ? 'var(--gold-400)' : 'rgba(0,0,0,0.3)',
                    color: mode === m ? '#000' : 'var(--smoke-300)',
                    border: `1px solid ${mode === m ? 'var(--gold-400)' : 'var(--gem-edge-gold)33'}`,
                  }}
                >
                  {m}
                </button>
              ))}

              {mode === 'explainer' && (
                <>
                  <span
                    className="text-xs font-mono ml-4"
                    style={{ color: 'var(--smoke-500)' }}
                  >
                    AUDIENCE:
                  </span>
                  <select
                    value={audience}
                    onChange={(e) => setAudience(e.target.value as Audience)}
                    className="rounded px-2 py-1 text-xs font-mono"
                    style={{
                      background: 'rgba(0,0,0,0.4)',
                      border: '1px solid var(--gem-edge-gold)44',
                      color: 'var(--smoke-100)',
                    }}
                  >
                    {(Object.keys(AUDIENCE_LABELS) as Audience[]).map((a) => (
                      <option key={a} value={a}>
                        {AUDIENCE_LABELS[a]}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>

            <Button
              onClick={runAnalysis}
              disabled={!canRun || loading}
              variant="primary"
            >
              {loading ? 'Analyzing…' : 'Run Legal Analysis'}
            </Button>
          </div>
        </Card>

        {/* Error */}
        {error && (
          <div
            className="rounded p-3 text-sm"
            style={{
              background: 'rgba(255,60,60,0.1)',
              border: '1px solid var(--severity-critical)44',
              color: 'var(--severity-critical)',
            }}
          >
            {error}
          </div>
        )}

        {/* Results */}
        {analyzeResult && (
          <Card>
            <CountsBar counts={analyzeResult.counts} />

            {/* Findings mode */}
            {(mode === 'findings' || analyzeResult.findings.length === 0) && (
              <>
                <p
                  className="text-xs font-mono uppercase tracking-wider mb-3"
                  style={{ color: 'var(--smoke-500)' }}
                >
                  Findings ({analyzeResult.findings.length})
                </p>
                {analyzeResult.findings.length === 0 ? (
                  <p className="text-sm" style={{ color: 'var(--smoke-400)' }}>
                    No legal issues detected in the provided text.
                  </p>
                ) : (
                  analyzeResult.findings.map((f) => (
                    <FindingCard key={f.id + f.layer} finding={f} />
                  ))
                )}
              </>
            )}

            {/* Memorandum mode */}
            {mode === 'memorandum' && memoResult && (
              <>
                <p
                  className="text-xs font-mono uppercase tracking-wider mb-3"
                  style={{ color: 'var(--smoke-500)' }}
                >
                  Legal Memorandum
                </p>
                <pre
                  className="text-xs whitespace-pre-wrap rounded p-3 overflow-auto"
                  style={{
                    background: 'rgba(0,0,0,0.4)',
                    color: 'var(--smoke-100)',
                    maxHeight: '60vh',
                  }}
                >
                  {memoResult.output}
                </pre>
              </>
            )}

            {/* Explainer mode */}
            {mode === 'explainer' && explainResult && (
              <>
                <p
                  className="text-xs font-mono uppercase tracking-wider mb-3"
                  style={{ color: 'var(--smoke-500)' }}
                >
                  Plain-Language Explainer · {AUDIENCE_LABELS[audience]}
                </p>
                <pre
                  className="text-xs whitespace-pre-wrap rounded p-3 overflow-auto"
                  style={{
                    background: 'rgba(0,0,0,0.4)',
                    color: 'var(--smoke-100)',
                    maxHeight: '60vh',
                  }}
                >
                  {explainResult.output}
                </pre>
              </>
            )}

            {/* Errors from detectors */}
            {analyzeResult.errors.length > 0 && (
              <details className="mt-3">
                <summary
                  className="text-xs font-mono cursor-pointer"
                  style={{ color: 'var(--smoke-500)' }}
                >
                  {analyzeResult.errors.length} detector error(s)
                </summary>
                <ul className="mt-1 text-xs font-mono" style={{ color: 'var(--severity-critical)' }}>
                  {analyzeResult.errors.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
              </details>
            )}
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
