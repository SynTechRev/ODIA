import { detectSurveillanceAnomalies } from '../../lib/analysis/detectors/surveillance';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectSurveillanceAnomalies', () => {
  it('returns empty for non-object input', () => {
    expect(detectSurveillanceAnomalies(null as any)).toEqual([]);
  });

  it('returns empty for document with no text', () => {
    expect(detectSurveillanceAnomalies({} as NormalizedDocument)).toEqual([]);
  });

  it('detects outsourced surveillance without safeguards', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The surveillance monitoring system will be operated by a contractor vendor.',
    };
    const result = detectSurveillanceAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'surveillance:outsourced-without-safeguards',
          severity: 'high',
          layer: 'surveillance',
        }),
      ])
    );
  });

  it('detects outsourced with safeguards (low severity)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The surveillance system operated by contractor requires a warrant and court order.',
    };
    const result = detectSurveillanceAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'surveillance:outsourced-with-safeguards',
          severity: 'low',
        }),
      ])
    );
  });

  it('returns empty when only surveillance keywords present (no contractor)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The surveillance monitoring tracking system is active.',
    };
    expect(detectSurveillanceAnomalies(doc)).toEqual([]);
  });

  it('returns empty when only contractor keywords present (no surveillance)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The contractor vendor provides office supplies.',
    };
    expect(detectSurveillanceAnomalies(doc)).toEqual([]);
  });

  it('limits keyword arrays in details', () => {
    const doc: NormalizedDocument = {
      raw_text:
        'surveillance monitoring tracking biometric facial recognition data collection contractor vendor third party',
    };
    const result = detectSurveillanceAnomalies(doc);
    const anomaly = result[0];
    expect((anomaly.details.surveillance_keywords as string[]).length).toBeLessThanOrEqual(3);
    expect((anomaly.details.contractor_keywords as string[]).length).toBeLessThanOrEqual(2);
  });
});
