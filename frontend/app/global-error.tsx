'use client';

/**
 * Global error boundary — catches any unhandled React render error at the root level.
 *
 * In Electron (file:// protocol) client-side navigation via next/router can fail
 * with a JS exception in certain edge cases.  Without this boundary the user sees
 * Next.js's raw "Application error" page with no way to recover.
 *
 * This boundary replaces that with a simple "Reload" prompt.
 */

import React from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            fontFamily: 'system-ui, sans-serif',
            background: '#f8fafc',
            color: '#1e293b',
            gap: '1rem',
            padding: '2rem',
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 12,
              background: '#fef3c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 24,
            }}
          >
            ⚠
          </div>
          <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0 }}>
            Something went wrong
          </h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0, textAlign: 'center', maxWidth: 360 }}>
            {error?.message ?? 'An unexpected error occurred while loading this page.'}
          </p>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
            <button
              onClick={reset}
              style={{
                padding: '0.5rem 1.25rem',
                borderRadius: 8,
                border: 'none',
                background: '#f59e0b',
                color: '#1c1917',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Try again
            </button>
            <button
              onClick={() => {
                // file:// apps need a hard path to the bundled index.html
                const loc = window.location.href;
                if (loc.startsWith('file://')) {
                  const root = loc.replace(/[^/]*$/, '').replace(/\/(upload|ingest|analysis|documents|results|anomalies|synthesis|rag|legal|orchestrator|automation|settings)\/$/, '/');
                  window.location.href = root + 'index.html';
                } else {
                  window.location.href = '/';
                }
              }}
              style={{
                padding: '0.5rem 1.25rem',
                borderRadius: 8,
                border: '1px solid #cbd5e1',
                background: 'white',
                color: '#1e293b',
                fontWeight: 600,
                fontSize: '0.875rem',
                cursor: 'pointer',
              }}
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
