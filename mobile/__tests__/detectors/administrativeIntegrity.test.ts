import { detectAdministrativeAnomalies } from '../../lib/analysis/detectors/administrativeIntegrity';
import { NormalizedDocument } from '../../lib/analysis/types';

describe('detectAdministrativeAnomalies', () => {
  it('returns empty for non-object input', () => {
    expect(detectAdministrativeAnomalies(null as any)).toEqual([]);
  });

  it('detects missing final_action with approval signal', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The motion was approved by a unanimous vote.',
      final_action: null,
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'admin:missing-final-action',
          severity: 'high',
          layer: 'administrative',
        }),
      ])
    );
  });

  it('does not flag final_action when present', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The motion was approved.',
      final_action: 'Approved',
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result.find((a) => a.id === 'admin:missing-final-action')).toBeUndefined();
  });

  it('detects blank required fields', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Some text',
      final_action: 'Done',
      status: '',
      vote_result: null,
      meeting_date: '2024-01-15',
      agenda_number: '5',
    };
    const result = detectAdministrativeAnomalies(doc);
    const anomaly = result.find((a) => a.id === 'admin:blank-required-fields');
    expect(anomaly).toBeDefined();
    expect(anomaly!.details.blank_fields).toEqual(expect.arrayContaining(['status', 'vote_result']));
  });

  it('detects retroactive authorization', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The contract was ratified after the execution date.',
      final_action: 'Done',
      status: 'Complete',
      vote_result: 'Yes',
      meeting_date: '2024-01-01',
      agenda_number: '1',
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'admin:retroactive-authorization',
          severity: 'high',
        }),
      ])
    );
  });

  it('detects nunc pro tunc language', () => {
    const doc: NormalizedDocument = {
      raw_text: 'The order is entered nunc pro tunc to the original filing date.',
      final_action: 'Entered',
      status: 'Active',
      vote_result: 'Yes',
      meeting_date: '2024-01-01',
      agenda_number: '1',
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result.find((a) => a.id === 'admin:retroactive-authorization')).toBeDefined();
  });

  it('detects misfiling indicators', () => {
    const doc: NormalizedDocument = {
      raw_text: 'This item was misfiled under the wrong agenda category.',
      final_action: 'Filed',
      status: 'Active',
      vote_result: 'NA',
      meeting_date: '2024-01-01',
      agenda_number: '1',
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: 'admin:potential-misfiling',
          severity: 'medium',
        }),
      ])
    );
  });

  it('treats whitespace-only as blank', () => {
    const doc: NormalizedDocument = {
      raw_text: 'Meeting notes with approved actions.',
      final_action: '   ',
    };
    const result = detectAdministrativeAnomalies(doc);
    expect(result.find((a) => a.id === 'admin:missing-final-action')).toBeDefined();
  });
});
