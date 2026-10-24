/**
 * Administrative Integrity Detector.
 *
 * Detects administrative record-keeping failures in legislative management
 * systems: missing final actions, blank required fields, misfiled documents,
 * and retroactive authorizations.
 * Direct port of src/oraculus_di_auditor/analysis/administrative_integrity.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Required metadata fields that must be present and non-empty */
export const REQUIRED_METADATA_FIELDS: string[] = [
  'final_action',
  'status',
  'vote_result',
  'meeting_date',
  'agenda_number',
];

/** Text signals of a completed/approved action */
export const APPROVAL_SIGNALS: string[] = [
  'approved',
  'adopted',
  'passed',
  'enacted',
  'authorized',
];

/** Misfiling indicators */
export const MISFILING_KEYWORDS: string[] = [
  'misfiled',
  'wrong agenda',
  'incorrect item',
  'clerical error',
];

/** Retroactive authorization patterns */
const RETROACTIVE_PATTERN =
  /\bretroactive\b|\bnunc\s+pro\s+tunc\b|\bratified\s+after\b|\bapproved\s+after\s+the\s+fact\b|\bback[\s-]dated\b|\beffective\s+prior\s+to\b/i;

/**
 * Return true if value is null, undefined, empty string, or whitespace-only.
 * Mirrors Python: _is_blank(value)
 */
function isBlank(value: unknown): boolean {
  if (value === null || value === undefined) {
    return true;
  }
  if (typeof value === 'string') {
    return value.trim().length === 0;
  }
  return false;
}

/**
 * Identify administrative integrity anomalies in a normalized document.
 * Mirrors Python: detect_administrative_anomalies(doc)
 */
export function detectAdministrativeAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  // Check 1: Missing final_action despite approval signals in text
  const finalAction = (doc as Record<string, unknown>).final_action;
  if (isBlank(finalAction)) {
    const textContent = extractTextContent(doc);
    const textLower = textContent ? textContent.toLowerCase() : '';
    const hasApprovalSignal = APPROVAL_SIGNALS.some((sig) =>
      textLower.includes(sig)
    );

    if (hasApprovalSignal) {
      anomalies.push({
        id: 'admin:missing-final-action',
        issue:
          'Document text indicates approval but final_action field is blank',
        severity: 'high',
        layer: 'administrative',
        details: {
          final_action_value: finalAction ?? null,
          approval_signals_found: APPROVAL_SIGNALS.filter((sig) =>
            textLower.includes(sig)
          ),
        },
      });
    }
  }

  // Check 2: Blank required metadata fields
  const blankFields = REQUIRED_METADATA_FIELDS.filter((f) =>
    isBlank((doc as Record<string, unknown>)[f])
  );
  const blankFieldsExcludingFinalAction = blankFields.filter(
    (f) => f !== 'final_action'
  );

  if (blankFieldsExcludingFinalAction.length > 0) {
    anomalies.push({
      id: 'admin:blank-required-fields',
      issue: 'Required metadata fields are blank or missing',
      severity: 'medium',
      layer: 'administrative',
      details: {
        blank_fields: blankFieldsExcludingFinalAction,
        field_count: blankFieldsExcludingFinalAction.length,
      },
    });
  }

  // Check 3: Retroactive authorization language
  const textContent = extractTextContent(doc);
  if (textContent) {
    const retroMatch = RETROACTIVE_PATTERN.exec(textContent);
    if (retroMatch) {
      anomalies.push({
        id: 'admin:retroactive-authorization',
        issue: 'Retroactive or back-dated authorization language detected',
        severity: 'high',
        layer: 'administrative',
        details: {
          matched_phrase: retroMatch[0],
          position: retroMatch.index,
        },
      });
    }

    // Check 4: Misfiling indicators
    const textLower = textContent.toLowerCase();
    const misfilingFound = MISFILING_KEYWORDS.filter((kw) =>
      textLower.includes(kw)
    );
    if (misfilingFound.length > 0) {
      anomalies.push({
        id: 'admin:potential-misfiling',
        issue: 'Misfiling or document placement error indicator found',
        severity: 'medium',
        layer: 'administrative',
        details: {
          misfiling_indicators: misfilingFound,
        },
      });
    }
  }

  return anomalies;
}
