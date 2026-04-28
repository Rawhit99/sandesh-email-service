"""Add authentication and audit tables

Revision ID: add_auth_tables
Revises: initial_migration
Create Date: 2024-01-01 12:00:00.000000

Idempotent: skips creating tables/indexes that already exist (brownfield DBs).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "add_auth_tables"
down_revision = "initial_migration"
branch_labels = None
depends_on = None


def _index_names(bind, table: str) -> set:
    insp = inspect(bind)
    if not insp.has_table(table):
        return set()
    return {ix["name"] for ix in insp.get_indexes(table)}


def upgrade():
    bind = op.get_bind()
    insp = inspect(bind)

    if not insp.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column(
                "organization_name", sa.String(length=255), nullable=True
            ),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    names = _index_names(bind, "users")
    if "ix_users_username" not in names:
        try:
            op.create_index(
                op.f("ix_users_username"), "users", ["username"], unique=True
            )
        except Exception:
            pass
    if "ix_users_id" not in names:
        try:
            op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
        except Exception:
            pass

    if not insp.has_table("api_keys"):
        op.create_table(
            "api_keys",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("key_hash", sa.String(length=255), nullable=False),
            sa.Column("key_prefix", sa.String(length=20), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    names = _index_names(bind, "api_keys")
    if "ix_api_keys_key_hash" not in names:
        try:
            op.create_index(
                op.f("ix_api_keys_key_hash"),
                "api_keys",
                ["key_hash"],
                unique=True,
            )
        except Exception:
            pass
    if "ix_api_keys_id" not in names:
        try:
            op.create_index(
                op.f("ix_api_keys_id"), "api_keys", ["id"], unique=False
            )
        except Exception:
            pass

    if not insp.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=100), nullable=False),
            sa.Column("email_to", sa.String(length=255), nullable=True),
            sa.Column("template_id", sa.String(length=255), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("ip_address", sa.String(length=50), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    names = _index_names(bind, "audit_logs")
    if "ix_audit_logs_created_at" not in names:
        try:
            op.create_index(
                op.f("ix_audit_logs_created_at"),
                "audit_logs",
                ["created_at"],
                unique=False,
            )
        except Exception:
            pass
    if "ix_audit_logs_id" not in names:
        try:
            op.create_index(
                op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False
            )
        except Exception:
            pass
    if "idx_user_created_at" not in names:
        try:
            op.create_index(
                "idx_user_created_at",
                "audit_logs",
                ["user_id", "created_at"],
                unique=False,
            )
        except Exception:
            pass
    if "idx_action_created_at" not in names:
        try:
            op.create_index(
                "idx_action_created_at",
                "audit_logs",
                ["action", "created_at"],
                unique=False,
            )
        except Exception:
            pass


def downgrade():
    bind = op.get_bind()
    insp = inspect(bind)
    if insp.has_table("audit_logs"):
        for ix in (
            "idx_action_created_at",
            "idx_user_created_at",
            op.f("ix_audit_logs_id"),
            op.f("ix_audit_logs_created_at"),
        ):
            try:
                op.drop_index(ix, table_name="audit_logs")
            except Exception:
                pass
        op.drop_table("audit_logs")
    if insp.has_table("api_keys"):
        for ix in (op.f("ix_api_keys_id"), op.f("ix_api_keys_key_hash")):
            try:
                op.drop_index(ix, table_name="api_keys")
            except Exception:
                pass
        op.drop_table("api_keys")
    if insp.has_table("users"):
        for ix in (op.f("ix_users_id"), op.f("ix_users_username")):
            try:
                op.drop_index(ix, table_name="users")
            except Exception:
                pass
        op.drop_table("users")
