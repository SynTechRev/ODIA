/**
 * PWA Install Prompt — surfaces an inline banner inviting the user to
 * install the app on their device. Two flavors:
 *
 *   • Android Chrome (and other Chromium browsers): the browser fires a
 *     `beforeinstallprompt` event. We capture it, render an "Install"
 *     button, and call `event.prompt()` on click.
 *
 *   • iOS Safari: there is no programmatic install API. The only path is
 *     Share → Add to Home Screen. We UA-sniff iOS + Safari and render an
 *     instructional hint instead of an Install button.
 *
 * Suppressed when:
 *   • Already running standalone (matchMedia '(display-mode: standalone)'
 *     or navigator.standalone for iOS).
 *   • Running under file:// (Electron desktop build — install is N/A).
 *   • User has dismissed the prompt previously (localStorage memo).
 */

'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { isFileProtocol } from '@/lib/navigation';

const DISMISS_KEY = 'odia.installPrompt.dismissedAt';
const DISMISS_TTL_MS = 1000 * 60 * 60 * 24 * 14; // 14 days

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

type Variant = 'android' | 'ios' | null;

function isStandalone(): boolean {
  if (typeof window === 'undefined') return false;
  if (window.matchMedia?.('(display-mode: standalone)').matches) return true;
  // iOS Safari exposes navigator.standalone
  const nav = window.navigator as Navigator & { standalone?: boolean };
  return nav.standalone === true;
}

function isIosSafari(): boolean {
  if (typeof window === 'undefined') return false;
  const ua = window.navigator.userAgent;
  const isIos = /iphone|ipad|ipod/i.test(ua);
  // iPadOS 13+ reports as Mac with touch — use platform + maxTouchPoints.
  const isIpadOS =
    /macintosh/i.test(ua) && (window.navigator.maxTouchPoints ?? 0) > 1;
  if (!isIos && !isIpadOS) return false;
  // Exclude in-app browsers (FB, IG, Twitter etc.) that won't honor A2HS
  // — those UAs include their own fragments.
  if (/(crios|fxios|edgios|opios|gsa)/i.test(ua)) return false;
  return /safari/i.test(ua);
}

function dismissedRecently(): boolean {
  try {
    const raw = window.localStorage.getItem(DISMISS_KEY);
    if (!raw) return false;
    const ts = parseInt(raw, 10);
    if (Number.isNaN(ts)) return false;
    return Date.now() - ts < DISMISS_TTL_MS;
  } catch {
    return false;
  }
}

export function InstallPrompt() {
  const [variant, setVariant] = useState<Variant>(null);
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(
    null,
  );

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (isFileProtocol()) return;
    if (isStandalone()) return;
    if (dismissedRecently()) return;

    // Android / Chromium path
    const onBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
      setVariant('android');
    };
    window.addEventListener('beforeinstallprompt', onBeforeInstall);

    // iOS Safari path — no event, just UA detection
    if (isIosSafari()) setVariant('ios');

    // If install completes, hide
    const onInstalled = () => setVariant(null);
    window.addEventListener('appinstalled', onInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', onBeforeInstall);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  const dismiss = useCallback(() => {
    try {
      window.localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      // localStorage may be blocked (Safari private mode); fail silent.
    }
    setVariant(null);
  }, []);

  const handleInstall = useCallback(async () => {
    if (!deferred) return;
    try {
      await deferred.prompt();
      const result = await deferred.userChoice;
      if (result.outcome === 'accepted') {
        setVariant(null);
      } else {
        dismiss();
      }
    } catch {
      // Some browsers reject prompt() if called outside a user gesture;
      // we already are in a click handler so this should be rare.
      dismiss();
    }
  }, [deferred, dismiss]);

  if (variant === null) return null;

  return (
    <div
      className="md:hidden fixed inset-x-3 bottom-[68px] z-40 hud-panel hud-panel-flow hud-panel-dense"
      role="dialog"
      aria-label="Install O.D.I.A."
      style={{
        padding: '0.75rem 0.875rem',
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 mt-0.5"
          style={{
            color: 'var(--neon-emerald)',
            filter: 'drop-shadow(0 0 6px rgba(31, 232, 143, 0.55))',
          }}
          aria-hidden="true"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 3v12m0 0l-4-4m4 4l4-4M5 21h14"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p
            className="text-sm font-semibold leading-tight"
            style={{ color: 'var(--smoke-100)' }}
          >
            Install O.D.I.A.
          </p>
          {variant === 'android' ? (
            <p
              className="text-xs mt-1 leading-snug"
              style={{ color: 'var(--smoke-300)' }}
            >
              Add the app to your home screen for offline access to cached
              audits.
            </p>
          ) : (
            <p
              className="text-xs mt-1 leading-snug"
              style={{ color: 'var(--smoke-300)' }}
            >
              Tap the Share icon, then choose{' '}
              <span style={{ color: 'var(--gold-200)' }}>
                Add to Home Screen
              </span>
              .
            </p>
          )}
        </div>
        <div className="flex flex-col gap-1.5 flex-shrink-0">
          {variant === 'android' && (
            <button
              type="button"
              onClick={handleInstall}
              className="min-h-[36px] px-3 text-xs font-semibold rounded transition-colors"
              style={{
                background:
                  'linear-gradient(135deg, var(--gold-300), var(--gold-500))',
                color: '#1a1404',
                boxShadow: '0 0 12px -4px rgba(216, 177, 60, 0.55)',
              }}
            >
              Install
            </button>
          )}
          <button
            type="button"
            onClick={dismiss}
            className="min-h-[32px] px-3 text-[11px] font-medium rounded transition-colors"
            style={{
              background: 'transparent',
              color: 'var(--smoke-400)',
              border: '1px solid var(--gem-edge-gold)',
            }}
          >
            Not now
          </button>
        </div>
      </div>
    </div>
  );
}
