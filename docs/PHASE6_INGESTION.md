# Phase 6: Large Legal Corpus Ingestion

This document provides a comprehensive guide to the Phase 6 ingestion pipeline for large legal corpora.

## Overview

The Phase 6 pipeline ingests, normalizes, embeds, and indexes legal documents from authoritative sources including:

- U.S. Constitution
- United States Code (54 titles)
- Code of Federal Regulations (50 titles)
- California Constitution and Statutes
- Federal and state case law

## Architecture

The pipeline consists of five main components:

1. **Ingestion** (`ingest.py`) - Loads raw documents and creates normalized JSON
2. **Normalization** (`normalize.py`) - Chunks text and creates canonical format
3. **Embedding** (`embeddings.py`) - Generates TF-IDF vectors for semantic search
4. **Indexing** (`retriever.py`) - Builds vector index for similarity search
5. **Analysis** (`analyzer.py`) - Detects anomalies and quality issues

## Quick Start

### 1. Setup

Ensure dependencies are installed:

```bash
pip install -e ".[dev]"
pip install -r requirements.txt
```

### 2. Add Source Documents

Place raw legal documents in `data/sources/`:

```bash
# Example: Download from authoritative sources
# U.S. Code: https://uscode.house.gov/
# CFR: https://www.ecfr.gov/
# CA Codes: https://leginfo.legislature.ca.gov/
```

Supported formats:
- `.txt` - Plain text
- `.md` - Markdown
- `.json` - Pre-normalized JSON

### 3. Run Pipeline

```bash
# Basic ingestion
python scripts/ingest_and_index.py --source data/sources --out data/cases

# With anomaly detection
python scripts/ingest_and_index.py --source data/sources --out data/cases --analyze

# Specify jurisdiction
python scripts/ingest_and_index.py --source data/sources --jurisdiction federal --analyze
```

### 4. Review Results

Check outputs:
- Normalized documents: `data/cases/*.json`
- Vector embeddings: `data/vectors/collection_vectors.npy`
- Audit reports: `data/reports/audit_report.json`

## Data Schema

All normalized documents conform to `schemas/legal_schema.json`:

```json
{
  "id": "unique-document-id",
  "title": "Document Title",
  "jurisdiction": "federal|california|unknown",
  "source": "path/to/source.txt",
  "source_url": "https://authoritative-source.gov/...",
  "version_date": "2024-01-01",
  "ingest_timestamp": "2025-11-13T06:00:00Z",
  "checksum": "sha256-hash-of-text",
  "citations": ["42 U.S.C. § 1983"],
  "metadata": {
    "processor_version": "0.1.0",
    "transformations": ["ingest", "normalize"]
  },
  "text": "Full document text..."
}
```

## Provenance Tracking

Every document includes:

- **checksum**: SHA-256 hash for integrity verification
- **ingest_timestamp**: UTC timestamp of ingestion
- **source**: Original file path
- **metadata**: Processor version and transformation history

This ensures reproducibility and audit trails.

## Embeddings

The pipeline uses TF-IDF (Term Frequency-Inverse Document Frequency) for vector embeddings:

- **Deterministic**: Same input always produces same output
- **Reproducible**: No external API calls or randomness
- **Efficient**: Fast computation, no GPU required
- **Semantic**: Captures term importance and document similarity

### Vocabulary Management

```python
from oraculus_di_auditor.embeddings import LocalEmbedder

# Create embedder
embedder = LocalEmbedder(max_features=2048)

# Fit on corpus
embedder.fit(documents)

# Save vocabulary for consistency
embedder.save_vocabulary("data/vectors/vocab.pkl")

# Load later
embedder.load_vocabulary("data/vectors/vocab.pkl")
```

## Anomaly Detection

The analyzer detects:

1. **Long sentences** (> 1000 chars)
2. **Missing citations** (patterns in text not in citations array)
3. **Contradictory dates** (years differing by > 50 years)

Example:

```python
from oraculus_di_auditor.analyzer import find_anomalies

result = find_anomalies(document)
# {
#   "id": "doc-id",
#   "anomalies": [...],
#   "count": 2
# }
```

## Retrieval

Search for similar documents:

```python
from oraculus_di_auditor.retriever import Retriever
from oraculus_di_auditor.embeddings import LocalEmbedder

# Load index
retriever = Retriever()
retriever.load("collection")

# Load embedder
embedder = LocalEmbedder()
embedder.load_vocabulary("data/vectors/collection_vocab.pkl")

# Query
query = "civil rights violations"
query_vec = embedder.embed(query)
results = retriever.search(query_vec, top_k=5)

for idx, score, metadata in results:
    print(f"{metadata['title']}: {score:.3f}")
```

## Scaling Strategies

### Short-term (Local)

- Use TF-IDF vectors and NumPy index
- Keep raw files in `data/sources/` (gitignored)
- Commit only small normalized samples to repo

### Long-term (Production)

- **Vector storage**: FAISS, Milvus, or Weaviate
- **Raw storage**: S3 or network-attached storage
- **Parallel processing**: Message queue (Celery/RabbitMQ)
- **Monitoring**: Prometheus + structured logging

## Bulk Ingestion

For large corpora (e.g., all 54 USC titles):

1. **Download in batches**: One title at a time
2. **Validate checksums**: Ensure data integrity
3. **Incremental indexing**: Build per-title indexes
4. **Merge indexes**: Combine after validation

Example workflow:

```bash
# Ingest Title 1
python scripts/ingest_and_index.py --source data/sources/title_1

# Ingest Title 2
python scripts/ingest_and_index.py --source data/sources/title_2

# Continue for all titles...
```

## Data Sources

### U.S. Federal

- **Constitution**: Public domain
- **U.S. Code**: https://uscode.house.gov/ (bulk downloads)
- **CFR**: https://www.ecfr.gov/ (XML/JSON formats)
- **Federal Register**: https://www.federalregister.gov/

### California

- **CA Constitution**: https://leginfo.legislature.ca.gov/
- **CA Codes**: https://leginfo.legislature.ca.gov/faces/codes.xhtml

### Case Law

- **CourtListener**: https://www.courtlistener.com/ (bulk data available)
- **SCOTUS**: https://www.supremecourt.gov/
- **RECAP**: https://free.law/recap/

## Legal & Privacy

- **Public domain only**: Only ingest official public documents
- **Gitignore raw files**: Keep `data/sources/` out of repo
- **Private sources**: Use `data/sources/private/` (also gitignored)
- **No secrets**: Never commit API keys or credentials

## Testing

Run tests:

```bash
# All tests
pytest -v

# Specific modules
pytest tests/test_ingest_module.py tests/test_embeddings_module.py -v

# With coverage
pytest --cov=src/oraculus_di_auditor --cov-report=term-missing
```

## CI/CD

The CI pipeline runs:

1. Code formatting (black)
2. Linting (ruff)
3. Tests (pytest)
4. Coverage reporting

See `.github/workflows/python-ci.yml` for details.

## Troubleshooting

### "Source directory does not exist"

```bash
mkdir -p data/sources
# Add some .txt files
```

### "Embedder must be fitted"

```bash
# Ensure you fit the embedder before calling embed()
embedder.fit(corpus)
```

### "Out of memory"

- Reduce `max_features` in LocalEmbedder
- Process documents in smaller batches
- Use external storage for large files

## Next Steps

1. Download sample corpora from authoritative sources
2. Run pipeline on small samples (1-3 docs per corpus)
3. Validate outputs and reports
4. Scale up to larger batches
5. Implement production storage (S3, FAISS, etc.)

## References

- [JSON Schema](schemas/legal_schema.json)
- [Ingestion Script](scripts/ingest_and_index.py)
- [API Documentation](src/oraculus_di_auditor/)
- [Test Suite](tests/)
