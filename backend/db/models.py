"""
Scout — SQLAlchemy ORM Models

All 12 core application tables as defined in the Master Shared Context (Section 5).
Uses PostgreSQL-specific types (UUID, JSONB) with timezone-aware timestamps.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    """Return current UTC time with timezone info for default column values."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Teams — top-level organisational unit
# ---------------------------------------------------------------------------
class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    users = relationship("User", back_populates="team", lazy="selectin")
    database_connections = relationship(
        "DatabaseConnection", back_populates="team", lazy="selectin"
    )
    master_configs = relationship(
        "MasterConfig", back_populates="team", lazy="selectin"
    )
    alert_configurations = relationship(
        "AlertConfiguration", back_populates="team", lazy="selectin"
    )
    alerts = relationship("Alert", back_populates="team", lazy="selectin")

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"


# ---------------------------------------------------------------------------
# Users — all personas and roles
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "persona IN ('MANAGER', 'DEVELOPER')",
            name="ck_users_persona",
        ),
        CheckConstraint(
            "role IN ('DATA_OWNER', 'ANALYST', 'PLATFORM_ADMIN', 'ENTERPRISE_ANALYST')",
            name="ck_users_role",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    persona = Column(String(20), nullable=False)
    role = Column(String(20), nullable=False, default="ANALYST")
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True
    )  # NULL for PLATFORM_ADMIN
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    team = relationship("Team", back_populates="users", lazy="selectin")
    chatrooms = relationship("Chatroom", back_populates="user", lazy="selectin")
    scheduled_queries = relationship(
        "ScheduledQuery", back_populates="user", lazy="selectin"
    )
    dashboard_cards = relationship(
        "DashboardCard", back_populates="user", lazy="selectin"
    )
    team_access_grants = relationship(
        "UserTeamAccess",
        back_populates="user",
        foreign_keys="UserTeamAccess.user_id",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


# ---------------------------------------------------------------------------
# UserTeamAccess — cross-team access map for ENTERPRISE_ANALYST
# ---------------------------------------------------------------------------
class UserTeamAccess(Base):
    __tablename__ = "user_team_access"
    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="uq_user_team_access"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user = relationship(
        "User",
        back_populates="team_access_grants",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    team = relationship("Team", lazy="selectin")
    granter = relationship("User", foreign_keys=[granted_by], lazy="selectin")

    def __repr__(self):
        return f"<UserTeamAccess(user_id={self.user_id}, team_id={self.team_id})>"


# ---------------------------------------------------------------------------
# DatabaseConnection — registered by Data Owners
# ---------------------------------------------------------------------------
class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    __table_args__ = (
        CheckConstraint(
            "db_type IN ('POSTGRES', 'MYSQL')",
            name="ck_db_connections_db_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=False)
    connection_string_enc = Column(Text, nullable=False)
    db_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    team = relationship("Team", back_populates="database_connections", lazy="selectin")
    master_configs = relationship(
        "MasterConfig", back_populates="db_connection", lazy="selectin"
    )

    def __repr__(self):
        return f"<DatabaseConnection(id={self.id}, name='{self.name}')>"


# ---------------------------------------------------------------------------
# MasterConfig — the security boundary; AI only reads tables registered here
# ---------------------------------------------------------------------------
class MasterConfig(Base):
    __tablename__ = "master_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    db_connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("database_connections.id"),
        nullable=False,
        index=True,
    )
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    table_name = Column(String(255), nullable=False)
    semantic_definition = Column(Text, nullable=False)
    columns_metadata = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    team = relationship("Team", back_populates="master_configs", lazy="selectin")
    db_connection = relationship(
        "DatabaseConnection", back_populates="master_configs", lazy="selectin"
    )

    def __repr__(self):
        return f"<MasterConfig(id={self.id}, table='{self.table_name}')>"


# ---------------------------------------------------------------------------
# Chatroom — one per user, isolated
# ---------------------------------------------------------------------------
class Chatroom(Base):
    __tablename__ = "chatrooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user = relationship("User", back_populates="chatrooms", lazy="selectin")
    messages = relationship(
        "Message",
        back_populates="chatroom",
        lazy="selectin",
        order_by="Message.created_at",
    )

    def __repr__(self):
        return f"<Chatroom(id={self.id}, name='{self.name}')>"


# ---------------------------------------------------------------------------
# Message — stores full chat history including Chain of Thought
# ---------------------------------------------------------------------------
class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('USER', 'ASSISTANT')",
            name="ck_messages_role",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatroom_id = Column(
        UUID(as_uuid=True), ForeignKey("chatrooms.id"), nullable=False, index=True
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    chain_of_thought = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    chatroom = relationship("Chatroom", back_populates="messages", lazy="selectin")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}')>"


# ---------------------------------------------------------------------------
# ScheduledQuery — user-configured recurring queries
# ---------------------------------------------------------------------------
class ScheduledQuery(Base):
    __tablename__ = "scheduled_queries"
    __table_args__ = (
        CheckConstraint(
            "delivery IN ('EMAIL', 'DASHBOARD')",
            name="ck_scheduled_queries_delivery",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    query_text = Column(Text, nullable=False)
    cron_expression = Column(String(100), nullable=False)
    delivery = Column(String(20), nullable=False)
    delivery_email = Column(String(255), nullable=True)
    alert_condition = Column(Text, nullable=True)
    alert_severity = Column(String(20), nullable=True, default="MEDIUM")
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user = relationship("User", back_populates="scheduled_queries", lazy="selectin")
    reports = relationship(
        "ScheduledReport", back_populates="scheduled_query", lazy="selectin"
    )

    def __repr__(self):
        return f"<ScheduledQuery(id={self.id}, active={self.is_active})>"


# ---------------------------------------------------------------------------
# ScheduledReport — results of scheduled query runs
# ---------------------------------------------------------------------------
class ScheduledReport(Base):
    __tablename__ = "scheduled_reports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('SUCCESS', 'FAILED')",
            name="ck_scheduled_reports_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scheduled_query_id = Column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_queries.id"),
        nullable=False,
        index=True,
    )
    result_data = Column(JSONB, nullable=False)
    status = Column(String(20), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    scheduled_query = relationship(
        "ScheduledQuery", back_populates="reports", lazy="selectin"
    )

    def __repr__(self):
        return f"<ScheduledReport(id={self.id}, status='{self.status}')>"


# ---------------------------------------------------------------------------
# AlertConfiguration — threshold definitions for anomaly detection
# ---------------------------------------------------------------------------
class AlertConfiguration(Base):
    __tablename__ = "alert_configurations"
    __table_args__ = (
        CheckConstraint(
            "condition IN ('ABOVE', 'BELOW', 'SPIKE')",
            name="ck_alert_configs_condition",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    metric_name = Column(String(255), nullable=False)
    table_name = Column(String(255), nullable=False)
    threshold = Column(Float, nullable=False)
    condition = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    team = relationship(
        "Team", back_populates="alert_configurations", lazy="selectin"
    )
    alerts = relationship("Alert", back_populates="alert_config", lazy="selectin")

    def __repr__(self):
        return f"<AlertConfiguration(id={self.id}, metric='{self.metric_name}')>"


# ---------------------------------------------------------------------------
# Alert — triggered alerts from anomaly detection
# ---------------------------------------------------------------------------
class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        CheckConstraint(
            "severity IN ('HIGH', 'MEDIUM', 'LOW')",
            name="ck_alerts_severity",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    alert_config_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alert_configurations.id"),
        nullable=True,
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    data_snapshot = Column(JSONB, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    team = relationship("Team", back_populates="alerts", lazy="selectin")
    alert_config = relationship(
        "AlertConfiguration", back_populates="alerts", lazy="selectin"
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, severity='{self.severity}')>"


# ---------------------------------------------------------------------------
# DashboardCard — persistent scheduled report outputs
# ---------------------------------------------------------------------------
class DashboardCard(Base):
    __tablename__ = "dashboard_cards"
    __table_args__ = (
        CheckConstraint(
            "chart_type IN ('BAR', 'LINE', 'PIE', 'TABLE')",
            name="ck_dashboard_cards_chart_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String(255), nullable=False)
    query_result = Column(JSONB, nullable=False)
    chart_type = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    user = relationship("User", back_populates="dashboard_cards", lazy="selectin")

    def __repr__(self):
        return f"<DashboardCard(id={self.id}, title='{self.title}')>"
