/**
 * DetectorStatusCard — list of registered analysis detectors.
 *
 * The backend /detectors endpoint returns a flat list.  Here we:
 *   • humanise each name (snake_case → Title Case)
 *   • show how many anomaly types each detector can emit
 *   • render a pulsing green dot per detector to suggest "live"
 *   • provide a proper empty state instead of infinite "Loading..."
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { getAPIClient } from '@/lib/api/client';
import {
  AnomaliesIcon,
  AlertCircleIcon,
} from '@/components/base/Icons';
import type { DetectorInfo } from '@/lib/types/api';

function humanise(name: string): string {
  return name
    .split(/[_\s]+/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

export function DetectorStatusCard() {
  const [detectors, setDetectors] = useState<DetectorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAPIClient()
      .getDetectors()
      .then((res) => {
        if (!cancelled) setDetectors(res.detectors);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : 'Failed to load detectors');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const totalTypes = detectors.reduce(
    (sum, d) => sum + d.anomaly_types.length,
    0,
  );

  return (
    <Card
      variant="bordered"
      icon={<AnomaliesIcon size={18} />}
      title="Active Detectors"
      subtitle={
        loading
          ? 'Loading detector registry…'
          : `${detectors.length} detectors · ${totalTypes} anomaly types`
      }
      actions={
        detectors.length > 0 && (
          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium ring-1 ring-inset ring-emerald-600/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Online
          </span>
        )
      }
    >
      {loading && (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="h-8 rounded bg-slate-100 animate-odia-pulse"
            />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3">
          <div className="flex items-start gap-2">
            <AlertCircleIcon size={16} className="text-red-600 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-900">
                Cannot load detectors
              </p>
              <p className="text-xs text-red-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && detectors.length === 0 && (
        <div className="text-center py-6 text-sm text-slate-500">
          No detectors are currently registered.
        </div>
      )}

      {!loading && !error && detectors.length > 0 && (
        <ul className="divide-y divide-slate-100 -my-2 max-h-72 overflow-y-auto pr-1">
          {detectors.map((d) => (
            <li
              key={d.name}
              className="flex items-center justify-between gap-3 py-2.5"
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0" />
                <span className="text-sm font-medium text-slate-800 truncate">
                  {humanise(d.name)}
                </span>
              </div>
              <span
                className="text-xs font-mono text-slate-600 bg-slate-100 px-2 py-0.5 rounded flex-shrink-0"
                title={d.anomaly_types.join(', ')}
              >
                {d.anomaly_types.length}{' '}
                {d.anomaly_types.length === 1 ? 'type' : 'types'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
