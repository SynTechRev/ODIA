/**
 * PullToRefresh — touch-driven pull-to-refresh wrapper for mobile pages.
 *
 * Active only on `<md:` viewports — desktop has its own refresh
 * semantics through the existing polling hooks. The wrapper is a
 * passthrough on `md:` and up; no DOM cost beyond the wrapping div.
 *
 * Mechanism (no library):
 *   • touchstart at scrollTop=0 captures the start Y.
 *   • touchmove computes the pull delta. If positive (downward pull),
 *     the indicator transforms into view with a damped curve.
 *   • Past the threshold (THRESHOLD_PX), arming the refresh action.
 *   • touchend either fires `onRefresh()` (armed) or springs back.
 *
 * The `onRefresh` callback is the page's main fetch hook. We hold a
 * minimum loading state (MIN_LOADING_MS) so the user sees the refresh
 * happen even on fast connections — pulling and seeing nothing change
 * feels broken.
 *
 * Spinner glow uses --signal-neon to match the gemstone palette (the
 * preserved digital-neon emerald reserved for live-state indicators).
 */

'use client';

import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from 'react';

const THRESHOLD_PX = 80;        // pull distance to arm refresh
const MAX_PULL_PX = 140;        // hard cap — past this we just show spinner
const SPRING_BACK_MS = 220;     // animation back to rest after release
const MIN_LOADING_MS = 1000;    // minimum spinner display so refresh feels real

interface PullToRefreshProps {
  onRefresh: () => Promise<void> | void;
  children: ReactNode;
  /** Disable the pull gesture entirely (e.g. while a modal is open). */
  disabled?: boolean;
}

export function PullToRefresh({
  onRefresh,
  children,
  disabled = false,
}: PullToRefreshProps) {
  const [pullPx, setPullPx] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const startYRef = useRef<number | null>(null);
  const pullPxRef = useRef(0);

  useEffect(() => {
    pullPxRef.current = pullPx;
  }, [pullPx]);

  const onTouchStart = useCallback(
    (e: React.TouchEvent<HTMLDivElement>) => {
      if (disabled || refreshing) return;
      // Only begin a pull when the user is at the top of the scroll
      // container — otherwise this conflicts with normal scroll.
      if (window.scrollY > 0) return;
      startYRef.current = e.touches[0].clientY;
    },
    [disabled, refreshing],
  );

  const onTouchMove = useCallback(
    (e: React.TouchEvent<HTMLDivElement>) => {
      if (disabled || refreshing || startYRef.current === null) return;
      const delta = e.touches[0].clientY - startYRef.current;
      if (delta <= 0) {
        if (pullPxRef.current !== 0) setPullPx(0);
        return;
      }
      // Damped pull — feels rubbery past the threshold.
      const damped =
        delta < THRESHOLD_PX
          ? delta
          : THRESHOLD_PX + (delta - THRESHOLD_PX) * 0.4;
      const clamped = Math.min(damped, MAX_PULL_PX);
      setPullPx(clamped);
    },
    [disabled, refreshing],
  );

  const onTouchEnd = useCallback(async () => {
    if (disabled || refreshing) return;
    const armed = pullPxRef.current >= THRESHOLD_PX;
    startYRef.current = null;

    if (!armed) {
      setPullPx(0);
      return;
    }

    setRefreshing(true);
    setPullPx(THRESHOLD_PX);
    const t0 = Date.now();
    try {
      await Promise.resolve(onRefresh());
    } catch (err) {
      // Surface but don't crash; the page's own fetch error handling
      // is responsible for the user-facing message.
      // eslint-disable-next-line no-console
      console.warn('[PullToRefresh] onRefresh failed:', err);
    }
    const elapsed = Date.now() - t0;
    if (elapsed < MIN_LOADING_MS) {
      await new Promise((r) => setTimeout(r, MIN_LOADING_MS - elapsed));
    }
    setRefreshing(false);
    setPullPx(0);
  }, [disabled, refreshing, onRefresh]);

  // Visual progress: 0 → 1 across THRESHOLD_PX.
  const progress = Math.min(pullPx / THRESHOLD_PX, 1);

  return (
    <div
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
      onTouchCancel={onTouchEnd}
      className="md:contents"
    >
      {/* Pull indicator — visible only on <md: via the parent wrapper */}
      <div
        aria-hidden="true"
        className="md:hidden flex items-center justify-center overflow-hidden"
        style={{
          height: pullPx,
          transition: refreshing
            ? 'none'
            : `height ${SPRING_BACK_MS}ms cubic-bezier(0.2, 0.8, 0.2, 1)`,
          pointerEvents: 'none',
        }}
      >
        <div
          className="rounded-full"
          style={{
            width: 26,
            height: 26,
            border: '2px solid rgba(31, 232, 143, 0.20)',
            borderTopColor: 'var(--signal-neon, #00ff9d)',
            boxShadow: refreshing
              ? '0 0 16px rgba(0, 255, 157, 0.65)'
              : `0 0 ${8 * progress}px rgba(0, 255, 157, ${0.3 * progress})`,
            transform: refreshing
              ? 'rotate(0deg)'
              : `rotate(${progress * 360}deg)`,
            animation: refreshing
              ? 'odia-pull-spin 0.9s linear infinite'
              : 'none',
            opacity: progress,
          }}
        />
      </div>
      {children}
      {/* Keyframes scoped to this component via a global style block.
          We can't use <style jsx> in a client component without next-jsx,
          and adding a global keyframe to globals.css for one component
          is overkill. */}
      <style>{`
        @keyframes odia-pull-spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
