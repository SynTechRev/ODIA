/**
 * API client for Oraculus-DI-Auditor backend.
 *
 * Base URL resolution (runtime, in this priority order):
 *
 *   1. window.odiaDesktop.backendBaseURL (Electron, injected at runtime
 *      by the preload script — see desktop/src/preload.js)
 *   2. NEXT_PUBLIC_API_URL env var baked in at build time (Docker / web)
 *   3. window.location.origin when served over http(s) (same-origin SPA)
 *   4. "http://127.0.0.1:18741" as a last-resort Electron default
 *
 * Why runtime: the static Electron build is loaded via file://, and the
 * backend in packaged mode binds to 127.0.0.1:18741.  Baking that URL in
 * at build time would break the browser/Docker build which uses a
 * different port.  Resolving at runtime lets a single static bundle
 * serve both deployment targets.
 */

import axios, { type AxiosInstance } from 'axios';
import type {
  AnalysisResult,
  AuditResultsResponse,
  AuditRunResult,
  AuditStatus,
  BatchAnalysisResult,
  BatchUploadResult,
  DetailedAnalysisResult,
  DetectorsResponse,
  FileMetadata,
  FilesListResult,
  HealthResponse,
  JurisdictionInfo,
} from '@/lib/types/api';

// ---------------------------------------------------------------------------
// Runtime base URL resolution
// ---------------------------------------------------------------------------

/**
 * Shape of the preload bridge the desktop app exposes on window.  Keep
 * this declaration loose — the renderer does not depend on the desktop
 * app being present, it just uses the bridge when it is.
 */
declare global {
  interface Window {
    odiaDesktop?: {
      backendBaseURL?: string;
      getBackendStatus?: () => Promise<{ host: string; port: number; connected: boolean }>;
      [key: string]: unknown;
    };
  }
}

const ELECTRON_FALLBACK = 'http://127.0.0.1:18741';

function resolveBaseURL(): string {
  // 1. Electron preload bridge
  if (typeof window !== 'undefined' && window.odiaDesktop?.backendBaseURL) {
    return window.odiaDesktop.backendBaseURL;
  }

  // 2. Build-time env var (NEXT_PUBLIC_API_URL is inlined by Next)
  if (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // 3. Same-origin SPA (Docker nginx proxy)
  if (typeof window !== 'undefined' && window.location.protocol !== 'file:') {
    return window.location.origin;
  }

  // 4. Electron fallback — must match BACKEND_PORT in desktop/src/backend.js
  return ELECTRON_FALLBACK;
}

// ---------------------------------------------------------------------------
// Request payload types
// ---------------------------------------------------------------------------

export interface AnalyzePayload {
  document_text: string;
  metadata?: Record<string, unknown>;
}

export interface BatchAnalyzePayload {
  documents: Array<{
    document_text: string;
    metadata?: Record<string, unknown>;
  }>;
}

// ---------------------------------------------------------------------------
// APIClient
// ---------------------------------------------------------------------------

export class APIClient {
  private readonly http: AxiosInstance;
  public readonly baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.http = axios.create({
      baseURL,
      headers: { 'Content-Type': 'application/json' },
      timeout: 30_000,
    });
  }

  /** GET /api/v1/health */
  async health(): Promise<HealthResponse> {
    const { data } = await this.http.get<HealthResponse>('/api/v1/health');
    return data;
  }

  /** POST /analyze — Phase 4 unified pipeline */
  async analyze(payload: AnalyzePayload): Promise<AnalysisResult> {
    const { data } = await this.http.post<AnalysisResult>('/analyze', payload);
    return data;
  }

  /** POST /analyze/detailed — per-detector breakdown */
  async analyzeDetailed(payload: AnalyzePayload): Promise<DetailedAnalysisResult> {
    const { data } = await this.http.post<DetailedAnalysisResult>(
      '/analyze/detailed',
      payload,
    );
    return data;
  }

  /** POST /analyze/batch — multi-document analysis */
  async analyzeBatch(payload: BatchAnalyzePayload): Promise<BatchAnalysisResult> {
    const { data } = await this.http.post<BatchAnalysisResult>(
      '/analyze/batch',
      payload,
    );
    return data;
  }

  /** GET /detectors — registry of all available detectors */
  async getDetectors(): Promise<DetectorsResponse> {
    const { data } = await this.http.get<DetectorsResponse>('/detectors');
    return data;
  }

  /** GET /config/jurisdiction — current jurisdiction config (non-sensitive) */
  async getJurisdiction(): Promise<JurisdictionInfo> {
    const { data } = await this.http.get<JurisdictionInfo>('/config/jurisdiction');
    return data;
  }

  // -------------------------------------------------------------------------
  // Upload endpoints (Sprint D)
  // -------------------------------------------------------------------------

  /** POST /api/v1/upload — upload single file with optional progress callback */
  async uploadFile(
    file: File,
    onProgress?: (percent: number) => void,
  ): Promise<FileMetadata> {
    const form = new FormData();
    form.append('file', file);
    const { data } = await this.http.post<FileMetadata>('/api/v1/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
        ? (e) => {
            if (e.total) onProgress(Math.round((e.loaded / e.total) * 100));
          }
        : undefined,
    });
    return data;
  }

  /** POST /api/v1/upload/batch — upload multiple files at once */
  async uploadBatch(files: File[]): Promise<BatchUploadResult> {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    const { data } = await this.http.post<BatchUploadResult>('/api/v1/upload/batch', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }

  /** POST /api/v1/upload/image — upload JPEG/PNG and extract text via OCR */
  async uploadImage(file: File): Promise<FileMetadata> {
    const form = new FormData();
    form.append('file', file);
    const { data } = await this.http.post<FileMetadata>(
      '/api/v1/upload/image',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return data;
  }

  /** GET /api/v1/upload/files */
  async listUploadedFiles(): Promise<FilesListResult> {
    const { data } = await this.http.get<FilesListResult>('/api/v1/upload/files');
    return data;
  }

  /** DELETE /api/v1/upload/files/{file_id} */
  async deleteUploadedFile(fileId: string): Promise<void> {
    await this.http.delete(`/api/v1/upload/files/${fileId}`);
  }

  // -------------------------------------------------------------------------
  // Audit pipeline endpoints (Sprint D)
  // -------------------------------------------------------------------------

  /** POST /api/v1/audit/run */
  async runAudit(fileIds: string[], jurisdiction?: string): Promise<AuditRunResult> {
    const { data } = await this.http.post<AuditRunResult>('/api/v1/audit/run', {
      file_ids: fileIds,
      jurisdiction: jurisdiction ?? null,
    });
    return data;
  }

  /** GET /api/v1/audit/status/{job_id} */
  async getAuditStatus(jobId: string): Promise<AuditStatus> {
    const { data } = await this.http.get<AuditStatus>(`/api/v1/audit/status/${jobId}`);
    return data;
  }

  /** GET /api/v1/audit/results/{job_id} */
  async getAuditResults(jobId: string): Promise<AuditResultsResponse> {
    const { data } = await this.http.get<AuditResultsResponse>(
      `/api/v1/audit/results/${jobId}`,
    );
    return data;
  }

  /** POST any trigger endpoint — used by Synthesis page RAIA button. */
  async postTrigger<T = unknown>(path: string, params?: Record<string, unknown>): Promise<T> {
    const { data } = await this.http.post<T>(path, null, { params });
    return data;
  }

  /** GET /api/v1/audit/history — lightweight summaries for history list. */
  async getAuditHistory(page = 1, perPage = 500): Promise<AuditHistoryResponse> {
    const { data } = await this.http.get<AuditHistoryResponse>(
      `/api/v1/audit/history?page=${page}&per_page=${perPage}`,
    );
    return data;
  }

  /** GET /api/v1/audit/export/{job_id} — returns Blob for download */
  async exportAudit(jobId: string, format = 'markdown'): Promise<Blob> {
    const { data } = await this.http.get<Blob>(
      `/api/v1/audit/export/${jobId}?format=${format}`,
      { responseType: 'blob' },
    );
    return data;
  }

  /** GET /api/v1/audit/evidence-packet/{job_id} — returns ZIP Blob */
  async downloadEvidencePacket(jobId: string): Promise<Blob> {
    const { data } = await this.http.get<Blob>(
      `/api/v1/audit/evidence-packet/${jobId}`,
      { responseType: 'blob' },
    );
    return data;
  }

  // -------------------------------------------------------------------------
  // Auth endpoints (Sprint F)
  // -------------------------------------------------------------------------

  /** Set JWT token on all future requests (stored in memory only) */
  setAuthToken(token: string | null): void {
    if (token) {
      this.http.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete this.http.defaults.headers.common['Authorization'];
    }
  }

  /** GET /api/v1/auth/status */
  async getAuthStatus(): Promise<{ auth_enabled: boolean; user_count: number }> {
    const { data } = await this.http.get('/api/v1/auth/status');
    return data;
  }

  /** POST /api/v1/auth/register */
  async authRegister(email: string, password: string, name: string): Promise<Record<string, unknown>> {
    const { data } = await this.http.post('/api/v1/auth/register', { email, password, name });
    return data;
  }

  /** POST /api/v1/auth/login — OAuth2 password form */
  async authLogin(email: string, password: string): Promise<{ access_token: string; token_type: string; user: Record<string, string> }> {
    const form = new URLSearchParams();
    form.set('username', email);
    form.set('password', password);
    const { data } = await this.http.post('/api/v1/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return data;
  }

  /** POST /api/v1/auth/logout */
  async authLogout(): Promise<void> {
    await this.http.post('/api/v1/auth/logout');
  }

  /** GET /api/v1/auth/me */
  async getMe(): Promise<Record<string, string>> {
    const { data } = await this.http.get('/api/v1/auth/me');
    return data;
  }

  // -------------------------------------------------------------------------
  // Legistar retrieval endpoints (Sprint F)
  // -------------------------------------------------------------------------

  /** GET /api/v1/retrieve/cities */
  async getLegistarCities(): Promise<{ cities: Array<{ city: string; state: string; client_id: string }>; count: number }> {
    const { data } = await this.http.get('/api/v1/retrieve/cities');
    return data;
  }

  /** POST /api/v1/retrieve/legistar */
  async startLegistarRetrieval(params: {
    client_id: string;
    start_date: string;
    end_date: string;
    output_dir?: string;
    matter_types?: string[] | null;
  }): Promise<{ job_id: string; status: string }> {
    const { data } = await this.http.post('/api/v1/retrieve/legistar', params);
    return data;
  }

  /** GET /api/v1/retrieve/status/{job_id} */
  async getRetrievalStatus(jobId: string): Promise<{
    job_id: string;
    status: string;
    client_id: string;
    manifest: Record<string, unknown> | null;
    error: string | null;
  }> {
    const { data } = await this.http.get(`/api/v1/retrieve/status/${jobId}`);
    return data;
  }

  // -------------------------------------------------------------------------
  // Dashboard summary (v2.7.6 X1)
  // -------------------------------------------------------------------------

  /** GET /api/v1/dashboard/summary */
  async getDashboardSummary(): Promise<DashboardSummary> {
    const { data } = await this.http.get<DashboardSummary>(
      '/api/v1/dashboard/summary',
    );
    return data;
  }

  /** POST /api/v1/dashboard/seed-jurisdictions (v2.7.6 X2) */
  async seedJurisdictions(force = false): Promise<SeedJurisdictionsResult> {
    const { data } = await this.http.post<SeedJurisdictionsResult>(
      '/api/v1/dashboard/seed-jurisdictions',
      null,
      { params: { force } },
    );
    return data;
  }

  // -------------------------------------------------------------------------
  // Runtime config — webhook token (v2.10.x)
  // -------------------------------------------------------------------------

  /** GET /api/v1/config/webhook-token — never returns the value itself. */
  async getWebhookTokenStatus(): Promise<WebhookTokenStatus> {
    const { data } = await this.http.get<WebhookTokenStatus>(
      '/api/v1/config/webhook-token',
    );
    return data;
  }

  /** POST /api/v1/config/webhook-token — empty string clears the token. */
  async setWebhookToken(token: string): Promise<WebhookTokenSetResult> {
    const { data } = await this.http.post<WebhookTokenSetResult>(
      '/api/v1/config/webhook-token',
      { token },
    );
    return data;
  }

  // -------------------------------------------------------------------------
  // DB-backed list queries (v3.2.0) — supersedes localStorage-only listing
  // -------------------------------------------------------------------------

  /** GET /api/v1/documents — paginated Document rows with anomaly counts. */
  async listDocuments(params: ListDocumentsParams = {}): Promise<PagedResponse<DocumentRow>> {
    const { data } = await this.http.get<PagedResponse<DocumentRow>>(
      '/api/v1/documents',
      { params },
    );
    return data;
  }

  /** GET /api/v1/anomalies — paginated Anomaly rows joined to documents. */
  async listAnomalies(params: ListAnomaliesParams = {}): Promise<PagedResponse<AnomalyRow>> {
    const { data } = await this.http.get<PagedResponse<AnomalyRow>>(
      '/api/v1/anomalies',
      { params },
    );
    return data;
  }

  /** GET /api/v1/analyses — paginated Analysis rows joined to documents. */
  async listAnalyses(params: ListAnalysesParams = {}): Promise<PagedResponse<AnalysisRow>> {
    const { data } = await this.http.get<PagedResponse<AnalysisRow>>(
      '/api/v1/analyses',
      { params },
    );
    return data;
  }

  /** GET /api/v1/jurisdictions — DISTINCT jurisdictions with rollup counts. */
  async listJurisdictions(): Promise<JurisdictionsResponse> {
    const { data } = await this.http.get<JurisdictionsResponse>(
      '/api/v1/jurisdictions',
    );
    return data;
  }

  /** GET /api/v1/synthesis/aggregates — cross-document aggregates for Synthesis. */
  async getSynthesisAggregates(
    jurisdictions?: string[],
  ): Promise<SynthesisAggregatesResponse> {
    const params: Record<string, string> = {};
    if (jurisdictions && jurisdictions.length) {
      params.jurisdictions = jurisdictions.join(',');
    }
    const { data } = await this.http.get<SynthesisAggregatesResponse>(
      '/api/v1/synthesis/aggregates',
      { params },
    );
    return data;
  }
}

// ---------------------------------------------------------------------------
// v3.3.2 audit history types
// ---------------------------------------------------------------------------

export interface AuditHistorySummaryItem {
  job_id: string;
  status: string;
  completed_at: string | null;
  generated_at: string | null;
  document_count: number;
  finding_count: number;
  severity_summary: { critical: number; high: number; medium: number; low: number };
  first_filename: string;
  more_docs: number;
}

export interface AuditHistoryResponse {
  items: AuditHistorySummaryItem[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// ---------------------------------------------------------------------------
// v3.2.0 query-endpoint types
// ---------------------------------------------------------------------------

export interface PagedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface ListDocumentsParams {
  page?: number;
  per_page?: number;
  jurisdiction?: string;
  document_type?: string;
}

export interface DocumentRow {
  id: number;
  document_id: string;
  title: string;
  document_type: string;
  jurisdiction: string | null;
  authority: string | null;
  version_date: string | null;
  signatory: string | null;
  created_at: string | null;
  updated_at: string | null;
  latest_analysis_id: number | null;
  latest_analysis_at: string | null;
  scalar_score: number | null;
  anomaly_count: number;
}

export interface ListAnomaliesParams {
  page?: number;
  per_page?: number;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  layer?: string;
  jurisdiction?: string;
  document_id?: string;
}

export interface AnomalyRow {
  id: number;
  anomaly_id: string;
  issue: string;
  severity: string;
  layer: string;
  details: Record<string, unknown>;
  analysis_id: number;
  analysis_timestamp: string | null;
  document_id: string;
  document_title: string;
  jurisdiction: string | null;
}

export interface ListAnalysesParams {
  page?: number;
  per_page?: number;
  jurisdiction?: string;
}

export interface AnalysisRow {
  id: number;
  document_id: string;
  document_title: string;
  document_type: string;
  jurisdiction: string | null;
  analysis_timestamp: string | null;
  anomaly_count: number;
  scalar_score: number | null;
  severity_score: number | null;
  engine_version: string | null;
  summary: string | null;
}

export interface JurisdictionRollup {
  jurisdiction: string;
  document_count: number;
  analysis_count: number;
  anomaly_count: number;
  last_audit_at: string | null;
}

export interface JurisdictionsResponse {
  available: boolean;
  items: JurisdictionRollup[];
}

export interface SynthesisFindingAggregate {
  anomaly_id: string;
  count: number;
  severity: string;
  layer: string;
  jurisdictions: string[];
  jurisdiction_count: number;
  example_issue: string;
}

export interface SynthesisVendorAggregate {
  vendor: string;
  count: number;
  jurisdictions: string[];
  jurisdiction_count: number;
}

export interface SynthesisLayerAggregate {
  layer: string;
  count: number;
}

export interface SynthesisAggregatesResponse {
  available: boolean;
  jurisdictions_scope: string[];
  total_documents: number;
  total_anomalies: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  by_finding_id: SynthesisFindingAggregate[];
  by_vendor: SynthesisVendorAggregate[];
  by_layer: SynthesisLayerAggregate[];
}

export interface WebhookTokenStatus {
  configured: boolean;
  source: 'env' | 'file' | null;
  file_path: string;
  env_var: string;
}

export interface WebhookTokenSetResult {
  status: 'ok';
  source: 'env' | 'file' | null;
  env_shadows_file: boolean;
}

export interface SeedJurisdictionsResult {
  status: 'ok' | 'no_bundle';
  message?: string;
  copied: string[];
  skipped: string[];
  target: string | null;
  force?: boolean;
}

export interface DashboardSummary {
  available: boolean;
  analyses: number;
  documents: number;
  findings: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  avg_severity_score: number;
  last_audit_at: string | null;
}

// ---------------------------------------------------------------------------
// Singleton factory
// ---------------------------------------------------------------------------

let _client: APIClient | null = null;

export function getAPIClient(): APIClient {
  if (!_client) {
    _client = new APIClient(resolveBaseURL());
  }
  return _client;
}

/**
 * Force the client to re-resolve its base URL.  Useful in Electron where
 * window.odiaDesktop may be injected slightly after the first render.
 */
export function resetAPIClient(): void {
  _client = null;
}

/** Exported for tests. */
export { resolveBaseURL };
