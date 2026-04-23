import hashlib
import secrets
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    org_slug = Column(String(60), unique=True, nullable=True, index=True)
    service_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    members = relationship(
        "User",
        back_populates="organization",
        foreign_keys="User.organization_id",
    )
    service_user = relationship(
        "User",
        foreign_keys=[service_user_id],
        uselist=False,
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_name = Column(String(255), nullable=True)
    organization_role = Column(String(20), nullable=True)
    is_platform_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    # Per-user outbound webhooks (Slack/Teams); merged with env defaults at send time.
    channel_webhooks = Column(JSONB, nullable=True)
    # DB-backed integration + email delivery (preferred over .env when user owns the send).
    integration_settings = Column(JSONB, nullable=True)
    email_delivery_settings = Column(JSONB, nullable=True)

    organization = relationship(
        "Organization",
        back_populates="members",
        foreign_keys=[organization_id],
    )

    # Relationships
    api_keys = relationship(
        "APIKey",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="user")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First 8 chars for display
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="api_keys")

    @staticmethod
    def generate_key() -> str:
        """Generate a secure API key."""
        return f"sandesh_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash the API key for storage."""
        return hashlib.sha256(key.encode()).hexdigest()

    @staticmethod
    def verify_key(key: str, key_hash: str) -> bool:
        """Verify if the provided key matches the hash."""
        return hashlib.sha256(key.encode()).hexdigest() == key_hash


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "email_sent", "email_failed"
    email_to = Column(String(255), nullable=True)
    template_id = Column(String(255), nullable=True)
    payload = Column(JSON, nullable=True)
    status = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_user_created_at", "user_id", "created_at"),
        Index("idx_action_created_at", "action", "created_at"),
    )


class Subscriber(Base):
    """Subscriber profile; deliveries can be gated on this row."""

    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    subscriber_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    data = Column(JSON, nullable=True)
    channels = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", backref="subscribers")

    __table_args__ = (
        UniqueConstraint("user_id", "subscriber_id", name="uq_subscriber_user_ext"),
    )


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(String(500), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    subscriber_external_id = Column(String(255), nullable=True, index=True)
    execution_run_id = Column(String(36), nullable=True, index=True)
    channels_requested = Column(JSON, nullable=True)
    from_email_override = Column(String(255), nullable=True)
    sender_display_name = Column(String(255), nullable=True)
    attachments = Column(JSON, nullable=True)
    seen_at = Column(DateTime, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index("idx_status_executed_at", "status", "executed_at"),
        Index("idx_template_status", "template_id", "status"),
        Index("idx_email_status", "email", "status"),
    )


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(255), nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(JSONB, nullable=False, server_default="{}")
    default_attachments = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)


class IntegrationCredential(Base):
    """Named, per-user credential set for a specific integration channel."""

    __tablename__ = "integration_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel = Column(String(60), nullable=False)
    name = Column(String(120), nullable=False)
    config = Column(JSONB, nullable=False, server_default="{}")
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", backref="integration_credentials")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "channel",
            "name",
            name="uq_intcred_user_channel_name",
        ),
        Index("ix_intcred_user_channel", "user_id", "channel"),
    )


class OrgTemplateSetting(Base):
    """Controls whether a template is enabled for an organization."""

    __tablename__ = "org_template_settings"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    template_id = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    organization = relationship("Organization", backref="template_settings")

    __table_args__ = (
        UniqueConstraint("organization_id", "template_id", name="uq_org_template_setting"),
        Index("ix_org_tpl_org_id", "organization_id"),
    )


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
