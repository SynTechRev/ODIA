/**
 * Settings Page — UI preferences, authentication, and system information.
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { useUISettingsStore } from '@/lib/stores/ui-settings';
import { useIntroStore } from '@/lib/stores/intro';
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
                <span className="hud-sev hud-sev-info mt-1 capitalize">
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
                className={`hud-btn ${view === 'login' ? 'hud-btn-emerald' : 'hud-btn-ghost'} flex-1 justify-center`}
              >
                Log In
              </button>
              <button
                onClick={() => { setView('register'); setError(null); }}
                className={`hud-btn ${view === 'register' ? 'hud-btn-emerald' : 'hud-btn-ghost'} flex-1 justify-center`}
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
  // v2.9.1 C1 — Theme dropdown removed; store fields kept for ui-settings shape compat.
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
        {/* v3.0 — unified malachite gemstone hero (matches Dashboard) */}
        <section className="gem-panel gem-panel-faceted gem-hero-malachite hud-brackets p-6 md:p-8 relative overflow-hidden">
          <div className="relative z-10">
            <div className="hud-label-accent hud-cyan-bright mb-3">
              [ APPLICATION CONFIG · USER SCOPE ]
            </div>
            <h1 className="hud-heading text-2xl md:text-3xl">
              Settings
            </h1>
            <p className="hud-subtext mt-3 max-w-3xl">
              Application appearance, analysis display, intro behaviour, and
              authentication preferences. All settings are stored locally;
              nothing is transmitted off-device.
            </p>
          </div>
        </section>

        {/* Appearance Settings */}
        <Card title="Appearance" variant="bordered">
          <div className="space-y-5">
            {/* v2.9.1 C1 — Theme dropdown removed; the app is dark-only per BRAND.md §9. */}
            <div>
              <div className="hud-metric-label mb-2">Theme</div>
              <div className="flex items-center gap-2 hud-panel hud-panel-inset px-3 py-2.5">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{
                    background: 'var(--gold-500)',
                    boxShadow: '0 0 6px var(--gold-500)',
                  }}
                />
                <span className="text-sm" style={{ color: 'var(--smoke-100)' }}>
                  Mineral (locked at v2.8.0)
                </span>
              </div>
              <p className="mt-1 text-sm" style={{ color: 'var(--smoke-400)' }}>
                O.D.I.A. ships with a single locked theme. Customisation lives in
                the brand reference at <code>docs/BRAND.md</code>.
              </p>
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

        {/* v2.7.9 B4 — Intro replay control */}
        <PresentationCard />

        {/* v2.10.x — Webhook token for n8n integration */}
        <WebhookTokenCard />

        {/* Authentication */}
        <AuthSection />

        {/* System Information */}
        <Card title="System Information" variant="bordered">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Package:</span>
              <span className="font-mono text-gray-900">odia 3.5.1</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Frontend:</span>
              <span className="font-mono text-gray-900">Next.js 15</span>
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

// ---------------------------------------------------------------------------
// v2.7.9 B4 — Presentation card: replay the Oraculus intro on next launch
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// v2.10.x — Webhook token card
//
// Persists the n8n shared secret (ODIA_WEBHOOK_TOKEN) to a per-user file
// via POST /api/v1/config/webhook-token.  Without this, the token can
// only be set via the env var, which is impractical on a desktop install
// where the Electron host has no shell.  The backend reads env first,
// then file fallback — so when both are set, env wins and we surface
// that to the user.
// ---------------------------------------------------------------------------
function WebhookTokenCard() {
  const client = getAPIClient();
  const [status, setStatus] = useState<{
    configured: boolean;
    source: 'env' | 'file' | null;
    file_path: string;
  } | null>(null);
  const [token, setToken] = useState('');
  const [reveal, setReveal] = useState(false);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: 'ok' | 'warn' | 'err'; text: string } | null>(null);

  const refresh = useCallback(async () => {
    try {
      const s = await client.getWebhookTokenStatus();
      setStatus({ configured: s.configured, source: s.source, file_path: s.file_path });
    } catch {
      setStatus(null);
    }
  }, [client]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSave = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const r = await client.setWebhookToken(token);
      setToken('');
      await refresh();
      if (r.env_shadows_file) {
        setMsg({
          kind: 'warn',
          text:
            'Saved to disk, but the ODIA_WEBHOOK_TOKEN environment variable is set ' +
            'and takes precedence. Unset it to use the value you just saved.',
        });
      } else {
        setMsg({ kind: 'ok', text: 'Webhook token saved. n8n endpoints will accept it on the next request.' });
      }
    } catch (e: unknown) {
      setMsg({ kind: 'err', text: e instanceof Error ? e.message : 'Failed to save token.' });
    } finally {
      setBusy(false);
    }
  };

  const handleClear = async () => {
    setBusy(true);
    setMsg(null);
    try {
      await client.setWebhookToken('');
      setToken('');
      await refresh();
      setMsg({ kind: 'ok', text: 'Webhook token cleared.' });
    } catch (e: unknown) {
      setMsg({ kind: 'err', text: e instanceof Error ? e.message : 'Failed to clear token.' });
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = () => {
    // Generate a 32-byte cryptographically random hex string (= 64 chars).
    // Falls back to Math.random when crypto is unavailable, which should
    // not happen in any modern browser or Electron — the fallback is
    // there only to keep the field usable in degraded environments.
    if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
      const buf = new Uint8Array(32);
      crypto.getRandomValues(buf);
      const hex = Array.from(buf, (b) => b.toString(16).padStart(2, '0')).join('');
      setToken(hex);
      setReveal(true);
    } else {
      setToken(Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2));
      setReveal(true);
    }
  };

  const sourcePill = status?.source === 'env'
    ? { tone: 'bg-amber-500/20 text-amber-300', text: 'env var' }
    : status?.source === 'file'
      ? { tone: 'bg-emerald-500/20 text-emerald-300', text: 'on disk' }
      : { tone: 'bg-slate-500/20 text-slate-300', text: 'not configured' };

  return (
    <Card title="Automation Webhook" variant="bordered">
      <div className="space-y-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="text-sm font-medium" style={{ color: 'var(--smoke-100)' }}>
              ODIA_WEBHOOK_TOKEN
            </div>
            <div className="text-xs mt-1" style={{ color: 'var(--smoke-400)' }}>
              Shared secret n8n sends in the <code>X-ODIA-Webhook-Token</code> header
              when calling <code>/api/v1/webhook/*</code>. Required for the CivicPlus
              scraper (WF-001) and every other n8n workflow that posts back into ODIA.
            </div>
          </div>
          <span
            className={`px-2 py-1 rounded text-xs font-semibold shrink-0 ${sourcePill.tone}`}
          >
            {sourcePill.text}
          </span>
        </div>

        {status?.source === 'env' && (
          <div className="p-3 rounded text-xs bg-amber-500/10 border border-amber-500/30 text-amber-200">
            The environment variable <code>ODIA_WEBHOOK_TOKEN</code> is set and takes
            precedence over anything saved here. To manage the token from this UI,
            unset the env var and restart the backend.
          </div>
        )}

        {msg && (
          <div
            className={`p-3 rounded text-sm border ${
              msg.kind === 'ok'
                ? 'bg-green-50 border-green-200 text-green-700'
                : msg.kind === 'warn'
                  ? 'bg-amber-50 border-amber-200 text-amber-800'
                  : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {msg.text}
            <button className="ml-2 underline" onClick={() => setMsg(null)}>×</button>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type={reveal ? 'text' : 'password'}
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder={
              status?.configured
                ? 'Enter a new token to replace the saved one'
                : 'Paste or generate a 32+ character secret'
            }
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500"
            spellCheck={false}
            autoComplete="off"
          />
          <button
            type="button"
            onClick={() => setReveal((v) => !v)}
            className="hud-btn hud-btn-ghost"
          >
            {reveal ? 'Hide' : 'Show'}
          </button>
          <button
            type="button"
            onClick={handleGenerate}
            className="hud-btn hud-btn-ghost"
          >
            Generate
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleSave}
            disabled={busy || !token.trim()}
            className="hud-btn hud-btn-emerald"
          >
            {busy ? '…' : 'Save Token'}
          </button>
          {status?.configured && status.source === 'file' && (
            <button
              onClick={handleClear}
              disabled={busy}
              className="hud-btn hud-btn-ghost"
            >
              Clear Saved Token
            </button>
          )}
        </div>

        <div className="text-xs" style={{ color: 'var(--smoke-500)' }}>
          Stored at <code className="break-all">{status?.file_path ?? '…'}</code>.
          The same value must be configured in n8n as the credential
          <code> odia-backend-token</code>.
        </div>
      </div>
    </Card>
  );
}

function PresentationCard() {
  const replay = useIntroStore((s) => s.replay);
  const [confirmed, setConfirmed] = useState(false);

  function handleClick() {
    replay();
    setConfirmed(true);
    // Reset the confirmation chip after a few seconds so the button
    // returns to its idle label and can be clicked again.
    setTimeout(() => setConfirmed(false), 2400);
  }

  return (
    <Card title="Presentation" variant="bordered">
      <div className="flex items-center justify-between gap-4">
        <div className="min-w-0">
          <div className="text-sm font-medium" style={{ color: 'var(--smoke-100)' }}>
            Show intro sequence
          </div>
          <div className="text-xs mt-1" style={{ color: 'var(--smoke-400)' }}>
            The Oraculus introduction plays at the start of every app
            launch. Click <strong>Show on next launch</strong> to force a
            replay even if you dismissed it during the current session.
          </div>
        </div>
        <button
          onClick={handleClick}
          className="hud-btn flex-shrink-0"
          aria-label={
            confirmed
              ? 'Intro replay forced for next launch'
              : 'Show intro sequence on next launch'
          }
        >
          {confirmed ? 'Scheduled ✓' : 'Show on next launch'}
        </button>
      </div>
    </Card>
  );
}
