#!/usr/bin/env python3
"""
OCR Configuration Module

Provides configuration settings for OCR extraction including API keys,
thresholds, and fallback behavior.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import os

# OCR Service API Keys (optional - graceful degradation if not provided)
# Set these via environment variables for production use
ADOBE_PDF_API_KEY = os.getenv("ADOBE_PDF_API_KEY")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
AWS_TEXTRACT_ACCESS_KEY = os.getenv("AWS_TEXTRACT_ACCESS_KEY")
AWS_TEXTRACT_SECRET_KEY = os.getenv("AWS_TEXTRACT_SECRET_KEY")
AZURE_VISION_KEY = os.getenv("AZURE_VISION_KEY")
AZURE_VISION_ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")

# OCR Quality Settings
OCR_MIN_CONFIDENCE = float(
    os.getenv("OCR_MIN_CONFIDENCE", "0.75")
)  # Trigger manual review if below
OCR_DPI = int(os.getenv("OCR_DPI", "300"))  # DPI for image conversion
OCR_THRESHOLD_CHARS = int(
    os.getenv("OCR_THRESHOLD_CHARS", "40")
)  # Min chars for digital extraction

# Preprocessing Settings
ENABLE_PREPROCESSING = os.getenv("ENABLE_PREPROCESSING", "true").lower() == "true"
ENABLE_DESKEW = os.getenv("ENABLE_DESKEW", "true").lower() == "true"
ENABLE_DENOISE = os.getenv("ENABLE_DENOISE", "true").lower() == "true"
ENABLE_CONTRAST = os.getenv("ENABLE_CONTRAST", "true").lower() == "true"

# Fallback Behavior
OCR_FALLBACK_ENABLED = os.getenv("OCR_FALLBACK_ENABLED", "true").lower() == "true"
CACHE_EXTRACTIONS = os.getenv("CACHE_EXTRACTIONS", "true").lower() == "true"

# Commercial OCR API Priority Order
# APIs will be tried in this order if API keys are available
OCR_API_PRIORITY = [
    "google_vision",  # Best for scanned documents
    "aws_textract",  # Good for tables/forms
    "azure_vision",  # Good for multi-column layouts
    "adobe_pdf",  # Best for complex layouts
    "pytesseract",  # Always available fallback
]


def has_api_key(service: str) -> bool:
    """
    Check if API key is configured for a service.

    Args:
        service: Service name (google_vision, aws_textract, azure_vision, adobe_pdf)

    Returns:
        True if API key is configured, False otherwise
    """
    key_map = {
        "google_vision": GOOGLE_VISION_API_KEY,
        "aws_textract": AWS_TEXTRACT_ACCESS_KEY and AWS_TEXTRACT_SECRET_KEY,
        "azure_vision": AZURE_VISION_KEY and AZURE_VISION_ENDPOINT,
        "adobe_pdf": ADOBE_PDF_API_KEY,
        "pytesseract": True,  # Always available (local)
    }
    return bool(key_map.get(service, False))


def get_available_ocr_engines() -> list[str]:
    """
    Get list of available OCR engines based on configured API keys.

    Returns:
        List of available engine names in priority order
    """
    available = []
    for engine in OCR_API_PRIORITY:
        if has_api_key(engine):
            available.append(engine)
    return available


def get_config_summary() -> dict:
    """
    Get summary of OCR configuration for logging.

    Returns:
        Dictionary with configuration settings
    """
    return {
        "min_confidence": OCR_MIN_CONFIDENCE,
        "ocr_dpi": OCR_DPI,
        "threshold_chars": OCR_THRESHOLD_CHARS,
        "preprocessing_enabled": ENABLE_PREPROCESSING,
        "fallback_enabled": OCR_FALLBACK_ENABLED,
        "cache_enabled": CACHE_EXTRACTIONS,
        "available_engines": get_available_ocr_engines(),
        "api_keys_configured": {
            "google_vision": has_api_key("google_vision"),
            "aws_textract": has_api_key("aws_textract"),
            "azure_vision": has_api_key("azure_vision"),
            "adobe_pdf": has_api_key("adobe_pdf"),
        },
    }


if __name__ == "__main__":
    """Print configuration summary for debugging."""
    import json

    config = get_config_summary()
    print("OCR Configuration Summary:")
    print(json.dumps(config, indent=2))

    print("\nAvailable OCR engines:")
    for engine in get_available_ocr_engines():
        print(f"  - {engine}")
