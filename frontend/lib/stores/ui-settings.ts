/**
 * UI settings Zustand store.
 *
 * Persists user preferences for display and theme options.
 */

import { create } from 'zustand';

interface UISettingsState {
  theme: 'light' | 'dark' | 'system';
  compact_mode: boolean;
  show_confidence_scores: boolean;
  highlight_high_severity: boolean;
  default_view: 'grid' | 'list';

  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setCompactMode: (enabled: boolean) => void;
  setShowConfidenceScores: (show: boolean) => void;
  setHighlightHighSeverity: (highlight: boolean) => void;
  setDefaultView: (view: 'grid' | 'list') => void;
}

export const useUISettingsStore = create<UISettingsState>((set) => ({
  theme: 'light',
  compact_mode: false,
  show_confidence_scores: true,
  highlight_high_severity: true,
  default_view: 'grid',

  setTheme: (theme) => set({ theme }),
  setCompactMode: (enabled) => set({ compact_mode: enabled }),
  setShowConfidenceScores: (show) => set({ show_confidence_scores: show }),
  setHighlightHighSeverity: (highlight) => set({ highlight_high_severity: highlight }),
  setDefaultView: (view) => set({ default_view: view }),
}));
