/**
 * Audit Intelligence Engine for ODIA Mobile.
 *
 * Provides a unified entry point to run multiple anomaly detectors over a
 * normalized legislative document, returning structured, explainable findings.
 *
 * Direct port of src/oraculus_di_auditor/analysis/audit_engine.py
 */

import { Anomaly, AuditResult, NormalizedDocument } from './types';
import { detectFiscalAnomalies } from './detectors/fiscal';
import { detectConstitutionalAnomalies } from './detectors/constitutional';
import { detectSurveillanceAnomalies } from './detectors/surveillance';
import { computeRecursiveScalarScore } from './scalarCore';

/**
 * Run all anomaly detectors against a normalized document.
 * Mirrors Python: analyze_document(doc)
 */
export function analyzeDocument(doc: NormalizedDocument): AuditResult {
  const anomalies: Anomaly[] = [];

  // Detectors should be side-effect-free and tolerant to missing fields.
  anomalies.push(...detectFiscalAnomalies(doc));
  anomalies.push(...detectConstitutionalAnomalies(doc));
  anomalies.push(...detectSurveillanceAnomalies(doc));

  // Compute a confidence-like score (1.0 is best) using scalar core.
  const score = computeRecursiveScalarScore(doc, anomalies);

  return {
    count: anomalies.length,
    score,
    anomalies,
  };
}
