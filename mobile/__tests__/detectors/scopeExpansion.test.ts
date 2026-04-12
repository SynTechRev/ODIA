import { detectScopeExpansionAnomalies, parseDollarAmount } from '../../lib/analysis/detectors/scopeExpansion';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('parseDollarAmount', () => {
  it('parses standard amounts', () => {
    expect(parseDollarAmount('$1,000,000')).toBe(1000000);
    expect(parseDollarAmount('$500.00')).toBe(500);
  });

  it('parses M/B/T suffixes', () => {
    expect(parseDollarAmount('$1.5M')).toBe(1500000);
    expect(parseDollarAmount('$2B')).toBe(2000000000);
    expect(parseDollarAmount('$1T')).toBe(1000000000000);
  });

  it('parses "illion" suffixes', () => {
    expect(parseDollarAmount('$2 Million')).toBe(2000000);
    expect(parseDollarAmount('$3 Billion')).toBe(3000000000);
  });

  it('returns null for invalid input', () => {
    expect(parseDollarAmount('not a number')).toBeNull();
  });
});

describe('detectScopeExpansionAnomalies', () => {
  it('returns empty for non-object input', () => {
    expect(detectScopeExpansionAnomalies(null as any)).toEqual([]);
  });

  it('returns empty when no amendment keywords', () => {
    const doc: NormalizedDocument = {
      raw_text: 'A standard contract for $1,000,000.',
    };
    expect(detectScopeExpansionAnomalies(doc)).toEqual([]);
  });

  it('detects significant expansion (>50%)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Amendment to original contract: $500,000 expanded to $1,000,000.',
    };
    const result = detectScopeExpansionAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'scope:significant-expansion',
          severity: 'high',
          layer: 'scope',
        }),
      ])
    );
    const anomaly = result.find((a) => a.id === 'scope:significant-expansion');
    expect(anomaly!.details.expansion_percentage).toBe(100);
  });

  it('detects amendment without baseline', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This amendment modifies the terms of service.',
    };
    const result = detectScopeExpansionAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'scope:amendment-without-baseline',
          severity: 'medium',
        }),
      ])
    );
  });

  it('does not flag amendment-without-baseline when baseline present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This amendment references the original contract terms.',
    };
    const result = detectScopeExpansionAnomalies(doc);
    expect(result.find((a) => a.id === 'scope:amendment-without-baseline')).toBeUndefined();
  });

  it('detects sole-source expansion', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This sole-source amendment extends the existing contract with the original contract.',
    };
    const result = detectScopeExpansionAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'scope:sole-source-expansion',
          severity: 'high',
        }),
      ])
    );
  });

  it('detects single source pattern', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This single source amendment to the original contract.',
    };
    const result = detectScopeExpansionAnomalies(doc);
    expect(result.find((a) => a.id === 'scope:sole-source-expansion')).toBeDefined();
  });
});
