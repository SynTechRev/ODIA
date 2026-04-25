/**
 * /ingest — legacy redirect to /upload (v2.7.4 W2).
 *
 * The Ingest page wrapped a single-file UploadPanel that was superseded
 * by the full Upload flow (drag-drop, multi-file, progress polling,
 * run-audit). Removed from sidebar nav in v2.7.4; the route now
 * client-redirects to /upload so any external bookmarks land on the
 * current intake surface instead of 404ing.
 */

'use client';

import { useEffect } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useAppNavigate } from '@/lib/navigation';

export default function IngestRedirectPage() {
  const nav = useAppNavigate();

  useEffect(() => {
    nav('/upload');
  }, [nav]);

  return (
    <DashboardLayout>
      <div className="hud-panel hud-panel-inset p-8 max-w-2xl mx-auto text-center">
        <h2 className="font-display text-xl font-semibold text-slate-100 mb-2">
          Redirecting to Upload…
        </h2>
        <p className="hud-subtext">
          The Ingest tab was consolidated into Upload. If your browser
          doesn&apos;t auto-redirect, click the Upload entry in the sidebar.
        </p>
      </div>
    </DashboardLayout>
  );
}
