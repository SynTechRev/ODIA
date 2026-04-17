'use client';

import { useEffect } from 'react';

/**
 * Register the service worker, but only when served over http(s).
 *
 * Under file:// (Electron packaged mode) service workers aren't supported
 * and calling register() would throw a DOMException.  The error is caught
 * below anyway, but we skip the attempt entirely to keep the console
 * clean and avoid a misleading error message on every app launch.
 *
 * We also skip when window.odiaDesktop is present — belt and braces — so
 * a future dev mode served over http://localhost still avoids registering
 * a PWA on top of the desktop shell.
 */
export function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.location.protocol === 'file:') return;
    if (window.odiaDesktop?.isDesktop) return;
    if (!('serviceWorker' in navigator)) return;

    const onLoad = () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // SW registration failure is non-fatal
      });
    };

    window.addEventListener('load', onLoad);
    return () => window.removeEventListener('load', onLoad);
  }, []);

  return null;
}
