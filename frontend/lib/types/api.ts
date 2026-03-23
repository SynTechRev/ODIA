/**
 * API type definitions for Oraculus-DI-Auditor.
 *
 * These interfaces reflect the actual shapes returned by the FastAPI backend.
 * Anomaly dicts follow the standard shape: { id, issue, severity, layer, details }
 */

// ---------------------------------------------------------------------------
// Core anomaly shape — matches every detector's output
// ---------------------------------------------------------------------------

export interface Anomaly {
  /** Stable dot-namespaced identifier, e.g. "fiscal:amount-without-appropriation" */
  id: string;
  /** Concise human-readable description */
  issue: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  /** Detector name, e.g. "fiscal", "procurement_timeline" */
  layer: string;
  /** Structured, explainable fields — keys vary per detector */
  details: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// /api/v1/health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  version: string;
}

// ---------------------------------------------------------------------------
// /analyze  (Phase 4 unified pipeline)
// ---------------------------------------------------------------------------

export interface AnalysisResult {
  document_id: string;
  /** Original metadata plus document_id */
  metadata: Record<string, unknown>;
  /** Jurisdiction name — only present when config was loaded at startup */
  jurisdiction?: string;
  findings: {
    fiscal: Anomaly[];
    constitutional: Anomaly[];
    surveillance: Anomaly[];
    /** Legacy field — not currently returned by the API */
    anomalies?: Anomaly[];
  };
  severity_score: number;
  lattice_score: number;
  coherence_bonus?: number;
  flags: string[];
  summary: string;
  timestamp: string;
  /** Confidence score — derived from lattice_score if not explicitly returned */
  confidence?: number;
  provenance?: {
    pipeline_version?: string;
    analysis_timestamp?: string;
    document_hash?: string;
  };
}

// ---------------------------------------------------------------------------
// /analyze/detailed  (per-detector breakdown)
// ---------------------------------------------------------------------------

export interface DetailedAnalysisResult {
  document_id: string;
  jurisdiction?: string;
  detectors: {
    fiscal: Anomaly[];
    constitutional: Anomaly[];
    surveillance: Anomaly[];
    procurement_timeline: Anomaly[];
    signature_chain: Anomaly[];
    scope_expansion: Anomaly[];
    governance_gap: Anomaly[];
    administrative_integrity: Anomaly[];
  };
  summary: {
    total_anomalies: number;
    by_severity: {
      critical: number;
      high: number;
      medium: number;
      low: number;
    };
    score: number;
  };
  timestamp: string;
}

// ---------------------------------------------------------------------------
// /analyze/batch
// ---------------------------------------------------------------------------

export interface BatchAnalysisResult {
  results: Array<
    Omit<DetailedAnalysisResult, 'timestamp'> & { jurisdiction?: string }
  >;
  cross_document_patterns: Anomaly[];
  summary: {
    document_count: number;
    total_anomalies: number;
    by_severity: { critical: number; high: number; medium: number; low: number };
    by_detector: Record<string, number>;
  };
  timestamp: string;
}

// ---------------------------------------------------------------------------
// /detectors
// ---------------------------------------------------------------------------

export interface DetectorInfo {
  name: string;
  description: string;
  anomaly_types: string[];
}

export interface DetectorsResponse {
  detectors: DetectorInfo[];
  count: number;
}

// ---------------------------------------------------------------------------
// /config/jurisdiction
// ---------------------------------------------------------------------------

export interface JurisdictionInfo {
  loaded: boolean;
  name: string | null;
  state: string | null;
  country: string | null;
  meeting_type: string | null;
  agency_count: number;
}

// ---------------------------------------------------------------------------
// Upload & audit pipeline types (Sprint D)
// ---------------------------------------------------------------------------

export interface FileMetadata {
  file_id: string;
  name: string;
  size: number;
  sha256: string;
  format: string;
  path?: string;
  uploaded_at: string;
  ocr_method?: string;
}

// ---------------------------------------------------------------------------
// Timeline types (Sprint E)
// ---------------------------------------------------------------------------

export interface TimelineEvent {
  id: string;
  date: string;        // ISO date string
  label: string;
  description: string;
  category: 'finding' | 'document' | 'milestone';
  severity?: string;
  document_id?: string;
}

// CCOPS mandate compliance status
export interface CCOPSMandate {
  id: string;
  title: string;
  description: string;
  status: 'pass' | 'fail' | 'warn' | 'unknown';
  evidence: string[];
}

export interface BatchUploadResult {
  uploaded: FileMetadata[];
  errors: Array<{ name: string; error: string }>;
}

export interface FilesListResult {
  files: FileMetadata[];
  count: number;
}

export interface AuditRunResult {
  job_id: string;
  status: string;
  file_count: number;
}

export interface AuditProgress {
  phase: string;
  docs_processed: number;
  findings_count: number;
  total_docs: number;
}

export interface AuditStatus {
  job_id: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  progress: AuditProgress;
  error?: string;
}

export interface AuditFinding extends Anomaly {
  document_id: string;
  plain_summary?: string;
  plain_impact?: string;
  plain_action?: string;
}

export interface AuditSeveritySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface AuditDocumentManifest {
  document_id: string;
  filename: string;
  sha256: string;
  size: number;
  format: string;
  finding_count: number;
}

export interface AuditResults {
  job_id: string;
  document_count: number;
  finding_count: number;
  severity_summary: AuditSeveritySummary;
  findings: AuditFinding[];
  document_manifest: AuditDocumentManifest[];
  generated_at: string;
}

export interface AuditResultsResponse {
  job_id: string;
  status: string;
  results: AuditResults | null;
}

// ---------------------------------------------------------------------------
// Local document model
// ---------------------------------------------------------------------------

export interface Document {
  document_id: string;
  title: string;
  text: string;
  metadata: Record<string, unknown>;
  chunks: string[];
  checksum?: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Legacy Finding type — kept for backward compat with existing components.
// New code should use Anomaly instead.
// ---------------------------------------------------------------------------

/** @deprecated Use Anomaly instead */
export interface FiscalFinding {
  type: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  detector: string;
  location: { text: string };
  fiscal_amount?: string | number;
  appropriation_status?: string;
}

/** @deprecated Use Anomaly instead */
export type Finding = FiscalFinding;
