import { analyzeDocument } from '../../lib/analysis/auditEngine';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('analyzeDocument', () => {
  it('returns expected structure', () => {
    const doc: NormalizedDocument = { raw_text: 'Sample text' };
    const result = analyzeDocument(doc);
    expect(result).toHaveProperty('count');
    expect(result).toHaveProperty('score');
    expect(result).toHaveProperty('anomalies');
    expect(typeof result.count).toBe('number');
    expect(typeof result.score).toBe('number');
    expect(Array.isArray(result.anomalies)).toBe(true);
  });

  it('returns perfect score for clean document', () => {
    const doc: NormalizedDocument = {
      raw_text: 'A simple document with no issues.',
      provenance: { hash: 'sha256-valid' },
    };
    const result = analyzeDocument(doc);
    expect(result.count).toBe(0);
    expect(result.score).toBe(1.0);
  });

  it('detects fiscal anomalies', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The cost is $1,000,000 for services.',
    };
    const result = analyzeDocument(doc);
    expect(result.anomalies.some((a) => a.layer === 'fiscal')).toBe(true);
  });

  it('detects constitutional anomalies', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The Secretary may determine the appropriate measures at their discretion.',
      provenance: { hash: 'abc' },
    };
    const result = analyzeDocument(doc);
    expect(result.anomalies.some((a) => a.layer === 'constitutional')).toBe(true);
  });

  it('detects surveillance anomalies', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The surveillance monitoring system is operated by a contractor vendor.',
      provenance: { hash: 'abc' },
    };
    const result = analyzeDocument(doc);
    expect(result.anomalies.some((a) => a.layer === 'surveillance')).toBe(true);
  });

  it('score decreases with more anomalies', () => {
    const cleanDoc: NormalizedDocument = {
      raw_text: 'Clean document.',
      provenance: { hash: 'abc' },
    };
    const dirtyDoc: NormalizedDocument = {
      raw_text: 'The Secretary may determine at their discretion surveillance monitoring contractor.',
    };
    const cleanResult = analyzeDocument(cleanDoc);
    const dirtyResult = analyzeDocument(dirtyDoc);
    expect(dirtyResult.score).toBeLessThan(cleanResult.score);
  });

  it('handles empty document', () => {
    const doc: NormalizedDocument = {};
    const result = analyzeDocument(doc);
    expect(result.count).toBeGreaterThanOrEqual(0);
    expect(result.score).toBeLessThanOrEqual(1.0);
    expect(result.score).toBeGreaterThanOrEqual(0.0);
  });
});
