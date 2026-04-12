import { extractTextContent } from '../lib/analysis/textUtils';
import { NormalizedDocument } from '../lib/analysis/types';

describe('extractTextContent', () => {
  it('extracts from raw_text', () => {
    const doc: NormalizedDocument = { raw_text: 'Hello world' };
    expect(extractTextContent(doc)).toBe('Hello world');
  });

  it('extracts from sections', () => {
    const doc: NormalizedDocument = {
      sections: [
        { content: 'Section 1' },
        { content: 'Section 2' },
      ],
    };
    expect(extractTextContent(doc)).toBe('Section 1 Section 2');
  });

  it('combines raw_text and sections', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Raw text',
      sections: [{ content: 'Section content' }],
    };
    expect(extractTextContent(doc)).toBe('Raw text Section content');
  });

  it('returns empty string for empty document', () => {
    const doc: NormalizedDocument = {};
    expect(extractTextContent(doc)).toBe('');
  });

  it('handles non-string section content via String()', () => {
    const doc: NormalizedDocument = {
      sections: [{ content: 42 as any }],
    };
    expect(extractTextContent(doc)).toBe('42');
  });

  it('skips sections without content key', () => {
    const doc: NormalizedDocument = {
      sections: [{ section_id: 'no-content' } as any, { content: 'valid' }],
    };
    expect(extractTextContent(doc)).toBe('valid');
  });

  it('handles null sections gracefully', () => {
    const doc: NormalizedDocument = {
      sections: null as any,
    };
    expect(extractTextContent(doc)).toBe('');
  });
});
