#!/usr/bin/env python3
"""
PDF Preprocessor - Image enhancement for improved OCR quality.

This module provides image preprocessing functions to improve OCR accuracy
on scanned documents, including deskewing, denoising, and contrast enhancement.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import logging
from pathlib import Path

import numpy as np
from PIL import Image

LOG = logging.getLogger("oraculus.pdf_preprocessor")

# Minimum DPI for good OCR quality
MIN_OCR_DPI = 300


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Apply preprocessing pipeline to enhance image for OCR.

    Args:
        image: PIL Image object

    Returns:
        Preprocessed PIL Image ready for OCR

    Pipeline:
        1. Convert to grayscale
        2. Upscale if resolution is too low
        3. Denoise
        4. Enhance contrast
        5. Deskew (if needed)
    """
    try:
        # Import OpenCV only when needed
        import cv2

        # Convert PIL Image to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Upscale if resolution is too low
        height, width = gray.shape
        if height < 1000 or width < 1000:
            scale_factor = max(1000 / height, 1000 / width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(
                gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC
            )
            LOG.debug(
                f"Upscaled image from {width}x{height} to {new_width}x{new_height}"
            )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(
            gray, None, h=10, templateWindowSize=7, searchWindowSize=21
        )

        # Enhance contrast with adaptive histogram equalization
        # CLAHE parameters tuned for typical legislative documents
        clahe_clip_limit = 2.0  # Higher = more contrast but more noise
        clahe_tile_size = (8, 8)  # Smaller = more local adaptation
        clahe = cv2.createCLAHE(
            clipLimit=clahe_clip_limit, tileGridSize=clahe_tile_size
        )
        enhanced = clahe.apply(denoised)

        # Apply adaptive thresholding for better text extraction
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Deskew if needed
        binary = deskew_image(binary)

        # Convert back to PIL Image
        result = Image.fromarray(binary)
        return result

    except ImportError:
        LOG.warning("OpenCV not available - skipping image preprocessing")
        return image
    except Exception as e:
        LOG.error(f"Image preprocessing failed: {e}")
        return image


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct image skew.

    Args:
        image: Grayscale image as numpy array

    Returns:
        Deskewed image
    """
    try:
        import cv2

        # Detect edges
        edges = cv2.Canny(image, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return image

        # Calculate average angle
        angles = []
        for _rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90
            if -45 < angle < 45:
                angles.append(angle)

        if not angles:
            return image

        median_angle = np.median(angles)

        # Only deskew if angle is significant (> 0.5 degrees)
        if abs(median_angle) < 0.5:
            return image

        # Rotate image to correct skew
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            image,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        LOG.debug(f"Deskewed image by {median_angle:.2f} degrees")
        return rotated

    except Exception as e:
        LOG.debug(f"Deskew failed: {e}")
        return image


def estimate_image_quality(image: Image.Image) -> float:
    """
    Estimate image quality for OCR (0.0 to 1.0).

    Args:
        image: PIL Image object

    Returns:
        Quality score between 0.0 (poor) and 1.0 (excellent)

    Factors:
        - Resolution (higher is better)
        - Contrast (moderate is better)
        - Noise level (lower is better)
    """
    try:
        import cv2

        # Convert to grayscale numpy array
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Resolution score (0-1)
        # Factor 10 accounts for typical page size in square inches
        # (e.g., 8.5x11 ≈ 93.5)
        typical_page_size_factor = 10
        height, width = gray.shape
        resolution_score = min(
            1.0,
            (height * width) / (MIN_OCR_DPI * MIN_OCR_DPI * typical_page_size_factor),
        )

        # Contrast score (0-1) - using standard deviation
        contrast_score = min(1.0, gray.std() / 100.0)

        # Noise score (0-1) - using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        noise_score = min(1.0, laplacian_var / 1000.0)

        # Weighted average
        quality = (
            (resolution_score * 0.4) + (contrast_score * 0.4) + (noise_score * 0.2)
        )

        return float(quality)

    except Exception as e:
        LOG.debug(f"Quality estimation failed: {e}")
        return 0.5  # Return neutral score on error


def main():
    """Main entry point for testing."""
    import argparse

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Preprocess images for OCR")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--output", help="Output path for preprocessed image")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        return 1

    # Load image
    image = Image.open(image_path)
    print(f"Original image size: {image.size}")

    # Estimate quality
    quality = estimate_image_quality(image)
    print(f"Estimated quality: {quality:.2f}")

    # Preprocess
    preprocessed = preprocess_image_for_ocr(image)
    print(f"Preprocessed image size: {preprocessed.size}")

    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        preprocessed.save(output_path)
        print(f"Saved preprocessed image to: {output_path}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main() or 0)
