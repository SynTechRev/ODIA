/**
 * Signature Chain Detector.
 *
 * Detects unsigned, partially signed, or placeholder-signed documents.
 * Direct port of src/oraculus_di_auditor/analysis/signature_chain.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Patterns indicating a blank or missing signature block */
export const SIGNATURE_GAP_PATTERNS: string[] = [
  '\\bsignature\\s+block\\s+blank\\b',
  '\\bunsigned\\b',
  '\\bnot\\b.{0,20}\\bexecuted\\b',
  '\\bplaceholder\\b',
  '_{5,}',
  '\\bDocuSign\\b.{0,80}\\bpending\\b',
  '\\bone\\s+party\\s+signed\\b',
  '\\bagency\\s+signature\\s+missing\\b',
  '\\bvendor\\s+signature\\s+only\\b',
  '\\bcity\\s+signature\\s+blank\\b',
];

/** Literal placeholder tokens used by contract-assembly tools */
export const PLACEHOLDER_PATTERN = /\\s1\\|\\d1\\|\[SIGNATURE\]/i;

/** Contract instrument keywords */
export const CONTRACT_INSTRUMENT_PATTERN =
  /\b(?:MSPA|MSA|PSA|SOW|MOU|agreement|contract|amendment|order\s+form)\b/i;

/** Fiscal amount pattern (reused from fiscal layer) */
const FISCAL_AMOUNT_PATTERN =
  /\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s*\d+(?:\.\d+)?\s*[MBT](?:illion)?/gi;

/** Compiled signature gap patterns */
const COMPILED_GAP_PATTERNS: RegExp[] = SIGNATURE_GAP_PATTERNS.map(
  (p) => new RegExp(p, 'i')
);

/**
 * Return each gap-pattern string that matched in text.
 * Mirrors Python: _detect_signature_gaps(text)
 */
function detectSignatureGaps(text: string): string[] {
  const matched: string[] = [];
  for (const pattern of COMPILED_GAP_PATTERNS) {
    if (pattern.test(text)) {
      matched.push(pattern.source);
    }
  }
  return matched;
}

/**
 * Return the contract instrument keyword closest to gapPosition in text.
 * Mirrors Python: _nearest_instrument(text, gap_match)
 */
function nearestInstrument(text: string, gapPosition: number): string | null {
  let bestWord: string | null = null;
  let bestDist = Infinity;

  const globalPattern = new RegExp(CONTRACT_INSTRUMENT_PATTERN.source, 'gi');
  let match: RegExpExecArray | null;
  while ((match = globalPattern.exec(text)) !== null) {
    const dist = Math.abs(match.index - gapPosition);
    if (dist < bestDist) {
      bestDist = dist;
      bestWord = match[0].toUpperCase();
    }
  }

  return bestWord;
}

/**
 * Identify signature chain anomalies in a normalized document.
 * Mirrors Python: detect_signature_anomalies(doc)
 */
export function detectSignatureAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  const textContent = extractTextContent(doc);
  if (!textContent) {
    return anomalies;
  }

  const hasInstrument = CONTRACT_INSTRUMENT_PATTERN.test(textContent);
  FISCAL_AMOUNT_PATTERN.lastIndex = 0;
  const dollarAmounts = textContent.match(FISCAL_AMOUNT_PATTERN) || [];

  // Check 1: Signature gap patterns near a contract instrument keyword
  if (hasInstrument) {
    const gapMatches: Array<{ index: number; pattern: string }> = [];
    const gapTypes: string[] = [];

    for (const pattern of COMPILED_GAP_PATTERNS) {
      const m = pattern.exec(textContent);
      if (m) {
        gapMatches.push({ index: m.index, pattern: pattern.source });
        gapTypes.push(pattern.source);
      }
      // Reset for stateless patterns
      pattern.lastIndex = 0;
    }

    if (gapMatches.length > 0) {
      const instrumentType =
        nearestInstrument(textContent, gapMatches[0].index) || 'UNKNOWN';
      const severity = dollarAmounts.length > 0 ? 'critical' : 'high';
      anomalies.push({
        id: 'signature:unsigned-instrument',
        issue: `Signature gap detected in ${instrumentType} instrument`,
        severity: severity as 'critical' | 'high',
        layer: 'signature',
        details: {
          instrument_type: instrumentType,
          signature_gap_type: gapTypes[0],
          gap_pattern_count: gapMatches.length,
          dollar_amount: dollarAmounts.length > 0 ? dollarAmounts[0] : null,
        },
      });
    }
  }

  // Check 2: Placeholder tokens anywhere in the document
  const placeholderMatch = PLACEHOLDER_PATTERN.exec(textContent);
  if (placeholderMatch) {
    anomalies.push({
      id: 'signature:placeholder-tokens',
      issue: 'Unresolved signature placeholder token found in document',
      severity: 'high',
      layer: 'signature',
      details: {
        token: placeholderMatch[0],
        position: placeholderMatch.index,
      },
    });
  }

  return anomalies;
}
