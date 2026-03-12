/**
 * Ingest Page - Document upload and ingestion
 */

'use client';

import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { UploadPanel } from '@/components/document/UploadPanel';

export default function IngestPage() {
  return (
    <DashboardLayout>
      <div className="max-w-4xl">
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Document Ingestion
          </h2>
          <p className="text-gray-600">
            Upload legislative documents for analysis. Supports TXT and JSON formats.
          </p>
        </div>

        <UploadPanel />
      </div>
    </DashboardLayout>
  );
}
