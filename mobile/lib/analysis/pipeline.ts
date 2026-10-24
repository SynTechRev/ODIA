/**
 * Unified Analysis Pipeline for ODIA Mobile.
 *
 * Central entry point for running a complete analysis on a document.
 * Direct port of src/oraculus_di_auditor/analysis/pipeline.py
 */

import { Anomaly, AnalysisResult, NormalizedDocument } from './types';
import { detectFiscalAnomalies } from './detectors/fiscal';
import { detectConstitutionalAnomalies } from './detectors/constitutional';
import { detectSurveillanceAnomalies } from './detectors/surveillance';
import { computeRecursiveScalarScore } from './scalarCore';

/** Severity weights for pipeline scoring (different from scalar_core weights) */
const PIPELINE_SEVERITY_WEIGHTS: Record<string, number> = {
  low: 0.1,
  medium: 0.3,
  high: 0.6,
};

/**
 * Execute complete anomaly detection analysis on document text.
 * Mirrors Python: run_full_analysis(document_text, metadata, *, jurisdiction_config)
 */
export function runFullAnalysis(
  documentText: string,
  metadata: Record<string, unknown>,
  options?: { jurisdictionName?: string; agencies?: Record<string, string[]> }
): AnalysisResult {
  // Preprocess: normalize metadata and create document structure
  const agencies = options?.agencies || {};
  const normalizedDoc = preprocessDocument(documentText, metadata, agencies);

  // Run all detectors
  const fiscalFindings = detectFiscalAnomalies(normalizedDoc);
  const constitutionalFindings = detectConstitutionalAnomalies(normalizedDoc);
  const surveillanceFindings = detectSurveillanceAnomalies(normalizedDoc);

  // Combine all findings
  const allAnomalies = [
    ...fiscalFindings,
    ...constitutionalFindings,
    ...surveillanceFindings,
  ];

  // Compute recursive scalar score (confidence-like, 1.0 = best)
  const latticeScore = computeRecursiveScalarScore(normalizedDoc, allAnomalies);

  // Compute additional metrics
  const severityScore = computeSeverityScore(allAnomalies);
  const coherenceBonus = computePipelineCoherenceBonus(normalizedDoc);
  const flags = extractHighPriorityFlags(allAnomalies);
  const summary = generateSummary(allAnomalies, severityScore, latticeScore);

  // Build structured response
  const result: AnalysisResult = {
    metadata: (normalizedDoc.metadata as Record<string, unknown>) || metadata,
    findings: {
      fiscal: fiscalFindings,
      constitutional: constitutionalFindings,
      surveillance: surveillanceFindings,
    },
    severity_score: severityScore,
    lattice_score: latticeScore,
    coherence_bonus: coherenceBonus,
    flags,
    summary,
    timestamp: new Date().toISOString(),
  };

  if (options?.jurisdictionName) {
    result.jurisdiction = options.jurisdictionName;
  }

  return result;
}

/**
 * Convert raw text and metadata into normalized document structure.
 * Mirrors Python: _preprocess_document(document_text, metadata, *, agencies)
 */
function preprocessDocument(
  documentText: string,
  metadata: Record<string, unknown>,
  agencies: Record<string, string[]>
): NormalizedDocument {
  const documentId =
    (metadata.document_id as string) ||
    `doc-${Math.abs(hashCode(documentText)) % 10 ** 8}`;

  const normalizedDoc: NormalizedDocument = {
    document_id: documentId,
    title: (metadata.title as string) || 'Untitled Document',
    document_type: (metadata.document_type as string) || 'document',
    raw_text: documentText,
    sections: [
      {
        section_id: 'main',
        content: documentText,
      },
    ],
    metadata: { ...metadata, document_id: documentId },
  };

  if (Object.keys(agencies).length > 0) {
    normalizedDoc.agencies = agencies;
  }

  // Add provenance if hash is provided in metadata
  if ('hash' in metadata) {
    normalizedDoc.provenance = {
      source: (metadata.source as string) || 'pipeline',
      hash: metadata.hash as string,
      verified_on: new Date().toISOString(),
    };
  }

  return normalizedDoc;
}

/** Simple hash code for strings (matching Python's hash() behavior for ID generation) */
function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}

/**
 * Compute aggregate severity score from anomalies.
 * Mirrors Python: _compute_severity_score(anomalies)
 */
function computeSeverityScore(anomalies: Anomaly[]): number {
  if (anomalies.length === 0) {
    return 0.0;
  }

  const totalWeight = anomalies.reduce((sum, a) => {
    const severity = a.severity || 'medium';
    return sum + (PIPELINE_SEVERITY_WEIGHTS[severity] ?? 0.3);
  }, 0);

  // Normalize to 0-1 range, with diminishing returns
  return Math.min(1.0, totalWeight / (anomalies.length + 5));
}

/**
 * Compute pattern coherence bonus for documents with strong provenance.
 * Mirrors Python: _compute_coherence_bonus(doc) in pipeline.py
 */
function computePipelineCoherenceBonus(doc: NormalizedDocument): number {
  let bonus = 0.0;

  const prov = doc.provenance;
  if (prov) {
    if (prov.hash) bonus += 0.05;
    if (prov.verified_on) bonus += 0.05;
    if (prov.source) bonus += 0.05;
  }

  if (doc.document_type && doc.title) {
    bonus += 0.05;
  }

  return Math.min(0.2, bonus);
}

/**
 * Extract high-priority flags from anomalies.
 * Mirrors Python: _extract_high_priority_flags(anomalies)
 */
function extractHighPriorityFlags(anomalies: Anomaly[]): string[] {
  const flags: string[] = [];

  for (const anomaly of anomalies) {
    if (anomaly.severity === 'high') {
      const flagId = anomaly.id || 'unknown';
      const issue = anomaly.issue || 'High-severity anomaly detected';
      flags.push(`${flagId}: ${issue}`);
    }
  }

  return flags;
}

/**
 * Generate human-readable summary of analysis results.
 * Mirrors Python: _generate_summary(anomalies, severity_score, lattice_score)
 */
function generateSummary(
  anomalies: Anomaly[],
  severityScore: number,
  latticeScore: number
): string {
  const anomalyCount = anomalies.length;

  if (anomalyCount === 0) {
    return (
      `Analysis complete. No anomalies detected. ` +
      `Confidence score: ${latticeScore.toFixed(2)}`
    );
  }

  // Categorize by severity
  const bySeverity: Record<string, number> = { low: 0, medium: 0, high: 0 };
  for (const a of anomalies) {
    const severity = a.severity || 'medium';
    bySeverity[severity] = (bySeverity[severity] || 0) + 1;
  }

  const severityParts: string[] = [];
  if (bySeverity.high > 0) severityParts.push(`${bySeverity.high} high`);
  if (bySeverity.medium > 0) severityParts.push(`${bySeverity.medium} medium`);
  if (bySeverity.low > 0) severityParts.push(`${bySeverity.low} low`);

  const severityStr = severityParts.join(', ');
  const anomalyWord = anomalyCount === 1 ? 'y' : 'ies';

  return (
    `Analysis detected ${anomalyCount} anomal${anomalyWord} ` +
    `(${severityStr} severity). ` +
    `Overall severity: ${severityScore.toFixed(2)}, ` +
    `confidence: ${latticeScore.toFixed(2)}`
  );
}
