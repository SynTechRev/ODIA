/**
 * IntroGate — orchestrator for the cinematic Oraculus intro.
 *
 * Wraps `RootLayout`'s children. Decides at mount-time whether to
 * render the intro (first launch / asset version bumped) or pass
 * through to the dashboard. SSR-safe: the decision is deferred to a
 * useEffect after hydration so the server render matches the client
 * render exactly (no hydration warnings).
 *
 * Respects `prefers-reduced-motion: reduce` — users with that OS
 * preference skip the intro entirely and see the dashboard from the
 * first frame. We also call `markSeen()` for them so a later session
 * with reduced-motion off won't suddenly play the intro that they've
 * effectively already opted out of.
 */

'use client';

import React, { useEffect, useState } from 'react';
import { useIntroStore } from '@/lib/stores/intro';
import { IntroFrame } from './IntroFrame';

interface IntroGateProps {
  children: React.ReactNode;
}

export function IntroGate({ children }: IntroGateProps) {
  const [showIntro, setShowIntro] = useState(false);
  const [decided, setDecided] = useState(false);
  const shouldShow = useIntroStore((s) => s.shouldShow);
  const markSeen = useIntroStore((s) => s.markSeen);

  useEffect(() => {
    // Reduced-motion users: skip + mark seen so we never re-render
    // the gate / iframe on subsequent navigations.
    if (
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      markSeen();
      setShowIntro(false);
      setDecided(true);
      return;
    }

    setShowIntro(shouldShow());
    setDecided(true);
  }, [shouldShow, markSeen]);

  function onComplete() {
    markSeen();
    setShowIntro(false);
  }

  // Pre-decision: render children with opacity 0 so the dashboard
  // doesn't flash before the intro decision is made. This is a single
  // tick (~1 frame on a fast device) — not perceptible, but eliminates
  // the FOUC the brand-handoff explicitly forbids.
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
