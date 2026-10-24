import { detectFiscalAnomalies, FISCAL_AMOUNT_PATTERN, APPROPRIATION_KEYWORDS } from '../../lib/analysis/detectors/fiscal';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectFiscalAnomalies', () => {
  it('returns empty array for non-object input', () => {
    expect(detectFiscalAnomalies(null as any)).toEqual([]);
    expect(detectFiscalAnomalies(undefined as any)).toEqual([]);
  });

  it('detects missing provenance hash', () => {
    const doc: NormalizedDocument = { raw_text: 'Some text' };
    const result = detectFiscalAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'fiscal:missing-provenance-hash',
          severity: 'low',
          layer: 'fiscal',
        }),
      ])
    );
  });

  it('does not flag missing provenance when hash exists', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Some text',
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:missing-provenance-hash')).toBeUndefined();
  });

  it('detects fiscal amounts without appropriation reference', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The contract is worth $1,000,000 and $500,000 for services.',
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'fiscal:amount-without-appropriation',
          severity: 'medium',
          layer: 'fiscal',
        }),
      ])
    );
    const amountAnomaly = result.find((a) => a.id === 'fiscal:amount-without-appropriation');
    expect(amountAnomaly!.details.amount_count).toBe(2);
  });

  it('does not flag amounts when appropriation keyword present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The budget appropriation is $1,000,000.',
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:amount-without-appropriation')).toBeUndefined();
  });

  it('handles documents with sections', () => {
    const doc: NormalizedDocument = {
      sections: [
        { content: 'The cost is $2,500,000.' },
        { content: 'Additional $500,000 requested.' },
      ],
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:amount-without-appropriation')).toBeDefined();
  });

  it('limits sample_amounts to 3', () => {
    const doc: NormalizedDocument = {
      raw_text: '$1,000 and $2,000 and $3,000 and $4,000 and $5,000 in the document.',
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    const anomaly = result.find((a) => a.id === 'fiscal:amount-without-appropriation');
    expect(anomaly).toBeDefined();
    expect((anomaly!.details.sample_amounts as string[]).length).toBeLessThanOrEqual(3);
  });

  it('handles $1.5M format', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Costs of $1.5M for the project.',
      provenance: { hash: 'abc123' },
    };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:amount-without-appropriation')).toBeDefined();
  });

  it('returns empty for document with no text', () => {
    const doc: NormalizedDocument = { provenance: { hash: 'abc123' } };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:amount-without-appropriation')).toBeUndefined();
  });

  it('handles empty provenance object', () => {
    const doc: NormalizedDocument = { raw_text: 'text', provenance: {} };
    const result = detectFiscalAnomalies(doc);
    expect(result.find((a) => a.id === 'fiscal:missing-provenance-hash')).toBeDefined();
  });
});

describe('FISCAL_AMOUNT_PATTERN', () => {
  it('matches standard dollar amounts', () => {
    expect('$1,000,000'.match(new RegExp(FISCAL_AMOUNT_PATTERN.source, 'gi'))).toBeTruthy();
    expect('$500.00'.match(new RegExp(FISCAL_AMOUNT_PATTERN.source, 'gi'))).toBeTruthy();
    expect('$1.5M'.match(new RegExp(FISCAL_AMOUNT_PATTERN.source, 'gi'))).toBeTruthy();
    expect('$2 Billion'.match(new RegExp(FISCAL_AMOUNT_PATTERN.source, 'gi'))).toBeTruthy();
  });
});
