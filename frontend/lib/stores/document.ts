/**
 * Document Zustand store.
 */

import { create } from 'zustand';
import type { Document } from '@/lib/types/api';

interface DocumentState {
  documents: Document[];
  selectedDocument: Document | null;

  addDocument: (doc: Document) => void;
  selectDocument: (doc: Document | null) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  selectedDocument: null,

  addDocument: (doc) =>
    set((state) => ({
      documents: [...state.documents, doc],
    })),

  selectDocument: (doc) => set({ selectedDocument: doc }),
}));
