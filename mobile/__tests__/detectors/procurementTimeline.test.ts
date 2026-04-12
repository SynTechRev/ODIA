import { detectProcurementTimelineAnomalies } from '../../lib/analysis/detectors/procurementTimeline';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectProcurementTimelineAnomalies', () => {
  it('returns empty for non-array input', () => {
    expect(detectProcurementTimelineAnomalies(null as any)).toEqual([]);
    expect(detectProcurementTimelineAnomalies('not an array' as any)).toEqual([]);
  });

  it('returns empty for empty array', () => {
    expect(detectProcurementTimelineAnomalies([])).toEqual([]);
  });

  it('detects execution before authorization', () => {
    const docs: NormalizedDocument[] = [
      {
        document_id: 'contract-1',
        title: 'Service Agreement',
        execution_date: '2024-01-15',
        authorization_date: '2024-02-01',
      },
    ];
    const result = detectProcurementTimelineAnomalies(docs);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'procurement:execution-precedes-authorization',
          severity: 'high',
          layer: 'procurement',
        }),
      ])
    );
    expect(result[0].details.days_early).toBe(17);
  });

  it('does not flag when execution is after authorization', () => {
    const docs: NormalizedDocument[] = [
      {
        execution_date: '2024-03-01',
        authorization_date: '2024-02-01',
      },
    ];
    expect(detectProcurementTimelineAnomalies(docs)).toEqual([]);
  });

  it('skips documents with missing dates', () => {
    const docs: NormalizedDocument[] = [
      { execution_date: '2024-01-15' },
      { authorization_date: '2024-02-01' },
      {},
    ];
    expect(detectProcurementTimelineAnomalies(docs)).toEqual([]);
  });

  it('skips non-object entries', () => {
    expect(detectProcurementTimelineAnomalies([null as any, 'string' as any])).toEqual([]);
  });

  it('uses doc index as fallback ID', () => {
    const docs: NormalizedDocument[] = [
      {
        execution_date: '2024-01-01',
        authorization_date: '2024-06-01',
      },
    ];
    const result = detectProcurementTimelineAnomalies(docs);
    expect(result[0].details.document_id).toBe('doc[0]');
  });

  it('skips invalid date formats', () => {
    const docs: NormalizedDocument[] = [
      {
        execution_date: 'not-a-date',
        authorization_date: '2024-02-01',
      },
    ];
    expect(detectProcurementTimelineAnomalies(docs)).toEqual([]);
  });

  it('handles same day execution and authorization', () => {
    const docs: NormalizedDocument[] = [
      {
        execution_date: '2024-02-01',
        authorization_date: '2024-02-01',
      },
    ];
    expect(detectProcurementTimelineAnomalies(docs)).toEqual([]);
  });
});
