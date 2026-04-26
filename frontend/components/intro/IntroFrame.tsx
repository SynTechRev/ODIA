/**
 * IntroFrame — iframe wrapper for the Oraculus boot animation.
 *
 * Loads `/intro/index.html` (a self-contained HTML+CSS+JS document with
 * embedded Google Fonts), listens for the completion `postMessage` the
 * intro fires at the end of its `run()` function, fades out, and calls
 * `onComplete`.
 *
 * Behaviour:
 *   • Skip button appears after 3 seconds (first-time users get the
 *     full sequence; returners can dismiss instantly).
 *   • Click anywhere inside the iframe also exits (handled inside the
 *     intro HTML's click listener — see B3 patch).
 *   • 30s fallback timer: if the intro never reports completion (e.g.
 *     the iframe failed to load), exit anyway so the user is never
 *     trapped on a black screen.
 *   • Escape key exits.
 *   • Skip button autofocused when it appears so screen-reader users
 *     can dismiss without first finding it.
 */

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { publicAssetURL } from '@/lib/navigation';

interface IntroFrameProps {
  onComplete: () => void;
}

export function IntroFrame({ onComplete }: IntroFrameProps) {
  const [fading, setFading] = useState(false);
  const [showSkip, setShowSkip] = useState(false);
  const completedRef = useRef(false);
  const skipButtonRef = useRef<HTMLButtonElement | null>(null);

  // v2.7.10 — resolve the iframe src at runtime. Under Electron file://
  // the leading-slash form `/intro/index.html` resolves to the
  // FILESYSTEM ROOT, which doesn't exist (this was the v2.7.9 black-
  // screen bug). publicAssetURL() rewrites it to a concrete file://
  // URL anchored at the app root.
  const iframeSrc = useMemo(() => publicAssetURL('/intro/index.html'), []);

  // Show skip button after 3 seconds.
  useEffect(() => {
    const t = setTimeout(() => setShowSkip(true), 3000);
    return () => clearTimeout(t);
  }, []);

  // Autofocus the skip button when it appears so keyboard / screen-
  // reader users can dismiss the intro without first locating it.
  useEffect(() => {
    if (showSkip && skipButtonRef.current) {
      skipButtonRef.current.focus();
    }
  }, [showSkip]);

  // Listen for postMessage from the iframe ('intro:complete').
  useEffect(() => {
    function onMessage(event: MessageEvent) {
      if (event.data === 'intro:complete' && !completedRef.current) {
        completedRef.current = true;
        triggerExit();
      }
    }
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, []);

  // Escape key exits.
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape' && !completedRef.current) {
        completedRef.current = true;
        triggerExit();
      }
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Fallback: if we never receive 'intro:complete' within 30s, exit
  // anyway so the user is never trapped on the intro.
  useEffect(() => {
    const t = setTimeout(() => {
      if (!completedRef.current) {
        completedRef.current = true;
        triggerExit();
      }
    }, 30_000);
    return () => clearTimeout(t);
  }, []);

  function triggerExit() {
    setFading(true);
    // Single console marker so a user looking at devtools can confirm
    // the transition fired. No analytics calls — privacy story forbids.
    console.info('[odia] intro:complete');
    setTimeout(onComplete, 800); // matches CSS transition below
  }

  return (
    <div
      role="dialog"
      aria-label="Application introduction"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: '#07070a',
        opacity: fading ? 0 : 1,
        transition: 'opacity 0.8s ease-out',
        pointerEvents: fading ? 'none' : 'auto',
      }}
    >
      <iframe
        src={iframeSrc}
        title="O.D.I.A. introduction"
        style={{
          width: '100%',
          height: '100%',
          border: 'none',
          display: 'block',
        }}
      />
      {showSkip && (
        <button
          ref={skipButtonRef}
          onClick={() => {
            if (!completedRef.current) {
              completedRef.current = true;
              triggerExit();
            }
          }}
          aria-label="Skip introduction"
          style={{
            position: 'absolute',
            top: 24,
            right: 24,
            padding: '8px 16px',
            background: 'rgba(7, 7, 10, 0.6)',
            color: 'rgba(244, 234, 215, 0.7)',
            border: '1px solid rgba(216, 177, 60, 0.3)',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            const el = e.currentTarget;
            el.style.color = '#e0c688';
            el.style.borderColor = '#c8a96e';
          }}
          onMouseLeave={(e) => {
            const el = e.currentTarget;
            el.style.color = 'rgba(244, 234, 215, 0.7)';
            el.style.borderColor = 'rgba(216, 177, 60, 0.3)';
          }}
        >
          Skip →
        </button>
      )}
    </div>
  );
}
