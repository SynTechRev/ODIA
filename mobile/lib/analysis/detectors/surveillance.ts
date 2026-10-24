/**
 * Surveillance Outsourcing Detector.
 *
 * Surfaces potential outsourcing of surveillance functions to private vendors
 * and associated privacy risks.
 * Direct port of src/oraculus_di_auditor/analysis/surveillance.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Surveillance-related keywords */
export const SURVEILLANCE_KEYWORDS: string[] = [
  'surveillance',
  'monitoring',
  'tracking',
  'biometric',
  'facial recognition',
  'data collection',
  'wiretap',
  'intercept',
  'metadata',
  'geolocation',
  'cell site',
  'stingray',
];

/** Private contractor indicators */
export const CONTRACTOR_KEYWORDS: string[] = [
  'contractor',
  'vendor',
  'third party',
  'private entity',
  'service provider',
];

/** Privacy safeguard indicators */
export const SAFEGUARD_KEYWORDS: string[] = [
  'warrant',
  'probable cause',
  'court order',
  'judicial authorization',
  'minimization',
  'oversight',
  'privacy protection',
  'data retention limit',
];

/**
 * Identify surveillance outsourcing anomalies.
 * Mirrors Python: detect_surveillance_anomalies(doc)
 */
export function detectSurveillanceAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  const textContent = extractTextContent(doc);
  if (!textContent) {
    return anomalies;
  }

  const textLower = textContent.toLowerCase();

  // Check 1: Surveillance + contractor without safeguards
  const hasSurveillance = SURVEILLANCE_KEYWORDS.some((kw) => textLower.includes(kw));
  const hasContractor = CONTRACTOR_KEYWORDS.some((kw) => textLower.includes(kw));
  const hasSafeguards = SAFEGUARD_KEYWORDS.some((kw) => textLower.includes(kw));

  if (hasSurveillance && hasContractor && !hasSafeguards) {
    const surveillanceFound = SURVEILLANCE_KEYWORDS.filter((kw) =>
      textLower.includes(kw)
    );
    const contractorFound = CONTRACTOR_KEYWORDS.filter((kw) =>
      textLower.includes(kw)
    );

    anomalies.push({
      id: 'surveillance:outsourced-without-safeguards',
      issue: 'Surveillance outsourcing detected without privacy safeguards',
      severity: 'high',
      layer: 'surveillance',
      details: {
        surveillance_keywords: surveillanceFound.slice(0, 3),
        contractor_keywords: contractorFound.slice(0, 2),
      },
    });
  } else if (hasSurveillance && hasContractor && hasSafeguards) {
    anomalies.push({
      id: 'surveillance:outsourced-with-safeguards',
      issue: 'Surveillance outsourcing detected with some safeguards',
      severity: 'low',
      layer: 'surveillance',
      details: { requires_review: true },
    });
  }

  return anomalies;
}
