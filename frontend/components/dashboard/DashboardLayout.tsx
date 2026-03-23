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

// Desktop sidebar — all nav items
const sidebarNav = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Upload', href: '/upload', icon: '⬆️' },
  { name: 'Results', href: '/results', icon: '📋' },
  { name: 'Ingest', href: '/ingest', icon: '📄' },
  { name: 'Analysis', href: '/analysis', icon: '🔍' },
  { name: 'Documents', href: '/documents', icon: '📚' },
  { name: 'Anomalies', href: '/anomalies', icon: '⚠️' },
  { name: 'Orchestrator', href: '/orchestrator', icon: '🔀' },
  { name: 'Settings', href: '/settings', icon: '⚙️' },
];

// Mobile bottom tab bar — 5 primary destinations
const tabNav = [
  { name: 'Home', href: '/', icon: '📊' },
  { name: 'Upload', href: '/upload', icon: '⬆️' },
  { name: 'Results', href: '/results', icon: '📋' },
  { name: 'Docs', href: '/documents', icon: '📚' },
  { name: 'Settings', href: '/settings', icon: '⚙️' },
];

function isActive(href: string, pathname: string): boolean {
  return pathname === href || (href !== '/' && pathname.startsWith(href));
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();
  const [offline, setOffline] = useState(false);

  // Listen for OFFLINE broadcast from service worker
  useEffect(() => {
    if (!('serviceWorker' in navigator)) return;

    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'OFFLINE') setOffline(true);
    };
    navigator.serviceWorker.addEventListener('message', handler);
    return () => navigator.serviceWorker.removeEventListener('message', handler);
  }, []);

  const currentPage =
    sidebarNav.find((item) => isActive(item.href, pathname))?.name ??
    'Oraculus DI Auditor';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Offline banner */}
      {offline && (
        <div className="fixed top-0 inset-x-0 z-50 bg-yellow-500 text-white text-sm text-center py-2 px-4">
          You are offline. Cached pages are available.
          <button
            className="ml-3 underline text-white"
            onClick={() => setOffline(false)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Desktop sidebar (hidden on mobile)                                  */}
      {/* ------------------------------------------------------------------ */}
      <aside className="hidden md:flex fixed inset-y-0 left-0 w-64 bg-gray-900 text-white flex-col">
        {/* Logo */}
        <div className="flex items-center h-16 px-6 bg-gray-800 flex-shrink-0">
          <h1 className="text-xl font-bold">Oraculus DI Auditor</h1>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto" role="navigation">
          {sidebarNav.map((item) => {
            const active = isActive(item.href, pathname);
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-4 py-3 rounded-lg
                  transition-colors duration-200
                  ${active
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }
                `}
                aria-current={active ? 'page' : undefined}
              >
                <span className="mr-3 text-xl" aria-hidden="true">{item.icon}</span>
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-800 flex-shrink-0">
          <p className="text-sm text-gray-400">Version 0.1.0</p>
        </div>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* Main content                                                         */}
      {/* ------------------------------------------------------------------ */}
      <main className={`md:pl-64 ${offline ? 'pt-10' : ''}`}>
        {/* Desktop page header */}
        <header className="hidden md:block bg-white border-b border-gray-200">
          <div className="px-8 py-4">
            <h2 className="text-2xl font-bold text-gray-900">{currentPage}</h2>
          </div>
        </header>

        {/* Mobile page header */}
        <header className="md:hidden bg-gray-900 text-white">
          <div className="px-4 py-4">
            <h2 className="text-lg font-bold">{currentPage}</h2>
          </div>
        </header>

        {/* Page content — extra bottom padding on mobile for tab bar */}
        <div className="p-4 md:p-8 pb-24 md:pb-8">
          {children}
        </div>
      </main>

      {/* ------------------------------------------------------------------ */}
      {/* Mobile bottom tab bar (hidden on desktop)                           */}
      {/* ------------------------------------------------------------------ */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 z-40"
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
                className={`
                  flex-1 flex flex-col items-center justify-center py-2 gap-0.5
                  text-xs font-medium transition-colors duration-150
                  ${active ? 'text-blue-600' : 'text-gray-500'}
                `}
                aria-current={active ? 'page' : undefined}
              >
                <span className="text-2xl leading-none" aria-hidden="true">
                  {item.icon}
                </span>
                <span className="leading-tight">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
