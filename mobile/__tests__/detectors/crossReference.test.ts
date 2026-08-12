import { detectCrossJurisdictionRefs, crossReferenceAudit } from '../../lib/analysis/detectors/crossReference';

describe('detectCrossJurisdictionRefs', () => {
  it('returns empty for text with no citations', () => {
    expect(detectCrossJurisdictionRefs('No legal references here.')).toEqual([]);
  });

  it('detects USC + California cross-reference', () => {
    const text = '42 U.S.C. § 1983 and Cal. Penal Code provisions apply.';
    const result = detectCrossJurisdictionRefs(text);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: 'federal_state_cross_reference',
          severity: 'info',
        }),
      ])
    );
  });

  it('detects CFR + California cross-reference', () => {
    const text = '21 CFR § 50 and Cal. Civil Code provisions.';
    const result = detectCrossJurisdictionRefs(text);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: 'cfr_state_cross_reference',
        }),
      ])
    );
  });

  it('does not flag only federal references', () => {
    const text = '42 U.S.C. § 1983 and 18 U.S.C. § 1001.';
    expect(detectCrossJurisdictionRefs(text)).toEqual([]);
  });
});

describe('crossReferenceAudit', () => {
  it('returns empty for empty docs list', () => {
    expect(crossReferenceAudit([])).toEqual([]);
  });

  it('detects jurisdiction mismatch for federal doc with more state refs', () => {
    const docs = [
      {
        id: 'doc-1',
        text: 'Cal. Penal Code and Cal. Civil Code and Cal. Health Code but only 42 U.S.C. § 1983.',
        jurisdiction: 'federal',
      },
    ];
    const result = crossReferenceAudit(docs as any);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          issue: 'jurisdiction_mismatch',
          severity: 'warning',
        }),
      ])
    );
  });

  it('detects jurisdiction mismatch for state doc with more federal refs', () => {
    const docs = [
      {
        id: 'doc-2',
        text: '42 U.S.C. § 1983, 18 U.S.C. § 1001, 21 CFR § 50, no state refs.',
        jurisdiction: 'california',
      },
    ];
    const result = crossReferenceAudit(docs as any);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          issue: 'jurisdiction_mismatch',
          severity: 'warning',
        }),
      ])
    );
  });
});
