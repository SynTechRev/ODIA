/**
 * Recursive Scalar Core (Pattern Lattice and Confidence Scoring).
 *
 * Direct port of src/oraculus_di_auditor/analysis/scalar_core.py
 */

import { Anomaly, NormalizedDocument } from './types';

/** Severity weights for anomaly scoring */
export const SEVERITY_WEIGHTS: Record<string, number> = {
  low: 0.02,
  medium: 0.05,
  high: 0.10,
};

/**
 * Compute a confidence-like score using recursive scalar model.
 * Returns a score in [0.0, 1.0], with 1.0 meaning fully consistent.
 * Mirrors Python: compute_recursive_scalar_score(doc, anomalies)
 */
export function computeRecursiveScalarScore(
  doc: NormalizedDocument,
  anomalies: Anomaly[]
): number {
  if (!anomalies || anomalies.length === 0) {
    return 1.0;
  }

  // Weighted scoring based on severity
  let totalPenalty = 0.0;
  for (const anomaly of anomalies) {
    const severity = anomaly.severity || 'medium';
    const weight = SEVERITY_WEIGHTS[severity] ?? 0.05;
    totalPenalty += weight;
  }

  // Apply pattern lattice coherence boost for documents with good provenance
  const coherenceBonus = computeCoherenceBonus(doc);
  const adjustedPenalty = Math.max(0.0, totalPenalty - coherenceBonus);

  // Clamp score to [0, 1]
  return Math.max(0.0, Math.min(1.0, 1.0 - adjustedPenalty));
}

/**
 * Compute coherence bonus based on document structural integrity.
 * Mirrors Python: _compute_coherence_bonus(doc)
 */
function computeCoherenceBonus(doc: NormalizedDocument): number {
  let bonus = 0.0;

  // Bonus for valid provenance
  const prov = doc.provenance;
  if (prov && typeof prov === 'object' && prov.hash) {
    bonus += 0.01;
  }

  // Bonus for having references (indicates lattice connectivity)
  const refs = doc.references;
  if (Array.isArray(refs) && refs.length > 0) {
    bonus += 0.005;
  }

  // Bonus for metadata completeness
  const metadata = doc.metadata;
  if (metadata && typeof metadata === 'object' && Object.keys(metadata).length > 0) {
    bonus += 0.005;
  }

  return bonus;
}
