/**
 * JurisdictionCard - Displays current jurisdiction configuration from the backend.
 *
 * Fetches from GET /config/jurisdiction on mount and renders a summary of the
 * loaded jurisdiction (or a "not configured" state if none is loaded).
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '../base/Card';
import { getAPIClient } from '@/lib/api/client';
import type { JurisdictionInfo } from '@/lib/types/api';

export function JurisdictionCard() {
  const [info, setInfo] = useState<JurisdictionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const client = getAPIClient();
    client
      .getJurisdiction()
      .then(setInfo)
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load jurisdiction'),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <Card title="Jurisdiction" variant="bordered">
      <div className="space-y-3">
        {loading && (
          <div className="text-sm text-gray-500">Loading jurisdiction config...</div>
        )}

        {error && (
          <div className="flex items-center gap-2 text-sm text-red-600">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {info && !loading && (
          <>
            {info.loaded ? (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Name</span>
                  <span className="font-medium text-gray-900">{info.name}</span>
                </div>

                {info.state && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">State</span>
                    <span className="text-sm text-gray-900">{info.state}</span>
                  </div>
                )}

                {info.country && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Country</span>
                    <span className="text-sm text-gray-900">{info.country}</span>
                  </div>
                )}

                {info.meeting_type && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Meeting Type</span>
                    <span className="text-sm text-gray-900 capitalize">
                      {info.meeting_type}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Agencies</span>
                  <span className="text-sm font-medium text-blue-700">
                    {info.agency_count}
                  </span>
                </div>

                <div className="pt-1 border-t border-gray-100">
                  <span className="inline-flex items-center gap-1 text-xs text-green-700 font-medium">
                    <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
                    Config loaded
                  </span>
                </div>
              </>
            ) : (
              <div className="text-center py-4">
                <div className="text-3xl mb-2">🗺️</div>
                <p className="text-sm text-gray-500">
                  No jurisdiction configured.
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Add <span className="font-mono">config/jurisdiction.json</span> to enable
                  jurisdiction-aware analysis.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
}
