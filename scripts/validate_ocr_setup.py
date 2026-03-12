#!/usr/bin/env python3
"""
OCR Setup Validation Script

Validates that all OCR enhancement components are properly installed
and configured.

Author: GitHub Copilot Agent
Date: 2025-12-18
"""

import sys
from pathlib import Path

# Add paths for imports
_script_dir = Path(__file__).parent
_repo_root = _script_dir.parent
sys.path.insert(0, str(_repo_root))


def check_dependencies():
    """Check if required dependencies are installed."""
    print("=" * 80)
    print("CHECKING DEPENDENCIES")
    print("=" * 80)

    dependencies = {
        "pypdf": "PDF reading",
        "PIL": "Image processing (Pillow)",
        "numpy": "Numerical operations",
        "cv2": "OpenCV for preprocessing",
        "pdf2image": "PDF to image conversion",
        "pytesseract": "Tesseract OCR wrapper",
        "skimage": "Scientific image processing",
    }

    all_installed = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✓ {module:20s} - {description}")
        except ImportError:
            print(f"✗ {module:20s} - {description} (NOT INSTALLED)")
            all_installed = False

    return all_installed


def check_modules():
    """Check if OCR enhancement modules can be imported."""
    print("\n" + "=" * 80)
    print("CHECKING OCR ENHANCEMENT MODULES")
    print("=" * 80)

    modules = [
        ("config.ocr_config", "OCR Configuration"),
        ("scripts.pdf_preprocessor", "Image Preprocessor"),
        ("scripts.pdf_extractor", "PDF Extractor"),
        ("scripts.bulk_pdf_extract", "Bulk Extraction"),
        ("scripts.flag_manual_review_queue", "Manual Review Queue"),
    ]

    all_ok = True
    for module, description in modules:
        try:
            __import__(module)
            print(f"✓ {module:40s} - {description}")
        except Exception as e:
            print(f"✗ {module:40s} - {description}")
            print(f"  Error: {e}")
            all_ok = False

    return all_ok


def check_config():
    """Check OCR configuration."""
    print("\n" + "=" * 80)
    print("CHECKING OCR CONFIGURATION")
    print("=" * 80)

    try:
        from config.ocr_config import get_available_ocr_engines, get_config_summary

        config = get_config_summary()
        engines = get_available_ocr_engines()

        print(f"Min Confidence Threshold: {config['min_confidence']}")
        print(f"OCR DPI: {config['ocr_dpi']}")
        print(f"Threshold Characters: {config['threshold_chars']}")
        print(f"Preprocessing Enabled: {config['preprocessing_enabled']}")
        print(f"Fallback Enabled: {config['fallback_enabled']}")
        print(f"Cache Enabled: {config['cache_enabled']}")

        print("\nAvailable OCR Engines:")
        for engine in engines:
            print(f"  • {engine}")

        if not engines:
            print("  ⚠ Warning: No OCR engines available!")
            return False

        print("\nAPI Keys Configured:")
        for service, configured in config["api_keys_configured"].items():
            status = "✓" if configured else "✗"
            print(f"  {status} {service}")

        return True

    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False


def check_file_structure():
    """Check if required files exist."""
    print("\n" + "=" * 80)
    print("CHECKING FILE STRUCTURE")
    print("=" * 80)

    required_files = [
        "config/ocr_config.py",
        "scripts/pdf_preprocessor.py",
        "scripts/pdf_extractor.py",
        "scripts/bulk_pdf_extract.py",
        "scripts/flag_manual_review_queue.py",
        "scripts/update_ingestion_report.py",
        "docs/OCR_SETUP.md",
        "tests/test_ocr_enhancement.py",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = _repo_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (MISSING)")
            all_exist = False

    return all_exist


def test_extraction():
    """Test basic extraction functionality."""
    print("\n" + "=" * 80)
    print("TESTING EXTRACTION FUNCTIONALITY")
    print("=" * 80)

    try:
        from scripts.pdf_extractor import extract_text

        # Test with non-existent file (should return error structure)
        test_path = Path("nonexistent") / "test.pdf"
        result = extract_text(test_path)

        # Verify structure
        required_keys = ["path", "text", "success", "method", "confidence", "error"]
        for key in required_keys:
            if key not in result:
                print(f"✗ Missing key in result: {key}")
                return False

        # Verify confidence range
        if not (0.0 <= result["confidence"] <= 1.0):
            print(f"✗ Confidence out of range: {result['confidence']}")
            return False

        print("✓ extract_text() returns correct structure")
        print(f"  Keys: {list(result.keys())}")
        print("  Confidence range: [0.0, 1.0] ✓")

        return True

    except Exception as e:
        print(f"✗ Extraction test failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("OCR SETUP VALIDATION")
    print("=" * 80)
    print()

    checks = [
        ("Dependencies", check_dependencies),
        ("Modules", check_modules),
        ("Configuration", check_config),
        ("File Structure", check_file_structure),
        ("Extraction", test_extraction),
    ]

    results = {}
    for name, check_func in checks:
        results[name] = check_func()

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL CHECKS PASSED - OCR enhancement is ready to use")
        print("\nNext steps:")
        print("  1. Populate corpus with PDF files")
        print("  2. Run: python scripts/bulk_pdf_extract.py")
        print("  3. Run: python scripts/flag_manual_review_queue.py")
        print("  4. Check: analysis/extracted_text/extraction_quality_report.json")
    else:
        print("✗ SOME CHECKS FAILED - Please review errors above")
        print("\nCommon issues:")
        print("  • Missing dependencies: pip install -r requirements.txt")
        print("  • Tesseract not installed: sudo apt-get install tesseract-ocr")
        print("  • OpenCV issues: pip install opencv-python")
        return 1

    print("=" * 80)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
