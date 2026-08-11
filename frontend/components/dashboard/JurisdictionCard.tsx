/**
 * JurisdictionCard — current jurisdiction config + active DB jurisdictions.
 *
 * Fetches GET /config/jurisdiction for the configured single-jurisdiction
 * context (legacy, single-jurisdiction setup) AND GET /api/v1/jurisdictions
 * (v3.2.0) for the multi-jurisdiction roll-up of every distinct
 * jurisdiction with persisted documents.
 *
 * Pre-v3.2 the card defaulted to "City of Example" placeholder content
 * when no jurisdiction.json was copied to the user dir, even if the DB
 * held documents tagged with real jurisdiction ids (visalia, tcda, etc.)
 * via webhook ingest. v3.2 surfaces those real DB jurisdictions in the
 * same card so the operator immediately sees what audit data they
 * actually have, regardless of the config-file state.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { getAPIClient } from '@/lib/api/client';
import {
  MapPinIcon,
  AlertCircleIcon,
  CheckCircleIcon,
} from '@/components/base/Icons';
import { AppLink } from '@/lib/navigation';
import type { JurisdictionInfo } from '@/lib/types/api';
import type { JurisdictionRollup } from '@/lib/api/client';

export function JurisdictionCard() {
  const [info, setInfo] = useState<JurisdictionInfo | null>(null);
  const [dbJurisdictions, setDbJurisdictions] = useState<JurisdictionRollup[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const client = getAPIClient();
    Promise.allSettled([
      client.getJurisdiction(),
      client.listJurisdictions(),
    ])
      .then(([configResult, dbResult]) => {
        if (cancelled) return;
        if (configResult.status === 'fulfilled') {
          setInfo(configResult.value);
        } else {
          setError(
            configResult.reason instanceof Error
              ? configResult.reason.message
              : 'Failed to load jurisdiction config',
          );
        }
        if (dbResult.status === 'fulfilled') {
          setDbJurisdictions(dbResult.value.items);
        }
        // DB rollup failing is non-fatal — we still show config alone.
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  // Retry automatically while the backend is still starting up.
  useEffect(() => {
    if (!error && dbJurisdictions.length > 0) return;
    if (loading) return;
    const timer = setTimeout(() => setAttempt((n) => n + 1), 3000);
    return () => clearTimeout(timer);
  }, [error, dbJurisdictions.length, loading]);

  const hasConfig = info && info.loaded;
  const hasDB = dbJurisdictions.length > 0;

  return (
    <Card
      variant="bordered"
      icon={<MapPinIcon size={18} />}
      title="Jurisdiction"
      subtitle="Active analysis context"
    >
      {loading && (
        <div
          className="flex items-center gap-2 text-sm py-2"
          style={{ color: 'var(--smoke-500)' }}
        >
          <span
            className="w-2 h-2 rounded-full animate-odia-pulse"
            style={{ background: 'var(--gold-400)' }}
          />
          Loading configuration…
        </div>
      )}

      {error && !loading && !hasDB && (
        <div className="p-3 gem-edge" style={{ background: 'rgba(244, 63, 94, 0.08)' }}>
          <div className="flex items-start gap-2">
            <AlertCircleIcon
              size={16}
              style={{ color: 'var(--severity-critical)' }}
              className="mt-0.5"
            />
            <div>
              <p
                className="text-sm font-medium"
                style={{ color: 'var(--severity-critical)' }}
              >
                Jurisdiction unavailable
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--smoke-200)' }}>
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Configured-jurisdiction section (legacy single-jurisdiction surface) */}
      {hasConfig && !loading && (
        <div className="space-y-3">
          <DetailRow label="Name" value={info.name} mono={false} strong />
          {info.state && <DetailRow label="State" value={info.state} />}
          {info.country && <DetailRow label="Country" value={info.country} />}
          {info.meeting_type && (
            <DetailRow
              label="Meeting Type"
              value={<span className="capitalize">{info.meeting_type}</span>}
            />
          )}
          <DetailRow
            label="Agencies"
            value={
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium gem-edge"
                style={{
                  color: 'var(--gold-200)',
                  background: 'rgba(216, 177, 60, 0.10)',
                }}
              >
                {info.agency_count}
              </span>
            }
          />
          <div
            className="pt-2"
            style={{ borderTop: '1px solid var(--gem-edge-gold)' }}
          >
            <span
              className="inline-flex items-center gap-1.5 text-xs font-medium"
              style={{ color: 'var(--neon-emerald)' }}
            >
              <CheckCircleIcon size={12} />
              Configuration loaded
            </span>
          </div>
        </div>
      )}

      {/* v3.2.0 — Active jurisdictions in DB (always shown when present) */}
      {hasDB && !loading && (
        <div
          className={hasConfig ? 'mt-4 pt-4' : ''}
          style={
            hasConfig
              ? { borderTop: '1px solid var(--gem-edge-gold)' }
              : undefined
          }
        >
          <div
            className="text-xs font-medium uppercase tracking-wide mb-2"
            style={{ color: 'var(--gold-400)' }}
          >
            Active jurisdictions ({dbJurisdictions.length})
          </div>
          <div className="space-y-1.5">
            {dbJurisdictions.slice(0, 6).map((j) => (
              <AppLink
                key={j.jurisdiction}
                href={`/anomalies?jurisdiction=${encodeURIComponent(j.jurisdiction)}`}
                className="flex items-center justify-between gap-3 px-2 py-1 -mx-2 rounded hover:bg-black/20"
              >
                <span
                  className="text-sm font-medium truncate"
                  style={{ color: 'var(--smoke-100)' }}
                >
                  {j.jurisdiction}
                </span>
                <span
                  className="text-xs flex-shrink-0 font-mono"
                  style={{ color: 'var(--smoke-400)' }}
                >
                  {j.document_count} docs · {j.anomaly_count} findings
                </span>
              </AppLink>
            ))}
            {dbJurisdictions.length > 6 && (
              <div
                className="text-xs pt-1"
                style={{ color: 'var(--smoke-500)' }}
              >
                …and {dbJurisdictions.length - 6} more
              </div>
            )}
          </div>
        </div>
      )}

      {/* Empty state: no config AND no DB jurisdictions */}
      {!hasConfig && !hasDB && !loading && !error && (
        <div className="text-center py-6">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 gem-edge"
            style={{
              background: 'rgba(216, 177, 60, 0.08)',
              color: 'var(--gold-300)',
            }}
          >
            <MapPinIcon size={20} />
          </div>
          <p className="text-sm font-medium" style={{ color: 'var(--smoke-100)' }}>
            No jurisdiction configured
          </p>
          <p
            className="text-xs mt-1 max-w-xs mx-auto"
            style={{ color: 'var(--smoke-500)' }}
          >
            Add a jurisdiction config file to enable location-aware analysis,
            or ingest documents via the scraper webhook to populate active
            jurisdictions directly from the DB.
          </p>
          <div
            className="inline-flex items-center gap-1.5 mt-3 px-2.5 py-1 font-mono text-xs gem-edge"
            style={{
              color: 'var(--gold-200)',
              background: 'rgba(216, 177, 60, 0.08)',
            }}
          >
            config/multi_jurisdiction/
          </div>
        </div>
      )}
    </Card>
  );
}

function DetailRow({
  label,
  value,
  mono = false,
  strong = false,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
  strong?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span
        className="text-xs font-medium uppercase tracking-wide"
        style={{ color: 'var(--gold-400)' }}
      >
        {label}
      </span>
      <span
        className={`text-right min-w-0 truncate ${mono ? 'font-mono text-xs' : 'text-sm'} ${strong ? 'font-semibold' : ''}`}
        style={{ color: strong ? 'var(--smoke-100)' : 'var(--smoke-200)' }}
      >
        {value}
      </span>
    </div>
  );
}
