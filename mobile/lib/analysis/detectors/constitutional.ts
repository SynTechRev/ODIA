/**
 * Constitutional Conformity Analyzer.
 *
 * Flags patterns suggestive of unconstitutional delegation or conflicts between
 * statutes and constitutional constraints.
 * Direct port of src/oraculus_di_auditor/analysis/constitutional.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Delegation patterns indicating potentially problematic grants of authority */
export const DELEGATION_PATTERNS: RegExp[] = [
  /\b(?:Secretary|Administrator|Director|Commissioner)\s+(?:may|shall)\s+(?:determine|prescribe|establish|define)/gi,
  /\b(?:as|in)\s+(?:the\s+)?(?:Secretary|Administrator|Director|Commissioner)\s+(?:deems?|determines?)/gi,
  /\bsuch\s+(?:rules?|regulations?|standards?)\s+as\s+(?:may\s+be\s+)?(?:necessary|appropriate|desirable)/gi,
  /\bin\s+(?:his|her|their)\s+discretion/gi,
];

/** Constitutional reference patterns */
export const CONSTITUTIONAL_REFERENCE_PATTERN =
  /\b(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh|Twelfth|Thirteenth|Fourteenth|Fifteenth|Sixteenth|Seventeenth|Eighteenth|Nineteenth|Twentieth|Twenty-First|Twenty-Second|Twenty-Third|Twenty-Fourth|Twenty-Fifth|Twenty-Sixth|Twenty-Seventh)\s+Amendment/gi;

/** Keywords indicating limiting standards */
const STANDARD_KEYWORDS: string[] = [
  'standard',
  'criteria',
  'guideline',
  'requirement',
  'limitation',
  'restriction',
  'subject to',
  'consistent with',
  'in accordance with',
  'pursuant to',
];

/**
 * Check if text contains limiting standards or intelligible principles.
 * Mirrors Python: _has_limiting_standards(text)
 */
function hasLimitingStandards(text: string): boolean {
  const textLower = text.toLowerCase();
  return STANDARD_KEYWORDS.some((keyword) => textLower.includes(keyword));
}

/**
 * Identify constitutional anomalies in a normalized legislative document.
 * Mirrors Python: detect_constitutional_anomalies(doc)
 */
export function detectConstitutionalAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  const textContent = extractTextContent(doc);
  if (!textContent) {
    return anomalies;
  }

  // Check 1: Broad delegation without standards
  const delegationMatches: string[] = [];
  for (const pattern of DELEGATION_PATTERNS) {
    pattern.lastIndex = 0;
    const matches = textContent.match(pattern);
    if (matches) {
      delegationMatches.push(...matches);
    }
  }

  if (delegationMatches.length > 0) {
    const hasStandards = hasLimitingStandards(textContent);

    if (!hasStandards) {
      anomalies.push({
        id: 'constitutional:broad-delegation',
        issue: 'Broad delegation of authority without clear standards',
        severity: 'medium',
        layer: 'constitutional',
        details: {
          delegation_count: delegationMatches.length,
          sample: delegationMatches.length > 0 ? delegationMatches[0] : '',
        },
      });
    }
  }

  return anomalies;
}
