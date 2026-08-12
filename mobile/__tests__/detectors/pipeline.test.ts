import { runFullAnalysis } from '../../lib/analysis/pipeline';

describe('runFullAnalysis', () => {
  it('returns complete result structure', () => {
    const result = runFullAnalysis('Sample text', { title: 'Test' });
    expect(result).toHaveProperty('metadata');
    expect(result).toHaveProperty('findings');
    expect(result).toHaveProperty('severity_score');
    expect(result).toHaveProperty('lattice_score');
    expect(result).toHaveProperty('coherence_bonus');
    expect(result).toHaveProperty('flags');
    expect(result).toHaveProperty('summary');
    expect(result).toHaveProperty('timestamp');

    expect(result.findings).toHaveProperty('fiscal');
    expect(result.findings).toHaveProperty('constitutional');
    expect(result.findings).toHaveProperty('surveillance');
  });

  it('includes jurisdiction when provided', () => {
    const result = runFullAnalysis('Text', { title: 'Test' }, {
      jurisdictionName: 'federal',
    });
    expect(result.jurisdiction).toBe('federal');
  });

  it('does not include jurisdiction when not provided', () => {
    const result = runFullAnalysis('Text', { title: 'Test' });
    expect(result.jurisdiction).toBeUndefined();
  });

  it('generates summary for clean document', () => {
    const result = runFullAnalysis('A simple clean document.', {
      title: 'Test',
      hash: 'abc123',
    });
    expect(result.summary).toContain('No anomalies detected');
  });

  it('generates summary with anomaly counts', () => {
    const result = runFullAnalysis(
      'The cost is $1,000,000 for the contractor vendor surveillance system.',
      { title: 'Test' }
    );
    expect(result.summary).toContain('detected');
    expect(result.summary).toContain('anomal');
  });

  it('severity_score is 0 for clean document', () => {
    const result = runFullAnalysis('Clean text.', {
      title: 'Test',
      hash: 'abc',
    });
    expect(result.severity_score).toBe(0.0);
  });

  it('lattice_score is 1.0 for clean document with hash', () => {
    const result = runFullAnalysis('Clean text.', {
      title: 'Test',
      hash: 'abc',
    });
    expect(result.lattice_score).toBe(1.0);
  });

  it('adds provenance when hash in metadata', () => {
    const result = runFullAnalysis('Text.', {
      title: 'Test',
      hash: 'sha256-test',
    });
    // Should not have provenance hash missing anomaly in fiscal findings
    const fiscalHashAnomaly = result.findings.fiscal.find(
      (a) => a.id === 'fiscal:missing-provenance-hash'
    );
    expect(fiscalHashAnomaly).toBeUndefined();
  });

  it('flags high-severity anomalies', () => {
    const result = runFullAnalysis(
      'surveillance monitoring tracking contractor vendor no safeguards.',
      { title: 'Test', hash: 'abc' }
    );
    expect(result.flags.length).toBeGreaterThan(0);
  });

  it('timestamp is valid ISO string', () => {
    const result = runFullAnalysis('Text', { title: 'Test' });
    const date = new Date(result.timestamp);
    expect(date.getTime()).not.toBeNaN();
  });

  it('handles singular anomaly word', () => {
    // Create a document that generates exactly 1 anomaly
    const result = runFullAnalysis('Clean document.', { title: 'Test', hash: 'x' });
    // Score should be high
    expect(result.lattice_score).toBeGreaterThan(0.5);
  });
});
