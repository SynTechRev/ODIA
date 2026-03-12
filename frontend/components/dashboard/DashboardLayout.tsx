/**
 * Dashboard Layout Component - Main application layout
 */

'use client';

import React, { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';

export interface DashboardLayoutProps {
  children: ReactNode;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: '📊' },
  { name: 'Ingest', href: '/ingest', icon: '📄' },
  { name: 'Analysis', href: '/analysis', icon: '🔍' },
  { name: 'Documents', href: '/documents', icon: '📚' },
  { name: 'Anomalies', href: '/anomalies', icon: '⚠️' },
  { name: 'Orchestrator', href: '/orchestrator', icon: '🔀' },
  { name: 'Settings', href: '/settings', icon: '⚙️' },
];

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 bg-gray-900 text-white">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center h-16 px-6 bg-gray-800">
            <h1 className="text-xl font-bold">Oraculus DI Auditor</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1" role="navigation">
            {navigation.map((item) => {
              const isActive = pathname === item.href || 
                (item.href !== '/' && pathname?.startsWith(item.href));
              
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    flex items-center px-4 py-3 rounded-lg
                    transition-colors duration-200
                    ${isActive
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                    }
                  `}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <span className="mr-3 text-xl" aria-hidden="true">
                    {item.icon}
                  </span>
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-800">
            <p className="text-sm text-gray-400">
              Version 0.1.0
            </p>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="pl-64">
        {/* Header */}
        <header className="bg-white border-b border-gray-200">
          <div className="px-8 py-4">
            <h2 className="text-2xl font-bold text-gray-900">
              {navigation.find(item => pathname === item.href || 
                (item.href !== '/' && pathname?.startsWith(item.href)))?.name || 'Oraculus DI Auditor'}
            </h2>
          </div>
        </header>

        {/* Page content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
