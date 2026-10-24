/**
 * Camera and OCR Module.
 *
 * Handles document capture and text recognition for on-device processing.
 * Uses expo-camera for capture and provides hooks for OCR integration.
 */

/** Camera capture result */
export interface CaptureResult {
  /** URI of the captured image */
  uri: string;
  /** Image width in pixels */
  width: number;
  /** Image height in pixels */
  height: number;
  /** Base64 encoded image data (optional) */
  base64?: string;
}

/** OCR result from text recognition */
export interface OCRResult {
  /** Extracted text content */
  text: string;
  /** Confidence score (0-1) */
  confidence: number;
  /** Individual text blocks detected */
  blocks: OCRTextBlock[];
}

/** Individual text block from OCR */
export interface OCRTextBlock {
  /** Text content of the block */
  text: string;
  /** Confidence for this block */
  confidence: number;
  /** Bounding box coordinates */
  bounds: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

/**
 * Process an image for text recognition.
 *
 * This is a stub that returns the image URI for manual text input.
 * In production, integrate with ML Kit or Tesseract for on-device OCR.
 */
export async function recognizeText(imageUri: string): Promise<OCRResult> {
  // Stub implementation — in production, this would use:
  // - Google ML Kit (react-native-mlkit-ocr)
  // - Tesseract.js (for web/Node)
  // - Apple Vision framework (iOS native)
  //
  // For now, returns an empty result indicating OCR is not yet configured.
  return {
    text: '',
    confidence: 0,
    blocks: [],
  };
}

/**
 * Check if OCR capabilities are available on this device.
 */
export async function isOCRAvailable(): Promise<boolean> {
  // Stub — will return true once an OCR provider is integrated
  return false;
}

/**
 * Camera permission status */
export type CameraPermissionStatus = 'granted' | 'denied' | 'undetermined';

/**
 * Check camera permission status.
 * Wraps expo-camera permission API.
 */
export async function getCameraPermission(): Promise<CameraPermissionStatus> {
  try {
    // Dynamic import to avoid crashes in test environments
    const Camera = await import('expo-camera');
    const { status } = await Camera.Camera.getCameraPermissionsAsync();
    if (status === 'granted') return 'granted';
    if (status === 'denied') return 'denied';
    return 'undetermined';
  } catch {
    return 'undetermined';
  }
}

/**
 * Request camera permission.
 */
export async function requestCameraPermission(): Promise<CameraPermissionStatus> {
  try {
    const Camera = await import('expo-camera');
    const { status } = await Camera.Camera.requestCameraPermissionsAsync();
    if (status === 'granted') return 'granted';
    if (status === 'denied') return 'denied';
    return 'undetermined';
  } catch {
    return 'denied';
  }
}
