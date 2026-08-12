/**
 * OCR module exports.
 */

export {
  recognizeText,
  isOCRAvailable,
  getCameraPermission,
  requestCameraPermission,
} from './camera';

export type {
  CaptureResult,
  OCRResult,
  OCRTextBlock,
  CameraPermissionStatus,
} from './camera';
