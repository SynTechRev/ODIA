/**
 * Core type definitions for ODIA analysis engine.
 * 
 * These types mirror the Python analysis engine's data structures
 * to ensure identical behavior between platforms.
 */

/** Severity levels for anomalies, matching Python detector output */
export type Severity = 'low' | 'medium' | 'high' | 'critical';

/** Standard anomaly record shape produced by all detectors */
export interface Anomaly {
  /** Stable dot-namespaced identifier (e.g., "fiscal:missing-provenance-hash") */
  id: string;
  /** Concise human-readable description */
  issue: string;
  /** Anomaly severity level */
  severity: Severity;
  /** Detector layer name (e.g., "fiscal", "constitutional") */
  layer: string;
  /** Structured, explainable fields specific to the anomaly type */
  details: Record<string, unknown>;
}

/** Provenance tracking information */
export interface Provenance {
  source?: string;
  hash?: string;
  verified_on?: string;
}

/** Document section */
export interface DocumentSection {
  section_id?: string;
  content: string;
}

/** Normalized document structure used by all detectors */
export interface NormalizedDocument {
  document_id?: string;
  title?: string;
  document_type?: string;
  raw_text?: string;
  sections?: DocumentSection[];
  provenance?: Provenance;
  metadata?: Record<string, unknown>;
  references?: unknown[];
  agencies?: Record<string, string[]>;
  /** Administrative fields */
  final_action?: string | null;
  status?: string | null;
  vote_result?: string | null;
  meeting_date?: string | null;
  agenda_number?: string | null;
  /** Procurement fields */
  execution_date?: string;
  authorization_date?: string;
  id?: string;
  /** Cross-reference fields */
  text?: string;
  jurisdiction?: string;
}

/** Audit engine result */
export interface AuditResult {
  count: number;
  score: number;
  anomalies: Anomaly[];
}

/** Full pipeline analysis result */
export interface AnalysisResult {
  metadata: Record<string, unknown>;
  jurisdiction?: string;
  findings: {
    fiscal: Anomaly[];
    constitutional: Anomaly[];
    surveillance: Anomaly[];
  };
  severity_score: number;
  lattice_score: number;
  coherence_bonus: number;
  flags: string[];
  summary: string;
  timestamp: string;
}

/** Cross-reference result */
export interface CrossReference {
  type: string;
  federal?: string[];
  state?: string[];
  severity: string;
  description: string;
}

/** Cross-reference audit anomaly */
export interface CrossReferenceAnomaly {
  id: string;
  jurisdiction: string;
  issue: string;
  severity: string;
  description: string;
  details?: Record<string, unknown>;
}

/** Stored document for offline access */
export interface StoredDocument {
  id: string;
  title: string;
  text: string;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

/** Stored analysis result */
export interface StoredAnalysisResult {
  id: string;
  documentId: string;
  result: AnalysisResult;
  createdAt: string;
}

/** Detector function type for single-document detectors */
export type SingleDocDetector = (doc: NormalizedDocument) => Anomaly[];

/** Detector function type for multi-document detectors */
export type MultiDocDetector = (docs: NormalizedDocument[]) => Anomaly[];
