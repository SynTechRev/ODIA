/**
 * DetectorStatusCard - Shows the list of active detectors from GET /detectors.
 *
 * Displays each registered detector with its name and anomaly type count,
 * providing a quick at-a-glance view of what the analysis pipeline can detect.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { getAPIClient } from '@/lib/api/client';
import type { DetectorInfo } from '@/lib/types/api';

export function DetectorStatusCard() {
  const [detectors, setDetectors] = useState<DetectorInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const client = getAPIClient();
    client
      .getDetectors()
      .then((res) => setDetectors(res.detectors))
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load detectors'),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <Card
      title={`Active Detectors${detectors.length > 0 ? ` (${detectors.length})` : ''}`}
      variant="bordered"
    >
      <div className="space-y-2">
        {loading && (
          <div className="text-sm text-gray-500">Loading detectors...</div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && detectors.length === 0 && (
          <div className="text-sm text-gray-500">No detectors available.</div>
        )}

        {detectors.map((detector) => (
          <div
            key={detector.name}
            className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0"
          >
            <div className="flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
              <span className="text-sm font-medium text-gray-800 capitalize">
                {detector.name.replace(/_/g, ' ')}
              </span>
            </div>
            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {detector.anomaly_types.length}{' '}
              {detector.anomaly_types.length === 1 ? 'type' : 'types'}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
