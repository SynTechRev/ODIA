import { detectGovernanceGapAnomalies } from '../../lib/analysis/detectors/governanceGap';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectGovernanceGapAnomalies', () => {
  it('returns empty for non-object input', () => {
    expect(detectGovernanceGapAnomalies(null as any)).toEqual([]);
  });

  it('returns empty for document with no text', () => {
    expect(detectGovernanceGapAnomalies({} as NormalizedDocument)).toEqual([]);
  });

  it('detects surveillance tech without governance (critical)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The ALPR facial recognition drone system is deployed citywide.',
    };
    const result = detectGovernanceGapAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'governance:capability-without-policy',
          severity: 'critical',
          layer: 'governance',
        }),
      ])
    );
  });

  it('detects data/AI capability without governance (high)', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The automated machine learning report writing system processes data.',
    };
    const result = detectGovernanceGapAnomalies(doc);
    const anomaly = result.find((a) => a.id === 'governance:capability-without-policy');
    expect(anomaly?.severity).toBe('high');
  });

  it('does not flag when governance keywords present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The drone system operates under a privacy policy with oversight and council approval.',
    };
    const result = detectGovernanceGapAnomalies(doc);
    expect(result.find((a) => a.id === 'governance:capability-without-policy')).toBeUndefined();
  });

  it('detects data retention gap', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The data sharing and third-party access system stores all records with oversight.',
    };
    const result = detectGovernanceGapAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'governance:data-retention-gap',
          severity: 'high',
        }),
      ])
    );
  });

  it('does not flag data retention gap when retention policy present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Data sharing operates under a retention policy with deletion policy guidelines.',
    };
    const result = detectGovernanceGapAnomalies(doc);
    expect(result.find((a) => a.id === 'governance:data-retention-gap')).toBeUndefined();
  });
});
