/**
 * IntroFrame — v2.8.2
 *
 * The fix: bump the fallback timeout from 30s → 35s.
 *
 * Diagnosis
 * ---------
 * The intro `run()` function takes ~31.4 seconds end-to-end:
 *   - 0.0  → 4.5s   Phase 0 deep grid + Phase 1 boot text
 *   - 4.5s → 13.5s  Phase 2 ODIA glyph assembly
 *   - 13.5s → 21.2s typeCode (7 lines, 7.6s typing)
 *   - 21.2s → 23.0s reset + Phase 3 declaration begin
 *   - 23.0s → 25.2s "We the People" words appear
 *   - 25.2s → 28.2s inscription stack + bottom rule
 *   - 28.2s → 29.0s brand tag fade-in
 *   - 29.0s → 31.4s 2.4-second final hold + postMessage
 *
 * v2.8.1 set the IntroFrame fallback timer to 30s — which fires
 * BEFORE the intro's postMessage, so the parent fades out the iframe
 * during the brand-tag phase. The user sees the "We the People"
 * inscription stack flash briefly and then the dashboard appears.
 * That's the "doesn't play the final frames" symptom.
 *
 * Why not just fix the intro to be shorter? The intro is the brand
 * artifact — its pacing was deliberate (the 7.6s typeCode is the
 * dramatic centerpiece; cutting it kills the moment). Extending the
 * fallback is the right move.
 *
 * Why 35s and not 32s? Buffer for slow-frame conditions on lower-
 * powered devices (tablets, older Macs). 4 seconds of cushion past
 * the genuine 31.4s end means the postMessage path always wins.
 *
 * Failure mode: if for some reason the intro JS errors mid-sequence
 * and never fires postMessage, the fallback at 35s rescues the user.
 * The skip button (3s) and click-to-dismiss (4s after start) remain
 * available for impatient users. So the worst case is "user waits
 * 35s for an unresponsive intro" rather than "user is permanently
 * trapped on a black screen."
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

  const iframeSrc = useMemo(() => publicAssetURL('/intro/index.html'), []);

  // Show skip button after 3 seconds.
  useEffect(() => {
    const t = setTimeout(() => setShowSkip(true), 3000);
    return () => clearTimeout(t);
  }, []);

  // Autofocus the skip button when it appears.
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

  // v2.8.2 — Fallback timeout bumped 30s → 35s. The intro's run()
  // function takes ~31.4s end-to-end (3 phases × multiple sleeps + a
  // 7.6s typeCode segment + 2.4s final hold). The previous 30s
  // fallback fired BEFORE the intro's postMessage, cutting off the
  // "We the People" declaration phase. 35s gives ~4s of cushion past
  // the genuine completion point so postMessage always wins under
  // normal conditions; the fallback only fires if the intro JS
  // genuinely errors out.
  useEffect(() => {
    const t = setTimeout(() => {
      if (!completedRef.current) {
        completedRef.current = true;
        triggerExit();
      }
    }, 35_000);
    return () => clearTimeout(t);
  }, []);

  function triggerExit() {
    setFading(true);
    console.info('[odia] intro:complete');
    setTimeout(onComplete, 800);
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
        background: '#050505',
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
            background: 'rgba(5, 5, 5, 0.6)',
            color: 'rgba(225, 215, 198, 0.7)',
            border: '1px solid rgba(174, 145, 104, 0.3)',
            fontFamily: 'monospace',
            fontSize: 11,
            letterSpacing: '0.18em',
            textTransform: 'uppercase',
            cursor: 'pointer',
            transition: 'all 0.3s ease',
          }}
          onMouseEnter={(e) => {
            const el = e.currentTarget;
            el.style.color = '#ded2be';
            el.style.borderColor = '#b89664';
          }}
          onMouseLeave={(e) => {
            const el = e.currentTarget;
            el.style.color = 'rgba(225, 215, 198, 0.7)';
            el.style.borderColor = 'rgba(174, 145, 104, 0.3)';
          }}
        >
          Skip →
        </button>
      )}
    </div>
  );
}
