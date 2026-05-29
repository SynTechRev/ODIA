/**
 * Audit history store — persists completed audit runs to localStorage so
 * reports survive navigation and backend restarts.
 *
 * Backend `_AUDIT_JOBS` is in-memory; jobs vanish when the Python process
 * exits. This store keeps the full `AuditResults` payload client-side so
 * the Results page can render from cache even if the job is gone on the
 * server.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { AuditResults } from '@/lib/types/api';

const MAX_ENTRIES = 100;

export interface AuditHistoryEntry {
  job_id: string;
  results: AuditResults;
  /** ms epoch — when the entry was saved locally (may differ from generated_at) */
  saved_at: number;
}

interface AuditHistoryState {
  entries: AuditHistoryEntry[];
  addAudit: (jobId: string, results: AuditResults) => void;
  getAudit: (jobId: string) => AuditHistoryEntry | undefined;
  removeAudit: (jobId: string) => void;
  clear: () => void;
}

export const useAuditHistoryStore = create<AuditHistoryState>()(
  persist(
    (set, get) => ({
      entries: [],

      addAudit: (jobId, results) =>
        set((state) => {
          const without = state.entries.filter((e) => e.job_id !== jobId);
          const entry: AuditHistoryEntry = {
            job_id: jobId,
            results,
            saved_at: Date.now(),
          };
          const next = [entry, ...without].slice(0, MAX_ENTRIES);
          return { entries: next };
        }),

      getAudit: (jobId) => get().entries.find((e) => e.job_id === jobId),

      removeAudit: (jobId) =>
        set((state) => ({ entries: state.entries.filter((e) => e.job_id !== jobId) })),

      clear: () => set({ entries: [] }),
    }),
    {
      name: 'odia-audit-history',
      storage: createJSONStorage(() => localStorage),
      version: 1,
    },
  ),
);
