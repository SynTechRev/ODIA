/**
 * Upload Page — drag-and-drop document upload with audit pipeline.
 *
 * Flow:
 *  1. User drops or selects files (PDF, JSON, TXT, XML)
 *  2. Files upload to POST /api/v1/upload with per-file progress bars
 *  3. User clicks "Run Audit" → POST /api/v1/audit/run
 *  4. Progress view polls GET /api/v1/audit/status every 2 s
 *  5. On completion, navigates to /results?job_id=…
 */

'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components/dashboard/DashboardLayout';
import { Card } from '@/components/base/Card';
import { getAPIClient } from '@/lib/api/client';
import type { AuditStatus, FileMetadata } from '@/lib/types/api';

// ---------------------------------------------------------------------------
// Legistar retrieval panel
// ---------------------------------------------------------------------------

type LegistarCity = { city: string; state: string; client_id: string };

function LegistarPanel({ onFilesRetrieved }: { onFilesRetrieved: () => void }) {
  const client = getAPIClient();
  const [open, setOpen] = useState(false);
  const [cities, setCities] = useState<LegistarCity[]>([]);
  const [search, setSearch] = useState('');
  const [selectedCity, setSelectedCity] = useState<LegistarCity | null>(null);
  const [startDate, setStartDate] = useState('2024-01-01');
  const [endDate, setEndDate] = useState(new Date().toISOString().slice(0, 10));
  const [docTypes, setDocTypes] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [manifest, setManifest] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open) return;
    client.getLegistarCities().then((res) => setCities(res.cities)).catch(() => {});
  }, [open, client]);

  // Poll retrieval job
  useEffect(() => {
    if (!jobId || jobStatus === 'complete' || jobStatus === 'error') return;
    const iv = setInterval(async () => {
      try {
        const status = await client.getRetrievalStatus(jobId);
        setJobStatus(status.status);
        if (status.status === 'complete') {
          setManifest(status.manifest);
          clearInterval(iv);
          onFilesRetrieved();
        } else if (status.status === 'error') {
          setError(status.error ?? 'Retrieval failed');
          clearInterval(iv);
        }
      } catch { /* keep polling */ }
    }, 2000);
    return () => clearInterval(iv);
  }, [jobId, jobStatus, client, onFilesRetrieved]);

  const filteredCities = cities.filter((c) =>
    `${c.city} ${c.state}`.toLowerCase().includes(search.toLowerCase())
  ).slice(0, 10);

  const handleStart = async () => {
    if (!selectedCity) { setError('Select a city first.'); return; }
    setError(null);
    setLoading(true);
    setManifest(null);
    try {
      const types = docTypes.split(',').map(s => s.trim()).filter(Boolean);
      const res = await client.startLegistarRetrieval({
        client_id: selectedCity.client_id,
        start_date: startDate,
        end_date: endDate,
        matter_types: types.length > 0 ? types : null,
      });
      setJobId(res.job_id);
      setJobStatus('pending');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to start retrieval');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card variant="bordered">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-2">
          <span className="text-xl" aria-hidden="true">🏛️</span>
          <div>
            <p className="font-medium text-gray-900 text-sm">Retrieve from Legistar</p>
            <p className="text-xs text-gray-500">Download legislative documents directly from a city's Legistar portal</p>
          </div>
        </div>
        <span className="text-gray-400 text-sm">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="mt-4 space-y-4 border-t border-gray-100 pt-4">
          {/* City search */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">City</label>
            <input
              type="text"
              placeholder="Search city name…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setSelectedCity(null); }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
            {search && filteredCities.length > 0 && !selectedCity && (
              <ul className="mt-1 border border-gray-200 rounded-lg bg-white shadow-sm max-h-48 overflow-y-auto">
                {filteredCities.map((c) => (
                  <li key={c.client_id}>
                    <button
                      onClick={() => { setSelectedCity(c); setSearch(`${c.city}, ${c.state}`); }}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 transition-colors"
                    >
                      {c.city}, {c.state}
                      <span className="ml-2 text-xs text-gray-400 font-mono">{c.client_id}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {selectedCity && (
              <p className="mt-1 text-xs text-green-600">
                ✓ {selectedCity.city}, {selectedCity.state} (client: {selectedCity.client_id})
              </p>
            )}
          </div>

          {/* Date range */}
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 mb-1">Start date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs font-medium text-gray-700 mb-1">End date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Document type filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Document types <span className="font-normal text-gray-400">(comma-separated, leave blank for all)</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Contract, Resolution, Ordinance"
              value={docTypes}
              onChange={(e) => setDocTypes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status / progress */}
          {jobStatus && jobStatus !== 'complete' && jobStatus !== 'error' && (
            <div className="flex items-center gap-2 text-sm text-blue-700">
              <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              Retrieving documents ({jobStatus})…
            </div>
          )}

          {manifest && (
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
              Retrieved {String(manifest.downloaded_count ?? 0)} document{manifest.downloaded_count !== 1 ? 's' : ''} from {String(manifest.matter_count ?? 0)} matters.
              {Number(manifest.failed_count) > 0 && (
                <span className="ml-1 text-yellow-700"> ({String(manifest.failed_count)} failed)</span>
              )}
              {' '}Documents added to upload list.
            </div>
          )}

          {error && (
            <p className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3">{error}</p>
          )}

          <button
            onClick={handleStart}
            disabled={loading || (!!jobStatus && jobStatus !== 'complete' && jobStatus !== 'error')}
            className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 transition-colors"
          >
            {loading || (jobStatus && jobStatus !== 'complete' && jobStatus !== 'error')
              ? 'Retrieving…'
              : 'Start Retrieval'}
          </button>
        </div>
      )}
    </Card>
  );
}

async function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.json', '.txt', '.xml'];
const ACCEPTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png'];
const ACCEPTED_MIME =
  'application/pdf,application/json,text/plain,text/xml,application/xml';
const ACCEPTED_IMAGE_MIME = 'image/jpeg,image/png';
const MAX_RETRIES = 2;

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function SeverityDot({ severity }: { severity: string }) {
  const colors: Record<string, string> = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-blue-400',
  };
  return (
    <span
      className={`inline-block w-2.5 h-2.5 rounded-full mr-1 ${colors[severity] ?? 'bg-gray-400'}`}
    />
  );
}

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const imageInputRef = useRef<HTMLInputElement>(null);

  const [uploadedFiles, setUploadedFiles] = useState<FileMetadata[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<AuditStatus | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const client = getAPIClient();

  // -------------------------------------------------------------------------
  // File upload
  // -------------------------------------------------------------------------

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files).filter((f) => {
        const ext = '.' + f.name.split('.').pop()?.toLowerCase();
        return ACCEPTED_EXTENSIONS.includes(ext);
      });

      if (fileArray.length === 0) {
        setError('No supported files found. Accepted: PDF, JSON, TXT, XML');
        return;
      }

      setError(null);
      setIsUploading(true);

      for (const file of fileArray) {
        let lastError: string | null = null;
        for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
          try {
            if (attempt > 0) await sleep(1000 * attempt);
            const meta = await client.uploadFile(file, (pct) => {
              setUploadProgress((prev) => ({ ...prev, [file.name]: pct }));
            });
            setUploadedFiles((prev) => [...prev, meta]);
            setUploadProgress((prev) => {
              const next = { ...prev };
              delete next[file.name];
              return next;
            });
            lastError = null;
            break;
          } catch {
            lastError = `Failed to upload "${file.name}"${attempt < MAX_RETRIES ? ` (retry ${attempt + 1}/${MAX_RETRIES})` : '. Check that the server is running.'}`;
          }
        }
        if (lastError) setError(lastError);
      }

      setIsUploading(false);
    },
    [client],
  );

  // Image upload (OCR)
  const handleImages = useCallback(
    async (files: FileList | File[]) => {
      const imageArray = Array.from(files).filter((f) => {
        const ext = '.' + f.name.split('.').pop()?.toLowerCase();
        return ACCEPTED_IMAGE_EXTENSIONS.includes(ext);
      });

      if (imageArray.length === 0) {
        setError('No supported images. Accepted: JPEG, PNG');
        return;
      }

      setError(null);
      setIsUploading(true);

      for (const file of imageArray) {
        let lastError: string | null = null;
        for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
          try {
            if (attempt > 0) await sleep(1000 * attempt);
            setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));
            const result = await client.uploadImage(file);
            const meta: FileMetadata = {
              file_id: result.file_id,
              name: result.name,
              size: result.size,
              sha256: result.sha256,
              format: result.format,
              uploaded_at: result.uploaded_at,
            };
            setUploadedFiles((prev) => [...prev, meta]);
            setUploadProgress((prev) => {
              const next = { ...prev };
              delete next[file.name];
              return next;
            });
            lastError = null;
            break;
          } catch {
            lastError = `Failed to process image "${file.name}"${attempt < MAX_RETRIES ? ` (retry ${attempt + 1}/${MAX_RETRIES})` : '. Check that the server is running.'}`;
          }
        }
        if (lastError) setError(lastError);
      }

      setIsUploading(false);
    },
    [client],
  );

  // -------------------------------------------------------------------------
  // Drag-and-drop handlers
  // -------------------------------------------------------------------------

  const onDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        handleFiles(e.dataTransfer.files);
      }
    },
    [handleFiles],
  );

  // -------------------------------------------------------------------------
  // Remove file
  // -------------------------------------------------------------------------

  const removeFile = useCallback(
    async (fileId: string) => {
      try {
        await client.deleteUploadedFile(fileId);
        setUploadedFiles((prev) => prev.filter((f) => f.file_id !== fileId));
      } catch {
        setError('Failed to remove file.');
      }
    },
    [client],
  );

  // -------------------------------------------------------------------------
  // Run audit
  // -------------------------------------------------------------------------

  const runAudit = useCallback(async () => {
    if (uploadedFiles.length === 0) return;
    setError(null);
    setIsRunning(true);
    try {
      const result = await client.runAudit(uploadedFiles.map((f) => f.file_id));
      setActiveJobId(result.job_id);
    } catch {
      setError('Failed to start audit. Check that the server is running.');
      setIsRunning(false);
    }
  }, [client, uploadedFiles]);

  // -------------------------------------------------------------------------
  // Poll job status
  // -------------------------------------------------------------------------

  useEffect(() => {
    if (!activeJobId) return;
    if (jobStatus?.status === 'complete' || jobStatus?.status === 'error') return;

    const interval = setInterval(async () => {
      try {
        const status = await client.getAuditStatus(activeJobId);
        setJobStatus(status);
        if (status.status === 'complete') {
          clearInterval(interval);
          router.push(`/results?job_id=${activeJobId}`);
        } else if (status.status === 'error') {
          clearInterval(interval);
          setError(`Audit failed: ${status.error ?? 'Unknown error'}`);
          setIsRunning(false);
        }
      } catch {
        // server may be busy — keep polling
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [activeJobId, jobStatus?.status, client, router]);

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-1">Upload Documents</h2>
          <p className="text-gray-600 text-sm">
            Drop legislative documents here, then click <strong>Run Audit</strong> to analyze them.
            Supports PDF, JSON, TXT, and XML.
          </p>
        </div>

        {/* Legistar retrieval */}
        <LegistarPanel
          onFilesRetrieved={async () => {
            try {
              const res = await client.listUploadedFiles();
              setUploadedFiles(res.files as FileMetadata[]);
            } catch { /* best-effort */ }
          }}
        />

        {/* Drop zone */}
        <div
          role="button"
          tabIndex={0}
          aria-label="Drop zone for file uploads"
          onDragEnter={onDragEnter}
          onDragLeave={onDragLeave}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onClick={() => fileInputRef.current?.click()}
          onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
            transition-colors duration-200 select-none
            ${isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'
            }
          `}
        >
          <div className="text-5xl mb-3">{isDragging ? '📂' : '📄'}</div>
          <p className="text-lg font-medium text-gray-700 mb-1">
            {isDragging ? 'Drop files to upload' : 'Drag & drop files here'}
          </p>
          <p className="text-sm text-gray-500">or click to choose files</p>
          <p className="text-xs text-gray-400 mt-2">PDF · JSON · TXT · XML · multiple files OK</p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_MIME}
          className="hidden"
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        {/* Camera capture (mobile) */}
        <input
          ref={cameraInputRef}
          type="file"
          accept={ACCEPTED_IMAGE_MIME}
          capture="environment"
          className="hidden"
          onChange={(e) => e.target.files && handleImages(e.target.files)}
        />
        {/* Image file picker */}
        <input
          ref={imageInputRef}
          type="file"
          multiple
          accept={ACCEPTED_IMAGE_MIME}
          className="hidden"
          onChange={(e) => e.target.files && handleImages(e.target.files)}
        />

        {/* Mobile-friendly alternative buttons */}
        <div className="flex gap-3 mt-2">
          <button
            type="button"
            onClick={() => imageInputRef.current?.click()}
            disabled={isUploading || isRunning}
            className="flex-1 flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <span aria-hidden="true">🖼️</span> From Gallery
          </button>
          <button
            type="button"
            onClick={() => cameraInputRef.current?.click()}
            disabled={isUploading || isRunning}
            className="flex-1 flex items-center justify-center gap-2 py-3 px-4 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <span aria-hidden="true">📷</span> Use Camera
          </button>
        </div>

        {/* Upload progress */}
        {Object.entries(uploadProgress).length > 0 && (
          <Card variant="bordered">
            <p className="text-sm font-medium text-gray-700 mb-3">Uploading…</p>
            {Object.entries(uploadProgress).map(([name, pct]) => (
              <div key={name} className="mb-2">
                <div className="flex justify-between text-xs text-gray-600 mb-1">
                  <span className="truncate max-w-xs">{name}</span>
                  <span>{pct}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-blue-600 h-1.5 rounded-full transition-all duration-200"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            ))}
          </Card>
        )}

        {/* Uploaded file list */}
        {uploadedFiles.length > 0 && (
          <Card
            title={`${uploadedFiles.length} file${uploadedFiles.length !== 1 ? 's' : ''} ready`}
            variant="bordered"
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-gray-500">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Size</th>
                    <th className="pb-2 pr-4 font-medium">Format</th>
                    <th className="pb-2 pr-4 font-medium">SHA-256</th>
                    <th className="pb-2 font-medium" />
                  </tr>
                </thead>
                <tbody>
                  {uploadedFiles.map((f) => (
                    <tr key={f.file_id} className="border-b border-gray-100 last:border-0">
                      <td className="py-2 pr-4 font-medium text-gray-800 truncate max-w-[180px]">
                        {f.name}
                      </td>
                      <td className="py-2 pr-4 text-gray-600">{formatBytes(f.size)}</td>
                      <td className="py-2 pr-4">
                        <span className="px-2 py-0.5 bg-gray-100 rounded text-xs uppercase font-mono text-gray-600">
                          {f.format}
                        </span>
                      </td>
                      <td className="py-2 pr-4 font-mono text-xs text-gray-400">
                        {f.sha256.slice(0, 12)}…
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => removeFile(f.file_id)}
                          disabled={isRunning}
                          className="text-red-500 hover:text-red-700 text-xs disabled:opacity-40"
                          title="Remove file"
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Error */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* Audit progress */}
        {activeJobId && jobStatus && (
          <Card variant="bordered">
            <div className="flex items-center gap-3 mb-3">
              {jobStatus.status !== 'error' && (
                <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
              )}
              <span className="font-medium text-gray-800">
                {jobStatus.status === 'complete'
                  ? 'Audit complete — redirecting…'
                  : jobStatus.status === 'error'
                    ? 'Audit failed'
                    : jobStatus.progress.phase}
              </span>
            </div>
            {jobStatus.progress.total_docs > 0 && (
              <div>
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>
                    {jobStatus.progress.docs_processed} / {jobStatus.progress.total_docs} documents
                  </span>
                  <span>{jobStatus.progress.findings_count} findings so far</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{
                      width: `${
                        (jobStatus.progress.docs_processed /
                          jobStatus.progress.total_docs) *
                        100
                      }%`,
                    }}
                  />
                </div>
              </div>
            )}
          </Card>
        )}

        {/* Run Audit button */}
        <button
          onClick={runAudit}
          disabled={uploadedFiles.length === 0 || isUploading || isRunning}
          className={`
            w-full py-4 px-6 rounded-xl font-semibold text-lg transition-colors duration-200
            ${
              uploadedFiles.length === 0 || isUploading || isRunning
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg'
            }
          `}
        >
          {isRunning
            ? 'Audit running…'
            : isUploading
              ? 'Uploading…'
              : uploadedFiles.length === 0
                ? 'Upload files to begin'
                : `Run Audit on ${uploadedFiles.length} file${uploadedFiles.length !== 1 ? 's' : ''}`}
        </button>
      </div>
    </DashboardLayout>
  );
}
