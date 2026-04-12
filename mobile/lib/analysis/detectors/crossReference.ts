/**
 * Cross-Reference Auditor for Legal Documents.
 *
 * Detects cross-jurisdiction references and potential conflicts between
 * different legal corpora.
 * Direct port of src/oraculus_di_auditor/analysis/cross_reference.py
 */

import { CrossReference, CrossReferenceAnomaly, NormalizedDocument } from '../types';

/** Pattern definitions for common legal citations */
export const CITATION_PATTERNS: Record<string, RegExp> = {
  usc: /\b\d+\s+U\.?S\.?C\.?\s+§?\s*\d+/gi,
  cfr: /\b\d+\s+C\.?F\.?R\.?\s+§?\s*\d+/gi,
  cal_code: /\bCal\.?\s+\w+\.?\s+Code\b/gi,
  pub_law: /\bPub\.?\s*L\.?\s+No\.?\s+\d+-\d+/gi,
  stat: /\b\d+\s+Stat\.?\s+\d+/gi,
};

/**
 * Detect references across different legal jurisdictions.
 * Mirrors Python: detect_cross_jurisdiction_refs(text)
 */
export function detectCrossJurisdictionRefs(text: string): CrossReference[] {
  const references: CrossReference[] = [];

  // Check for each citation type
  const detectedTypes: Record<string, string[]> = {};
  for (const [citeType, pattern] of Object.entries(CITATION_PATTERNS)) {
    const regex = new RegExp(pattern.source, 'gi');
    const matches: string[] = [];
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text)) !== null) {
      matches.push(match[0]);
    }
    if (matches.length > 0) {
      detectedTypes[citeType] = matches;
    }
  }

  // Identify cross-jurisdiction patterns
  if ('usc' in detectedTypes && 'cal_code' in detectedTypes) {
    references.push({
      type: 'federal_state_cross_reference',
      federal: detectedTypes.usc,
      state: detectedTypes.cal_code,
      severity: 'info',
      description:
        'Document contains both federal (USC) and California state code references',
    });
  }

  if ('cfr' in detectedTypes && 'cal_code' in detectedTypes) {
    references.push({
      type: 'cfr_state_cross_reference',
      federal: detectedTypes.cfr,
      state: detectedTypes.cal_code,
      severity: 'info',
      description:
        'Document contains both federal regulations (CFR) and California state code references',
    });
  }

  return references;
}

/**
 * Audit documents for cross-jurisdiction references and anomalies.
 * Mirrors Python: cross_reference_audit(docs)
 */
export function crossReferenceAudit(
  docs: NormalizedDocument[]
): CrossReferenceAnomaly[] {
  const anomalies: CrossReferenceAnomaly[] = [];

  for (const doc of docs) {
    const docId = doc.id || 'unknown';
    const text = doc.text || '';
    const jurisdiction = doc.jurisdiction || 'unknown';

    // Detect cross-jurisdiction references
    const crossRefs = detectCrossJurisdictionRefs(text);

    for (const ref of crossRefs) {
      const details: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(ref)) {
        if (k !== 'type' && k !== 'severity' && k !== 'description') {
          details[k] = v;
        }
      }

      anomalies.push({
        id: docId,
        jurisdiction,
        issue: ref.type,
        severity: ref.severity,
        description: ref.description,
        details,
      });
    }

    // Additional checks for specific jurisdiction mismatches
    if (jurisdiction === 'federal') {
      const calCodePattern = new RegExp(CITATION_PATTERNS.cal_code.source, 'gi');
      const uscPattern = new RegExp(CITATION_PATTERNS.usc.source, 'gi');
      const cfrPattern = new RegExp(CITATION_PATTERNS.cfr.source, 'gi');

      const stateMatches = text.match(calCodePattern) || [];
      const federalMatches =
        (text.match(uscPattern) || []).length +
        (text.match(cfrPattern) || []).length;

      if (stateMatches.length > 0 && stateMatches.length > federalMatches) {
        anomalies.push({
          id: docId,
          jurisdiction,
          issue: 'jurisdiction_mismatch',
          severity: 'warning',
          description: `Federal document contains more state references (${stateMatches.length}) than federal references (${federalMatches})`,
        });
      }
    } else if (jurisdiction === 'california' || jurisdiction === 'state') {
      const uscPattern = new RegExp(CITATION_PATTERNS.usc.source, 'gi');
      const cfrPattern = new RegExp(CITATION_PATTERNS.cfr.source, 'gi');
      const calCodePattern = new RegExp(CITATION_PATTERNS.cal_code.source, 'gi');

      const federalMatches =
        (text.match(uscPattern) || []).length +
        (text.match(cfrPattern) || []).length;
      const stateMatches = text.match(calCodePattern) || [];

      if (federalMatches > stateMatches.length * 2) {
        anomalies.push({
          id: docId,
          jurisdiction,
          issue: 'jurisdiction_mismatch',
          severity: 'warning',
          description: `State document contains significantly more federal references (${federalMatches}) than state references (${stateMatches.length})`,
        });
      }
    }
  }

  return anomalies;
}
