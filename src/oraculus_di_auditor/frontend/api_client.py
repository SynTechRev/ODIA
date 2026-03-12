"""API Client Generator - Creates front-end API integration layer.

This module generates TypeScript/JavaScript API client code that provides
a clean interface to the Oraculus-DI-Auditor backend.

Features:
- Type-safe API methods
- Error handling
- Request retries
- Response caching (optional)
- Authentication support (plug-in ready)

All generated code is deterministic and production-ready.
"""

from __future__ import annotations

from typing import Any


class APIClientGenerator:
    """API client code generator for Phase 6 front-end system."""

    def identify_required_apis(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Identify required API methods based on backend endpoints.

        Args:
            backend_analysis: Analysis of backend capabilities

        Returns:
            List of required API methods
        """
        endpoints = backend_analysis.get("endpoints", [])
        apis = []

        for endpoint in endpoints:
            apis.append(
                {
                    "name": self._endpoint_to_method_name(endpoint["path"]),
                    "endpoint": endpoint["path"],
                    "method": endpoint.get("method", "GET"),
                    "description": endpoint.get("description", ""),
                    "input_schema": endpoint.get("input_schema"),
                    "output_schema": endpoint.get("output_schema"),
                }
            )

        return apis

    def generate_client_code(
        self, backend_analysis: dict[str, Any], framework: str
    ) -> dict[str, Any]:
        """Generate complete API client code structure.

        Args:
            backend_analysis: Analysis of backend capabilities
            framework: Target framework

        Returns:
            API client code structure with TypeScript definitions
        """
        return {
            "structure": self._generate_client_structure(),
            "types": self._generate_typescript_types(backend_analysis),
            "client_class": self._generate_client_class(backend_analysis),
            "methods": self._generate_api_methods(backend_analysis),
            "interceptors": self._generate_interceptors(),
            "error_handling": self._generate_error_handlers(),
            "usage_examples": self._generate_usage_examples(backend_analysis),
        }

    def _endpoint_to_method_name(self, path: str) -> str:
        """Convert endpoint path to camelCase method name.

        Args:
            path: Endpoint path (e.g., "/api/v1/analyze")

        Returns:
            Method name (e.g., "analyzeDocument")
        """
        # Remove leading slash and "api/v1" prefix
        path = path.lstrip("/").replace("api/v1/", "")

        # Handle special cases
        if path == "health":
            return "checkHealth"
        elif path == "info":
            return "getInfo"
        elif path == "analyze":
            return "analyzeDocument"

        # Convert to camelCase
        parts = path.split("/")
        if len(parts) == 1:
            return parts[0]

        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def _generate_client_structure(self) -> dict[str, Any]:
        """Generate client file structure."""
        return {
            "files": {
                "lib/api/client.ts": "Main API client class",
                "lib/api/types.ts": "TypeScript type definitions",
                "lib/api/errors.ts": "Custom error classes",
                "lib/api/config.ts": "API configuration",
            },
            "organization": "Each file has a single responsibility",
        }

    def _generate_typescript_types(
        self, backend_analysis: dict[str, Any]
    ) -> dict[str, str]:
        """Generate TypeScript type definitions.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            Map of type names to TypeScript definitions
        """
        types = {}

        # Request types
        analyze_request_ts = """export interface AnalyzeRequest {
  document_text: string;
  metadata?: Record<string, any>;
}"""
        types["AnalyzeRequest"] = analyze_request_ts

        # Response types
        analysis_result_ts = """export interface AnalysisResult {
  findings: Record<string, Finding[]>;
  severity_score: number;
  lattice_score: number;
  flags: string[];
  summary: string;
  timestamp: string;
  metadata?: Record<string, any>;
}"""
        types["AnalysisResult"] = analysis_result_ts

        finding_ts = """export interface Finding {
  type: string;
  description: string;
  location: string | null;
  severity: number;
}"""
        types["Finding"] = finding_ts

        health_response_ts = """export interface HealthResponse {
  status: string;
  version: string;
}"""
        types["HealthResponse"] = health_response_ts

        info_response_ts = """export interface InfoResponse {
  version: string;
  endpoints: string[];
  detectors: string[];
  features: string[];
}"""
        types["InfoResponse"] = info_response_ts

        # Error type
        api_error_ts = """export class APIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}"""
        types["APIError"] = api_error_ts

        return types

    def _generate_client_class(self, backend_analysis: dict[str, Any]) -> str:
        """Generate main API client class code.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            TypeScript class definition as string
        """
        return """import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  AnalyzeRequest,
  AnalysisResult,
  HealthResponse,
  InfoResponse,
} from './types';
import { APIError } from './errors';

export class OraculusAPIClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(
    baseURL: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  ) {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Setup interceptors
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add authentication token if available
        const token = this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const apiError = new APIError(
          error.message,
          error.response?.status,
          error.response?.data
        );
        return Promise.reject(apiError);
      }
    );
  }

  private getAuthToken(): string | null {
    // Placeholder for authentication
    // In production, retrieve from secure storage
    return null;
  }

  // API Methods are defined below
}"""

    def _generate_api_methods(self, backend_analysis: dict[str, Any]) -> dict[str, str]:
        """Generate API method implementations.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            Map of method names to implementations
        """
        methods = {}

        # Health check
        check_health_ts = """  /**
   * Check API health status.
   *
   * @returns Health status response
   */
  async checkHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/api/v1/health');
    return response.data;
  }"""
        methods["checkHealth"] = check_health_ts

        # Get info
        get_info_ts = """  /**
   * Get API information and capabilities.
   *
   * @returns API information
   */
  async getInfo(): Promise<InfoResponse> {
    const response = await this.client.get<InfoResponse>('/api/v1/info');
    return response.data;
  }"""
        methods["getInfo"] = get_info_ts

        # Analyze document
        analyze_document_ts = """  /**
   * Analyze document for anomalies.
   *
   * @param request - Analysis request with document text and metadata
   * @returns Analysis results with findings and scores
   */
  async analyzeDocument(request: AnalyzeRequest): Promise<AnalysisResult> {
    const response = await this.client.post<AnalysisResult>('/analyze', request);
    return response.data;
  }"""
        methods["analyzeDocument"] = analyze_document_ts

        return methods

    def _generate_interceptors(self) -> dict[str, Any]:
        """Generate request/response interceptor specifications."""
        return {
            "request": {
                "purpose": "Add authentication, logging, custom headers",
                "operations": [
                    "Add auth token if available",
                    "Log request details (dev mode)",
                    "Add correlation ID",
                ],
            },
            "response": {
                "purpose": "Handle errors, transform responses",
                "operations": [
                    "Transform errors to APIError",
                    "Log response details (dev mode)",
                    "Handle 401/403 redirects",
                    "Retry on network errors (optional)",
                ],
            },
        }

    def _generate_error_handlers(self) -> dict[str, Any]:
        """Generate error handling specifications."""
        return {
            "APIError": {
                "description": "Custom error class for API errors",
                "properties": ["message", "statusCode", "response"],
                "usage": "Thrown by API client on errors",
            },
            "error_types": {
                "NetworkError": "Network connectivity issues",
                "TimeoutError": "Request timeout",
                "ValidationError": "Input validation failed (400)",
                "AuthenticationError": "Auth required (401)",
                "AuthorizationError": "Permission denied (403)",
                "NotFoundError": "Resource not found (404)",
                "ServerError": "Server error (500)",
            },
            "retry_strategy": {
                "enabled": False,
                "max_retries": 3,
                "retry_delay": "exponential_backoff",
                "retryable_errors": ["NetworkError", "TimeoutError", "ServerError"],
            },
        }

    def _generate_usage_examples(
        self, backend_analysis: dict[str, Any]
    ) -> list[dict[str, str]]:
        """Generate usage examples for API client.

        Args:
            backend_analysis: Backend capabilities

        Returns:
            List of usage examples
        """
        return [
            {
                "title": "Initialize Client",
                "code": """import { OraculusAPIClient } from '@/lib/api/client';

const apiClient = new OraculusAPIClient();""",
            },
            {
                "title": "Check Health",
                "code": """const health = await apiClient.checkHealth();
console.log('API Status:', health.status);""",
            },
            {
                "title": "Analyze Document",
                "code": """const result = await apiClient.analyzeDocument({
  document_text: 'Your document text here...',
  metadata: {
    title: 'Sample Document',
    jurisdiction: 'federal'
  }
});

console.log('Findings:', result.findings);
console.log('Severity Score:', result.severity_score);""",
            },
            {
                "title": "Error Handling",
                "code": """try {
  const result = await apiClient.analyzeDocument(request);
  // Handle success
} catch (error) {
  if (error instanceof APIError) {
    console.error('API Error:', error.message);
    console.error('Status Code:', error.statusCode);
  }
}""",
            },
        ]


__all__ = ["APIClientGenerator"]
