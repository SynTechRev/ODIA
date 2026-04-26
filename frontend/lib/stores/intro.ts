/**
 * Intro sequence Zustand store (v2.7.9 Track B).
 *
 * Persists the "has the user seen the intro?" decision to localStorage
 * under `odia.intro` so the cinematic boot animation plays exactly
 * once on first launch — and once more when the asset is replaced
 * (bump `INTRO_VERSION` to force a re-show).
 *
 * Mirrors the contract documented in BRAND.md §7.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Bump this when `frontend/public/intro/index.html` changes
 * substantively. Returning users will see the new intro exactly once,
 * then it auto-dismisses for subsequent sessions.
 */
const INTRO_VERSION = 'v8';

interface IntroState {
  hasSeenIntro: boolean;
  lastSeenVersion: string;
  markSeen: () => void;
  replay: () => void;
  shouldShow: () => boolean;
}

export const useIntroStore = create<IntroState>()(
  persist(
    (set, get) => ({
      hasSeenIntro: false,
      lastSeenVersion: '',
      markSeen: () =>
        set({ hasSeenIntro: true, lastSeenVersion: INTRO_VERSION }),
      replay: () => set({ hasSeenIntro: false }),
      shouldShow: () =>
        !get().hasSeenIntro || get().lastSeenVersion !== INTRO_VERSION,
    }),
    { name: 'odia.intro' },
  ),
);

export { INTRO_VERSION };
