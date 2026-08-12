import { detectConstitutionalAnomalies } from '../../lib/analysis/detectors/constitutional';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectConstitutionalAnomalies', () => {
  it('returns empty array for non-object input', () => {
    expect(detectConstitutionalAnomalies(null as any)).toEqual([]);
  });

  it('returns empty for document with no text', () => {
    const doc: NormalizedDocument = {};
    expect(detectConstitutionalAnomalies(doc)).toEqual([]);
  });

  it('detects broad delegation without standards', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The Secretary may determine the appropriate levels and the Director shall establish new rules.',
    };
    const result = detectConstitutionalAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'constitutional:broad-delegation',
          severity: 'medium',
          layer: 'constitutional',
        }),
      ])
    );
  });

  it('does not flag delegation when standards are present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The Secretary may determine levels subject to the standard criteria established by Congress.',
    };
    const result = detectConstitutionalAnomalies(doc);
    expect(result.find((a) => a.id === 'constitutional:broad-delegation')).toBeUndefined();
  });

  it('detects "in their discretion" pattern', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The Commissioner may act in their discretion to implement new policies.',
    };
    const result = detectConstitutionalAnomalies(doc);
    expect(result.find((a) => a.id === 'constitutional:broad-delegation')).toBeDefined();
  });

  it('reports delegation_count in details', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The Secretary may determine X. The Administrator shall prescribe Y.',
    };
    const result = detectConstitutionalAnomalies(doc);
    const anomaly = result.find((a) => a.id === 'constitutional:broad-delegation');
    expect(anomaly).toBeDefined();
    expect(anomaly!.details.delegation_count).toBeGreaterThanOrEqual(2);
  });
});
