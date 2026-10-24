import { detectSignatureAnomalies } from '../../lib/analysis/detectors/signatureChain';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectSignatureAnomalies', () => {
  it('returns empty for non-object input', () => {
    expect(detectSignatureAnomalies(null as any)).toEqual([]);
  });

  it('returns empty for document with no text', () => {
    expect(detectSignatureAnomalies({} as NormalizedDocument)).toEqual([]);
  });

  it('detects unsigned instrument without dollar amounts (high severity)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This agreement contract is unsigned and requires signature.',
    };
    const result = detectSignatureAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'signature:unsigned-instrument',
          severity: 'high',
          layer: 'signature',
        }),
      ])
    );
  });

  it('detects unsigned instrument with dollar amounts (critical severity)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This contract for $1,000,000 has signature block blank.',
    };
    const result = detectSignatureAnomalies(doc);
    const anomaly = result.find((a) => a.id === 'signature:unsigned-instrument');
    expect(anomaly?.severity).toBe('critical');
  });

  it('does not flag when no instrument keywords present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This document is unsigned and pending review.',
    };
    const result = detectSignatureAnomalies(doc);
    expect(result.find((a) => a.id === 'signature:unsigned-instrument')).toBeUndefined();
  });

  it('detects underscore signature lines', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Signed: __________ for the MOU agreement.',
    };
    const result = detectSignatureAnomalies(doc);
    expect(result.find((a) => a.id === 'signature:unsigned-instrument')).toBeDefined();
  });

  it('detects DocuSign pending', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The PSA was sent via DocuSign and is still pending completion.',
    };
    const result = detectSignatureAnomalies(doc);
    expect(result.find((a) => a.id === 'signature:unsigned-instrument')).toBeDefined();
  });

  it('returns empty when no gaps detected in instrument', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This contract has been fully executed by all parties.',
    };
    const result = detectSignatureAnomalies(doc);
    expect(result.find((a) => a.id === 'signature:unsigned-instrument')).toBeUndefined();
  });
});
