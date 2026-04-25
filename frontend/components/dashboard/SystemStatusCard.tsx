/**
 * SystemStatusCard — backend health, version, connection state.
 *
 * Hits GET /api/v1/health every 30 s.  When the backend is unreachable
 * (common in Electron if the Python subprocess crashed), shows a clear
 * actionable error state instead of spinning "Checking..." forever.
 *
 * v2.7.7 Y5 — pastel light-theme color chains replaced with gemstone
 * tokens; healthy state uses neon-emerald, error uses severity-critical.
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { Button } from '../base/Button';
import { getAPIClient } from '@/lib/api/client';
import {
  ShieldIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  RefreshIcon,
} from '@/components/base/Icons';
import type { HealthResponse } from '@/lib/types/api';

type Phase = 'loading' | 'ok' | 'error';

export function SystemStatusCard() {
  const [phase, setPhase] = useState<Phase>('loading');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checkedAt, setCheckedAt] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    setPhase('loading');
    setError(null);
    try {
      const data = await getAPIClient().health();
      setHealth(data);
      setCheckedAt(new Date());
      setPhase('ok');
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Backend unreachable',
      );
      setCheckedAt(new Date());
      setPhase('error');
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const id = setInterval(checkHealth, 30_000);
    return () => clearInterval(id);
  }, [checkHealth]);

  const isHealthy = phase === 'ok' && health?.status === 'healthy';

  return (
    <Card
      variant="bordered"
      icon={<ShieldIcon size={18} />}
      title="System Status"
      subtitle="Local Python backend"
      actions={
        <Button
          size="sm"
          variant="ghost"
          onClick={checkHealth}
          loading={phase === 'loading'}
          icon={<RefreshIcon size={14} />}
          aria-label="Refresh backend status"
        >
          Refresh
        </Button>
      }
    >
      <div className="space-y-4">
        <Row label="Backend">
          {phase === 'loading' && !health && (
            <span className="inline-flex items-center gap-1.5" style={{ color: 'var(--smoke-500)' }}>
              <span
                className="w-2 h-2 rounded-full animate-odia-pulse"
                style={{ background: 'var(--gold-400)' }}
              />
              <span className="text-sm">Checking…</span>
            </span>
          )}
          {isHealthy && (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium gem-edge"
              style={{
                color: 'var(--neon-emerald)',
                background: 'rgba(31, 232, 143, 0.10)',
              }}
            >
              <CheckCircleIcon size={12} />
              Healthy
            </span>
          )}
          {phase === 'error' && (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium gem-edge"
              style={{
                color: 'var(--severity-critical)',
                background: 'rgba(244, 63, 94, 0.10)',
              }}
            >
              <AlertCircleIcon size={12} />
              Unreachable
            </span>
          )}
        </Row>

        {health && (
          <>
            <Row label="API Version">
              <span
                className="font-mono text-xs px-2 py-0.5 gem-edge"
                style={{
                  color: 'var(--gold-200)',
                  background: 'rgba(216, 177, 60, 0.10)',
                }}
              >
                {health.version}
              </span>
            </Row>
            <Row label="Endpoint">
              <span
                className="font-mono text-xs truncate max-w-[220px]"
                style={{ color: 'var(--smoke-300)' }}
              >
                {getAPIClient().baseURL}
              </span>
            </Row>
          </>
        )}

        {phase === 'error' && (
          <div
            className="p-3 gem-edge"
            style={{ background: 'rgba(244, 63, 94, 0.08)' }}
          >
            <div className="flex items-start gap-2">
              <AlertCircleIcon
                size={16}
                className="flex-shrink-0 mt-0.5"
                style={{ color: 'var(--severity-critical)' }}
              />
              <div className="min-w-0">
                <p className="text-sm font-medium" style={{ color: 'var(--severity-critical)' }}>
                  Cannot reach backend
                </p>
                <p className="text-xs mt-1 break-words" style={{ color: 'var(--smoke-200)' }}>
                  {error}
                </p>
                <p className="text-xs mt-2" style={{ color: 'var(--smoke-300)' }}>
                  The Python analysis engine may have failed to start. Try
                  restarting O.D.I.A., or check the application logs.
                </p>
              </div>
            </div>
          </div>
        )}

        {checkedAt && (
          <div
            className="pt-3 text-xs"
            style={{
              borderTop: '1px solid var(--gem-edge-gold)',
              color: 'var(--smoke-500)',
            }}
          >
            Last checked {checkedAt.toLocaleTimeString()}
          </div>
        )}
      </div>
    </Card>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span style={{ color: 'var(--smoke-300)' }}>{label}</span>
      {children}
    </div>
  );
}
