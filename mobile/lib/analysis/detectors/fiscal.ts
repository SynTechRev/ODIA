/**
 * Fiscal Trail Analyzer.
 *
 * Detects potential gaps or inconsistencies in appropriation and fiscal lineage.
 * Direct port of src/oraculus_di_auditor/analysis/fiscal.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Fiscal keywords indicating appropriation or budget references */
export const APPROPRIATION_KEYWORDS: string[] = [
  'appropriation',
  'appropriated',
  'budget',
  'expenditure',
  'funding',
  'allocation',
  'fiscal year',
];

/** Fiscal amount pattern (e.g., $1,000,000 or $1M) */
export const FISCAL_AMOUNT_PATTERN =
  /\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\$\s*\d+(?:\.\d+)?\s*[MBT](?:illion)?/gi;

/**
 * Identify fiscal anomalies in a normalized legislative document.
 * Mirrors Python: detect_fiscal_anomalies(doc)
 */
export function detectFiscalAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  // Check 1: Provenance integrity
  const prov = doc.provenance;
  if (!prov || typeof prov !== 'object' || !prov.hash) {
    anomalies.push({
      id: 'fiscal:missing-provenance-hash',
      issue: 'Provenance hash missing; integrity trail incomplete',
      severity: 'low',
      layer: 'fiscal',
      details: { provenance_present: Boolean(prov) },
    });
  }

  // Check 2: Appropriation trail - detect fiscal amounts without appropriation reference
  const textContent = extractTextContent(doc);
  if (textContent) {
    // Reset regex lastIndex since it has the 'g' flag
    FISCAL_AMOUNT_PATTERN.lastIndex = 0;
    const fiscalAmounts = textContent.match(FISCAL_AMOUNT_PATTERN) || [];
    const hasAppropriationRef = APPROPRIATION_KEYWORDS.some((keyword) =>
      textContent.toLowerCase().includes(keyword)
    );

    if (fiscalAmounts.length > 0 && !hasAppropriationRef) {
      anomalies.push({
        id: 'fiscal:amount-without-appropriation',
        issue: 'Fiscal amounts present without appropriation reference',
        severity: 'medium',
        layer: 'fiscal',
        details: {
          amount_count: fiscalAmounts.length,
          sample_amounts: fiscalAmounts.slice(0, 3),
        },
      });
    }
  }

  return anomalies;
}
