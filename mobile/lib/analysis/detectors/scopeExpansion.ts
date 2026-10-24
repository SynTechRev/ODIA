/**
 * Scope Expansion Detector.
 *
 * Detects the "amendment-as-procurement" pattern: contract amendments or renewals
 * that expand significantly beyond the original authorization scope.
 * Direct port of src/oraculus_di_auditor/analysis/scope_expansion.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';
import { FISCAL_AMOUNT_PATTERN } from './fiscal';

/** Amendment / renewal instrument keywords */
export const AMENDMENT_KEYWORDS: string[] = [
  'amendment',
  'renewal',
  'extension',
  'modification',
  'change order',
  'supplemental',
  'addendum',
];

/** Original authorization / baseline reference keywords */
export const BASELINE_KEYWORDS: string[] = [
  'original contract',
  'base contract',
  'initial authorization',
  'approved amount',
  'not to exceed',
];

/** Sole-source procurement pattern */
const SOLE_SOURCE_PATTERN = /\bsole[\s-]source\b|\bsingle\s+source\b/i;

/** Multiplier map for M/B/T suffixes */
const SUFFIX_MULTIPLIERS: Record<string, number> = {
  m: 1_000_000,
  b: 1_000_000_000,
  t: 1_000_000_000_000,
};

/** Expansion threshold (50%) */
const EXPANSION_THRESHOLD = 0.50;

/**
 * Convert a matched dollar string to a number, handling M/B/T suffixes.
 * Mirrors Python: _parse_dollar_amount(raw)
 */
export function parseDollarAmount(raw: string): number | null {
  let s = raw.replace(/\$/g, '').replace(/,/g, '').trim();

  // Strip the "illion" tail so "Million" → "M", etc.
  if (s.toLowerCase().endsWith('illion')) {
    s = s.slice(0, -'illion'.length);
  }

  if (s.length > 0 && s[s.length - 1].toLowerCase() in SUFFIX_MULTIPLIERS) {
    const mult = SUFFIX_MULTIPLIERS[s[s.length - 1].toLowerCase()];
    const numStr = s.slice(0, -1).trim();
    const val = parseFloat(numStr);
    if (isNaN(val)) return null;
    return val * mult;
  }

  const val = parseFloat(s);
  if (isNaN(val)) return null;
  return val;
}

/**
 * Identify scope expansion anomalies in a normalized document.
 * Mirrors Python: detect_scope_expansion_anomalies(doc)
 */
export function detectScopeExpansionAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  const textContent = extractTextContent(doc);
  if (!textContent) {
    return anomalies;
  }

  const textLower = textContent.toLowerCase();

  const hasAmendment = AMENDMENT_KEYWORDS.some((kw) => textLower.includes(kw));
  if (!hasAmendment) {
    return anomalies;
  }

  const hasBaseline = BASELINE_KEYWORDS.some((kw) => textLower.includes(kw));

  // Parse all dollar amounts in the document
  // Create a new regex instance to avoid global state issues
  const amountPattern = new RegExp(FISCAL_AMOUNT_PATTERN.source, 'gi');
  const rawAmounts = textContent.match(amountPattern) || [];
  const parsed: Array<[string, number]> = [];
  for (const raw of rawAmounts) {
    const value = parseDollarAmount(raw);
    if (value !== null && value > 0) {
      parsed.push([raw, value]);
    }
  }

  // Check 1: Significant expansion — any amount >50% above another
  if (parsed.length >= 2) {
    const values = parsed.map(([, v]) => v);
    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);
    if (maxVal > minVal * (1 + EXPANSION_THRESHOLD)) {
      const expansionPct = Math.round(((maxVal - minVal) / minVal) * 1000) / 10;
      const originalRaw = parsed.find(([, v]) => v === minVal)![0];
      const expandedRaw = parsed.find(([, v]) => v === maxVal)![0];
      anomalies.push({
        id: 'scope:significant-expansion',
        issue: `Contract amount expanded by ${expansionPct}% — possible amendment-as-procurement`,
        severity: 'high',
        layer: 'scope',
        details: {
          original_amount: originalRaw,
          expanded_amount: expandedRaw,
          expansion_percentage: expansionPct,
        },
      });
    }
  }

  // Check 2: Amendment present but no original authorization reference
  if (!hasBaseline) {
    anomalies.push({
      id: 'scope:amendment-without-baseline',
      issue: 'Amendment instrument found with no original authorization reference',
      severity: 'medium',
      layer: 'scope',
      details: {
        baseline_keywords_checked: BASELINE_KEYWORDS,
      },
    });
  }

  // Check 3: Sole-source justification combined with amendment
  const soleSourceMatch = SOLE_SOURCE_PATTERN.exec(textContent);
  if (soleSourceMatch) {
    anomalies.push({
      id: 'scope:sole-source-expansion',
      issue: 'Sole-source justification combined with amendment instrument',
      severity: 'high',
      layer: 'scope',
      details: {
        sole_source_match: soleSourceMatch[0],
      },
    });
  }

  return anomalies;
}
