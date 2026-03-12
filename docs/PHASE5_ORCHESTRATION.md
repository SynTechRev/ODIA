# Phase 5: Autonomous Agent Networking & Async Orchestration

## Overview

Phase 5 implements the autonomous orchestration kernel for Oraculus-DI-Auditor, enabling multi-agent coordination, task scheduling, and parallel execution for complex document analysis workflows.

## Architecture

### Core Components

#### 1. Phase5Orchestrator
The main coordination kernel that:
- Classifies incoming requests
- Generates task execution plans
- Assigns tasks to specialized agents
- Executes tasks with proper dependency handling
- Merges results into harmonized outputs

#### 2. Agents

Six specialized agents handle different aspects of document processing:

**IngestionAgent**
- Materializes documents into structured chunks
- Normalizes text and metadata
- Generates document IDs and checksums
- Creates chunks with configurable overlap

**AnalysisAgent**
- Executes unified analysis pipeline
- Runs fiscal, constitutional, and surveillance analysis
- Computes scalar scores
- Generates structured findings

**AnomalyAgent**
- Identifies inconsistencies and contradictions
- Detects risk patterns
- Flags high-priority issues
- Computes risk scores

**SynthesisAgent**
- Produces narrative summaries
- Identifies cross-document themes
- Detects structural divergences
- Generates recommendations

**DatabaseAgent**
- Persists documents and analyses
- Maintains provenance records
- Handles query operations
- Stores anomaly data

**InterfaceAgent**
- Formats results for external systems
- Generates reports (JSON, CSV)
- Prepares API responses
- Creates visualizations

#### 3. TaskGraph

Manages task dependencies and execution order:
- Topological sorting for dependency resolution
- Parallel execution where possible
- Sequential execution where required
- Hybrid execution for complex workflows
- Circular dependency detection

#### 4. Result Formats

Four structured output formats:

**TaskExecutionPlan**
```json
{
  "task_graph": [...],
  "agents_involved": [...],
  "inputs": {...},
  "execution_mode": "sequential|parallel|hybrid",
  "dependencies": [...],
  "expected_outputs": [...],
  "risk_flags": [...],
  "confidence": 0.95
}
```

**AgentResponse**
```json
{
  "agent": "AnalysisAgent",
  "action": "run_analysis",
  "inputs": {...},
  "outputs": {...},
  "provenance": {...},
  "confidence": 0.98
}
```

**CrossDocumentSynthesis**
```json
{
  "summary": "...",
  "themes": [...],
  "anomalies": [...],
  "scalar_metrics": {...},
  "cross_document_links": [...],
  "risk_assessment": {...},
  "recommendations": [...],
  "confidence": 0.85
}
```

**PipelineOutput** (Phase 4 Compatible)
```json
{
  "metadata": {...},
  "findings": {
    "fiscal": [...],
    "constitutional": [...],
    "surveillance": [...],
    "anomalies": [...]
  },
  "scores": {...},
  "flags": [...],
  "provenance": {...},
  "confidence": 0.95,
  "timestamp": "2025-11-18T04:14:03.535Z"
}
```

## Usage

### Basic Single Document Analysis

```python
from oraculus_di_auditor.orchestrator import Phase5Orchestrator

orchestrator = Phase5Orchestrator()

request = {
    "document_text": "There is appropriated $1,000,000 for fiscal year 2025...",
    "metadata": {
        "title": "Budget Authorization Act 2025",
        "jurisdiction": "federal"
    }
}

result = orchestrator.execute_request(request)

print(f"Request type: {result['request_type']}")
print(f"Confidence: {result['confidence']}")
print(f"Findings: {result['harmonized_output']['findings']}")
```

### Cross-Document Analysis

```python
request = {
    "documents": [
        {
            "text": "Document 1 text...",
            "metadata": {"title": "Act 1", "year": 2024}
        },
        {
            "text": "Document 2 text...",
            "metadata": {"title": "Act 2", "year": 2025}
        }
    ]
}

result = orchestrator.execute_request(request)

# Access cross-document synthesis
synthesis = result['harmonized_output']
print(f"Themes: {synthesis['themes']}")
print(f"Cross-links: {synthesis['cross_document_links']}")
print(f"Recommendations: {synthesis['recommendations']}")
```

### Plan-Only Mode

Generate execution plan without running tasks:

```python
result = orchestrator.execute_request(request, mode="plan_only")

plan = result['execution_plan']
print(f"Execution mode: {plan['execution_mode']}")
print(f"Agents involved: {plan['agents_involved']}")
print(f"Task count: {len(plan['task_graph'])}")
```

### Get Agent Information

```python
info = orchestrator.get_agent_info()

print(f"Available agents: {info['agents']}")
print(f"Capabilities: {info['capabilities']}")
```

## Execution Modes

The orchestrator automatically determines the optimal execution mode based on task dependencies:

### Sequential Mode
All tasks must run in strict order:
```
Task1 → Task2 → Task3 → Task4
```

### Parallel Mode
All tasks can run simultaneously:
```
Task1
Task2  } All execute in parallel
Task3
Task4
```

### Hybrid Mode
Mix of sequential and parallel execution:
```
Level 0: Task1, Task2  (parallel)
Level 1: Task3, Task4  (parallel, depends on Level 0)
Level 2: Task5         (sequential, depends on Level 1)
```

## Design Principles

### 1. Deterministic Behavior
- All operations are reproducible
- No hidden state
- No external API calls
- Pure functions where possible

### 2. Explainability
- Full provenance tracking
- Confidence scores at all levels
- Detailed lineage information
- Human-readable summaries

### 3. Chain of Custody
- Every transformation tracked
- Source attribution maintained
- Timestamp all operations
- Cryptographic hashing

### 4. Secure Defaults
- Input validation
- Error handling
- Graceful degradation
- No credential exposure

### 5. Graceful Degradation
- Continue on agent failure
- Report partial results
- Track error conditions
- Maintain system stability

## Performance Characteristics

### Task Execution
- **Parallel tasks**: Execute simultaneously within a level
- **Sequential tasks**: Execute in dependency order
- **Hybrid workflows**: Mix of parallel and sequential execution

### Memory Usage
- **Single document**: ~50MB typical
- **10 documents**: ~200MB typical
- **100 documents**: ~1.5GB typical

### Processing Time
- **Single document analysis**: 100-500ms
- **Cross-document (10 docs)**: 1-3 seconds
- **Cross-document (100 docs)**: 10-30 seconds

## Integration with Phase 4

Phase 5 is fully backward compatible with Phase 4:

```python
# Phase 4 (direct pipeline)
from oraculus_di_auditor.analysis.pipeline import run_full_analysis

result = run_full_analysis(document_text, metadata)

# Phase 5 (orchestrated)
from oraculus_di_auditor.orchestrator import Phase5Orchestrator

orchestrator = Phase5Orchestrator()
result = orchestrator.execute_request({
    "document_text": document_text,
    "metadata": metadata
})
harmonized = result['harmonized_output']  # Phase 4 compatible format
```

## Testing

Comprehensive test suite with 34 tests covering:

- Task graph management
- Agent execution
- Orchestration workflows
- Result formatting
- Provenance tracking
- Confidence scoring
- Error handling

Run tests:
```bash
pytest tests/test_phase5_orchestrator.py -v
```

## Future Enhancements

### Phase 5.1: Advanced Scheduling
- Priority-based task scheduling
- Resource allocation
- Load balancing
- Timeout handling

### Phase 5.2: Distributed Execution
- Multi-process execution
- Remote agent invocation
- Result streaming
- Progress tracking

### Phase 5.3: Agent Learning
- Agent performance metrics
- Adaptive confidence scoring
- Pattern recognition
- Self-optimization

## Security Considerations

### Data Privacy
- All processing is local
- No external API calls
- No data exfiltration
- Secure defaults

### Input Validation
- Schema validation
- Type checking
- Bounds checking
- Sanitization

### Error Handling
- Graceful degradation
- Error isolation
- Safe defaults
- Audit logging

## API Reference

See module docstrings for detailed API documentation:

- `orchestrator.py`: Main orchestration kernel
- `agents.py`: Agent implementations
- `task_graph.py`: Task dependency management
- `results.py`: Result formatting

## Examples

See `tests/test_phase5_orchestrator.py` for comprehensive usage examples.

## Contributing

When adding new agents:

1. Inherit from `Agent` base class
2. Implement `execute()` method
3. Return structured `AgentResponse`
4. Include provenance metadata
5. Add comprehensive tests
6. Update this documentation

## License

Copyright © 2025 Synthetic Technology Revolution
