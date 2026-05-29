/**
 * Audit history store — persists lightweight summaries of completed audit
 * runs to localStorage and syncs from the backend DB.
 *
 * Design rationale:
 *   - Full AuditResults payloads (findings array, document manifest, etc.)
 *     can be 100–500 KB each. Storing them in localStorage caps out around
 *     20–50 entries before hitting the browser's 5–10 MB origin limit.
 *   - This store holds only the summary metadata needed to render the history
 *     list (~300 bytes per entry), allowing 10,000+ entries in localStorage.
 *   - Full results are fetched on demand from GET /api/v1/audit/results/{id},
 *     which now falls back to the DB when the in-memory job has been evicted.
 *   - On mount the results page calls syncFromBackend() to pull any jobs
 *     that were completed in previous server sessions.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

const MAX_ENTRIES = 10_000;

export interface AuditHistorySummary {
  job_id: string;
  saved_at: number;
  generated_at: string | null;
  document_count: number;
  finding_count: number;
  severity_summary: { critical: number; high: number; medium: number; low: number };
  first_filename: string;
  more_docs: number;
}

interface AuditHistoryState {
  entries: AuditHistorySummary[];
  addAudit: (summary: AuditHistorySummary) => void;
  addAuditFromResults: (jobId: string, results: Record<string, unknown>) => void;
  mergeFromBackend: (items: AuditHistorySummary[]) => void;
  hasEntry: (jobId: string) => boolean;
  removeAudit: (jobId: string) => void;
  clear: () => void;
}

export const useAuditHistoryStore = create<AuditHistoryState>()(
  persist(
    (set, get) => ({
      entries: [],

      addAudit: (summary) =>
        set((state) => {
          const without = state.entries.filter((e) => e.job_id !== summary.job_id);
          return { entries: [summary, ...without].slice(0, MAX_ENTRIES) };
        }),

      /** Convenience: build a summary from a full AuditResults payload. */
      addAuditFromResults: (jobId, results) => {
        const manifest = (results.document_manifest as Array<{ filename: string }>) ?? [];
        const sev = (results.severity_summary as AuditHistorySummary['severity_summary']) ?? {};
        const summary: AuditHistorySummary = {
          job_id: jobId,
          saved_at: Date.now(),
          generated_at: (results.generated_at as string) ?? null,
          document_count: (results.document_count as number) ?? 0,
          finding_count: (results.finding_count as number) ?? 0,
          severity_summary: {
            critical: sev.critical ?? 0,
            high: sev.high ?? 0,
            medium: sev.medium ?? 0,
            low: sev.low ?? 0,
          },
          first_filename: manifest[0]?.filename ?? 'Unknown',
          more_docs: Math.max(0, ((results.document_count as number) ?? 0) - 1),
        };
        get().addAudit(summary);
      },

      /** Merge backend history items without displacing locally-saved entries. */
      mergeFromBackend: (items) =>
        set((state) => {
          const existingIds = new Set(state.entries.map((e) => e.job_id));
          const newItems = items.filter((i) => !existingIds.has(i.job_id));
          if (newItems.length === 0) return state;
          return {
            entries: [...state.entries, ...newItems]
              .sort((a, b) => (b.saved_at ?? 0) - (a.saved_at ?? 0))
              .slice(0, MAX_ENTRIES),
          };
        }),

      hasEntry: (jobId) => get().entries.some((e) => e.job_id === jobId),

      removeAudit: (jobId) =>
        set((state) => ({ entries: state.entries.filter((e) => e.job_id !== jobId) })),

      clear: () => set({ entries: [] }),
    }),
    {
      name: 'odia-audit-history',
      storage: createJSONStorage(() => localStorage),
      version: 2,
      migrate: (persisted: unknown, version: number) => {
        // v1 stored full AuditResults under entries[].results — strip to summary shape.
        if (version < 2) {
          const old = persisted as { entries?: Array<Record<string, unknown>> };
          const migrated = (old.entries ?? []).map((e) => {
            const r = (e.results ?? {}) as Record<string, unknown>;
            const manifest = (r.document_manifest as Array<{ filename: string }>) ?? [];
            const sev = (r.severity_summary as AuditHistorySummary['severity_summary']) ?? {};
            return {
              job_id: e.job_id as string,
              saved_at: (e.saved_at as number) ?? Date.now(),
              generated_at: (r.generated_at as string) ?? null,
              document_count: (r.document_count as number) ?? 0,
              finding_count: (r.finding_count as number) ?? 0,
              severity_summary: {
                critical: sev.critical ?? 0,
                high: sev.high ?? 0,
                medium: sev.medium ?? 0,
                low: sev.low ?? 0,
              },
              first_filename: manifest[0]?.filename ?? 'Unknown',
              more_docs: Math.max(0, ((r.document_count as number) ?? 0) - 1),
            } as AuditHistorySummary;
          });
          return { entries: migrated };
        }
        return persisted as { entries: AuditHistorySummary[] };
      },
    },
  ),
);
