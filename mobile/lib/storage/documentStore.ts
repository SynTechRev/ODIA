/**
 * Document Storage Layer.
 *
 * Provides offline-first document storage using AsyncStorage for metadata
 * and FileSystem for document content. All data stays on-device.
 */

import { StoredDocument, StoredAnalysisResult, AnalysisResult } from '../analysis/types';

/** Storage key prefixes */
const KEYS = {
  DOCUMENT_LIST: '@odia/documents',
  DOCUMENT_PREFIX: '@odia/doc/',
  RESULT_PREFIX: '@odia/result/',
  SETTINGS: '@odia/settings',
} as const;

/**
 * In-memory storage fallback for environments without AsyncStorage.
 * This allows the storage layer to work in tests and non-React-Native contexts.
 */
class InMemoryStorage {
  private store: Map<string, string> = new Map();

  async getItem(key: string): Promise<string | null> {
    return this.store.get(key) ?? null;
  }

  async setItem(key: string, value: string): Promise<void> {
    this.store.set(key, value);
  }

  async removeItem(key: string): Promise<void> {
    this.store.delete(key);
  }

  async getAllKeys(): Promise<string[]> {
    return Array.from(this.store.keys());
  }

  async multiGet(keys: string[]): Promise<Array<[string, string | null]>> {
    return keys.map((key) => [key, this.store.get(key) ?? null]);
  }

  async multiRemove(keys: string[]): Promise<void> {
    for (const key of keys) {
      this.store.delete(key);
    }
  }

  clear(): void {
    this.store.clear();
  }
}

/** Storage backend interface */
interface StorageBackend {
  getItem(key: string): Promise<string | null>;
  setItem(key: string, value: string): Promise<void>;
  removeItem(key: string): Promise<void>;
  getAllKeys(): Promise<string[]>;
  multiGet(keys: string[]): Promise<Array<[string, string | null]>>;
  multiRemove(keys: string[]): Promise<void>;
}

/** Global storage backend — can be swapped for testing */
let storage: StorageBackend = new InMemoryStorage();

/**
 * Set the storage backend. Call this at app startup to inject AsyncStorage.
 * For tests, the default InMemoryStorage is used.
 */
export function setStorageBackend(backend: StorageBackend): void {
  storage = backend;
}

/** Reset storage to in-memory (for testing) */
export function resetStorage(): void {
  const memStorage = new InMemoryStorage();
  storage = memStorage;
}

/** Generate a unique document ID */
function generateId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `${timestamp}-${random}`;
}

/**
 * Save a new document to storage.
 */
export async function saveDocument(
  title: string,
  text: string,
  metadata: Record<string, unknown> = {}
): Promise<StoredDocument> {
  const id = generateId();
  const now = new Date().toISOString();

  const doc: StoredDocument = {
    id,
    title,
    text,
    metadata,
    createdAt: now,
    updatedAt: now,
  };

  // Save document data
  await storage.setItem(
    `${KEYS.DOCUMENT_PREFIX}${id}`,
    JSON.stringify(doc)
  );

  // Update document list
  const listRaw = await storage.getItem(KEYS.DOCUMENT_LIST);
  const list: string[] = listRaw ? JSON.parse(listRaw) : [];
  list.unshift(id);
  await storage.setItem(KEYS.DOCUMENT_LIST, JSON.stringify(list));

  return doc;
}

/**
 * Get a document by ID.
 */
export async function getDocument(id: string): Promise<StoredDocument | null> {
  const raw = await storage.getItem(`${KEYS.DOCUMENT_PREFIX}${id}`);
  if (!raw) return null;
  return JSON.parse(raw) as StoredDocument;
}

/**
 * Get all stored documents, ordered by creation date (newest first).
 */
export async function listDocuments(): Promise<StoredDocument[]> {
  const listRaw = await storage.getItem(KEYS.DOCUMENT_LIST);
  if (!listRaw) return [];

  const ids: string[] = JSON.parse(listRaw);
  const keys = ids.map((id) => `${KEYS.DOCUMENT_PREFIX}${id}`);
  const pairs = await storage.multiGet(keys);

  const docs: StoredDocument[] = [];
  for (const [, value] of pairs) {
    if (value) {
      docs.push(JSON.parse(value) as StoredDocument);
    }
  }

  return docs;
}

/**
 * Delete a document and its associated analysis results.
 */
export async function deleteDocument(id: string): Promise<void> {
  // Remove document
  await storage.removeItem(`${KEYS.DOCUMENT_PREFIX}${id}`);

  // Remove associated results
  await storage.removeItem(`${KEYS.RESULT_PREFIX}${id}`);

  // Update list
  const listRaw = await storage.getItem(KEYS.DOCUMENT_LIST);
  if (listRaw) {
    const list: string[] = JSON.parse(listRaw);
    const filtered = list.filter((docId) => docId !== id);
    await storage.setItem(KEYS.DOCUMENT_LIST, JSON.stringify(filtered));
  }
}

/**
 * Save an analysis result for a document.
 */
export async function saveAnalysisResult(
  documentId: string,
  result: AnalysisResult
): Promise<StoredAnalysisResult> {
  const stored: StoredAnalysisResult = {
    id: generateId(),
    documentId,
    result,
    createdAt: new Date().toISOString(),
  };

  await storage.setItem(
    `${KEYS.RESULT_PREFIX}${documentId}`,
    JSON.stringify(stored)
  );

  return stored;
}

/**
 * Get the analysis result for a document.
 */
export async function getAnalysisResult(
  documentId: string
): Promise<StoredAnalysisResult | null> {
  const raw = await storage.getItem(`${KEYS.RESULT_PREFIX}${documentId}`);
  if (!raw) return null;
  return JSON.parse(raw) as StoredAnalysisResult;
}

/**
 * Get the count of stored documents.
 */
export async function getDocumentCount(): Promise<number> {
  const listRaw = await storage.getItem(KEYS.DOCUMENT_LIST);
  if (!listRaw) return 0;
  const list: string[] = JSON.parse(listRaw);
  return list.length;
}
