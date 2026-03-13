/**
 * Analysis Zustand store.
 *
 * Holds results from /analyze (AnalysisResult) and /analyze/detailed
 * (DetailedAnalysisResult), keyed by document_id.
 */

import { create } from 'zustand';
import type { AnalysisResult, DetailedAnalysisResult } from '@/lib/types/api';

interface AnalysisState {
  /** Results from /analyze, keyed by document_id */
  analyses: Record<string, AnalysisResult>;
  /** Results from /analyze/detailed, keyed by document_id */
  detailedAnalyses: Record<string, DetailedAnalysisResult>;
  /** Currently selected analysis for the analysis page */
  currentAnalysis: AnalysisResult | null;

  setAnalysis: (id: string, result: AnalysisResult) => void;
  setDetailedAnalysis: (id: string, result: DetailedAnalysisResult) => void;
  setCurrentAnalysis: (result: AnalysisResult | null) => void;
  getAnalysis: (id: string) => AnalysisResult | undefined;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  analyses: {},
  detailedAnalyses: {},
  currentAnalysis: null,

  setAnalysis: (id, result) =>
    set((state) => ({
      analyses: { ...state.analyses, [id]: result },
    })),

  setDetailedAnalysis: (id, result) =>
    set((state) => ({
      detailedAnalyses: { ...state.detailedAnalyses, [id]: result },
    })),

  setCurrentAnalysis: (result) => set({ currentAnalysis: result }),

  getAnalysis: (id) => get().analyses[id],
}));
