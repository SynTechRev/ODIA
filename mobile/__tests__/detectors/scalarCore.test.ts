import { computeRecursiveScalarScore, SEVERITY_WEIGHTS } from '../../lib/analysis/scalarCore';
import { Anomaly, NormalizedDocument } from '../../lib/analysis/types';

describe('computeRecursiveScalarScore', () => {
  const emptyDoc: NormalizedDocument = {};

  it('returns 1.0 when no anomalies', () => {
    expect(computeRecursiveScalarScore(emptyDoc, [])).toBe(1.0);
  });

  it('returns 1.0 for null/undefined anomalies', () => {
    expect(computeRecursiveScalarScore(emptyDoc, null as any)).toBe(1.0);
  });

  it('reduces score based on severity weights', () => {
    const anomalies: Anomaly[] = [
      { id: 'test:1', issue: 'Test', severity: 'low', layer: 'test', details: {} },
    ];
    const score = computeRecursiveScalarScore(emptyDoc, anomalies);
    expect(score).toBe(1.0 - SEVERITY_WEIGHTS.low);
  });

  it('accumulates penalties for multiple anomalies', () => {
    const anomalies: Anomaly[] = [
      { id: 'test:1', issue: 'Test', severity: 'high', layer: 'test', details: {} },
      { id: 'test:2', issue: 'Test', severity: 'high', layer: 'test', details: {} },
    ];
    const score = computeRecursiveScalarScore(emptyDoc, anomalies);
    expect(score).toBe(1.0 - SEVERITY_WEIGHTS.high * 2);
  });

  it('clamps score to minimum 0.0', () => {
    const anomalies: Anomaly[] = Array.from({ length: 20 }, (_, i) => ({
      id: `test:${i}`,
      issue: 'Test',
      severity: 'high' as const,
      layer: 'test',
      details: {},
    }));
    const score = computeRecursiveScalarScore(emptyDoc, anomalies);
    expect(score).toBe(0.0);
  });

  it('applies coherence bonus for documents with provenance', () => {
    const doc: NormalizedDocument = {
      provenance: { hash: 'abc123' },
      references: ['ref1'],
      metadata: { key: 'value' },
    };
    const anomalies: Anomaly[] = [
      { id: 'test:1', issue: 'Test', severity: 'high', layer: 'test', details: {} },
    ];
    const scoreWithBonus = computeRecursiveScalarScore(doc, anomalies);
    const scoreWithoutBonus = computeRecursiveScalarScore(emptyDoc, anomalies);
    expect(scoreWithBonus).toBeGreaterThan(scoreWithoutBonus);
  });

  it('uses default weight for unknown severity', () => {
    const anomalies: Anomaly[] = [
      { id: 'test:1', issue: 'Test', severity: 'unknown' as any, layer: 'test', details: {} },
    ];
    const score = computeRecursiveScalarScore(emptyDoc, anomalies);
    // Default weight is 0.05 (same as medium)
    expect(score).toBe(1.0 - 0.05);
  });
});

describe('SEVERITY_WEIGHTS', () => {
  it('has correct values matching Python implementation', () => {
    expect(SEVERITY_WEIGHTS.low).toBe(0.02);
    expect(SEVERITY_WEIGHTS.medium).toBe(0.05);
    expect(SEVERITY_WEIGHTS.high).toBe(0.10);
  });
});
