/**
 * Anomaly Zustand store.
 *
 * Holds a flat list of anomalies aggregated from analyses, plus UI state
 * for filtering and selection.
 */

import { create } from 'zustand';
import type { Anomaly } from '@/lib/types/api';

type SeverityFilter = 'all' | 'critical' | 'high' | 'medium' | 'low';

interface AnomalyState {
  anomalies: Anomaly[];
  selectedAnomaly: Anomaly | null;
  filterSeverity: SeverityFilter;

  setAnomalies: (anomalies: Anomaly[]) => void;
  selectAnomaly: (anomaly: Anomaly | null) => void;
  setFilterSeverity: (severity: SeverityFilter) => void;
}

export const useAnomalyStore = create<AnomalyState>((set) => ({
  anomalies: [],
  selectedAnomaly: null,
  filterSeverity: 'all',

  setAnomalies: (anomalies) => set({ anomalies }),
  selectAnomaly: (anomaly) => set({ selectedAnomaly: anomaly }),
  setFilterSeverity: (severity) => set({ filterSeverity: severity }),
}));
