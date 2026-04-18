/**
 * Dashboard Layout — fixed sidebar (desktop) + bottom tab bar (mobile).
 *
 * The sidebar uses inline SVG icons (see Icons.tsx) so the UI renders
 * correctly under file:// in Electron where emoji fonts and Google Fonts
 * are unavailable.
 */

'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { AppLink } from '@/lib/navigation';
import {
  DashboardIcon,
  UploadIcon,
  ResultsIcon,
  IngestIcon,
  AnalysisIcon,
  DocumentsIcon,
  AnomaliesIcon,
  OrchestratorIcon,
  SettingsIcon,
  OdiaMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  type IconProps,
} from '@/components/base/Icons';
import { isFileProtocol } from '@/lib/navigation';
import { getAPIClient } from '@/lib/api/client';

export interface DashboardLayoutProps {
  children: ReactNode;
}

interface NavItem {
  name: string;
  href: string;
  Icon: React.FC<IconProps>;
  group?: string;
}

// Grouped so the sidebar can render section headings — makes the
// information hierarchy readable rather than a flat dump of 9 links.
const sidebarNav: NavItem[] = [
  { name: 'Dashboard',     href: '/',              Icon: DashboardIcon,    group: 'Overview' },

  { name: 'Upload',        href: '/upload',        Icon: UploadIcon,       group: 'Workflow' },
  { name: 'Ingest',        href: '/ingest',        Icon: IngestIcon,       group: 'Workflow' },
  { name: 'Analysis',      href: '/analysis',      Icon: AnalysisIcon,     group: 'Workflow' },

  { name: 'Documents',     href: '/documents',     Icon: DocumentsIcon,    group: 'Evidence' },
  { name: 'Results',       href: '/results',       Icon: ResultsIcon,      group: 'Evidence' },
  { name: 'Anomalies',     href: '/anomalies',     Icon: AnomaliesIcon,    group: 'Evidence' },

  { name: 'Orchestrator',  href: '/orchestrator',  Icon: OrchestratorIcon, group: 'System' },
  { name: 'Settings',      href: '/settings',      Icon: SettingsIcon,     group: 'System' },
];

const mobileNav: NavItem[] = [
  { name: 'Home',     href: '/',           Icon: DashboardIcon },
  { name: 'Upload',   href: '/upload',     Icon: UploadIcon },
  { name: 'Results',  href: '/results',    Icon: ResultsIcon },
  { name: 'Docs',     href: '/documents',  Icon: DocumentsIcon },
  { name: 'Settings', href: '/settings',   Icon: SettingsIcon },
];

function isActive(href: string, pathname: string): boolean {
  return pathname === href || (href !== '/' && pathname.startsWith(href));
}

// ---------------------------------------------------------------------------

type BackendState = 'checking' | 'connected' | 'disconnected';

function useBackendStatus(): { state: BackendState; retry: () => void } {
  const [state, setState] = useState<BackendState>('checking');
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        await getAPIClient().health();
        if (!cancelled) setState('connected');
      } catch {
        if (!cancelled) setState('disconnected');
      }
    };
    check();
    const id = setInterval(check, 15_000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [tick]);

  return { state, retry: () => setTick((t) => t + 1) };
}

// ---------------------------------------------------------------------------

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { state: backendState, retry } = useBackendStatus();
  const [offline, setOffline] = useState(false);

  // Service-worker OFFLINE broadcast (web/PWA only — no-op in Electron)
  useEffect(() => {
    if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'OFFLINE') setOffline(true);
    };
    navigator.serviceWorker.addEventListener('message', handler);
    return () => navigator.serviceWorker.removeEventListener('message', handler);
  }, []);

  const current = sidebarNav.find((n) => isActive(n.href, pathname));
  const currentName = current?.name ?? 'O.D.I.A.';

  // Group sidebar items while preserving order
  const groups = sidebarNav.reduce<Record<string, NavItem[]>>((acc, item) => {
    const g = item.group ?? 'Other';
    if (!acc[g]) acc[g] = [];
    acc[g].push(item);
    return acc;
  }, {});
  const groupOrder = ['Overview', 'Workflow', 'Evidence', 'System'];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* ---- Offline banner -------------------------------------------- */}
      {offline && (
        <div className="fixed top-0 inset-x-0 z-50 bg-amber-500 text-slate-900 text-sm text-center py-2 px-4 shadow-md">
          <span className="font-medium">You are offline.</span> Cached pages are available.
          <button
            className="ml-3 underline hover:no-underline"
            onClick={() => setOffline(false)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ================================================================== */}
      {/* Desktop sidebar                                                     */}
      {/* ================================================================== */}
      <aside
        className="hidden md:flex fixed inset-y-0 left-0 w-64 flex-col bg-slate-950 text-slate-100 border-r border-slate-800 z-40"
        aria-label="Primary navigation"
      >
        {/* Brand */}
        <div className="flex items-center gap-3 h-16 px-5 bg-slate-900 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center justify-center w-9 h-9 rounded-md bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/30">
            <OdiaMarkIcon size={20} />
          </div>
          <div className="leading-tight">
            <div className="text-sm font-bold tracking-wide text-white">O.D.I.A.</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-400">
              Oraculus Decimus Intellect Analyst
            </div>
          </div>
        </div>

        {/* Navigation (scrollable) */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto" role="navigation">
          {groupOrder
            .filter((g) => groups[g])
            .map((group) => (
              <div key={group} className="mb-5 last:mb-0">
                <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-widest text-slate-500">
                  {group}
                </div>
                <ul className="space-y-0.5">
                  {groups[group].map(({ name, href, Icon }) => {
                    const active = isActive(href, pathname);
                    return (
                      <li key={name}>
                        <AppLink
                          href={href}
                          className={`
                            group relative flex items-center gap-3 px-3 py-2 rounded-md
                            text-sm font-medium transition-colors
                            ${active
                              ? 'bg-slate-800 text-white'
                              : 'text-slate-300 hover:bg-slate-900 hover:text-white'}
                          `}
                          aria-current={active ? 'page' : undefined}
                        >
                          {/* Active indicator bar */}
                          <span
                            className={`
                              absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r
                              ${active ? 'bg-amber-500' : 'bg-transparent group-hover:bg-slate-700'}
                            `}
                            aria-hidden="true"
                          />
                          <Icon size={18} className={active ? 'text-amber-400' : 'text-slate-400 group-hover:text-slate-200'} />
                          <span>{name}</span>
                        </AppLink>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
        </nav>

        {/* Backend status pill + version */}
        <div className="px-4 py-3 border-t border-slate-800 flex-shrink-0">
          <button
            onClick={retry}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-md bg-slate-900 hover:bg-slate-800 transition-colors text-left group"
            title="Click to re-check backend connection"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span
                className={`
                  inline-block w-2 h-2 rounded-full flex-shrink-0
                  ${backendState === 'connected'   ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]' : ''}
                  ${backendState === 'disconnected' ? 'bg-red-500' : ''}
                  ${backendState === 'checking'     ? 'bg-amber-400 animate-odia-pulse' : ''}
                `}
                aria-hidden="true"
              />
              <span className="text-xs font-medium text-slate-200 truncate">
                {backendState === 'connected'    && 'Backend online'}
                {backendState === 'disconnected' && 'Backend offline'}
                {backendState === 'checking'     && 'Connecting…'}
              </span>
            </div>
            <span className="text-[10px] text-slate-500 group-hover:text-slate-300">
              v2.2.1
            </span>
          </button>
        </div>
      </aside>

      {/* ================================================================== */}
      {/* Main content                                                        */}
      {/* ================================================================== */}
      <main className={`md:pl-64 ${offline ? 'pt-10' : ''}`}>
        {/* Desktop top bar */}
        <header className="hidden md:flex sticky top-0 z-30 h-14 bg-slate-900 border-b border-slate-700/60 items-center justify-between px-6 shadow-[0_1px_0_rgba(255,255,255,0.04),0_4px_16px_rgba(0,0,0,0.24)]">
          <div className="flex items-center gap-2.5">
            {/* Back / forward — only shown in Electron where hard-nav builds real history */}
            {isFileProtocol() && (
              <div className="flex items-center gap-0.5 mr-0.5">
                <button
                  onClick={() => window.history.back()}
                  className="p-1.5 rounded text-slate-500 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                  title="Go back"
                  aria-label="Go back"
                >
                  <ChevronLeftIcon size={15} />
                </button>
                <button
                  onClick={() => window.history.forward()}
                  className="p-1.5 rounded text-slate-500 hover:bg-slate-800 hover:text-slate-200 transition-colors"
                  title="Go forward"
                  aria-label="Go forward"
                >
                  <ChevronRightIcon size={15} />
                </button>
              </div>
            )}
            {current?.Icon && (
              <span className="flex items-center justify-center w-7 h-7 rounded bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20 flex-shrink-0">
                <current.Icon size={15} />
              </span>
            )}
            <div className="flex flex-col leading-none">
              <h2 className="text-sm font-semibold text-white tracking-wide">
                {currentName}
              </h2>
              <span className="text-[10px] text-slate-500 uppercase tracking-widest mt-0.5">
                Oraculus Intelligence Platform
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={retry}
              className={`
                flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium
                border transition-colors cursor-pointer
                ${backendState === 'connected'
                  ? 'bg-emerald-950/60 border-emerald-700/40 text-emerald-400 hover:bg-emerald-900/60'
                  : backendState === 'disconnected'
                  ? 'bg-red-950/60 border-red-700/40 text-red-400 hover:bg-red-900/60'
                  : 'bg-amber-950/40 border-amber-700/30 text-amber-400'}
              `}
              title="Click to re-check backend connection"
            >
              <span
                className={`
                  inline-block w-1.5 h-1.5 rounded-full flex-shrink-0
                  ${backendState === 'connected'    ? 'bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.8)]' : ''}
                  ${backendState === 'disconnected' ? 'bg-red-400' : ''}
                  ${backendState === 'checking'     ? 'bg-amber-400 animate-odia-pulse' : ''}
                `}
                aria-hidden="true"
              />
              {backendState === 'connected'    && 'System Online'}
              {backendState === 'disconnected' && 'System Offline'}
              {backendState === 'checking'     && 'Connecting…'}
            </button>
          </div>
        </header>

        {/* Mobile top bar */}
        <header className="md:hidden sticky top-0 z-30 bg-slate-950 text-white border-b border-slate-800">
          <div className="px-4 py-3 flex items-center gap-2">
            <div className="flex items-center justify-center w-7 h-7 rounded bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/30">
              <OdiaMarkIcon size={16} />
            </div>
            <h2 className="text-base font-semibold">{currentName}</h2>
          </div>
        </header>

        {/* Page content — bottom padding accounts for mobile tab bar */}
        <div className="p-4 md:p-8 pb-24 md:pb-12 animate-odia-fade">
          {children}
        </div>
      </main>

      {/* ================================================================== */}
      {/* Mobile bottom tab bar                                              */}
      {/* ================================================================== */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-slate-200 z-40 shadow-[0_-2px_12px_rgba(15,23,42,0.08)]"
        role="navigation"
        aria-label="Primary navigation"
      >
        <div className="flex">
          {mobileNav.map(({ name, href, Icon }) => {
            const active = isActive(href, pathname);
            return (
              <AppLink
                key={name}
                href={href}
                className={`
                  flex-1 flex flex-col items-center justify-center py-2.5 gap-1
                  text-[10px] font-medium transition-colors
                  ${active ? 'text-amber-600' : 'text-slate-500 hover:text-slate-700'}
                `}
                aria-current={active ? 'page' : undefined}
              >
                <Icon size={20} />
                <span>{name}</span>
              </AppLink>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
