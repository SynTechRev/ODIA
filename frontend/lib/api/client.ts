/**
 * API client for Oraculus-DI-Auditor backend.
 *
 * Provides a typed singleton client for all backend endpoints.
 * Backend base URL defaults to http://localhost:8000 and can be
 * overridden via NEXT_PUBLIC_API_URL environment variable.
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

  constructor(baseURL: string) {
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
  async uploadImage(file: File): Promise<Record<string, unknown>> {
    const form = new FormData();
    form.append('file', file);
    const { data } = await this.http.post<Record<string, unknown>>(
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
}

// ---------------------------------------------------------------------------
// Singleton factory
// ---------------------------------------------------------------------------

let _client: APIClient | null = null;

export function getAPIClient(): APIClient {
  if (!_client) {
    const baseURL =
      (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) ||
      'http://localhost:8000';
    _client = new APIClient(baseURL);
  }
  return _client;
}
