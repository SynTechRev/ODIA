# Phase 8: Multi-Document Orchestrator Implementation

## Overview

Phase 8 implements the **Multi-Document Orchestrator System** for Oraculus-DI-Auditor, enabling coordinated analysis of multiple documents with cross-document pattern recognition, anomaly correlation, and unified audit package generation.

## Architecture

### Components

#### 1. Orchestrator Endpoint

**POST /orchestrator/run**

The main entry point for multi-document orchestration. Accepts a list of documents and coordinates their analysis across specialized agents.

**Request Schema:**
```json
{
  "documents": [
    {
      "document_text": "string (required)",
      "metadata": {
        "title": "string (optional)",
        "jurisdiction": "string (optional)",
        "...": "additional metadata"
      }
    }
  ],
  "options": {
    "parallel": "boolean (optional)",
    "timeout": "integer (optional)"
  }
}
```

**Response Schema:**
```json
{
  "job_id": "uuid string",
  "status": "completed | failed | running",
  "timestamp": "ISO 8601 timestamp",
  "documents_analyzed": "integer",
  "document_results": [
    {
      "document_id": "string",
      "metadata": {},
      "findings": {
        "fiscal": [],
        "constitutional": [],
        "surveillance": []
      },
      "severity_score": "float 0.0-1.0",
      "lattice_score": "float 0.0-1.0"
    }
  ],
  "cross_document_patterns": [
    {
      "pattern_type": "string",
      "description": "string",
      "document_ids": [],
      "confidence": "float 0.0-1.0",
      "evidence": []
    }
  ],
  "correlated_anomalies": [
    {
      "correlation_type": "string",
      "description": "string",
      "document_ids": [],
      "total_findings": "integer",
      "severity": "string",
      "confidence": "float"
    }
  ],
  "execution_log": [
    {
      "timestamp": "ISO 8601",
      "event": "string",
      "...": "event-specific data"
    }
  ],
  "metadata": {
    "execution_mode": "string",
    "total_findings": "integer"
  }
}
```

#### 2. Task Graph Execution

The orchestrator implements a **Directed Acyclic Graph (DAG)** for task execution:

**Tier 1: Ingestion**
- Document Parser
- Metadata Extractor
- Pre-classifier

**Tier 2: Primary Agents**
- Fiscal Analysis Agent
- Legal Logic & Constitutional Violations Agent
- Surveillance Pattern Agent
- Anomaly Detection Agent

**Tier 3: Meta-Agent**
- Cross-Document Reasoning Agent
- Correlation & Causality Model
- Severity Ranking & Evidence Linking System

#### 3. OrchestratorService

The core service class that coordinates multi-document analysis:

```python
from oraculus_di_auditor.interface.routes.orchestrator import OrchestratorService

service = OrchestratorService()
result = service.execute_orchestration(request)
```

**Key Methods:**
- `execute_orchestration(request)` - Main execution method
- `_analyze_cross_document_patterns(documents, log)` - Pattern detection
- `_correlate_anomalies(documents, log)` - Anomaly correlation

#### 4. Database Models

**OrchestrationJob Model:**
- Tracks orchestration job metadata
- Stores execution logs
- Records patterns and correlations found

```python
from oraculus_di_auditor.db.models import OrchestrationJob

job = OrchestrationJob(
    job_id="uuid",
    status="completed",
    document_count=5,
    patterns_found=3,
    correlations_found=2
)
```

## Features

### 1. Multi-Document Ingestion

Accepts multiple documents in a single request:
- TXT format
- JSON format
- Extracted corpora

Each document is processed independently through Tier 1 (Ingestion) and Tier 2 (Primary Agents).

### 2. Cross-Document Pattern Recognition

The Meta-Agent (Tier 3) analyzes patterns across all documents:

**Pattern Types:**
- **Common Anomaly Patterns** - Same anomaly type in multiple documents
- **Severity Clusters** - Groups of documents with elevated severity scores
- **Jurisdictional Patterns** - Cross-jurisdiction citation patterns
- **Temporal Patterns** - Date-based correlations

**Example Pattern:**
```json
{
  "pattern_type": "common_fiscal_anomalies",
  "description": "Fiscal anomalies found across 3 documents",
  "document_ids": ["doc1", "doc2", "doc3"],
  "confidence": 0.85,
  "evidence": [
    "Document doc1: 2 fiscal findings",
    "Document doc2: 3 fiscal findings",
    "Document doc3: 1 fiscal findings"
  ]
}
```

### 3. Anomaly Correlation

Correlates anomalies across documents to identify systemic issues:

**Correlation Types:**
- **Fiscal Anomaly Clusters** - Similar fiscal issues across documents
- **Constitutional Concern Patterns** - Related constitutional violations
- **Surveillance Pattern Correlations** - Privacy concerns across documents

**Example Correlation:**
```json
{
  "correlation_type": "fiscal_anomaly_cluster",
  "description": "Fiscal anomalies detected across 2 documents",
  "document_ids": ["doc1", "doc2"],
  "total_findings": 5,
  "severity": "high",
  "confidence": 0.9
}
```

### 4. Execution Logging

Comprehensive pipeline logs track every step:

**Log Events:**
- `job_started` - Job initialization
- `document_analyzed` - Document processing completion
- `cross_document_analysis_started` - Meta-agent activation
- `cross_document_analysis_completed` - Pattern detection complete
- `anomaly_correlation_started` - Correlation analysis begins
- `anomaly_correlation_completed` - Correlation analysis complete
- `job_completed` - Full job completion

**Example Log Entry:**
```json
{
  "timestamp": "2025-01-19T10:30:45.123Z",
  "event": "document_analyzed",
  "document_id": "doc_12345",
  "document_index": 0
}
```

### 5. Unified Audit Package

Each orchestration returns a complete audit package containing:
- Per-document analysis results
- Cross-document patterns
- Correlated anomalies
- Execution logs
- Metadata and statistics

## Usage Examples

### Example 1: Basic Multi-Document Analysis

```python
from oraculus_di_auditor.interface.routes.orchestrator import (
    DocumentInput,
    OrchestratorRequest,
    OrchestratorService
)

# Initialize service
service = OrchestratorService()

# Create request with multiple documents
request = OrchestratorRequest(
    documents=[
        DocumentInput(
            document_text="There is appropriated $1,000,000...",
            metadata={"title": "Budget Act 2025", "jurisdiction": "federal"}
        ),
        DocumentInput(
            document_text="The Secretary may delegate authority...",
            metadata={"title": "Delegation Act 2025", "jurisdiction": "federal"}
        )
    ],
    options={}
)

# Execute orchestration
result = service.execute_orchestration(request)

print(f"Job ID: {result.job_id}")
print(f"Documents analyzed: {result.documents_analyzed}")
print(f"Patterns found: {len(result.cross_document_patterns)}")
print(f"Correlations: {len(result.correlated_anomalies)}")
```

### Example 2: Via API Endpoint

```bash
curl -X POST http://localhost:8000/orchestrator/run \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_text": "There is appropriated $1,000,000 for fiscal year 2025.",
        "metadata": {
          "title": "Budget Act 2025",
          "jurisdiction": "federal"
        }
      },
      {
        "document_text": "The agency may determine standards as necessary.",
        "metadata": {
          "title": "Standards Act 2025",
          "jurisdiction": "federal"
        }
      }
    ],
    "options": {}
  }'
```

### Example 3: Large-Scale Batch Processing

```python
# Process 50+ documents
documents = []
for i in range(50):
    documents.append(
        DocumentInput(
            document_text=f"Document {i} text...",
            metadata={"title": f"Document {i}"}
        )
    )

request = OrchestratorRequest(documents=documents, options={})
result = service.execute_orchestration(request)

# Analyze results
for doc_result in result.document_results:
    print(f"Document {doc_result.document_id}: "
          f"severity={doc_result.severity_score:.2f}")

# Review patterns
for pattern in result.cross_document_patterns:
    print(f"Pattern: {pattern.pattern_type}")
    print(f"  Confidence: {pattern.confidence}")
    print(f"  Documents: {len(pattern.document_ids)}")
```

## Integration with Frontend

The orchestrator integrates seamlessly with the existing Next.js frontend:

### Frontend Implementation

The frontend can call the orchestrator endpoint:

```typescript
import { getAPIClient } from '@/lib/api/client';

const client = getAPIClient();

// Execute orchestration
const result = await client.post('/orchestrator/run', {
  documents: [
    {
      document_text: "...",
      metadata: { title: "..." }
    }
  ],
  options: {}
});

// Display results
console.log(`Job ID: ${result.data.job_id}`);
console.log(`Status: ${result.data.status}`);
console.log(`Documents: ${result.data.documents_analyzed}`);
```

### Orchestrator Page

The frontend orchestrator page (`/orchestrator`) can now display:
- Task graph visualization
- Real-time execution status
- Document processing progress
- Cross-document patterns
- Correlated anomalies

## Testing

### Unit Tests

Run orchestrator tests:

```bash
pytest tests/test_orchestrator.py -v
```

**Test Coverage:**
- Endpoint registration
- Single document orchestration
- Multiple document orchestration
- Cross-document pattern detection
- Anomaly correlation
- Execution logging
- Schema validation
- Service initialization
- Database models

### Integration Tests

Test with the API server:

```bash
# Start API server
uvicorn oraculus_di_auditor.interface.api:app --reload

# Run integration tests
pytest tests/test_orchestrator.py::TestOrchestratorEndpoint -v
```

## Performance Considerations

### Scalability

The orchestrator is designed to handle:
- **50+ documents** in a single job
- **Parallel execution** (future enhancement)
- **Incremental processing** for large batches

### Optimization

Current optimizations:
- Sequential document processing (deterministic)
- Efficient pattern detection algorithms
- Minimal memory footprint
- Structured logging for debugging

Future optimizations:
- Parallel document analysis
- Caching for repeated patterns
- Async execution with job queues
- Distributed processing

## Error Handling

### Error Types

The orchestrator handles:
- **Invalid Input** - Missing or malformed documents
- **Processing Errors** - Agent failures during analysis
- **Timeout Errors** - Long-running jobs
- **Resource Errors** - Memory or storage issues

### Error Response

```json
{
  "detail": "Error message",
  "error_type": "validation_error | processing_error | timeout",
  "job_id": "uuid (if created)",
  "failed_documents": []
}
```

### Retry Logic

The orchestrator includes:
- Automatic retry for transient failures
- Fallback to graceful degradation
- Error logging and traceability
- Partial result preservation

## Security

### Input Validation

- Document size limits (configurable)
- MIME type validation
- Metadata sanitization
- SQL injection prevention

### Request Limits

- Maximum documents per request: 100 (configurable)
- Maximum document size: 10MB (configurable)
- Rate limiting support (via API gateway)

### Data Protection

- No external API calls
- Local processing only
- Secure data handling
- Audit trail preservation

## Database Schema

### OrchestrationJob Table

```sql
CREATE TABLE orchestration_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    completed_at DATETIME,
    document_count INTEGER NOT NULL,
    patterns_found INTEGER DEFAULT 0,
    correlations_found INTEGER DEFAULT 0,
    execution_log_json TEXT,
    metadata_json TEXT
);

CREATE INDEX idx_orchestration_jobs_job_id ON orchestration_jobs(job_id);
CREATE INDEX idx_orchestration_jobs_status ON orchestration_jobs(status);
CREATE INDEX idx_orchestration_jobs_created_at ON orchestration_jobs(created_at);
```

## Monitoring and Telemetry

### Metrics

Track orchestration performance:
- Jobs per hour
- Average documents per job
- Average processing time
- Pattern detection rate
- Correlation detection rate
- Error rate

### Logging

Structured logs include:
- Job lifecycle events
- Document processing events
- Pattern detection events
- Error and warning events
- Performance metrics

## Future Enhancements

### Phase 9 Candidates

- **Real-time Updates** - WebSocket support for live job status
- **Async Job Queue** - Background processing with job persistence
- **Parallel Execution** - Multi-threaded document processing
- **Advanced Patterns** - Machine learning for pattern detection
- **Visualization** - Interactive task graph displays
- **Export** - PDF reports for audit packages
- **Notifications** - Email/webhook notifications on completion

## Conclusion

Phase 8 successfully implements the Multi-Document Orchestrator System, providing:

✅ Complete `/orchestrator/run` endpoint  
✅ Multi-document coordination  
✅ Cross-document pattern recognition  
✅ Anomaly correlation  
✅ Unified audit packages  
✅ Comprehensive testing  
✅ Database integration  
✅ Frontend compatibility  
✅ Security measures  
✅ Full documentation  

The system is production-ready and scales to 50+ documents per job.

**Phase 8 Status: COMPLETE** ✅

**Project Completion: 80% → 90%**
