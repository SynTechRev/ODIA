/**
 * ODIA Analysis Engine - TypeScript Port
 * 
 * Complete port of src/oraculus_di_auditor/analysis/
 * All detectors produce identical results to the Python implementations.
 */

export * from './types';
export { extractTextContent } from './textUtils';
export { detectFiscalAnomalies } from './detectors/fiscal';
export { detectConstitutionalAnomalies } from './detectors/constitutional';
export { detectSurveillanceAnomalies } from './detectors/surveillance';
export { detectProcurementTimelineAnomalies } from './detectors/procurementTimeline';
export { detectGovernanceGapAnomalies } from './detectors/governanceGap';
export { detectSignatureAnomalies } from './detectors/signatureChain';
export { detectAdministrativeAnomalies } from './detectors/administrativeIntegrity';
export { detectScopeExpansionAnomalies } from './detectors/scopeExpansion';
export { detectCrossJurisdictionRefs, crossReferenceAudit } from './detectors/crossReference';
export { computeRecursiveScalarScore } from './scalarCore';
export { analyzeDocument } from './auditEngine';
export { runFullAnalysis } from './pipeline';
