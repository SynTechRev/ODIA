/**
 * SystemStatusCard - Displays system health and status
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { getAPIClient } from '@/lib/api/client';
import type { HealthResponse } from '@/lib/types/api';

export function SystemStatusCard() {
  const [status, setStatus] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        setLoading(true);
        const client = getAPIClient();
        const health = await client.health();
        setStatus(health);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to check system status');
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card title="System Status" variant="bordered">
      <div className="space-y-4">
        {loading && (
          <div className="text-gray-500">Checking system status...</div>
        )}

        {error && (
          <div className="flex items-center text-red-600">
            <span className="mr-2">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {status && !loading && (
          <>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Backend Status</span>
              <span
                className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${status.status === 'healthy'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                  }
                `}
              >
                {status.status === 'healthy' ? '✓ Healthy' : '✗ Unhealthy'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-gray-700">API Version</span>
              <span className="font-mono text-sm">{status.version}</span>
            </div>

            <div className="pt-2 border-t border-gray-200">
              <span className="text-xs text-gray-500">
                Last checked: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </>
        )}
      </div>
    </Card>
  );
}
