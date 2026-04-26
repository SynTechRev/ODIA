/**
 * Intro sequence store — v2.8.0
 *
 * The intro plays on every app launch (per user direction at v2.8.0).
 * Per-session deduplication is handled in IntroGate via sessionStorage —
 * this store is no longer the source of truth for "have we seen it
 * yet?".
 *
 * What this store does now: expose a `replay()` action that schedules
 * the intro to fire on the NEXT launch even if the user dismissed it
 * during the current session. Used by the Settings → "Show on next
 * launch" button. Implementation: writes a one-shot flag to localStorage
 * which IntroGate reads-and-clears on mount.
 *
 * The legacy `markSeen()` / `shouldShow()` API is preserved as no-ops
 * so existing call sites keep compiling. They will be removed in v2.9.0.
 */

import { create } from 'zustand';

/** localStorage one-shot key — must match IntroGate's FORCE_REPLAY_KEY. */
const FORCE_REPLAY_KEY = 'odia.intro.forceReplay';

/**
 * Asset version marker. Bump when `frontend/public/intro/index.html`
 * changes substantively. Currently informational only — IntroGate at
 * v2.8.0 doesn't consult it (the intro plays every launch regardless).
 */
const INTRO_VERSION = 'v8';

interface IntroState {
  /** Schedule the intro for the next app launch. */
  replay: () => void;

  /** @deprecated v2.8.0 — kept to preserve existing call sites. No-op. */
  markSeen: () => void;
  /** @deprecated v2.8.0 — always returns true now. */
  shouldShow: () => boolean;
  /** @deprecated v2.8.0 — kept for typing compatibility. */
  hasSeenIntro: boolean;
  /** @deprecated v2.8.0 — kept for typing compatibility. */
  lastSeenVersion: string;
}

export const useIntroStore = create<IntroState>(() => ({
  replay: () => {
    if (typeof window === 'undefined') return;
    try {
      localStorage.setItem(FORCE_REPLAY_KEY, '1');
    } catch {
      // localStorage may be unavailable in private-browsing or under
      // Electron file:// in some configurations. The intro will still
      // play next launch because the IntroGate at v2.8.0 plays on
      // every launch by default — this flag is only for "force replay
      // even if dismissed within the current session", which already
      // doesn't apply if there is no session-storage flag set.
    }
  },
  markSeen: () => { /* deprecated no-op */ },
  shouldShow: () => true,
  hasSeenIntro: false,
  lastSeenVersion: '',
}));

export { INTRO_VERSION };
