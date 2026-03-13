/**
 * Document Upload Panel Component
 *
 * Calls both /analyze (for full pipeline result) and /analyze/detailed
 * (for per-detector breakdown) on submit, storing both in their respective stores.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Card } from '../base/Card';
import { Button } from '../base/Button';
import { getAPIClient } from '@/lib/api/client';
import { useDocumentStore } from '@/lib/stores/document';
import { useAnalysisStore } from '@/lib/stores/analysis';

export function UploadPanel() {
  const [documentText, setDocumentText] = useState('');
  const [title, setTitle] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const addDocument = useDocumentStore((state) => state.addDocument);
  const setAnalysis = useAnalysisStore((state) => state.setAnalysis);
  const setDetailedAnalysis = useAnalysisStore((state) => state.setDetailedAnalysis);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!documentText.trim()) {
        setError('Please enter document text');
        return;
      }

      setIsAnalyzing(true);
      setError(null);
      setSuccess(false);

      const client = getAPIClient();
      const payload = {
        document_text: documentText,
        metadata: {
          title: title || 'Untitled Document',
          jurisdiction: jurisdiction || 'unknown',
        },
      };

      try {
        // Run both analysis calls in parallel
        const [result, detailed] = await Promise.all([
          client.analyze(payload),
          client.analyzeDetailed(payload),
        ]);

        setAnalysis(result.document_id, result);
        setDetailedAnalysis(detailed.document_id, detailed);

        const document = {
          document_id: result.document_id,
          title: title || 'Untitled Document',
          text: documentText,
          metadata: result.metadata,
          chunks: [],
          checksum: result.provenance?.document_hash ?? '',
          created_at: new Date().toISOString(),
        };
        addDocument(document);

        setSuccess(true);
        setTimeout(() => {
          setDocumentText('');
          setTitle('');
          setJurisdiction('');
          setSuccess(false);
        }, 2000);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to analyze document');
      } finally {
        setIsAnalyzing(false);
      }
    },
    [documentText, title, jurisdiction, addDocument, setAnalysis, setDetailedAnalysis],
  );

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target?.result as string;
        setDocumentText(text);
        if (!title) {
          setTitle(file.name.replace(/\.[^/.]+$/, ''));
        }
      };
      reader.readAsText(file);
    },
    [title],
  );

  return (
    <Card title="Upload Document" variant="bordered">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Upload File (TXT, JSON)
          </label>
          <input
            type="file"
            accept=".txt,.json"
            onChange={handleFileUpload}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:text-sm file:font-medium
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"
          />
        </div>

        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
            Document Title
          </label>
          <input
            id="title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g., Budget Authorization Act 2025"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Jurisdiction */}
        <div>
          <label htmlFor="jurisdiction" className="block text-sm font-medium text-gray-700 mb-2">
            Jurisdiction
          </label>
          <select
            id="jurisdiction"
            value={jurisdiction}
            onChange={(e) => setJurisdiction(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Select jurisdiction...</option>
            <option value="federal">Federal</option>
            <option value="state">State</option>
            <option value="local">Local</option>
          </select>
        </div>

        {/* Document Text */}
        <div>
          <label htmlFor="document-text" className="block text-sm font-medium text-gray-700 mb-2">
            Document Text *
          </label>
          <textarea
            id="document-text"
            value={documentText}
            onChange={(e) => setDocumentText(e.target.value)}
            placeholder="Paste or type document text here..."
            rows={12}
            required
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          />
          <p className="mt-1 text-sm text-gray-500">{documentText.length} characters</p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-md text-green-700">
            Document analyzed successfully!
          </div>
        )}

        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={isAnalyzing}
          disabled={!documentText.trim()}
          className="w-full"
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Document'}
        </Button>
      </form>
    </Card>
  );
}
