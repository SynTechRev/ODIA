/**
 * JurisdictionCard — current jurisdiction configuration summary.
 *
 * Fetches GET /config/jurisdiction on mount.  Distinguishes three UI
 * states:
 *   1. Loading
 *   2. Loaded + configured — structured detail table
 *   3. Loaded + not configured — empty state with helper text
 *   4. Error — inline error with backend context
 *
 * v2.7.7 Y5 — light-theme pastel chains replaced with gemstone tokens.
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
import type { JurisdictionInfo } from '@/lib/types/api';

export function JurisdictionCard() {
  const [info, setInfo] = useState<JurisdictionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAPIClient()
      .getJurisdiction()
      .then((data) => {
        if (!cancelled) setInfo(data);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : 'Failed to load jurisdiction');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Card
      variant="bordered"
      icon={<MapPinIcon size={18} />}
      title="Jurisdiction"
      subtitle="Active analysis context"
    >
      {loading && (
        <div className="flex items-center gap-2 text-sm py-2" style={{ color: 'var(--smoke-500)' }}>
          <span
            className="w-2 h-2 rounded-full animate-odia-pulse"
            style={{ background: 'var(--gold-400)' }}
          />
          Loading configuration…
        </div>
      )}

      {error && !loading && (
        <div className="p-3 gem-edge" style={{ background: 'rgba(244, 63, 94, 0.08)' }}>
          <div className="flex items-start gap-2">
            <AlertCircleIcon size={16} style={{ color: 'var(--severity-critical)' }} className="mt-0.5" />
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--severity-critical)' }}>
                Jurisdiction unavailable
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--smoke-200)' }}>
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {info && !loading && info.loaded && (
        <div className="space-y-3">
          <DetailRow label="Name"          value={info.name} mono={false} strong />
          {info.state &&        <DetailRow label="State"         value={info.state} />}
          {info.country &&      <DetailRow label="Country"       value={info.country} />}
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
          <div className="pt-2" style={{ borderTop: '1px solid var(--gem-edge-gold)' }}>
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

      {info && !loading && !info.loaded && (
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
          <p className="text-xs mt-1 max-w-xs mx-auto" style={{ color: 'var(--smoke-500)' }}>
            Add a jurisdiction config file to enable location-aware
            analysis (agency mapping, local statute references). The
            "Seed Example Jurisdictions" trigger on the Automation page
            populates the user-writable config dir for you.
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
