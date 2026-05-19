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
  SynthesisIcon,
  OrchestratorIcon,
  AutomationIcon,
  SettingsIcon,
  OraculusMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  type IconProps,
} from '@/components/base/Icons';
import { isFileProtocol } from '@/lib/navigation';
import { getAPIClient } from '@/lib/api/client';
import { InstallPrompt } from '@/components/pwa/InstallPrompt';

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
  // Ingest removed in v2.7.4 W2 — Upload is the canonical document-intake
  // surface (drag-drop + multi-file + run-audit). The /ingest route now
  // redirects to /upload to preserve any external bookmarks.
  { name: 'Analysis',      href: '/analysis',      Icon: AnalysisIcon,     group: 'Workflow' },

  { name: 'Documents',     href: '/documents',     Icon: DocumentsIcon,    group: 'Evidence' },
  { name: 'Results',       href: '/results',       Icon: ResultsIcon,      group: 'Evidence' },
  { name: 'Anomalies',     href: '/anomalies',     Icon: AnomaliesIcon,    group: 'Evidence' },
  { name: 'Synthesis',     href: '/synthesis',     Icon: SynthesisIcon,    group: 'Evidence' },

  { name: 'Orchestrator',  href: '/orchestrator',  Icon: OrchestratorIcon, group: 'System' },
  { name: 'Automation',    href: '/automation',    Icon: AutomationIcon,   group: 'System' },
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

// v2.7.3 V2: fallback when /api/v1/health doesn't return odia_version
// (older backends) or when the check hasn't completed yet. Updated on
// every release.
const ODIA_VERSION_FALLBACK = 'v3.2.4';

function useBackendStatus(): {
  state: BackendState;
  version: string;
  retry: () => void;
} {
  const [state, setState] = useState<BackendState>('checking');
  const [version, setVersion] = useState<string>(ODIA_VERSION_FALLBACK);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      try {
        const health = await getAPIClient().health();
        if (cancelled) return;
        setState('connected');
        if (health.odia_version) {
          const raw = health.odia_version.trim();
          // Preserve leading 'v' when present, otherwise prepend it.
          setVersion(raw.startsWith('v') ? raw : `v${raw}`);
        }
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

  return { state, version, retry: () => setTick((t) => t + 1) };
}

// ---------------------------------------------------------------------------

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const { state: backendState, version: backendVersion, retry } = useBackendStatus();
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
    <div className="min-h-screen text-[var(--smoke-100)]" style={{ background: 'var(--background)' }}>
      {/* ---- Offline banner -------------------------------------------- */}
      {offline && (
        <div
          className="fixed top-0 inset-x-0 z-50 text-sm text-center py-2 px-4"
          style={{
            background: 'linear-gradient(90deg, var(--gold-500), var(--gold-300), var(--gold-500))',
            color: '#1a1404',
            boxShadow: '0 2px 12px -2px rgba(216, 177, 60, 0.45)',
          }}
        >
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
        className="hidden md:flex fixed inset-y-0 left-0 w-64 flex-col z-40 hud-rail-right hud-scanlines"
        style={{
          background:
            'linear-gradient(180deg, var(--smoke-950) 0%, var(--smoke-900) 60%, var(--smoke-950) 100%)',
          color: 'var(--smoke-100)',
        }}
        aria-label="Primary navigation"
      >
        {/* Brand — gold-edged gem badge + gradient wordmark */}
        <div
          className="flex items-center gap-3 h-16 px-5 flex-shrink-0 hud-rail-bottom"
          style={{ background: 'rgba(7, 7, 10, 0.85)' }}
        >
          <div
            className="flex items-center justify-center w-9 h-9 flex-shrink-0 gem-edge"
            style={{
              background:
                'linear-gradient(135deg, rgba(216, 177, 60, 0.18) 0%, rgba(31, 232, 143, 0.12) 100%)',
              color: 'var(--gold-200)',
            }}
          >
            <OraculusMarkIcon size={20} />
          </div>
          <div className="leading-tight min-w-0">
            <div
              className="text-sm font-bold tracking-[0.2em] bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  'linear-gradient(90deg, var(--gold-200), var(--neon-emerald), var(--gold-300))',
              }}
            >
              O.D.I.A.
            </div>
            <div
              className="text-[9px] uppercase tracking-[0.25em] truncate mt-0.5"
              style={{ color: 'var(--smoke-500)' }}
            >
              Forensic Audit Platform
            </div>
          </div>
        </div>

        {/* Navigation (scrollable) */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto" role="navigation">
          {groupOrder
            .filter((g) => groups[g])
            .map((group) => (
              <div key={group} className="mb-5 last:mb-0">
                <div
                  className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-widest"
                  style={{ color: 'var(--gold-400)' }}
                >
                  {group}
                </div>
                <ul className="space-y-0.5">
                  {groups[group].map(({ name, href, Icon }) => {
                    const active = isActive(href, pathname);
                    return (
                      <li key={name}>
                        <AppLink
                          href={href}
                          className="group relative flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                          style={{
                            background: active
                              ? 'linear-gradient(90deg, rgba(31, 232, 143, 0.10), rgba(216, 177, 60, 0.08))'
                              : 'transparent',
                            color: active ? 'var(--neon-emerald)' : 'var(--smoke-300)',
                            boxShadow: active
                              ? 'inset 0 0 0 1px rgba(216, 177, 60, 0.30), 0 0 18px -8px var(--neon-emerald)'
                              : 'none',
                          }}
                          aria-current={active ? 'page' : undefined}
                        >
                          {/* Active indicator bar — gold left edge */}
                          <span
                            className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-r"
                            style={{
                              background: active
                                ? 'linear-gradient(180deg, var(--gold-200), var(--neon-emerald), var(--gold-200))'
                                : 'transparent',
                              boxShadow: active ? '0 0 8px var(--neon-emerald)' : 'none',
                            }}
                            aria-hidden="true"
                          />
                          <Icon
                            size={18}
                            className="transition-colors"
                            style={{
                              color: active
                                ? 'var(--neon-emerald)'
                                : 'var(--smoke-500)',
                            }}
                          />
                          <span>{name}</span>
                        </AppLink>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
        </nav>

        {/* Backend status pill + version — gem-edged */}
        <div className="px-4 py-3 flex-shrink-0" style={{ borderTop: '1px solid var(--gem-edge-gold)' }}>
          <button
            onClick={retry}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 transition-all text-left group gem-edge"
            style={{ background: 'rgba(14, 14, 20, 0.85)' }}
            title="Click to re-check backend connection"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                style={{
                  background:
                    backendState === 'connected'
                      ? 'var(--neon-emerald)'
                      : backendState === 'disconnected'
                        ? 'var(--severity-critical)'
                        : 'var(--gold-400)',
                  boxShadow:
                    backendState === 'connected'
                      ? '0 0 10px var(--neon-emerald)'
                      : backendState === 'disconnected'
                        ? '0 0 8px var(--severity-critical)'
                        : '0 0 6px var(--gold-400)',
                  animation: backendState === 'checking' ? 'odia-pulse 1.4s ease-in-out infinite' : 'none',
                }}
                aria-hidden="true"
              />
              <span
                className="text-xs font-medium truncate"
                style={{ color: 'var(--smoke-100)' }}
              >
                {backendState === 'connected'    && 'Backend online'}
                {backendState === 'disconnected' && 'Backend offline'}
                {backendState === 'checking'     && 'Connecting…'}
              </span>
            </div>
            <span
              className="text-[10px] hud-num group-hover:text-[var(--neon-emerald)] transition-colors"
              style={{ color: 'var(--gold-300)' }}
            >
              {backendVersion}
            </span>
          </button>
        </div>
      </aside>

      {/* ================================================================== */}
      {/* Main content                                                        */}
      {/* ================================================================== */}
      <main className={`md:pl-64 ${offline ? 'pt-10' : ''}`}>
        {/* Desktop top bar */}
        <header
          className="hidden md:flex sticky top-0 z-30 h-14 items-center justify-between px-6 hud-rail-bottom hud-scanlines"
          style={{ background: 'rgba(7, 7, 10, 0.92)', backdropFilter: 'blur(8px)' }}
        >
          <div className="flex items-center gap-2.5">
            {/* Back / forward — only shown in Electron where hard-nav builds real history */}
            {isFileProtocol() && (
              <div className="flex items-center gap-0.5 mr-0.5">
                <button
                  onClick={() => window.history.back()}
                  className="p-1.5 rounded transition-colors"
                  style={{ color: 'var(--smoke-500)' }}
                  title="Go back"
                  aria-label="Go back"
                >
                  <ChevronLeftIcon size={15} />
                </button>
                <button
                  onClick={() => window.history.forward()}
                  className="p-1.5 rounded transition-colors"
                  style={{ color: 'var(--smoke-500)' }}
                  title="Go forward"
                  aria-label="Go forward"
                >
                  <ChevronRightIcon size={15} />
                </button>
              </div>
            )}
            {current?.Icon && (
              <span
                className="flex items-center justify-center w-7 h-7 flex-shrink-0 gem-edge"
                style={{
                  background: 'rgba(31, 232, 143, 0.12)',
                  color: 'var(--neon-emerald)',
                }}
              >
                <current.Icon size={15} />
              </span>
            )}
            <div className="flex flex-col leading-none">
              <h2
                className="text-sm font-semibold tracking-[0.15em] uppercase bg-clip-text text-transparent"
                style={{
                  backgroundImage:
                    'linear-gradient(90deg, var(--smoke-100), var(--gold-200), var(--neon-emerald))',
                }}
              >
                {currentName}
              </h2>
              <span
                className="text-[9px] uppercase tracking-[0.25em] mt-1"
                style={{ color: 'var(--gold-500)' }}
              >
                Forensic Audit Platform
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={retry}
              className="flex items-center gap-1.5 px-3 py-1 text-[11px] font-medium transition-all cursor-pointer gem-edge"
              style={{
                background: 'rgba(14, 14, 20, 0.85)',
                color:
                  backendState === 'connected'
                    ? 'var(--neon-emerald)'
                    : backendState === 'disconnected'
                      ? 'var(--severity-critical)'
                      : 'var(--gold-300)',
              }}
              title="Click to re-check backend connection"
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full flex-shrink-0"
                style={{
                  background:
                    backendState === 'connected'
                      ? 'var(--neon-emerald)'
                      : backendState === 'disconnected'
                        ? 'var(--severity-critical)'
                        : 'var(--gold-400)',
                  boxShadow:
                    backendState === 'connected'
                      ? '0 0 10px var(--neon-emerald)'
                      : backendState === 'disconnected'
                        ? '0 0 6px var(--severity-critical)'
                        : '0 0 6px var(--gold-400)',
                  animation: backendState === 'checking' ? 'odia-pulse 1.4s ease-in-out infinite' : 'none',
                }}
                aria-hidden="true"
              />
              {backendState === 'connected'    && 'System Online'}
              {backendState === 'disconnected' && 'System Offline'}
              {backendState === 'checking'     && 'Connecting…'}
            </button>
          </div>
        </header>

        {/* Mobile top bar */}
        <header
          className="md:hidden sticky top-0 z-30 hud-rail-bottom"
          style={{ background: 'rgba(7, 7, 10, 0.92)' }}
        >
          <div className="px-4 py-3 flex items-center gap-2">
            <div
              className="flex items-center justify-center w-7 h-7 gem-edge"
              style={{
                background: 'rgba(216, 177, 60, 0.12)',
                color: 'var(--gold-200)',
              }}
            >
              <OraculusMarkIcon size={16} />
            </div>
            <h2
              className="text-base font-semibold tracking-wider uppercase bg-clip-text text-transparent"
              style={{
                backgroundImage:
                  'linear-gradient(90deg, var(--smoke-100), var(--neon-emerald), var(--gold-200))',
              }}
            >
              {currentName}
            </h2>
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
        className="md:hidden fixed bottom-0 inset-x-0 z-40"
        style={{
          background: 'rgba(7, 7, 10, 0.96)',
          borderTop: '1px solid var(--gem-edge-gold)',
          boxShadow:
            '0 -2px 16px rgba(31, 232, 143, 0.18), inset 0 1px 0 rgba(216, 177, 60, 0.20)',
        }}
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
                className="flex-1 flex flex-col items-center justify-center min-h-[56px] py-2.5 gap-1 text-[10px] font-medium transition-colors"
                style={{
                  color: active ? 'var(--neon-emerald)' : 'var(--smoke-500)',
                  textShadow: active ? '0 0 8px var(--neon-emerald)' : 'none',
                }}
                aria-current={active ? 'page' : undefined}
              >
                <Icon size={20} />
                <span>{name}</span>
              </AppLink>
            );
          })}
        </div>
      </nav>

      {/* PWA install prompt — mobile only, suppressed in standalone/Electron */}
      <InstallPrompt />
    </div>
  );
}
