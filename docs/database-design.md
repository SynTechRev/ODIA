# Database-Backed Metadata Storage Design

## Overview

This document describes the design for persistent metadata storage to support the Oraculus-DI-Auditor system. The database will store document metadata, provenance records, anomaly detections, and reference graphs for efficient querying and auditing.

## Goals

1. **Persistent Storage**: Replace in-memory storage with durable database backend
2. **Query Performance**: Enable fast lookups by document ID, jurisdiction, date range
3. **Audit Trail**: Maintain complete history of all analyses and detections
4. **Scalability**: Support corpus of 50,000+ documents (USC, CFR, state codes)
5. **Provenance**: Track full lineage from source files to analysis results

## Database Options

### Option 1: SQLite (Recommended for v1.0)
**Pros**:
- Zero configuration, file-based
- Built into Python standard library
- Sufficient for single-node deployments
- Easy backup (copy .db file)

**Cons**:
- Limited concurrency
- Not suitable for distributed systems

### Option 2: PostgreSQL (Recommended for Production)
**Pros**:
- Full ACID compliance
- Advanced indexing (GiST, GIN)
- JSON/JSONB support for flexible schema
- Excellent concurrent read/write performance
- Replication and high availability

**Cons**:
- Requires separate server installation
- More complex setup and maintenance

### Option 3: Hybrid Approach
- SQLite for development and small deployments
- PostgreSQL for production and large-scale deployments
- Abstract database layer (SQLAlchemy) for compatibility

## Schema Design

### Core Tables

#### 1. `documents`
Stores normalized document metadata.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    jurisdiction VARCHAR(100),
    authority VARCHAR(255),
    version_date DATE,
    signatory VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata_json TEXT  -- JSON blob for extensibility
);

CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_jurisdiction ON documents(jurisdiction);
CREATE INDEX idx_documents_version_date ON documents(version_date);
```

#### 2. `provenance`
Tracks document provenance and integrity.

```sql
CREATE TABLE provenance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR(255) NOT NULL,
    source_path TEXT NOT NULL,
    hash VARCHAR(64) NOT NULL,  -- SHA-256
    verified_on TIMESTAMP NOT NULL,
    file_size_bytes INTEGER,
    format VARCHAR(20),  -- json, txt, pdf, xml
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_provenance_doc_id ON provenance(document_id);
CREATE INDEX idx_provenance_hash ON provenance(hash);
```

#### 3. `sections`
Stores document sections for full-text search.

```sql
CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR(255) NOT NULL,
    section_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    order_index INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_sections_doc_id ON sections(document_id);
CREATE UNIQUE INDEX idx_sections_composite ON sections(document_id, section_id);
CREATE VIRTUAL TABLE sections_fts USING fts5(document_id, section_id, content);
```

#### 4. `references`
Tracks citations and cross-references.

```sql
CREATE TABLE references (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_document_id VARCHAR(255) NOT NULL,
    target_document_id VARCHAR(255),  -- NULL if external reference
    reference_text TEXT NOT NULL,
    reference_type VARCHAR(50),  -- usc, cfr, case, statute, etc.
    FOREIGN KEY (source_document_id) REFERENCES documents(document_id),
    FOREIGN KEY (target_document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_references_source ON references(source_document_id);
CREATE INDEX idx_references_target ON references(target_document_id);
CREATE INDEX idx_references_type ON references(reference_type);
```

#### 5. `analyses`
Stores analysis results from audit engine.

```sql
CREATE TABLE analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR(255) NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anomaly_count INTEGER NOT NULL,
    scalar_score REAL NOT NULL,  -- 0.0 to 1.0
    engine_version VARCHAR(20),
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_analyses_doc_id ON analyses(document_id);
CREATE INDEX idx_analyses_timestamp ON analyses(analysis_timestamp);
CREATE INDEX idx_analyses_score ON analyses(scalar_score);
```

#### 6. `anomalies`
Stores detected anomalies with full details.

```sql
CREATE TABLE anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    anomaly_id VARCHAR(255) NOT NULL,  -- e.g., fiscal:missing-provenance-hash
    issue TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- low, medium, high
    layer VARCHAR(50) NOT NULL,  -- fiscal, constitutional, surveillance, etc.
    details_json TEXT,  -- JSON blob with structured details
    FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);

CREATE INDEX idx_anomalies_analysis ON anomalies(analysis_id);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);
CREATE INDEX idx_anomalies_layer ON anomalies(layer);
```

#### 7. `embeddings`
Stores vector embeddings for semantic search.

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR(255) NOT NULL,
    embedding_vector BLOB NOT NULL,  -- Serialized numpy array
    model_name VARCHAR(100) NOT NULL,  -- e.g., tfidf-local
    dimension INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX idx_embeddings_doc_id ON embeddings(document_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name);
```

## Implementation Plan

### Phase 1: Database Abstraction Layer
Create a database interface using SQLAlchemy ORM:

```python
# src/oraculus_di_auditor/storage/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def store_document(self, doc: dict) -> int:
        """Store normalized document and return DB ID."""
        pass

    def get_document(self, document_id: str) -> dict:
        """Retrieve document by ID."""
        pass

    def store_analysis(self, document_id: str, result: dict) -> int:
        """Store analysis result."""
        pass

    def query_anomalies(
        self, severity: str = None, layer: str = None
    ) -> list[dict]:
        """Query anomalies by filters."""
        pass
```

### Phase 2: Migration from In-Memory to Database
Replace in-memory storage in:
- `provenance_tracker.py` → Use `provenance` and `references` tables
- `retriever.py` → Use `embeddings` table with optional vector database
- `reporter.py` → Query from `analyses` and `anomalies` tables

### Phase 3: Query API
Add query endpoints to REST API:

```python
@app.get("/api/v1/documents/{document_id}")
async def get_document(document_id: str):
    """Retrieve document by ID."""
    pass

@app.get("/api/v1/anomalies")
async def query_anomalies(
    severity: str = None,
    layer: str = None,
    limit: int = 100
):
    """Query anomalies with filters."""
    pass

@app.get("/api/v1/documents/{document_id}/references")
async def get_references(document_id: str):
    """Get all references for a document."""
    pass
```

## Vector Database Integration (Optional)

For large-scale semantic search, consider specialized vector databases:

### Option 1: FAISS (Facebook AI Similarity Search)
- High-performance in-memory vector search
- Good for read-heavy workloads
- Requires periodic index rebuilds

### Option 2: Qdrant
- Purpose-built vector database
- REST API and Python client
- Persistent storage with fast search

### Option 3: Chroma
- Lightweight, embedded vector DB
- Easy integration with Python
- Good for development and small deployments

## Migration Strategy

### Step 1: Create Schema
```bash
python scripts/create_schema.py --db-url sqlite:///data/oraculus.db
```

### Step 2: Import Existing Data
```bash
python scripts/import_legacy_data.py \
  --source data/cases \
  --db-url sqlite:///data/oraculus.db
```

### Step 3: Update Configuration
```python
# config.py
DATABASE_URL = os.getenv(
    "ORACULUS_DB_URL",
    "sqlite:///data/oraculus.db"
)
```

### Step 4: Gradual Rollout
1. Add database writes alongside existing in-memory storage
2. Validate consistency
3. Switch reads to database
4. Remove in-memory storage code

## Performance Considerations

### Indexing Strategy
- Index foreign keys for join performance
- Index commonly queried fields (document_type, jurisdiction, severity)
- Full-text search index for sections (FTS5 in SQLite, GIN in PostgreSQL)

### Batch Operations
- Use bulk inserts for initial data load
- Commit in batches of 1000 documents

### Caching
- Cache frequently accessed documents in Redis
- Cache analysis results for 1 hour
- Invalidate cache on document updates

### Partitioning (PostgreSQL Only)
- Partition `analyses` by month
- Partition `anomalies` by severity and date

## Backup and Recovery

### SQLite
```bash
# Backup
sqlite3 data/oraculus.db ".backup data/oraculus_backup.db"

# Restore
cp data/oraculus_backup.db data/oraculus.db
```

### PostgreSQL
```bash
# Backup
pg_dump oraculus > oraculus_backup.sql

# Restore
psql oraculus < oraculus_backup.sql
```

## Security Considerations

1. **Connection Security**: Use SSL/TLS for PostgreSQL connections
2. **Access Control**: Implement role-based access control (RBAC)
3. **Encryption at Rest**: Encrypt database files (LUKS, BitLocker, or database-level)
4. **Audit Logging**: Enable database audit logs for compliance
5. **Input Validation**: Sanitize all inputs to prevent SQL injection (use parameterized queries)

## Testing Strategy

### Unit Tests
- Test database operations (CRUD)
- Test query filters and joins
- Test transaction rollback

### Integration Tests
- Test full pipeline: ingest → analyze → store → query
- Test concurrent access (write conflicts)
- Test backup/restore procedures

### Performance Tests
- Benchmark query performance with 10K, 50K, 100K documents
- Profile slow queries with EXPLAIN
- Test embedding search latency

## Future Enhancements

1. **GraphQL API**: Alternative to REST for flexible queries
2. **Time-Series Analysis**: Track anomaly trends over time
3. **Data Lake Integration**: Export to Parquet for analytics
4. **Multi-Tenancy**: Isolate data by organization/project
5. **Streaming Updates**: Real-time notifications via WebSockets

## References

- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **PostgreSQL Full-Text Search**: https://www.postgresql.org/docs/current/textsearch.html
- **FAISS**: https://github.com/facebookresearch/faiss
- **Qdrant**: https://qdrant.tech/
- **Chroma**: https://www.trychroma.com/

## Conclusion

The database-backed metadata storage will provide a robust foundation for scaling the Oraculus-DI-Auditor system to production workloads. By using SQLAlchemy for database abstraction, we maintain flexibility to support both SQLite (development) and PostgreSQL (production) deployments.

**Recommended Next Steps**:
1. Implement database abstraction layer with SQLAlchemy
2. Create schema migration scripts
3. Add database configuration to `config.py`
4. Update existing modules to use database storage
5. Add query API endpoints
6. Write integration tests
