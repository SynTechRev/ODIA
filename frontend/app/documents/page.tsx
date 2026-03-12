/**
 * Documents Page - Browse and manage documents
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { useDocumentStore } from '@/lib/stores/document';
import { DocumentList } from '@/components/document/DocumentList';
import { DocumentDetailPanel } from '@/components/document/DocumentDetailPanel';
import { Card } from '@/components/base/Card';
import { Button } from '@/components/base/Button';
import { useRouter } from 'next/navigation';

export default function DocumentsPage() {
  const router = useRouter();
  const documents = useDocumentStore((state) => state.documents);
  const selectedDocument = useDocumentStore((state) => state.selectedDocument);
  const selectDocument = useDocumentStore((state) => state.selectDocument);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {documents.length === 0 ? (
          <Card variant="bordered">
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📚</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Documents Yet
              </h3>
              <p className="text-gray-600 mb-6">
                Upload documents to start analyzing legislative content.
              </p>
              <Button
                variant="primary"
                onClick={() => router.push('/ingest')}
              >
                Upload Document
              </Button>
            </div>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Document List */}
            <div className="lg:col-span-1">
              <Card title="Documents" variant="bordered">
                <DocumentList
                  documents={documents}
                  onSelectDocument={selectDocument}
                  selectedId={selectedDocument?.document_id}
                />
              </Card>
            </div>

            {/* Document Details */}
            <div className="lg:col-span-2">
              {selectedDocument ? (
                <DocumentDetailPanel document={selectedDocument} />
              ) : (
                <Card variant="bordered">
                  <div className="text-center py-12 text-gray-500">
                    Select a document from the list to view details
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
