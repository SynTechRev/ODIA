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
  BatchAnalysisResult,
  DetailedAnalysisResult,
  DetectorsResponse,
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
