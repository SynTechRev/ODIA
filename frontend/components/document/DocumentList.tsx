/**
 * Document List Component - Display list of documents
 */

'use client';

import React from 'react';
import type { Document } from '@/lib/types/api';

interface DocumentListProps {
  documents: Document[];
  onSelectDocument: (documentId: string) => void;
  selectedId?: string | null;
}

export function DocumentList({ documents, onSelectDocument, selectedId }: DocumentListProps) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <div className="text-6xl mb-4">📚</div>
        <p>No documents yet. Upload documents to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <button
          key={doc.document_id}
          onClick={() => onSelectDocument(doc.document_id)}
          className={`
            w-full text-left p-4 rounded-lg border-2 transition-colors
            ${selectedId === doc.document_id
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }
          `}
        >
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-medium text-gray-900">{doc.title}</h3>
            <span className="text-xs text-gray-500">
              {new Date(doc.created_at).toLocaleDateString()}
            </span>
          </div>
          
          {doc.metadata.jurisdiction && (
            <div className="text-sm text-gray-600 mb-2">
              <span className="inline-block px-2 py-1 bg-gray-100 rounded text-xs">
                {doc.metadata.jurisdiction}
              </span>
            </div>
          )}
          
          <div className="text-xs text-gray-500">
            {doc.text.length} characters • {doc.chunks.length} chunks
          </div>
        </button>
      ))}
    </div>
  );
}
