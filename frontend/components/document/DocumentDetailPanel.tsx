/**
 * Document Detail Panel Component - Display full document details
 */

'use client';

import React from 'react';
import { Card } from '../base/Card';
import { Button } from '../base/Button';
import type { Document } from '@/lib/types/api';
import { useAnalysisStore } from '@/lib/stores/analysis';

interface DocumentDetailPanelProps {
  document: Document;
  onAnalyze?: (documentId: string) => void;
}

export function DocumentDetailPanel({ document, onAnalyze }: DocumentDetailPanelProps) {
  const analysis = useAnalysisStore((state) => state.getAnalysis(document.document_id));

  return (
    <div className="space-y-4">
      {/* Metadata Card */}
      <Card title="Document Metadata" variant="bordered">
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600 mb-1">Title</div>
              <div className="font-medium text-gray-900">{document.title}</div>
            </div>
            
            <div>
              <div className="text-sm text-gray-600 mb-1">Document ID</div>
              <div className="font-mono text-sm text-gray-900">{document.document_id}</div>
            </div>
          </div>

          {document.metadata.jurisdiction && (
            <div>
              <div className="text-sm text-gray-600 mb-1">Jurisdiction</div>
              <div className="font-medium text-gray-900">{document.metadata.jurisdiction}</div>
            </div>
          )}

          {document.metadata.year && (
            <div>
              <div className="text-sm text-gray-600 mb-1">Year</div>
              <div className="font-medium text-gray-900">{document.metadata.year}</div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600 mb-1">Created</div>
              <div className="text-sm text-gray-900">
                {new Date(document.created_at).toLocaleString()}
              </div>
            </div>

            {document.checksum && (
              <div>
                <div className="text-sm text-gray-600 mb-1">Checksum</div>
                <div className="font-mono text-xs text-gray-900 truncate">
                  {document.checksum}
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Statistics Card */}
      <Card title="Statistics" variant="bordered">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-2xl font-bold text-gray-900">{document.text.length}</div>
            <div className="text-sm text-gray-600">Characters</div>
          </div>
          
          <div>
            <div className="text-2xl font-bold text-gray-900">{document.chunks.length}</div>
            <div className="text-sm text-gray-600">Chunks</div>
          </div>

          <div>
            <div className="text-2xl font-bold text-gray-900">
              {analysis ? '✓' : '○'}
            </div>
            <div className="text-sm text-gray-600">Analyzed</div>
          </div>
        </div>
      </Card>

      {/* Document Text Card */}
      <Card title="Document Text" variant="bordered">
        <div className="max-h-96 overflow-y-auto">
          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
            {document.text}
          </pre>
        </div>
      </Card>

      {/* Actions */}
      {onAnalyze && !analysis && (
        <Button
          variant="primary"
          size="lg"
          onClick={() => onAnalyze(document.document_id)}
          className="w-full"
        >
          Analyze Document
        </Button>
      )}

      {analysis && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          ✓ This document has been analyzed
        </div>
      )}
    </div>
  );
}
