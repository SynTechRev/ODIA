# Oraculus DI Auditor Architecture

## Overview

The Oraculus DI Auditor is a foundational architecture for legal document ingestion, normalization, embedding, and anomaly auditing. It supports large-scale, chronological & cross-referenced auditing of statutes, cases, and contracts.

## Module Architecture

### Data Flow

```
Raw Documents → Ingest → Normalize → Embed → Analyze → Report
```

### Core Modules

#### 1. Ingest (`ingest.py`)
- **Purpose**: Read raw files into normalized JSON
- **Inputs**: Plain-text files, JSON documents, PDFs
- **Outputs**: Normalized JSON with standard schema
- **Features**:
  - Multi-format support (TXT, JSON, PDF)
  - Automatic file discovery
  - Batch processing

#### 2. Normalize (`normalize.py`)
- **Purpose**: Transform to canonical schema with text chunking
- **Process**:
  - Break long text into overlapping chunks (default: 512 chars, 64 overlap)
  - Generate chunk metadata (position, length)
  - Standardize document structure
- **Schema Fields**:
  - `id`: Unique document identifier
  - `title`: Document title
  - `source`: Source information
  - `date`: Document date
  - `text`: Full text content
  - `citations`: Array of referenced documents
  - `chunks`: Text chunks with metadata

#### 3. Embeddings (`embeddings.py`)
- **Purpose**: Vectorize textual chunks for retrieval
- **Modes**:
  - **Local (default)**: Hash-based deterministic embeddings
  - **Model**: Pluggable interface for transformer models (future)
- **Features**:
  - Deterministic for reproducible tests
  - No external dependencies in local mode
  - 128-dimensional vectors by default

#### 4. Retriever (`retriever.py`)
- **Purpose**: Store vectors and perform similarity search
- **Storage**: NumPy `.npy` files for vectors and metadata
- **Search**: Cosine similarity with configurable top-k
- **Features**:
  - Persistent storage
  - Metadata tracking
  - Fast similarity search

#### 5. Analyzer (`analyzer.py`)
- **Purpose**: Rule-based + ML detectors to find anomalies/inconsistencies
- **Detectors**:
  - **Long Sentence**: Sentences exceeding 1000 characters
  - **Cross-Reference Mismatch**: Citations in text not in citation array
  - **Contradictory Dates**: Dates mentioned that don't match document date
- **Output**: Structured findings with severity levels

#### 6. Reporter (`reporter.py`)
- **Purpose**: Human-readable audit artifacts
- **Formats**:
  - **JSON**: Machine-readable with full provenance
  - **CSV**: Spreadsheet-compatible summary
- **Features**:
  - Timestamped reports
  - Provenance metadata
  - Flattened CSV for analysis

## Configuration

The `config.py` module defines standard paths:
- `REPO_ROOT`: Repository root directory
- `DATA_DIR`: Data storage directory
- `CASES_DIR`: Normalized case documents
- `STATUTES_DIR`: Statute documents
- `SOURCES_DIR`: Raw source files (gitignored)
- `VECTORS_DIR`: Embedding vectors

## Command Line Interface

The `cli.py` module provides command-line access:

```bash
python -m oraculus_di_auditor.cli ingest --source data/sources
```

## Extension Points

### Future Enhancements
1. **Semantic Analysis**: Integrate transformer models for deep semantic understanding
2. **Database Backend**: Replace file storage with PostgreSQL for scale
3. **Visualization**: Graph visualization of document relationships
4. **ML Anomaly Detection**: Train custom models on audit data
5. **Multi-language Support**: Extend to non-English documents

## Security Model

- **No External API Calls**: All processing is local
- **Data Privacy**: Source files never leave local environment
- **Gitignore Protection**: Sensitive data directories are excluded
- **Hash Verification**: SHA-256 hashing for data integrity

## Testing Strategy

- **Unit Tests**: Each module has comprehensive unit tests
- **Integration Tests**: End-to-end pipeline testing
- **Fixtures**: Sample data for reproducible testing
- **Coverage Target**: ≥ 90%

## Performance Considerations

- **Batch Processing**: Process multiple documents efficiently
- **Chunking**: Configurable chunk size for memory management
- **Vector Storage**: NumPy for fast numerical operations
- **Lazy Loading**: Load data only when needed
