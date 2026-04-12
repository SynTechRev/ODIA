/**
 * Governance Gap Detector.
 *
 * Detects surveillance or monitoring capabilities deployed without
 * governance documentation.
 * Direct port of src/oraculus_di_auditor/analysis/governance_gap.py
 */

import { Anomaly, NormalizedDocument } from '../types';
import { extractTextContent } from '../textUtils';

/** Surveillance technology keywords — triggers critical severity when ungoverned */
export const SURVEILLANCE_TECH_KEYWORDS: string[] = [
  'alpr',
  'license plate reader',
  'body camera',
  'bwc',
  'facial recognition',
  'drone',
  'uas',
  'real-time',
  'geofence',
  'cell site simulator',
  'stingray',
  'predictive policing',
];

/** Data-handling capabilities — triggers high severity when ungoverned */
export const DATA_CAPABILITY_KEYWORDS: string[] = [
  'data sharing',
  'data retention',
  'cloud storage',
  'third-party access',
  'federal access',
  'interagency',
];

/** AI/automation capabilities — triggers high severity when ungoverned */
export const AI_CAPABILITY_KEYWORDS: string[] = [
  'automated',
  'ai-generated',
  'machine learning',
  'draft one',
  'report writing',
];

/** All capability keywords combined */
export const ALL_CAPABILITY_KEYWORDS: string[] = [
  ...SURVEILLANCE_TECH_KEYWORDS,
  ...DATA_CAPABILITY_KEYWORDS,
  ...AI_CAPABILITY_KEYWORDS,
];

/** Governance keywords */
export const GOVERNANCE_KEYWORDS: string[] = [
  'privacy policy',
  'use policy',
  'retention policy',
  'access control',
  'audit log',
  'oversight',
  'governance framework',
  'warrant',
  'court order',
  'probable cause',
  'privacy impact assessment',
  'civil liberties',
  'cjis',
  'public hearing',
  'council approval',
  'community input',
  'transparency report',
];

/** Retention-specific governance keywords */
export const RETENTION_GOVERNANCE_KEYWORDS: string[] = [
  'retention policy',
  'data retention policy',
  'retention schedule',
  'purge',
  'deletion policy',
];

/** Data sharing/retention capability keywords */
export const DATA_SHARING_RETENTION_KEYWORDS: string[] = [
  'data sharing',
  'data retention',
  'third-party access',
  'federal access',
  'interagency',
];

/**
 * Identify governance gap anomalies in a normalized document.
 * Mirrors Python: detect_governance_gap_anomalies(doc)
 */
export function detectGovernanceGapAnomalies(doc: NormalizedDocument): Anomaly[] {
  const anomalies: Anomaly[] = [];

  if (!doc || typeof doc !== 'object') {
    return anomalies;
  }

  const textContent = extractTextContent(doc);
  if (!textContent) {
    return anomalies;
  }

  const textLower = textContent.toLowerCase();

  // Identify which capability and governance keywords are present
  const surveillanceFound = SURVEILLANCE_TECH_KEYWORDS.filter((kw) =>
    textLower.includes(kw)
  );
  const dataFound = DATA_CAPABILITY_KEYWORDS.filter((kw) =>
    textLower.includes(kw)
  );
  const aiFound = AI_CAPABILITY_KEYWORDS.filter((kw) =>
    textLower.includes(kw)
  );
  const capabilitiesFound = [...surveillanceFound, ...dataFound, ...aiFound];

  const governanceFound = GOVERNANCE_KEYWORDS.filter((kw) =>
    textLower.includes(kw)
  );
  const governanceMissing = GOVERNANCE_KEYWORDS.filter(
    (kw) => !textLower.includes(kw)
  );

  // Check 1: Capabilities present without governance documentation
  if (capabilitiesFound.length > 0 && governanceFound.length === 0) {
    const severity = surveillanceFound.length > 0 ? 'critical' : 'high';
    anomalies.push({
      id: 'governance:capability-without-policy',
      issue:
        'Surveillance or monitoring capability deployed without governance documentation',
      severity: severity as 'critical' | 'high',
      layer: 'governance',
      details: {
        capabilities_found: capabilitiesFound,
        governance_keywords_missing: governanceMissing,
        capability_count: capabilitiesFound.length,
        governance_count: 0,
      },
    });
  }

  // Check 2: Data sharing or retention present without retention policy
  const dataSharingPresent = DATA_SHARING_RETENTION_KEYWORDS.some((kw) =>
    textLower.includes(kw)
  );
  const retentionPolicyPresent = RETENTION_GOVERNANCE_KEYWORDS.some((kw) =>
    textLower.includes(kw)
  );

  if (dataSharingPresent && !retentionPolicyPresent) {
    const dataKeywordsFound = DATA_SHARING_RETENTION_KEYWORDS.filter((kw) =>
      textLower.includes(kw)
    );
    anomalies.push({
      id: 'governance:data-retention-gap',
      issue:
        'Data sharing or retention capability found without retention policy reference',
      severity: 'high',
      layer: 'governance',
      details: {
        data_keywords_found: dataKeywordsFound,
        retention_keywords_checked: RETENTION_GOVERNANCE_KEYWORDS,
      },
    });
  }

  return anomalies;
}
