# OCR Extraction Setup Guide

This document describes the enhanced OCR extraction system implemented in the Oraculus-DI-Auditor.

## Overview

The system provides a multi-tier OCR extraction strategy with:
- **Native PDF text extraction** (fastest, highest quality)
- **Enhanced OCR with preprocessing** (for scanned documents)
- **Confidence scoring** (quality assessment)
- **Graceful degradation** (fallback to pytesseract if commercial APIs unavailable)

## Architecture

### Extraction Pipeline

1. **Digital Text Extraction** - Attempts to extract embedded text from PDF
2. **OCR Fallback** - If text extraction yields <40 characters, triggers OCR
3. **Image Preprocessing** - Enhances image quality before OCR
4. **Confidence Assessment** - Tracks extraction quality metrics

### Preprocessing Pipeline

For scanned documents, images are enhanced through:
1. **Grayscale conversion**
2. **Resolution upscaling** (minimum 1000px)
3. **Denoising** (fastNlMeansDenoising)
4. **Contrast enhancement** (CLAHE)
5. **Adaptive thresholding**
6. **Deskewing** (if needed)

## Installation

### Basic Setup (Pytesseract)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Tesseract OCR engine (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# Or on macOS
brew install tesseract

# Or on Windows
# Download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

### Optional: Commercial OCR APIs

For improved accuracy on complex documents, configure commercial OCR APIs:

```bash
# Set environment variables in .env file or shell
export GOOGLE_VISION_API_KEY="your-api-key"
export AWS_TEXTRACT_ACCESS_KEY="your-access-key"
export AWS_TEXTRACT_SECRET_KEY="your-secret-key"
export AZURE_VISION_KEY="your-vision-key"
export AZURE_VISION_ENDPOINT="your-endpoint-url"
```

The system will automatically use available APIs in priority order:
1. Google Cloud Vision (best for scanned documents)
2. AWS Textract (best for tables/forms)
3. Azure Computer Vision (good for multi-column layouts)
4. Pytesseract (always available fallback)

## Configuration

OCR settings can be configured via environment variables or in `config/ocr_config.py`:

```bash
# Quality threshold for manual review
export OCR_MIN_CONFIDENCE=0.75

# DPI for image conversion
export OCR_DPI=300

# Minimum characters for digital extraction
export OCR_THRESHOLD_CHARS=40

# Enable/disable preprocessing features
export ENABLE_PREPROCESSING=true
export ENABLE_DESKEW=true
export ENABLE_DENOISE=true
export ENABLE_CONTRAST=true

# Fallback and caching
export OCR_FALLBACK_ENABLED=true
export CACHE_EXTRACTIONS=true
```

## Usage

### Extract Single PDF

```bash
python scripts/pdf_extractor.py path/to/document.pdf --out-dir analysis/extracted_text
```

### Bulk Extraction

```bash
python scripts/bulk_pdf_extract.py
```

This will:
- Extract all PDFs from the corpus manifest
- Track extraction quality metrics
- Generate `extraction_quality_report.json`

### Generate Manual Review Queue

```bash
python scripts/flag_manual_review_queue.py
```

This identifies low-confidence extractions that may need manual review.

## Output Files

### Extraction Quality Report
`analysis/extracted_text/extraction_quality_report.json`

Contains:
- Total PDFs processed
- Success/failure counts
- Extraction methods used
- Average confidence score
- List of low-confidence files

Example:
```json
{
  "total_pdfs": 100,
  "successful": 95,
  "failed": 5,
  "methods": {
    "digital": 60,
    "ocr_enhanced": 35
  },
  "avg_confidence": 0.87,
  "low_confidence_files": [
    {
      "file": "path/to/document.pdf",
      "confidence": 0.65,
      "method": "ocr_enhanced"
    }
  ]
}
```

### Manual Review Queue
`oraculus/corpus/manual_review_queue.json`

Lists documents requiring manual review with:
- Corpus ID
- PDF path
- Confidence score
- Extraction method
- Identified issues
- Manual extraction flag

## Confidence Scoring

Confidence scores range from 0.0 (poor) to 1.0 (excellent):

- **1.0** - Native PDF text extraction
- **0.8-1.0** - High-quality OCR
- **0.5-0.8** - Acceptable OCR quality
- **<0.5** - Low quality, may need manual review
- **<0.75** - Flagged for quality review (default threshold)

## Troubleshooting

### "OCR dependencies missing" error

Install required packages:
```bash
pip install pytesseract pdf2image Pillow
sudo apt-get install tesseract-ocr poppler-utils
```

### Low extraction quality

1. Check image resolution: `convert document.pdf document.png && identify document.png`
2. Try adjusting preprocessing settings in `config/ocr_config.py`
3. Consider using commercial OCR APIs for complex layouts
4. Manually review low-confidence extractions

### Import errors

Ensure all paths are correct:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

## API Key Management

For production deployments:

1. **Never commit API keys to version control**
2. Use environment variables or secret management systems
3. Set up key rotation policies
4. Monitor API usage and costs
5. Implement rate limiting if needed

Example `.env` file:
```bash
# OCR API Keys (keep secure!)
GOOGLE_VISION_API_KEY=your_key_here
AWS_TEXTRACT_ACCESS_KEY=your_key_here
AWS_TEXTRACT_SECRET_KEY=your_secret_here
AZURE_VISION_KEY=your_key_here
AZURE_VISION_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
```

## Performance Optimization

### Caching

Extraction results are cached by default. To clear cache:
```bash
rm -rf analysis/extracted_text/
```

### Parallel Processing

For large document sets, consider parallel extraction:
```python
from multiprocessing import Pool
from scripts.pdf_extractor import extract_text

with Pool(processes=4) as pool:
    results = pool.map(extract_text, pdf_paths)
```

### Resource Limits

OCR is resource-intensive. Monitor:
- CPU usage (preprocessing)
- Memory usage (large images)
- API quotas (commercial services)
- Disk space (extracted text)

## Validation

Test extraction quality:

```bash
# Run OCR enhancement tests
python tests/test_ocr_enhancement.py

# Check configuration
python config/ocr_config.py

# Test preprocessor
python scripts/pdf_preprocessor.py path/to/image.png --output test_output.png
```

## Integration with Pipeline

The full pipeline includes OCR extraction:

```bash
python scripts/run_full_pipeline.py
```

This runs:
1. Corpus ingestion
2. **PDF extraction with OCR** ← Enhanced with this PR
3. Validation
4. Anomaly detection
5. Reporting

## Future Enhancements

Potential improvements:
- Layout analysis for multi-column documents
- Table extraction and structuring
- Handwriting recognition
- Language detection and multi-language support
- OCR result post-processing (spell check, format correction)

## References

- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [Google Cloud Vision API](https://cloud.google.com/vision/docs/ocr)
- [AWS Textract](https://aws.amazon.com/textract/)
- [Azure Computer Vision](https://azure.microsoft.com/en-us/services/cognitive-services/computer-vision/)
- [OpenCV Documentation](https://docs.opencv.org/)

## Support

For issues or questions:
1. Check this documentation
2. Review `analysis/logs/artifact_trace.log`
3. Check extraction quality reports
4. Open an issue on GitHub with:
   - Error messages
   - Sample PDF (if possible)
   - Configuration details
   - System information
