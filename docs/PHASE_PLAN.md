# Oraculus DI Auditor - Phase Plan

## Phase 1: Ingestion & Normalization (Current)

**Goal**: Establish reliable document ingestion and normalization pipeline

### Deliverables
- [x] Multi-format document loader (TXT, JSON, PDF)
- [x] Canonical schema definition
- [x] Text chunking with overlap
- [x] CLI interface for ingestion
- [x] Unit tests for core functionality

### Metrics
- Support for 3+ document formats
- 100% schema compliance
- < 1s processing time per document

### Status: ✅ Complete

## Phase 2: Analysis & Anomaly Detection (Next)

**Goal**: Implement rule-based and ML-based anomaly detection

### Tasks
1. **Rule-Based Detectors**
   - Implement long-sentence detector
   - Implement cross-reference validator
   - Implement date consistency checker
   - Add severity scoring system

2. **Embedding Pipeline**
   - Deploy hash-based local embedder
   - Create vector storage system
   - Implement similarity search
   - Build retrieval interface

3. **Reporting System**
   - JSON report generator with provenance
   - CSV export for spreadsheet analysis
   - Confidence scoring
   - Audit trail generation

### Deliverables
- Anomaly detection engine with 3+ detectors
- Embedding and retrieval system
- Report generation (JSON + CSV)
- Integration tests
- Documentation updates

### Metrics
- False anomaly rate < 2%
- Anomaly detection coverage ≥ 90%
- Report generation time < 5s for 100 documents

### Target: End of Q1 2026

## Phase 3: Scale & Intelligence (Future)

**Goal**: Scale to handle 11 years of legislative data with advanced analytics

### Tasks
1. **Data Ingestion at Scale**
   - Ingest all 54 titles of U.S. Code
   - Ingest all 50 titles of CFR
   - Build temporal lineage tracking
   - Create cross-title reference graph

2. **Advanced Analytics**
   - Train custom ML models for anomaly detection
   - Implement semantic similarity using transformers
   - Build contradiction detection system
   - Create impact analysis tools

3. **Visualization & Exploration**
   - Interactive reference graph viewer
   - Temporal evolution visualization
   - Anomaly heatmaps
   - Search and filter interface

4. **Performance Optimization**
   - Migrate to database backend (PostgreSQL)
   - Implement parallel processing
   - Add caching layer
   - Optimize vector search

### Deliverables
- Complete U.S. Code & CFR ingestion
- Advanced ML models
- Interactive visualization
- Scalable architecture
- Comprehensive documentation
- Public research paper

### Metrics
- Handle 1M+ documents
- Query response time < 100ms
- ML model accuracy ≥ 95%
- Full provenance for all documents

### Target: End of 2026

## Success Criteria

### Phase 1
- ✅ All tests passing
- ✅ Code coverage ≥ 90%
- ✅ Documentation complete
- ✅ CLI functional

### Phase 2
- [ ] Anomaly detection operational
- [ ] Reports generated successfully
- [ ] Integration tests passing
- [ ] False positive rate < 2%

### Phase 3
- [ ] Full dataset ingested
- [ ] Advanced ML models deployed
- [ ] Visualization complete
- [ ] Research findings published

## Risk Mitigation

### Data Privacy
- Keep all data local
- Gitignore sensitive directories
- Document privacy policies

### Technical Debt
- Regular refactoring sprints
- Code review requirements
- Automated testing

### Scalability
- Design for scale from day 1
- Benchmark early and often
- Plan database migration path
