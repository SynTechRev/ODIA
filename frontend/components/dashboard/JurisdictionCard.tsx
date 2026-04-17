/**
 * JurisdictionCard — current jurisdiction configuration summary.
 *
 * Fetches GET /config/jurisdiction on mount.  Distinguishes three UI
 * states:
 *   1. Loading
 *   2. Loaded + configured — structured detail table
 *   3. Loaded + not configured — empty state with helper text
 *   4. Error — inline error with backend context
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
        <div className="flex items-center gap-2 text-sm text-slate-500 py-2">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-odia-pulse" />
          Loading configuration…
        </div>
      )}

      {error && !loading && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3">
          <div className="flex items-start gap-2">
            <AlertCircleIcon size={16} className="text-red-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-900">
                Jurisdiction unavailable
              </p>
              <p className="text-xs text-red-700 mt-1">{error}</p>
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
              value={
                <span className="capitalize">{info.meeting_type}</span>
              }
            />
          )}
          <DetailRow
            label="Agencies"
            value={
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 text-xs font-medium ring-1 ring-inset ring-amber-600/20">
                {info.agency_count}
              </span>
            }
          />
          <div className="pt-2 border-t border-slate-100">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-700">
              <CheckCircleIcon size={12} />
              Configuration loaded
            </span>
          </div>
        </div>
      )}

      {info && !loading && !info.loaded && (
        <div className="text-center py-6">
          <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center mx-auto mb-3">
            <MapPinIcon size={20} />
          </div>
          <p className="text-sm font-medium text-slate-700">
            No jurisdiction configured
          </p>
          <p className="text-xs text-slate-500 mt-1 max-w-xs mx-auto">
            Add a jurisdiction config file to enable location-aware
            analysis (agency mapping, local statute references).
          </p>
          <div className="inline-flex items-center gap-1.5 mt-3 px-2.5 py-1 rounded bg-slate-100 font-mono text-xs text-slate-700">
            config/jurisdiction.json
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
      <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <span
        className={`
          text-right min-w-0 truncate
          ${mono ? 'font-mono text-xs' : 'text-sm'}
          ${strong ? 'font-semibold text-slate-900' : 'text-slate-800'}
        `}
      >
        {value}
      </span>
    </div>
  );
}
