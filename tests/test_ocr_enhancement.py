"""Tests for OCR enhancement functionality."""

import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_ocr_config_loading():
    """Test that OCR configuration loads without errors."""
    from config.ocr_config import get_available_ocr_engines, get_config_summary

    config = get_config_summary()
    assert "min_confidence" in config
    assert "ocr_dpi" in config
    assert "available_engines" in config

    engines = get_available_ocr_engines()
    assert isinstance(engines, list)
    assert "pytesseract" in engines  # Always available


def test_preprocessor_import():
    """Test that preprocessor module imports successfully."""
    try:
        from scripts.pdf_preprocessor import (
            deskew_image,
            estimate_image_quality,
            preprocess_image_for_ocr,
        )

        # Basic smoke test
        assert callable(preprocess_image_for_ocr)
        assert callable(estimate_image_quality)
        assert callable(deskew_image)
    except ImportError as e:
        pytest.skip(f"Preprocessor dependencies not available: {e}")


def test_pdf_extractor_enhanced():
    """Test that enhanced PDF extractor works."""
    from scripts.pdf_extractor import extract_text

    # Test with non-existent file should return error result
    # Use pathlib for cross-platform compatibility
    test_path = Path("nonexistent") / "test.pdf"
    result = extract_text(test_path)

    # Should have standard result structure
    assert "path" in result
    assert "success" in result
    assert "confidence" in result
    assert "method" in result


def test_extract_text_result_structure():
    """Test that extract_text returns proper structure."""
    from scripts.pdf_extractor import extract_text

    # Use pathlib for cross-platform compatibility
    test_path = Path("nonexistent") / "test.pdf"
    result = extract_text(test_path)

    # Verify all expected keys are present
    expected_keys = ["path", "text", "success", "method", "confidence", "error"]
    for key in expected_keys:
        assert key in result, f"Missing key: {key}"

    # Verify confidence is a float
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


def test_manual_review_queue_generation():
    """Test manual review queue generator."""
    from scripts.flag_manual_review_queue import generate_manual_review_queue

    # Should work even without quality report
    queue = generate_manual_review_queue()

    assert "generated_at" in queue
    assert "threshold" in queue
    assert "low_confidence_documents" in queue
    assert isinstance(queue["low_confidence_documents"], list)


def test_preprocessor_with_mock_image():
    """Test preprocessor with a mock PIL Image."""
    try:
        import numpy as np
        from PIL import Image

        from scripts.pdf_preprocessor import (
            estimate_image_quality,
            preprocess_image_for_ocr,
        )

        # Create a simple test image
        img_array = np.ones((100, 100, 3), dtype=np.uint8) * 255
        image = Image.fromarray(img_array)

        # Test preprocessing
        preprocessed = preprocess_image_for_ocr(image)
        assert preprocessed is not None
        assert hasattr(preprocessed, "size")

        # Test quality estimation
        quality = estimate_image_quality(image)
        assert isinstance(quality, float)
        assert 0.0 <= quality <= 1.0

    except ImportError as e:
        pytest.skip(f"PIL or numpy not available: {e}")


def test_ocr_config_has_api_key():
    """Test API key checking functionality."""
    from config.ocr_config import has_api_key

    # pytesseract should always return True (local)
    assert has_api_key("pytesseract") is True

    # Commercial APIs should check env vars
    result = has_api_key("google_vision")
    assert isinstance(result, bool)


def test_extraction_confidence_range():
    """Test that confidence scores are in valid range."""
    from pathlib import Path

    from scripts.pdf_extractor import run_ocr

    # Call with non-existent file should still return valid structure
    # Use pathlib for cross-platform compatibility
    test_path = Path("nonexistent") / "test.pdf"
    text, confidence = run_ocr(test_path, enhanced=True)

    assert isinstance(text, str)
    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
