/**
 * SystemStatusCard — backend health, version, connection state.
 *
 * Hits GET /api/v1/health every 30 s.  When the backend is unreachable
 * (common in Electron if the Python subprocess crashed), shows a clear
 * actionable error state instead of spinning "Checking..." forever.
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
        {/* Status row */}
        <div className="flex items-center justify-between">
          <span className="text-slate-600">Backend</span>
          {phase === 'loading' && !health && (
            <span className="inline-flex items-center gap-1.5 text-slate-500">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-odia-pulse" />
              <span className="text-sm">Checking…</span>
            </span>
          )}
          {isHealthy && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium ring-1 ring-inset ring-emerald-600/20">
              <CheckCircleIcon size={12} />
              Healthy
            </span>
          )}
          {phase === 'error' && (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-50 text-red-700 text-xs font-medium ring-1 ring-inset ring-red-600/20">
              <AlertCircleIcon size={12} />
              Unreachable
            </span>
          )}
        </div>

        {/* Version + endpoint */}
        {health && (
          <>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">API Version</span>
              <span className="font-mono text-xs text-slate-800 bg-slate-100 px-2 py-0.5 rounded">
                {health.version}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Endpoint</span>
              <span className="font-mono text-xs text-slate-800 truncate max-w-[220px]">
                {getAPIClient().baseURL}
              </span>
            </div>
          </>
        )}

        {/* Error detail */}
        {phase === 'error' && (
          <div className="rounded-md border border-red-200 bg-red-50 p-3">
            <div className="flex items-start gap-2">
              <AlertCircleIcon size={16} className="text-red-600 flex-shrink-0 mt-0.5" />
              <div className="min-w-0">
                <p className="text-sm font-medium text-red-900">
                  Cannot reach backend
                </p>
                <p className="text-xs text-red-700 mt-1 break-words">
                  {error}
                </p>
                <p className="text-xs text-red-700 mt-2">
                  The Python analysis engine may have failed to start. Try
                  restarting O.D.I.A., or check the application logs.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Last checked */}
        {checkedAt && (
          <div className="pt-3 border-t border-slate-100 text-xs text-slate-500">
            Last checked {checkedAt.toLocaleTimeString()}
          </div>
        )}
      </div>
    </Card>
  );
}
