/**
 * Dashboard Layout Component - Main application layout
 *
 * Desktop: fixed sidebar (left)
 * Mobile:  bottom tab bar (5 primary tabs)
 */

'use client';

import React, { ReactNode, useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

export interface DashboardLayoutProps {
  children: ReactNode;
}

const sidebarNav = [
  { name: 'Dashboard',    href: '/',            icon: '⬡' },
  { name: 'Upload',       href: '/upload',       icon: '↑' },
  { name: 'Results',      href: '/results',      icon: '≡' },
  { name: 'Ingest',       href: '/ingest',       icon: '▤' },
  { name: 'Analysis',     href: '/analysis',     icon: '◎' },
  { name: 'Documents',    href: '/documents',    icon: '▣' },
  { name: 'Anomalies',    href: '/anomalies',    icon: '△' },
  { name: 'Orchestrator', href: '/orchestrator', icon: '⊛' },
  { name: 'Settings',     href: '/settings',     icon: '✦' },
];

const tabNav = [
  { name: 'Home',     href: '/',         icon: '⬡' },
  { name: 'Upload',   href: '/upload',   icon: '↑' },
  { name: 'Results',  href: '/results',  icon: '≡' },
  { name: 'Docs',     href: '/documents',icon: '▣' },
  { name: 'Settings', href: '/settings', icon: '✦' },
];

function isActive(href: string, pathname: string): boolean {
  return pathname === href || (href !== '/' && pathname.startsWith(href));
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'OFFLINE') setOffline(true);
    };
    navigator.serviceWorker.addEventListener('message', handler);
    return () => navigator.serviceWorker.removeEventListener('message', handler);
  }, []);

  const currentPage =
    sidebarNav.find((item) => isActive(item.href, pathname))?.name ?? 'O.D.I.A.';

  return (
    <div className="min-h-screen" style={{ background: 'var(--background)' }}>

      {/* Offline banner */}
      {offline && (
        <div
          className="fixed top-0 inset-x-0 z-50 text-sm text-center py-2 px-4 font-medium"
          style={{ background: 'var(--warning)', color: '#000' }}
        >
          Offline mode — cached pages available.
          <button className="ml-3 underline opacity-80" onClick={() => setOffline(false)}>
            Dismiss
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Desktop sidebar                                                      */}
      {/* ------------------------------------------------------------------ */}
      <aside
        className="hidden md:flex fixed inset-y-0 left-0 w-64 flex-col"
        style={{ background: 'var(--surface)', borderRight: '1px solid var(--border)' }}
      >
        {/* Branding */}
        <div
          className="flex flex-col justify-center px-6 py-5 flex-shrink-0"
          style={{
            background: 'linear-gradient(135deg, #0a1628 0%, #0d1f38 100%)',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-7 h-7 rounded flex items-center justify-center text-xs font-black"
              style={{ background: 'var(--gold)', color: '#000' }}
            >
              ⬡
            </div>
            <span
              className="text-lg font-black tracking-widest"
              style={{ color: 'var(--gold)', letterSpacing: '0.2em' }}
            >
              O.D.I.A.
            </span>
          </div>
          <p
            className="text-xs leading-tight pl-9"
            style={{ color: 'var(--muted)' }}
          >
            Oraculus Decimus<br />Intellect Analyst
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto" role="navigation">
          {sidebarNav.map((item) => {
            const active = isActive(item.href, pathname);
            return (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center px-3 py-2.5 rounded-md transition-all duration-150 group"
                style={{
                  background: active ? 'rgba(14,165,233,0.15)' : 'transparent',
                  color: active ? 'var(--accent-2)' : 'var(--muted)',
                  borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
                }}
                aria-current={active ? 'page' : undefined}
              >
                <span
                  className="w-6 text-center text-base mr-3 font-mono"
                  style={{ color: active ? 'var(--accent)' : 'var(--muted)' }}
                  aria-hidden="true"
                >
                  {item.icon}
                </span>
                <span className="text-sm font-medium">{item.name}</span>
                {active && (
                  <span
                    className="ml-auto w-1.5 h-1.5 rounded-full"
                    style={{ background: 'var(--accent)' }}
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div
          className="px-5 py-4 flex-shrink-0"
          style={{ borderTop: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ background: 'var(--success)' }}
            />
            <p className="text-xs" style={{ color: 'var(--muted)' }}>
              v2.1.2 &nbsp;·&nbsp; System Online
            </p>
          </div>
        </div>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* Main content                                                         */}
      {/* ------------------------------------------------------------------ */}
      <main className={`md:pl-64 ${offline ? 'pt-10' : ''}`}>
        {/* Desktop page header */}
        <header
          className="hidden md:block"
          style={{
            background: 'var(--surface)',
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div className="px-8 py-4 flex items-center gap-3">
            <div
              className="w-1 h-6 rounded"
              style={{ background: 'var(--accent)' }}
            />
            <h2
              className="text-lg font-semibold tracking-wide"
              style={{ color: 'var(--foreground)' }}
            >
              {currentPage}
            </h2>
          </div>
        </header>

        {/* Mobile page header */}
        <header
          className="md:hidden"
          style={{ background: 'var(--surface)', borderBottom: '1px solid var(--border)' }}
        >
          <div className="px-4 py-3 flex items-center gap-3">
            <span
              className="text-xs font-black tracking-widest"
              style={{ color: 'var(--gold)' }}
            >
              O.D.I.A.
            </span>
            <span style={{ color: 'var(--border)' }}>|</span>
            <span className="text-sm font-medium" style={{ color: 'var(--foreground)' }}>
              {currentPage}
            </span>
          </div>
        </header>

        <div className="p-4 md:p-8 pb-24 md:pb-8">
          {children}
        </div>
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* Mobile bottom tab bar                                                */}
      {/* ------------------------------------------------------------------ */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 z-40"
        style={{
          background: 'var(--surface)',
          borderTop: '1px solid var(--border)',
        }}
        role="navigation"
        aria-label="Primary navigation"
      >
        <div className="flex">
          {tabNav.map((item) => {
            const active = isActive(item.href, pathname);
            return (
              <Link
                key={item.name}
                href={item.href}
                className="flex-1 flex flex-col items-center justify-center py-2.5 gap-1 transition-colors duration-150"
                style={{ color: active ? 'var(--accent)' : 'var(--muted)' }}
                aria-current={active ? 'page' : undefined}
              >
                <span className="text-lg leading-none font-mono" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="text-xs font-medium">{item.name}</span>
                {active && (
                  <div
                    className="absolute bottom-0 w-8 h-0.5 rounded-t"
                    style={{ background: 'var(--accent)' }}
                  />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
