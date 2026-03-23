/**
 * Settings Page — UI preferences, authentication, and system information.
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { useUISettingsStore } from '@/lib/stores/ui-settings';
import { getAPIClient } from '@/lib/api/client';

// ---------------------------------------------------------------------------
// Toggle switch (mobile-friendly, replaces checkboxes)
// ---------------------------------------------------------------------------

function Toggle({
  id,
  checked,
  onChange,
  label,
  description,
}: {
  id: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  description?: string;
}) {
  return (
    <div className="flex items-start justify-between gap-4">
      <div>
        <label htmlFor={id} className="text-sm font-medium text-gray-900 cursor-pointer">
          {label}
        </label>
        {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
      </div>
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`
          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
          transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          ${checked ? 'bg-blue-600' : 'bg-gray-200'}
        `}
      >
        <span
          className={`
            pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
            transition duration-200 ease-in-out
            ${checked ? 'translate-x-5' : 'translate-x-0'}
          `}
        />
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Auth section
// ---------------------------------------------------------------------------

type AuthView = 'status' | 'login' | 'register';

function AuthSection() {
  const client = getAPIClient();
  const [authEnabled, setAuthEnabled] = useState(false);
  const [currentUser, setCurrentUser] = useState<Record<string, string> | null>(null);
  const [view, setView] = useState<AuthView>('status');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    try {
      const status = await client.getAuthStatus();
      setAuthEnabled(status.auth_enabled);
      const user = await client.getMe();
      if (user.id !== 'anonymous') setCurrentUser(user as Record<string, string>);
    } catch {
      // server may not have auth routes yet
    }
  }, [client]);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const handleRegister = async () => {
    if (!email || !password || !name) {
      setError('All fields are required.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await client.authRegister(email, password, name);
      setStatusMsg('Registration successful. Please log in.');
      setView('login');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!email || !password) {
      setError('Email and password are required.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await client.authLogin(email, password);
      client.setAuthToken(result.access_token);
      setCurrentUser(result.user as Record<string, string>);
      setView('status');
      setStatusMsg(`Welcome back, ${result.user.name}!`);
      await checkStatus();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await client.authLogout();
      client.setAuthToken(null);
      setCurrentUser(null);
      setStatusMsg('Logged out.');
      await checkStatus();
    } catch {
      client.setAuthToken(null);
      setCurrentUser(null);
    }
  };

  return (
    <Card title="Authentication" variant="bordered">
      <div className="space-y-4">
        {statusMsg && (
          <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-700">
            {statusMsg}
            <button className="ml-2 text-green-600 underline" onClick={() => setStatusMsg(null)}>×</button>
          </div>
        )}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {error}
            <button className="ml-2 text-red-600 underline" onClick={() => setError(null)}>×</button>
          </div>
        )}

        {/* Status */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-900">
              {authEnabled ? 'Authentication enabled' : 'Single-user mode (no auth)'}
            </p>
            <p className="text-xs text-gray-500 mt-0.5">
              {authEnabled
                ? 'Login required to access the platform.'
                : 'Register the first user to enable authentication.'}
            </p>
          </div>
          <span
            className={`px-2 py-1 rounded text-xs font-semibold ${
              authEnabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
            }`}
          >
            {authEnabled ? 'ON' : 'OFF'}
          </span>
        </div>

        {/* Current user info */}
        {currentUser && (
          <div className="p-3 bg-blue-50 border border-blue-100 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-900">{currentUser.name}</p>
                <p className="text-xs text-gray-500">{currentUser.email}</p>
                <span className="mt-1 inline-block px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-medium capitalize">
                  {currentUser.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Log out
              </button>
            </div>
          </div>
        )}

        {/* Forms */}
        {!currentUser && (
          <>
            <div className="flex gap-2">
              <button
                onClick={() => { setView('login'); setError(null); }}
                className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${
                  view === 'login' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                Log In
              </button>
              <button
                onClick={() => { setView('register'); setError(null); }}
                className={`flex-1 py-2 text-sm rounded-lg border transition-colors ${
                  view === 'register' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {authEnabled ? 'Register' : 'Enable Auth'}
              </button>
            </div>

            {(view === 'login' || view === 'register') && (
              <div className="space-y-3">
                {view === 'register' && (
                  <input
                    type="text"
                    placeholder="Full name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                )}
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
                <input
                  type="password"
                  placeholder="Password (min 8 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (view === 'login' ? handleLogin() : handleRegister())}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={view === 'login' ? handleLogin : handleRegister}
                  disabled={loading}
                  className="w-full py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? '…' : view === 'login' ? 'Log In' : 'Create Account'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function SettingsPage() {
  const theme = useUISettingsStore((state) => state.theme);
  const setTheme = useUISettingsStore((state) => state.setTheme);
  const compactMode = useUISettingsStore((state) => state.compact_mode);
  const setCompactMode = useUISettingsStore((state) => state.setCompactMode);
  const showConfidenceScores = useUISettingsStore((state) => state.show_confidence_scores);
  const setShowConfidenceScores = useUISettingsStore((state) => state.setShowConfidenceScores);
  const highlightHighSeverity = useUISettingsStore((state) => state.highlight_high_severity);
  const setHighlightHighSeverity = useUISettingsStore((state) => state.setHighlightHighSeverity);
  const defaultView = useUISettingsStore((state) => state.default_view);
  const setDefaultView = useUISettingsStore((state) => state.setDefaultView);

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-6">
        {/* Appearance Settings */}
        <Card title="Appearance" variant="bordered">
          <div className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as Parameters<typeof setTheme>[0])}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
              <p className="mt-1 text-sm text-gray-500">Choose your preferred color theme</p>
            </div>

            <Toggle
              id="compact-mode"
              checked={compactMode}
              onChange={setCompactMode}
              label="Compact Mode"
              description="Reduce spacing and padding for a denser layout"
            />
          </div>
        </Card>

        {/* Analysis Settings */}
        <Card title="Analysis Display" variant="bordered">
          <div className="space-y-5">
            <Toggle
              id="show-confidence"
              checked={showConfidenceScores}
              onChange={setShowConfidenceScores}
              label="Show Confidence Scores"
              description="Display confidence percentages for findings and anomalies"
            />
            <Toggle
              id="highlight-severity"
              checked={highlightHighSeverity}
              onChange={setHighlightHighSeverity}
              label="Highlight High Severity"
              description="Use prominent colors for high and critical severity findings"
            />
          </div>
        </Card>

        {/* View Preferences */}
        <Card title="Default View" variant="bordered">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Default List View</label>
            <select
              value={defaultView}
              onChange={(e) => setDefaultView(e.target.value as Parameters<typeof setDefaultView>[0])}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="list">List</option>
              <option value="grid">Grid</option>
              <option value="table">Table</option>
            </select>
            <p className="mt-1 text-sm text-gray-500">
              Choose how documents and analyses are displayed by default
            </p>
          </div>
        </Card>

        {/* Authentication */}
        <AuthSection />

        {/* System Information */}
        <Card title="System Information" variant="bordered">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Package:</span>
              <span className="font-mono text-gray-900">odia 2.1.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Frontend:</span>
              <span className="font-mono text-gray-900">Next.js 14</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Backend API:</span>
              <span className="font-mono text-gray-900">
                {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}
