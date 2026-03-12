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
]
