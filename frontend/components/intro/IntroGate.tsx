/**
 * IntroGate — v2.8.0
 *
 * The cinematic Oraculus intro plays on EVERY app launch (per user
 * direction at v2.8.0). Session-stable: once dismissed within a single
 * session (tab open or Electron window open), navigating between pages
 * does not replay it.
 *
 * Mechanism
 * ---------
 * The decision to show is made on RootLayout mount. For each mount:
 *   1. If user has prefers-reduced-motion: skip immediately.
 *   2. If a sessionStorage flag `odia.intro.dismissed.session` is set
 *      (i.e. the user has already seen / dismissed the intro this
 *      session): skip.
 *   3. Otherwise: render the intro, mark dismissed when done.
 *
 * sessionStorage (not localStorage) is the right primitive — it clears
 * when the tab/window closes, which exactly matches "every launch".
 *
 * The Settings replay button now writes a one-shot flag that survives
 * the next launch and forces the intro to play even if the user had
 * dismissed it in a prior session. After consuming the flag, it's
 * cleared.
 *
 * SSR-safe: the decision happens inside useEffect, so the server
 * render and the first client render match (no hydration warning).
 */

'use client';

import React, { useEffect, useState } from 'react';
import { IntroFrame } from './IntroFrame';

const SESSION_KEY    = 'odia.intro.dismissed.session';
const FORCE_REPLAY_KEY = 'odia.intro.forceReplay';  // localStorage one-shot

interface IntroGateProps {
  children: React.ReactNode;
}

export function IntroGate({ children }: IntroGateProps) {
  const [showIntro, setShowIntro] = useState(false);
  const [decided, setDecided] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') {
      setDecided(true);
      return;
    }

    // 1. Reduced-motion users opt out entirely.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setShowIntro(false);
      setDecided(true);
      return;
    }

    // 2. Already dismissed this session?
    let dismissed = false;
    try {
      dismissed = sessionStorage.getItem(SESSION_KEY) === '1';
    } catch {
      // sessionStorage may throw under file:// in some Electron builds;
      // fall through to "show" rather than locking the intro out.
    }

    // 3. One-shot force-replay from Settings? Consume the flag so it
    //    fires exactly once.
    let forceReplay = false;
    try {
      if (localStorage.getItem(FORCE_REPLAY_KEY) === '1') {
        forceReplay = true;
        localStorage.removeItem(FORCE_REPLAY_KEY);
      }
    } catch { /* same fallback as above */ }

    setShowIntro(forceReplay || !dismissed);
    setDecided(true);
  }, []);

  function onComplete() {
    try {
      sessionStorage.setItem(SESSION_KEY, '1');
    } catch { /* survive sessionStorage failures gracefully */ }
    setShowIntro(false);
  }

  // Pre-decision: render children with opacity 0 so the dashboard
  // doesn't flash before the intro decision is made (~1 frame).
  if (!decided) {
    return (
      <div style={{ opacity: 0, transition: 'opacity 0.2s' }}>{children}</div>
    );
  }

  return (
    <>
      {showIntro && <IntroFrame onComplete={onComplete} />}
      <div
        style={{
          opacity: showIntro ? 0 : 1,
          transition: 'opacity 0.4s ease-in 0.2s',
        }}
      >
        {children}
      </div>
    </>
  );
}
