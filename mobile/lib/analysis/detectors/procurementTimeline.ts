/**
 * Procurement Timeline Detector.
 *
 * Detects contract execution dates that precede council authorization dates.
 * Direct port of src/oraculus_di_auditor/analysis/procurement_timeline.py
 */

import { Anomaly, NormalizedDocument } from '../types';

/**
 * Parse an ISO-format date string (YYYY-MM-DD) into a Date object.
 * Returns null on any parse failure.
 * Mirrors Python: _parse_date(value)
 */
function parseDate(value: unknown): Date | null {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  // Validate ISO date format YYYY-MM-DD
  if (!/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
    return null;
  }
  const date = new Date(trimmed + 'T00:00:00Z');
  if (isNaN(date.getTime())) {
    return null;
  }
  return date;
}

/**
 * Identify contracts executed before council authorization.
 * Mirrors Python: detect_procurement_timeline_anomalies(documents)
 *
 * Note: This detector takes a LIST of documents, unlike most others.
 */
export function detectProcurementTimelineAnomalies(
  documents: NormalizedDocument[]
): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!Array.isArray(documents)) {
    return anomalies;
  }

  for (let idx = 0; idx < documents.length; idx++) {
    const doc = documents[idx];
    if (!doc || typeof doc !== 'object') {
      continue;
    }

    const docId =
      (doc as Record<string, unknown>).document_id ||
      doc.id ||
      `doc[${idx}]`;
    const title = doc.title || '';

    const execRaw = doc.execution_date;
    const authRaw = doc.authorization_date;

    const execDate = parseDate(execRaw);
    const authDate = parseDate(authRaw);

    // Skip documents with missing or unparseable dates
    if (execDate === null || authDate === null) {
      continue;
    }

    if (execDate < authDate) {
      const deltaDays = Math.round(
        (authDate.getTime() - execDate.getTime()) / (1000 * 60 * 60 * 24)
      );
      anomalies.push({
        id: 'procurement:execution-precedes-authorization',
        issue: `Contract executed ${deltaDays} day(s) before council authorization`,
        severity: 'high',
        layer: 'procurement',
        details: {
          document_id: docId,
          title: title,
          execution_date: execRaw,
          authorization_date: authRaw,
          days_early: deltaDays,
        },
      });
    }
  }

  return anomalies;
}
