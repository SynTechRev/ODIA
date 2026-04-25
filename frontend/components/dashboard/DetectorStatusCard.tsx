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
          <span
            className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium gem-edge"
            style={{
              color: 'var(--neon-emerald)',
              background: 'rgba(31, 232, 143, 0.10)',
            }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{
                background: 'var(--neon-emerald)',
                boxShadow: '0 0 6px var(--neon-emerald)',
              }}
            />
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
              className="h-8 animate-odia-pulse"
              style={{ background: 'rgba(216, 177, 60, 0.08)' }}
            />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="p-3 gem-edge" style={{ background: 'rgba(244, 63, 94, 0.08)' }}>
          <div className="flex items-start gap-2">
            <AlertCircleIcon size={16} style={{ color: 'var(--severity-critical)' }} className="mt-0.5" />
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--severity-critical)' }}>
                Cannot load detectors
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--smoke-200)' }}>
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && detectors.length === 0 && (
        <div className="text-center py-6 text-sm" style={{ color: 'var(--smoke-500)' }}>
          No detectors are currently registered.
        </div>
      )}

      {!loading && !error && detectors.length > 0 && (
        <ul
          className="-my-2 max-h-72 overflow-y-auto pr-1"
          style={{ borderTop: '1px solid var(--gem-edge-gold)' }}
        >
          {detectors.map((d) => (
            <li
              key={d.name}
              className="flex items-center justify-between gap-3 py-2.5"
              style={{ borderBottom: '1px solid rgba(216, 177, 60, 0.18)' }}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{
                    background: 'var(--neon-emerald)',
                    boxShadow: '0 0 6px var(--neon-emerald)',
                  }}
                />
                <span
                  className="text-sm font-medium truncate"
                  style={{ color: 'var(--smoke-100)' }}
                >
                  {humanise(d.name)}
                </span>
              </div>
              <span
                className="text-xs font-mono px-2 py-0.5 flex-shrink-0 gem-edge"
                style={{
                  color: 'var(--gold-200)',
                  background: 'rgba(216, 177, 60, 0.08)',
                }}
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
