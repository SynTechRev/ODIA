import {
  saveDocument,
  getDocument,
  listDocuments,
  deleteDocument,
  saveAnalysisResult,
  getAnalysisResult,
  getDocumentCount,
  resetStorage,
} from '../../lib/storage/documentStore';
import { AnalysisResult } from '../../lib/analysis/types';

describe('Document Storage', () => {
  beforeEach(() => {
    resetStorage();
  });

  describe('saveDocument', () => {
    it('saves and returns a document with generated ID', async () => {
      const doc = await saveDocument('Test Doc', 'Document text');
      expect(doc.id).toBeTruthy();
      expect(doc.title).toBe('Test Doc');
      expect(doc.text).toBe('Document text');
      expect(doc.createdAt).toBeTruthy();
    });
  });

  describe('getDocument', () => {
    it('retrieves a saved document', async () => {
      const saved = await saveDocument('Test', 'Text');
      const retrieved = await getDocument(saved.id);
      expect(retrieved).not.toBeNull();
      expect(retrieved!.id).toBe(saved.id);
      expect(retrieved!.title).toBe('Test');
    });

    it('returns null for unknown ID', async () => {
      const result = await getDocument('nonexistent');
      expect(result).toBeNull();
    });
  });

  describe('listDocuments', () => {
    it('returns empty array initially', async () => {
      const docs = await listDocuments();
      expect(docs).toEqual([]);
    });

    it('lists documents newest first', async () => {
      await saveDocument('Doc 1', 'Text 1');
      await saveDocument('Doc 2', 'Text 2');
      const docs = await listDocuments();
      expect(docs.length).toBe(2);
      expect(docs[0].title).toBe('Doc 2');
    });
  });

  describe('deleteDocument', () => {
    it('removes a document', async () => {
      const saved = await saveDocument('Delete Me', 'Text');
      await deleteDocument(saved.id);
      const result = await getDocument(saved.id);
      expect(result).toBeNull();
    });

    it('updates the document list', async () => {
      const saved = await saveDocument('Delete Me', 'Text');
      await deleteDocument(saved.id);
      const docs = await listDocuments();
      expect(docs.length).toBe(0);
    });
  });

  describe('saveAnalysisResult / getAnalysisResult', () => {
    it('saves and retrieves analysis results', async () => {
      const mockResult: AnalysisResult = {
        metadata: {},
        findings: { fiscal: [], constitutional: [], surveillance: [] },
        severity_score: 0,
        lattice_score: 1.0,
        coherence_bonus: 0,
        flags: [],
        summary: 'Clean',
        timestamp: new Date().toISOString(),
      };

      const stored = await saveAnalysisResult('doc-1', mockResult);
      expect(stored.documentId).toBe('doc-1');

      const retrieved = await getAnalysisResult('doc-1');
      expect(retrieved).not.toBeNull();
      expect(retrieved!.result.summary).toBe('Clean');
    });

    it('returns null for unknown document', async () => {
      const result = await getAnalysisResult('nonexistent');
      expect(result).toBeNull();
    });
  });

  describe('getDocumentCount', () => {
    it('returns 0 initially', async () => {
      const count = await getDocumentCount();
      expect(count).toBe(0);
    });

    it('counts saved documents', async () => {
      await saveDocument('Doc 1', 'Text 1');
      await saveDocument('Doc 2', 'Text 2');
      const count = await getDocumentCount();
      expect(count).toBe(2);
    });
  });
});
