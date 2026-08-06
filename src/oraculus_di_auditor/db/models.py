"""SQLAlchemy ORM models for Oraculus-DI-Auditor.

Implements 7-table schema for documents, provenance, sections, references,
analyses, anomalies, and embeddings.

Based on database design in docs/database-design.md
"""

from __future__ import annotations

from datetime import UTC, datetime

# Fail-fast import: database functionality requires SQLAlchemy
try:  # pragma: no cover - import logic
    from sqlalchemy import (
        Boolean,
        Column,
        DateTime,
        Float,
        ForeignKey,
        Integer,
        String,
        Text,
    )
    from sqlalchemy.orm import declarative_base, relationship
except ImportError as e:  # pragma: no cover - environment without dependency
    raise ImportError(
        "SQLAlchemy is required for database models. "
        "Install with: pip install SQLAlchemy"
    ) from e

Base = declarative_base()


class Document(Base):  # type: ignore
    """Document metadata table."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    document_type = Column(String(50), nullable=False, index=True)
    jurisdiction = Column(String(100), index=True)
    authority = Column(String(255))
    version_date = Column(DateTime, index=True)
    signatory = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    metadata_json = Column(Text)  # JSON blob for extensibility

    # Relationships
    provenance = relationship("Provenance", back_populates="document", uselist=False)
    sections = relationship("Section", back_populates="document")
    analyses = relationship("Analysis", back_populates="document")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, document_id='{self.document_id}', title='{self.title[:50]}...')>"  # noqa: E501


class Provenance(Base):  # type: ignore
    """Document provenance and integrity tracking."""

    __tablename__ = "provenance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        String(255), ForeignKey("documents.document_id"), nullable=False, index=True
    )
    source_path = Column(Text, nullable=False)
    hash = Column(String(64), nullable=False, index=True)  # SHA-256
    verified_on = Column(DateTime, nullable=False)
    file_size_bytes = Column(Integer)
    format = Column(String(20))  # json, txt, pdf, xml

    # Relationship
    document = relationship("Document", back_populates="provenance")

    def __repr__(self) -> str:
        return f"<Provenance(document_id='{self.document_id}', hash='{self.hash[:16]}...')>"  # noqa: E501


class Section(Base):  # type: ignore
    """Document sections for full-text search."""

    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        String(255), ForeignKey("documents.document_id"), nullable=False, index=True
    )
    section_id = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    order_index = Column(Integer)

    # Relationship
    document = relationship("Document", back_populates="sections")

    def __repr__(self) -> str:
        return f"<Section(document_id='{self.document_id}', section_id='{self.section_id}')>"  # noqa: E501


class Reference(Base):  # type: ignore
    """Cross-references and citations."""

    __tablename__ = "references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_document_id = Column(
        String(255), ForeignKey("documents.document_id"), nullable=False, index=True
    )
    target_document_id = Column(
        String(255), ForeignKey("documents.document_id"), index=True
    )
    reference_text = Column(Text, nullable=False)
    reference_type = Column(String(50), index=True)  # usc, cfr, case, statute, etc.

    def __repr__(self) -> str:
        return f"<Reference(source='{self.source_document_id}', target='{self.target_document_id}', type='{self.reference_type}')>"  # noqa: E501


class Analysis(Base):  # type: ignore
    """Analysis results from audit engine."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        String(255), ForeignKey("documents.document_id"), nullable=False, index=True
    )
    analysis_timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    anomaly_count = Column(Integer, nullable=False)
    scalar_score = Column(Float, nullable=False, index=True)  # 0.0 to 1.0
    severity_score = Column(Float)  # Phase 4 addition
    coherence_bonus = Column(Float)  # Phase 4 addition
    engine_version = Column(String(20))
    summary = Column(Text)  # Phase 4 addition
    metadata_json = Column(Text)  # JSON blob for additional fields

    # Relationships
    document = relationship("Document", back_populates="analyses")
    anomalies = relationship("Anomaly", back_populates="analysis")

    def __repr__(self) -> str:
        return f"<Analysis(id={self.id}, document_id='{self.document_id}', score={self.scalar_score:.2f})>"  # noqa: E501


class Anomaly(Base):  # type: ignore
    """Detected anomalies with full details."""

    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False, index=True)
    anomaly_id = Column(
        String(255), nullable=False
    )  # e.g., fiscal:missing-provenance-hash
    issue = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high
    layer = Column(
        String(50), nullable=False, index=True
    )  # fiscal, constitutional, etc.
    details_json = Column(Text)  # JSON blob with structured details

    # Relationship
    analysis = relationship("Analysis", back_populates="anomalies")

    def __repr__(self) -> str:
        return f"<Anomaly(id={self.id}, anomaly_id='{self.anomaly_id}', severity='{self.severity}')>"  # noqa: E501


class OrchestrationJob(Base):  # type: ignore
    """Phase 8 orchestration job tracking."""

    __tablename__ = "orchestration_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(
        String(50), nullable=False, index=True
    )  # queued, running, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    completed_at = Column(DateTime)
    document_count = Column(Integer, nullable=False)
    patterns_found = Column(Integer, default=0)
    correlations_found = Column(Integer, default=0)
    execution_log_json = Column(Text)  # JSON blob with execution log
    metadata_json = Column(Text)  # JSON blob for additional metadata

    def __repr__(self) -> str:
        return f"<OrchestrationJob(job_id='{self.job_id}', status='{self.status}', documents={self.document_count})>"  # noqa: E501


class GovernancePolicy(Base):  # type: ignore
    """Phase 9 governance policy storage."""

    __tablename__ = "governance_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(255), unique=True, nullable=False, index=True)
    policy_name = Column(String(255), nullable=False)
    policy_type = Column(
        String(50), nullable=False, index=True
    )  # document, orchestrator, security, analysis
    policy_version = Column(String(20), nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    severity = Column(String(20), nullable=False)  # error, warning, critical
    policy_config_json = Column(Text)  # JSON blob with policy configuration
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<GovernancePolicy(policy_id='{self.policy_id}', type='{self.policy_type}', version='{self.policy_version}')>"  # noqa: E501


class ValidationResult(Base):  # type: ignore
    """Phase 9 validation result tracking."""

    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    validation_id = Column(String(255), unique=True, nullable=False, index=True)
    validation_type = Column(
        String(50), nullable=False, index=True
    )  # full, quick, security, policy
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    overall_status = Column(
        String(50), nullable=False, index=True
    )  # success, warning, error
    checks_performed = Column(Integer, default=0)
    errors_found = Column(Integer, default=0)
    warnings_found = Column(Integer, default=0)
    results_json = Column(Text)  # JSON blob with full validation results

    def __repr__(self) -> str:
        return f"<ValidationResult(validation_id='{self.validation_id}', type='{self.validation_type}', status='{self.overall_status}')>"  # noqa: E501


class SecurityEvent(Base):  # type: ignore
    """Phase 9 security event tracking."""

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(
        String(50), nullable=False, index=True
    )  # threat_detected, policy_violation, sanitation
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    severity = Column(
        String(20), nullable=False, index=True
    )  # low, medium, high, critical
    threat_score = Column(Float, default=0.0)
    document_id = Column(String(255), index=True)  # Optional reference to document
    event_details_json = Column(Text)  # JSON blob with event details

    def __repr__(self) -> str:
        return f"<SecurityEvent(event_id='{self.event_id}', type='{self.event_type}', severity='{self.severity}')>"  # noqa: E501


class GCNRule(Base):  # type: ignore
    """Phase 10 Global Constraint Network rule storage."""

    __tablename__ = "gcn_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(255), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(
        String(50), nullable=False, index=True
    )  # structural, policy, document, pipeline, safety
    rule_version = Column(String(20), nullable=False, index=True)
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(
        Integer, default=0, index=True
    )  # Higher priority rules evaluated first
    scope = Column(String(100), nullable=False)  # global, agent, document, job
    constraint_expression = Column(Text, nullable=False)  # Constraint definition
    violation_action = Column(
        String(50), nullable=False
    )  # block, warn, log, quarantine
    rule_config_json = Column(Text)  # JSON blob with additional configuration
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        return f"<GCNRule(rule_id='{self.rule_id}', type='{self.rule_type}', version='{self.rule_version}')>"  # noqa: E501


class AgentNode(Base):  # type: ignore
    """Phase 10 Agent Mesh node registration."""

    __tablename__ = "agent_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    agent_name = Column(String(255), nullable=False)
    agent_type = Column(
        String(50), nullable=False, index=True
    )  # sentinel, constraint, routing, synthesis, specialist
    status = Column(
        String(50), nullable=False, index=True
    )  # active, inactive, suspended, error
    capabilities = Column(Text)  # JSON array of capabilities
    version = Column(String(20), nullable=False)
    priority = Column(Integer, default=0, index=True)
    max_concurrent_tasks = Column(Integer, default=10)
    current_task_count = Column(Integer, default=0)
    registered_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    last_heartbeat = Column(DateTime, default=lambda: datetime.now(UTC))
    metadata_json = Column(Text)  # JSON blob for additional agent metadata

    # Relationships
    outgoing_links = relationship(
        "AgentLink",
        foreign_keys="AgentLink.source_agent_id",
        back_populates="source_agent",
    )
    incoming_links = relationship(
        "AgentLink",
        foreign_keys="AgentLink.target_agent_id",
        back_populates="target_agent",
    )

    def __repr__(self) -> str:
        return f"<AgentNode(agent_id='{self.agent_id}', type='{self.agent_type}', status='{self.status}')>"  # noqa: E501


class AgentLink(Base):  # type: ignore
    """Phase 10 Agent Mesh connectivity graph."""

    __tablename__ = "agent_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(String(255), unique=True, nullable=False, index=True)
    source_agent_id = Column(
        String(255), ForeignKey("agent_nodes.agent_id"), nullable=False, index=True
    )
    target_agent_id = Column(
        String(255), ForeignKey("agent_nodes.agent_id"), nullable=False, index=True
    )
    link_type = Column(
        String(50), nullable=False, index=True
    )  # delegation, synthesis, coordination, notification
    enabled = Column(Boolean, default=True, index=True)
    weight = Column(Float, default=1.0)  # Link weight for routing
    latency_ms = Column(Float)  # Measured or expected latency
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    metadata_json = Column(Text)  # JSON blob for additional link metadata

    # Relationships
    source_agent = relationship(
        "AgentNode", foreign_keys=[source_agent_id], back_populates="outgoing_links"
    )
    target_agent = relationship(
        "AgentNode", foreign_keys=[target_agent_id], back_populates="incoming_links"
    )

    def __repr__(self) -> str:
        return f"<AgentLink(link_id='{self.link_id}', source='{self.source_agent_id}', target='{self.target_agent_id}')>"  # noqa: E501


class MeshExecutionJob(Base):  # type: ignore
    """Phase 10 Multi-agent mesh execution job tracking."""

    __tablename__ = "mesh_execution_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    job_type = Column(
        String(50), nullable=False, index=True
    )  # analysis, synthesis, routing, validation
    status = Column(
        String(50), nullable=False, index=True
    )  # queued, routing, executing, synthesizing, completed, failed, interrupted
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    agent_count = Column(Integer, default=0)  # Number of agents involved
    task_count = Column(Integer, default=0)  # Number of tasks executed
    gcn_validated = Column(Boolean, default=False)  # GCN pre-validation status
    governor_approved = Column(Boolean, default=False)  # Governor approval status
    execution_graph_json = Column(Text)  # JSON blob with execution DAG
    results_json = Column(Text)  # JSON blob with aggregated results
    metadata_json = Column(Text)  # JSON blob for additional job metadata

    def __repr__(self) -> str:
        return f"<MeshExecutionJob(job_id='{self.job_id}', type='{self.job_type}', status='{self.status}')>"  # noqa: E501


class AgentBehaviorEvent(Base):  # type: ignore
    """Phase 10 Agent behavior auditing and event tracking."""

    __tablename__ = "agent_behavior_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(255), unique=True, nullable=False, index=True)
    agent_id = Column(
        String(255), ForeignKey("agent_nodes.agent_id"), nullable=False, index=True
    )
    job_id = Column(
        String(255), ForeignKey("mesh_execution_jobs.job_id"), index=True
    )  # Optional job reference
    event_type = Column(
        String(50), nullable=False, index=True
    )  # task_start, task_complete, task_fail, constraint_violation, policy_check  # noqa: E501
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), index=True)
    severity = Column(
        String(20), nullable=False, index=True
    )  # info, warning, error, critical
    task_name = Column(String(255))  # Task being executed
    constraint_violated = Column(String(255))  # GCN rule violated (if any)
    event_details_json = Column(Text)  # JSON blob with event details
    metrics_json = Column(Text)  # JSON blob with performance metrics

    def __repr__(self) -> str:
        return f"<AgentBehaviorEvent(event_id='{self.event_id}', agent_id='{self.agent_id}', type='{self.event_type}')>"  # noqa: E501


class SeenHash(Base):  # type: ignore
    """v2.7.1 — webhook dedup table.

    Records every SHA-256 the `/api/v1/webhook/ingest-and-analyze` endpoint
    has accepted so WF-001's retry loop + CivicPlus's duplicate URLs don't
    cause the same document to be analysed twice. First-write-wins; the
    webhook route queries this table before running the Tier 1 pipeline.

    sha256 is the primary key so duplicate inserts raise an IntegrityError
    that the caller can translate into an `already_seen=true` response.
    """

    __tablename__ = "seen_hashes"

    sha256 = Column(String(64), primary_key=True)
    first_seen_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    document_id = Column(String(255), nullable=True, index=True)
    jurisdiction_id = Column(String(100), nullable=True, index=True)
    # v2.9.3 Track A.2 — extraction provenance. Nullable for backward
    # compatibility with rows written before the columns existed; the
    # session-bootstrap helper ALTER-TABLE-ADDs the columns on existing
    # SQLite databases via _migrate_seen_hash_extraction_columns().
    text_extraction_method = Column(String(32), nullable=True)
    text_char_count = Column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SeenHash(sha256='{self.sha256[:16]}...', "
            f"jurisdiction_id='{self.jurisdiction_id}', "
            f"extraction='{self.text_extraction_method}')>"
        )


class CPRARequest(Base):  # type: ignore
    """v2.7.1 — tracked California Public Records Act request.

    Rows here are what WF-005 (CPRA Deadline Watcher) queries each
    morning via `GET /api/v1/cpra/deadlines-within/{window}` to decide
    which requests are approaching their statutory response deadline.

    California Gov. Code § 7922.535 gives the public agency 10 calendar
    days to respond to a CPRA request, extendable by 14 days under
    § 7922.535(b). Most of this table's business logic lives in the
    calling workflow (escalation rules, who gets alerted); the DB just
    stores the facts: when filed, when due, current status, free-text
    description for the operator.

    Indexed on (jurisdiction_id, statutory_deadline) so the watcher's
    range query is covered — `WHERE deadline BETWEEN now AND now+window`
    on a jurisdiction-scoped slice is the hot query.
    """

    __tablename__ = "cpra_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jurisdiction_id = Column(String(100), nullable=False, index=True)
    requested_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    statutory_deadline = Column(DateTime, nullable=False, index=True)
    status = Column(
        String(32), nullable=False, default="open", index=True
    )  # open, responded, extended, withdrawn, overdue
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        deadline_iso = (
            self.statutory_deadline.isoformat() if self.statutory_deadline else None
        )
        return (
            f"<CPRARequest(id={self.id}, "
            f"jurisdiction_id='{self.jurisdiction_id}', "
            f"status='{self.status}', "
            f"deadline={deadline_iso})>"
        )


class FieldObservation(Base):  # type: ignore
    """v2.7.1 C4 — operator-submitted field verification of a surveillance
    deployment.

    Rows here are submitted from the field (mobile browser, Obsidian
    dataview, or a dedicated CivicSignal app) when an operator physically
    verifies — or fails to verify — a Flock ALPR / BWC / drone deployment
    that was supposed to exist per vendor contracts or press releases.

    The KEY analytical signal is `exclusion_zone`: when True, the
    observation asserts the vendor has placed a device inside a zone
    their contract forbids (parks near schools, exempted residential
    streets, outside jurisdiction boundaries). Those rows get promoted
    into the MAS report's "Field-Verified Placement" section verbatim
    as evidence.

    Schema alignment: the verification_type enum matches the DeFlock
    cheatsheet (photo with vantage, pass-by confirmation, cross-ref
    against the deflock.me community map). Lat/lng are stored as
    plain floats — 6 decimal places is ~11cm, more precision than any
    GPS receiver actually delivers, so Float is sufficient.
    """

    __tablename__ = "field_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jurisdiction_id = Column(String(100), nullable=False, index=True)
    observed_at = Column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    verification_type = Column(
        String(32), nullable=False, index=True
    )  # photo, pass_by, deflock_cross_ref
    notes = Column(Text, nullable=True)
    exclusion_zone = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self) -> str:
        return (
            f"<FieldObservation(id={self.id}, "
            f"jurisdiction_id='{self.jurisdiction_id}', "
            f"type='{self.verification_type}', "
            f"exclusion={self.exclusion_zone})>"
        )


class WebhookAuditLog(Base):  # type: ignore
    """v2.7.1 — litigation-grade audit trail for every n8n webhook call.

    Written best-effort from the webhook routes. One row per call to
    any /api/v1/webhook/* endpoint, regardless of whether the call
    succeeded or errored. Combined with n8n's own execution history
    (keyed by X-N8N-Execution-Id), this gives the Provenance Chain
    Export (WF-014) a complete chain from scraper trigger → document
    hash → finding.

    Indexed on timestamp + workflow_id so the export query can slice
    by time window or by specific workflow (e.g. "all WF-001 calls in
    the last 30 days").
    """

    __tablename__ = "webhook_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True
    )
    endpoint = Column(String(64), nullable=False)
    workflow_id = Column(String(64), nullable=True, index=True)
    execution_id = Column(String(64), nullable=True)
    status = Column(Integer, nullable=False)
    source_ip = Column(String(45), nullable=True)  # fits IPv6

    def __repr__(self) -> str:
        return (
            f"<WebhookAuditLog(id={self.id}, endpoint='{self.endpoint}', "
            f"workflow_id='{self.workflow_id}', status={self.status})>"
        )


# ---------------------------------------------------------------------------
# C.O.N.T.R.A. schema extension (Framework V1.0, August 2026)
# Additive — does not modify any existing table.
# ---------------------------------------------------------------------------


class CommercialEntity(Base):  # type: ignore
    """C.O.N.T.R.A. entity registry: businesses whose contracts are ingested."""

    __tablename__ = "commercial_entities"

    entity_id = Column(String(255), primary_key=True)
    canonical_name = Column(Text, nullable=False)
    naics = Column(String(10))  # NAICS industry code
    corporate_family = Column(String(255))
    in_contra_corpus = Column(Boolean, default=False)
    in_tulare_priority_list = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    aliases = relationship("CommercialEntityAlias", back_populates="entity")
    documents = relationship("CommercialDocument", back_populates="entity")

    def __repr__(self) -> str:
        return f"<CommercialEntity(entity_id='{self.entity_id}', name='{self.canonical_name}')>"


class CommercialEntityAlias(Base):  # type: ignore
    """Name aliases for entity fuzzy-matching (e.g. 'ATT' -> AT&T Mobility LLC)."""

    __tablename__ = "commercial_entity_aliases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_id = Column(
        String(255), ForeignKey("commercial_entities.entity_id"), nullable=False
    )
    alias = Column(Text, nullable=False)

    entity = relationship("CommercialEntity", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<CommercialEntityAlias(entity_id='{self.entity_id}', alias='{self.alias}')>"


class CommercialDocument(Base):  # type: ignore
    """Commercial contract or privacy notice ingested through C.O.N.T.R.A."""

    __tablename__ = "commercial_documents"

    document_hash = Column(String(64), primary_key=True)  # SHA-256
    entity_id = Column(
        String(255), ForeignKey("commercial_entities.entity_id"), nullable=False
    )
    doc_type = Column(
        String(50), nullable=False
    )  # tos, privacy_notice, arbitration, employment, eula
    effective_date = Column(DateTime)
    version_label = Column(String(100))
    source_url = Column(Text)
    wayback_url = Column(Text)
    retrieval_ts = Column(DateTime, nullable=False)
    ingest_ts = Column(DateTime, default=lambda: datetime.now(UTC))

    entity = relationship("CommercialEntity", back_populates="documents")
    findings = relationship("ContraFinding", back_populates="document")
    casi_score = relationship("CasiScore", back_populates="document", uselist=False)

    def __repr__(self) -> str:
        return f"<CommercialDocument(hash='{self.document_hash[:16]}...', type='{self.doc_type}')>"


class ContraFinding(Base):  # type: ignore
    """Single L-11 through L-20 detector finding on a commercial document."""

    __tablename__ = "contra_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    finding_id = Column(String(255), unique=True, nullable=False, index=True)
    document_hash = Column(
        String(64), ForeignKey("commercial_documents.document_hash"), nullable=False
    )
    layer = Column(String(10), nullable=False, index=True)  # L-11 through L-20
    sub_detector = Column(String(5), nullable=False)  # A, B, ...
    severity = Column(String(20), nullable=False, index=True)  # low/medium/high/critical
    doctrinal_anchor = Column(Text, nullable=False)
    evidence_start = Column(Integer)
    evidence_end = Column(Integer)
    evidence_excerpt = Column(Text)  # <= 15 words verbatim
    scoring_axis = Column(String(50))
    scoring_delta = Column(Integer)
    remedy_channels = Column(Text)  # JSON array
    prompt_id = Column(String(100))
    prompt_version = Column(String(20))
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    document = relationship("CommercialDocument", back_populates="findings")

    def __repr__(self) -> str:
        return f"<ContraFinding(finding_id='{self.finding_id}', layer='{self.layer}', severity='{self.severity}')>"


class CasiScore(Base):  # type: ignore
    """CASI aggregate score for a single commercial document."""

    __tablename__ = "casi_scores"

    document_hash = Column(
        String(64), ForeignKey("commercial_documents.document_hash"), primary_key=True
    )
    remedy_foreclosure = Column(Integer, nullable=False)
    data_extraction_depth = Column(Integer, nullable=False)
    modification_and_consent = Column(Integer, nullable=False)
    procedural_adhesion = Column(Integer, nullable=False)
    enforcement_cost_asymmetry = Column(Integer, nullable=False)
    aggregate = Column(Integer, nullable=False)
    band = Column(String(50), nullable=False)
    framework_version = Column(String(20), nullable=False, default="1.0")
    computed_at = Column(DateTime, default=lambda: datetime.now(UTC))

    document = relationship("CommercialDocument", back_populates="casi_score")

    def __repr__(self) -> str:
        return f"<CasiScore(hash='{self.document_hash[:16]}...', aggregate={self.aggregate}, band='{self.band}')>"


class S128196Case(Base):  # type: ignore
    """California CCP section 1281.96 arbitration case record.

    Populated by the section1281_96 retrieval pipeline from AAA, JAMS,
    and smaller providers. Each row is one consumer arbitration case
    filed in California.
    """

    __tablename__ = "s1281_96_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String(255), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # AAA, JAMS, ADRS, ...
    case_url = Column(Text)
    retrieval_ts = Column(DateTime, nullable=False)
    retrieval_sha256 = Column(String(64), nullable=False)
    case_year = Column(Integer, index=True)
    case_quarter = Column(Integer)
    filing_date = Column(DateTime)
    disposition_date = Column(DateTime)
    days_to_disposition = Column(Integer)
    non_consumer_party_name = Column(Text)
    non_consumer_entity_id = Column(
        String(255), ForeignKey("commercial_entities.entity_id"), index=True
    )  # nullable — not all parties are in the entity registry
    non_consumer_initiating = Column(Boolean)
    dispute_type = Column(String(100))
    dispute_subtype = Column(String(100))
    consumer_represented = Column(String(10))  # YES / NO / UNKNOWN
    prevailing_party = Column(String(50))
    claim_amount_usd = Column(Float)
    claim_amount_tier = Column(String(50))
    award_amount_usd = Column(Float)
    claim_to_award_ratio = Column(Float)
    disposition_type = Column(String(50))
    arbitrator_names = Column(Text)  # JSON array
    arbitrator_fee_total_usd = Column(Float)
    arbitrator_fee_alloc_consumer_pct = Column(Float)
    fee_waiver = Column(Boolean)
    other_relief = Column(Text)
    quality_flags = Column(Text)  # JSON array

    def __repr__(self) -> str:
        return f"<S128196Case(case_id='{self.case_id}', provider='{self.provider}', year={self.case_year})>"


__all__ = [
    "Base",
    "Document",
    "Provenance",
    "Section",
    "Reference",
    "Analysis",
    "Anomaly",
    "OrchestrationJob",
    "GovernancePolicy",
    "ValidationResult",
    "SecurityEvent",
    "GCNRule",
    "AgentNode",
    "AgentLink",
    "MeshExecutionJob",
    "AgentBehaviorEvent",
    "SeenHash",
    "WebhookAuditLog",
    "CPRARequest",
    "FieldObservation",
    # C.O.N.T.R.A. extension
    "CommercialEntity",
    "CommercialEntityAlias",
    "CommercialDocument",
    "ContraFinding",
    "CasiScore",
    "S128196Case",
]
