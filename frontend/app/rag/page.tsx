'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { getAPIClient } from '@/lib/api/client';
import type { RAGQueryResponse, RAGStatusResponse } from '@/lib/api/client';

const EXAMPLE_QUESTIONS = [
  'Which jurisdictions have the most critical JAG violations?',
  'What surveillance procurement findings appear across multiple jurisdictions?',
  'Summarize fiscal anomalies detected in the audit corpus.',
  'Which vendors appear most frequently in procurement findings?',
];

const SOURCE_FILTER_OPTIONS = [
  { value: '', label: 'All sources' },
  { value: 'documents', label: 'Documents only' },
  { value: 'findings', label: 'Findings only' },
  { value: 'analysis', label: 'Analysis only' },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatusBar({ status, onRefresh }: {
  status: RAGStatusResponse | null;
  onRefresh: () => void;
}) {
  if (!status) return null;
  const totalIndexed = Object.values(status.indexed).reduce((a, b) => a + b, 0);
  return (
    <div
      className="flex flex-wrap items-center gap-4 px-4 py-2 rounded text-xs font-mono"
      style={{
        background: 'rgba(14,14,20,0.7)',
        border: '1px solid var(--gem-edge-gold)',
        color: 'var(--smoke-300)',
      }}
    >
      <span style={{ color: 'var(--gold-400)' }}>[ RAG INDEX ]</span>
      {Object.entries(status.indexed).map(([name, count]) => (
        <span key={name}>
          <span style={{ color: 'var(--smoke-500)' }}>{name}:</span>{' '}
          <span style={{ color: 'var(--neon-emerald)' }}>{count}</span>
        </span>
      ))}
      <span>
        <span style={{ color: 'var(--smoke-500)' }}>total:</span>{' '}
        <span style={{ color: 'var(--neon-emerald)' }}>{totalIndexed}</span>
      </span>
      <span className="ml-auto flex items-center gap-2">
        <span className="flex items-center gap-1.5">
          <span
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{
              background: status.llm_available ? 'var(--neon-emerald)' : 'var(--severity-critical)',
              boxShadow: status.llm_available
                ? '0 0 6px var(--neon-emerald)'
                : '0 0 6px var(--severity-critical)',
            }}
          />
          {status.llm_available
            ? `${status.llm_provider} · ${status.llm_model}`
            : 'LLM offline — retrieval only'}
        </span>
        <button
          type="button"
          onClick={onRefresh}
          style={{ color: 'var(--smoke-500)' }}
          title="Refresh status"
        >
          ↻
        </button>
      </span>
    </div>
  );
}

function SourceCard({ source, index }: { source: Record<string, unknown>; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const title = String(source.title ?? source.id ?? `Source ${index + 1}`);
  const text = String(source.text ?? source.content ?? '');
  const jurisdiction = source.jurisdiction ? String(source.jurisdiction) : null;
  const layer = source.layer ? String(source.layer) : null;
  const score = typeof source.score === 'number' ? source.score : null;
  const issue = source.issue ? String(source.issue) : null;

  return (
    <div
      className="rounded text-xs"
      style={{
        background: 'rgba(14,14,20,0.6)',
        border: '1px solid rgba(216,177,60,0.15)',
      }}
    >
      <button
        type="button"
        className="w-full flex items-start gap-3 px-3 py-2 text-left"
        onClick={() => setExpanded((v) => !v)}
      >
        <span
          className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded font-semibold"
          style={{ background: 'rgba(31,232,143,0.12)', color: 'var(--neon-emerald)' }}
        >
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate" style={{ color: 'var(--smoke-100)' }}>
            {title}
          </div>
          <div className="flex flex-wrap gap-2 mt-0.5">
            {jurisdiction && <span style={{ color: 'var(--gold-400)' }}>{jurisdiction}</span>}
            {layer && <span style={{ color: 'var(--smoke-500)' }}>{layer}</span>}
            {score !== null && (
              <span style={{ color: 'var(--smoke-500)' }}>score: {score.toFixed(3)}</span>
            )}
          </div>
        </div>
        <span style={{ color: 'var(--smoke-500)' }}>{expanded ? '▲' : '▼'}</span>
      </button>
      {expanded && (
        <div
          className="px-3 pb-3 pt-1 border-t"
          style={{ borderColor: 'rgba(216,177,60,0.10)', color: 'var(--smoke-300)' }}
        >
          {issue && (
            <p className="mb-1">
              <span style={{ color: 'var(--gold-400)' }}>Finding: </span>{issue}
            </p>
          )}
          {text && <p className="whitespace-pre-wrap leading-relaxed">{text}</p>}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page — no Suspense wrapper (page does not use useSearchParams)
// ---------------------------------------------------------------------------

export default function RAGPage() {
  const mountedRef = useRef(true);

  const [status, setStatus] = useState<RAGStatusResponse | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);

  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [sourceFilter, setSourceFilter] = useState('');

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGQueryResponse | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Register mounted flag — cleanup on unmount
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; };
  }, []);

  // Status fetch — manual or on mount, with AbortController
  const fetchStatus = useCallback(() => {
    const client = getAPIClient();
    const controller = new AbortController();
    setStatusLoading(true);
    setStatusMsg(null);

    // Try /api/v1/rag/status first, fall back to /rag/status
    client.ragStatus()
      .then((s) => {
        if (!mountedRef.current) return;
        setStatus(s);
        setStatusLoading(false);
      })
      .catch(() => {
        // Fallback: try old path /rag/status directly
        client.ragStatusLegacy()
          .then((s) => {
            if (!mountedRef.current) return;
            setStatus(s);
            setStatusLoading(false);
          })
          .catch(() => {
            if (!mountedRef.current) return;
            setStatusMsg('RAG status unavailable — index may not be built yet.');
            setStatusLoading(false);
          });
      });

    return () => controller.abort();
  }, []);

  // Auto-fetch status once on mount
  useEffect(() => {
    const cleanup = fetchStatus();
    return cleanup;
  }, [fetchStatus]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    const client = getAPIClient();
    setLoading(true);
    setResult(null);
    setQueryError(null);
    try {
      const r = await client.ragQuery(
        question.trim(),
        topK,
        sourceFilter || null,
      );
      if (mountedRef.current) setResult(r);
    } catch (err: unknown) {
      if (mountedRef.current) {
        const msg = err instanceof Error ? err.message : 'Query failed';
        setQueryError(msg);
      }
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, [question, topK, sourceFilter]);

  const totalIndexed = status
    ? Object.values(status.indexed).reduce((a, b) => a + b, 0)
    : null;

  return (
    <DashboardLayout>
      <div className="space-y-5">

        {/* Hero */}
        <section
          className="hud-brackets p-6 relative overflow-hidden"
          style={{ background: 'rgba(7,7,10,0.7)' }}
        >
          <div className="relative z-10">
            <div
              className="hud-label-accent mb-3"
              style={{ color: 'var(--neon-emerald)' }}
            >
              [ ORACULUS RAG · NATURAL LANGUAGE QUERY ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Ask the Audit Corpus
            </h1>
            <p className="hud-subtext mt-2 max-w-2xl">
              Natural language queries grounded in your indexed audit findings,
              documents, and cross-jurisdiction patterns.
            </p>
            <div className="mt-4 space-y-2">
              {statusLoading && (
                <p className="text-xs" style={{ color: 'var(--smoke-500)' }}>
                  Checking RAG status…
                </p>
              )}
              {!statusLoading && status && (
                <StatusBar status={status} onRefresh={fetchStatus} />
              )}
              {!statusLoading && statusMsg && (
                <p className="text-xs" style={{ color: 'var(--severity-high)' }}>
                  {statusMsg}
                </p>
              )}
            </div>
          </div>
        </section>

        {/* Empty index warning */}
        {status && totalIndexed === 0 && (
          <Card variant="bordered">
            <div className="text-center py-6">
              <p className="font-medium mb-2" style={{ color: 'var(--gold-300)' }}>
                Index not built
              </p>
              <p className="text-sm mb-4" style={{ color: 'var(--smoke-400)' }}>
                Run from the repo root to enable querying:
              </p>
              <pre
                className="inline-block px-4 py-2 rounded text-sm"
                style={{
                  background: 'rgba(0,0,0,0.5)',
                  color: 'var(--neon-emerald)',
                  border: '1px solid rgba(31,232,143,0.2)',
                }}
              >
                .venv\Scripts\python scripts\build_rag_index.py
              </pre>
            </div>
          </Card>
        )}

        {/* Query form */}
        <Card variant="bordered">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="rag-question"
                className="block text-xs font-semibold uppercase tracking-widest mb-2"
                style={{ color: 'var(--gold-400)' }}
              >
                Question
              </label>
              <textarea
                id="rag-question"
                rows={3}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g. Which jurisdictions have the most critical JAG violations?"
                className="w-full px-3 py-2 rounded text-sm resize-none focus:outline-none"
                style={{
                  background: 'rgba(14,14,20,0.8)',
                  border: '1px solid rgba(216,177,60,0.25)',
                  color: 'var(--smoke-100)',
                }}
                disabled={loading}
              />
              <div className="flex flex-wrap gap-2 mt-2">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    type="button"
                    onClick={() => setQuestion(q)}
                    className="text-xs px-2 py-1 rounded"
                    style={{
                      background: 'rgba(31,232,143,0.07)',
                      border: '1px solid rgba(31,232,143,0.18)',
                      color: 'var(--smoke-400)',
                    }}
                    disabled={loading}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-wrap items-end gap-4">
              <div>
                <label
                  htmlFor="rag-topk"
                  className="block text-xs font-semibold uppercase tracking-widest mb-1"
                  style={{ color: 'var(--gold-400)' }}
                >
                  Top‑K
                </label>
                <input
                  id="rag-topk"
                  type="number"
                  min={1}
                  max={20}
                  value={topK}
                  onChange={(e) =>
                    setTopK(Math.max(1, Math.min(20, Number(e.target.value))))
                  }
                  className="w-20 px-2 py-1.5 rounded text-sm focus:outline-none"
                  style={{
                    background: 'rgba(14,14,20,0.8)',
                    border: '1px solid rgba(216,177,60,0.25)',
                    color: 'var(--smoke-100)',
                  }}
                  disabled={loading}
                />
              </div>

              <div>
                <label
                  htmlFor="rag-filter"
                  className="block text-xs font-semibold uppercase tracking-widest mb-1"
                  style={{ color: 'var(--gold-400)' }}
                >
                  Source filter
                </label>
                <select
                  id="rag-filter"
                  value={sourceFilter}
                  onChange={(e) => setSourceFilter(e.target.value)}
                  className="px-2 py-1.5 rounded text-sm focus:outline-none"
                  style={{
                    background: 'rgba(14,14,20,0.8)',
                    border: '1px solid rgba(216,177,60,0.25)',
                    color: 'var(--smoke-100)',
                  }}
                  disabled={loading}
                >
                  {SOURCE_FILTER_OPTIONS.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>
              </div>

              <div className="ml-auto">
                <Button
                  variant="primary"
                  type="submit"
                  disabled={loading || !question.trim()}
                >
                  {loading ? 'Querying…' : 'Run Query'}
                </Button>
              </div>
            </div>
          </form>
        </Card>

        {/* Errors */}
        {queryError && (
          <Card variant="bordered">
            <p className="text-sm" style={{ color: 'var(--severity-critical)' }}>
              {queryError}
            </p>
          </Card>
        )}

        {/* Loading */}
        {loading && (
          <Card variant="bordered">
            <div className="flex items-center gap-3 py-4">
              <span
                className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  background: 'var(--neon-emerald)',
                  boxShadow: '0 0 8px var(--neon-emerald)',
                  animation: 'odia-pulse 1.4s ease-in-out infinite',
                }}
              />
              <span className="text-sm" style={{ color: 'var(--smoke-300)' }}>
                Querying corpus — first query may take up to 90s if Ollama is loading cold…
              </span>
            </div>
          </Card>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-4">
            <Card title="Answer" variant="bordered">
              <div className="space-y-3">
                {result.error ? (
                  <p className="text-sm" style={{ color: 'var(--severity-high)' }}>
                    {result.error}
                  </p>
                ) : (
                  <div
                    className="text-sm leading-relaxed whitespace-pre-wrap"
                    style={{ color: 'var(--smoke-100)' }}
                  >
                    {result.answer || (
                      <span style={{ color: 'var(--smoke-500)' }}>
                        No answer generated — LLM may be offline. See retrieved sources below.
                      </span>
                    )}
                  </div>
                )}
                <div
                  className="flex flex-wrap gap-4 text-xs pt-2 border-t"
                  style={{
                    borderColor: 'rgba(216,177,60,0.12)',
                    color: 'var(--smoke-500)',
                  }}
                >
                  {result.confidence != null && (
                    <span>
                      confidence:{' '}
                      <span style={{ color: 'var(--gold-300)' }}>
                        {(result.confidence * 100).toFixed(0)}%
                      </span>
                    </span>
                  )}
                  {result.model_used && (
                    <span>
                      model:{' '}
                      <span style={{ color: 'var(--gold-300)' }}>{result.model_used}</span>
                    </span>
                  )}
                  <span>
                    sources retrieved:{' '}
                    <span style={{ color: 'var(--neon-emerald)' }}>
                      {result.sources.length}
                    </span>
                  </span>
                </div>
              </div>
            </Card>

            {result.sources.length > 0 && (
              <Card
                title={`Retrieved sources (${result.sources.length})`}
                variant="bordered"
              >
                <div className="space-y-2">
                  {result.sources.map((src, i) => (
                    <SourceCard
                      key={String(src.id ?? i)}
                      source={src as Record<string, unknown>}
                      index={i}
                    />
                  ))}
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
